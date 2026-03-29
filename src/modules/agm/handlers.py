from __future__ import annotations
from loguru import logger
from dataclasses import asdict
from src.modules.agm import tasks
from src.modules.agm.messages import StoredFieldRecalculationRequested, NodeSyncRequested

async def handle_stored_field_recalc(event: StoredFieldRecalculationRequested, uow=None):
    """Fallback handler for single field events (deprecated)."""
    try:
        if event.use_taskiq:
            await tasks.compute_stored_field.kiq(
                node_id=event.node_id,
                field_name=event.field_name,
                source_value=event.new_source_val,
                context=event.context_metadata
            )
        else:
            await tasks.compute_stored_field(
                node_id=event.node_id,
                field_name=event.field_name,
                source_value=event.new_source_val,
                context=event.context_metadata
            )
    except Exception as e:
        logger.error(f"Failed to process single-field recal for '{event.field_name}': {e}")

async def handle_node_sync_requested(event: NodeSyncRequested, uow=None):
    """Primary Batch Handler addressing Windows stability issues."""
    try:
        fields_data = [asdict(f) for f in event.fields]
        if event.use_taskiq:
            await tasks.sync_node_metadata.kiq(
                node_id=event.node_id,
                fields=fields_data,
                mime_type=event.mime_type
            )
            logger.info(f"Offloaded BATC metadata sync for {event.node_id} to TaskIQ.")
        else:
            await tasks.sync_node_metadata(
                node_id=event.node_id,
                fields=fields_data,
                mime_type=event.mime_type
            )
    except Exception as e:
        logger.error(f"Failed to process batch node sync for {event.node_id}: {e}")
