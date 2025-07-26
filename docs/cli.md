# CLI Reference

This document provides a detailed reference for the `edi-cli` command-line interface.

## `convert`

Converts an EDI file to another format (JSON or CSV).

### Usage

```bash
edi convert <input_file> [--to <format>] [--out <output_file>] [--schema <schema_name>]
```

### Arguments

*   `<input_file>`: The path to the input EDI file.
*   `--to <format>`: (Optional) The output format (`json` or `csv`). Default: `json`.
*   `--out <output_file>`, `-o <output_file>`: (Optional) The path to the output file. If not provided, outputs to stdout.
*   `--schema <schema_name>`: (Optional) The name of the schema to use for parsing. Default: `x12-835-5010`.

### Examples

```bash
# Convert to JSON (default)
edi convert sample.edi

# Convert to JSON with output file
edi convert sample.edi --to json --out output.json

# Convert to CSV
edi convert sample.edi --to csv --out claims.csv
```

## `validate`

Validates an EDI file against a schema and performs basic parsing validation.

### Usage

```bash
edi validate <input_file> [--schema <schema_name>] [--rules <rules_file>]
```

### Arguments

*   `<input_file>`: The path to the input EDI file.
*   `--schema <schema_name>`: (Optional) The name of the schema to use for validation. Default: `x12-835-5010`.
*   `--rules <rules_file>`: (Optional) The path to a YAML file containing validation rules. *(Note: Custom rules not yet implemented in v0.1)*

### Examples

```bash
# Basic validation
edi validate sample.edi

# Validate with specific schema
edi validate sample.edi --schema x12-835-5010
```

The validate command currently performs:
- Basic parsing validation
- Structure verification
- Element counting (interchanges, functional groups, transactions, claims)

## `inspect`

Inspects an EDI file and extracts specific segments or shows file structure.

### Usage

```bash
edi inspect <input_file> [--segments <segment_list>] [--schema <schema_name>]
```

### Arguments

*   `<input_file>`: The path to the input EDI file.
*   `--segments <segment_list>`: (Optional) A comma-separated list of segment IDs to extract (e.g., `NM1,CLP`). If not provided, shows file structure summary.
*   `--schema <schema_name>`: (Optional) The name of the schema to use for parsing. Default: `x12-835-5010`.

### Examples

```bash
# Show file structure
edi inspect sample.edi

# Extract specific segments
edi inspect sample.edi --segments CLP,SVC

# Extract claim and adjustment segments
edi inspect sample.edi --segments CLP,CAS,SVC
```

## `diff`

Compares two EDI files and shows high-level differences.

### Usage

```bash
edi diff <file_a> <file_b> [--schema <schema_name>]
```

### Arguments

*   `<file_a>`: The path to the first EDI file.
*   `<file_b>`: The path to the second EDI file.
*   `--schema <schema_name>`: (Optional) The name of the schema to use for parsing. Default: `x12-835-5010`.

### Examples

```bash
# Compare two EDI files
edi diff file1.edi file2.edi

# Compare with specific schema
edi diff original.edi modified.edi --schema x12-835-5010
```

The diff command currently shows:
- Whether files are identical when parsed
- High-level structural differences (number of interchanges)
- Basic comparison statistics
