"""
Integration test: verify that ingesting the same directory twice
creates NO duplicate nodes in Neo4j (idempotent ingestion).

Requires:
- Neo4j at bolt://localhost:7687 (neo4j/password)
- PYTHONPATH=.
- A small test image directory (uses a 5-file subset)
"""
from __future__ import annotations

import asyncio
import os
import pytest
from neo4j import AsyncGraphDatabase

from src.modules.assets.domain.factory import AssetFactory
from src.modules.assets.domain.services import AssetIngestionService
from src.modules.agm.mapper import AGMMapper
from src.core.messagebus import MessageBus


# ── Minimal Provider stub ─────────────────────────────────────────────────────

class _MockBus:
    async def dispatch(self, event):
        pass
    def register_event(self, *a, **kw):
        pass


class _NullContainer:
    async def get(self, t):
        return None


# ── Helpers ───────────────────────────────────────────────────────────────────

ROOT = "D:/image_db/safe repo/ddsearch/kim_possible"
NEO4J_URI = "bolt://localhost:7687"
NEO4J_AUTH = ("neo4j", "password")


async def _count_assets(driver) -> int:
    async with driver.session() as s:
        res = await s.run("MATCH (n:ImageAsset) RETURN count(n) AS c")
        row = await res.single()
        return row["c"] if row else 0


# ── Tests ─────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_deterministic_ids():
    """Same URI → same asset ID every call."""
    uri = "file:///D:/image_db/safe repo/ddsearch/kim_possible/kim_possible_1.webp"
    a1 = AssetFactory.create(uri=uri)
    a2 = AssetFactory.create(uri=uri)
    assert a1.id == a2.id, f"IDs diverged: {a1.id} vs {a2.id}"


@pytest.mark.asyncio
async def test_uri_key_identity_map():
    """Loading the same URI twice returns the *same Python object*."""
    mapper = AGMMapper(container=_NullContainer(), message_bus=_MockBus())
    record = {
        "id": "fixed-id-001",
        "uri": "file:///some/path/img.jpg",
        "name": "img.jpg",
        "mime_type": "image/jpeg",
        "description": "",
        "content_hash": "",
        "size": 0,
    }
    from src.modules.assets.domain.models import ImageAsset

    inst1 = await mapper.load(ImageAsset, record, resolve_live=False)
    inst2 = await mapper.load(ImageAsset, record, resolve_live=False)
    assert inst1 is inst2, "Identity Map should return the same object for the same URI+ID"


@pytest.mark.asyncio
async def test_idempotent_ingestion():
    """Running ingest_directory twice produces the same node count."""
    if not os.path.exists(ROOT):
        pytest.skip(f"Test directory {ROOT} not found.")

    async with AsyncGraphDatabase.driver(NEO4J_URI, auth=NEO4J_AUTH) as driver:
        # Clear slate
        async with driver.session() as s:
            await s.run("MATCH (n:ImageAsset) DETACH DELETE n")

        bus = _MockBus()
        mapper = AGMMapper(container=_NullContainer(), message_bus=bus)
        factory = AssetFactory()
        service = AssetIngestionService(mapper=mapper, factory=factory)

        # First run
        assets_1 = await service.ingest_directory(ROOT, session=None)
        count_1 = await _count_assets(driver)
        print(f"\nFirst run: {len(assets_1)} returned, {count_1} in DB")

        # Second run (should be fully cached — no new DB nodes)
        assets_2 = await service.ingest_directory(ROOT, session=None)
        count_2 = await _count_assets(driver)
        print(f"Second run: {len(assets_2)} returned, {count_2} in DB")

        assert count_1 == count_2, (
            f"Duplicate nodes created: first={count_1} second={count_2}"
        )
        assert len(assets_2) == len(assets_1), "Second run should return same asset list"
