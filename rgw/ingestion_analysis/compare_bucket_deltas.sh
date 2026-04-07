#!/bin/bash
#
# compare_bucket_deltas.sh - Compare bucket object deltas between two data files
#
# Description:
#   Compares bucket object counts between two pre-processed data files
#   and calculates deltas. Supports multiple column formats for backward compatibility.
#
# This script consolidates the functionality of:
#   - script.sh (5 columns)
#   - script-v2.sh (6 columns with header)
#   - script-v3.sh (7 columns with header)
#
# Version: 2.0.0
#

set -euo pipefail

# Script metadata
SCRIPT_NAME=$(basename "$0")
SCRIPT_VERSION="2.0.0"

# Default configuration
DEFAULT_COLUMN_FORMAT=7
SHOW_HEADER=true

# Usage function
usage() {
    cat << EOF
Usage: $SCRIPT_NAME <primary_data_file> <secondary_data_file> [options]

Compare bucket object counts between two pre-processed data files.

Arguments:
  primary_data_file          Path to primary/old data file
  secondary_data_file        Path to secondary/new data file

Options:
  --columns {5,6,7}         Output column format (default: $DEFAULT_COLUMN_FORMAT)
                            5: Basic format (v1 compatibility)
                            6: With primary objects column (v2 compatibility)
                            7: Full format with all details (v3 compatibility)
  --no-header               Omit header row
  --format {table,tsv}      Output format (default: table)
  --help, -h                Show this help message
  --version, -v             Show version information

Column Formats:
  5 columns: Bucket, Shards, Objects_B, Objects/Shard, Delta
  6 columns: Bucket, Shards, Objects_B, Objects/Shard, Objects_A, Delta
  7 columns: Bucket, Shards_Primary, Objects_Primary, Obj/Shard_Primary, 
             Objects_Secondary, Shards_Secondary, Delta

Examples:
  # Basic comparison (7 columns with header)
  $SCRIPT_NAME primary.txt secondary.txt

  # 5-column format (v1 compatibility)
  $SCRIPT_NAME primary.txt secondary.txt --columns 5

  # 6-column format without header (v2 compatibility)
  $SCRIPT_NAME primary.txt secondary.txt --columns 6 --no-header

  # TSV output for piping
  $SCRIPT_NAME primary.txt secondary.txt --format tsv

Version: $SCRIPT_VERSION
Consolidates: script.sh, script-v2.sh, script-v3.sh

EOF
    exit 0
}

# Initialize variables
PRIMARY_FILE=""
SECONDARY_FILE=""
COLUMN_FORMAT=$DEFAULT_COLUMN_FORMAT
OUTPUT_FORMAT="table"

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --columns)
            COLUMN_FORMAT="$2"
            if [[ ! "$COLUMN_FORMAT" =~ ^[567]$ ]]; then
                echo "Error: --columns must be 5, 6, or 7" >&2
                exit 1
            fi
            shift 2
            ;;
        --no-header)
            SHOW_HEADER=false
            shift
            ;;
        --format)
            OUTPUT_FORMAT="$2"
            if [[ "$OUTPUT_FORMAT" != "table" && "$OUTPUT_FORMAT" != "tsv" ]]; then
                echo "Error: --format must be 'table' or 'tsv'" >&2
                exit 1
            fi
            shift 2
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
            if [[ -z "$PRIMARY_FILE" ]]; then
                PRIMARY_FILE="$1"
            elif [[ -z "$SECONDARY_FILE" ]]; then
                SECONDARY_FILE="$1"
            else
                echo "Error: Too many arguments" >&2
                usage
            fi
            shift
            ;;
    esac
done

# Validate required arguments
if [[ -z "$PRIMARY_FILE" ]] || [[ -z "$SECONDARY_FILE" ]]; then
    echo "Error: Both primary and secondary data files are required" >&2
    usage
fi

# Validate files exist
if [[ ! -f "$PRIMARY_FILE" ]]; then
    echo "Error: Primary file not found: $PRIMARY_FILE" >&2
    exit 1
fi

if [[ ! -f "$SECONDARY_FILE" ]]; then
    echo "Error: Secondary file not found: $SECONDARY_FILE" >&2
    exit 1
fi

# Process data with AWK
awk -v cols="$COLUMN_FORMAT" -v header="$SHOW_HEADER" '
BEGIN {
    FS = " "  # Field separator is space
    
    # Print header if requested
    if (header == "true") {
        if (cols == 5) {
            print "Bucket\tShards\tObjects_B\tObjects/Shard\tDelta"
        } else if (cols == 6) {
            print "Bucket\tShards\tObjects_B\tObjects/Shard\tObjects_A\tDelta"
        } else {
            print "Bucket\tShards_Primary\tObjects_Primary\tObj/Shard_Primary\tObjects_Secondary\tShards_Secondary\tDelta"
        }
    }
}

# Phase 1: Read primary file (fileA)
FNR == NR {
    # Store data from primary file
    fileA_objects[$1] = $3
    fileA_shards[$1] = $2
    fileA_ops[$1] = $4  # objects per shard
    next
}

# Phase 2: Process secondary file (fileB)
{
    bucket_name = $1
    num_shards_B = $2
    num_objects_B = $3
    objects_per_shard_B = $4
    
    # Get corresponding data from primary file
    num_objects_A = (bucket_name in fileA_objects) ? fileA_objects[bucket_name] : 0
    num_shards_A = (bucket_name in fileA_shards) ? fileA_shards[bucket_name] : 0
    objects_per_shard_A = (bucket_name in fileA_ops) ? fileA_ops[bucket_name] : 0
    
    # Calculate delta
    delta = num_objects_B - num_objects_A
    
    # Output based on column format
    if (cols == 5) {
        # 5-column format: Bucket, Shards, Objects_B, Objects/Shard, Delta
        printf "%s\t%s\t%s\t%s\t%s\n", \
               bucket_name, num_shards_B, num_objects_B, objects_per_shard_B, delta
    } else if (cols == 6) {
        # 6-column format: Bucket, Shards, Objects_B, Objects/Shard, Objects_A, Delta
        printf "%s\t%s\t%s\t%s\t%s\t%s\n", \
               bucket_name, num_shards_B, num_objects_B, objects_per_shard_B, \
               num_objects_A, delta
    } else {
        # 7-column format: Full details
        printf "%s\t%s\t%s\t%s\t%s\t%s\t%s\n", \
               bucket_name, num_shards_A, num_objects_A, objects_per_shard_A, \
               num_objects_B, num_shards_B, delta
    }
}
' "$PRIMARY_FILE" "$SECONDARY_FILE" | {
    if [[ "$OUTPUT_FORMAT" == "table" ]]; then
        column -t
    else
        cat  # TSV output, no formatting
    fi
}

# Made with Bob
