import uuid
import time
from typing import Any, Protocol, Sequence
from .models import DedupeSession
from src.modules.assets.domain.models import Asset, ImageAsset, SimilarTo, RelationType
from src.modules.assets.domain.services import AssetIngestionService
from src.modules.assets.infrastructure.dedup import SemanticDuplicateFinder

class DeduplicationService:
    """Orchestrates the lifecycle of a deduplication session.
    
    Coordinates filesystem ingestion, graph metadata extraction,
    and semantic similarity clustering using the declarative BCor core.
    """
    
    def __init__(
        self, 
        ingestion: AssetIngestionService, 
        mapper: Any
    ):
        self._ingestion = ingestion
        self._mapper = mapper

    async def run_dedupe(self, root_path: str, session_neo: Any, threshold: float = 0.95, engine: str = "clip") -> DedupeSession:
        """Execute a full deduplication pass on the given directory."""
        # --- Init Finder ---
        if engine == "phash":
            finder = PHashFinder(threshold=int(threshold))
        else:
            finder = VectorFinder(mapper=self._mapper, embedding_field=f"{engine}_embedding", threshold=threshold)

        """Execute a full deduplication pass on the given directory.
        
        1. Initializes a tracking session in the graph.
        2. Scans and ingests files into the graph (Asset nodes).
        3. Computes semantic similarity clusters using graph-native vector search.
        4. Persists 'SIMILAR' relationships with scores directly on graph edges.
        """
        # 1. Start Session
        session = DedupeSession(
            id=str(uuid.uuid4()),
            root_path=root_path,
            threshold=threshold,
            status="scanning",
            created_at=time.time()
        )
        await self._mapper.save(session, session=session_neo)

        # 2. Ingest
        assets = await self._ingestion.ingest_directory(root_path, session=session_neo)
        
        # 3. Reload assets to pick up side-effect computations (hashes)
        from src.modules.assets.domain.models import ImageAsset
        assets = await self._mapper.query(ImageAsset).all(session_neo)
        
        has_h = [a for a in assets if a.perceptual_hash]
        logger.debug(f"RELODED ASSETS: total={len(assets)}, with_hash={len(has_h)}")
        if assets:
            logger.debug(f"SAMPLE HASH: {assets[0].perceptual_hash}")
        
        session.count_total = len(assets)
        session.status = "clustering"
        await self._mapper.save(session, session=session_neo)

        for asset in assets:
            if engine == "phash":
                # For phash we use find_pairs usually for batches, 
                # but for simplicity in run_dedupe let's do a quick local check
                similars = []
                for other in assets:
                    if other.id == asset.id: continue
                    dist = PHashFinder.hamming_distance(asset.perceptual_hash, other.perceptual_hash)
                    if dist <= int(threshold):
                        similars.append((other.id, float(dist)))
                await asyncio.sleep(0)  # Yield to GUI loop per asset
            else:
                similars = await finder.find_similar(asset)
            
            new_sims = []
            for other_id, score in similars:
                new_sims.append(SimilarTo(id=other_id, score=score, engine=engine))
            
            if new_sims:
                asset.similar.extend(new_sims)
                await self._mapper.save(asset, session=session_neo)

        # 4. Finish
        session.status = "finished"
        session.count_total = len(assets)
        # Simplified duplicate count: nodes that have SIMILAR relationships
        # (In a real app, we'd use more complex clustering logic)
        session.count_duplicates = sum(1 for a in assets if a.similar)
        
        await self._mapper.save(session, session=session_neo)
        return session


class SimilarityFinder(Protocol):
    """Protocol for asset similarity search strategies."""
    async def find_pairs(self, assets: Sequence[ImageAsset]) -> list[tuple[ImageAsset, ImageAsset, float]]: ...
    async def find_similar(self, asset: ImageAsset) -> list[tuple[str, float]]: ...


class PHashFinder:
    """Finds visually similar images using Perceptual Hashing and Hamming distance.
    
    Uses a simple O(N^2) comparison for now, optimizable via BK-Tree.
    """
    def __init__(self, threshold: int = 5):
        self.threshold = threshold

    @staticmethod
    def hamming_distance(h1: str, h2: str) -> int:
        """Calculate Hamming distance between two hex hashes."""
        if len(h1) != len(h2):
            return 999
        return sum(bin(int(a, 16) ^ int(b, 16)).count('1') for a, b in zip(h1, h2))

    async def find_pairs(self, assets: Sequence[ImageAsset]) -> list[tuple[ImageAsset, ImageAsset, float]]:
        results = []
        for i, a1 in enumerate(assets):
            if not a1.perceptual_hash: continue
            for a2 in assets[i+1:]:
                if not a2.perceptual_hash: continue
                dist = self.hamming_distance(a1.perceptual_hash, a2.perceptual_hash)
                if dist <= self.threshold:
                    results.append((a1, a2, float(dist)))
        return results

    async def find_similar(self, asset: ImageAsset) -> list[tuple[str, float]]:
        # This would ideally query the graph, but for now it's local
        return []


class VectorFinder:
    """Finds semantically similar assets using vector embeddings and ANN search."""
    def __init__(self, mapper: Any, embedding_field: str = "clip_embedding", threshold: float = 0.9):
        self._mapper = mapper
        self.field = embedding_field
        self.threshold = threshold

    async def find_similar(self, asset: ImageAsset) -> list[tuple[str, float]]:
        embedding = getattr(asset, self.field, [])
        if not embedding:
            return []

        # Offload to Neo4j Vector Index via AGMMapper
        similars = await self._mapper.vector_search(
            label="ImageAsset",
            property_name=self.field,
            vector=embedding,
            limit=10  # Configurable
        )
        
        return [(id_, score) for id_, score in similars if score >= self.threshold]
