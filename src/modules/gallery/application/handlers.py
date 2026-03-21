import hashlib
import os
from typing import TYPE_CHECKING
from uuid import UUID

from ..domain.entities import Image, Category, RelationRecord
from .commands import UploadImage, UpdateImageMetadata, AssignCategories, BulkCreateRelations
from .uow import GalleryUnitOfWork

if TYPE_CHECKING:
    pass


async def handle_upload_image(cmd: UploadImage, uow: GalleryUnitOfWork) -> UUID:
    """Handles the uploading of a new image with duplicate detection."""
    # Calculate MD5 for duplicate detection
    md5_hash = None
    if os.path.exists(cmd.file_path):
        with open(cmd.file_path, "rb") as f:
            md5_hash = hashlib.md5(f.read()).hexdigest()

    async with uow:
        # Check for duplicate
        if md5_hash:
            existing = uow.images.find_by_hash(md5_hash)
            if existing:
                return existing.id

        new_image = Image(
            file_path=cmd.file_path,
            title=cmd.title,
            description=cmd.description,
            category_ids=cmd.category_ids,
            md5_hash=md5_hash
        )
        uow.images.add(new_image)
        uow.commit()
        return new_image.id


async def handle_update_metadata(cmd: UpdateImageMetadata, uow: GalleryUnitOfWork) -> None:
    """Updates metadata for an existing image."""
    async with uow:
        image = uow.images.get_by_id(cmd.image_id)
        if not image:
            raise ValueError(f"Image {cmd.image_id} not found")
            
        if cmd.title is not None:
            image.title = cmd.title
        if cmd.description is not None:
            image.description = cmd.description
        if cmd.category_ids is not None:
            image.category_ids = cmd.category_ids
            
        uow.commit()


async def handle_assign_categories(cmd: AssignCategories, uow: GalleryUnitOfWork) -> None:
    """Bulk assigns categories to multiple images."""
    async with uow:
        for image_id in cmd.image_ids:
            image = uow.images.get_by_id(image_id)
            if not image:
                continue
                
            if cmd.mode == "replace":
                image.category_ids = cmd.category_ids
            else:
                # Add unique
                existing = set(image.category_ids)
                for cat_id in cmd.category_ids:
                    existing.add(cat_id)
                image.category_ids = list(existing)
                
        uow.commit()


async def handle_bulk_create_relations(cmd: BulkCreateRelations, uow: GalleryUnitOfWork) -> None:
    """Creates relations from a set of entities to a target entity."""
    async with uow:
        for from_id in cmd.from_ids:
            relation = RelationRecord(
                from_entity_type=cmd.from_type,
                from_id=from_id,
                to_entity_type=cmd.to_type,
                to_id=cmd.to_id,
                relation_type_code=cmd.relation_type
            )
            uow.relations.save(relation)
        uow.commit()
