# CLI Reference

This document provides a detailed reference for the `edi-cli` command-line interface.

## `convert`

Converts an EDI file to another format (e.g., JSON, CSV).

### Usage

```bash
edi convert <input_file> --to <format> --out <output_file> [--schema <schema_name>]
```

### Arguments

*   `<input_file>`: The path to the input EDI file.
*   `--to <format>`: The output format (`json` or `csv`).
*   `--out <output_file>`: The path to the output file.
*   `--schema <schema_name>`: (Optional) The name of the schema to use for parsing.

## `validate`

Validates an EDI file against a schema and a set of rules.

### Usage

```bash
edi validate <input_file> --schema <schema_name> [--rules <rules_file>]
```

### Arguments

*   `<input_file>`: The path to the input EDI file.
*   `--schema <schema_name>`: The name of the schema to use for validation.
*   `--rules <rules_file>`: (Optional) The path to a YAML file containing validation rules.

## `inspect`

Inspects an EDI file and extracts specific segments.

### Usage

```bash
edi inspect <input_file> --segments <segment_list>
```

### Arguments

*   `<input_file>`: The path to the input EDI file.
*   `--segments <segment_list>`: A comma-separated list of segment IDs to extract (e.g., `NM1,CLP`).

## `diff`

Compares two EDI files.

### Usage

```bash
edi diff <file_a> <file_b> [--schema <schema_name>]
```

### Arguments

*   `<file_a>`: The path to the first EDI file.
*   `<file_b>`: The path to the second EDI file.
*   `--schema <schema_name>`: (Optional) The name of the schema to use for parsing.
