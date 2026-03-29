"""
Log Analyzer - Tools for analyzing image processing logs
Provides insights into performance bottlenecks, stuck images, and processing patterns
"""
import os
import json
import gzip
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from collections import defaultdict, Counter
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

from .image_processor_logger import ProcessingPhase, LogLevel


class ImageProcessingLogAnalyzer:
    """
    Analyzes image processing logs to identify bottlenecks, stuck images, and performance patterns
    """

    def __init__(self, log_directory: str = "logs/image_processing"):
        self.log_directory = Path(log_directory)
        self.log_directory.mkdir(parents=True, exist_ok=True)

    def load_logs(self, session_id: Optional[str] = None, hours_back: int = 24) -> List[Dict[str, Any]]:
        """
        Load and parse log files

        Args:
            session_id: Specific session to analyze, or None for all recent sessions
            hours_back: How many hours back to look for logs

        Returns:
            List of parsed log events
        """
        cutoff_time = datetime.now() - timedelta(hours=hours_back)
        all_events = []

        # Load JSONL files
        for jsonl_file in self.log_directory.glob("*.jsonl"):
            if session_id and f"session_{session_id}" not in jsonl_file.name:
                continue

            try:
                with open(jsonl_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        if line.strip():
                            event = json.loads(line)
                            event_time = datetime.fromisoformat(event['timestamp'])

                            if event_time >= cutoff_time:
                                all_events.append(event)
            except Exception as e:
                print(f"Error reading {jsonl_file}: {e}")

        # Sort by timestamp
        all_events.sort(key=lambda x: x['timestamp'])
        return all_events

    def analyze_performance_bottlenecks(self, events: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analyze performance bottlenecks across all phases
        """
        phase_timings = defaultdict(list)
        operation_timings = defaultdict(list)
        error_counts = Counter()
        stuck_images = []

        for event in events:
            # Collect timing data
            if 'duration_ms' in event and event['duration_ms'] is not None:
                phase = event.get('phase', 'unknown')
                operation = event.get('operation', 'unknown')
                duration = event['duration_ms']

                phase_timings[phase].append(duration)
                operation_timings[f"{phase}_{operation}"].append(duration)

            # Collect errors
            if event.get('level') in ['ERROR', 'CRITICAL']:
                error_key = f"{event.get('phase', 'unknown')}_{event.get('operation', 'unknown')}"
                error_counts[error_key] += 1

            # Detect stuck images (events with very long duration)
            if event.get('duration_ms', 0) > 30000:  # 30 seconds
                stuck_images.append({
                    'image': event.get('image_context', {}).get('image_path', 'unknown'),
                    'phase': event.get('phase', 'unknown'),
                    'operation': event.get('operation', 'unknown'),
                    'duration_ms': event['duration_ms'],
                    'timestamp': event['timestamp']
                })

        # Calculate statistics
        bottleneck_report = {
            'phase_performance': {},
            'operation_performance': {},
            'error_hotspots': dict(error_counts.most_common(10)),
            'stuck_images': stuck_images[:20],  # Top 20 stuck images
            'total_events': len(events)
        }

        # Phase performance stats
        for phase, timings in phase_timings.items():
            if timings:
                bottleneck_report['phase_performance'][phase] = {
                    'count': len(timings),
                    'avg_ms': sum(timings) / len(timings),
                    'min_ms': min(timings),
                    'max_ms': max(timings),
                    'p95_ms': sorted(timings)[int(len(timings) * 0.95)],
                    'bottleneck_threshold': sum(timings) / len(timings) * 2  # 2x average
                }

        # Operation performance stats
        for operation, timings in operation_timings.items():
            if timings:
                bottleneck_report['operation_performance'][operation] = {
                    'count': len(timings),
                    'avg_ms': sum(timings) / len(timings),
                    'min_ms': min(timings),
                    'max_ms': max(timings),
                    'p95_ms': sorted(timings)[int(len(timings) * 0.95)]
                }

        return bottleneck_report

    def analyze_batch_processing(self, events: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analyze batch processing patterns and identify problematic batches
        """
        batch_stats = defaultdict(lambda: {
            'events': [],
            'start_time': None,
            'end_time': None,
            'total_images': 0,
            'processed_images': 0,
            'errors': 0,
            'stuck_images': 0
        })

        for event in events:
            batch_id = event.get('image_context', {}).get('batch_id')
            if not batch_id:
                continue

            batch = batch_stats[batch_id]
            batch['events'].append(event)

            # Track timing
            event_time = datetime.fromisoformat(event['timestamp'])
            if batch['start_time'] is None or event_time < batch['start_time']:
                batch['start_time'] = event_time
            if batch['end_time'] is None or event_time > batch['end_time']:
                batch['end_time'] = event_time

            # Count metrics
            if 'batch_progress' in event.get('operation', ''):
                perf = event.get('performance_metrics', {})
                batch['total_images'] = perf.get('total', 0)
                batch['processed_images'] = perf.get('completed', 0)

            if event.get('level') in ['ERROR', 'CRITICAL']:
                batch['errors'] += 1

            if event.get('performance_metrics', {}).get('stuck'):
                batch['stuck_images'] += 1

        # Calculate batch metrics
        batch_report = {}
        for batch_id, stats in batch_stats.items():
            events = stats['events']
            if not events:
                continue

            duration = (stats['end_time'] - stats['start_time']).total_seconds() if stats['start_time'] and stats['end_time'] else 0

            batch_report[batch_id] = {
                'duration_seconds': duration,
                'total_images': stats['total_images'],
                'processed_images': stats['processed_images'],
                'errors': stats['errors'],
                'stuck_images': stats['stuck_images'],
                'processing_rate': stats['processed_images'] / duration if duration > 0 else 0,
                'error_rate': stats['errors'] / max(stats['processed_images'], 1),
                'start_time': stats['start_time'].isoformat() if stats['start_time'] else None,
                'end_time': stats['end_time'].isoformat() if stats['end_time'] else None
            }

        return batch_report

    def identify_stuck_images(self, events: List[Dict[str, Any]], threshold_seconds: int = 30) -> List[Dict[str, Any]]:
        """
        Identify images that got stuck during processing
        """
        stuck_images = []

        # Group events by image
        image_events = defaultdict(list)
        for event in events:
            image_path = event.get('image_context', {}).get('image_path')
            if image_path:
                image_events[image_path].append(event)

        for image_path, events in image_events.items():
            # Find processing start and end times
            start_times = []
            end_times = []

            for event in events:
                if 'start' in event.get('operation', ''):
                    start_times.append(datetime.fromisoformat(event['timestamp']))
                if 'complete' in event.get('operation', '') or 'failed' in event.get('operation', ''):
                    end_times.append(datetime.fromisoformat(event['timestamp']))

            if start_times and end_times:
                earliest_start = min(start_times)
                latest_end = max(end_times)
                total_duration = (latest_end - earliest_start).total_seconds()

                if total_duration > threshold_seconds:
                    stuck_images.append({
                        'image_path': image_path,
                        'total_duration_seconds': total_duration,
                        'start_time': earliest_start.isoformat(),
                        'end_time': latest_end.isoformat(),
                        'event_count': len(events),
                        'error_events': sum(1 for e in events if e.get('level') in ['ERROR', 'CRITICAL'])
                    })

        # Sort by duration (most stuck first)
        stuck_images.sort(key=lambda x: x['total_duration_seconds'], reverse=True)
        return stuck_images

    def generate_performance_report(self, session_id: Optional[str] = None, hours_back: int = 24) -> Dict[str, Any]:
        """
        Generate a comprehensive performance report
        """
        events = self.load_logs(session_id, hours_back)

        if not events:
            return {'error': 'No log events found'}

        report = {
            'analysis_timestamp': datetime.now().isoformat(),
            'session_id': session_id,
            'hours_analyzed': hours_back,
            'total_events': len(events),
            'time_range': {
                'start': min(e['timestamp'] for e in events),
                'end': max(e['timestamp'] for e in events)
            }
        }

        # Performance bottlenecks
        report['performance_bottlenecks'] = self.analyze_performance_bottlenecks(events)

        # Batch processing analysis
        report['batch_analysis'] = self.analyze_batch_processing(events)

        # Stuck images
        report['stuck_images'] = self.identify_stuck_images(events)

        # Summary statistics
        report['summary'] = {
            'total_stuck_images': len(report['stuck_images']),
            'total_errors': sum(stats['errors'] for stats in report['batch_analysis'].values()),
            'avg_processing_rate': sum(stats.get('processing_rate', 0) for stats in report['batch_analysis'].values()) / max(len(report['batch_analysis']), 1),
            'most_common_errors': Counter(
                f"{e.get('phase', 'unknown')}_{e.get('operation', 'unknown')}"
                for e in events
                if e.get('level') in ['ERROR', 'CRITICAL']
            ).most_common(5)
        }

        return report

    def save_report(self, report: Dict[str, Any], output_file: Optional[str] = None) -> str:
        """
        Save analysis report to file
        """
        if not output_file:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"performance_report_{timestamp}.json"

        output_path = self.log_directory / output_file

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, default=str)

        return str(output_path)

    def print_summary_report(self, report: Dict[str, Any]):
        """
        Print a human-readable summary of the analysis
        """
        print("=" * 80)
        print("IMAGE PROCESSING PERFORMANCE ANALYSIS REPORT")
        print("=" * 80)

        print(f"Analysis Time: {report['analysis_timestamp']}")
        print(f"Hours Analyzed: {report['hours_analyzed']}")
        print(f"Total Events: {report['total_events']:,}")
        print()

        # Performance bottlenecks
        bottlenecks = report['performance_bottlenecks']
        print("PHASE PERFORMANCE BOTTLENECKS:")
        print("-" * 40)

        for phase, stats in bottlenecks['phase_performance'].items():
            print(f"{phase:<15} | Count: {stats['count']:>4} | Avg: {stats['avg_ms']:>6.1f}ms | P95: {stats['p95_ms']:>6.1f}ms")

        print()

        # Stuck images
        stuck = report['stuck_images']
        if stuck:
            print(f"🚨 STUCK IMAGES DETECTED: {len(stuck)}")
            print("-" * 40)
            for i, img in enumerate(stuck[:10]):  # Show top 10
                print(f"{i+1:2d}. {Path(img['image_path']).name} - {img['total_duration_seconds']:.1f}s")
            print()

        # Batch analysis
        batches = report['batch_analysis']
        if batches:
            print("BATCH PROCESSING SUMMARY:")
            print("-" * 40)

            for batch_id, stats in batches.items():
                success_rate = ((stats['processed_images'] - stats['errors']) / max(stats['processed_images'], 1)) * 100
                print(f"Batch {batch_id}: {stats['processed_images']}/{stats['total_images']} images | "
                      f"Rate: {stats['processing_rate']:.2f} img/s | Errors: {stats['errors']} | "
                      f"Success: {success_rate:.1f}%")
            print()

        # Error hotspots
        errors = bottlenecks['error_hotspots']
        if errors:
            print("ERROR HOTSPOTS:")
            print("-" * 40)
            for error_type, count in errors.items():
                print(f"{error_type}: {count} errors")
            print()

        print("=" * 80)


# Convenience functions
def analyze_recent_logs(hours_back: int = 24, save_report: bool = True) -> Dict[str, Any]:
    """
    Analyze recent logs and optionally save report
    """
    analyzer = ImageProcessingLogAnalyzer()
    report = analyzer.generate_performance_report(hours_back=hours_back)

    if save_report:
        report_file = analyzer.save_report(report)
        print(f"Report saved to: {report_file}")

    analyzer.print_summary_report(report)
    return report


def find_stuck_images(hours_back: int = 24, threshold_seconds: int = 30) -> List[Dict[str, Any]]:
    """
    Quickly find images that got stuck during processing
    """
    analyzer = ImageProcessingLogAnalyzer()
    events = analyzer.load_logs(hours_back=hours_back)
    stuck_images = analyzer.identify_stuck_images(events, threshold_seconds)

    if stuck_images:
        print(f"🚨 Found {len(stuck_images)} stuck images (>{threshold_seconds}s):")
        for i, img in enumerate(stuck_images[:10]):
            print(f"  {i+1}. {Path(img['image_path']).name} - {img['total_duration_seconds']:.1f}s")
    else:
        print("✅ No stuck images found in the analyzed period.")

    return stuck_images


if __name__ == "__main__":
    # Example usage
    print("Analyzing recent image processing logs...")
    analyze_recent_logs(hours_back=24)
