"""
LLM XMP Tagger - CLI Tool
AI-powered image tagging tool that writes tags directly to XMP metadata
"""
import sys
import os
import time
import argparse
from pathlib import Path
# Removed ProcessPoolExecutor - using sequential processing for reliability

# Add Python directory to path to access SLM framework
python_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if python_dir not in sys.path:
    sys.path.insert(0, python_dir)

from tagger_engine import TaggerEngine
from xmp_writer import XMPWriter
from loguru import logger

# Import comprehensive logging
from SLM.logging import (
    image_logger,
    ProcessingPhase,
    LogLevel,
    get_image_context,
    log_image_discovery,
    log_processing_stuck
)


def process_image_with_timeout(tagger_engine, xmp_writer, image_path_str, batch_id):
    """
    Process a single image with tag prediction and XMP writing

    Returns:
        tuple: (success: bool, general_tags: list, character_tags: list, rating: str, num_tags: int, error: str)
    """
    try:
        # Tag prediction phase
        general_tags, character_tags, rating = tagger_engine.predict(image_path_str, batch_id=batch_id)

        # XMP writing phase
        success, num_tags, error = xmp_writer.write_tags(
            image_path_str, general_tags, character_tags, rating, batch_id=batch_id
        )

        return (success, general_tags, character_tags, rating, num_tags, error)

    except Exception as e:
        error_msg = str(e)
        return (False, [], [], None, 0, error_msg)


def print_header():
    """Print application header"""
    print("=" * 60)
    print("LLM XMP Tagger - AI-Powered Image Tagging Tool")
    print("=" * 60)


def print_stats(files_found, files_processed, files_skipped, tags_added, errors, timeouts, elapsed):
    """Print detailed statistics"""
    speed = files_processed / elapsed if elapsed > 0 else 0

    print(f"\n{'='*60}")
    print("PROCESSING COMPLETE - DETAILED REPORT")
    print(f"{'='*60}")

    print(f"📁 Files Found:      {files_found:,}")
    print(f"✅ Processed:        {files_processed:,}")
    print(f"⏭️  Skipped:          {files_skipped:,} (already tagged)")
    print(f"🏷️  Tags Added:       {tags_added:,}")
    print(f"❌ Errors:           {errors:,}")
    print(f"⏰ Timeouts:         {timeouts:,} (3min limit)")
    print(f"⏱️  Time Elapsed:     {elapsed:.2f}s")
    print(f"⚡ Speed:            {speed:.2f} files/sec")

    if files_found > 0:
        success_rate = ((files_processed - errors - timeouts) / files_found) * 100
        print(f"📊 Success Rate:     {success_rate:.1f}%")

    print(f"{'='*60}")


def run_cli_mode(folder_path: str, verbose: bool = True):
    """Run in CLI mode with detailed reporting and comprehensive logging"""
    # Generate batch ID for this processing session
    batch_id = f"batch_{int(time.time())}"

    if verbose:
        print_header()
        print(f"📂 Scanning folder recursively: {folder_path}")
        print(f"🔖 Batch ID: {batch_id}")

    # Phase 1: Discovery - Scan for images
    with image_logger.operation_context(ProcessingPhase.DISCOVERY, "folder_scan", get_image_context(folder_path, batch_id)):
        image_extensions = {'.jpg', '.jpeg', '.png', '.bmp', '.gif', '.webp'}
        image_files = []

        folder = Path(folder_path)
        for ext in image_extensions:
            image_files.extend(folder.glob(f"**/*{ext}"))
            image_files.extend(folder.glob(f"**/*{ext.upper()}"))

        total_files = len(image_files)

        image_logger.log_event(
            ProcessingPhase.DISCOVERY,
            LogLevel.INFO,
            get_image_context(folder_path, batch_id),
            "folder_scan_complete",
            f"Discovered {total_files} image files in {folder_path}",
            performance_metrics={'total_files': total_files, 'folder_path': folder_path}
        )

    if verbose:
        print(f"🖼️  Found {total_files} image files (including subdirectories)")

    if total_files == 0:
        print("❌ No images found. Exiting.")
        return

    # Phase 2: Model Loading
    if verbose:
        print("🤖 Loading AI model...")

    with image_logger.operation_context(ProcessingPhase.PREPROCESSING, "model_initialization", get_image_context(folder_path, batch_id)):
        tagger_engine = TaggerEngine()
        tagger_engine.load_model()

        image_logger.log_event(
            ProcessingPhase.PREPROCESSING,
            LogLevel.INFO,
            get_image_context(folder_path, batch_id),
            "model_ready",
            "AI tagging model loaded and ready for processing"
        )

    if verbose:
        print("✅ Model loaded successfully")

    xmp_writer = XMPWriter()

    # Phase 3: Batch Processing
    files_processed = 0
    files_skipped = 0
    tags_added = 0
    errors = 0
    timeouts = 0
    stuck_images = []
    start_time = time.time()

    if verbose:
        print(f"\n🚀 Processing {total_files} files...")
        print("-" * 60)

    for idx, image_path in enumerate(image_files):
        image_path_str = str(image_path)
        file_name = image_path.name

        # Log individual image discovery
        log_image_discovery(image_path_str, batch_id)

        # Check if already has WD tags
        if xmp_writer.has_wd_tags(image_path_str):
            files_skipped += 1
            if verbose:
                print(f"[{idx+1:4d}/{total_files}] ⏭️  Skipped: {file_name} (already tagged)")

            image_logger.log_event(
                ProcessingPhase.VALIDATION,
                LogLevel.INFO,
                get_image_context(image_path_str, batch_id),
                "image_skipped",
                f"Image already has WD tags: {file_name}"
            )
            files_processed += 1
            continue

        # Process individual image sequentially (no timeout needed - runs in main thread)
        image_start_time = time.time()

        try:
            # Call processing function directly in main thread
            result = process_image_with_timeout(tagger_engine, xmp_writer, image_path_str, batch_id)

            processing_time = time.time() - image_start_time
            success, general_tags, character_tags, rating, num_tags, error = result

            if success:
                tags_added += num_tags
                if verbose:
                    print(f"[{idx+1:4d}/{total_files}] ✅ Processed: {file_name} (+{num_tags} tags, {processing_time:.2f}s)")

                image_logger.log_event(
                    ProcessingPhase.POST_PROCESSING,
                    LogLevel.INFO,
                    get_image_context(image_path_str, batch_id),
                    "image_processing_complete",
                    f"Successfully processed {file_name}: +{num_tags} tags in {processing_time:.2f}s",
                    duration_ms=processing_time * 1000,
                    performance_metrics={
                        'tags_added': num_tags,
                        'processing_time_seconds': processing_time,
                        'general_tags': len(general_tags),
                        'character_tags': len(character_tags),
                        'rating': rating
                    }
                )
            else:
                errors += 1
                if verbose:
                    print(f"[{idx+1:4d}/{total_files}] ❌ Error: {file_name} - {error}")

                image_logger.log_event(
                    ProcessingPhase.POST_PROCESSING,
                    LogLevel.ERROR,
                    get_image_context(image_path_str, batch_id),
                    "image_processing_failed",
                    f"Failed to write XMP for {file_name}: {error}",
                    duration_ms=processing_time * 1000,
                    error_details=error
                )

        except Exception as e:
            processing_time = time.time() - image_start_time
            errors += 1
            error_msg = str(e)

            # Check if this might be a stuck image (processing took too long)
            if processing_time > 30:  # 30 seconds threshold
                stuck_images.append(image_path_str)
                log_processing_stuck(image_path_str, ProcessingPhase.INFERENCE, "tag_prediction", processing_time, batch_id)

            if verbose:
                print(f"[{idx+1:4d}/{total_files}] 💥 Error processing {file_name}: {error_msg}")

            logger.error(f"Error processing {image_path_str}: {e}")

            image_logger.log_event(
                ProcessingPhase.POST_PROCESSING,
                LogLevel.CRITICAL,
                get_image_context(image_path_str, batch_id),
                "image_processing_crashed",
                f"Critical error processing {file_name}: {error_msg}",
                duration_ms=processing_time * 1000,
                error_details=error_msg
            )

        files_processed += 1

        # Periodic progress logging and stuck image detection
        if (idx + 1) % 10 == 0 or (idx + 1) == total_files:
            elapsed = time.time() - start_time
            image_logger.log_batch_progress(batch_id, files_processed, total_files, stuck_images)

            # Check for stuck images every 10 images
            stuck_report = image_logger.get_stuck_images_report(timeout_seconds=60)
            if stuck_report:
                print(f"🚨 STUCK IMAGES DETECTED: {len(stuck_report)}")
                for stuck in stuck_report[:3]:  # Show first 3
                    print(f"   - {stuck['image_path']} stuck in {stuck['operation']} for {stuck['elapsed_seconds']:.1f}s")

    # Phase 4: Final Summary and Performance Report
    elapsed = time.time() - start_time

    # Generate comprehensive performance report
    performance_report = image_logger.get_performance_report()

    image_logger.log_event(
        ProcessingPhase.CLEANUP,
        LogLevel.INFO,
        get_image_context(folder_path, batch_id),
        "batch_processing_complete",
        f"Batch {batch_id} completed: {files_processed}/{total_files} processed, {tags_added} tags added, {errors} errors, {timeouts} timeouts",
        duration_ms=elapsed * 1000,
        performance_metrics={
            'total_files': total_files,
            'files_processed': files_processed,
            'files_skipped': files_skipped,
            'tags_added': tags_added,
            'errors': errors,
            'timeouts': timeouts,
            'stuck_images': len(stuck_images),
            'elapsed_seconds': elapsed,
            'processing_rate': files_processed / elapsed if elapsed > 0 else 0
        }
    )

    # Print final statistics
    print_stats(total_files, files_processed, files_skipped, tags_added, errors, timeouts, elapsed)

    # Print stuck images warning if any
    if stuck_images:
        print(f"\n🚨 WARNING: {len(stuck_images)} images appeared to get stuck during processing:")
        for stuck_image in stuck_images[:5]:  # Show first 5
            print(f"   - {Path(stuck_image).name}")
        if len(stuck_images) > 5:
            print(f"   ... and {len(stuck_images) - 5} more")

    # Print performance insights
    if verbose and performance_report['phase_timings']:
        print(f"\n⚡ PERFORMANCE INSIGHTS:")
        for phase_op, stats in performance_report['phase_timings'].items():
            if stats['count'] > 0:
                print(f"   {phase_op}: {stats['avg_ms']:.1f}ms avg ({stats['count']} operations)")


def main():
    """Run the CLI application"""
    parser = argparse.ArgumentParser(
        description="LLM XMP Tagger - AI-powered image tagging tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s "D:\\Images\\dataset"          # Process specific folder
  %(prog)s                               # Interactive folder selection
  %(prog)s --quiet "D:\\Images\\dataset" # Quiet mode, minimal output
        """
    )
    parser.add_argument(
        "folder",
        nargs="?",
        help="Folder path containing images to process"
    )
    parser.add_argument(
        "--quiet", "-q",
        action="store_true",
        help="Quiet mode - minimal output, only final statistics"
    )

    args = parser.parse_args()

    folder_path = args.folder
    verbose = not args.quiet

    # If no folder provided, ask interactively
    if not folder_path:
        if verbose:
            print_header()
            print("📂 Enter the folder path containing images to process:")
            print("   (You can drag and drop the folder into the terminal)")
        folder_path = input("> ").strip().strip('"').strip("'")

    if not folder_path:
        print("❌ Error: No folder path provided")
        return

    if not os.path.exists(folder_path):
        print(f"❌ Error: Folder does not exist: {folder_path}")
        return

    if not os.path.isdir(folder_path):
        print(f"❌ Error: Path is not a directory: {folder_path}")
        return

    run_cli_mode(folder_path, verbose=verbose)


if __name__ == "__main__":
    main()
