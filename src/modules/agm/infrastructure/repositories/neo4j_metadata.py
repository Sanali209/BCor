from __future__ import annotations
import json
import logging
import uuid
from typing import Any, Dict, List, Optional
from neo4j import AsyncGraphDatabase

logger = logging.getLogger(__name__)

class Neo4jMetadataRepository:
    def __init__(self, uri: str, auth: tuple):
        self.driver = AsyncGraphDatabase.driver(uri, auth=auth)

    async def close(self):
        await self.driver.close()

    async def init_schema(self):
        async with self.driver.session() as session:
            await session.run("CREATE CONSTRAINT asset_id_unique IF NOT EXISTS FOR (n:Asset) REQUIRE n.id IS UNIQUE")
            await session.run("CREATE CONSTRAINT event_id_unique IF NOT EXISTS FOR (n:InferenceEvent) REQUIRE n.id IS UNIQUE")

    async def persist_metadata_batch(self, node_id: str, event_id: str, results: List[Dict[str, Any]], model_name: str = "Asset"):
        """ATOMIC Batch Persistence addressing Q4 (One Event per Batch)."""
        async with self.driver.session() as session:
            await session.execute_write(self._persist_batch_tx, node_id, event_id, results, model_name)

    @staticmethod
    async def _persist_batch_tx(tx, node_id, event_id, results, model_name):
        await tx.run(f"MERGE (n {{id: $id}}) SET n:Asset, n:StoredAsset, n:{model_name}", {"id": node_id})
        
        # 1. Create Single Batch Event
        await tx.run("""
            MATCH (n {id: $node_id})
            MERGE (e:InferenceEvent {id: $event_id})
            SET e.status = 'COMPLETED', e.created_at = timestamp(), e.batch = true
            MERGE (n)-[:HAS_INFERENCE]->(e)
            WITH n, e
            MATCH (n)-[:HAS_INFERENCE]->(prev:InferenceEvent)
            WHERE prev.id <> $event_id
            WITH e, prev ORDER BY prev.created_at DESC LIMIT 1
            MERGE (prev)-[:NEXT_INFERENCE]->(e)
        """, {"node_id": node_id, "event_id": event_id})

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
