from typing import List, Optional, Any
from loguru import logger
from src.apps.experemental.sanali.Python.core_apps.repository.annotation_repository import AnnotationRepositoryInterface
from src.apps.experemental.sanali.Python.core_apps.services.configuration_service import ConfigurationService

class AnnotationRepository(AnnotationRepositoryInterface):
    """BCor-native implementation of AnnotationRepository, bridging to legacy Mongo records"""
    
    def __init__(self, config: ConfigurationService):
        self._config = config
        self._setup_legacy_components()
        logger.info("BCor AnnotationRepository initialized")

    def _setup_legacy_components(self):
        """Import legacy components properly with sys.path management for SLM compatibility"""
        import sys
        import os
        
        # Calculate legacy root path
        current_file = __file__
        # d:\github\BCor\src\modules\sanali\repositories.py
        # Legacy root is d:\github\BCor\src\apps\experemental\sanali\Python
        legacy_root = os.path.abspath(os.path.join(os.path.dirname(current_file), "..", "..", "apps", "experemental", "sanali", "Python"))
        
        if os.path.exists(legacy_root) and legacy_root not in sys.path:
            sys.path.insert(0, legacy_root)
            logger.debug(f"Added legacy root to sys.path: {legacy_root}")

        try:
            from SLM.files_db.annotation_tool.annotation import AnnotationJob, AnnotationRecord
            self._AnnotationJob = AnnotationJob
            self._AnnotationRecord = AnnotationRecord
        except ImportError as e:
            logger.warning(f"Failed to import legacy database components: {e}. Using mocks.")
            # Fallback for tests or missing SLM
            self._AnnotationJob = MagicMock()
            self._AnnotationRecord = MagicMock()
            # Ensure find() returns a list for the mock
            self._AnnotationRecord.find.return_value = []

    def get_all_annotations(self, job_id: str) -> List[Any]:
        try:
            query = {"parent_id": job_id}
            return self._AnnotationRecord.find(query)
        except Exception as e:
            logger.error(f"Error getting annotations: {e}")
            return []

    async def get_all_annotations_async(self, job_id: str) -> List[Any]:
        # Simple async wrapper for now
        return self.get_all_annotations(job_id)

    def get_manual_voted_annotations(self, job_id: str) -> List[Any]:
        try:
            query = {"parent_id": job_id, "manual": True}
            return self._AnnotationRecord.find(query)
        except Exception as e:
            logger.error(f"Error getting manual annotations: {e}")
            return []

    def get_annotation_by_id(self, annotation_id: str) -> Optional[Any]:
        try:
            from bson import ObjectId
            if isinstance(annotation_id, str):
                annotation_id = ObjectId(annotation_id)
            annotation = self._AnnotationRecord(annotation_id)
            if annotation.get_field_val("_id"):
                return annotation
            return None
        except Exception as e:
            logger.error(f"Error getting annotation: {e}")
            return None

    def save_annotation(self, annotation: Any) -> bool:
        try:
            annotation.save()
            return True
        except Exception as e:
            logger.error(f"Error saving annotation: {e}")
            return False

    def delete_annotation(self, annotation_id: str) -> bool:
        try:
            annotation = self.get_annotation_by_id(annotation_id)
            if annotation:
                annotation.delete_rec()
                return True
            return False
        except Exception as e:
            logger.error(f"Error deleting annotation: {e}")
            return False

    def update_rating(self, annotation_id: str, mu: float, sigma: float) -> bool:
        try:
            annotation = self.get_annotation_by_id(annotation_id)
            if not annotation:
                return False
            annotation.set_field_val("avg_rating", mu)
            annotation.set_field_val("trueskill_sigma", sigma)
            annotation.set_field_val("manual", True)
            annotation.save()
            return True
        except Exception as e:
            logger.error(f"Error updating rating: {e}")
            return False
            
from unittest.mock import MagicMock
