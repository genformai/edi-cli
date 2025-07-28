# EDI Fixtures Migration Guide

This guide helps you migrate from the old `fixtures.py` system to the new enhanced fixture architecture.

## Overview

The new fixture system provides:
- **Builder Pattern**: Fluent API for constructing test data
- **Realistic Data**: YAML-based realistic payers, providers, and codes
- **Scenario-Based**: Pre-built scenarios for common testing patterns
- **Type Safety**: Proper data structures and validation
- **Extensibility**: Easy to add new transaction types and scenarios

## Quick Migration

### Old Way (Still Works)
```python
from tests.core.fixtures import EDIFixtures

# Old API still works through legacy layer
edi_data = EDIFixtures.get_minimal_835()
```

### New Way (Recommended)
```python
from tests.core.fixtures import EDI835Builder, PaymentScenarios

# Build custom fixture
edi_data = (EDI835Builder()
           .with_realistic_payer()
           .with_realistic_payee() 
           .with_ach_payment(Decimal("1000.00"))
           .with_primary_claim(charge=Decimal("1200.00"), paid=Decimal("1000.00"))
           .build())

# Or use pre-built scenario
edi_data = PaymentScenarios.ach_payment_standard().build()
```

## Migration Steps

### Step 1: Update Imports

**Before:**
```python
from tests.core.fixtures import EDIFixtures
```

**After:**
```python
# For backward compatibility (temporary)
from tests.core.fixtures import EDIFixtures

# For new system (recommended)
from tests.core.fixtures import (
    EDI835Builder, EDI270Builder, EDI276Builder, EDI837pBuilder,
    PaymentScenarios, ClaimScenarios, ErrorScenarios,
    data_loader
)
```

### Step 2: Replace Static Fixtures with Builders

**Before:**
```python
def test_835_processing():
    edi_data = EDIFixtures.get_minimal_835()
    # test logic
```

**After:**
```python
def test_835_processing():
    edi_data = (EDI835Builder()
               .with_realistic_payer()
               .with_ach_payment(Decimal("1000.00"))
               .build())
    # test logic
```

### Step 3: Use Scenarios for Common Patterns

**Before:**
```python
def test_multiple_claims():
    edi_data = EDIFixtures.get_835_with_multiple_claims()
```

**After:**
```python
def test_multiple_claims():
    edi_data = PaymentScenarios.mixed_claim_statuses().build()
```

### Step 4: Leverage Realistic Data

**Before:**
```python
# Hardcoded test data
payer_name = "INSURANCE COMPANY"
```

**After:**
```python
# Realistic test data
payer = data_loader.get_random_payer()
payer_name = payer['name']  # e.g., "AETNA BETTER HEALTH"
```

## Migration Mapping

### EDI 835 Fixtures

| Old Method | New Approach |
|------------|--------------|
| `get_minimal_835()` | `EDI835Builder().with_realistic_payer().with_ach_payment().build()` |
| `get_835_with_multiple_claims()` | `PaymentScenarios.mixed_claim_statuses().build()` |
| `get_835_denied_claim()` | `ClaimScenarios.denied_claim().build()` |

### EDI 270 Fixtures

| Old Method | New Approach |
|------------|--------------|
| `get_270_eligibility_inquiry()` | `EDI270Builder.minimal().build()` |

### Sample Data

| Old Method | New Approach |
|------------|--------------|
| `get_sample_addresses()` | Use `AddressGenerator` or YAML data |
| `get_sample_adjustments()` | Use builder adjustment methods |
| `get_sample_service_lines()` | Use builder service methods |

## Advanced Usage

### Custom Scenarios
```python
# Create your own scenario
def create_cardiology_payment():
    return (EDI835Builder()
           .with_realistic_payer()
           .with_provider("HEART SPECIALISTS", specialty="207RC0000X")
           .with_ach_payment(Decimal("1500.00"))
           .with_primary_claim(charge=Decimal("1800.00"), paid=Decimal("1500.00"))
           .with_diagnosis("I25.10")  # Coronary artery disease
           .with_service("93307", Decimal("800.00"))  # Echocardiogram
           .with_service("99243", Decimal("300.00"))  # Consultation
           .build())
```

### Error Testing
```python
# Test invalid data
invalid_edi = ErrorScenarios.invalid_npi_transaction().build()

# Test specific error conditions
malformed_edi = ErrorScenarios.malformed_segments().build()
```

### Integration Testing
```python
# Complete workflow testing
workflow = IntegrationScenarios.complete_patient_workflow()
eligibility = workflow["eligibility_inquiry"].build()
claim = workflow["claim_submission"].build()
payment = workflow["payment_advice"].build()
```

## Benefits of Migration

1. **More Realistic Tests**: Use actual insurance company names, real NPIs, valid procedure codes
2. **Better Maintainability**: Centralized data management through YAML files
3. **Improved Readability**: Fluent API makes test intent clearer
4. **Enhanced Flexibility**: Easy to create custom scenarios for specific test cases
5. **Type Safety**: Proper data structures prevent common errors
6. **Performance**: Lazy loading and caching of test data

## Gradual Migration Strategy

1. **Phase 1**: Start using new builders for new tests
2. **Phase 2**: Replace static fixtures with scenarios for existing tests
3. **Phase 3**: Enhance tests with realistic data from YAML sources
4. **Phase 4**: Remove dependency on legacy fixtures

## Common Patterns

### Testing Payment Processing
```python
def test_ach_payment():
    payment = PaymentScenarios.ach_payment_standard()
    edi_data = payment.build()
    # Test ACH processing logic

def test_check_payment():
    payment = PaymentScenarios.check_payment_large()
    edi_data = payment.build()
    # Test check processing logic
```

### Testing Claim Scenarios
```python
def test_fully_paid_claim():
    claim = ClaimScenarios.fully_paid_claim()
    edi_data = claim.build()
    # Test full payment processing

def test_partial_payment():
    claim = ClaimScenarios.partial_payment_claim()
    edi_data = claim.build()
    # Test partial payment handling
```

### Testing Error Conditions
```python
def test_invalid_npi():
    invalid_data = ErrorScenarios.invalid_npi_transaction()
    edi_data = invalid_data.build()
    # Test validation error handling

def test_missing_segments():
    minimal_data = ErrorScenarios.missing_required_segments()
    edi_data = minimal_data.build()
    # Test missing data handling
```

## Support

The legacy `EDIFixtures` class will remain available for backward compatibility, but new development should use the enhanced fixture system. Both systems can coexist during the migration period.