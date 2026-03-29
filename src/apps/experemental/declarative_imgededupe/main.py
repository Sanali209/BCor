import asyncio
import sys
import os
import time
from loguru import logger
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from rich.table import Table

# BCor imports
# Since we are an "experimental" app, we might need manual DI for now 
# if we don't want to register in the global module registry just yet.
from src.modules.agm.mapper import AGMMapper
from src.modules.assets.domain.factory import AssetFactory
from src.modules.assets.domain.services import AssetIngestionService
from src.modules.assets.infrastructure.dedup import SemanticDuplicateFinder

from .services import DeduplicationService
from .models import DedupeSession

console = Console()

async def run_app(root_path: str):
    if not os.path.exists(root_path):
        console.print(f"[bold red]Error:[/bold red] Path [yellow]{root_path}[/yellow] does not exist.")
        return

    console.print(Panel.fit(
        "[bold cyan]BCor Declarative ImageDedup[/bold cyan]\n"
        "[dim]Modern, Graph-Native Deduplication Evolution[/dim]",
        border_style="cyan"
    ))

    # 1. Manual DI setup for experimental app 
    from src.modules.agm.mapper import AGMMapper
    from src.modules.assets.domain.factory import AssetFactory
    from src.core.messagebus import MessageBus
    from src.core.unit_of_work import AbstractUnitOfWork
    from dishka import make_async_container, Provider, provide, Scope
    
    class MockUoW(AbstractUnitOfWork):
        def _commit(self): pass
        def rollback(self): pass
        def _get_all_seen_aggregates(self): return []

    class AppProvider(Provider):
        @provide(scope=Scope.APP)
        def get_bus(self, uow: AbstractUnitOfWork) -> MessageBus:
            return MessageBus(uow=uow)
        
        @provide(scope=Scope.APP)
        def get_uow(self) -> AbstractUnitOfWork:
            return MockUoW()

    container = make_async_container(AppProvider())
    bus = await container.get(MessageBus)
    mapper = AGMMapper(container=container, message_bus=bus) 
    
    factory = AssetFactory()
    ingestion = AssetIngestionService(mapper, factory)
    service = DeduplicationService(ingestion, mapper)

    # 2. Execution with Progress UI
    engine = "phash" if len(sys.argv) < 3 else sys.argv[2]
    threshold = 5 if engine == "phash" else 0.85
    from neo4j import AsyncGraphDatabase
    uri = "bolt://localhost:7687"
    auth = ("neo4j", "password")
    
    try:
        async with AsyncGraphDatabase.driver(uri, auth=auth) as driver:
            async with driver.session() as neo_session:
                console.print(f"[cyan]Scanning [yellow]{root_path}[/cyan] with [magenta]{engine}[/magenta]...")
                session_result = await service.run_dedupe(root_path, neo_session, threshold=threshold, engine=engine)
    except Exception as e:
        console.print(f"[bold red]Critical Error:[/bold red] {e}")
        return

    # 3. Results Dashboard
    table = Table(title="[bold]Session Results[/bold]", border_style="cyan")
    table.add_column("Property", style="magenta")
    table.add_column("Value", style="white")
    
    table.add_row("Session ID", f"[dim]{session_result.id}[/dim]")
    table.add_row("Root Path", f"[blue]{session_result.root_path}[/blue]")
    table.add_row("Total Assets Processed", str(session_result.count_total))
    table.add_row("Duplicates Linked", f"[bold green]{session_result.count_duplicates}[/bold green]")
    table.add_row("Similarity Engine", f"[bold cyan]{engine.upper()}[/bold cyan]")
    table.add_row("Persistence", "Neo4j (L2 Graph)")
    table.add_row("Duration", f"{time.time() - session_result.created_at:.2f}s")
    
    console.print(table)
    console.print("\n[dim italic]Note: Pairs are now persisted in the graph under 'SIMILAR' relationships with scores.[/dim italic]")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        console.print("[yellow]Usage:[/yellow] python -m src.apps.experemental.declarative_imgededupe.main <directory_path> [engine: phash|clip|blip]")
    else:
        # Resolve path
        path = os.path.abspath(sys.argv[1])
        asyncio.run(run_app(path))
