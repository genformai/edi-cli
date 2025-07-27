# YAML Validation DSL Documentation

The EDI CLI includes a powerful YAML-based Domain Specific Language (DSL) for defining custom validation rules. This allows users to create sophisticated validation logic without writing Python code.

## Overview

The YAML validation framework enables you to:
- Define custom business rules for EDI transactions
- Validate data integrity and compliance requirements  
- Create reusable rule sets for different scenarios
- Integrate validation into automated workflows

## Basic Structure

A YAML validation file contains a `rules` array where each rule defines validation logic:

```yaml
rules:
  - name: "rule_name"
    description: "What this rule validates"
    severity: "error|warning|info"
    transaction_types: ["835"]
    category: "structural|business|data|compliance"
    error_code: "CUSTOM_ERROR_CODE"
    message: "Error message shown to users"
    enabled: true
    conditions:
      - field: "field.path"
        operator: "comparison_operator"
        value: expected_value
        message: "Optional condition-specific message"
```

## Field Reference

### Rule Properties

| Property | Required | Description |
|----------|----------|-------------|
| `name` | Yes | Unique identifier for the rule |
| `description` | Yes | Human-readable description |
| `severity` | No | `error`, `warning`, or `info` (default: `error`) |
| `transaction_types` | No | Array of transaction codes (default: `["835"]`) |
| `category` | No | Rule category for organization |
| `error_code` | No | Custom error code (auto-generated if not specified) |
| `message` | No | Custom error message |
| `enabled` | No | Whether rule is active (default: `true`) |
| `conditions` | Yes | Array of validation conditions |

### Condition Properties

| Property | Required | Description |
|----------|----------|-------------|
| `field` | Yes | Path to the field being validated |
| `operator` | Yes | Comparison operator (see below) |
| `value` | No | Expected value (required for most operators) |
| `message` | No | Custom message for this condition |

## Field Paths

Field paths use dot notation to navigate the transaction data structure:

### Common 835 Field Paths

```yaml
# Financial Information
financial_information.total_paid
financial_information.payment_method
financial_information.payment_date

# Payer/Payee Information
payer.name
payee.name
payee.npi
payee.tax_id

# Claims (use [0] for first claim, [1] for second, etc.)
claims[0].claim_id
claims[0].status_code
claims[0].total_charge
claims[0].total_paid
claims[0].patient_responsibility

# Services within claims
claims[0].services[0].service_code
claims[0].services[0].procedure_code
claims[0].services[0].charge_amount
claims[0].services[0].paid_amount

# Provider Level Adjustments
plb[0].provider_npi
plb[0].amount
plb[0].reason

# Transaction Header
header.transaction_set_code
header.transaction_set_control_number
```

## Operators

| Operator | Description | Example |
|----------|-------------|---------|
| `exists` | Field exists and is not null | `field: "payer"` |
| `not_exists` | Field is missing or null | `field: "optional_field"` |
| `eq` | Equals | `value: "ACH"` |
| `ne` | Not equals | `value: "INVALID"` |
| `gt` | Greater than | `value: 0` |
| `lt` | Less than | `value: 10000` |
| `gte` | Greater than or equal | `value: 0` |
| `lte` | Less than or equal | `value: 999.99` |
| `in` | Value is in list | `value: ["ACH", "CHK"]` |
| `not_in` | Value is not in list | `value: ["INVALID", "TEST"]` |
| `matches` | Regex pattern match | `value: "\\d{5}"` |
| `not_matches` | Regex pattern doesn't match | `value: "^[A-Z]+"` |

## Rule Examples

### Structural Validation

```yaml
rules:
  - name: "require_payer"
    description: "Payer information must be present"
    severity: "error"
    conditions:
      - field: "payer"
        operator: "not_exists"
        message: "Missing required payer information"
```

### Data Validation

```yaml
rules:
  - name: "positive_amounts"
    description: "Financial amounts must be non-negative"
    severity: "error"
    conditions:
      - field: "financial_information.total_paid"
        operator: "lt"
        value: 0
        message: "Total paid amount cannot be negative"
```

### Business Logic

```yaml
rules:
  - name: "high_value_alert"
    description: "Alert for high-value transactions"
    severity: "info"
    conditions:
      - field: "financial_information.total_paid"
        operator: "gt"
        value: 50000
        message: "High-value transaction requires additional review"
```

### Compliance Rules

```yaml
rules:
  - name: "require_npi"
    description: "Payee must have valid NPI"
    severity: "error"
    category: "compliance"
    conditions:
      - field: "payee.npi"
        operator: "not_exists"
        message: "NPI required for HIPAA compliance"
```

### Pattern Matching

```yaml
rules:
  - name: "validate_procedure_codes"
    description: "Procedure codes must follow CPT format"
    severity: "warning"
    conditions:
      - field: "claims[0].services[0].procedure_code"
        operator: "not_matches"
        value: "^\\d{5}$"
        message: "Procedure code must be 5 digits"
```

## Predefined Rule Sets

The CLI includes predefined rule sets:

### Basic Rules (`--rule-set basic`)
- Required segments (BPR, payer, payee)
- Non-negative amounts
- Valid payment methods
- Claim structure validation

### Business Rules (`--rule-set business`)
- Includes all basic rules
- Financial balance checks
- Business logic validation
- Overpayment detection

### All Rules (`--rule-set all`)
- All basic and business rules
- Comprehensive validation coverage

## Usage Examples

### Command Line

```bash
# Use predefined rule set
edi validate sample.edi --rule-set basic

# Use custom rules file
edi validate sample.edi --rules my-rules.yml

# Combine with verbose output
edi validate sample.edi --rule-set business --verbose
```

### Custom Rules File

Create `my-rules.yml`:

```yaml
rules:
  - name: "company_specific_validation"
    description: "Validate company-specific requirements"
    severity: "error"
    conditions:
      - field: "payer.name"
        operator: "in"
        value: ["APPROVED_PAYER_1", "APPROVED_PAYER_2"]
        
  - name: "payment_threshold"
    description: "Flag payments over threshold"
    severity: "warning"
    conditions:
      - field: "financial_information.total_paid"
        operator: "gt"
        value: 1000
```

Then run: `edi validate sample.edi --rules my-rules.yml`

## Advanced Features

### Multiple Conditions

Rules can have multiple conditions (all must be true to trigger):

```yaml
rules:
  - name: "complex_validation"
    description: "Multiple condition example"
    conditions:
      - field: "claims[0].total_paid"
        operator: "eq"
        value: 0
      - field: "claims[0].status_code"
        operator: "eq"
        value: "22"
    message: "Zero payment with denial status"
```

### Rule Categories

Organize rules by category:

```yaml
rules:
  - name: "hipaa_compliance"
    category: "compliance"
    # ... rule definition
    
  - name: "business_logic"
    category: "business"
    # ... rule definition
```

### Conditional Enablement

Enable/disable rules as needed:

```yaml
rules:
  - name: "optional_check"
    enabled: false  # Disabled by default
    # ... rule definition
```

## Best Practices

1. **Use descriptive names**: Make rule names clear and specific
2. **Provide good error messages**: Help users understand what's wrong
3. **Choose appropriate severity**: Use `error` for blocking issues, `warning` for concerns, `info` for notifications
4. **Test your rules**: Validate against sample data to ensure they work correctly
5. **Document complex logic**: Use descriptions to explain business rules
6. **Organize by category**: Group related rules together
7. **Use appropriate operators**: Choose the most specific operator for your validation

## Limitations

- Array indexing requires specific indices (e.g., `claims[0]`)
- Complex business logic may require custom Python rules
- Pattern matching uses Python regex syntax
- Field paths must match exact data structure

## Integration

The YAML validation DSL integrates seamlessly with:
- Command-line validation workflows
- CI/CD pipelines
- Automated testing
- Custom business processes

For advanced validation scenarios requiring custom logic, consider extending the validation engine with Python-based rules.