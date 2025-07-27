# Enhanced Business Rule Engine

The EDI CLI includes a sophisticated business rule engine that provides field-level validation and detailed error reporting capabilities. This engine goes beyond simple YAML rules to offer complex business logic validation, mathematical calculations, and comprehensive reporting.

## Overview

The Enhanced Business Rule Engine provides:

- **Field-Level Validation**: Detailed validation of individual fields with format checking
- **Cross-Field Validation**: Consistency checks between related fields
- **Mathematical Validation**: Balance checks, calculations, and financial logic
- **Custom Business Logic**: Complex validation functions for specialized business rules
- **Detailed Error Reporting**: Rich context and diagnostic information
- **Performance Optimization**: Efficient validation with minimal overhead

## Architecture

### Core Components

1. **BusinessRuleEngine**: Main engine that orchestrates validation
2. **BusinessRule**: Individual business rules with multiple validation types
3. **FieldValidator**: Specialized validators for individual fields
4. **BusinessRuleValidationPlugin**: Integration with the main validation framework
5. **FieldLevelValidationPlugin**: Specialized field-level validation reporting

### Validation Types

#### Field-Level Validators

- `currency_format`: Validates monetary amounts (precision, range, format)
- `date_format`: Validates dates (format, range, reasonableness)
- `npi_format`: Validates National Provider Identifier (10 digits)
- `tax_id_format`: Validates Tax ID/EIN formats
- `range`: Validates numeric ranges
- `enum`: Validates against allowed value lists
- `regex`: Validates against regular expression patterns
- `required`: Validates field presence
- `conditional_required`: Context-dependent required field validation

#### Cross-Field Validations

- `balance_check`: Financial balance validation with tolerance
- `consistency_check`: Relationship validation between fields
- `calculation_check`: Mathematical calculation verification
- `logical_check`: Complex business logic evaluation

## Usage

### Command Line Interface

#### Enhanced Business Rules Only
```bash
edi validate sample.edi --rule-set enhanced-business --verbose
```

#### Comprehensive Validation (All Rules)
```bash
edi validate sample.edi --rule-set comprehensive --verbose
```

### Available Rule Sets

| Rule Set | Description |
|----------|-------------|
| `basic` | Basic structural validation (YAML) |
| `business` | Business logic validation (YAML) |
| `hipaa` | HIPAA compliance rules (YAML) |
| `hipaa-advanced` | Advanced HIPAA safeguards (YAML) |
| `enhanced-business` | Advanced business rule engine |
| `comprehensive` | All YAML rules + enhanced business engine |
| `all` | All YAML rules only |

## Business Rules for EDI 835

### Financial Validation Rules

#### Comprehensive Financial Balance
- **Purpose**: Validates BPR total against sum of claim payments
- **Features**: 
  - PLB (Provider Level Adjustment) consideration
  - Configurable tolerance (default: $0.01)
  - Detailed financial reporting
- **Severity**: Warning
- **Example**:
  ```
  Financial imbalance: BPR total $2350.75 vs claims total $2351.00, difference $0.25
  ```

#### Claim Payment Validation
- **Purpose**: Validates individual claim payment logic
- **Features**:
  - Overpayment detection (paid > charged)
  - Zero payment analysis
  - Adjustment requirement checking
- **Severity**: Warning
- **Example**:
  ```
  Claim overpayment detected: paid $1200.75 > charged $1125.25
  ```

### Data Format Validation

#### Currency Format Validation
- **Purpose**: Ensures all monetary fields follow proper format
- **Features**:
  - Maximum 2 decimal places
  - Reasonable value ranges
  - Proper numeric format
- **Fields Validated**:
  - BPR total paid amount
  - Claim charge/paid amounts
  - Patient responsibility
- **Severity**: Error

#### Date Format Validation
- **Purpose**: Validates date fields for format and reasonableness
- **Features**:
  - CCYYMMDD format validation
  - Reasonable date range checking (10 years back to 1 year forward)
  - Multiple date format support
- **Severity**: Warning

#### Identifier Format Validation
- **Purpose**: Validates healthcare identifiers
- **Features**:
  - NPI format (exactly 10 digits)
  - Tax ID/EIN format validation
  - Payment method code validation
- **Severity**: Warning/Info

### Service Line Validation

#### Service Line Totals
- **Purpose**: Validates service line amounts aggregate to claim totals
- **Features**:
  - Service charge total validation
  - Service payment total validation
  - Tolerance-based comparison
- **Severity**: Info
- **Example**:
  ```
  Service line charges ($1125.00) do not match claim total ($1125.25)
  ```

### Adjustment Validation

#### Claim Adjustment Validation
- **Purpose**: Validates claim adjustment codes and amounts
- **Features**:
  - Reason code format validation
  - Zero adjustment detection
  - Invalid amount format detection
- **Severity**: Warning

#### Provider Level Adjustment (PLB) Validation
- **Purpose**: Validates provider-level adjustments
- **Features**:
  - Unusual amount detection (>$50,000)
  - Zero adjustment flagging
  - Missing reason detection
- **Severity**: Info

### Consistency Validation

#### Claim Consistency
- **Purpose**: Validates logical consistency across claim fields
- **Features**:
  - Charge vs. paid amount relationships
  - Zero payment logic validation
  - Conditional field requirements
- **Severity**: Warning

### Business Logic Validation

#### Comprehensive Business Logic
- **Purpose**: Applies sophisticated business rules
- **Features**:
  - High-value transaction flagging (>$100,000)
  - High claim volume detection (>100 claims)
  - Negative patient responsibility detection
  - Zero claim detection
- **Severity**: Info/Warning

## Error Reporting

### Rich Context Information

The enhanced business rule engine provides detailed context for each validation error:

```json
{
  "severity": "warning",
  "message": "Financial imbalance: BPR total $2350.75 vs claims total $2351.00",
  "code": "835_FINANCIAL_IMBALANCE",
  "path": "interchange[0].functional_group[0].transaction[0]",
  "context": {
    "rule_category": "financial",
    "validation_type": "business_rule",
    "financial_details": {
      "bpr_total": "2350.75",
      "claims_total": "2351.00",
      "difference": "0.25",
      "tolerance": "0.01"
    }
  }
}
```

### Context Types

- **Financial Details**: BPR totals, claim totals, differences, tolerances
- **Field Details**: Field paths, values, validation parameters
- **Calculation Details**: Expected vs. actual values, calculation types
- **Adjustment Details**: Adjustment indices, reason codes, amounts
- **Service Line Details**: Service totals vs. claim totals
- **PLB Details**: PLB indices, amounts, reasons

## Performance Characteristics

### Execution Metrics

- **Typical Execution Time**: 1-5ms for standard 835 transactions
- **Memory Usage**: Minimal overhead with efficient field extraction
- **Scalability**: Handles large transactions (100+ claims) efficiently

### Optimization Features

- **Lazy Evaluation**: Field values extracted only when needed
- **Error Tolerance**: Continues validation despite individual field errors
- **Context Caching**: Reuses extracted values across validations

## Integration

### Plugin Architecture

The business rule engine integrates seamlessly with the existing validation framework through plugins:

- **BusinessRuleValidationPlugin**: Main business logic validation
- **FieldLevelValidationPlugin**: Specialized field-level validation

### Extensibility

#### Adding Custom Business Rules

```python
from core.validation.business_engine import BusinessRule, FieldValidator, BusinessRuleSeverity

def create_custom_rule():
    return BusinessRule(
        name="custom_validation",
        description="Custom business validation",
        category="custom",
        severity=BusinessRuleSeverity.WARNING,
        field_validators=[
            FieldValidator(
                field_path="custom.field",
                validator_type="range",
                parameters={'min': 0, 'max': 1000},
                error_message="Custom field must be between 0 and 1000"
            )
        ]
    )
```

#### Custom Validation Functions

```python
def custom_validation_function(transaction_data):
    errors = []
    # Custom validation logic
    if some_complex_condition:
        errors.append({
            'severity': 'warning',
            'message': 'Custom validation failed',
            'code': 'CUSTOM_ERROR'
        })
    return errors
```

## Best Practices

### Rule Development

1. **Use Appropriate Severity Levels**:
   - `CRITICAL`: Blocking business errors
   - `ERROR`: Standard violations requiring attention
   - `WARNING`: Concerns that should be reviewed
   - `INFO`: Insights and notifications

2. **Provide Meaningful Error Messages**:
   - Include actual vs. expected values
   - Specify field paths clearly
   - Explain business impact

3. **Set Reasonable Tolerances**:
   - Use appropriate tolerance for financial calculations
   - Consider real-world data variations
   - Document tolerance rationale

4. **Optimize Performance**:
   - Avoid redundant field extractions
   - Use efficient comparison methods
   - Handle exceptions gracefully

### Validation Strategy

1. **Layered Validation**:
   - Start with basic structural validation
   - Add business logic validation
   - Include compliance checks
   - Apply field-level validation

2. **Progressive Enhancement**:
   - Begin with essential rules
   - Add sophisticated validation incrementally
   - Monitor performance impact

3. **Context-Aware Validation**:
   - Consider transaction context
   - Apply appropriate business rules
   - Customize validation based on data characteristics

## Troubleshooting

### Common Issues

#### Field Path Errors
- **Issue**: Field not found during validation
- **Solution**: Verify field path syntax and data structure
- **Example**: Use `claims[0].total_paid` not `claims.total_paid`

#### Performance Issues
- **Issue**: Slow validation with large transactions
- **Solution**: Optimize custom validation functions, check for infinite loops

#### False Positives
- **Issue**: Valid data flagged as errors
- **Solution**: Adjust tolerance values, review business logic

### Debugging

#### Enable Verbose Logging
```python
import logging
logging.getLogger('core.validation').setLevel(logging.DEBUG)
```

#### Field Value Inspection
```python
# Extract field value directly for debugging
validator = FieldValidator("field.path", "dummy")
value = validator._extract_field_value(transaction_data, "field.path")
print(f"Field value: {value}")
```

## Future Enhancements

### Planned Features

- **Rule Templates**: Pre-defined rule templates for common scenarios
- **Dynamic Rule Loading**: Runtime rule configuration
- **Rule Dependencies**: Rules that depend on other rule results
- **Batch Validation**: Validation across multiple transactions
- **Machine Learning Integration**: Anomaly detection using ML models

### Extension Points

- **Custom Validators**: Additional field validation types
- **External Data Sources**: Integration with external validation data
- **Reporting Formats**: Additional output formats (PDF, Excel)
- **API Integration**: REST API for validation services

The Enhanced Business Rule Engine represents a significant advancement in EDI validation capabilities, providing healthcare organizations with the tools needed for comprehensive, accurate, and efficient transaction validation.