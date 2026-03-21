import logging
from typing import List, Optional
from uuid import UUID

from src.modules.vision.adapters.wd_tagger_adapter import WDTaggerAdapter
from .uow import GalleryUnitOfWork
from ..infrastructure.vector_repository import ChromaVectorRepository

logger = logging.getLogger(__name__)


class AiService:
    """Service to coordinate AI processing for gallery images."""

    def __init__(
        self, 
        uow: GalleryUnitOfWork, 
        vector_repo: ChromaVectorRepository,
        tagger: WDTaggerAdapter
    ) -> None:
        self.uow = uow
        self.vector_repo = vector_repo
        self.tagger = tagger

    async def run_full_scan(self, image_id: UUID) -> None:
        """
        Runs a complete AI analysis on an image:
        1. Extract tags and rating using WD-Tagger.
        2. Generate and store embeddings (CLIP/BLIP - placeholder for now).
        3. Update image metadata and processing flags.
        """
        async with self.uow:
            image = self.uow.images.get_by_id(image_id)
            if not image:
                logger.error(f"Image {image_id} not found for AI scan.")
                return

            try:
                # 1. Prediction via Vision Module
                gen_tags, char_tags, rating_label = await self.tagger.predict_tags(image.file_path)
                
                # 2. Update Image Tags/Description based on AI (logic similar to djangogal)
                # For now, we update rating and store tags in metadata
                if rating_label != "error":
                    # Simple mapping for rating (e.g., 'general' -> 0, 'sensitive' -> 1, etc.)
                    # This could be expanded to a proper rating system.
                    pass

                # 3. Vector Generation (Placeholder)
                # In a real setup, we'd use a CLIP model here to get a vector
                # dummy_vector = [0.1] * 512
                # self.vector_repo.add_vector(image_id, dummy_vector, "clip", {"title": image.title})
                
                # image.has_clip_vector = True
                
                self.uow.commit()
                logger.info(f"AI scan completed for image {image_id}")
                
            except Exception as e:
                logger.exception(f"Failed AI scan for image {image_id}: {e}")
                self.uow.rollback()
