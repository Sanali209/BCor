"""
Annotation Repository - Data access layer following Repository pattern
Centralizes all database operations for annotation records.
"""
from typing import List, Optional, Dict, Any
import os
import sys
from abc import ABC, abstractmethod
from loguru import logger


class AnnotationRepositoryInterface(ABC):
    """Interface for annotation repository operations"""

    @abstractmethod
    def get_all_annotations(self, job_id: str) -> List[Any]:
        """Get all annotations for a job"""
        pass

    @abstractmethod
    def get_manual_voted_annotations(self, job_id: str) -> List[Any]:
        """Get manually voted annotations for a job"""
        pass

    @abstractmethod
    def get_annotation_by_id(self, annotation_id: str) -> Optional[Any]:
        """Get a specific annotation by ID"""
        pass

    @abstractmethod
    def save_annotation(self, annotation: Any) -> bool:
        """Save an annotation record"""
        pass

    @abstractmethod
    def delete_annotation(self, annotation_id: str) -> bool:
        """Delete an annotation record"""
        pass

    @abstractmethod
    def update_rating(self, annotation_id: str, mu: float, sigma: float) -> bool:
        """Update rating for an annotation"""
        pass


class MongoAnnotationRepository(AnnotationRepositoryInterface):
    """MongoDB implementation of annotation repository"""

    def __init__(self, service_container):
        self._service_container = service_container
        self._collection = None
        self._job_collection = None

        # Initialize database connections
        self._setup_database_connections()

        logger.info("MongoAnnotationRepository initialized")

    def _setup_database_connections(self):
        """Set up database connections"""
        try:
            # Import database components
            import sys
            current_dir = os.path.dirname(os.path.abspath(__file__))
            slm_path = os.path.join(current_dir, '..', '..', '..', '..', 'SLM')
            annotations_path = os.path.join(current_dir, '..', '..', '..', '..', 'SLM', 'files_db', 'annotation_tool')

            if slm_path not in sys.path:
                sys.path.insert(0, slm_path)
            if annotations_path not in sys.path:
                sys.path.insert(0, annotations_path)

            # Import database classes
            from annotation import AnnotationJob, AnnotationRecord

            # Store classes for use
            self._AnnotationJob = AnnotationJob
            self._AnnotationRecord = AnnotationRecord

            logger.debug("Database connections initialized")

        except Exception as e:
            logger.error(f"Failed to setup database connections: {e}")
            raise

    def get_or_create_job(self, job_name: str) -> Any:
        """Get or create a job by name"""
        try:
            job = self._AnnotationJob.get_by_name(job_name)
            if not job:
                # Create new job using configuration service
                config = self._service_container.get_service(1)  # ConfigurationService

                job_data = {
                    "name": job_name,
                    "type": "multiclass/image",
                    "choices": config.get_choices_list()
                }
                job_id = self._AnnotationJob.collection().insert_one(job_data).inserted_id
                job = self._AnnotationJob(job_id)
                logger.info(f"Created new rating job: {job_name}")
            return job
        except Exception as e:
            logger.error(f"Error getting/creating job {job_name}: {e}")
            raise

    def get_all_annotations(self, job_id: str) -> List[Any]:
        """Get all annotations for a job"""
        try:
            query = {"parent_id": job_id}
            annotations = self._AnnotationRecord.find(query)
            logger.debug(f"Retrieved {len(annotations)} annotations for job {job_id}")
            return annotations
        except Exception as e:
            logger.error(f"Error getting annotations for job {job_id}: {e}")
            return []

    def get_manual_voted_annotations(self, job_id: str) -> List[Any]:
        """Get manually voted annotations for a job"""
        try:
            query = {"parent_id": job_id, "manual": True}
            annotations = self._AnnotationRecord.find(query)
            logger.debug(f"Retrieved {len(annotations)} manual annotations for job {job_id}")
            return annotations
        except Exception as e:
            logger.error(f"Error getting manual annotations for job {job_id}: {e}")
            return []

    def get_annotation_by_id(self, annotation_id: str) -> Optional[Any]:
        """Get a specific annotation by ID"""
        try:
            # Convert string ID to ObjectId if needed
            from bson import ObjectId
            if isinstance(annotation_id, str):
                annotation_id = ObjectId(annotation_id)

            annotation = self._AnnotationRecord(annotation_id)
            # Check if it exists
            if annotation.get_field_val("_id"):
                return annotation
            return None
        except Exception as e:
            logger.error(f"Error getting annotation {annotation_id}: {e}")
            return None

    def save_annotation(self, annotation: Any) -> bool:
        """Save an annotation record"""
        try:
            annotation.save()
            logger.debug(f"Saved annotation {annotation.id}")
            return True
        except Exception as e:
            logger.error(f"Error saving annotation {annotation.id}: {e}")
            return False

    def delete_annotation(self, annotation_id: str) -> bool:
        """Delete an annotation record"""
        try:
            annotation = self.get_annotation_by_id(annotation_id)
            if annotation:
                annotation.delete_rec()
                logger.debug(f"Deleted annotation {annotation_id}")
                return True
            return False
        except Exception as e:
            logger.error(f"Error deleting annotation {annotation_id}: {e}")
            return False

    def update_rating(self, annotation_id: str, mu: float, sigma: float) -> bool:
        """Update rating for an annotation"""
        try:
            annotation = self.get_annotation_by_id(annotation_id)
            if not annotation:
                logger.warning(f"Annotation {annotation_id} not found for rating update")
                return False

            annotation.set_field_val("avg_rating", mu)
            annotation.set_field_val("trueskill_sigma", sigma)
            annotation.set_field_val("manual", True)
            annotation.save()

            logger.debug(f"Updated rating for annotation {annotation_id}: μ={mu:.2f}, σ={sigma:.2f}")
            return True

        except Exception as e:
            logger.error(f"Error updating rating for annotation {annotation_id}: {e}")
            return False


# Factory function for creating repository instances
def create_annotation_repository(service_container) -> AnnotationRepositoryInterface:
    """Factory function to create annotation repository"""
    return MongoAnnotationRepository(service_container)


# Repository instances will be managed by service container
annotation_repository = None
