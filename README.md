# LogKit

A command-line tool for analyzing line-delimited JSON log files with filtering and aggregation capabilities.

## Project Overview

LogKit provides utilities to parse, filter, and analyze log events from JSON-formatted log files. It supports filtering by source IP, message content, and timestamp ranges, and can generate both human-readable and JSON output formats.

## Project Structure

### Core Modules

- **logkit/** - Main package directory
  - **logkit/__init__.py** - Package initialization file
  - **logkit/__main__.py** - Entry point for running the package as a module (`python -m logkit`)
  - **logkit/cli.py** - Command-line interface and argument parsing
  - **logkit/parser.py** - Core log parsing and filtering logic

### Supporting Files

- **main.py** - Primary entry point that delegates to the CLI
- **pyproject.toml** - Project configuration (pytest settings)
- **tests/** - Test suite with unit tests for core functionality

### Output Examples

- **out.txt** - Sample text output showing log counts by level
- **out.json** - Sample JSON output with metadata and filters
- **top.csv** - Sample CSV output of top source IPs

## Core Functional Elements

### 1. Event Model (logkit/parser.py)

The `Event` dataclass represents a single log entry with:
- `ts` - Timestamp (ISO8601 format)
- `level` - Log level (e.g., INFO, WARN, ERROR)
- `msg` - Log message text
- `src_ip` - Source IP address

### 2. Log Parsing (logkit/parser.py)

**`iter_events()`** - Reads and parses a line-delimited JSON log file with optional filtering:
- Supports timestamp range filtering (`since` and `until` parameters)
- Strict mode for validation (raises on malformed JSON)
- Lazy evaluation via generator pattern for memory efficiency

**`parse_ts()`** - Converts ISO8601 timestamps to UTC datetime objects

### 3. Aggregation Functions (logkit/parser.py)

**`count_by_level()`** - Aggregates log events by their level:
- Optional filtering by source IP
- Optional filtering by message content (case-insensitive substring match)

**`top_src_ips()`** - Identifies the most frequent source IP addresses:
- Returns top N entries sorted by count
- Optional message filtering

### 4. CLI Interface (logkit/cli.py)

**`main()`** - Main entry point handling:
- Argument parsing and validation
- Filter application (IP, message content, timestamps)
- Multiple output formats (text, JSON, CSV)
- File output capability

**`emit()`** - Output helper that writes to file or stdout

## Usage

### Basic Usage

```bash
python main.py data/sample.log
```

### Command-Line Options

- `--src-ip IP` - Filter to a specific source IP address
- `--contains TEXT` - Filter to messages containing this text (case-insensitive)
- `--since TIMESTAMP` - Include only events at/after this ISO8601 timestamp
- `--until TIMESTAMP` - Include only events at/before this ISO8601 timestamp
- `--top-src N` - Show top N source IP addresses (default: 0, disabled)
- `--top-src-csv FILE` - Write top source IPs as CSV to file
- `--json` - Output results as JSON instead of text
- `--out FILE` - Write output to file instead of stdout
- `--quiet` - Suppress stdout output (useful with `--out`)
- `--strict` - Fail on first malformed JSON line (default: skip)

### Examples

```bash
# Count logs by level
python main.py data/sample.log

# Filter by source IP and get JSON output
python main.py data/sample.log --src-ip 10.0.0.5 --json

# Find top 5 IPs with messages containing "error"
python main.py data/sample.log --contains error --top-src 5 --top-src-csv top_errors.csv

# Filter by timestamp range
python main.py data/sample.log --since "2026-01-30T05:00:00Z" --until "2026-01-30T05:00:03Z"

# Combined filters with file output
python main.py data/sample.log \
  --src-ip 10.0.0.8 \
  --contains "login failed" \
  --json \
  --out results.json \
  --quiet
```

## Output Formats

### Text Output

Simple columnar format showing counts by log level:
```
ERROR  1
INFO   2
WARN   2
```

With `--top-src`:
```
ERROR  1
INFO   2
WARN   2

Top source IPs:
10.0.0.5  2
10.0.0.8  2
```

### JSON Output

Structured output with metadata and filters applied:
```json
{
  "counts_by_level": {
    "ERROR": 1,
    "INFO": 2,
    "WARN": 2
  },
  "filters": {
    "contains": null,
    "since": null,
    "src_ip": null,
    "strict": false,
    "until": null
  },
  "path": "data/sample.log"
}
```

### CSV Output

Top source IPs in CSV format:
```
src_ip,count
10.0.0.5,2
10.0.0.8,2
```

## Testing

Run the test suite with pytest:

```bash
pytest tests/
```

Tests cover:
- Basic log counting by level
- Message content filtering
- Source IP filtering
- Timestamp range filtering
- Combined filter scenarios
- Strict mode validation
- JSON output format

## Requirements

- Python 3.12+
- Standard library only (no external dependencies)

## Development

This project uses a dev container with Python 3.12 and common development tools pre-installed.
