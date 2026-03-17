from src.adapters.taskiq_broker import broker


@broker.task
async def compute_stored_field(node_id: str, field_name: str, source_value: str):
    # This would calculate embedding and update Neo4j
    # Then emit a Bubus event.
    pass
