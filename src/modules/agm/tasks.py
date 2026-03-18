from src.adapters.taskiq_broker import broker


@broker.task
async def compute_stored_field(node_id: str, field_name: str, source_value: str):
    """Background task to recalculate a stored field.

    This task is triggered when a source field changes. It is 
    responsible for performing heavy computations (e.g., embedding 
    generation) and updating the graph database.

    Args:
        node_id: Unique ID of the node to update.
        field_name: The name of the stored field to compute.
        source_value: The new value of the source field used as input.
    """
    # This would calculate embedding and update Neo4j
    # Then emit a Bubus event.
    pass
