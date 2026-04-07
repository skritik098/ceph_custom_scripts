## In this we reading a hard coded output from two files primary-data.txt & secondary.txt which is created using the following command
## less radosgw-admin bucket stats | jq -r '.[] | select(( (.usage."rgw.main".num_objects // 0) / .num_shards | floor) > 200000) | "\(.bucket)\t\(.num_shards)\t\(.usage."rgw.main".num_objects)\t\(( (.usage."rgw.main".num_objects // 0) / .num_shards | floor))"' | \
## column -t | \
## head
## However, this has change for the information print / extraction phase that include 6 columns while the script.sh has 5 columns

awk '
BEGIN {
    FS = " " # Set field separator to space for parsing input files
    # Print the header row. Use tabs to ensure consistent spacing for column -t.
    print "Bucket\tShards\tObjects_B\tObjects/Shard\tObjects_A\tDelta_Objects"
}

# --- Phase 1: Read fileA.txt (the first file specified on the command line) ---
FNR == NR {
    # Store the num_objects from fileA, indexed by the bucket name ($1).
    # $1 is bucket, $3 is num_objects.
    fileA_objects[$1] = $3
    next # Skip to the next line in fileA.txt
}

# --- Phase 2: Process fileB.txt (the second file specified on the command line) ---
{
    bucket_name = $1       # Get the bucket name from the current line in fileB
    num_shards_B = $2      # Get num_shards from fileB
    num_objects_B = $3     # Get num_objects from fileB
    objects_per_shard_B = $4 # Get objects/shard from fileB

    # Get the num_objects for this bucket from fileA.
    # If the bucket_name was not found in fileA_objects array, it means the bucket
    # didn''t exist in fileA''s output, so we default its num_objects_A to 0.
    num_objects_A = (bucket_name in fileA_objects) ? fileA_objects[bucket_name] : 0

    # Calculate the delta: (num_objects from FileB - num_objects from FileA)
    delta = num_objects_B - num_objects_A

    # Print the fields. We''re explicitly listing them now to insert Objects_A.
    # Use tabs for separation so column -t can align them perfectly.
    printf "%s\t%s\t%s\t%s\t%s\t%s\n", \
           bucket_name, \
           num_shards_B, \
           num_objects_B, \
           objects_per_shard_B, \
           num_objects_A, \
           delta
}' primary-data-o.txt secondary-data-o.txt | column -t