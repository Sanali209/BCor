import asyncio
import json
from typing import Annotated, Any, Dict, List, Optional, TypeVar, get_args, get_origin, get_type_hints

from adaptix import Retort
from dishka import AsyncContainer
from loguru import logger

from src.core.messagebus import MessageBus
from src.modules.agm.messages import StoredFieldRecalculationRequested, NodeSyncRequested, SyncFieldInfo
from src.modules.agm.metadata import Live, Rel, Stored, OnComplete
from src.modules.agm.schema import AGMSchemaManager
from src.modules.agm.query import CypherQuery

T = TypeVar("T")


class AGMMapper:
    """Graph-Object Mapper (GOM) for Neo4j."""

    def __init__(
        self,
        container: AsyncContainer,
        message_bus: MessageBus,
        schema_manager: Optional[AGMSchemaManager] = None,
    ) -> None:
        self.container = container
        self.message_bus = message_bus
        self.schema_manager = schema_manager
        
        from datetime import datetime
        from uuid import UUID
        from adaptix import dumper, loader

        self.retort = Retort(
            recipe=[
                dumper(datetime, lambda d: d.isoformat()),
                dumper(UUID, str),
                loader(datetime, datetime.fromisoformat),
                loader(UUID, UUID),
            ]
        )
        self.polymorphic_registry: dict[str, type] = {}
        self._identity_map: dict[tuple[type, Any], Any] = {}
        self._uri_map: dict[str, Any] = {}

    async def register_subclass(self, label: str, cls: type):
        self.polymorphic_registry[label] = cls
        if self.schema_manager:
            await self.schema_manager.sync_class(cls)

    def query(self, model_class: type[T]) -> CypherQuery[T]:
        return CypherQuery(self, model_class)

    async def load(self, model_class: type[T], record: dict[str, Any], resolve_live: bool = True) -> T:
        node_id = record.get("id")
        if not node_id:
            return await self._load_instance(model_class, record, resolve_live)

        cache_key = (model_class, node_id)
        if cache_key in self._identity_map:
            instance = self._identity_map[cache_key]
            if resolve_live and not getattr(instance, "_agm_hydrated", False):
                await self._hydrate_instance(instance, resolve_live)
            return instance

        instance = await self._load_instance(model_class, record, resolve_live)
        self._identity_map[cache_key] = instance
        return instance

    async def _load_instance(self, model_class: type[T], record: dict[str, Any], resolve_live: bool) -> T:
        processed_record = {}
        for k, v in record.items():
            if isinstance(v, str) and (v.startswith("{") or v.startswith("[")):
                try:
                    processed_record[k] = json.loads(v)
                except json.JSONDecodeError:
                    processed_record[k] = v
            else:
                processed_record[k] = v

        labels = processed_record.get("labels", [])
        actual_class = model_class
        for label in labels:
            if label in self.polymorphic_registry:
                actual_class = self.polymorphic_registry[label]
                break

        clean_record = {k: v for k, v in processed_record.items() if v is not None}
        instance = self.retort.load(clean_record, actual_class)
        await self._hydrate_instance(instance, resolve_live)
        return instance

    async def _hydrate_instance(self, instance: Any, resolve_live: bool):
        if not resolve_live: return
        hints = get_type_hints(type(instance), include_extras=True)
        live_tasks = []
        async def fetch_and_set(field_name: str, handler_type: type):
            try:
                value = await self.container.get(handler_type)
                setattr(instance, field_name, value)
            except Exception as e:
                logger.warning(f"Live Hydration failed for {field_name}: {e}")

        for field_name, field_type in hints.items():
            if get_origin(field_type) is Annotated:
                for metadata in get_args(field_type)[1:]:
                    if isinstance(metadata, Live):
                        live_tasks.append(fetch_and_set(field_name, metadata.handler))
        if live_tasks: await asyncio.gather(*live_tasks)
        setattr(instance, "_agm_hydrated", True)

    async def save(self, model: Any, previous_state: dict[str, Any] = None, session: Any = None):
        """Saves a single instance, preserving all relationships and side effects."""
        await self.save_batch([model], session=session, previous_states={id(model): previous_state or {}})

    async def save_batch(self, models: List[Any], session: Any = None, previous_states: Dict[int, Dict[str, Any]] = None):
        """Optimized batch save using UNWIND for properties, and sequential handling for relations."""
        if not models: return
        previous_states = previous_states or {}

        # 1. Properties Batch (UNWIND)
        batch_payload = []
        labels_map = {} # label_clause -> [ids]
        
        for model in models:
            node_id = getattr(model, "id", None)
            if not node_id: continue
            
            # Identity cache
            self._identity_map[(type(model), node_id)] = model
            if uri := getattr(model, "uri", None): self._uri_map[uri] = model

            # Extract properties
            dumped = self.retort.dump(model)
            hints = get_type_hints(type(model), include_extras=True)
            props = {}
            for k, h in hints.items():
                if k in ("id", "labels", "_agm_hydrated"): continue
                # Skip Rel and Live
                meta = getattr(h, "__metadata__", [])
                if any(isinstance(m, (Rel, Live)) for m in meta): continue
                
                val = dumped.get(k)
                if isinstance(val, (dict, list)): val = json.dumps(val)
                props[k] = val
            
            batch_payload.append({"id": node_id, "props": props})
            
            # Label clause
            labels = sorted([cls.__name__ for cls in type(model).mro() if cls.__name__ not in ("object", "ABC") and not cls.__module__.startswith("typing")])
            label_clause = ":".join(labels)
            labels_map.setdefault(label_clause, []).append(node_id)

        if session and batch_payload:
            # Batch Properties
            await session.run("UNWIND $batch AS row MERGE (n {id: row.id}) SET n += row.props", {"batch": batch_payload})
            # Batch Labels
            for label_clause, ids in labels_map.items():
                await session.run(f"MATCH (n) WHERE n.id IN $ids SET n:{label_clause}", {"ids": ids})
            logger.info(f"[AGM:BATCH] Saved {len(batch_payload)} nodes")

        # 2. Individual Handling (Relations & Sync)
        # For simplicity in Phase 1, we iterate for relations. UNWIND for relations is Phase 2.
        for model in models:
            await self._handle_side_effects(model, previous_states.get(id(model), {}), session)

    async def _handle_side_effects(self, model: Any, previous_state: Dict[str, Any], session: Any):
        node_id = getattr(model, "id")
        hints = get_type_hints(type(model), include_extras=True)
        
        # 1. Relationships
        for field_name, field_type in hints.items():
            meta = getattr(field_type, "__metadata__", [])
            rel_meta = next((m for m in meta if isinstance(m, Rel)), None)
            if rel_meta:
                val = getattr(model, field_name, None)
                if not val: continue
                targets = val if isinstance(val, list) else [val]
                for target_node in targets:
                    target_id = getattr(target_node, "id", None)
                    if not target_id: continue
                    target_label = type(target_node).__name__
                    
                    cypher = f"MATCH (n {{id: $node_id}}) MERGE (m:{target_label} {{id: $tid}}) "
                    if rel_meta.direction == "OUTGOING":
                        cypher += f"MERGE (n)-[r:{rel_meta.type}]->(m)"
                    else:
                        cypher += f"MERGE (n)<-[r:{rel_meta.type}]-(m)"
                    
                    if session: await session.run(cypher, {"node_id": node_id, "tid": target_id})

        # 2. Sync Triggers
        fields_to_sync = []
        use_taskiq = False
        for field_name, field_type in hints.items():
            meta = getattr(field_type, "__metadata__", [])
            stored_meta = next((m for m in meta if isinstance(m, Stored)), None)
            if stored_meta:
                sources = stored_meta.effective_source_fields()
                changed = any(getattr(model, s, None) != previous_state.get(s) for s in sources)
                if changed:
                    if stored_meta.use_taskiq: use_taskiq = True
                    fields_to_sync.append(SyncFieldInfo(
                        field_name=field_name,
                        source_value=getattr(model, sources[0], None),
                        handler=stored_meta.handler,
                        priority=stored_meta.priority,
                        context_metadata=stored_meta.context_metadata_dict
                    ))
        
        if fields_to_sync:
            await self.message_bus.dispatch(NodeSyncRequested(
                node_id=node_id, fields=fields_to_sync, 
                mime_type=getattr(model, "mime_type", ""), use_taskiq=use_taskiq
            ))
