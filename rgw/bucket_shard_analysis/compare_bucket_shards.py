#!/usr/bin/env python3
"""
Compare Bucket Shards

Compares bucket shard counts between two Ceph RGW sites and identifies
buckets with different shard configurations and relatively small object counts.

This script consolidates the functionality of:
- compare_bucket_shards.py (v1)
- compare_bucket_shards-v2.py (dynamic column widths)
- compare_bucket_shards-v3.py (sorting options)

Version: 2.0.0
"""

import sys
import argparse
from pathlib import Path
from typing import Dict, List, Tuple

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.bucket_parser import parse_bucket_json
from utils.formatters import format_table_output, format_json_output, format_csv_output
from utils.validators import (
    validate_file_exists,
    validate_json_file,
    validate_percentile,
    validate_sort_order,
    validate_output_format,
    handle_error
)


def calculate_percentile_threshold(all_objects: List[int], percentile: float) -> int:
    """
    Calculate the threshold value at the given percentile.
    
    Args:
        all_objects: List of object counts
        percentile: Percentile value (0.0 to 1.0)
        
    Returns:
        Threshold value at the percentile
    """
    if not all_objects:
        return 0
    
    sorted_objects = sorted(all_objects)
    percentile = max(0.0, min(1.0, percentile))
    
    index = int(len(sorted_objects) * percentile)
    if index >= len(sorted_objects):
        index = len(sorted_objects) - 1
    if index < 0:
        index = 0
    
    return sorted_objects[index]


def find_discrepant_buckets(site1_data: Dict, site2_data: Dict) -> Tuple[List[Dict], List[int]]:
    """
    Find buckets with different shard counts between two sites.
    
    Args:
        site1_data: Bucket data from site 1
        site2_data: Bucket data from site 2
        
    Returns:
        Tuple of (discrepant_buckets, all_object_counts)
    """
    discrepant_buckets = []
    all_num_objects = []
    
    all_bucket_names = set(site1_data.keys()).union(set(site2_data.keys()))
    
    for bucket_name in all_bucket_names:
        s1_info = site1_data.get(bucket_name)
        s2_info = site2_data.get(bucket_name)
        
        if s1_info and s2_info:
            all_num_objects.append(s1_info['num_objects'])
            all_num_objects.append(s2_info['num_objects'])
            
            if s1_info['num_shards'] != s2_info['num_shards']:
                discrepant_buckets.append({
                    'bucket': bucket_name,
                    'site1_shards': s1_info['num_shards'],
                    'site2_shards': s2_info['num_shards'],
                    'site1_objects': s1_info['num_objects'],
                    'site2_objects': s2_info['num_objects']
                })
        elif s1_info:
            all_num_objects.append(s1_info['num_objects'])
        elif s2_info:
            all_num_objects.append(s2_info['num_objects'])
    
    return discrepant_buckets, all_num_objects


def filter_by_threshold(buckets: List[Dict], threshold: int) -> List[Dict]:
    """
    Filter buckets by object count threshold.
    
    Args:
        buckets: List of bucket dictionaries
        threshold: Object count threshold
        
    Returns:
        Filtered list of buckets
    """
    filtered = []
    for bucket in buckets:
        min_objects = min(bucket['site1_objects'], bucket['site2_objects'])
        if min_objects <= threshold:
            filtered.append(bucket)
    return filtered


def sort_results(buckets: List[Dict], sort_order: str) -> List[Dict]:
    """
    Sort bucket results by site1 object count.
    
    Args:
        buckets: List of bucket dictionaries
        sort_order: 'asc' or 'desc'
        
    Returns:
        Sorted list of buckets
    """
    reverse = (sort_order == 'desc')
    return sorted(buckets, key=lambda x: x['site1_objects'], reverse=reverse)


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
        return "No buckets found matching the criteria (different shard counts AND relatively small objects)."
    
    headers = ['bucket', 'site1_shards', 'site2_shards', 'site1_objects', 'site2_objects']
    
    if output_format == 'json':
        return format_json_output(results)
    elif output_format == 'csv':
        return format_csv_output(results, headers)
    else:  # table
        return format_table_output(results, headers)


def main():
    """Main function."""
    parser = argparse.ArgumentParser(
        description="Compare RadosGW bucket shard counts between two sites",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic comparison with default settings (25th percentile, ascending sort)
  %(prog)s site1.json site2.json

  # Show all buckets (no filtering by object count)
  %(prog)s site1.json site2.json --percentile 1.0

  # Sort by descending object count
  %(prog)s site1.json site2.json --sort-order desc

  # Output as JSON
  %(prog)s site1.json site2.json --output-format json

  # Combine options
  %(prog)s site1.json site2.json --percentile 0.5 --sort-order desc --output-format csv

Version: 2.0.0
Consolidates: compare_bucket_shards.py (v1, v2, v3)
        """
    )
    
    parser.add_argument('site1_file', 
                       help='Path to Site 1 bucket stats JSON file')
    parser.add_argument('site2_file', 
                       help='Path to Site 2 bucket stats JSON file')
    parser.add_argument('--percentile', type=float, default=0.25,
                       help='Percentile threshold for small objects (0.0-1.0, default: 0.25)')
    parser.add_argument('--sort-order', choices=['asc', 'desc'], default='asc',
                       help='Sort order by Site 1 object count (default: asc)')
    parser.add_argument('--output-format', choices=['table', 'json', 'csv'], default='table',
                       help='Output format (default: table)')
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Enable verbose output')
    parser.add_argument('--version', action='version', version='%(prog)s 2.0.0')
    
    args = parser.parse_args()
    
    try:
        # Validate inputs
        validate_file_exists(args.site1_file, "Site 1 file")
        validate_file_exists(args.site2_file, "Site 2 file")
        validate_json_file(args.site1_file)
        validate_json_file(args.site2_file)
        validate_percentile(args.percentile)
        validate_sort_order(args.sort_order)
        validate_output_format(args.output_format)
        
        if args.verbose:
            print(f"Loading Site 1 data from: {args.site1_file}", file=sys.stderr)
        
        # Parse data files
        site1_data = parse_bucket_json(args.site1_file)
        
        if args.verbose:
            print(f"Loading Site 2 data from: {args.site2_file}", file=sys.stderr)
        
        site2_data = parse_bucket_json(args.site2_file)
        
        if not site1_data and not site2_data:
            print("Error: No bucket data loaded from either file.", file=sys.stderr)
            sys.exit(1)
        
        if args.verbose:
            print(f"Site 1: {len(site1_data)} buckets", file=sys.stderr)
            print(f"Site 2: {len(site2_data)} buckets", file=sys.stderr)
        
        # Find buckets with different shard counts
        discrepant_buckets, all_num_objects = find_discrepant_buckets(site1_data, site2_data)
        
        if args.verbose:
            print(f"Found {len(discrepant_buckets)} buckets with different shard counts", file=sys.stderr)
        
        # Calculate threshold
        threshold = calculate_percentile_threshold(all_num_objects, args.percentile)
        
        if args.verbose or args.output_format == 'table':
            if args.percentile < 1.0:
                print(f"\nCalculated 'small objects' threshold (approx. {args.percentile*100:.0f}th percentile): {threshold}", file=sys.stderr)
            else:
                print("\nPercentile set to 100%, showing all buckets with different shard counts.", file=sys.stderr)
        
        # Filter by threshold
        filtered_results = filter_by_threshold(discrepant_buckets, threshold)
        
        if args.verbose:
            print(f"After filtering: {len(filtered_results)} buckets", file=sys.stderr)
        
        # Sort results
        sorted_results = sort_results(filtered_results, args.sort_order)
        
        # Format and print output
        if args.output_format == 'table':
            print("\n--- Buckets with Different Shard Counts and Relatively Small Objects ---")
        
        output = format_output(sorted_results, args.output_format)
        print(output)
        
    except KeyboardInterrupt:
        print("\nOperation cancelled by user.", file=sys.stderr)
        sys.exit(130)
    except Exception as e:
        handle_error(e, show_traceback=args.verbose if 'verbose' in args else False)


if __name__ == "__main__":
    main()

# Made with Bob
