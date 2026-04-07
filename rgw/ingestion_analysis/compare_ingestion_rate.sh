#!/bin/bash
#
# compare_ingestion_rate.sh - Compare RGW bucket ingestion rates
#
# Description:
#   Compares object counts between two radosgw-admin bucket stats snapshots
#   to analyze ingestion rates and identify high-growth buckets.
#
# This script consolidates the functionality of:
#   - compare_radosgw_ingestion.sh (v1)
#   - compare_radosgw_ingestion-v2.sh (top N by delta)
#   - compare_radosgw_ingestion-v3.sh (proper header handling)
#
# Version: 2.0.0
#

set -euo pipefail  # Exit on error, undefined vars, pipe failures

# Script metadata
SCRIPT_NAME=$(basename "$0")
SCRIPT_VERSION="2.0.0"

# Default configuration
DEFAULT_THRESHOLD=20000
DEFAULT_TOP_N=10
DEFAULT_SORT_BY="delta"

# Usage function
usage() {
    cat << EOF
Usage: $SCRIPT_NAME <old_json_file> <new_json_file> [options]

Compare RGW bucket ingestion rates between two snapshots.

Arguments:
  old_json_file              Path to older bucket stats JSON
  new_json_file              Path to newer bucket stats JSON

Options:
  --threshold INT            Objects/shard threshold (default: $DEFAULT_THRESHOLD)
  --top-n INT               Show top N buckets (0=all, default: $DEFAULT_TOP_N)
  --sort-by {delta,objects} Sort criteria (default: $DEFAULT_SORT_BY)
  --no-header               Omit header row
  --help, -h                Show this help message
  --version, -v             Show version information

Examples:
  # Basic comparison
  $SCRIPT_NAME old.json new.json

  # Show top 20 buckets with threshold 10000
  $SCRIPT_NAME old.json new.json --threshold 10000 --top-n 20

  # Show all buckets sorted by current object count
  $SCRIPT_NAME old.json new.json --top-n 0 --sort-by objects

  # No header (for piping to other tools)
  $SCRIPT_NAME old.json new.json --no-header

Version: $SCRIPT_VERSION
Consolidates: compare_radosgw_ingestion.sh (v1, v2, v3)

EOF
    exit 0
}

# Initialize variables
OLD_JSON_FILE=""
NEW_JSON_FILE=""
THRESHOLD=$DEFAULT_THRESHOLD
TOP_N=$DEFAULT_TOP_N
SORT_BY=$DEFAULT_SORT_BY
SHOW_HEADER=true

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --threshold)
            THRESHOLD="$2"
            shift 2
            ;;
        --top-n)
            TOP_N="$2"
            shift 2
            ;;
        --sort-by)
            SORT_BY="$2"
            if [[ "$SORT_BY" != "delta" && "$SORT_BY" != "objects" ]]; then
                echo "Error: --sort-by must be 'delta' or 'objects'" >&2
                exit 1
            fi
            shift 2
            ;;
        --no-header)
            SHOW_HEADER=false
            shift
            ;;
        --help|-h)
            usage
            ;;
        --version|-v)
            echo "$SCRIPT_NAME version $SCRIPT_VERSION"
            exit 0
            ;;
        -*)
            echo "Error: Unknown option: $1" >&2
            usage
            ;;
        *)
            if [[ -z "$OLD_JSON_FILE" ]]; then
                OLD_JSON_FILE="$1"
            elif [[ -z "$NEW_JSON_FILE" ]]; then
                NEW_JSON_FILE="$1"
            else
                echo "Error: Too many arguments" >&2
                usage
            fi
            shift
            ;;
    esac
done

# Validate required arguments
if [[ -z "$OLD_JSON_FILE" ]] || [[ -z "$NEW_JSON_FILE" ]]; then
    echo "Error: Both old and new JSON files are required" >&2
    usage
fi

# Validate files exist
if [[ ! -f "$OLD_JSON_FILE" ]]; then
    echo "Error: Old JSON file not found: $OLD_JSON_FILE" >&2
    exit 1
fi

if [[ ! -f "$NEW_JSON_FILE" ]]; then
    echo "Error: New JSON file not found: $NEW_JSON_FILE" >&2
    exit 1
fi

# Validate JSON format
if ! jq empty "$OLD_JSON_FILE" 2>/dev/null; then
    echo "Error: Invalid JSON in old file: $OLD_JSON_FILE" >&2
    exit 2
fi

if ! jq empty "$NEW_JSON_FILE" 2>/dev/null; then
    echo "Error: Invalid JSON in new file: $NEW_JSON_FILE" >&2
    exit 2
fi

# Validate numeric parameters
if ! [[ "$THRESHOLD" =~ ^[0-9]+$ ]]; then
    echo "Error: Threshold must be a positive integer" >&2
    exit 1
fi

if ! [[ "$TOP_N" =~ ^[0-9]+$ ]]; then
    echo "Error: Top-N must be a non-negative integer" >&2
    exit 1
fi

# Create temporary files
TEMP_OLD=$(mktemp)
TEMP_NEW=$(mktemp)

# Cleanup on exit
trap 'rm -f "$TEMP_OLD" "$TEMP_NEW"' EXIT

# Process old data
echo "Processing $OLD_JSON_FILE (filtering for >$THRESHOLD objects/shard)..." >&2
jq -r --argjson threshold "$THRESHOLD" \
    '.[] | select(( (.usage."rgw.main".num_objects // 0) / .num_shards | floor) > $threshold) | 
    "\(.bucket)\t\(.num_shards)\t\(.usage."rgw.main".num_objects)\t\(( (.usage."rgw.main".num_objects // 0) / .num_shards | floor))"' \
    "$OLD_JSON_FILE" > "$TEMP_OLD"

# Process new data
echo "Processing $NEW_JSON_FILE (filtering for >$THRESHOLD objects/shard)..." >&2
jq -r --argjson threshold "$THRESHOLD" \
    '.[] | select(( (.usage."rgw.main".num_objects // 0) / .num_shards | floor) > $threshold) | 
    "\(.bucket)\t\(.num_shards)\t\(.usage."rgw.main".num_objects)\t\(( (.usage."rgw.main".num_objects // 0) / .num_shards | floor))"' \
    "$NEW_JSON_FILE" > "$TEMP_NEW"

echo "Calculating delta and sorting..." >&2

# Generate output
{
    # Print header if requested
    if [[ "$SHOW_HEADER" == "true" ]]; then
        printf "%s\t%s\t%s\t%s\t%s\t%s\t%s\n" \
            "Bucket" "Shards" "Objects_Old" "Obj/Shard_Old" \
            "Objects_New" "Obj/Shard_New" "Delta"
    fi
    
    # Process data with AWK
    awk -F'\t' '
    FNR == NR {
        objects_old[$1] = $3
        ops_old[$1] = $4
        next
    }
    {
        bucket = $1
        shards = $2
        objects_new = $3
        ops_new = $4
        objects_old_val = (bucket in objects_old) ? objects_old[bucket] : 0
        ops_old_val = (bucket in ops_old) ? ops_old[bucket] : 0
        delta = objects_new - objects_old_val
        printf "%s\t%s\t%s\t%s\t%s\t%s\t%s\n", \
            bucket, shards, objects_old_val, ops_old_val, \
            objects_new, ops_new, delta
    }' "$TEMP_OLD" "$TEMP_NEW"
} | {
    # Apply sorting and limiting
    if [[ "$TOP_N" -gt 0 ]]; then
        if [[ "$SORT_BY" == "delta" ]]; then
            # Sort by delta (column 7), numeric, reverse
            if [[ "$SHOW_HEADER" == "true" ]]; then
                # Keep header, sort rest
                (read -r header; echo "$header"; sort -t$'\t' -k7 -nr) | head -n $((TOP_N + 1))
            else
                sort -t$'\t' -k7 -nr | head -n "$TOP_N"
            fi
        else
            # Sort by current objects (column 5), numeric, reverse
            if [[ "$SHOW_HEADER" == "true" ]]; then
                (read -r header; echo "$header"; sort -t$'\t' -k5 -nr) | head -n $((TOP_N + 1))
            else
                sort -t$'\t' -k5 -nr | head -n "$TOP_N"
            fi
        fi
    else
        # No limiting, just pass through
        cat
    fi
} | column -t

echo "Comparison complete." >&2
if [[ "$TOP_N" -gt 0 ]]; then
    echo "Displaying top $TOP_N buckets by $SORT_BY." >&2
fi

# Made with Bob
