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

Validates an EDI file against a schema and comprehensive business rules with HIPAA compliance checking.

### Usage

```bash
edi validate <input_file> [--schema <schema_name>] [--rules <rules_file>] [--rule-set <set_name>] [--verbose] [--format <format>]
```

### Arguments

*   `<input_file>`: The path to the input EDI file.
*   `--schema <schema_name>`: (Optional) The name of the schema to use for validation. Default: `x12-835-5010`.
*   `--rules <rules_file>`: (Optional) The path to a YAML file containing custom validation rules.
*   `--rule-set <set_name>`: (Optional) Predefined rule set to use (`basic`, `hipaa`, `business`).
*   `--verbose`, `-v`: (Optional) Show detailed validation results including field paths and values.
*   `--format <format>`: (Optional) Output format (`text`, `json`). Default: `text`.

### Examples

```bash
# Basic validation with parsing only
edi validate sample.edi

# Validate with basic business rules
edi validate sample.edi --rule-set basic

# Validate with HIPAA compliance rules
edi validate sample.edi --rule-set hipaa

# Validate with comprehensive business rules
edi validate sample.edi --rule-set business

# Validate with custom rules file
edi validate sample.edi --rules custom-rules.yml

# Get detailed validation results
edi validate sample.edi --rule-set basic --verbose

# Get JSON output for programmatic use
edi validate sample.edi --rule-set basic --format json
```

### Validation Features (v0.2)

**Built-in Rule Sets:**
- **`basic`**: Structural validation, required fields, format checking
- **`hipaa`**: HIPAA compliance validation including NPI verification, date formats, amount precision
- **`business`**: Comprehensive business logic validation including financial consistency, claim validation

**Business Rules Validation:**
- Financial consistency across transactions
- Claim amount validation and logic checks
- Service line validation and consistency
- Date validation and logical constraints
- Payer/payee information validation with NPI Luhn algorithm

**HIPAA Compliance:**
- NPI validation with Luhn algorithm check
- Proper date format validation (CCYYMMDD → YYYY-MM-DD)
- Monetary amount precision requirements (max 2 decimal places)
- Entity identifier requirements
- Control number format validation

**Field-level Validation:**
- Required field checking
- Data type validation (numeric, date, text)
- Format validation with regex patterns
- Length constraints
- Custom validation functions

**Error Reporting:**
- Detailed error messages with field paths
- Severity levels (error, warning, info)
- Categorized validation results (structural, business, HIPAA, format)
- Summary statistics and document structure analysis

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
