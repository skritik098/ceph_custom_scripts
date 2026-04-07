
## In this we reading a hard coded output from two files primary-data.txt & secondary.txt which is created using the following command
## less radosgw-admin bucket stats | jq -r '.[] | select(( (.usage."rgw.main".num_objects // 0) / .num_shards | floor) > 200000) | "\(.bucket)\t\(.num_shards)\t\(.usage."rgw.main".num_objects)\t\(( (.usage."rgw.main".num_objects // 0) / .num_shards | floor))"' | \
## column -t | \
## head

awk '
BEGIN {
    # Set the field separator to a space. Awk treats multiple spaces as a single separator
    # when FS is a single space, which is perfect for column -t output.
    FS = " "
}

# --- Phase 1: Read fileA.txt (the first file specified on the command line) ---
# FNR == NR is true only when awk is processing the first file.
FNR == NR {
    # Store the num_objects from fileA, indexed by the bucket name ($1).
    # $1 is bucket name, $3 is num_objects.
    fileA_objects[$1] = $3
    next # Skip to the next line in fileA.txt
}

# --- Phase 2: Process fileB.txt (the second file specified on the command line) ---
# This block executes for every line in fileB.txt after fileA.txt has been fully read.
{
    bucket_name = $1       # Get the bucket name from the current line in fileB
    num_objects_B = $3     # Get num_objects from the current line in fileB

    # Get the num_objects for this bucket from fileA.
    # If the bucket_name was not found in fileA_objects array, it means the bucket
    # didn''t exist in fileA''s output, so we default its num_objects_A to 0.
    num_objects_A = (bucket_name in fileA_objects) ? fileA_objects[bucket_name] : 0

    # Calculate the delta: (num_objects from FileB - num_objects from FileA)
    # This will be negative if FileA had more objects.
    delta = num_objects_B - num_objects_A

    # Print the entire current line from fileB ($0), followed by the calculated delta.
    print $0, delta
}' primary-data.txt secondary.txt | column -t