#!/usr/bin/env python3
"""
Compare Bucket Stats

Compares bucket statistics between two Ceph RGW snapshots and calculates
object count deltas. Optionally filters by objects-per-shard threshold.

This script consolidates the functionality of:
- compare_bucket_stats_internal_json.py (v1 - with filtering)
- compare_bucket_stats_internal_json-v2.py (no filtering, sorted by delta)

Version: 2.0.0
"""

import sys
import argparse
import math
from pathlib import Path
from typing import Dict, List, Tuple

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.bucket_parser import parse_bucket_json, calculate_objects_per_shard
from utils.formatters import format_table_output, format_json_output, format_csv_output
from utils.validators import (
    validate_file_exists,
    validate_json_file,
    validate_threshold,
    validate_output_format,
    handle_error
)


def filter_by_objects_per_shard(bucket_data: Dict, threshold: int) -> Dict:
    """
    Filter buckets by objects per shard threshold.
    
    Args:
        bucket_data: Dictionary of bucket data
        threshold: Minimum objects per shard (0 = no filter)
        
    Returns:
        Filtered bucket data dictionary
    """
    if threshold == 0:
        return bucket_data
    
    filtered = {}
    for bucket_name, data in bucket_data.items():
        objects_per_shard = data.get('objects_per_shard', 0)
        if objects_per_shard > threshold:
            filtered[bucket_name] = data
    
    return filtered


def compare_bucket_stats(data1: Dict, data2: Dict, show_all: bool = False) -> List[Dict]:
    """
    Compare bucket statistics between two datasets.
    
    Args:
        data1: Bucket data from first snapshot (old)
        data2: Bucket data from second snapshot (new)
        show_all: Whether to show buckets with no changes
        
    Returns:
        List of comparison result dictionaries
    """
    results = []
    all_buckets = set(data1.keys()).union(set(data2.keys()))
    
    for bucket in all_buckets:
        objects1 = data1.get(bucket, {}).get('num_objects', 0)
        objects2 = data2.get(bucket, {}).get('num_objects', 0)
        
        delta = objects2 - objects1
        
        # Skip if no change and show_all is False
        if not show_all and delta == 0 and bucket in data1 and bucket in data2:
            continue
        
        result = {
            'bucket': bucket,
            'old_objects': objects1 if bucket in data1 else 'N/A',
            'new_objects': objects2 if bucket in data2 else 'N/A',
            'delta': delta,
            'abs_delta': abs(delta),
            'status': 'changed'
        }
        
        # Determine status
        if bucket not in data1 and bucket in data2:
            result['status'] = 'added'
            result['delta'] = f"Added ({objects2} objects)"
        elif bucket in data1 and bucket not in data2:
            result['status'] = 'removed'
            result['delta'] = f"Removed ({objects1} objects)"
        
        results.append(result)
    
    return results


def sort_results(results: List[Dict], sort_by: str) -> List[Dict]:
    """
    Sort comparison results.
    
    Args:
        results: List of result dictionaries
        sort_by: Sort criteria ('delta', 'abs-delta', or 'name')
        
    Returns:
        Sorted list of results
    """
    if sort_by == 'delta':
        return sorted(results, key=lambda x: x.get('abs_delta', 0) if isinstance(x['delta'], int) else 0, reverse=True)
    elif sort_by == 'abs-delta':
        return sorted(results, key=lambda x: x.get('abs_delta', 0), reverse=True)
    else:  # name
        return sorted(results, key=lambda x: x['bucket'])


def format_output(results: List[Dict], output_format: str) -> str:
    """
    Format results in the specified output format.
    
    Args:
        results: List of result dictionaries
        output_format: 'table', 'json', or 'csv'
        
    Returns:
        Formatted output string
    """
    if not results:
        return "No differences in object counts or bucket presence found between snapshots."
    
    headers = ['bucket', 'old_objects', 'new_objects', 'delta']
    
    # Prepare data for output (remove internal fields)
    output_data = []
    for r in results:
        output_data.append({
            'bucket': r['bucket'],
            'old_objects': r['old_objects'],
            'new_objects': r['new_objects'],
            'delta': r['delta']
        })
    
    if output_format == 'json':
        return format_json_output(output_data)
    elif output_format == 'csv':
        return format_csv_output(output_data, headers)
    else:  # table
        return format_table_output(output_data, headers)


def main():
    """Main function."""
    parser = argparse.ArgumentParser(
        description="Compare RadosGW bucket statistics between two snapshots",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic comparison (filters buckets with >2000 objects/shard)
  %(prog)s old_stats.json new_stats.json

  # Compare all buckets (no filtering)
  %(prog)s old_stats.json new_stats.json --min-objects-per-shard 0

  # Sort by delta instead of absolute delta
  %(prog)s old_stats.json new_stats.json --sort-by delta

  # Show all buckets including those with no changes
  %(prog)s old_stats.json new_stats.json --show-all

  # Output as CSV
  %(prog)s old_stats.json new_stats.json --output-format csv

Version: 2.0.0
Consolidates: compare_bucket_stats_internal_json.py (v1, v2)
        """
    )
    
    parser.add_argument('old_stats_file',
                       help='Path to older bucket stats JSON file')
    parser.add_argument('new_stats_file',
                       help='Path to newer bucket stats JSON file')
    parser.add_argument('--min-objects-per-shard', type=int, default=2000,
                       help='Minimum objects/shard threshold (0=no filter, default: 2000)')
    parser.add_argument('--sort-by', choices=['delta', 'abs-delta', 'name'], default='abs-delta',
                       help='Sort criteria (default: abs-delta)')
    parser.add_argument('--output-format', choices=['table', 'json', 'csv'], default='table',
                       help='Output format (default: table)')
    parser.add_argument('--show-all', action='store_true',
                       help='Show all buckets including those with no changes')
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Enable verbose output')
    parser.add_argument('--version', action='version', version='%(prog)s 2.0.0')
    
    args = parser.parse_args()
    
    try:
        # Validate inputs
        validate_file_exists(args.old_stats_file, "Old stats file")
        validate_file_exists(args.new_stats_file, "New stats file")
        validate_json_file(args.old_stats_file)
        validate_json_file(args.new_stats_file)
        validate_threshold(args.min_objects_per_shard, min_value=0)
        validate_output_format(args.output_format)
        
        if args.verbose:
            print(f"Loading old stats from: {args.old_stats_file}", file=sys.stderr)
        
        # Parse data files
        old_data = parse_bucket_json(args.old_stats_file)
        
        if args.verbose:
            print(f"Loading new stats from: {args.new_stats_file}", file=sys.stderr)
        
        new_data = parse_bucket_json(args.new_stats_file)
        
        if not old_data and not new_data:
            print("Error: No bucket data loaded from either file.", file=sys.stderr)
            sys.exit(1)
        
        if args.verbose:
            print(f"Old snapshot: {len(old_data)} buckets", file=sys.stderr)
            print(f"New snapshot: {len(new_data)} buckets", file=sys.stderr)
        
        # Apply filtering if threshold > 0
        if args.min_objects_per_shard > 0:
            if args.verbose:
                print(f"Filtering buckets with >{args.min_objects_per_shard} objects/shard", file=sys.stderr)
            
            old_data = filter_by_objects_per_shard(old_data, args.min_objects_per_shard)
            new_data = filter_by_objects_per_shard(new_data, args.min_objects_per_shard)
            
            if args.verbose:
                print(f"After filtering - Old: {len(old_data)}, New: {len(new_data)}", file=sys.stderr)
        
        # Compare bucket stats
        results = compare_bucket_stats(old_data, new_data, args.show_all)
        
        if args.verbose:
            print(f"Found {len(results)} buckets with changes", file=sys.stderr)
        
        # Sort results
        sorted_results = sort_results(results, args.sort_by)
        
        # Format and print output
        if args.output_format == 'table':
            if args.min_objects_per_shard > 0:
                print(f"\n--- Comparing Bucket Object Counts (filtered by >{args.min_objects_per_shard} objects/shard) ---")
            else:
                print("\n--- Comparing Bucket Object Counts (all buckets) ---")
        
        output = format_output(sorted_results, args.output_format)
        print(output)
        
        if args.output_format == 'table':
            print("-" * 95)
        
    except KeyboardInterrupt:
        print("\nOperation cancelled by user.", file=sys.stderr)
        sys.exit(130)
    except Exception as e:
        handle_error(e, show_traceback=args.verbose if 'verbose' in args else False)


if __name__ == "__main__":
    main()

# Made with Bob
