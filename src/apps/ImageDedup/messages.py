from src.core.messages import Command, Event


class LaunchGuiCommand(Command):
    """Command to start the legacy GUI via BCor System."""
    pass

class LoadProjectCommand(Command):
    """Command to load a dedup project from a path."""
    path: str

class ProjectLoadedEvent(Event):
    """Event emitted when a dedup project is successfully loaded."""
    project_id: str
    work_path: str
    group_count: int

