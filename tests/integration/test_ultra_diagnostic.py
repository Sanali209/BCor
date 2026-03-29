"""Diagnostic test for the 10x Robust CAS Pipeline.

Verifies:
1. content_hash calculation in AssetFactory.
2. CAS Thumbnail generation (S/M/L) and sharding.
3. AI Inference (Ollama VLM, Ollama Embedding, BLIP, CLIP).
4. Metadata extraction (Pyexiv2).
"""
import asyncio
import os
import sys
import hashlib
import time
from loguru import logger

# Ensure workspace is in sys.path
PROJECT_ROOT = r"d:\github\BCor"
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from src.modules.assets.domain.factory import AssetFactory
from src.modules.assets.domain.models import ImageAsset
from src.modules.assets.infrastructure.providers import AssetsInfrastructureProvider
from src.modules.assets.infrastructure.registry import HandlerRegistry
from dishka import make_async_container

# Map fields to handler names (from models.py annotations)
FIELD_TO_HANDLER = {
    "thumbnails_ready": "ThumbnailHandler",
    "description": "OllamaVLM",
    "ollama_embedding": "OllamaEmbedding",
    "exif_data": "Pyexiv2",
    "captured_at": "Pyexiv2Smart",
    "perceptual_hash": "PHashHandler",
    "clip_embedding": "CLIPHandler",
    "blip_embedding": "BLIPHandler",
    "auto_tags": "TagMerger",
    "xmp_sync": "Pyexiv2_Write"
}

async def run_diagnostic():
    logger.info("Starting Ultra Pipeline Diagnostic...")
    
    # 1. Setup DI
    container = make_async_container(AssetsInfrastructureProvider())
    registry = await container.get(HandlerRegistry)
    
    # 2. Pick a sample image (create if missing)
    sample_img = os.path.join(PROJECT_ROOT, "tests", "samples", "test_diagnostic.webp")
    if not os.path.exists(sample_img):
        from PIL import Image
        os.makedirs(os.path.dirname(sample_img), exist_ok=True)
        img = Image.new('RGB', (1024, 768), color = (73, 109, 137))
        img.save(sample_img)
        logger.info(f"Created dummy sample image: {sample_img}")

    # 3. Test AssetFactory & content_hash
    uri = f"file://{os.path.abspath(sample_img).replace('\\', '/')}"
    logger.info(f"Ingesting URI: {uri}")
    asset = AssetFactory.create(uri)
    
    logger.info(f"Asset Created: {asset.name}")
    logger.info(f"Content Hash (Factory): '{asset.content_hash}'")
    
    with open(sample_img, "rb") as f:
        actual_hash = hashlib.sha256(f.read()).hexdigest()
    
    if asset.content_hash == actual_hash:
        logger.success(f"PASSED: Content Hash is correct: {asset.content_hash}")
    else:
        logger.error(f"!!! FAILED: Content Hash mismatch. Got '{asset.content_hash}', expected '{actual_hash}'")

    if not isinstance(asset, ImageAsset):
         logger.error(f"!!! FAILED: Asset is {type(asset)}, expected ImageAsset !!!")
         return

    # 4. Trigger Stored Handlers Manually
    logger.info(f"Testing inference of {len(FIELD_TO_HANDLER)} fields...")
    
    for field_name, handler_name in FIELD_TO_HANDLER.items():
        logger.info(f"--- [FIELD: {field_name} (via {handler_name})] ---")
        try:
            handler_cls = registry.resolve(asset.mime_type, handler_name)
            
            if not handler_cls:
                 logger.warning(f"No handler resolved for field '{field_name}' / name '{handler_name}'")
                 continue
            
            logger.info(f"Resolved Handler: {handler_cls.__name__}")
            
            # Context for run
            context = {"field_name": field_name, "storage_root": "data"}
            
            start_t = time.perf_counter()
            
            # Execute
            if handler_name == "ThumbnailHandler":
                res = await handler_cls.run(asset.uri, asset.content_hash, context)
            else:
                # Mock some dependencies for composite handlers
                if field_name == "auto_tags":
                     context["new_source_val"] = {"exif_data": {}, "xmp_data": {}, "llm_tags": ["test", "ai"]}
                elif field_name == "xmp_sync":
                     context["new_source_val"] = ["synced_tag", "10x_robust"]
                
                res = await handler_cls.run(asset.uri, context)
            
            duration = time.perf_counter() - start_t
            
            # Report result
            if isinstance(res, list):
                logger.success(f"Result [{duration:.2f}s]: List[len={len(res)}]")
            elif isinstance(res, str):
                logger.success(f"Result [{duration:.2f}s]: Str[len={len(res)}]: {res[:80]}...")
            else:
                logger.success(f"Result [{duration:.2f}s]: {res}")
                
        except Exception as e:
            logger.error(f"FAILED Field '{field_name}': {e}")

    logger.info("Diagnostic Finished.")

if __name__ == "__main__":
    asyncio.run(run_diagnostic())
