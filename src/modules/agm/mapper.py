import asyncio
import json
from typing import Annotated, Any, Optional, TypeVar, get_args, get_origin, get_type_hints

from adaptix import Retort
from dishka import AsyncContainer
from loguru import logger

from src.core.messagebus import MessageBus
from src.modules.agm.messages import StoredFieldRecalculationRequested
from src.modules.agm.metadata import Live, Rel, Stored
from src.modules.agm.schema import AGMSchemaManager
from src.modules.agm.query import CypherQuery

T = TypeVar("T")


class AGMMapper:
    """Graph-Object Mapper (GOM) for Neo4j.

    The AGMMapper handles the conversion between Python domain models
    and Neo4j node/relationship records. It supports:
    1. Polymorphism: Loading subclasses based on graph labels.
    2. Dependency Injection: Hydrating 'Live' fields via Dishka.
    3. Change Tracking: Identifying changes to trigger background tasks.
    4. Relationship Mapping: Merging graph relationships from model attributes.

    Attributes:
        container: Dishka AsyncContainer for live field resolution.
        message_bus: System MessageBus for side-effect dispatching.
        retort: Adaptix Retort instance for structural mapping.
        polymorphic_registry: Map of graph labels to Python classes.
    """

    def __init__(
        self,
        container: AsyncContainer,
        message_bus: MessageBus,
        schema_manager: Optional[AGMSchemaManager] = None,
    ) -> None:
        """Initializes the AGMMapper."""
        self.container = container
        self.message_bus = message_bus
        self.schema_manager = schema_manager
        
        # Specialized Retort for Neo4j
        from adaptix import loader, dumper, name_mapping, Omitted
        from adaptix.load_error import TypeLoadError
        from datetime import datetime
        from uuid import UUID
        
        def maybe_parse_json(data):
            if isinstance(data, str) and (data.startswith("{") or data.startswith("[")):
                try:
                    return json.loads(data)
                except json.JSONDecodeError:
                    return data
            return data

        self.retort = Retort(
            recipe=[
                # 1. Structural Mapping (Dump)
                dumper(datetime, lambda d: d.isoformat()),
                dumper(UUID, str),
                
                # 2. Structural Mapping (Load)
                loader(datetime, datetime.fromisoformat),
                loader(UUID, UUID),
            ]
        )
        self.polymorphic_registry: dict[str, type] = {}
        # Identity Map: (Class, ID) -> Instance (primary key)
        self._identity_map: dict[tuple[type, Any], Any] = {}
        # Secondary index: URI -> Instance (for dedup on ingest)
        self._uri_map: dict[str, Any] = {}

    async def register_subclass(self, label: str, cls: type):
        """Registers a subclass for polymorphic loading and syncs its schema.

        Args:
            label: The Neo4j label associated with the class.
            cls: The Python class to instantiate for this label.
        """
        self.polymorphic_registry[label] = cls
        if self.schema_manager:
            logger.info(f"Syncing schema for registered subclass: {label}")
            await self.schema_manager.sync_class(cls)

    def query(self, model_class: type[T]) -> CypherQuery[T]:
        """Returns a fluent query builder for the given model class.
        
        Args:
            model_class: The domain model class to query.
        """
        return CypherQuery(self, model_class)

    async def load(self, model_class: type[T], record: dict[str, Any], resolve_live: bool = True) -> T:
        """Loads a domain model instance from a database record.

        Args:
            model_class: The base class expected from the record.
            record: The raw dictionary record from Neo4j.
            resolve_live: Whether to hydrate fields marked with @Live.

        Returns:
            An instance of model_class (or a registered subclass).
        """
        node_id = record.get("id")
        if not node_id:
            logger.warning("Loading model from record without 'id'. Identity Cache bypassed.")
            return await self._load_instance(model_class, record, resolve_live)

        # 1. Identity Map Lookup (by ID)
        cache_key = (model_class, node_id)
        if cache_key in self._identity_map:
            instance = self._identity_map[cache_key]
            # Smart Hydration: run DI hydration if not yet done
            if resolve_live and not getattr(instance, "_agm_hydrated", False):
                await self._hydrate_instance(instance, resolve_live)
            return instance

        # 2. Secondary index lookup — URI dedup
        node_uri = record.get("uri")
        if node_uri and node_uri in self._uri_map:
            instance = self._uri_map[node_uri]
            # Re-register under the ID key (in case ID changed)
            self._identity_map[cache_key] = instance
            return instance

        # 3. Fresh Load
        instance = await self._load_instance(model_class, record, resolve_live)
        self._identity_map[cache_key] = instance
        if uri := getattr(instance, "uri", None):
            self._uri_map[uri] = instance
        return instance

    async def _load_instance(self, model_class: type[T], record: dict[str, Any], resolve_live: bool) -> T:
        """Helper to create and hydrate a fresh instance."""
        # 0. Pre-process record (e.g. JSON strings from Neo4j)
        processed_record = {}
        for k, v in record.items():
            if isinstance(v, str) and (v.startswith("{") or v.startswith("[")):
                try:
                    processed_record[k] = json.loads(v)
                except json.JSONDecodeError:
                    processed_record[k] = v
            else:
                processed_record[k] = v

        # 1. Discrimination (Polymorphism)
        labels = processed_record.get("labels", [])
        actual_class = model_class
        for label in labels:
            if label in self.polymorphic_registry:
                actual_class = self.polymorphic_registry[label]
                break


                # 2. Cleanup record for Adaptix (remove None to let defaults work)
        clean_record = {k: v for k, v in processed_record.items() if v is not None}
        instance = self.retort.load(clean_record, actual_class)

        # 3. Live Hydration
        await self._hydrate_instance(instance, resolve_live)
        return instance

    async def _hydrate_instance(self, instance: Any, resolve_live: bool):
        """Performs DI hydration on an instance if resolve_live is True."""
        if not resolve_live:
            return

        actual_class = type(instance)
        hints = get_type_hints(actual_class, include_extras=True)
        live_tasks = []

        async def fetch_and_set(field_name: str, handler_type: type):
            try:
                value = await self.container.get(handler_type)
                setattr(instance, field_name, value)
            except Exception as e:
                logger.warning(f"Live Hydration failed for field '{field_name}' via handler '{handler_type}': {e}")

        for field_name, field_type in hints.items():
            if get_origin(field_type) is Annotated:
                for metadata in get_args(field_type)[1:]:
                    if isinstance(metadata, Live):
                        live_tasks.append(fetch_and_set(field_name, metadata.handler))

        if live_tasks:
            await asyncio.gather(*live_tasks)
        
        # Mark as hydrated to avoid redundant calls in Smart Hydration pattern
        setattr(instance, "_agm_hydrated", True)

    async def save(self, model: Any, previous_state: dict[str, Any] = None, session: Any = None):
        """Saves a domain model instance to Neo4j using Cypher MERGE.

        This method generates a Cypher query based on model attributes
        and metadata, merges the node and its relationships, and
        dispatches recalculation events for changed source fields.

        Args:
            model: The domain model instance to save.
            previous_state: Optional dict representing the state before changes.
            session: An active Neo4j driver session.
        """
        if previous_state is None:
            previous_state = {}

        hints = get_type_hints(type(model), include_extras=True)
        # 1. Cypher MERGE Generation
        # Collect all labels from the class hierarchy that are not standard built-ins
        labels_list = []
        for cls in type(model).mro():
            if cls.__name__ in ("object", "ABC", "BaseModel") or cls.__module__.startswith("abc") or cls.__module__.startswith("typing"):
                continue
            labels_list.append(cls.__name__)
        
        # Sort for deterministic query generation
        labels_list.sort()
        label_clause = ":".join(labels_list)
        node_id = getattr(model, "id", None)

        if not node_id:
            logger.error("Cannot save model without 'id' field.")
            return

        # Use Adaptix to dump all properties
        dumped_data = self.retort.dump(model)
        cypher_params = {"id": node_id}
        set_statements = []
        rel_statements = []
        
        # Track fields that should NOT be part of the node properties (Rel, Live)
        exclude_fields = {"id", "labels", "_agm_hydrated"}

        for field_name, field_type in hints.items():
            if field_name in exclude_fields:
                continue

            is_live = False
            is_rel = False
            rel_metadata = None
            
            origin = get_origin(field_type)

            if origin is Annotated:
                for metadata in get_args(field_type)[1:]:
                    if isinstance(metadata, Live):
                        is_live = True
                    elif isinstance(metadata, Rel):
                        is_rel = True
                        rel_metadata = metadata

            if is_live:
                exclude_fields.add(field_name)
                continue

            if is_rel:
                exclude_fields.add(field_name)
                val = getattr(model, field_name, None)
                if val:
                    nodes = val if isinstance(val, list) else [val]
                    for idx, target_node in enumerate(nodes):
                        target_id = getattr(target_node, "id", None)
                        if target_id:
                            target_label = getattr(target_node, "target_label", type(target_node).__name__)
                            param_name = f"rel_{field_name}_{idx}"
                            cypher_params[param_name] = target_id
                            
                            # Handle relationship properties
                            props_param = f"rel_props_{field_name}_{idx}"
                            rel_props = {}
                            if rel_metadata.metadata and rel_metadata.metadata.model:
                                try:
                                    raw_dump = self.retort.dump(target_node, rel_metadata.metadata.model)
                                    rel_props = {k: v for k, v in raw_dump.items() if k not in ("id", "labels")}
                                except Exception:
                                    pass
                                    
                            cypher_params[props_param] = rel_props
                            rel_statements.append(
                                (rel_metadata.type, target_label, param_name, rel_metadata.direction, props_param)
                            )
            else:
                # Basic property: use the dumped value from Adaptix
                val = dumped_data.get(field_name)
                
                # Transport-level serialization for Neo4j (JSON strings for non-primitives)
                if isinstance(val, (dict, list)):
                    val = json.dumps(val)
                
                cypher_params[field_name] = val
                set_statements.append(f"n.{field_name} = ${field_name}")

        set_clause = ",\n  ".join(set_statements)
        set_part = f"SET\n  {set_clause}\n" if set_clause else ""
        
        # Use explicit WITH/MERGE for each relationship to ensure robust matching
        rel_blocks = []
        for idx, (rel_type, target_label, target_id_param, direction, props_param) in enumerate(rel_statements):
            set_rel_props = f"SET r_{idx} += ${props_param}"
            if direction == "OUTGOING":
                rel_blocks.append(
                    f"WITH n\nMERGE (m_{idx}:{target_label} {{id: ${target_id_param}}})\nMERGE (n)-[r_{idx}:{rel_type}]->(m_{idx})\n{set_rel_props}"
                )
            else:
                rel_blocks.append(
                    f"WITH n\nMERGE (m_{idx}:{target_label} {{id: ${target_id_param}}})\nMERGE (n)<-[r_{idx}:{rel_type}]-(m_{idx})\n{set_rel_props}"
                )
        
        rel_part = "\n".join(rel_blocks)
        
        # FIX: Match strictly on ID first to avoid duplicates when label set evolves.
        # Then SET labels separately to ensure polymorphic labels are applied.
        cypher_query = (
            f"MERGE (n {{id: $id}})\n"
            f"SET n:{label_clause}\n"
            f"{set_part}{rel_part}\n"
            f"RETURN n"
        )

        logger.debug(f"Generated Cypher MERGE:\n{cypher_query}\nParams: {cypher_params}")

        # Execute the query using the provided session
        if session and hasattr(session, "run"):
            result = await session.run(cypher_query, cypher_params)
            await result.consume()

        # 2. Update Identity Map after save (both ID and URI keys)
        self._identity_map[(type(model), node_id)] = model
        if uri := getattr(model, "uri", None):
            self._uri_map[uri] = model

        # 3. Side Effects (Group into Batch Event to avoid Windows Timer Exhaustion)
        fields_to_sync = []
        use_taskiq_batch = False
        
        for field_name, field_type in hints.items():
            if get_origin(field_type) is Annotated:
                for metadata in get_args(field_type)[1:]:
                    if isinstance(metadata, Stored):
                        effective_sources = metadata.effective_source_fields()
                        changed = any(
                            getattr(model, src, None) != previous_state.get(src)
                            for src in effective_sources
                        )
                        deps_met = all(
                            getattr(model, dep, None) is not None
                            for dep in metadata.depends_on
                        )
                        
                        if changed and deps_met:
                            from src.modules.agm.messages import SyncFieldInfo
                            
                            # Gather config
                            context_dict = metadata.context_metadata_dict.copy()
                            rel_meta = next((m for m in get_args(field_type)[1:] if isinstance(m, Rel)), None)
                            if rel_meta:
                                context_dict["agm_field_type"] = "RELATION"
                                context_dict["rel_type"] = rel_meta.type
                            
                            if metadata.use_taskiq:
                                use_taskiq_batch = True
                                
                            fields_to_sync.append(SyncFieldInfo(
                                field_name=field_name,
                                source_value=getattr(model, effective_sources[0], None),
                                handler=metadata.handler,
                                model=metadata.model,
                                priority=metadata.priority,
                                context_metadata=context_dict
                            ))
                    
                    elif type(metadata).__name__ == "OnComplete":
                        deps_met = all(
                            getattr(model, dep, None) is not None and getattr(model, dep, None) != ""
                            for dep in metadata.depends_on
                        )
                        prev_deps_met = False
                        if previous_state:
                            prev_deps_met = all(
                                previous_state.get(dep, None) is not None and previous_state.get(dep, None) != ""
                                for dep in metadata.depends_on
                            )
                        has_changed = any(
                            getattr(model, dep, None) != previous_state.get(dep)
                            for dep in metadata.depends_on
                        )
                        
                        if deps_met and (not prev_deps_met or has_changed):
                            from src.modules.agm.messages import SyncFieldInfo
                            if metadata.use_taskiq: use_taskiq_batch = True
                            fields_to_sync.append(SyncFieldInfo(
                                field_name=field_name,
                                source_value="trigger",
                                handler=metadata.handler,
                                model=None,
                                priority=metadata.priority,
                                context_metadata={"agm_field_type": "ACTION"}
                            ))

        if fields_to_sync:
            from src.modules.agm.messages import NodeSyncRequested
            batch_event = NodeSyncRequested(
                node_id=node_id,
                fields=fields_to_sync,
                mime_type=getattr(model, "mime_type", ""),
                use_taskiq=use_taskiq_batch
            )
            try:
                await self.message_bus.dispatch(batch_event)
                logger.info(f"Dispatched batch sync for {len(fields_to_sync)} fields on {node_id}")
            except Exception as e:
                logger.error(f"Failed to dispatch batch sync: {e}")
