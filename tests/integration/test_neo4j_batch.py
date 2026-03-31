import asyncio
import uuid
import pytest
from src.modules.agm.infrastructure.repositories.neo4j_metadata import Neo4jMetadataRepository

@pytest.mark.asyncio
async def test_persist_batch_with_dict_fails():
    """TDD Step 1: Confirm that current repo fails with CypherTypeError for dicts."""
    repo = Neo4jMetadataRepository("bolt://localhost:7687", auth=("neo4j", "password"))
    await repo.init_schema()
    
    node_id = str(uuid.uuid4())
    # 1. Create initial node
    async with repo.driver.session() as session:
        await session.run("CREATE (n:Asset {id: $id, name: 'TDD Test'})", {"id": node_id})
    
    # 2. Results with a dictionary (This should fail in Neo4j)
    results = [
        {
            "id": str(uuid.uuid4()),
            "field": "exif_data",
            "status": "SUCCESS",
            "result": {"make": "Sony", "model": "A7RIII"}, # DICTIONARY -> FAIL
            "handler": "Pyexiv2Smart",
            "agm_field_type": "PROPERTY"
        }
    ]
    
    # 3. Attempt batch persistence
    try:
        await repo.persist_metadata_batch(node_id, "", results)
        # If it doesn't fail, our TDD 'Red' state is not reached or repo is already fixed
    except Exception as e:
        print(f"\nCaught expected error: {type(e).__name__}: {e}")
        assert "Property values can only be of primitive types" in str(e) or "CypherTypeError" in type(e).__name__
    finally:
        await repo.close()

if __name__ == "__main__":
    asyncio.run(test_persist_batch_with_dict_fails())
