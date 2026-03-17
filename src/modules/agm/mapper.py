import asyncio
from typing import Any, TypeVar, get_type_hints, Annotated, get_origin, get_args, Type
from adaptix import Retort
from src.core.messagebus import MessageBus
from src.modules.agm.messages import StoredFieldRecalculationRequested
from dishka import AsyncContainer
from src.modules.agm.metadata import Live, Stored, Rel
from loguru import logger

T = TypeVar("T")


class AGMMapper:
    def __init__(self, container: AsyncContainer, message_bus: MessageBus):
        self.container = container
        self.message_bus = message_bus
        self.retort = Retort()
        self.polymorphic_registry = {}

    def register_subclass(self, label: str, cls: Type[T]):
        self.polymorphic_registry[label] = cls

    async def load(
        self, model_class: type[T], record: dict[str, Any], resolve_live: bool = True
    ) -> T:
        # 1. Discrimination (Polymorphism)
        labels = record.get("labels", [])
        actual_class = model_class
        for label in labels:
            if label in self.polymorphic_registry:
                actual_class = self.polymorphic_registry[label]
                break

        # 2. Base Mapping
        instance = self.retort.load(record, actual_class)

        # 3. Live Hydration
        if resolve_live:
            hints = get_type_hints(actual_class, include_extras=True)
            live_tasks = []

            async def fetch_and_set(field_name: str, handler_type: type):
                try:
                    value = await self.container.get(handler_type)
                    setattr(instance, field_name, value)
                except Exception as e:
                    logger.warning(
                        f"Live Hydration failed for field '{field_name}' via handler '{handler_type}': {e}"
                    )

            for field_name, field_type in hints.items():
                if get_origin(field_type) is Annotated:
                    for metadata in get_args(field_type)[1:]:
                        if isinstance(metadata, Live):
                            live_tasks.append(
                                fetch_and_set(field_name, metadata.handler)
                            )

            if live_tasks:
                await asyncio.gather(*live_tasks)

        return instance

    async def save(
        self, model: Any, previous_state: dict[str, Any] = None, session: Any = None
    ):
        if previous_state is None:
            previous_state = {}

        # 1. Cypher MERGE Generation
        hints = get_type_hints(type(model), include_extras=True)
        label = type(model).__name__
        node_id = getattr(model, "id", None)

        if not node_id:
            logger.error("Cannot save model without 'id' field.")
            return

        set_statements = []
        cypher_params = {"id": node_id}
        rel_statements = []

        for field_name, field_type in hints.items():
            if field_name == "id" or field_name == "labels":
                continue

            is_live = False
            is_rel = False
            rel_metadata = None

            if get_origin(field_type) is Annotated:
                for metadata in get_args(field_type)[1:]:
                    if isinstance(metadata, Live):
                        is_live = True
                    elif isinstance(metadata, Rel):
                        is_rel = True
                        rel_metadata = metadata

            if is_live:
                continue

            val = getattr(model, field_name, None)

            if is_rel:
                # Handles relationship merge
                if val:
                    nodes = val if isinstance(val, list) else [val]
                    for idx, target_node in enumerate(nodes):
                        target_id = getattr(target_node, "id", None)
                        if target_id:
                            target_label = type(target_node).__name__
                            param_name = f"rel_{field_name}_{idx}"
                            cypher_params[param_name] = target_id
                            if rel_metadata.direction == "OUTGOING":
                                rel_statements.append(
                                    f"MERGE (n)-[:{rel_metadata.type}]->(:{target_label} {{id: ${param_name}}})"
                                )
                            else:
                                rel_statements.append(
                                    f"MERGE (n)<-[:{rel_metadata.type}]-(:{target_label} {{id: ${param_name}}})"
                                )
            else:
                cypher_params[field_name] = val
                set_statements.append(f"n.{field_name} = ${field_name}")

        set_clause = ",\n  ".join(set_statements)
        set_part = f"SET\n  {set_clause}\n" if set_clause else ""
        rel_part = "\n".join(rel_statements)

        cypher_query = f"MERGE (n:{label} {{id: $id}})\n{set_part}{rel_part}\nRETURN n"

        logger.debug(
            f"Generated Cypher MERGE:\n{cypher_query}\nParams: {cypher_params}"
        )

        # Execute the query using the provided session
        if session and hasattr(session, "run"):
            await session.run(cypher_query, cypher_params)

        # 2. Side Effects (Publish Event for stored fields)
        events_to_publish = []
        for field_name, field_type in hints.items():
            if get_origin(field_type) is Annotated:
                for metadata in get_args(field_type)[1:]:
                    if isinstance(metadata, Stored):
                        source_field = metadata.source_field
                        new_source_val = getattr(model, source_field, None)
                        old_source_val = previous_state.get(source_field)

                        if new_source_val != old_source_val:
                            logger.info(
                                f"Source field '{source_field}' changed. Requesting recalculation for '{field_name}'."
                            )
                            event = StoredFieldRecalculationRequested(
                                node_id=node_id,
                                field_name=field_name,
                                new_source_val=new_source_val,
                            )
                            events_to_publish.append(event)

        for event in events_to_publish:
            try:
                await self.message_bus.dispatch(event)
            except Exception as e:
                logger.error(
                    f"Failed to dispatch StoredFieldRecalculationRequested event: {e}"
                )
