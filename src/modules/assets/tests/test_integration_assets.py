"""Integration tests for the Assets module against a real Neo4j instance.

Prerequisites:
    docker compose -f docker-compose.agm.yml up -d

These tests are SKIPPED automatically if Neo4j is not available at localhost:7687.
They cover:
    1. Vector index creation via APOC (Neo4j 5.12 compatible)
    2. Asset CRUD roundtrip (save + load)
    3. Tag hierarchy (PARENT_TAG relationship)
    4. Hierarchical Album (CHILD_OF relationship)
    5. Annotation roundtrip (BoundingBox + Caption)
    6. ContentChunk storage
    7. Semantic dedup — L1 (content_hash) and L2 (cosine similarity)
    8. SmartAlbum criteria persistence
    9. TagMerger + persist result as Tag nodes
    10. Full-pipeline smoke test
"""
from __future__ import annotations

import asyncio
import json
import uuid
from typing import AsyncGenerator
from unittest.mock import AsyncMock, MagicMock

import pytest
from neo4j import AsyncGraphDatabase, AsyncDriver, AsyncSession
from src.modules.agm.mapper import AGMMapper
from src.modules.agm.schema import AGMSchemaManager
from src.modules.assets.domain.factory import AssetFactory
from src.modules.assets.domain.models import (
    Album,
    BoundingBoxAnnotation,
    CaptionAnnotation,
    ContentChunk,
    DocumentAsset,
    ImageAsset,
    SmartAlbum,
    Tag,
    VideoAsset,
)
from src.modules.assets.domain.services import (
    AnnotationService,
    ContentChunker,
    TagMerger,
)
from src.modules.assets.infrastructure.dedup import SemanticDuplicateFinder


# ─── Fixtures ─────────────────────────────────────────────────────────────────

NEO4J_URI = "bolt://localhost:7687"
NEO4J_AUTH = ("neo4j", "password")

_CLEANUP_CYPHER = (
    "MATCH (n) WHERE "
    "n:Asset OR n:ImageAsset OR n:VideoAsset OR n:DocumentAsset "
    "OR n:Tag OR n:Album OR n:SmartAlbum OR n:ContentChunk "
    "OR n:BoundingBoxAnnotation OR n:CaptionAnnotation "
    "OR n:SingleLabelAnnotation OR n:Annotation "
    "DETACH DELETE n"
)


# All fixtures MUST be function-scoped on Windows to avoid event-loop conflicts.
@pytest.fixture
async def neo4j_driver() -> AsyncGenerator[AsyncDriver, None]:
    driver = AsyncGraphDatabase.driver(NEO4J_URI, auth=NEO4J_AUTH)
    for _ in range(15):
        try:
            await driver.verify_connectivity()
            break
        except Exception:
            await asyncio.sleep(2)
    else:
        await driver.close()
        pytest.skip("Neo4j not available at localhost:7687")
    yield driver
    await driver.close()


@pytest.fixture
async def session(neo4j_driver: AsyncDriver) -> AsyncGenerator[AsyncSession, None]:
    async with neo4j_driver.session() as s:
        await s.run(_CLEANUP_CYPHER)
        yield s


@pytest.fixture
async def mapper(neo4j_driver: AsyncDriver) -> AGMMapper:
    container = MagicMock()
    bus = AsyncMock()
    schema_manager = AGMSchemaManager(neo4j_driver)
    m = AGMMapper(container, bus, schema_manager=schema_manager)
    
    # 2. Registration (now triggers schema sync)
    await m.register_subclass("ImageAsset", ImageAsset)
    await m.register_subclass("VideoAsset", VideoAsset)
    await m.register_subclass("DocumentAsset", DocumentAsset)
    await m.register_subclass("Tag", Tag)
    await m.register_subclass("Album", Album)
    await m.register_subclass("SmartAlbum", SmartAlbum)
    await m.register_subclass("ContentChunk", ContentChunk)
    
    return m


@pytest.fixture
def annotation_svc() -> AnnotationService:
    return AnnotationService()


# ─── 1. Declarative Schema Manager (Implicitly Tested) ─────────────────────────

@pytest.mark.asyncio
async def test_declarative_indexes_are_created(mapper: AGMMapper, session: AsyncSession):
    """Verifies that vector and unique indexes are created automatically with polling."""
    # Indexes are created asynchronously in Neo4j, so we poll for 5 seconds
    for _ in range(10):
        # Check Vector Index (dims=384 for ImageAsset)
        result = await session.run("SHOW INDEXES WHERE name = 'vec_ImageAsset_embedding'")
        records = await result.data()
        if len(records) == 1:
            break
        await asyncio.sleep(0.5)
    else:
        pytest.fail("Vector index vec_ImageAsset_embedding not found after timeout")

    # Check Uniqueness Constraint (for Tag.id)
    result = await session.run("SHOW CONSTRAINTS WHERE name = 'uniq_Tag_id'")
    records = await result.data()
    assert len(records) == 1
    assert records[0]["type"] == "UNIQUENESS"


# ─── 2. Asset CRUD Roundtrip ──────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_image_asset_save_and_load(mapper: AGMMapper, session: AsyncSession):
    """ImageAsset fields are persisted and readable from Neo4j."""
    asset = ImageAsset(
        id=str(uuid.uuid4()),
        uri="file:///photos/cat.jpg",
        name="cat.jpg",
        mime_type="image/jpeg",
        description="A tabby cat",
        content_hash="sha256:abc123",
        width=1920,
        height=1080,
    )
    await mapper.save(asset, session=session)

    result = await session.run(
        "MATCH (n:ImageAsset {id: $id}) RETURN properties(n) AS props",
        {"id": asset.id},
    )
    record = await result.single()
    assert record is not None
    props = record["props"]
    assert props["uri"] == "file:///photos/cat.jpg"
    assert props["content_hash"] == "sha256:abc123"
    assert props["width"] == 1920
    assert props["mime_type"] == "image/jpeg"


@pytest.mark.asyncio
async def test_asset_factory_and_save_video(mapper: AGMMapper, session: AsyncSession):
    """AssetFactory creates VideoAsset that can be persisted."""
    asset = AssetFactory.create(
        "https://www.youtube.com/watch?v=dQw4w9WgXcQ", name="Rick Roll"
    )
    assert isinstance(asset, VideoAsset)
    asset.description = "Classic meme video"

    await mapper.save(asset, session=session)

    result = await session.run(
        "MATCH (n:VideoAsset {id: $id}) RETURN properties(n) AS props",
        {"id": asset.id},
    )
    record = await result.single()
    assert record is not None
    assert record["props"]["mime_type"] == "video/youtube"


# ─── 3. Tag Hierarchy ─────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_tag_hierarchy_parent_child(mapper: AGMMapper, session: AsyncSession):
    """Tags linked via PARENT_TAG relationship are queryable."""
    parent_tag = Tag(id=str(uuid.uuid4()), name="Animals")
    child_tag = Tag(id=str(uuid.uuid4()), name="Cats", parent=parent_tag)

    await mapper.save(parent_tag, session=session)
    await mapper.save(child_tag, session=session)

    result = await session.run(
        "MATCH (child:Tag {name: 'Cats'})-[:PARENT_TAG]->(parent:Tag {name: 'Animals'}) "
        "RETURN parent.name AS parent, child.name AS child"
    )
    record = await result.single()
    assert record is not None
    assert record["parent"] == "Animals"
    assert record["child"] == "Cats"


@pytest.mark.asyncio
async def test_asset_linked_to_tags(mapper: AGMMapper, session: AsyncSession):
    """HAS_TAG relationship is created between ImageAsset and Tag."""
    tag = Tag(id=str(uuid.uuid4()), name="Nature")
    asset = ImageAsset(
        id=str(uuid.uuid4()), uri="file:///mountain.jpg",
        name="mountain.jpg", mime_type="image/jpeg",
        tags=[tag],
    )

    await mapper.save(tag, session=session)
    await mapper.save(asset, session=session)

    result = await session.run(
        "MATCH (a:ImageAsset)-[:HAS_TAG]->(t:Tag {name: 'Nature'}) RETURN a.uri AS uri"
    )
    record = await result.single()
    assert record is not None
    assert record["uri"] == "file:///mountain.jpg"


# ─── 4. Album Hierarchy ───────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_album_hierarchy_child_of(mapper: AGMMapper, session: AsyncSession):
    """Albums nested via CHILD_OF relationship are queryable."""
    root = Album(id=str(uuid.uuid4()), name="Holidays")
    child = Album(id=str(uuid.uuid4()), name="Greece 2024", parent=root)

    await mapper.save(root, session=session)
    await mapper.save(child, session=session)

    result = await session.run(
        "MATCH (c:Album {name: 'Greece 2024'})-[:CHILD_OF]->(p:Album {name: 'Holidays'}) "
        "RETURN p.name AS parent"
    )
    record = await result.single()
    assert record is not None
    assert record["parent"] == "Holidays"


@pytest.mark.asyncio
async def test_smart_album_criteria_roundtrip(mapper: AGMMapper, session: AsyncSession):
    """SmartAlbum JSON criteria roundtrip through Neo4j."""
    criteria = {"mime": "image/*", "tags": ["vacation"], "rating_min": 4}
    album = SmartAlbum(
        id=str(uuid.uuid4()),
        name="Beach Pics",
        filter_criteria=json.dumps(criteria),
    )
    await mapper.save(album, session=session)

    result = await session.run(
        "MATCH (n:SmartAlbum {id: $id}) RETURN n.filter_criteria AS fc",
        {"id": album.id},
    )
    record = await result.single()
    assert record is not None
    parsed = json.loads(record["fc"])
    assert parsed["mime"] == "image/*"
    assert "vacation" in parsed["tags"]


# ─── 5. Annotation Roundtrip ──────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_bounding_box_annotation_roundtrip(
    mapper: AGMMapper, session: AsyncSession, annotation_svc: AnnotationService
):
    """BoundingBoxAnnotation fields are persisted correctly."""
    asset = ImageAsset(
        id=str(uuid.uuid4()), uri="file:///dog.jpg",
        name="dog.jpg", mime_type="image/jpeg",
    )
    ann = annotation_svc.add_bbox(
        asset, class_label="dog", x=0.1, y=0.2, w=0.3, h=0.4, confidence=0.92
    )

    await mapper.save(asset, session=session)
    await mapper.save(ann, session=session)

    result = await session.run(
        "MATCH (n:BoundingBoxAnnotation {asset_id: $aid}) RETURN properties(n) AS props",
        {"aid": asset.id},
    )
    record = await result.single()
    assert record is not None
    props = record["props"]
    assert props["class_label"] == "dog"
    assert abs(props["confidence"] - 0.92) < 0.001


@pytest.mark.asyncio
async def test_caption_annotation_roundtrip(
    mapper: AGMMapper, session: AsyncSession, annotation_svc: AnnotationService
):
    """CaptionAnnotation text and language are persisted."""
    asset = ImageAsset(
        id=str(uuid.uuid4()), uri="file:///sunset.jpg",
        name="sunset.jpg", mime_type="image/jpeg",
    )
    cap = annotation_svc.add_caption(
        asset, text="A beautiful sunset over the ocean", language="en"
    )

    await mapper.save(asset, session=session)
    await mapper.save(cap, session=session)

    result = await session.run(
        "MATCH (n:CaptionAnnotation {asset_id: $aid}) RETURN n.text AS text, n.language AS lang",
        {"aid": asset.id},
    )
    record = await result.single()
    assert record is not None
    assert record["text"] == "A beautiful sunset over the ocean"
    assert record["lang"] == "en"


# ─── 6. ContentChunk Storage ──────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_content_chunks_stored_with_parent_ref(
    mapper: AGMMapper, session: AsyncSession
):
    """ContentChunker output is persisted with correct asset_id and chunk_index."""
    asset = AssetFactory.create("file:///report.pdf")
    assert isinstance(asset, DocumentAsset)

    chunker = ContentChunker(chunk_size=50, overlap=10)
    chunks = chunker.chunk(
        asset_id=asset.id,
        text="This is a long document for chunking tests. " * 10,
    )
    assert len(chunks) > 1

    await mapper.save(asset, session=session)
    for chunk in chunks:
        await mapper.save(chunk, session=session)

    result = await session.run(
        "MATCH (c:ContentChunk {asset_id: $aid}) RETURN count(c) AS cnt",
        {"aid": asset.id},
    )
    record = await result.single()
    assert record is not None
    assert record["cnt"] == len(chunks)


# ─── 7. L1 Dedup ──────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_l1_dedup_finds_exact_duplicates_in_graph(
    mapper: AGMMapper, session: AsyncSession
):
    """Assets with identical content_hash are found as duplicates."""
    hash_val = "sha256:deadbeef"
    a1 = ImageAsset(id=str(uuid.uuid4()), uri="file:///a.jpg", name="a.jpg",
                    mime_type="image/jpeg", content_hash=hash_val)
    a2 = ImageAsset(id=str(uuid.uuid4()), uri="file:///b.jpg", name="b.jpg",
                    mime_type="image/jpeg", content_hash=hash_val)
    unique = ImageAsset(id=str(uuid.uuid4()), uri="file:///c.jpg", name="c.jpg",
                        mime_type="image/jpeg", content_hash="sha256:unique999")

    for a in [a1, a2, unique]:
        await mapper.save(a, session=session)

    result = await session.run(
        "MATCH (n:ImageAsset) WHERE n.content_hash = $h RETURN n.id AS id",
        {"h": hash_val},
    )
    records = await result.data()
    ids = {r["id"] for r in records}
    assert a1.id in ids
    assert a2.id in ids
    assert unique.id not in ids

    finder = SemanticDuplicateFinder()
    groups = finder.find_exact_duplicates([a1, a2, unique])
    assert len(groups) == 1
    assert set(g.id for g in groups[0]) == {a1.id, a2.id}


# ─── 8. L2 Dedup (cosine similarity) ─────────────────────────────────────────

@pytest.mark.asyncio
async def test_l2_dedup_cosine_similarity(session: AsyncSession):
    """In-memory cosine similarity identifies near-duplicate embeddings."""
    finder = SemanticDuplicateFinder(similarity_threshold=0.95)

    a1 = AssetFactory.create("file:///img1.jpg")
    a1.embedding = [1.0, 0.01, 0.0]

    a2 = AssetFactory.create("file:///img2.jpg")
    a2.embedding = [0.999, 0.010, 0.005]

    a3 = AssetFactory.create("file:///img3.jpg")
    a3.embedding = [0.0, 1.0, 0.0]  # orthogonal → low similarity

    pairs = finder.find_similar_pairs([a1, a2, a3])
    assert len(pairs) >= 1
    # a1 ↔ a2 should be paired, a3 should not appear
    assert any(a1.id in (p[0].id, p[1].id) and a2.id in (p[0].id, p[1].id) for p in pairs)
    assert not any(a3.id in (p[0].id, p[1].id) for p in pairs)


# ─── 9. TagMerger + Persist ───────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_tag_merger_and_persist(mapper: AGMMapper, session: AsyncSession):
    """TagMerger output is stored as Tag nodes linked to ImageAsset."""
    merger = TagMerger()
    merged = merger.merge(
        exif_tags=["Cat", "Indoor", "Flash"],
        llm_tags=["cat", "cozy", "indoor"],
    )
    # cat + indoor deduped; flash + cozy kept → 4 unique
    assert len(merged) == 4

    tag_nodes = [Tag(id=str(uuid.uuid4()), name=t) for t in merged]
    asset = ImageAsset(
        id=str(uuid.uuid4()), uri="file:///cozy_cat.jpg",
        name="cozy_cat.jpg", mime_type="image/jpeg",
        tags=tag_nodes,
    )

    for t in tag_nodes:
        await mapper.save(t, session=session)
    await mapper.save(asset, session=session)

    result = await session.run(
        "MATCH (a:ImageAsset {id: $aid})-[:HAS_TAG]->(t:Tag) RETURN t.name AS name",
        {"aid": asset.id},
    )
    records = await result.data()
    names = {r["name"] for r in records}
    assert "cat" in names
    assert "indoor" in names
    assert "flash" in names
    assert "cozy" in names


# ─── 10. Full Pipeline Smoke Test ─────────────────────────────────────────────

@pytest.mark.asyncio
async def test_full_pipeline_image_asset(
    mapper: AGMMapper, session: AsyncSession, annotation_svc: AnnotationService
):
    """End-to-end: image asset → tags → annotations → chunks → all in graph."""
    asset = ImageAsset(
        id=str(uuid.uuid4()), uri="file:///scene.jpg",
        name="scene.jpg", mime_type="image/jpeg",
        description="A busy city street at night",
        content_hash="sha256:sceneXYZ",
        width=4096, height=2160,
    )

    tag_city = Tag(id=str(uuid.uuid4()), name="city")
    tag_night = Tag(id=str(uuid.uuid4()), name="night")
    asset.tags = [tag_city, tag_night]

    caption = annotation_svc.add_caption(
        asset, text="Neon lights on wet pavement", language="en"
    )
    bbox = annotation_svc.add_bbox(
        asset, class_label="car", x=0.2, y=0.3, w=0.15, h=0.1
    )

    chunker = ContentChunker(chunk_size=20, overlap=5)
    chunks = chunker.chunk(asset_id=asset.id, text=asset.description)

    # Persist
    await mapper.save(tag_city, session=session)
    await mapper.save(tag_night, session=session)
    await mapper.save(asset, session=session)
    await mapper.save(caption, session=session)
    await mapper.save(bbox, session=session)
    for c in chunks:
        await mapper.save(c, session=session)

    # Verify
    result = await session.run(
        "MATCH (a:ImageAsset {id: $aid}) "
        "OPTIONAL MATCH (a)-[:HAS_TAG]->(t:Tag) "
        "OPTIONAL MATCH (cap:CaptionAnnotation {asset_id: $aid}) "
        "OPTIONAL MATCH (bb:BoundingBoxAnnotation {asset_id: $aid}) "
        "OPTIONAL MATCH (ch:ContentChunk {asset_id: $aid}) "
        "RETURN a.content_hash AS hash, "
        "       count(DISTINCT t) AS tag_count, "
        "       count(DISTINCT cap) AS caps, "
        "       count(DISTINCT bb) AS bboxes, "
        "       count(DISTINCT ch) AS chunk_count",
        {"aid": asset.id},
    )
    record = await result.single()
    assert record is not None
    assert record["hash"] == "sha256:sceneXYZ"
    assert record["tag_count"] == 2
    assert record["caps"] == 1
    assert record["bboxes"] == 1
    assert record["chunk_count"] == len(chunks)
