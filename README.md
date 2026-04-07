# Ceph RGW Custom Scripts

A comprehensive toolkit for analyzing Ceph RADOS Gateway (RGW) bucket statistics, comparing configurations across sites, and monitoring data ingestion rates.

**Version:** 2.0.0

## 📋 Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Directory Structure](#directory-structure)
- [Installation](#installation)
- [Quick Start](#quick-start)
- [Scripts](#scripts)
- [Configuration](#configuration)
- [Migration Guide](#migration-guide)
- [Examples](#examples)
- [Contributing](#contributing)
- [License](#license)

## 🎯 Overview

This toolkit provides a set of Python and Bash scripts for analyzing Ceph RGW bucket statistics. It helps administrators:

- Compare bucket shard configurations across multiple sites
- Analyze bucket statistics and object count changes over time
- Monitor data ingestion rates and identify high-growth buckets
- Parse and analyze sync errors

**What's New in v2.0:**
- Consolidated 12 scripts into 5 well-organized scripts
- Shared utility modules for code reuse
- Comprehensive CLI options replacing multiple script versions
- Better error handling and validation
- Extensive documentation and examples

## ✨ Features

- **Bucket Shard Analysis**: Compare shard counts between sites and identify misconfigurations
- **Stats Comparison**: Track object count changes between snapshots
- **Ingestion Monitoring**: Analyze data ingestion rates and growth patterns
- **Sync Error Analysis**: Parse and group sync errors by bucket
- **Multiple Output Formats**: Table, JSON, and CSV output support
- **Flexible Filtering**: Filter by percentiles, thresholds, and custom criteria
- **Configurable**: YAML configuration file for default settings

## 📁 Directory Structure

```
ceph_custom_scripts/
├── README.md                          # This file
├── REFACTORING_PLAN.md               # Detailed refactoring documentation
├── ARCHITECTURE.md                    # System architecture
├── IMPLEMENTATION_GUIDE.md            # Implementation details
│
├── rgw/                              # Main scripts directory
│   ├── bucket_shard_analysis/        # Bucket shard comparison
│   │   ├── compare_bucket_shards.py
│   │   └── README.md
│   │
│   ├── bucket_stats_comparison/      # Bucket statistics comparison
│   │   ├── compare_bucket_stats.py
│   │   └── README.md
│   │
│   ├── ingestion_analysis/           # Data ingestion analysis
│   │   ├── compare_ingestion_rate.sh
│   │   ├── compare_bucket_deltas.sh
│   │   └── README.md
│   │
│   ├── sync_analysis/                # Sync error analysis
│   │   ├── parse_sync_errors.sh
│   │   └── README.md
│   │
│   ├── utils/                        # Shared Python utilities
│   │   ├── __init__.py
│   │   ├── bucket_parser.py
│   │   ├── formatters.py
│   │   └── validators.py
│   │
│   ├── config/                       # Configuration files
│   │   └── defaults.yaml
│   │
│   └── examples/                     # Usage examples
│       ├── sample_data/
│       └── usage_examples.md
│
└── legacy/                           # Archived original scripts
    └── rgw/
```

## 🚀 Installation

### Prerequisites

- **Python 3.7+** (for Python scripts)
- **Bash 4.0+** (for shell scripts)
- **jq** (JSON processor for shell scripts)
- Standard Unix tools: `awk`, `column`, `sort`, `head`

### Setup

1. Clone or download this repository:
```bash
git clone <repository-url>
cd ceph_custom_scripts
```

2. Ensure scripts are executable:
```bash
chmod +x rgw/bucket_shard_analysis/*.py
chmod +x rgw/bucket_stats_comparison/*.py
chmod +x rgw/ingestion_analysis/*.sh
chmod +x rgw/sync_analysis/*.sh
```

3. (Optional) Add to PATH:
```bash
export PATH="$PATH:$(pwd)/rgw/bucket_shard_analysis"
export PATH="$PATH:$(pwd)/rgw/bucket_stats_comparison"
export PATH="$PATH:$(pwd)/rgw/ingestion_analysis"
export PATH="$PATH:$(pwd)/rgw/sync_analysis"
```

## 🏃 Quick Start

### 1. Compare Bucket Shards Between Sites

```bash
# Generate bucket stats on each site
radosgw-admin bucket stats > site1_stats.json
radosgw-admin bucket stats > site2_stats.json

# Compare shard configurations
./rgw/bucket_shard_analysis/compare_bucket_shards.py site1_stats.json site2_stats.json
```

### 2. Analyze Object Count Changes

```bash
# Take snapshots at different times
radosgw-admin bucket stats > stats_old.json
# ... wait some time ...
radosgw-admin bucket stats > stats_new.json

# Compare and see deltas
./rgw/bucket_stats_comparison/compare_bucket_stats.py stats_old.json stats_new.json
```

### 3. Monitor Ingestion Rates

```bash
# Compare ingestion between two snapshots
./rgw/ingestion_analysis/compare_ingestion_rate.sh old.json new.json --top-n 20
```

### 4. Parse Sync Errors

```bash
# Get sync errors
radosgw-admin sync error list > sync_errors.json

# Parse for specific bucket
./rgw/sync_analysis/parse_sync_errors.sh sync_errors.json my-bucket-name
```

## 📚 Scripts

### Bucket Shard Analysis

**Script:** `rgw/bucket_shard_analysis/compare_bucket_shards.py`

Compares bucket shard counts between two sites and identifies buckets with different configurations.

**Key Features:**
- Filters by object count percentile
- Sorts results by object count (ascending/descending)
- Multiple output formats (table, JSON, CSV)

**Usage:**
```bash
compare_bucket_shards.py site1.json site2.json [options]

Options:
  --percentile FLOAT        Threshold percentile (0.0-1.0, default: 0.25)
  --sort-order {asc,desc}   Sort order (default: asc)
  --output-format {table,json,csv}  Output format (default: table)
  --verbose                 Enable verbose output
```

**Examples:**
```bash
# Basic comparison
compare_bucket_shards.py site1.json site2.json

# Show all buckets (no filtering)
compare_bucket_shards.py site1.json site2.json --percentile 1.0

# Sort descending, output as JSON
compare_bucket_shards.py site1.json site2.json --sort-order desc --output-format json
```

### Bucket Stats Comparison

**Script:** `rgw/bucket_stats_comparison/compare_bucket_stats.py`

Compares bucket statistics between two snapshots and calculates object count deltas.

**Key Features:**
- Optional filtering by objects-per-shard threshold
- Sorts by delta, absolute delta, or name
- Identifies added/removed buckets

**Usage:**
```bash
compare_bucket_stats.py old_stats.json new_stats.json [options]

Options:
  --min-objects-per-shard INT  Threshold (0=no filter, default: 2000)
  --sort-by {delta,abs-delta,name}  Sort criteria (default: abs-delta)
  --output-format {table,json,csv}  Output format (default: table)
  --show-all                   Show buckets with no changes
```

**Examples:**
```bash
# Basic comparison with filtering
compare_bucket_stats.py old.json new.json

# Compare all buckets (no filtering)
compare_bucket_stats.py old.json new.json --min-objects-per-shard 0

# Show all buckets including unchanged
compare_bucket_stats.py old.json new.json --show-all
```

### Ingestion Rate Analysis

**Script:** `rgw/ingestion_analysis/compare_ingestion_rate.sh`

Analyzes data ingestion rates between two snapshots.

**Key Features:**
- Filters by objects-per-shard threshold
- Shows top N buckets by delta or object count
- Configurable sorting and display options

**Usage:**
```bash
compare_ingestion_rate.sh old.json new.json [options]

Options:
  --threshold INT           Objects/shard threshold (default: 20000)
  --top-n INT              Show top N buckets (0=all, default: 10)
  --sort-by {delta,objects}  Sort criteria (default: delta)
  --no-header              Omit header row
```

**Examples:**
```bash
# Show top 10 by delta
compare_ingestion_rate.sh old.json new.json

# Show top 20 with lower threshold
compare_ingestion_rate.sh old.json new.json --threshold 10000 --top-n 20

# Show all buckets sorted by current object count
compare_ingestion_rate.sh old.json new.json --top-n 0 --sort-by objects
```

### Bucket Delta Comparison

**Script:** `rgw/ingestion_analysis/compare_bucket_deltas.sh`

Compares pre-processed bucket data files and calculates deltas.

**Key Features:**
- Multiple column format options (5, 6, or 7 columns)
- Backward compatible with legacy scripts
- Table or TSV output

**Usage:**
```bash
compare_bucket_deltas.sh primary.txt secondary.txt [options]

Options:
  --columns {5,6,7}        Column format (default: 7)
  --no-header             Omit header row
  --format {table,tsv}    Output format (default: table)
```

### Sync Error Parser

**Script:** `rgw/sync_analysis/parse_sync_errors.sh`

Parses and analyzes RGW sync errors.

**Key Features:**
- Groups errors by message
- Filters by bucket name
- Provides error counts and timestamps

**Usage:**
```bash
parse_sync_errors.sh sync_errors.json bucket_name [options]

Options:
  --pretty                Pretty-print JSON output
```

## ⚙️ Configuration

Default settings are stored in `rgw/config/defaults.yaml`. You can customize:

- Default percentiles and thresholds
- Sort orders and output formats
- Table formatting options
- Logging levels
- Performance settings

Example configuration:
```yaml
bucket_shard_analysis:
  default_percentile: 0.25
  default_sort_order: "asc"
  default_output_format: "table"

bucket_stats_comparison:
  default_min_objects_per_shard: 2000
  default_sort_by: "abs-delta"
```

## 🔄 Migration Guide

### From Legacy Scripts

If you're migrating from the old scripts, here's the mapping:

| Old Script | New Script | Notes |
|------------|------------|-------|
| `compare_bucket_shards.py` | `bucket_shard_analysis/compare_bucket_shards.py` | Use `--sort-order asc` |
| `compare_bucket_shards-v2.py` | Same as above | Default behavior |
| `compare_bucket_shards-v3.py` | Same as above | Use `--sort-order desc` |
| `compare_bucket_stats_internal_json.py` | `bucket_stats_comparison/compare_bucket_stats.py` | Use `--min-objects-per-shard 2000` |
| `compare_bucket_stats_internal_json-v2.py` | Same as above | Use `--min-objects-per-shard 0` |
| `compare_radosgw_ingestion.sh` | `ingestion_analysis/compare_ingestion_rate.sh` | Use `--top-n 0` for v1 behavior |
| `compare_radosgw_ingestion-v2.sh` | Same as above | Default behavior |
| `compare_radosgw_ingestion-v3.sh` | Same as above | Default behavior |
| `script.sh` | `ingestion_analysis/compare_bucket_deltas.sh` | Use `--columns 5` |
| `script-v2.sh` | Same as above | Use `--columns 6 --header` |
| `script-v3.sh` | Same as above | Use `--columns 7 --header` |
| `sync_err_parsing.sh` | `sync_analysis/parse_sync_errors.sh` | Enhanced version |

**Legacy scripts are preserved in the `legacy/rgw/` directory for reference.**

## 📖 Examples

See `rgw/examples/usage_examples.md` for detailed examples including:

- Multi-site bucket shard comparison workflows
- Time-series object count analysis
- Ingestion rate monitoring and alerting
- Sync error troubleshooting
- Automated reporting scripts

## 🤝 Contributing

Contributions are welcome! Please:

1. Follow the existing code style
2. Add tests for new features
3. Update documentation
4. Submit pull requests with clear descriptions

## 📄 License

[Add your license information here]

## 📞 Support

For issues, questions, or contributions:
- Review the documentation in `ARCHITECTURE.md` and `IMPLEMENTATION_GUIDE.md`
- Check `rgw/examples/usage_examples.md` for common use cases
- Refer to legacy scripts in `legacy/rgw/` for comparison

## 🎉 Acknowledgments

This refactoring consolidates and improves upon the original Ceph RGW analysis scripts, making them more maintainable, flexible, and user-friendly.

---

**Version 2.0.0** - Refactored and consolidated from 12 legacy scripts
