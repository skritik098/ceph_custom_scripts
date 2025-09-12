## In this script, we will parse the sync error log and extract the relevant information by grouping
## the errors and counting the name, section of error in each group.

# In this we assume that we have the output of the following command:
# radosgw-admin sync erorr list

#!/bin/bash

# Check if both file and bucket name arguments are provided
if [ -z "$1" ] || [ -z "$2" ]; then
  echo "Usage: $0 <input_json_file> <bucket_name>"
  exit 1
fi

# Check if the file exists
if [ ! -f "$1" ]; then
  echo "Error: File '$1' not found."
  exit 1
fi

INPUT_FILE="$1"
BUCKET_NAME="$2"

# Pipe the file's content to the jq command, passing the bucket name as a variable
cat "$INPUT_FILE" | jq --arg BUCKET "$BUCKET_NAME" '
  [.[].entries[]] | 
  group_by(.info.message) | 
  map({ 
    key: .[0].info.message, 
    value: {
      count: length,
      entries: [
        .[] | 
        select(.name | type == "string" and contains($BUCKET)) |
        { 
          name, 
          section, 
          timestamp 
        }
      ]
    }
  }) | 
  from_entries
'