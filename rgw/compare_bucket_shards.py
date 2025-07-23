import sys
import json
import argparse # For parsing command-line arguments
import statistics # For calculating percentile (though we'll use sort/index for simplicity)

def parse_bucket_data_from_file(filepath):
    """Reads JSON data from a file and returns a dictionary of bucket data."""
    try:
        with open(filepath, 'r') as f:
            raw_data = f.read()
            if not raw_data.strip():
                print(f"Warning: File '{filepath}' is empty or contains only whitespace.", file=sys.stderr)
                return {}
            
            parsed_json = json.loads(raw_data)
            
            data = {}
            for item in parsed_json:
                bucket_name = item.get('bucket')
                num_shards = item.get('num_shards')
                # Use .get() with a default for safety, especially for nested keys
                num_objects = item.get('usage', {}).get('rgw.main', {}).get('num_objects', 0)

                if bucket_name is not None and num_shards is not None:
                    data[bucket_name] = {'num_shards': num_shards, 'num_objects': num_objects}
            return data
    except FileNotFoundError:
        print(f"Error: File '{filepath}' not found.", file=sys.stderr)
        return {}
    except json.JSONDecodeError as e:
        print(f"Error: Could not decode JSON from '{filepath}': {e}", file=sys.stderr)
        return {}
    except Exception as e:
        print(f"An unexpected error occurred while processing '{filepath}': {e}", file=sys.stderr)
        return {}

def main():
    parser = argparse.ArgumentParser(description="Compare RadosGW bucket stats from two JSON files.")
    parser.add_argument('site1_file', help="Path to the radosgw-admin bucket stats JSON file for Site 1.")
    parser.add_argument('site2_file', help="Path to the radosgw-admin bucket stats JSON file for Site 2.")
    parser.add_argument('--percentile', type=float, default=0.25,
                        help="The percentile to use for the 'small objects' threshold (e.g., 0.25 for 25th percentile). Default: 0.25")

    args = parser.parse_args()

    site1_data = parse_bucket_data_from_file(args.site1_file)
    site2_data = parse_bucket_data_from_file(args.site2_file)

    if not site1_data and not site2_data:
        print("Error: No bucket data loaded from either file. Please check file paths and content.", file=sys.stderr)
        return

    # --- Find buckets with different shard counts ---
    discrepant_shard_buckets = []
    all_num_objects = []

    # Get all unique bucket names from both sites to ensure comprehensive comparison
    all_bucket_names = set(site1_data.keys()).union(set(site2_data.keys()))

    for bucket_name in all_bucket_names:
        s1_info = site1_data.get(bucket_name)
        s2_info = site2_data.get(bucket_name)

        # If a bucket exists on both sites
        if s1_info and s2_info:
            all_num_objects.append(s1_info['num_objects'])
            all_num_objects.append(s2_info['num_objects'])

            if s1_info['num_shards'] != s2_info['num_shards']:
                discrepant_shard_buckets.append({
                    'bucket': bucket_name,
                    'site1_shards': s1_info['num_shards'],
                    'site2_shards': s2_info['num_shards'],
                    'site1_objects': s1_info['num_objects'],
                    'site2_objects': s2_info['num_objects']
                })
        elif s1_info: # Only on Site 1
             all_num_objects.append(s1_info['num_objects'])
        elif s2_info: # Only on Site 2
            all_num_objects.append(s2_info['num_objects'])


    # --- Determine "small objects" threshold ---
    if not all_num_objects:
        print("No object data to analyze for thresholding. Setting threshold to 0.", file=sys.stderr)
        small_objects_threshold = 0
    else:
        all_num_objects.sort()
        # Calculate percentile. Ensure index is valid and handle edge cases.
        if len(all_num_objects) > 0:
            # Ensure percentile is within [0, 1]
            percentile_val = max(0.0, min(1.0, args.percentile))
            
            # Calculate the index for the given percentile
            # Using floor to get a conservative index for "at or below"
            index = int(len(all_num_objects) * percentile_val)
            
            # Adjust index for 0-based list and ensure it's not out of bounds
            if index >= len(all_num_objects):
                index = len(all_num_objects) - 1
            if index < 0:
                index = 0
            
            small_objects_threshold = all_num_objects[index]
        else:
            small_objects_threshold = 0


    print(f"\nCalculated 'small objects' threshold (approx. {args.percentile*100:.0f}th percentile of all observed num_objects): {small_objects_threshold}")

    # --- Filter for buckets with small objects among those with discrepant shards ---
    final_results = []
    for bucket in discrepant_shard_buckets:
        # Use the lower num_objects between the two sites for comparison against threshold
        min_objects_for_bucket = min(bucket['site1_objects'], bucket['site2_objects'])
        if min_objects_for_bucket <= small_objects_threshold:
            final_results.append(bucket)

    # --- Print results ---
    if final_results:
        print("\n--- Buckets with Different Shard Counts and Relatively Small Objects ---")
        print(f"{'Bucket Name':<30} | {'Site1 Shards':<15} | {'Site2 Shards':<15} | {'Site1 Objects':<15} | {'Site2 Objects':<15}")
        print(f"{'-'*30}-+-{'-'*15}-+-{'-'*15}-+-{'-'*15}-+-{'-'*15}")
        for result in final_results:
            print(f"{result['bucket']:<30} | {result['site1_shards']:<15} | {result['site2_shards']:<15} | {result['site1_objects']:<15} | {result['site2_objects']:<15}")
    else:
        print("\nNo buckets found matching the criteria (different shard counts AND relatively small objects).")

if __name__ == "__main__":
    main()