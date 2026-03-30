import pytest
from unittest.mock import MagicMock, AsyncMock
from src.modules.agm.query import CypherQuery
from src.modules.assets.domain.models import Asset

@pytest.fixture
def mock_mapper():
    mapper = MagicMock()
    return mapper

def test_query_contains(mock_mapper):
    query = CypherQuery(mock_mapper, Asset).contains("name", "test")
    cypher, params = query.build_cypher()
    
    assert "WHERE n.name CONTAINS $p_name_contains" in cypher
    assert params["p_name_contains"] == "test"

def test_query_range(mock_mapper):
    query = CypherQuery(mock_mapper, Asset).range("size", 100, 500)
    cypher, params = query.build_cypher()
    
    assert "WHERE n.size >= $p_size_start AND n.size <= $p_size_end" in cypher
    assert params["p_size_start"] == 100
    assert params["p_size_end"] == 500

def test_query_near(mock_mapper):
    # Vector index for Asset.embedding is 384 dims
    vector = [0.1] * 384
    query = CypherQuery(mock_mapper, Asset).near("embedding", vector, limit=10)
    cypher, params = query.build_cypher()
    
    # Vector search in Neo4j 5.x uses CALL db.index.vector.queryNodes
    # The index name convention from AGMSchemaManager is vec_{Label}_{Field}
    assert "CALL db.index.vector.queryNodes('vec_Asset_embedding', $p_limit, $p_vector) YIELD node AS n, score" in cypher
    assert params["p_limit"] == 10
    assert params["p_vector"] == vector
    # Labels should still be returned
    assert "RETURN n, labels(n) as labels, elementId(n) as id, score" in cypher

def test_query_combined(mock_mapper):
    query = CypherQuery(mock_mapper, Asset).where(mime_type="image/jpeg").contains("name", "vaca")
    cypher, params = query.build_cypher()
    
    assert "WHERE n.mime_type = $p_mime_type AND n.name CONTAINS $p_name_contains" in cypher
