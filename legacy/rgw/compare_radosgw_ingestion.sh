#!/bin/bash

# --- Configuration ---
# Default threshold for objects per shard filter
DEFAULT_THRESHOLD=20000
# Default number of lines to 'head' after sorting (adjust if you want more/less)
DEFAULT_HEAD_LINES=10

# --- Usage Function ---
usage() {
    echo "Usage: $0 <old_radosgw_json_file> <new_radosgw_json_file> [objects_per_shard_threshold] [num_head_lines]"
    echo ""
    echo "Compares object counts for buckets between two radosgw-admin bucket stats JSON files."
    echo "Filters buckets by 'objects/shard > threshold' and then 'sort -k2 | head' before comparison."
    echo ""
    echo "Arguments:"
    echo "  <old_radosgw_json_file>        Path to the older radosgw bucket stats JSON output file."
    echo "  <new_radosgw_json_file>        Path to the newer radosgw bucket stats JSON output file."
    echo "  [objects_per_shard_threshold]  Optional: Minimum objects per shard to include buckets (default: $DEFAULT_THRESHOLD)."
    echo "  [num_head_lines]               Optional: Number of top buckets to compare after sorting (default: $DEFAULT_HEAD_LINES)."
    exit 1
}

# --- Argument Parsing ---
if [[ "$#" -lt 2 ]]; then
    usage
fi

OLD_JSON_FILE="$1"
NEW_JSON_FILE="$2"
THRESHOLD=${3:-$DEFAULT_THRESHOLD} # Use provided threshold or default
NUM_HEAD=${4:-$DEFAULT_HEAD_LINES} # Use provided head lines or default

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
# These temporary files will hold tab-separated data, filtered and sorted.
# Using `mktemp` ensures unique and safe temporary file creation.
TEMP_OLD_DATA=$(mktemp)
TEMP_NEW_DATA=$(mktemp)

echo "Processing $OLD_JSON_FILE (filtering for >$THRESHOLD objects/shard, sorting, heading $NUM_HEAD lines)..." >&2
cat "$OLD_JSON_FILE" | \
jq -r --argjson threshold "$THRESHOLD" '.[] | select(( (.usage."rgw.main".num_objects // 0) / .num_shards | floor) > $threshold) | "\(.bucket)\t\(.num_shards)\t\(.usage."rgw.main".num_objects)\t\(( (.usage."rgw.main".num_objects // 0) / .num_shards | floor))"' | \
sort -k2 | head -n "$NUM_HEAD" > "$TEMP_OLD_DATA"

echo "Processing $NEW_JSON_FILE (filtering for >$THRESHOLD objects/shard, sorting, heading $NUM_HEAD lines)..." >&2
cat "$NEW_JSON_FILE" | \
jq -r --argjson threshold "$THRESHOLD" '.[] | select(( (.usage."rgw.main".num_objects // 0) / .num_shards | floor) > $threshold) | "\(.bucket)\t\(.num_shards)\t\(.usage."rgw.main".num_objects)\t\(( (.usage."rgw.main".num_objects // 0) / .num_shards | floor))"' | \
sort -k2 | head -n "$NUM_HEAD" > "$TEMP_NEW_DATA"

echo "Comparing object counts and calculating delta..." >&2

# --- AWK Script for Comparison ---
# The AWK script reads the two pre-processed temporary files,
# calculates the delta, and prints the formatted output with headers.
awk '
BEGIN {
    FS = "\t" # Input fields are tab-separated (from jq output)
    # Print the header row
    printf "%s\t%s\t%s\t%s\t%s\t%s\t%s\n", \
           "Bucket", "Shards", "Objects_Old", "Objects/Shard_Old", "Objects_Current", "Objects/Shard_Current", "Delta_Objects"
}

# Phase 1: Read the data from the OLD file (first input to awk)
# FNR == NR is true only for the first file being processed.
FNR == NR {
    # Store relevant data from the old file in associative arrays
    # $1 = bucket name, $3 = num_objects, $4 = objects/shard
    objects_old[$1] = $3
    shards_old[$1] = $2
    ops_old[$1] = $4 # objects per shard old
    next # Move to the next line in the old file
}

# Phase 2: Process the data from the NEW file (second input to awk)
# This block runs for every line in the new file after the old file is fully read.
{
    bucket_name = $1
    num_shards_current = $2
    num_objects_current = $3
    ops_current = $4 # objects per shard current

    # Get the corresponding objects_old count.
    # If the bucket doesn''t exist in the old data (e.g., new bucket, or filtered out),
    # treat its old object count as 0.
    num_objects_old = (bucket_name in objects_old) ? objects_old[bucket_name] : 0
    shards_old_val = (bucket_name in shards_old) ? shards_old[bucket_name] : 0 # Not directly used in print but good to have
    ops_old_val = (bucket_name in ops_old) ? ops_old[bucket_name] : 0

    # Calculate the delta (Current Objects - Old Objects)
    delta_objects = num_objects_current - num_objects_old

    # Print the combined data with delta, using tabs for alignment
    printf "%s\t%s\t%s\t%s\t%s\t%s\t%s\n", \
           bucket_name, \
           num_shards_current, \
           num_objects_old, \
           ops_old_val, \
           num_objects_current, \
           ops_current, \
           delta_objects
}' "$TEMP_OLD_DATA" "$TEMP_NEW_DATA" | column -t

# --- Clean up Temporary Files ---
rm "$TEMP_OLD_DATA" "$TEMP_NEW_DATA"
echo "Comparison complete." >&2
