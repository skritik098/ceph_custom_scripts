#!/bin/bash

## In this script, the difference is for that it will print Output that will show the top $NUM_TOP_DELTA_BUCKETS buckets with the highest delta increase."

# --- Configuration ---
# Default threshold for objects per shard filter
DEFAULT_THRESHOLD=20000 # Your example had 20000, not 200000, double check this if needed
# Number of top lines to display based on delta
NUM_TOP_DELTA_BUCKETS=10

# --- Usage Function ---
usage() {
    echo "Usage: $0 <old_radosgw_json_file> <new_radosgw_json_file> [objects_per_shard_threshold]"
    echo ""
    echo "Compares object counts for buckets between two radosgw-admin bucket stats JSON files."
    echo "Filters buckets by 'objects/shard > threshold', calculates delta, then prints top N by delta (desc)."
    echo ""
    echo "Arguments:"
    echo "  <old_radosgw_json_file>        Path to the older radosgw bucket stats JSON output file."
    echo "  <new_radosgw_json_file>        Path to the newer radosgw bucket stats JSON output file."
    echo "  [objects_per_shard_threshold]  Optional: Minimum objects per shard to include buckets (default: $DEFAULT_THRESHOLD)."
    echo ""
    echo "Output will show the top $NUM_TOP_DELTA_BUCKETS buckets with the highest delta increase."
    exit 1
}

# --- Argument Parsing ---
if [[ "$#" -lt 2 ]]; then
    usage
fi

OLD_JSON_FILE="$1"
NEW_JSON_FILE="$2"
THRESHOLD=${3:-$DEFAULT_THRESHOLD} # Use provided threshold or default

# Check if input files exist
if [[ ! -f "$OLD_JSON_FILE" ]]; then
    echo "Error: Old JSON file not found: $OLD_JSON_FILE" >&2
    exit 1
fi
if [[ ! -f "$NEW_JSON_FILE" ]]; then
    echo "Error: New JSON file not found: $NEW_JSON_FILE" >&2
    exit 1
fi

# --- Create Temporary Files for Processed Data ---
# These temporary files will hold tab-separated data that has been filtered by objects/shard,
# but NOT yet sorted or headed, so all qualifying buckets are included for delta calculation.
TEMP_OLD_DATA=$(mktemp)
TEMP_NEW_DATA=$(mktemp)

echo "Processing $OLD_JSON_FILE (filtering for >$THRESHOLD objects/shard)..." >&2
cat "$OLD_JSON_FILE" | \
jq -r --argjson threshold "$THRESHOLD" '.[] | select(( (.usage."rgw.main".num_objects // 0) / .num_shards | floor) > $threshold) | "\(.bucket)\t\(.num_shards)\t\(.usage."rgw.main".num_objects)\t\(( (.usage."rgw.main".num_objects // 0) / .num_shards | floor))"' \
> "$TEMP_OLD_DATA"

echo "Processing $NEW_JSON_FILE (filtering for >$THRESHOLD objects/shard)..." >&2
cat "$NEW_JSON_FILE" | \
jq -r --argjson threshold "$THRESHOLD" '.[] | select(( (.usage."rgw.main".num_objects // 0) / .num_shards | floor) > $threshold) | "\(.bucket)\t\(.num_shards)\t\(.usage."rgw.main".num_objects)\t\(( (.usage."rgw.main".num_objects // 0) / .num_shards | floor))"' \
> "$TEMP_NEW_DATA"

echo "Calculating delta and sorting by highest delta..." >&2

# --- AWK Script for Comparison, then Sort and Head ---
# The AWK script calculates the delta for all filtered buckets.
# The output is then piped to `sort -k7 -nr` to sort by the delta column (7th, numeric, reverse)
# and then `head -n NUM_TOP_DELTA_BUCKETS` to get the top results.
# Finally, `column -t` for alignment.
awk '
BEGIN {
    FS = "\t" # Input fields are tab-separated (from jq output)
    # Print the header row
    printf "%s\t%s\t%s\t%s\t%s\t%s\t%s\n", \
           "Bucket", "Shards", "Objects_Old", "Objects/Shard_Old", "Objects_Current", "Objects/Shard_Current", "Delta_Objects"
}

# Phase 1: Read the data from the OLD file (first input to awk)
FNR == NR {
    # Store relevant data from the old file in associative arrays
    objects_old[$1] = $3         # $1 = bucket name, $3 = num_objects
    ops_old[$1] = $4             # $4 = objects per shard old
    next
}

# Phase 2: Process the data from the NEW file (second input to awk)
{
    bucket_name = $1
    num_shards_current = $2
    num_objects_current = $3
    ops_current = $4 # objects per shard current

    # Get the corresponding objects_old count.
    # If the bucket doesn''t exist in the old data (e.g., new bucket, or didn''t meet old filter),
    # treat its old object count as 0.
    num_objects_old = (bucket_name in objects_old) ? objects_old[bucket_name] : 0
    ops_old_val = (bucket_name in ops_old) ? ops_old[bucket_name] : 0

    # Calculate the delta (Current Objects - Old Objects)
    delta_objects = num_objects_current - num_objects_old

    # Print the combined data with delta, using tabs for consistency before final sort/column
    printf "%s\t%s\t%s\t%s\t%s\t%s\t%s\n", \
           bucket_name, \
           num_shards_current, \
           num_objects_old, \
           ops_old_val, \
           num_objects_current, \
           ops_current, \
           delta_objects
}' "$TEMP_OLD_DATA" "$TEMP_NEW_DATA" | \
sort -k7 -nr | \
head -n "$NUM_TOP_DELTA_BUCKETS" | \
column -t

# --- Clean up Temporary Files ---
rm "$TEMP_OLD_DATA" "$TEMP_NEW_DATA"
echo "Comparison complete. Displaying top $NUM_TOP_DELTA_BUCKETS buckets by delta." >&2