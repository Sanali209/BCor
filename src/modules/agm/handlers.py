from loguru import logger
from src.modules.agm import tasks
from src.modules.agm.messages import StoredFieldRecalculationRequested


async def handle_stored_field_recalc(
    event: StoredFieldRecalculationRequested, uow=None
):
    """
    Subscribes to StoredFieldRecalculationRequested events from the MessageBus
    and delegates the actual calculation to the TaskIQ background worker.
    """
    try:
        await tasks.compute_stored_field.kiq(
            event.node_id, event.field_name, event.new_source_val
        )
        logger.info(
            f"Dispatched TaskIQ job for stored field '{event.field_name}' on node '{event.node_id}'."
        )
    except Exception as e:
        logger.error(f"Failed to dispatch TaskIQ job for '{event.field_name}': {e}")
