import pytest
import asyncio
import os
import json
import base64
from typing import Any
from neo4j import AsyncGraphDatabase
import pytest_asyncio
from src.modules.agm.tasks import compute_stored_field

@pytest_asyncio.fixture
async def neo4j_session():
    uri = os.getenv("NEO4J_URI", "bolt://127.0.0.1:7687")
    auth = (os.getenv("NEO4J_USER", "neo4j"), os.getenv("NEO4J_PASSWORD", "password"))
    async with AsyncGraphDatabase.driver(uri, auth=auth) as driver:
        async with driver.session() as session:
            # Full cleanup BEFORE each test for maximum clarity. 
            # We leave the DB as is AFTER the test for debugging purposes.
            await session.run("MATCH (n) DETACH DELETE n")
            # Create a base Asset node first. The worker should upgrade it to :ImageAsset later.
            await session.run("CREATE (:Asset {id: 'regression-asset-1'})")
            yield session

@pytest.mark.asyncio
async def test_metadata_primitive_type_regression(neo4j_session):
    """
    FAILURE CASE: f_number and camera_make should NOT contain a full JSON dictionary.
    They should be primitives (float, str).
    """
    repo_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    sample_path = os.path.join(repo_dir, "tests", "test_data", "images", "37948324394_38056398fb_b.webp")
    
    # 1. Test f_number (should be float)
    await getattr(compute_stored_field, "coroutine", compute_stored_field)(
        node_id="regression-asset-1",
        field_name="f_number",
        source_value=f"file://{sample_path}",
        mime_type="image/webp",
        handler="Pyexiv2Smart",
        model="ImageAsset",
        priority=0
    )
    
    # 2. Test camera_make (should be str)
    await getattr(compute_stored_field, "coroutine", compute_stored_field)(
        node_id="regression-asset-1",
        field_name="camera_make",
        source_value=f"file://{sample_path}",
        mime_type="image/webp",
        handler="Pyexiv2Smart",
        model="ImageAsset",
        priority=0
    )
    
    # Note: We removed the HAS_WD_TAG assertion here because Pyexiv2Smart does not generate tags.
    result = await neo4j_session.run(
        "MATCH (n {id: 'regression-asset-1'}) RETURN n.f_number as f, n.camera_make as m"
    )
    record = await result.single()
    
    f_val = record["f"]
    m_val = record["m"]
    
    # EXPECTED FAILURES if bugs persist:
    # 1. These will be JSON strings containing dictionaries
    # 2. Or if dumped as dict, they will be strings starting with '{'
    
    assert f_val is None or isinstance(f_val, (float, int)), f"f_number should be numeric or None, got {type(f_val)}: {f_val}"
    assert m_val is None or isinstance(m_val, str), f"camera_make should be string or None, got {type(m_val)}: {m_val}"
    if m_val is not None:
        assert not str(m_val).startswith("{"), f"camera_make should not be a JSON dict: {m_val}"

@pytest.mark.asyncio
async def test_binary_serialization_regression(neo4j_session):
    """
    FAILURE CASE: thumbnail_bytes should NOT be '[object Object]' or serialized badly.
    It should be a Base64 encoded string or a raw byte-safe format.
    """
    repo_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    sample_path = os.path.join(repo_dir, "tests", "test_data", "images", "37948324394_38056398fb_b.webp")
    
    # 1. Compute Hash first
    await getattr(compute_stored_field, "coroutine", compute_stored_field)(
        node_id="regression-asset-1",
        field_name="content_hash",
        source_value=f"file://{sample_path}",
        mime_type="image/webp",
        handler="ContentHashHandler",
        model="ImageAsset"
    )

    # 2. Fetch the computed hash from the DB so we can pass it in the context kwargs
    result = await neo4j_session.run("MATCH (n {id: 'regression-asset-1'}) RETURN n.content_hash as h")
    content_hash = (await result.single())["h"]
    assert content_hash, "content_hash must be present for CAS lookup"

    # 3. Compute Thumbnail using the hash
    await getattr(compute_stored_field, "coroutine", compute_stored_field)(
        node_id="regression-asset-1",
        field_name="thumbnails_ready",
        source_value=f"file://{sample_path}",
        mime_type="image/webp",
        handler="ThumbnailHandler",
        model="ImageAsset",
        priority=0,
        content_hash=content_hash  # MUST pass this to context for ThumbnailHandler
    )
    
    # 4. Verify in DB (should be base64 data URI)
    result = await neo4j_session.run(
        "MATCH (n {id: 'regression-asset-1'}) RETURN n.thumbnails_ready as ready"
    )
    record = await result.single()
    assert record["ready"] is True, "thumbnails_ready flag should be True"

    # 4. Verify in CAS (Local Filesystem)
    from src.core.storage import get_cas_path
    from pathlib import Path
    
    # Use repo root for storage context if needed, but get_cas_path handles defaults
    thumb_path = get_cas_path("data", content_hash, "medium")
    assert thumb_path.exists(), f"Thumbnail file should exist at {thumb_path}"
    assert thumb_path.stat().st_size > 0, "Thumbnail file should not be empty"

@pytest.mark.asyncio
async def test_blip_embedding_regression(neo4j_session):
    """
    FAILURE CASE: blip_embedding should NOT be empty [].
    """
    repo_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    sample_path = os.path.join(repo_dir, "tests", "samples", "test_diagnostic.webp")
    
    await getattr(compute_stored_field, "coroutine", compute_stored_field)(
        node_id="regression-asset-1",
        field_name="blip_embedding",
        source_value=f"file://{sample_path}",
        mime_type="image/webp",
        handler="BLIP",
        model="ImageAsset",
        priority=0
    )
    
    # 3. Verify in DB (should be list of floats >= 512 dims)
    # Deep Diagnostics: Dump entire graph for debugging
    all_nodes = await neo4j_session.run("MATCH (n)-[r]->(m) RETURN n.id as from, type(r) as rel, m.id as to, labels(m) as labels")
    items = [dict(r) async for r in all_nodes]
    print(f"\nDEBUG GRAPH CONTENT: {items}")
    
    result = await neo4j_session.run(
        "MATCH (n {id: 'regression-asset-1'}) RETURN n.blip_embedding as e"
    )
    record = await result.single()
    emb_json = record["e"]
    
    assert emb_json is not None
    emb = emb_json # Result is already a list from worker
    assert isinstance(emb, list)
    assert len(emb) == 768, f"BLIP embedding should have 768 dims, got {len(emb) if emb else 0}"

@pytest.mark.asyncio
async def test_inference_event_provenance_regression(neo4j_session):
    """
    FAILURE CASE: InferenceEvent should be linked to the result (Tag) via :GENERATED
    and to the previous InferenceEvent via :NEXT_INFERENCE.
    """
    repo_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    sample_path = os.path.join(repo_dir, "tests", "test_data", "images", "37948324394_38056398fb_b.webp")
    
    # 1. First inference (tags) - use wd_tags to trigger HAS_WD_TAG rel
    await getattr(compute_stored_field, "coroutine", compute_stored_field)(
        node_id="regression-asset-1",
        field_name="wd_tags",
        source_value=f"file://{sample_path}",
        mime_type="image/webp",
        handler="SmilingWolf",
        model="ImageAsset",
        agm_field_type="RELATION",
        rel_type="HAS_WD_TAG",
        target_label="Tag",
        priority=0
    )
    
    # 2. Verify Tag linking in Neo4j (DECLARATIVE: ImageAsset.wd_tags -> HAS_WD_TAG)
    result = await neo4j_session.run(
        """
        MATCH (n {id: 'regression-asset-1'})-[:HAS_WD_TAG]->(t)
        WHERE t.id STARTS WITH 'auto/wd_tag/'
        RETURN count(t) as tag_count
        """
    )
    record = await result.single()
    assert record["tag_count"] > 0, "ImageAsset should be linked to generated Tags via HAS_WD_TAG"
    
    # 3. Second inference (blip)
    await getattr(compute_stored_field, "coroutine", compute_stored_field)(
        node_id="regression-asset-1",
        field_name="blip_embedding",
        source_value=f"file://{sample_path}",
        mime_type="image/webp",
        handler="BLIP",
        model="ImageAsset",
        priority=0
    )
    
    # Verify GENERATED link for tags (SmilingWolf)
    result_gen = await neo4j_session.run(
        """
        MATCH (e:InferenceEvent {handler_name: 'SmilingWolf'})-[:GENERATED]->(t)
        RETURN count(t) as tag_count
        """
    )
    record_gen = await result_gen.single()
    assert record_gen["tag_count"] > 0, "InferenceEvent should be linked to generated Tags"
    
    # Verify NEXT_INFERENCE link
    result_next = await neo4j_session.run(
        """
        MATCH (e1:InferenceEvent {handler_name: 'SmilingWolf'})-[:NEXT_INFERENCE]->(e2:InferenceEvent {handler_name: 'BLIP'})
        RETURN e1, e2
        """
    )
    record_next = await result_next.single()
    assert record_next is not None, "Consecutive InferenceEvents should be linked via NEXT_INFERENCE"

@pytest.mark.asyncio
async def test_inference_event_metadata_regression(neo4j_session):
    """
    FAILURE CASE: InferenceEvent should have field_name and created_at.
    """
    repo_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    sample_path = os.path.join(repo_dir, "tests", "test_data", "images", "37948324394_38056398fb_b.webp")
    
    await getattr(compute_stored_field, "coroutine", compute_stored_field)(
        node_id="regression-asset-1",
        field_name="f_number",
        source_value=f"file://{sample_path}",
        mime_type="image/webp",
        handler="Pyexiv2Smart",
        model="ImageAsset",
        priority=0
    )
    
    result = await neo4j_session.run(
        "MATCH (e:InferenceEvent {handler_name: 'Pyexiv2Smart'}) RETURN e.field_name as f, e.created_at as t"
    )
    record = await result.single()
    assert record["f"] == "f_number", f"InferenceEvent should store field_name 'f_number', got {record['f']}"
    assert record["t"] is not None, "InferenceEvent should have a created_at timestamp"
