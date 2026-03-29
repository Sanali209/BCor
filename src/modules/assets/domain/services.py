"""Domain services: TagMerger, ContentChunker, AnnotationService."""
from __future__ import annotations

import uuid
import asyncio
from typing import Any, Type, TypeVar

from src.modules.assets.domain.models import (
    Annotation,
    Asset,
    BoundingBoxAnnotation,
    CaptionAnnotation,
    ContentChunk,
    MultiLabelAnnotation,
    PolygonAnnotation,
    SingleLabelAnnotation,
)

A = TypeVar("A", bound=Annotation)


# ─── TagMerger ────────────────────────────────────────────────────────────────

class TagMerger:
    """Merges and deduplicates tags from multiple sources.

    Normalizes to lowercase and strips whitespace before comparing.
    Source priority is preserved in ordering (EXIF first, then LLM).
    """

    def merge(self, exif_tags: list[str], llm_tags: list[str]) -> list[str]:
        """Merge two tag lists removing duplicates (case-insensitive)."""
        seen: set[str] = set()
        result: list[str] = []
        # Flatten and normalize
        for raw in (exif_tags or []) + (llm_tags or []):
            if not isinstance(raw, str):
                continue
            normalized = raw.strip().lower()
            if normalized and normalized not in seen:
                seen.add(normalized)
                result.append(normalized)
        return result

    @staticmethod
    async def run(source_value: Any, context: dict[str, Any] | None = None) -> list[str]:
        """TaskIQ handler entry point for TagMerger.
        
        Note: Current AGMMapper only passes one changed source field. 
        A future update should pass the whole node state for multi-source mergers.
        """
        if isinstance(source_value, list):
            return TagMerger().merge([], source_value)
        if isinstance(source_value, dict):
            # Extract tags from EXIF dict if that's what we got
            tags = source_value.get("tags", [])
            if isinstance(tags, str): tags = [tags]
            return TagMerger().merge(tags, [])
        return []


# ─── ContentChunker ──────────────────────────────────────────────────────────

class ContentChunker:
    """Splits long-form text into overlapping ContentChunk objects.

    Creates sliding-window chunks suitable for RAG (Retrieval-Augmented
    Generation) indexing. Each chunk is a standalone ContentChunk node
    that can be linked back to its parent Asset via PART_OF.

    Args:
        chunk_size: Maximum characters per chunk.
        overlap:    Characters of overlap between consecutive chunks.
    """

    def __init__(self, chunk_size: int = 500, overlap: int = 50) -> None:
        self.chunk_size = chunk_size
        self.overlap = overlap

    def chunk(self, asset_id: str, text: str) -> list[ContentChunk]:
        """Split text into ContentChunk instances.

        Args:
            asset_id: ID of the parent Asset.
            text:     Full text to split.

        Returns:
            Ordered list of ContentChunk objects.
        """
        if not text:
            return []

        chunks: list[ContentChunk] = []
        step = max(1, self.chunk_size - self.overlap)
        start = 0
        idx = 0
        while start < len(text):
            end = min(start + self.chunk_size, len(text))
            chunk_text = text[start:end]
            chunks.append(
                ContentChunk(
                    id=str(uuid.uuid4()),
                    asset_id=asset_id,
                    content=chunk_text,
                    chunk_index=idx,
                )
            )
            idx += 1
            start += step
        return chunks


# ─── AssetIngestionService ────────────────────────────────────────────────────

class AssetIngestionService:
    """Orchestrates the ingestion of local files into the Asset graph.
    
    This service crawls directories, uses AssetFactory to create domain
    objects, and uses AGMMapper to persist them.
    """

    def __init__(self, mapper: Any, factory: Any) -> None:
        self._mapper = mapper
        self._factory = factory
        self._abort = False

    def stop_ingestion(self):
        """Signals the ingestion process to abort as soon as possible."""
        self._abort = True

    async def ingest_directory(
        self,
        root_path: str,
        session: Any,
        recursive: bool = True,
        ignore_patterns: list[str] | None = None,
        overwrite: bool = False,
    ) -> list[Asset]:
        """Scan a directory and ingest all discovered assets.

        Assets already known to the mapper (by URI) are skipped unless
        *overwrite* is True.  This makes repeated ingestion idempotent.

        Args:
            root_path: Path to start scanning from.
            session: Neo4j session for persistence (may be None; mapper opens its own).
            recursive: Whether to crawl subdirectories.
            ignore_patterns: Glob patterns to skip.
            overwrite: When True, re-save assets even if already tracked.

        Returns:
            List of ingested Asset domain objects (newly created or cached).
        """
        import os
        from loguru import logger

        self._abort = False
        ingested: list[Asset] = []
        for dirpath, _, filenames in os.walk(root_path):
            if self._abort:
                logger.info("Ingestion process aborted by request.")
                break
            if not recursive and dirpath != root_path:
                continue

            for filename in filenames:
                if self._abort:
                    break
                full_path = os.path.join(dirpath, filename)
                if ignore_patterns and any(p in filename for p in ignore_patterns):
                    continue

                try:
                    uri = f"file://{full_path}"

                    # ── Fast path: URI already in Identity Map ─────────────
                    uri_map: dict = getattr(self._mapper, "_uri_map", {})
                    if not overwrite and uri in uri_map:
                        ingested.append(uri_map[uri])
                        if len(ingested) % 5 == 0:
                            await asyncio.sleep(0.01) # Throttling for Windows UI stability
                        continue

                    asset = self._factory.create_from_path(full_path)
                    if asset:
                        await self._mapper.save(asset, session=session)
                        ingested.append(asset)

                    # Yield to GUI / event loop more aggressively for stability
                    if len(ingested) % 2 == 0:
                        await asyncio.sleep(0.01) 
                except Exception as e:
                    logger.error(f"Failed to ingest {full_path}: {e}")

        return ingested



# ─── AnnotationService ────────────────────────────────────────────────────────

class AnnotationService:
    """Manages annotations on Asset objects (in-memory).

    Persistence to Neo4j is handled separately by AGMMapper.
    """

    def add_single_label(
        self,
        asset: Asset,
        label: str,
        annotator: str = "system",
        confidence: float = 1.0,
    ) -> SingleLabelAnnotation:
        ann = SingleLabelAnnotation(
            id=str(uuid.uuid4()),
            asset_id=asset.id,
            label=label,
            annotator=annotator,
            confidence=confidence,
        )
        asset.annotations.append(ann)
        return ann

    def add_multi_label(
        self,
        asset: Asset,
        labels: list[str],
        annotator: str = "system",
        confidence: float = 1.0,
    ) -> MultiLabelAnnotation:
        ann = MultiLabelAnnotation(
            id=str(uuid.uuid4()),
            asset_id=asset.id,
            labels=labels,
            annotator=annotator,
            confidence=confidence,
        )
        asset.annotations.append(ann)
        return ann

    def add_bbox(
        self,
        asset: Asset,
        class_label: str,
        x: float, y: float, w: float, h: float,
        annotator: str = "system",
        confidence: float = 1.0,
    ) -> BoundingBoxAnnotation:
        ann = BoundingBoxAnnotation(
            id=str(uuid.uuid4()),
            asset_id=asset.id,
            class_label=class_label,
            x=x, y=y, w=w, h=h,
            annotator=annotator,
            confidence=confidence,
        )
        asset.annotations.append(ann)
        return ann

    def add_caption(
        self,
        asset: Asset,
        text: str,
        language: str = "en",
        annotator: str = "system",
    ) -> CaptionAnnotation:
        ann = CaptionAnnotation(
            id=str(uuid.uuid4()),
            asset_id=asset.id,
            text=text,
            language=language,
            annotator=annotator,
        )
        asset.annotations.append(ann)
        return ann

    def add_polygon(
        self,
        asset: Asset,
        points: list[list[float]],
        class_label: str,
        annotator: str = "system",
        confidence: float = 1.0,
    ) -> PolygonAnnotation:
        ann = PolygonAnnotation(
            id=str(uuid.uuid4()),
            asset_id=asset.id,
            points=points,
            class_label=class_label,
            annotator=annotator,
            confidence=confidence,
        )
        asset.annotations.append(ann)
        return ann

    def get_by_type(self, asset: Asset, ann_type: type[A]) -> list[A]:
        """Filter annotations by concrete type."""
        return [a for a in asset.annotations if isinstance(a, ann_type)]

    def remove(self, asset: Asset, annotation: Annotation) -> None:
        """Remove an annotation from the asset's annotation list."""
        if annotation in asset.annotations:
            asset.annotations.remove(annotation)
