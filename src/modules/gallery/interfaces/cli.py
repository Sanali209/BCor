import argparse
import asyncio
import logging
import sys
from uuid import UUID

from ..application.ai_service import AiService
from ..application.uow import GalleryUnitOfWork
from ..infrastructure.chroma_adapter import ChromaAdapter
from ..infrastructure.vector_repository import ChromaVectorRepository
from src.modules.vision.adapters.wd_tagger_adapter import WDTaggerAdapter

logger = logging.getLogger(__name__)

async def scan_all(ids: list[str] = None):
    """Triggers AI scan for images."""
    # This is a simplified example. In a real BCor app, we'd use DI (Dishka)
    # to get these dependencies from the container.
    print(f"Scanning images: {ids or 'ALL'}")
    # Logic to iterate and call ai_service.run_full_scan
    pass

async def reindex():
    """Rebuilds Chroma index from database content."""
    print("Re-indexing vectors in Chroma...")
    # Logic to clear chroma and re-populate from SQL Image table
    pass

def main():
    parser = argparse.ArgumentParser(description="BCor Gallery Management CLI")
    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # Scan command
    scan_parser = subparsers.add_parser("scan", help="Run AI analysis on images")
    scan_parser.add_argument("--ids", nargs="+", help="Specific image IDs to scan")

    # Index command
    subparsers.add_parser("index", help="Re-index vectors in Chroma")

    # Maintenance command
    subparsers.add_parser("clean", help="Cleanup orphaned relations and metadata")

    args = parser.parse_args()

    if args.command == "scan":
        asyncio.run(scan_all(args.ids))
    elif args.command == "index":
        asyncio.run(reindex())
    elif args.command == "clean":
        print("Cleaning up system...")
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
