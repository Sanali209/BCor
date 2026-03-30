from __future__ import annotations
import asyncio
import logging
import uuid
import os
from dataclasses import asdict
from typing import Any, Dict, List, Optional, get_type_hints, get_origin, get_args

# BCor Imports
from src.modules.agm.metadata import Stored, OnComplete, Rel
from src.modules.agm.infrastructure.repositories.neo4j_metadata import Neo4jMetadataRepository
from src.adapters.taskiq_broker import broker

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global concurrency guard for heavy AI tasks (Windows stability)
_HEAVY_TASK_SEMAPHORE = asyncio.Semaphore(1)

@broker.task
async def compute_stored_field(
    node_id: str,
    field_name: str,
    source_value: Any,
    handler: Optional[str] = None,
    context: Optional[Dict[str, Any]] = None,
    **kwargs: Any
) -> None:
    """Model-Aware Metadata Worker for BCor (Single Field)."""
    priority = kwargs.get("priority", 0)
    
    # Sequential Execution for high-priority tasks (e.g., Vision/Ollama)
    if priority >= 10:
        async with _HEAVY_TASK_SEMAPHORE:
            logger.info(f"[AGM:SEQUENTIAL] START field={field_name} node={node_id}")
            result = await _process_single_field(node_id, field_name, source_value, handler, context, **kwargs)
            logger.info(f"[AGM:SEQUENTIAL] END field={field_name}")
    else:
        result = await _process_single_field(node_id, field_name, source_value, handler, context, **kwargs)
    
    # Latest-Only Persistence
    repo = _get_repo()
    try:
        event_id = str(uuid.uuid4())
        await repo.persist_metadata(
            node_id=node_id,
            event_id=event_id,
            handler=handler or field_name,
            field=field_name,
            status="SUCCESS" if result not in (None, "", [], {}) else "EMPTY",
            props=result,
            model_name=kwargs.get("model_name", "Asset")
        )
    finally:
        await repo.close()
    return result

@broker.task
async def sync_node_metadata(
    node_id: str,
    fields: List[Dict[str, Any]],
    mime_type: str = "image/webp",
    model_name: str = "Asset"
) -> None:
    """Batch Metadata Worker (Addressing Q3, Q4, Q7)."""
    logger.info(f"Batch Sync started for {node_id} ({len(fields)} fields)")
    
    results = []
    for f_info in fields:
        field_name = f_info["field_name"]
        try:
            res = await _process_single_field(
                node_id, 
                field_name, 
                f_info["source_value"], 
                f_info.get("handler"), 
                f_info.get("context_metadata"),
                mime_type=mime_type,
                model_name=model_name
            )
            results.append({
                "field": field_name,
                "status": "SUCCESS" if res not in (None, "", [], {}) else "EMPTY",
                "result": res,
                "handler": f_info.get("handler") or field_name,
                "agm_field_type": (f_info.get("context_metadata") or {}).get("agm_field_type", "PROPERTY"),
                "rel_type": (f_info.get("context_metadata") or {}).get("rel_type", "RELATED_TO"),
                "target_label": (f_info.get("context_metadata") or {}).get("target_label", "Tag")
            })
        except Exception as e:
            logger.error(f"Field {field_name} failed in batch: {e}")
            results.append({"field": field_name, "status": "FAILED", "result": None})

    repo = _get_repo()
    try:
        event_id = str(uuid.uuid4())
        await repo.persist_metadata_batch(node_id, event_id, results, model_name=model_name)
    finally:
        await repo.close()

async def _process_single_field(node_id, field_name, source_value, handler, context, **kwargs):
    processing_context = (context or {}).copy()
    processing_context.update(kwargs)
    
    target_model_name = processing_context.get("model_name") or processing_context.get("model") or "Asset"
    actual_mime = processing_context.get("mime_type") or "image/webp"
    
    # Introspection
    from src.modules.assets.domain import models
    model_cls = getattr(models, target_model_name, None)
    if model_cls:
        try:
            hints = get_type_hints(model_cls, include_extras=True)
            if field_name in hints:
                hint = hints[field_name]
                meta = getattr(hint, "__metadata__", [])
                decl_rel = next((m for m in meta if isinstance(m, Rel)), None)
                if decl_rel: processing_context["rel_type"] = decl_rel.type
                decl_on_complete = next((m for m in meta if isinstance(m, OnComplete)), None)
                if decl_on_complete: processing_context["on_complete"] = decl_on_complete
        except Exception: pass

    # Handler Execution
    handler_name = handler or processing_context.get("handler") or field_name
    processor = None
    try:
        from src.modules.assets.infrastructure.providers import AssetsInfrastructureProvider
        registry = AssetsInfrastructureProvider().provide_handler_registry()
        processor = registry.resolve(actual_mime, handler_name=handler_name)
    except Exception: pass

    if not processor:
        # Fallback Map logic...
        fallback_map = {
            "clip_embedding": "src.modules.assets.infrastructure.handlers.clip.CLIPHandler",
            "exif_data": "src.modules.assets.infrastructure.handlers.smart_exif.Pyexiv2SmartHandler"
        }
        if handler_name in fallback_map:
            import importlib
            m_path, c_name = fallback_map[handler_name].rsplit(".", 1)
            processor = getattr(importlib.import_module(m_path), c_name)

    if not processor: return None

    try:
        result = await processor.run(source_value, processing_context)
        return result
    except Exception as e:
        logger.error(f"Handler {handler_name} failed: {e}")
        raise

def _get_repo():
    return Neo4jMetadataRepository(
        uri=os.getenv("NEO4J_URI", "bolt://127.0.0.1:7687"),
        auth=(os.getenv("NEO4J_USER", "neo4j"), os.getenv("NEO4J_PASSWORD", "password"))
    )
