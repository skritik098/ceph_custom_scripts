##  This script will compare the bucket stats from two sites or two different timestamp on the same site. Compares the num_objects between two Ceph RGW bucket stats JSON files
##  and prints the delta for common buckets.

## In this script, I have removed the filter for bucket of skipping bucket that have object/shard less concept and print all of the buckets

import sys
import json
import math # Still useful for completeness, though not strictly needed for filter anymore

def parse_ceph_json_file(filepath):
    """
    Parses a Ceph RGW bucket stats JSON file and extracts bucket name and num_objects.
    Returns a dictionary mapping bucket names to their num_objects.
    """
    bucket_data = {}
    try:
        with open(filepath, 'r') as f:
            raw_data = json.load(f)

        if not isinstance(raw_data, list):
            print(f"Error: Expected JSON to be a list/array in {filepath}", file=sys.stderr)
            return bucket_data

        for bucket_stat in raw_data:
            bucket_name = bucket_stat.get('bucket')
            usage_main = bucket_stat.get('usage', {}).get('rgw.main', {})
            num_objects = usage_main.get('num_objects') # This can be null/None if not present

            # Handle potential None values for num_objects (mimicking jq's // 0)
            current_num_objects = num_objects if num_objects is not None else 0
            
            # --- REMOVED THE OBJECTS_PER_SHARD FILTER HERE ---
            # All buckets will be processed, regardless of objects_per_shard
            
            if bucket_name:
                bucket_data[bucket_name] = current_num_objects
            else:
                print(f"Warning: Skipping bucket with no name in {filepath}: {bucket_stat}", file=sys.stderr)

    except FileNotFoundError:
        print(f"Error: Input JSON file not found at {filepath}", file=sys.stderr)
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"Error: Could not decode JSON from {filepath}: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"An unexpected error occurred while processing {filepath}: {e}", file=sys.stderr)
        sys.exit(1)
        
    return bucket_data

def compare_bucket_stats(file1_path, file2_path):
    """
    Compares the num_objects between two Ceph RGW bucket stats JSON files
    and prints the delta for all unique buckets, sorted by absolute delta.
    """
    print(f"Loading and parsing data from {file1_path} (Site 1)...", file=sys.stderr)
    data1 = parse_ceph_json_file(file1_path)
    print(f"Loading and parsing data from {file2_path} (Site 2)...", file=sys.stderr)
    data2 = parse_ceph_json_file(file2_path)

    comparison_results = []
    all_buckets = sorted(list(set(data1.keys()) | set(data2.keys()))) # Get all unique buckets from both files

    for bucket in all_buckets:
        objects1 = data1.get(bucket, 0)
        objects2 = data2.get(bucket, 0)

        delta = objects2 - objects1
        
        # Store results for later sorting
        comparison_results.append({
            'bucket': bucket,
            'objects1': objects1,
            'objects2': objects2,
            'delta': delta,
            'absolute_delta': abs(delta) # Store absolute delta for sorting
        })

    # Sort results by absolute_delta in descending order
    # If absolute deltas are equal, sort by actual delta (e.g., -100 before +100) or bucket name for consistency
    sorted_results = sorted(comparison_results, key=lambda x: x['absolute_delta'], reverse=True)

    print("\n--- Comparing Bucket Object Counts (Sorted by Absolute Delta) ---")
    print(f"{'Bucket Name':<40} {'Site 1 Objects':>15} {'Site 2 Objects':>15} {'Delta (Site2 - Site1)':>25}")
    print("-" * 95)

    found_deltas = False
    for item in sorted_results:
        bucket = item['bucket']
        objects1 = item['objects1']
        objects2 = item['objects2']
        delta = item['delta']

        # Determine how to display 'N/A' for added/removed buckets
        objects1_display = str(objects1) if bucket in data1 else 'N/A'
        objects2_display = str(objects2) if bucket in data2 else 'N/A'
        
        delta_display = str(delta)
        if bucket not in data1 and bucket in data2:
            delta_display = 'Bucket added/new in Site 2'
        elif bucket in data1 and bucket not in data2:
            delta_display = 'Bucket removed/not in Site 2'


        print(f"{bucket:<40} {objects1_display:>15} {objects2_display:>15} {delta_display:>25}")
        if delta != 0 or bucket not in data1 or bucket not in data2: # Mark as found if there's any change or addition/removal
            found_deltas = True

    if not found_deltas:
        print("No differences in object counts or bucket presence found between sites.")
    print("-" * 95)

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python compare_bucket_stats_all_buckets.py <path_to_site1_raw_json.txt> <path_to_site2_raw_json.txt>", file=sys.stderr)
        sys.exit(1)

    file1 = sys.argv[1]
    file2 = sys.argv[2]

    compare_bucket_stats(file1, file2)