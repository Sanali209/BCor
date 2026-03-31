from loguru import logger
from src.apps.experemental.imgededupe.application.messages import (
    StartDeduplicationCommand, DeduplicationStarted, DuplicatesFound,
    StartScanCommand, ScanStarted, ScanCompleted,
    ClustersGenerated
)
from src.apps.experemental.imgededupe.core.deduper import Deduper
from src.apps.experemental.imgededupe.core.scanner import Scanner
from src.apps.experemental.imgededupe.core.unit_of_work import SqliteUnitOfWork
from src.core.messagebus import MessageBus
from src.apps.experemental.imgededupe.ui.adapter import GuiEventAdapter
from src.apps.experemental.imgededupe.core.scan_session import ScanSession

async def handle_start_deduplication(
    cmd: StartDeduplicationCommand,
    deduper: Deduper,
    bus: MessageBus,
    uow: SqliteUnitOfWork,
):
    """
    Handler for StartDeduplicationCommand.
    Delegates to legacy Deduper.
    """
    logger.info(f"Starting deduplication with engine: {cmd.engine_type}")
    
    # Emit start event
    await bus.dispatch(DeduplicationStarted(engine_type=cmd.engine_type))
    
    # Bridge to legacy logic
    # In legacy, set_engine might be needed
    deduper.set_engine(cmd.engine_type)
    
    results = deduper.find_duplicates(
        threshold=cmd.threshold,
        include_ignored=cmd.include_ignored,
        roots=cmd.roots,
        # progress_callback=... # TODO: Bridge this to events later
    )
    
    logger.info(f"Deduplication finished. Found {len(results)} relations.")
    
    # Emit results event
    await bus.dispatch(DuplicatesFound(relations_count=len(results)))

async def handle_start_scan(
    cmd: StartScanCommand,
    scanner: Scanner,
    bus: MessageBus,
    uow: SqliteUnitOfWork,
):
    """Handler for StartScanCommand."""
    logger.info(f"Starting scan in {cmd.roots}")
    await bus.dispatch(ScanStarted(roots=cmd.roots))
    
    # Bridge to legacy logic
    count = scanner.scan(roots=cmd.roots, recursive=cmd.recursive)
    
    logger.info(f"Scan finished. Processed {count} files.")
    await bus.dispatch(ScanCompleted(files_count=count))

async def handle_generate_clusters(
    bus: MessageBus,
    deduper: Deduper,
    uow: SqliteUnitOfWork,
):
    """Placeholder for cluster generation bridging if needed."""
    logger.info("Generating clusters (bridged)")
    # Legacy logic often does this inside find_duplicates or after
    # For now, just a stub to show where it goes
    await bus.dispatch(ClustersGenerated(clusters_count=0))

# --- UI Bridging Handlers ---

async def handle_scan_started_ui(event: ScanStarted, adapter: GuiEventAdapter):
    adapter.on_scan_started(event)

async def handle_scan_completed_ui(event: ScanCompleted, adapter: GuiEventAdapter):
    adapter.on_scan_completed(event)

async def handle_dedupe_started_ui(event: DeduplicationStarted, adapter: GuiEventAdapter):
    adapter.on_dedupe_started(event)

async def handle_duplicates_found_ui(event: DuplicatesFound, adapter: GuiEventAdapter):
    adapter.on_duplicates_found(event)

async def handle_clusters_generated_ui(event: ClustersGenerated, adapter: GuiEventAdapter):
    adapter.on_clusters_generated(event)

# --- Domain Logic Chains ---

async def handle_trigger_dedupe_on_scan_completed(
    event: ScanCompleted,
    bus: MessageBus,
    session: ScanSession,
):
    """
    Automated chain: Scan is done -> Start Deduplication.
    Uses current parameters from the active ScanSession.
    """
    logger.info(f"Scan completed. Triggering deduplication with engine {session.engine}")
    await bus.dispatch(StartDeduplicationCommand(
        engine_type=session.engine,
        threshold=session.threshold,
        include_ignored=session.include_ignored,
        roots=session.roots
    ))
