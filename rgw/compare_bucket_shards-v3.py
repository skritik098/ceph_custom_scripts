## In this script we are printing it for all of the buckets in the cluster instead of few top buckets.
## Additionally, in this I added the option of sort order by number of objects on primary site.

import sys
import json
import argparse
import math

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
                        help="The percentile to use for the 'small objects' threshold (e.g., 0.25 for 25th percentile). Set to 1.0 for no effective object count filtering. Default: 0.25")
    parser.add_argument('--sort_order', choices=['asc', 'desc'], default='asc',
                        help="Sort order for results by Site 1 objects count. 'asc' for ascending, 'desc' for descending. Default: 'asc'")

    args = parser.parse_args()

    site1_data = parse_bucket_data_from_file(args.site1_file)
    site2_data = parse_bucket_data_from_file(args.site2_file)

    if not site1_data and not site2_data:
        print("Error: No bucket data loaded from either file. Please check file paths and content.", file=sys.stderr)
        return

    # --- Find buckets with different shard counts ---
    discrepant_shard_buckets = []
    all_num_objects = []

    all_bucket_names = set(site1_data.keys()).union(set(site2_data.keys()))

    for bucket_name in all_bucket_names:
        s1_info = site1_data.get(bucket_name)
        s2_info = site2_data.get(bucket_name)

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
        elif s1_info:
             all_num_objects.append(s1_info['num_objects'])
        elif s2_info:
            all_num_objects.append(s2_info['num_objects'])

    # --- Determine "small objects" threshold ---
    # Normalize percentile value
    effective_percentile = max(0.0, min(1.0, args.percentile))

    if not all_num_objects:
        print("No object data to analyze for thresholding. Setting threshold to 0.", file=sys.stderr)
        small_objects_threshold = 0
    else:
        all_num_objects.sort()
        
        if len(all_num_objects) > 0:
            index = int(len(all_num_objects) * effective_percentile)
            # Adjust index for 0-based list and ensure it's not out of bounds
            if index >= len(all_num_objects):
                index = len(all_num_objects) - 1
            if index < 0:
                index = 0
            small_objects_threshold = all_num_objects[index]
        else:
            small_objects_threshold = 0

    if effective_percentile < 1.0: # Only print threshold if filtering is actually happening
        print(f"\nCalculated 'small objects' threshold (approx. {effective_percentile*100:.0f}th percentile of all observed num_objects): {small_objects_threshold}")
    else:
        print("\nPercentile set to 100%, effectively no 'small objects' filtering applied based on object count.")


    # --- Filter for buckets with small objects among those with discrepant shards ---
    final_results = []
    for bucket in discrepant_shard_buckets:
        min_objects_for_bucket = min(bucket['site1_objects'], bucket['site2_objects'])
        
        # The condition now incorporates the effective_percentile
        # If percentile is 1.0 (100%), this condition will always be true (as min_objects_for_bucket <= max_object_count)
        if min_objects_for_bucket <= small_objects_threshold:
            final_results.append(bucket)

    # --- Sort final results by Site 1 objects count ---
    reverse_sort = True if args.sort_order == 'desc' else False
    final_results.sort(key=lambda x: x['site1_objects'], reverse=reverse_sort)

    # --- Print results with dynamic column widths ---
    if final_results:
        # Calculate maximum widths for each column
        max_bucket_len = len("Bucket Name")
        max_site1_shards_len = len("Site1 Shards")
        max_site2_shards_len = len("Site2 Shards")
        max_site1_objects_len = len("Site1 Objects")
        max_site2_objects_len = len("Site2 Objects")

        for result in final_results:
            max_bucket_len = max(max_bucket_len, len(result['bucket']))
            max_site1_shards_len = max(max_site1_shards_len, len(str(result['site1_shards'])))
            max_site2_shards_len = max(max_site2_shards_len, len(str(result['site2_shards'])))
            max_site1_objects_len = max(max_site1_objects_len, len(str(result['site1_objects'])))
            max_site2_objects_len = max(max_site2_objects_len, len(str(result['site2_objects'])))
        
        # Add a little padding to the calculated max lengths
        padding = 3
        max_bucket_len += padding
        max_site1_shards_len += padding
        max_site2_shards_len += padding
        max_site1_objects_len += padding
        max_site2_objects_len += padding

        print("\n--- Buckets with Different Shard Counts and Relatively Small Objects (Sorted by Site 1 Objects) ---")
        
        # Construct the format string dynamically
        header_format = (
            f"{{:<{max_bucket_len}}} | "
            f"{{:<{max_site1_shards_len}}} | "
            f"{{:<{max_site2_shards_len}}} | "
            f"{{:<{max_site1_objects_len}}} | "
            f"{{:<{max_site2_objects_len}}}"
        )
        
        print(header_format.format("Bucket Name", "Site1 Shards", "Site2 Shards", "Site1 Objects", "Site2 Objects"))
        
        # Print separator line
        print(f"{'-' * max_bucket_len}-+-{'-' * max_site1_shards_len}-+-{'-' * max_site2_shards_len}-+-{'-' * max_site1_objects_len}-+-{'-' * max_site2_objects_len}")
        
        # Print data rows
        for result in final_results:
            print(header_format.format(
                result['bucket'],
                result['site1_shards'],
                result['site2_shards'],
                result['site1_objects'],
                result['site2_objects']
            ))
    else:
        print("\nNo buckets found matching the criteria (different shard counts AND relatively small objects).")

if __name__ == "__main__":
    main()