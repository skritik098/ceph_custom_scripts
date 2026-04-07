##  This script will compare the bucket stats from two sites or two different timestamp on the same site. Compares the num_objects between two Ceph RGW bucket stats JSON files
##  and prints the delta for common buckets.


import sys
import json
import math # For math.floor

def parse_ceph_json_file(filepath):
    """
    Parses a Ceph RGW bucket stats JSON file, applies the filtering logic
    and extracts bucket name, num_objects, and calculates objects_per_shard.
    Returns a dictionary mapping bucket names to their num_objects.
    """
    bucket_data = {}
    try:
        with open(filepath, 'r') as f:
            raw_data = json.load(f)

        # Assuming the JSON structure is an array of objects, similar to jq's .[]
        if not isinstance(raw_data, list):
            print(f"Error: Expected JSON to be a list/array in {filepath}", file=sys.stderr)
            return bucket_data

        for bucket_stat in raw_data:
            bucket_name = bucket_stat.get('bucket')
            num_shards = bucket_stat.get('num_shards')
            usage_main = bucket_stat.get('usage', {}).get('rgw.main', {})
            num_objects = usage_main.get('num_objects') # This can be null/None if not present

            # Apply the filtering logic from your jq command:
            # select(( (.usage."rgw.main".num_objects // 0) / .num_shards | floor) > 20000)
            
            # Handle potential None values for num_objects and num_shards
            current_num_objects = num_objects if num_objects is not None else 0
            
            # If num_shards is 0 or None, division by zero is an issue.
            # The original jq uses `// 0` for num_objects, effectively treating missing as 0.
            # For num_shards, if it's 0, division by zero will occur.
            # Let's mimic jq's behavior: if num_shards is 0 or None, objects_per_shard can be considered 0 for comparison.
            
            objects_per_shard = 0
            if num_shards is not None and num_shards > 0:
                objects_per_shard = math.floor(current_num_objects / num_shards)
            
            # Apply the filter condition
            if objects_per_shard > 2000:
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
    and prints the delta for common buckets.
    """
    print(f"Loading and parsing data from {file1_path} (Site 1)...", file=sys.stderr)
    data1 = parse_ceph_json_file(file1_path)
    print(f"Loading and parsing data from {file2_path} (Site 2)...", file=sys.stderr)
    data2 = parse_ceph_json_file(file2_path)

    print("\n--- Comparing Bucket Object Counts ---")
    print(f"{'Bucket Name':<40} {'Site 1 Objects':>15} {'Site 2 Objects':>15} {'Delta (Site2 - Site1)':>25}")
    print("-" * 95)

    found_deltas = False
    all_buckets = sorted(list(set(data1.keys()) | set(data2.keys()))) # Get all unique buckets from both files

    for bucket in all_buckets:
        objects1 = data1.get(bucket, 0)
        objects2 = data2.get(bucket, 0)

        delta = objects2 - objects1

        if bucket in data1 and bucket in data2:
            print(f"{bucket:<40} {objects1:>15} {objects2:>15} {delta:>25}")
            found_deltas = True
        elif bucket in data1 and bucket not in data2:
            print(f"{bucket:<40} {objects1:>15} {'N/A':>15} {'Bucket removed/not in Site 2':>25}")
            found_deltas = True
        elif bucket not in data1 and bucket in data2:
            print(f"{bucket:<40} {'N/A':>15} {objects2:>15} {'Bucket added/new in Site 2':>25}")
            found_deltas = True

    if not found_deltas:
        print("No common buckets with a delta or no changes found.")
    print("-" * 95)

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python compare_bucket_stats_internal_json.py <path_to_site1_raw_json.txt> <path_to_site2_raw_json.txt>", file=sys.stderr)
        sys.exit(1)

    file1 = sys.argv[1]
    file2 = sys.argv[2]

    compare_bucket_stats(file1, file2)