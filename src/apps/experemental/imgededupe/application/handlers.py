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
    await bus.publish(DeduplicationStarted(engine_type=cmd.engine_type))
    
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
    await bus.publish(DuplicatesFound(relations_count=len(results)))

async def handle_start_scan(
    cmd: StartScanCommand,
    scanner: Scanner,
    bus: MessageBus,
    uow: SqliteUnitOfWork,
):
    """Handler for StartScanCommand."""
    logger.info(f"Starting scan in {cmd.roots}")
    await bus.publish(ScanStarted(roots=cmd.roots))
    
    # Bridge to legacy logic
    count = scanner.scan(roots=cmd.roots, recursive=cmd.recursive)
    
    logger.info(f"Scan finished. Processed {count} files.")
    await bus.publish(ScanCompleted(files_count=count))

async def handle_generate_clusters(
    # This might need a Command in messages.py
    bus: MessageBus,
    deduper: Deduper,
    uow: SqliteUnitOfWork,
):
    """Placeholder for cluster generation bridging if needed."""
    logger.info("Generating clusters (bridged)")
    # Legacy logic often does this inside find_duplicates or after
    # For now, just a stub to show where it goes
    await bus.publish(ClustersGenerated(clusters_count=0))
