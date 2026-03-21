"""ImageDedup CQRS messages: Commands and Events."""
from src.core.messages import Command, Event

# ─── Commands ─────────────────────────────────────────────────────────────────


class LaunchImageDedupCommand(Command):
    """Open the ImageDedup GUI window."""
    project_id: str


class FindDuplicatesCommand(Command):
    project_id: str
    work_path: str = ""
    similarity_threshold: float = 0.95


class TagImagesCommand(Command):
    """Trigger AI tagging on specific images."""
    project_id: str
    image_paths: list[str]
    gen_threshold: float = 0.35
    char_threshold: float = 0.75


class SaveProjectCommand(Command):
    project_id: str
    save_path: str


class LoadProjectCommand(Command):
    project_id: str
    load_path: str


# ─── Events ───────────────────────────────────────────────────────────────────


class DuplicatesFoundEvent(Event):
    project_id: str
    group_count: int
    work_path: str


class ProjectSavedEvent(Event):
    project_id: str
    save_path: str


class ProjectLoadedEvent(Event):
    project_id: str
    group_count: int
