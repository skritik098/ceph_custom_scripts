# Migration Guide - Legacy to v2.0.0

This guide helps you migrate from the legacy Ceph RGW scripts to the new consolidated v2.0.0 toolkit.

## Overview

The refactoring consolidates **12 legacy scripts into 5 well-organized scripts** with improved functionality, better error handling, and comprehensive documentation.

## Key Changes

### What's New

✅ **Consolidated Scripts** - Multiple versions merged into single scripts with CLI options  
✅ **Shared Utilities** - Reusable Python modules for common operations  
✅ **Better Organization** - Scripts organized by functionality  
✅ **Comprehensive Documentation** - Detailed README files and examples  
✅ **Configuration File** - Centralized default settings  
✅ **Multiple Output Formats** - Table, JSON, and CSV support  
✅ **Improved Error Handling** - Clear error messages and validation  

### What's Preserved

✅ **All Functionality** - Every feature from legacy scripts is available  
✅ **Backward Compatibility** - Legacy scripts preserved in `legacy/` directory  
✅ **Same Input Format** - Works with existing `radosgw-admin` output  
✅ **Same Core Logic** - Calculations and algorithms unchanged  

## Script Migration Map

### Python Scripts

#### 1. Bucket Shard Comparison Scripts

| Legacy Script | New Script | Migration Command |
|---------------|------------|-------------------|
| `compare_bucket_shards.py` | `bucket_shard_analysis/compare_bucket_shards.py` | Use `--sort-order asc` (default) |
| `compare_bucket_shards-v2.py` | Same | Default behavior (no changes needed) |
| `compare_bucket_shards-v3.py` | Same | Use `--sort-order desc` |

**Migration Examples:**

```bash
# Old v1
python compare_bucket_shards.py site1.json site2.json

# New (equivalent)
python rgw/bucket_shard_analysis/compare_bucket_shards.py site1.json site2.json --sort-order asc

# Old v2 (default)
python compare_bucket_shards-v2.py site1.json site2.json

# New (equivalent)
python rgw/bucket_shard_analysis/compare_bucket_shards.py site1.json site2.json

# Old v3
python compare_bucket_shards-v3.py site1.json site2.json

# New (equivalent)
python rgw/bucket_shard_analysis/compare_bucket_shards.py site1.json site2.json --sort-order desc
```

#### 2. Bucket Stats Comparison Scripts

| Legacy Script | New Script | Migration Command |
|---------------|------------|-------------------|
| `compare_bucket_stats_intecompare_bucket_stats_internal_json.py` | `bucket_stats_comparison/compare_bucket_stats.py` | Use `--min-objects-per-shard 2000` (default) |
| `compare_bucket_stats_intecompare_bucket_stats_internal_json-v2.py` | Same | Use `--min-objects-per-shard 0` |

**Migration Examples:**

```bash
# Old v1 (with filtering)
python compare_bucket_stats_internal_json.py old.json new.json

# New (equivalent)
python rgw/bucket_stats_comparison/compare_bucket_stats.py old.json new.json --min-objects-per-shard 2000

# Old v2 (no filtering)
python compare_bucket_stats_internal_json-v2.py old.json new.json

# New (equivalent)
python rgw/bucket_stats_comparison/compare_bucket_stats.py old.json new.json --min-objects-per-shard 0
```

### Shell Scripts

#### 3. Ingestion Rate Comparison Scripts

| Legacy Script | New Script | Migration Command |
|---------------|------------|-------------------|
| `compare_radosgw_ingestion.sh` | `ingestion_analysis/compare_ingestion_rate.sh` | Use `--top-n 0` for v1 behavior |
| `compare_radosgw_ingestion-v2.sh` | Same | Default behavior (top 10) |
| `compare_radosgw_ingestion-v3.sh` | Same | Default behavior (with header) |

**Migration Examples:**

```bash
# Old v1 (show all, with head parameter)
bash compare_radosgw_ingestion.sh old.json new.json 20000 10

# New (equivalent)
bash rgw/ingestion_analysis/compare_ingestion_rate.sh old.json new.json --threshold 20000 --top-n 10

# Old v2 (top 10 by delta)
bash compare_radosgw_ingestion-v2.sh old.json new.json

# New (equivalent)
bash rgw/ingestion_analysis/compare_ingestion_rate.sh old.json new.json

# Old v3 (with proper header)
bash compare_radosgw_ingestion-v3.sh old.json new.json 20000

# New (equivalent)
bash rgw/ingestion_analysis/compare_ingestion_rate.sh old.json new.json --threshold 20000
```

#### 4. Bucket Delta Scripts

| Legacy Script | New Script | Migration Command |
|---------------|------------|-------------------|
| `script.sh` | `ingestion_analysis/compare_bucket_deltas.sh` | Use `--columns 5` |
| `script-v2.sh` | Same | Use `--columns 6` |
| `script-v3.sh` | Same | Use `--columns 7` (default) |

**Migration Examples:**

```bash
# Old script.sh (5 columns)
awk '...' primary.txt secondary.txt | column -t

# New (equivalent)
bash rgw/ingestion_analysis/compare_bucket_deltas.sh primary.txt secondary.txt --columns 5

# Old script-v2.sh (6 columns with header)
awk '...' primary.txt secondary.txt | column -t

# New (equivalent)
bash rgw/ingestion_analysis/compare_bucket_deltas.sh primary.txt secondary.txt --columns 6

# Old script-v3.sh (7 columns with header)
awk '...' primary.txt secondary.txt | column -t

# New (equivalent)
bash rgw/ingestion_analysis/compare_bucket_deltas.sh primary.txt secondary.txt --columns 7
```

#### 5. Sync Error Parsing

| Legacy Script | New Script | Migration Command |
|---------------|------------|-------------------|
| `sync_err_parsing.sh` | `sync_analysis/parse_sync_errors.sh` | Direct replacement (enhanced) |

**Migration Examples:**

```bash
# Old
bash sync_err_parsing.sh sync_errors.json my-bucket

# New (equivalent, with improvements)
bash rgw/sync_analysis/parse_sync_errors.sh sync_errors.json my-bucket

# New with pretty printing
bash rgw/sync_analysis/parse_sync_errors.sh sync_errors.json my-bucket --pretty
```

## Step-by-Step Migration

### Step 1: Backup Existing Scripts

```bash
# Create backup of your current scripts
cp -r rgw/ rgw_backup_$(date +%Y%m%d)/
```

### Step 2: Update Script Paths

If you have automation scripts or cron jobs, update the paths:

```bash
# Old path
/path/to/compare_bucket_shards.py

# New path
/path/to/rgw/bucket_shard_analysis/compare_bucket_shards.py
```

### Step 3: Update Command-Line Arguments

Review your existing commands and add appropriate options:

**Example: Bucket Shard Comparison**

```bash
# Old command
python compare_bucket_shards-v3.py site1.json site2.json

# New command
python rgw/bucket_shard_analysis/compare_bucket_shards.py \
    site1.json site2.json \
    --sort-order desc \
    --output-format table
```

### Step 4: Test New Scripts

Run the new scripts with your actual data to verify output:

```bash
# Test with real data
python rgw/bucket_shard_analysis/compare_bucket_shards.py \
    /path/to/site1.json \
    /path/to/site2.json \
    --verbose
```

### Step 5: Update Documentation

Update any internal documentation, runbooks, or wikis with new script paths and options.

## Common Migration Scenarios

### Scenario 1: Automated Monitoring Script

**Old Script:**
```bash
#!/bin/bash
python /opt/scripts/compare_bucket_shards-v3.py \
    /data/site1_stats.json \
    /data/site2_stats.json > /var/log/shard_comparison.log
```

**New Script:**
```bash
#!/bin/bash
python /opt/scripts/rgw/bucket_shard_analysis/compare_bucket_shards.py \
    /data/site1_stats.json \
    /data/site2_stats.json \
    --sort-order desc \
    --output-format table > /var/log/shard_comparison.log
```

### Scenario 2: Cron Job for Stats Comparison

**Old Cron:**
```cron
0 2 * * * /usr/bin/python /opt/scripts/compare_bucket_stats_internal_json-v2.py /data/old.json /data/new.json
```

**New Cron:**
```cron
0 2 * * * /usr/bin/python /opt/scripts/rgw/bucket_stats_comparison/compare_bucket_stats.py /data/old.json /data/new.json --min-objects-per-shard 0
```

### Scenario 3: Report Generation

**Old Script:**
```bash
#!/bin/bash
DATE=$(date +%Y%m%d)
python compare_bucket_shards-v2.py site1.json site2.json > report_${DATE}.txt
```

**New Script:**
```bash
#!/bin/bash
DATE=$(date +%Y%m%d)
python rgw/bucket_shard_analysis/compare_bucket_shards.py \
    site1.json site2.json \
    --output-format csv > report_${DATE}.csv
```

## Feature Enhancements

### New Features Not in Legacy Scripts

#### 1. Multiple Output Formats

```bash
# JSON output for programmatic processing
python rgw/bucket_shard_analysis/compare_bucket_shards.py \
    site1.json site2.json \
    --output-format json | jq .

# CSV output for spreadsheets
python rgw/bucket_shard_analysis/compare_bucket_shards.py \
    site1.json site2.json \
    --output-format csv > results.csv
```

#### 2. Verbose Mode

```bash
# See detailed processing information
python rgw/bucket_shard_analysis/compare_bucket_shards.py \
    site1.json site2.json \
    --verbose
```

#### 3. Flexible Filtering

```bash
# Show all buckets (no filtering)
python rgw/bucket_shard_analysis/compare_bucket_shards.py \
    site1.json site2.json \
    --percentile 1.0

# Show only top 50% by object count
python rgw/bucket_shard_analysis/compare_bucket_shards.py \
    site1.json site2.json \
    --percentile 0.5
```

#### 4. Better Error Messages

The new scripts provide clear, actionable error messages:

```
Error (FileNotFoundError): Site 1 file not found: site1.json
Error (JSONDecodeError): Invalid JSON in file 'site2.json': Expecting value: line 1 column 1 (char 0)
Error (ValueError): Percentile must be between 0.0 and 1.0, got 1.5
```

## Troubleshooting

### Issue: "Module not found" Error

**Problem:**
```
ModuleNotFoundError: No module named 'utils'
```

**Solution:**
Ensure you're running scripts from the correct directory or that the Python path is set correctly:

```bash
# Run from project root
cd /path/to/ceph_custom_scripts
python rgw/bucket_shard_analysis/compare_bucket_shards.py site1.json site2.json
```

### Issue: Permission Denied

**Problem:**
```
bash: ./compare_bucket_shards.py: Permission denied
```

**Solution:**
Make scripts executable:

```bash
chmod +x rgw/bucket_shard_analysis/*.py
chmod +x rgw/bucket_stats_comparison/*.py
chmod +x rgw/ingestion_analysis/*.sh
chmod +x rgw/sync_analysis/*.sh
```

### Issue: Different Output Format

**Problem:**
Output looks different from legacy scripts.

**Solution:**
The new scripts use dynamic column widths. If you need exact legacy format, use CSV output:

```bash
python rgw/bucket_shard_analysis/compare_bucket_shards.py \
    site1.json site2.json \
    --output-format csv | column -t -s,
```

## Rollback Plan

If you need to rollback to legacy scripts:

### Option 1: Use Legacy Directory

```bash
# Legacy scripts are preserved
python legacy/rgw/compare_bucket_shards-v3.py site1.json site2.json
```

### Option 2: Restore from Backup

```bash
# Restore from your backup
cp -r rgw_backup_20260407/* rgw/
```

### Option 3: Create Symlinks

```bash
# Create symlinks for backward compatibility
cd rgw
ln -s bucket_shard_analysis/compare_bucket_shards.py compare_bucket_shards-v3.py
ln -s bucket_stats_comparison/compare_bucket_stats.py compare_bucket_stats_internal_json-v2.py
```

## Getting Help

- **Documentation**: See [README.md](README.md) for comprehensive documentation
- **Examples**: Check [rgw/examples/usage_examples.md](rgw/examples/usage_examples.md)
- **Architecture**: Review [ARCHITECTURE.md](ARCHITECTURE.md) for system design
- **Legacy Scripts**: Reference scripts in `legacy/rgw/` directory

## Checklist

Use this checklist to track your migration progress:

- [ ] Backup existing scripts
- [ ] Review script migration map
- [ ] Update automation scripts with new paths
- [ ] Update command-line arguments
- [ ] Test new scripts with real data
- [ ] Update documentation and runbooks
- [ ] Update cron jobs
- [ ] Update monitoring scripts
- [ ] Train team on new scripts
- [ ] Archive or remove old scripts (optional)

## Summary

The migration to v2.0.0 provides:

- **58% reduction** in script count (12 → 5)
- **Better organization** with clear directory structure
- **More features** with CLI options
- **Better documentation** with comprehensive guides
- **Backward compatibility** with legacy scripts preserved

All legacy functionality is preserved and enhanced. Take your time with the migration, and don't hesitate to use the legacy scripts during the transition period.