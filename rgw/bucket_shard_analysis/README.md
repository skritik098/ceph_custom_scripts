# Bucket Shard Analysis

Compare bucket shard configurations between two Ceph RGW sites.

## Overview

This module helps identify buckets with different shard counts across sites, which can indicate configuration drift or replication issues. It filters results by object count percentiles to focus on buckets that matter most.

## Script

**`compare_bucket_shards.py`** - Consolidated bucket shard comparison tool

Consolidates functionality from:
- `compare_bucket_shards.py` (v1)
- `compare_bucket_shards-v2.py` (dynamic column widths)
- `compare_bucket_shards-v3.py` (sorting options)

## Usage

```bash
compare_bucket_shards.py <site1_file> <site2_file> [options]
```

### Arguments

- `site1_file` - Path to Site 1 bucket stats JSON file
- `site2_file` - Path to Site 2 bucket stats JSON file

### Options

- `--percentile FLOAT` - Percentile threshold for small objects (0.0-1.0, default: 0.25)
- `--sort-order {asc,desc}` - Sort order by Site 1 object count (default: asc)
- `--output-format {table,json,csv}` - Output format (default: table)
- `--verbose, -v` - Enable verbose output
- `--version` - Show version information
- `--help, -h` - Show help message

## Examples

### Basic Comparison

```bash
# Compare with default settings (25th percentile, ascending sort)
./compare_bucket_shards.py site1_stats.json site2_stats.json
```

### Show All Buckets

```bash
# No filtering by object count
./compare_bucket_shards.py site1_stats.json site2_stats.json --percentile 1.0
```

### Sort by Descending Object Count

```bash
# Show buckets with most objects first
./compare_bucket_shards.py site1_stats.json site2_stats.json --sort-order desc
```

### JSON Output

```bash
# Output as JSON for programmatic processing
./compare_bucket_shards.py site1_stats.json site2_stats.json --output-format json > results.json
```

### CSV Export

```bash
# Export to CSV for spreadsheet analysis
./compare_bucket_shards.py site1_stats.json site2_stats.json --output-format csv > results.csv
```

### Verbose Mode

```bash
# Show detailed processing information
./compare_bucket_shards.py site1_stats.json site2_stats.json --verbose
```

## Input Format

The script expects JSON output from `radosgw-admin bucket stats`:

```bash
radosgw-admin bucket stats > site1_stats.json
```

Expected JSON structure:
```json
[
  {
    "bucket": "bucket-name",
    "num_shards": 11,
    "usage": {
      "rgw.main": {
        "num_objects": 1000000
      }
    }
  }
]
```

## Output Format

### Table Output (Default)

```
Calculated 'small objects' threshold (approx. 25th percentile): 50000

--- Buckets with Different Shard Counts and Relatively Small Objects ---
bucket                          | site1_shards    | site2_shards    | site1_objects   | site2_objects   
--------------------------------+-----------------+-----------------+-----------------+-----------------
my-bucket-1                     | 11              | 1               | 45000           | 45000           
my-bucket-2                     | 1               | 11              | 30000           | 30000           
```

### JSON Output

```json
[
  {
    "bucket": "my-bucket-1",
    "site1_shards": 11,
    "site2_shards": 1,
    "site1_objects": 45000,
    "site2_objects": 45000
  }
]
```

### CSV Output

```csv
bucket,site1_shards,site2_shards,site1_objects,site2_objects
my-bucket-1,11,1,45000,45000
my-bucket-2,1,11,30000,30000
```

## Use Cases

### 1. Identify Shard Misconfigurations

Find buckets where shard counts differ between sites:

```bash
./compare_bucket_shards.py primary.json secondary.json --percentile 0.5
```

### 2. Focus on High-Impact Buckets

Show only buckets in the top 10% by object count:

```bash
./compare_bucket_shards.py site1.json site2.json --percentile 0.9 --sort-order desc
```

### 3. Generate Reports

Create CSV reports for management:

```bash
./compare_bucket_shards.py site1.json site2.json --output-format csv > weekly_report.csv
```

### 4. Automated Monitoring

Use in monitoring scripts:

```bash
#!/bin/bash
RESULT=$(./compare_bucket_shards.py site1.json site2.json --output-format json)
COUNT=$(echo "$RESULT" | jq 'length')
if [ "$COUNT" -gt 0 ]; then
    echo "WARNING: $COUNT buckets have shard mismatches"
    echo "$RESULT" | jq .
fi
```

## Troubleshooting

### Empty Output

If you see "No buckets found matching the criteria":
- Check that both JSON files contain valid data
- Try increasing the percentile (e.g., `--percentile 0.5` or `--percentile 1.0`)
- Use `--verbose` to see processing details

### JSON Decode Errors

If you get JSON decode errors:
- Verify the input files are valid JSON: `jq . site1.json`
- Ensure files are complete (not truncated)
- Check file permissions

### Performance Issues

For very large datasets:
- Use `--output-format json` to avoid table formatting overhead
- Consider filtering data before comparison using `jq`

## Version History

- **2.0.0** - Consolidated version with all features
  - Dynamic column widths
  - Flexible sorting options
  - Multiple output formats
  - Improved error handling

## See Also

- [Main README](../../README.md)
- [Bucket Stats Comparison](../bucket_stats_comparison/README.md)
- [Configuration Guide](../config/defaults.yaml)