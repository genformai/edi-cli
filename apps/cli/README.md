# EDI CLI - Terminal Application

Command-line interface for parsing, validating, and analyzing EDI files.

## Features

- Parse EDI 835, 837P, 270/271, 276/277 transaction sets
- Comprehensive validation with YAML-based rules
- HIPAA compliance checking
- Plugin architecture for custom transaction types
- JSON and CSV export formats
- Batch processing capabilities

## Installation

```bash
# Install from project root
pip install -e apps/cli

# Or install published package
pip install edi-cli
```

## Usage

```bash
# Convert EDI to JSON
edi convert sample-835.edi --to json --schema 835

# Validate with business rules
edi validate sample-835.edi --rule-set comprehensive --verbose

# Inspect EDI structure
edi inspect sample.edi --segments BPR,CLP,SV1
```

## Commands

- `convert` - Convert EDI files to JSON/CSV
- `validate` - Validate EDI files with rule sets
- `inspect` - Inspect EDI structure and segments
- `plugin` - Manage parser plugins

## Development

```bash
# Install in development mode
cd apps/cli
pip install -e .

# Run tests
python -m pytest

# Run specific command
python -m src.main convert sample.edi --to json
```

## Integration

The CLI uses the shared core library located in `../../core/` for:
- Transaction parsers
- Validation engines
- Schema definitions
- Plugin system

See the [core library documentation](../../core/README.md) for API details.