"""ImageDedup command handlers."""
from __future__ import annotations

import os
from typing import Any

from loguru import logger

from src.apps.ImageDedup.domain.image_group import GroupType, ImageGroup
from src.apps.ImageDedup.domain.image_item import ImageItem
from src.apps.ImageDedup.domain.interfaces.i_image_differ import IDuplicateFinder, IThumbnailCache
from src.apps.ImageDedup.domain.interfaces.i_image_tagger import IImageTagger
from src.apps.ImageDedup.domain.interfaces.i_xmp_metadata import IXmpMetadata
from src.apps.ImageDedup.domain.project import ImageDedupProject
from src.apps.ImageDedup.infrastructure.uow import ImageDedupUnitOfWork
from src.apps.ImageDedup.messages import (
    DuplicatesFoundEvent,
    FindDuplicatesCommand,
    LaunchImageDedupCommand,
    LoadProjectCommand,
    ProjectLoadedEvent,
    ProjectSavedEvent,
    SaveProjectCommand,
    TagImagesCommand,
)
from src.core.messagebus import MessageBus
from src.core.monads import BusinessResult, success


async def launch_image_dedup_handler(
    command: LaunchImageDedupCommand,
    bus: MessageBus,
    uow: ImageDedupUnitOfWork,
    thumbnail_cache: IThumbnailCache,
) -> None:
    """Open the ImageDedup GUI. Runs the PySide6 window."""
    logger.info("Launching ImageDedup GUI")
    
    async with uow:
        project = await uow.projects.get(command.project_id)

    from src.apps.ImageDedup.gui.main_window import run_image_dedup_app
    run_image_dedup_app(bus=bus, thumbnail_cache=thumbnail_cache, project=project)


async def find_duplicates_handler(
    command: FindDuplicatesCommand,
    uow: ImageDedupUnitOfWork,
    duplicate_finder: IDuplicateFinder,
) -> BusinessResult[Any, Any]:
    """Scan *work_path* for duplicates and update the project's groups."""
    async with uow:
        project: ImageDedupProject = await uow.projects.get(command.project_id)
        work_path = command.work_path or project.work_path

        logger.info(f"Scanning {work_path} for duplicates (threshold={command.similarity_threshold})")

        # Collect image files
        image_exts = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".gif"}
        file_paths: list[str] = []
        for root, _dirs, files in os.walk(str(work_path)):
            file_paths.extend(
                os.path.join(root, f) for f in files
                if os.path.splitext(f)[1].lower() in image_exts
            )

        # Build CNN index and find duplicates
        duplicate_finder.build_index(file_paths)
        raw_duplicates = duplicate_finder.find_duplicates(command.similarity_threshold)

        # Convert raw dict → ImageGroup entities
        new_groups: list[ImageGroup] = []
        for primary_path, dup_paths in raw_duplicates.items():
            group = ImageGroup(
                label=os.path.basename(primary_path),
                group_type=GroupType.SIMILAR_ITEMS,
            )
            group.items.append(ImageItem(path=primary_path))
            for dp in dup_paths:
                group.items.append(ImageItem(path=dp))
            new_groups.append(group)

        project.load_groups(new_groups)
        project.apply_hidden_pairs()
        project.remove_groups_with_single_image()

        await uow.projects.save(project)
        uow.commit()

        evt = DuplicatesFoundEvent(
            project_id=command.project_id,
            group_count=len(project.groups),
            work_path=work_path,
        )
        return success(evt)


async def save_project_handler(
    command: SaveProjectCommand,
    uow: ImageDedupUnitOfWork,
) -> ProjectSavedEvent:
    """Persist project groups to a JSON file."""
    async with uow:
        project: ImageDedupProject = await uow.projects.get(command.project_id)
        save_path = os.path.join(command.save_path, "groupList.json")
        os.makedirs(command.save_path, exist_ok=True)
        with open(save_path, "w", encoding="utf-8") as fh:
            fh.write(project.to_json())
        logger.info(f"Project saved to {save_path}")

    return ProjectSavedEvent(project_id=command.project_id, save_path=save_path)


async def load_project_handler(
    command: LoadProjectCommand,
    uow: ImageDedupUnitOfWork,
) -> ProjectLoadedEvent:
    """Load project groups from a JSON file."""
    async with uow:
        project: ImageDedupProject = await uow.projects.get(command.project_id)
        load_path = os.path.join(command.load_path, "groupList.json")
        if not os.path.exists(load_path):
            logger.warning(f"No saved project found at {load_path}")
            return ProjectLoadedEvent(project_id=command.project_id, group_count=0)

        with open(load_path, encoding="utf-8") as fh:
            raw = fh.read()
        groups = ImageDedupProject.groups_from_json(raw)
        project.load_groups(groups)

        await uow.projects.save(project)
        uow.commit()

    return ProjectLoadedEvent(project_id=command.project_id, group_count=len(groups))


async def tag_images_handler(
    cmd: TagImagesCommand,
    uow: ImageDedupUnitOfWork,
    tagger: IImageTagger,
    xmp: IXmpMetadata,
) -> BusinessResult[Any, Any]:
    """Predict and write XMP tags for multiple images."""
    logger.info(f"Tagging {len(cmd.image_paths)} images for project {cmd.project_id}")
    
    tags_written = 0
    for path in cmd.image_paths:
        try:
            # 1. Predict
            gen_tags, char_tags, rating = await tagger.predict_tags(
                path, 
                gen_threshold=cmd.gen_threshold, 
                char_threshold=cmd.char_threshold
            )
            
            # 2. Prepare prefixed tags
            new_tags = []
            for t in gen_tags:
                new_tags.append(f"auto/wd_tag/{t.replace(' ', '_')}")
            for c in char_tags:
                new_tags.append(f"auto/wd_characters/{c.replace(' ', '_')}")
            if rating:
                new_tags.append(f"auto/wd_rating/{rating}")
                
            # 3. Read & Merge
            metadata = xmp.read_metadata(path)
            existing_subjects = metadata.get("subjects", [])
            
            # Deduplicate
            merged = list(set(existing_subjects) | set(new_tags))
            
            # 4. Write
            # pyexiv2 expects string for Rating, but IXmpMetadata might use int.
            # PyExiv2MetadataAdapter handles conversion.
            if xmp.write_metadata(path, subjects=merged):
                tags_written += 1
                
        except Exception as e:
            logger.error(f"Failed to process tagging for {path}: {e}")

    return success(cmd)
