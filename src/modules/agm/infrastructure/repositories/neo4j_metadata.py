from __future__ import annotations
import dataclasses
import json
import logging
import uuid
from typing import Any, Dict, List, Optional
from neo4j import AsyncGraphDatabase

logger = logging.getLogger(__name__)

def _serialize_val(val: Any) -> Any:
    """Recursively convert objects to Neo4j-compatible primitives/dicts."""
    if dataclasses.is_dataclass(val):
        return _serialize_val(dataclasses.asdict(val))
    if isinstance(val, list):
        return [_serialize_val(v) for v in val]
    if isinstance(val, dict):
        return {k: _serialize_val(v) for k, v in val.items()}
    if hasattr(val, "__dict__") and not isinstance(val, (str, int, float, bool, type(None))):
        # Handle custom objects that aren't dataclasses
        return _serialize_val(val.__dict__)
    if isinstance(val, uuid.UUID):
        return str(val)
    return val

class Neo4jMetadataRepository:
    def __init__(self, uri: str, auth: tuple):
        self.driver = AsyncGraphDatabase.driver(uri, auth=auth)

    async def close(self):
        await self.driver.close()

    async def init_schema(self):
        async with self.driver.session() as session:
            await session.run("CREATE CONSTRAINT asset_id_unique IF NOT EXISTS FOR (n:Asset) REQUIRE n.id IS UNIQUE")
            await session.run("CREATE INDEX inference_field_idx IF NOT EXISTS FOR (n:InferenceEvent) ON (n.field_name)")
            await session.run("CREATE INDEX asset_uri_idx IF NOT EXISTS FOR (n:Asset) ON (n.uri)")

    async def persist_metadata(self, node_id: str, event_id: str, handler: str, field: str, status: str, props: Any, model_name: str = "Asset"):
        """Single Field Persistence (Latest-Only)."""
        props = _serialize_val(props)
        async with self.driver.session() as session:
            await session.execute_write(self._persist_single_tx, node_id, event_id, handler, field, status, props, model_name)

    @staticmethod
    async def _persist_single_tx(tx, node_id, event_id, handler, field, status, props, model_name):
        # 1. Update Asset Property (if SUCCESS)
        if status == "SUCCESS" and props is not None:
             # Basic property update. For relations, use persist_metadata_batch for now or expand this.
             await tx.run(f"""
                MATCH (n {{id: $node_id}})
                SET n.{field} = $val, n.last_sync = timestamp()
            """, {"node_id": node_id, "val": props})
        
        # 2. Latest-Only Inference Event
        await tx.run("""
            MATCH (n {id: $node_id})
            MERGE (n)-[:HAS_INFERENCE {field_name: $field}]->(e:InferenceEvent)
            SET e.id = $event_id, 
                e.handler_name = $handler, 
                e.status = $status, 
                e.updated_at = timestamp(),
                e.field_name = $field
        """, {"node_id": node_id, "event_id": event_id, "handler": handler, "field": field, "status": status})

    async def persist_metadata_batch(self, node_id: str, event_id: str, results: List[Dict[str, Any]], model_name: str = "Asset"):
        """ATOMIC Batch Persistence addressing Q4 (One Event per Batch)."""
        results = [_serialize_val(res) for res in results]
        async with self.driver.session() as session:
            await session.execute_write(self._persist_batch_tx, node_id, event_id, results, model_name)

    @staticmethod
    async def _persist_batch_tx(tx, node_id, event_id, results, model_name):
        await tx.run(f"MERGE (n {{id: $id}}) SET n:Asset, n:StoredAsset, n:{model_name}", {"id": node_id})
        
        # Latest-Only Batch Events
        await tx.run("""
            MATCH (n {id: $node_id})
            UNWIND $results AS res
            MERGE (n)-[:HAS_INFERENCE {field_name: res.field}]->(e:InferenceEvent)
            SET e.id = $event_id,
                e.handler_name = res.handler,
                e.status = res.status,
                e.updated_at = timestamp(),
                e.field_name = res.field
        """, {"node_id": node_id, "event_id": event_id, "results": results})

        for res in results:
            field = res["field"]
            status = res["status"]
            val = res["result"]
            handler = res.get("handler", "unknown")
            agm_type = res.get("agm_field_type", "PROPERTY")
            rel_type = res.get("rel_type", "RELATED_TO")
            target_label = res.get("target_label", "Tag")
            
            if status == "SUCCESS" and val is not None:
                # 2. Persist to Node Property
                if agm_type == "PROPERTY":
                    await tx.run(f"""
                        MATCH (n {{id: $node_id}})
                        SET n.{field} = $val, n.last_sync = timestamp()
                    """, {"node_id": node_id, "val": val})
                
                # 3. Persist to Multiple Relations (Tags etc)
                elif agm_type == "RELATION":
                    if isinstance(val, list):
                        for item in val:
                            target_id = item.get("id") if isinstance(item, dict) else str(item)
                            target_name = item.get("name") if isinstance(item, dict) else str(item)
                            await tx.run(f"""
                                MATCH (n {{id: $node_id}})
                                MERGE (t:{target_label} {{id: $tid}})
                                ON CREATE SET t.name = $tname
                                MERGE (n)-[r:{rel_type}]->(t)
                                SET r.handler = $handler, r.sync_at = timestamp()
                            """, {"node_id": node_id, "tid": target_id, "tname": target_name, "handler": handler})
                    else:
                        target_id = val.get("id") if isinstance(val, dict) else str(val)
                        target_name = val.get("name") if isinstance(val, dict) else str(val)
                        await tx.run(f"""
                            MATCH (n {{id: $node_id}})
                            MERGE (t:{target_label} {{id: $tid}})
                            ON CREATE SET t.name = $tname
                            MERGE (n)-[r:{rel_type}]->(t)
                            SET r.handler = $handler, r.sync_at = timestamp()
                        """, {"node_id": node_id, "tid": target_id, "tname": target_name, "handler": handler})
