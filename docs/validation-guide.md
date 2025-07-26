# EDI Validation Guide (v0.2)

This guide covers the comprehensive validation capabilities introduced in edi-cli v0.2, including business rules, HIPAA compliance, and custom validation configuration.

## Overview

The validation engine in edi-cli v0.2 provides multi-layered validation:

1. **Structural Validation**: Ensures EDI documents are properly formatted
2. **Business Rules**: Validates business logic and data consistency
3. **HIPAA Compliance**: Enforces healthcare industry standards
4. **Custom Rules**: Allows user-defined validation logic via YAML configuration

## Quick Start

### Basic Validation

```bash
# Simple parsing validation
edi validate sample.edi

# Basic business rules
edi validate sample.edi --rule-set basic

# HIPAA compliance checking
edi validate sample.edi --rule-set hipaa

# Comprehensive validation
edi validate sample.edi --rule-set business --verbose
```

### JSON Output for Integration

```bash
edi validate sample.edi --rule-set basic --format json > validation-results.json
```

## Built-in Rule Sets

### Basic Rules (`--rule-set basic`)

Validates fundamental EDI structure and required fields:

- **Interchange Header (ISA)**: Sender/receiver IDs, dates, control numbers
- **Financial Information (BPR)**: Total paid amounts, payment methods, dates
- **Claim Information (CLP)**: Claim IDs, status codes, monetary amounts
- **Service Information (SVC)**: Service codes, charge amounts, dates
- **Adjustment Information (CAS)**: Group codes, reason codes, amounts

### HIPAA Rules (`--rule-set hipaa`)

Enforces healthcare industry compliance standards:

- **NPI Validation**: 10-digit National Provider Identifier with Luhn algorithm check
- **Date Formats**: Proper CCYYMMDD → YYYY-MM-DD conversion
- **Amount Precision**: Maximum 2 decimal places for monetary values
- **Entity Identifiers**: Required healthcare entity information
- **Control Numbers**: Unique interchange and transaction control numbers
- **Transaction Codes**: Valid HIPAA transaction set codes (835, 837, 270, etc.)

### Business Rules (`--rule-set business`)

Comprehensive business logic validation:

- **Financial Consistency**: Total paid amounts match sum of claim payments  
- **Claim Validation**: Paid amounts don't exceed charges, valid status codes
- **Service Line Logic**: Service amounts consistent with claim totals
- **Date Logic**: Service dates not in future, logical date relationships
- **Adjustment Logic**: Valid group codes, positive amounts

## Custom Validation Rules

### YAML Configuration Format

Create custom validation rules using YAML configuration:

```yaml
# custom-rules.yml
version: "0.2.0"
transaction_set: "835"
description: "Custom validation rules for 835 processing"

rules:
  - id: "CUSTOM_PAYER_NAME"
    type: "field"
    description: "Payer name must be present"
    field_path: "interchanges.0.functional_groups.0.transactions.0.payer.name"
    validation_type: "required"
    severity: "error"
    category: "business"
    
  - id: "CUSTOM_AMOUNT_RANGE"
    type: "field" 
    description: "Total paid must be reasonable amount"
    field_path: "interchanges.0.functional_groups.0.transactions.0.financial_information.total_paid"
    validation_type: "numeric"
    severity: "warning"
    category: "business"
```

### Validation Types

#### Field Validation Types

- **`required`**: Field must be present and non-empty
- **`regex`**: Field must match regular expression pattern
- **`length`**: Field length must be within min/max bounds
- **`numeric`**: Field must be a valid number
- **`custom`**: Use custom validator function

#### Custom Validator Functions

Built-in custom validators:
- `validate_npi`: NPI Luhn algorithm validation
- `validate_amount_format`: Monetary amount format validation
- `validate_control_number`: Control number format validation

### Using Custom Rules

```bash
edi validate sample.edi --rules custom-rules.yml --verbose
```

## Validation Categories

### Error Severity Levels

- **`error`**: Critical issues that make the document invalid
- **`warning`**: Issues that should be addressed but don't invalidate the document
- **`info`**: Informational notices about the document

### Validation Categories

- **`structural`**: EDI document structure and format
- **`business`**: Business logic and data consistency  
- **`hipaa`**: HIPAA compliance requirements
- **`format`**: Data format and pattern validation
- **`custom`**: User-defined validation rules

## Advanced Features

### Field Path Navigation

The validation engine uses dot notation to navigate document structure:

```yaml
# Access nested fields
field_path: "interchanges.0.functional_groups.0.transactions.0.claims.*.total_charge"

# Array access with wildcards
field_path: "claims.*.services.*.charge_amount"

# Specific array indices
field_path: "interchanges.0.header.sender_id"
```

### Validation Context

Pass additional context for validation:

```python
from packages.core.validation import ValidationEngine

engine = ValidationEngine()
context = {
    "trading_partner": "ACME_INSURANCE",
    "validation_date": "2024-03-15"
}
result = engine.validate(edi_root, context=context)
```

## Error Analysis

### Understanding Validation Results

```json
{
  "is_valid": false,
  "summary": {
    "errors": 2,
    "warnings": 1, 
    "info": 0,
    "rules_applied": 25
  },
  "errors": [
    {
      "code": "BPR_TOTAL_PAID_NUMERIC",
      "message": "Total paid amount must be numeric",
      "severity": "error",
      "category": "business",
      "field_path": "financial_information.total_paid",
      "value": "invalid",
      "rule_id": "BPR_TOTAL_PAID_NUMERIC"
    }
  ]
}
```

### Common Validation Issues

#### Financial Inconsistencies
```
Error: 835_FINANCIAL_CONSISTENCY
Cause: Sum of claim payments ≠ total paid amount
Solution: Verify claim amounts or total paid calculation
```

#### NPI Validation Failures
```
Error: HIPAA_NPI_LUHN_CHECK  
Cause: NPI fails Luhn algorithm check
Solution: Verify NPI is correct 10-digit number
```

#### Date Format Issues
```
Error: BPR_PAYMENT_DATE_FORMAT
Cause: Date not in YYYY-MM-DD format
Solution: Ensure dates follow ISO format after parsing
```

## Integration Examples

### Python Integration

```python
from packages.core.parser import EdiParser
from packages.core.validation import ValidationEngine
from packages.core.validators_835 import get_835_business_rules

# Parse EDI
parser = EdiParser(edi_string=edi_content, schema_path=schema_path)
edi_root = parser.parse()

# Set up validation
engine = ValidationEngine()
engine.load_rules_from_yaml("rules/basic.yml")
for rule in get_835_business_rules():
    engine.add_rule(rule)

# Validate
result = engine.validate(edi_root)

if not result.is_valid:
    for error in result.errors:
        print(f"Error: {error.message}")
```

### CI/CD Integration

```bash
#!/bin/bash
# validate-edi.sh

set -e

for file in edi-files/*.edi; do
    echo "Validating $file..."
    if ! edi validate "$file" --rule-set business --format json > "${file%.edi}-validation.json"; then
        echo "❌ Validation failed for $file"
        exit 1
    fi
done

echo "✅ All EDI files validated successfully"
```

## Performance Considerations

### Rule Loading
- YAML rules are parsed once during engine initialization
- Business rules are cached for reuse
- Use rule sets to minimize validation overhead

### Large Files
- Validation memory usage scales with document size
- Consider validating in batches for very large files
- Stream processing coming in future versions

## Troubleshooting

### Common Issues

**Rules not loading**: Check YAML syntax and file paths
**False positives**: Review rule severity levels and field paths  
**Performance**: Use specific rule sets instead of loading all rules
**Custom validators**: Ensure custom functions are properly imported

### Debug Mode

```bash
# Enable verbose logging
export EDI_CLI_LOG_LEVEL=DEBUG
edi validate sample.edi --rule-set basic --verbose
```

## Next Steps

- Review the [CLI Reference](cli.md) for complete command options
- Explore the [roadmap](roadmap-detailed.md) for upcoming validation features
- Contribute custom validation rules to the community

The validation engine in v0.2 provides a solid foundation for ensuring EDI data quality and compliance. As we progress toward v0.3, expect additional transaction set support and more sophisticated validation capabilities.