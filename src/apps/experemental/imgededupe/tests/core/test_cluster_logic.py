import pytest
import os
from unittest.mock import MagicMock
from src.apps.experemental.imgededupe.core.cluster_services import GraphBuilder, ClusterReconciler
from src.apps.experemental.imgededupe.core.models import FileRelation, RelationType

@pytest.fixture
def mock_db():
    db = MagicMock()
    return db

@pytest.fixture
def mock_repo():
    repo = MagicMock()
    return repo

def test_graph_builder_exact_hash(mock_db):
    gb = GraphBuilder(mock_db)
    
    files = [
        {'id': 1, 'path': 'a.png', 'phash': 'hash1'},
        {'id': 2, 'path': 'b.png', 'phash': 'hash1'},
        {'id': 3, 'path': 'c.png', 'phash': 'hash2'},
    ]
    
    # Exact hash clustering enabled by default
    criteria = {'exact_hash': True}
    components = gb.build_graph_and_find_components(files, criteria)
    
    assert len(components) == 1
    assert set(components[0]) == {'a.png', 'b.png'}

def test_graph_builder_with_relations(mock_db, mock_repo):
    gb = GraphBuilder(mock_db, mock_repo)
    
    files = [
        {'id': 1, 'path': 'a.png', 'phash': 'h1'},
        {'id': 2, 'path': 'b.png', 'phash': 'h2'},
        {'id': 3, 'path': 'c.png', 'phash': 'h3'},
    ]
    
    # Simulate DB relations
    mock_repo.get_all_relations.return_value = [
        FileRelation(id1=1, id2=2, relation_type=RelationType.NEW_MATCH, distance=2.0)
    ]
    
    # Try with type disabled
    criteria = {'exact_hash': False, 'new_match': False}
    components = gb.build_graph_and_find_components(files, criteria)
    assert len(components) == 0
    
    # Try with type enabled
    criteria = {'exact_hash': False, 'new_match': True}
    components = gb.build_graph_and_find_components(files, criteria)
    assert len(components) == 1
    assert set(components[0]) == {'a.png', 'b.png'}

def test_graph_builder_negative_edges(mock_db, mock_repo):
    gb = GraphBuilder(mock_db, mock_repo)
    
    files = [
        {'id': 1, 'path': 'a.png', 'phash': 'hash1'},
        {'id': 2, 'path': 'b.png', 'phash': 'hash1'},
    ]
    
    # Relation says NOT duplicate
    mock_repo.get_all_relations.return_value = [
        FileRelation(id1=1, id2=2, relation_type=RelationType.NOT_DUPLICATE)
    ]
    
    # criteria says 'exact_hash' is True, but 'not_duplicate' (negative) should break it
    criteria = {'exact_hash': True, 'not_duplicate': False}
    components = gb.build_graph_and_find_components(files, criteria)
    
    assert len(components) == 0

def test_reconciler_new_clusters(mock_db):
    reconciler = ClusterReconciler(mock_db)
    
    mock_db.get_all_cluster_members.return_value = {}
    mock_db.get_clusters.return_value = []
    
    components = [['a.png', 'b.png']]
    file_map = {
        'a.png': {'id': 1, 'path': 'a.png'},
        'b.png': {'id': 2, 'path': 'b.png'}
    }
    
    results = reconciler.reconcile(components, file_map)
    
    assert len(results) == 1
    assert results[0]['id'] < 0 # Transient ID
    assert len(results[0]['files']) == 2

def test_reconciler_sticky_cluster(mock_db):
    reconciler = ClusterReconciler(mock_db)
    
    # Existing cluster 10 has a.png
    mock_db.get_all_cluster_members.return_value = {'a.png': 10}
    mock_db.get_clusters.return_value = [{'id': 10, 'name': 'Cluster 10', 'target_folder': '/tmp'}]
    
    # Graph now says a.png is matched with c.png
    components = [['a.png', 'c.png']]
    file_map = {
        'a.png': {'id': 1, 'path': 'a.png'},
        'c.png': {'id': 3, 'path': 'c.png'}
    }
    
    results = reconciler.reconcile(components, file_map)
    
    # Result should be merged into cluster 10
    assert len(results) == 1
    assert results[0]['id'] == 10
    assert {f['path'] for f in results[0]['files']} == {'a.png', 'c.png'}
    
    # Verify persistence call for NEW member c.png
    mock_db.add_cluster_members.assert_called_with(10, ['c.png'])
