# Enhanced EDI Test Fixtures

A comprehensive, modern fixture system for X12 EDI transaction testing with realistic data, scenario-based patterns, and flexible builder APIs.

## Overview

This fixture system replaces the original static fixtures with a powerful, data-driven approach that provides:

- **Realistic Test Data**: YAML-based realistic payers, providers, and medical codes
- **Builder Pattern**: Fluent API for constructing custom test scenarios
- **Pre-built Scenarios**: Common testing patterns ready to use
- **Error Testing**: Dedicated scenarios for validation and error handling
- **Integration Testing**: Complex multi-transaction workflows
- **Backward Compatibility**: Existing tests continue to work unchanged

## Quick Start

### Basic Usage

```python
from tests.core.fixtures import EDI835Builder, PaymentScenarios

# Use pre-built scenario
edi_data = PaymentScenarios.ach_payment_standard().build()

# Build custom fixture
edi_data = (EDI835Builder()
           .with_realistic_payer()
           .with_realistic_payee()
           .with_ach_payment(Decimal("1000.00"))
           .with_primary_claim(charge=Decimal("1200.00"), paid=Decimal("1000.00"))
           .build())
```

### Available Builders

- **EDI835Builder** - Electronic Remittance Advice (Payment)
- **EDI270Builder** - Eligibility Inquiry
- **EDI276Builder** - Claim Status Inquiry  
- **EDI837pBuilder** - Professional Healthcare Claim

### Pre-built Scenarios

#### Payment Scenarios
- `ach_payment_standard()` - Standard ACH payment
- `check_payment_large()` - Large check payment
- `wire_transfer_urgent()` - Wire transfer
- `coordination_of_benefits()` - COB secondary payer
- `overpayment_recovery()` - Overpayment recovery
- `high_volume_batch()` - High-volume batch processing

#### Claim Scenarios
- `fully_paid_claim()` - Claim paid in full
- `partial_payment_claim()` - Partial payment with adjustments
- `denied_claim()` - Completely denied claim
- `claim_with_deductible()` - Patient deductible applied
- `bundled_services_claim()` - Multiple bundled services

#### Error Scenarios
- `invalid_npi_transaction()` - Invalid NPI format
- `missing_required_segments()` - Missing data
- `negative_payment_amounts()` - Invalid amounts
- `malformed_segments()` - Corrupted EDI

#### Integration Scenarios
- `complete_patient_workflow()` - End-to-end patient journey
- `multi_payer_coordination()` - Primary/secondary coordination
- `claim_correction_workflow()` - Denial and resubmission

## Realistic Data Sources

### YAML Data Files

- **payers.yaml** - Insurance companies with real names and IDs
- **providers.yaml** - Healthcare providers and facilities
- **procedure_codes.yaml** - CPT codes with descriptions and charges
- **diagnosis_codes.yaml** - ICD-10 codes organized by specialty

### Data Loader Usage

```python
from tests.core.fixtures import data_loader

# Get realistic payers
commercial_payer = data_loader.get_random_payer(payer_type="insurance")
government_payer = data_loader.get_random_payer(payer_type="government")

# Get providers by specialty
cardiologist = data_loader.get_random_provider(specialty="207RC0000X")

# Get related codes
diagnosis, procedure, charge = data_loader.get_related_diagnosis_and_procedure("cardiovascular")
```

## Builder API Reference

### Common Builder Methods

All builders inherit from `EDIBuilder` and support:

```python
builder = (EDIBuilder()
          .with_envelope(sender, receiver, functional_id, version)
          .with_control_numbers(interchange, group, transaction)
          .with_payer(name, id, address)
          .with_payee(name, npi, address)
          .with_trace_number(trace_id))
```

### EDI835Builder Specific Methods

```python
payment = (EDI835Builder()
          .with_ach_payment(amount, routing_number, account_number)
          .with_check_payment(amount, check_number)
          .with_wire_payment(amount, wire_reference)
          .with_no_payment()
          .with_primary_claim(claim_id, charge, paid, patient_resp)
          .with_secondary_claim(claim_id, charge, paid, patient_resp, prior_paid)
          .with_denied_claim(claim_id, charge, reason_code)
          .with_adjustment(group, reason, amount)
          .with_multiple_claims(count))
```

### EDI270Builder Specific Methods

```python
eligibility = (EDI270Builder()
              .with_subscriber(first_name, last_name, member_id)
              .with_dependent(first_name, last_name, relationship)
              .with_provider(name, npi)
              .with_eligibility_inquiry(service_type)
              .with_service_date_range(start_date, end_date))
```

### EDI837pBuilder Specific Methods

```python
claim = (EDI837pBuilder()
        .with_billing_provider(name, npi, tax_id)
        .with_rendering_provider(first_name, last_name, npi)
        .with_subscriber(first_name, last_name, member_id)
        .with_diagnosis(diagnosis_code)
        .with_office_visit(procedure_code, charge)
        .with_place_of_service(pos_code))
```

## Migration Guide

### From Old Fixtures

**Before:**
```python
from tests.core.fixtures import EDIFixtures
edi_data = EDIFixtures.get_minimal_835()
```

**After:**
```python
from tests.core.fixtures import EDI835Builder
edi_data = EDI835Builder().with_realistic_payer().with_ach_payment(Decimal("1000.00")).build()
```

### Common Migration Patterns

1. **Static → Scenario**: Replace static fixtures with pre-built scenarios
2. **Hardcoded → Realistic**: Use YAML data instead of hardcoded values
3. **Manual → Builder**: Use fluent API instead of string concatenation
4. **Single → Multiple**: Create variations using builders instead of duplicate fixtures

See `MIGRATION.md` for detailed migration instructions.

## Testing Patterns

### Unit Testing

```python
def test_ach_payment_processing():
    # Arrange
    payment_data = PaymentScenarios.ach_payment_standard().build()
    
    # Act
    result = process_payment(payment_data)
    
    # Assert
    assert result.payment_method == "ACH"
    assert result.total_amount > 0
```

### Integration Testing

```python
def test_complete_patient_workflow():
    workflow = IntegrationScenarios.complete_patient_workflow()
    
    # Test each step
    eligibility_response = process_eligibility(workflow["eligibility_inquiry"].build())
    claim_response = process_claim(workflow["claim_submission"].build())
    payment_response = process_payment(workflow["payment_advice"].build())
    
    # Verify workflow consistency
    assert eligibility_response.patient_id == claim_response.patient_id
```

### Error Testing

```python
def test_invalid_data_handling():
    invalid_data = ErrorScenarios.invalid_npi_transaction().build()
    
    with pytest.raises(ValidationError):
        process_transaction(invalid_data)
```

### Performance Testing

```python
def test_high_volume_processing():
    batch_data = PaymentScenarios.high_volume_batch().build()
    
    start_time = time.time()
    result = process_batch(batch_data)
    processing_time = time.time() - start_time
    
    assert len(result.claims) >= 15
    assert processing_time < 5.0  # Should process within 5 seconds
```

## Advanced Usage

### Custom Scenarios

```python
def create_cardiology_scenario():
    return (EDI835Builder()
           .with_realistic_payer()
           .with_provider("HEART SPECIALISTS", specialty="207RC0000X")
           .with_ach_payment(Decimal("1500.00"))
           .with_diagnosis("I25.10")  # Coronary artery disease
           .with_service("93307", Decimal("800.00"))  # Echocardiogram
           .with_adjustment("CO", "45", Decimal("300.00")))
```

### Pytest Fixtures

```python
@pytest.fixture
def medicare_payment():
    payer = data_loader.get_random_payer(payer_type="government")
    return (EDI835Builder()
           .with_payer(payer['name'], payer['id'])
           .with_realistic_payee()
           .with_ach_payment(Decimal("750.00")))

def test_medicare_processing(medicare_payment):
    edi_data = medicare_payment.build()
    result = process_medicare_payment(edi_data)
    assert result.is_government_payer
```

### Data Validation

```python
def test_realistic_data_quality():
    # Verify payer data is realistic
    payer = data_loader.get_random_payer()
    assert len(payer['id']) >= 5
    assert payer['name'].isupper()
    assert 'address' in payer
    
    # Verify procedure codes are valid
    procedure = data_loader.get_random_procedure_codes(count=1)[0]
    assert procedure['code'].isdigit()
    assert len(procedure['code']) == 5
    assert procedure['typical_charge'] > 0
```

## File Structure

```
tests/core/fixtures/
├── __init__.py                 # Main exports
├── MIGRATION.md               # Migration guide
├── README.md                  # This file
├── legacy_fixtures.py         # Backward compatibility
├── migration_examples.py      # Migration examples
│
├── base/                      # Core infrastructure
│   ├── data_types.py         # Data classes and enums
│   └── generators.py         # Data generators
│
├── builders/                  # Transaction builders
│   ├── edi_builder.py        # Base builder class
│   ├── builder_835.py        # 835 builder
│   ├── builder_270.py        # 270 builder
│   ├── builder_276.py        # 276 builder
│   └── builder_837p.py       # 837P builder
│
├── scenarios/                 # Pre-built scenarios
│   ├── payment_scenarios.py  # Payment scenarios
│   ├── claim_scenarios.py    # Claim scenarios
│   ├── error_scenarios.py    # Error scenarios
│   └── integration_scenarios.py # Integration scenarios
│
└── data/                     # YAML data sources
    ├── data_loader.py        # Data loading utilities
    ├── payers.yaml           # Insurance payers
    ├── providers.yaml        # Healthcare providers
    ├── procedure_codes.yaml  # CPT codes
    └── diagnosis_codes.yaml  # ICD-10 codes
```

## Contributing

### Adding New Scenarios

1. Create scenario in appropriate file (`payment_scenarios.py`, etc.)
2. Follow naming convention: `{description}_{type}_scenario()`
3. Use realistic data from YAML sources
4. Add to `get_all_scenarios()` method
5. Update documentation

### Adding New Transaction Types

1. Create builder in `builders/` directory
2. Inherit from `EDIBuilder`
3. Implement transaction-specific methods
4. Add to main `__init__.py`
5. Create scenarios in `scenarios/` directory

### Adding New Data Sources

1. Create YAML file in `data/` directory
2. Update `data_loader.py` with loading methods
3. Add filtering and selection capabilities
4. Update generators to use new data
5. Add tests for data quality

## Best Practices

1. **Use Scenarios First**: Check if existing scenario meets your needs
2. **Realistic Data**: Prefer YAML data over hardcoded values
3. **Builder Pattern**: Use fluent API for custom requirements
4. **Error Testing**: Include negative test cases
5. **Performance**: Test with realistic data volumes
6. **Documentation**: Document custom scenarios and patterns

## Support

- **Migration Issues**: See `MIGRATION.md` and `migration_examples.py`
- **Custom Scenarios**: Reference existing scenarios in `scenarios/` directory
- **Data Issues**: Check YAML files in `data/` directory
- **Builder API**: See method documentation in builder classes

The legacy `EDIFixtures` class remains available for backward compatibility during migration.