#!/bin/bash
#
# parse_sync_errors.sh - Parse and analyze RGW sync errors
#
# Description:
#   Parses the output of 'radosgw-admin sync error list' and groups
#   errors by message, filtering by bucket name and providing counts.
#
# Version: 2.0.0
#

set -euo pipefail

# Script metadata
SCRIPT_NAME=$(basename "$0")
SCRIPT_VERSION="2.0.0"

# Usage function
usage() {
    cat << EOF
Usage: $SCRIPT_NAME <input_json_file> <bucket_name> [options]

Parse and analyze RGW sync errors from radosgw-admin output.

Arguments:
  input_json_file           Path to sync error list JSON file
  bucket_name              Bucket name to filter errors for

Options:
  --pretty                 Pretty-print JSON output
  --help, -h              Show this help message
  --version, -v           Show version information

Examples:
  # Basic usage
  $SCRIPT_NAME sync_errors.json my-bucket

  # Pretty-printed output
  $SCRIPT_NAME sync_errors.json my-bucket --pretty

  # Generate sync error list and parse
  radosgw-admin sync error list > sync_errors.json
  $SCRIPT_NAME sync_errors.json my-bucket

Input Format:
  The input file should be the JSON output from:
  radosgw-admin sync error list

Output Format:
  JSON object with error messages as keys and details as values:
  {
    "error_message": {
      "count": <number of occurrences>,
      "entries": [
        {
          "name": "<entry name>",
          "section": "<section>",
          "timestamp": "<timestamp>"
        }
      ]
    }
  }

Version: $SCRIPT_VERSION

EOF
    exit 0
}

# Initialize variables
INPUT_FILE=""
BUCKET_NAME=""
PRETTY_PRINT=false

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --pretty)
            PRETTY_PRINT=true
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
            if [[ -z "$INPUT_FILE" ]]; then
                INPUT_FILE="$1"
            elif [[ -z "$BUCKET_NAME" ]]; then
                BUCKET_NAME="$1"
            else
                echo "Error: Too many arguments" >&2
                usage
            fi
            shift
            ;;
    esac
done

# Validate required arguments
if [[ -z "$INPUT_FILE" ]] || [[ -z "$BUCKET_NAME" ]]; then
    echo "Error: Both input file and bucket name are required" >&2
    usage
fi

# Validate file exists
if [[ ! -f "$INPUT_FILE" ]]; then
    echo "Error: File '$INPUT_FILE' not found." >&2
    exit 1
fi

# Validate JSON format
if ! jq empty "$INPUT_FILE" 2>/dev/null; then
    echo "Error: Invalid JSON in file '$INPUT_FILE'" >&2
    exit 2
fi

# Build jq command based on pretty print option
if [[ "$PRETTY_PRINT" == "true" ]]; then
    JQ_OPTS=""
else
    JQ_OPTS="-c"
fi

# Process the JSON file
cat "$INPUT_FILE" | jq $JQ_OPTS --arg BUCKET "$BUCKET_NAME" '
  # Extract all entries from all items
  [.[].entries[]] | 
  
  # Group by error message
  group_by(.info.message) | 
  
  # Transform into desired format
  map({ 
    key: .[0].info.message, 
    value: {
      count: length,
      entries: [
        .[] | 
        # Filter entries that contain the bucket name
        select(.name | type == "string" and contains($BUCKET)) |
        { 
          name, 
          section, 
          timestamp 
        }
      ]
    }
  }) | 
  
  # Convert array to object with messages as keys
  from_entries |
  
  # Remove entries with empty arrays (no matches for bucket)
  with_entries(select(.value.entries | length > 0))
'

# Check if jq command succeeded
if [[ $? -ne 0 ]]; then
    echo "Error: Failed to process JSON data" >&2
    exit 3
fi

# Made with Bob
