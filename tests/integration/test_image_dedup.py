import pytest
import os
import asyncio
from pathlib import Path
from src.apps.ImageDedup.messages import FindDuplicatesCommand, DuplicatesFoundEvent
from src.core.messagebus import MessageBus
from src.core.system import System
from src.apps.ImageDedup.domain.project import ImageDedupProject
from src.core.unit_of_work import AbstractUnitOfWork
from src.apps.ImageDedup.domain.interfaces.i_image_differ import IDuplicateFinder
from dishka import Provider, Scope, provide

class FakeDuplicateFinder(IDuplicateFinder):
    def build_index(self, paths): self.paths = paths
    def find_duplicates(self, threshold): 
        if not hasattr(self, "paths") or len(self.paths) < 2:
            return {}
        return {self.paths[0]: [self.paths[1]]}
    def find_top_similar(self, path, count=5): return []

class FakeProjectRepo:
    def __init__(self):
        self.projects = {}
    async def get(self, id: str):
        if id not in self.projects:
            self.projects[id] = ImageDedupProject(project_id=id, work_path=".")
        return self.projects[id]
    async def save(self, project):
        self.projects[project.project_id] = project

from src.apps.ImageDedup.infrastructure.uow import ImageDedupUnitOfWork

class FakeUnitOfWork(ImageDedupUnitOfWork):
    def __init__(self):
        self.projects = FakeProjectRepo()
        self.committed = False
    def _commit(self): self.committed = True
    def rollback(self): pass
    def collect_new_events(self): yield from []

class TestProvider(Provider):
    @provide(scope=Scope.REQUEST)
    def provide_uow(self) -> AbstractUnitOfWork:
        return FakeUnitOfWork()
    
    @provide(scope=Scope.REQUEST)
    def provide_duplicate_finder(self) -> IDuplicateFinder:
        return FakeDuplicateFinder()

@pytest.mark.asyncio
async def test_image_dedup_flow(tmp_path):
    import traceback
    try:
        (tmp_path / "img1.jpg").write_bytes(b"data1")
        (tmp_path / "img2.jpg").write_bytes(b"data2")
        
        manifest_content = """
[system]
name = "TestDedup"
version = "0.1.0"
[modules]
enabled = ["ImageDedup"]
paths = ["src.apps"]
"""
        manifest_path = tmp_path / "app.toml"
        manifest_path.write_text(manifest_content)
        
        from src.apps.ImageDedup.module import ImageDedupModule
        module = ImageDedupModule()
        # Mock settings for the module
        from pydantic_settings import BaseSettings
        class MockSettings(BaseSettings):
            work_path: str = str(tmp_path)
            model_config = {"extra": "allow"}
        module.settings = MockSettings()
        
        system = System(modules=[module])
        system.providers.append(TestProvider())
        
        await system.start()
        
        async with system.container() as container:
            bus = await container.get(MessageBus)
            uow = await container.get(AbstractUnitOfWork)
            
            cmd = FindDuplicatesCommand(project_id="test_project", work_path=str(tmp_path))
            
            # Dispatch command
            res = await bus.dispatch(cmd)
            
            # Wait for handler to complete
            await res.event_result(timeout=5.0)
            
            # Verify project resulted in groups
            project = await uow.projects.get("test_project")
            assert project is not None
            assert len(project.groups) == 1
            # Check for images in group
            paths = [item.path for item in project.groups[0].items]
            assert any("img1.jpg" in p for p in paths)
            assert any("img2.jpg" in p for p in paths)
            
        await system.stop()
    except Exception as e:
        traceback.print_exc()
        raise e
