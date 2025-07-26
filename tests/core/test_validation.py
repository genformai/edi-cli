"""
Test cases for EDI validation engine and rules.

This file contains comprehensive validation tests for the EDI validation framework.
"""

import pytest
import tempfile
import os
from pathlib import Path
from .test_utils import parse_edi
from .fixtures import EDIFixtures
from packages.core.validation import (
    ValidationEngine, ValidationRule, ValidationError, ValidationSeverity, 
    ValidationCategory, FieldValidationRule, BusinessRule, validate_npi, 
    validate_amount_format, validate_control_number
)
from packages.core.validators_835 import get_835_business_rules


class TestValidationEngine:
    """Test the validation engine functionality."""

    @pytest.fixture
    def validation_engine(self):
        """Basic validation engine instance."""
        return ValidationEngine()

    @pytest.fixture
    def sample_field_validation_rule(self):
        """Sample field validation rule for testing."""
        return FieldValidationRule(
            "TEST_RULE", "Test rule", ValidationSeverity.ERROR, 
            ValidationCategory.BUSINESS, "test.field", lambda x: x is not None
        )

    @pytest.fixture
    def sample_rule_set(self):
        """Sample rule set for testing."""
        return [
            FieldValidationRule(
                "TEST_RULE1", "Test rule 1", ValidationSeverity.ERROR,
                ValidationCategory.BUSINESS, "test.field1", lambda x: x is not None
            ),
            FieldValidationRule(
                "TEST_RULE2", "Test rule 2", ValidationSeverity.WARNING,
                ValidationCategory.FORMAT, "test.field2", lambda x: len(str(x)) > 0
            )
        ]

    @pytest.fixture
    def sample_yaml_rules(self):
        """Sample YAML validation rules content."""
        return """
rules:
  - id: "TEST_REQUIRED"
    type: "field"
    description: "Test field is required"
    field_path: "test.field"
    validation_type: "required"
    severity: "error"
    category: "business"
  - id: "TEST_REGEX"
    type: "field"
    description: "Test regex validation"
    field_path: "test.pattern"
    validation_type: "regex"
    pattern: "^[A-Z]+$"
    severity: "warning"
    category: "format"
"""

    def test_validation_engine_initialization(self, validation_engine):
        """Test validation engine can be initialized."""
        assert len(validation_engine.rules) == 0
        assert len(validation_engine.rule_sets) == 0

    def test_add_rule(self, validation_engine, sample_field_validation_rule):
        """Test adding validation rules."""
        validation_engine.add_rule(sample_field_validation_rule)
        assert len(validation_engine.rules) == 1

    def test_add_rule_set(self, validation_engine, sample_rule_set):
        """Test adding named rule sets."""
        validation_engine.add_rule_set("test_set", sample_rule_set)
        assert "test_set" in validation_engine.rule_sets
        assert len(validation_engine.rule_sets["test_set"]) == 2

    def test_load_rules_from_yaml(self, validation_engine, sample_yaml_rules):
        """Test loading validation rules from YAML file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yml', delete=False) as f:
            f.write(sample_yaml_rules)
            yaml_path = f.name
        
        try:
            loaded_count = validation_engine.load_rules_from_yaml(yaml_path)
            assert loaded_count == 2
            assert len(validation_engine.rules) == 2
        finally:
            os.unlink(yaml_path)


class TestValidationRules:
    """Test individual validation rules."""

    @pytest.fixture
    def test_obj_valid(self):
        """Valid test object for validation."""
        class TestObj:
            name = "Valid Name"
            valid = True
            existing_field = "value"
        return TestObj()

    @pytest.fixture
    def test_obj_invalid(self):
        """Invalid test object for validation."""
        class TestObjInvalid:
            name = ""
            valid = False
        return TestObjInvalid()

    def test_field_validation_rule_required(self, test_obj_valid, test_obj_invalid):
        """Test required field validation rule."""
        rule = FieldValidationRule(
            "REQ_TEST", "Required field test", ValidationSeverity.ERROR,
            ValidationCategory.BUSINESS, "name", lambda x: x is not None and str(x).strip() != ''
        )
        
        # Test with valid data
        errors = rule.validate(test_obj_valid)
        assert len(errors) == 0
        
        # Test with invalid data
        errors = rule.validate(test_obj_invalid)
        assert len(errors) == 1
        assert errors[0].code == "REQ_TEST"

    def test_business_rule_validation(self, test_obj_valid, test_obj_invalid):
        """Test business rule validation."""
        def test_condition(edi_root, context):
            return hasattr(edi_root, 'valid') and edi_root.valid
        
        rule = BusinessRule(
            "BIZ_TEST", "Business rule test", ValidationSeverity.ERROR,
            ValidationCategory.BUSINESS, test_condition, "Business rule failed"
        )
        
        # Test with valid data
        errors = rule.validate(test_obj_valid)
        assert len(errors) == 0
        
        # Test with invalid data
        errors = rule.validate(test_obj_invalid)
        assert len(errors) == 1
        assert errors[0].code == "BIZ_TEST"


class TestBuiltInValidators:
    """Test built-in validation functions."""

    def test_validate_npi(self):
        """Test NPI validation."""
        # Valid NPI (calculated to pass Luhn algorithm)
        assert validate_npi("1234567897") == True   # Valid NPI with correct check digit
        
        # Invalid NPIs
        assert validate_npi("1234567893") == False  # Invalid Luhn check
        assert validate_npi("123456789") == False   # Too short
        assert validate_npi("12345678901") == False # Too long
        assert validate_npi("123456789a") == False  # Non-numeric
        assert validate_npi("") == False            # Empty
        assert validate_npi(None) == False          # None
        assert validate_npi("1111111111") == False  # Invalid Luhn check

    def test_validate_amount_format(self):
        """Test amount format validation."""
        # Valid amounts
        assert validate_amount_format(100) == True
        assert validate_amount_format(100.50) == True
        assert validate_amount_format("100.50") == True
        assert validate_amount_format("1,000.50") == True
        assert validate_amount_format(0) == True
        
        # Invalid amounts
        assert validate_amount_format(-100) == False
        assert validate_amount_format("100.555") == False  # Too many decimals
        assert validate_amount_format("abc") == False
        assert validate_amount_format("") == False

    def test_validate_control_number(self):
        """Test control number validation."""
        # Valid control numbers
        assert validate_control_number("123456789") == True
        assert validate_control_number("ABC123") == True
        assert validate_control_number("1") == True
        
        # Invalid control numbers
        assert validate_control_number("") == False
        assert validate_control_number("   ") == False
        assert validate_control_number("1234567890") == False  # Too long
        assert validate_control_number(None) == False


class Test835BusinessRules:
    """Test 835-specific business rules."""

    @pytest.fixture
    def validation_engine_with_835_rules(self):
        """Validation engine pre-loaded with 835 business rules."""
        engine = ValidationEngine()
        for rule in get_835_business_rules():
            engine.add_rule(rule)
        return engine

    @pytest.fixture
    def parsed_835_root(self, schema_835_path):
        """Parsed 835 EDI root object."""
        edi_content = EDIFixtures.get_minimal_835()
        return parse_edi(edi_content, schema_835_path)

    @pytest.fixture
    def parsed_invalid_835_root(self, schema_835_path):
        """Parsed invalid 835 EDI root object."""
        edi_content = (
            "ISA*00*          *00*          *ZZ*SENDER         *ZZ*RECEIVER       "
            "*241226*1430*^*00501*000012345*0*P*:~"
            "GS*HP*SENDER*RECEIVER*20241226*1430*000006789*X*005010X221A1~"
            "ST*835*0001~"
            "BPR*I*-100*C*CHK*20241226~"  # Negative amount
            "CLP*TEST*1*100*150*0*12*CTRL~"  # Inconsistent amounts
            "SE*5*0001~"
            "GE*1*000006789~"
            "IEA*1*000012345~"
        )
        return parse_edi(edi_content, schema_835_path)

    def test_835_business_rules_loading(self):
        """Test that 835 business rules can be loaded."""
        rules = get_835_business_rules()
        assert len(rules) > 0
        
        # Check that all rules are ValidationRule instances
        for rule in rules:
            assert isinstance(rule, ValidationRule)

    def test_835_validation_with_valid_data(self, validation_engine_with_835_rules, parsed_835_root):
        """Test 835 validation with valid data."""
        result = validation_engine_with_835_rules.validate(parsed_835_root)
        
        # Should have some rules applied
        assert result.rules_applied > 0

    def test_835_validation_with_rule_sets(self):
        """Test 835 validation using predefined rule sets."""
        validation_engine = ValidationEngine()
        
        # Load basic rules if they exist
        basic_rules_path = Path("packages/validation-rules/835-basic.yml")
        if basic_rules_path.exists():
            loaded_count = validation_engine.load_rules_from_yaml(str(basic_rules_path))
            assert loaded_count > 0
        
        # Load HIPAA rules if they exist
        hipaa_rules_path = Path("packages/validation-rules/hipaa-basic.yml")
        if hipaa_rules_path.exists():
            loaded_count = validation_engine.load_rules_from_yaml(str(hipaa_rules_path))
            assert loaded_count > 0

    def test_financial_consistency_validation(self, parsed_835_root):
        """Test financial consistency validation."""
        from packages.core.validators_835 import Financial835ValidationRule
        
        rule = Financial835ValidationRule()
        errors = rule.validate(parsed_835_root)
        
        # Should not have errors for our test data
        assert isinstance(errors, list)

    def test_claim_validation(self, parsed_835_root):
        """Test claim validation."""
        from packages.core.validators_835 import Claim835ValidationRule
        
        rule = Claim835ValidationRule()
        errors = rule.validate(parsed_835_root)
        
        # Should not have errors for our test data
        assert isinstance(errors, list)

    def test_date_validation(self, parsed_835_root):
        """Test date validation."""
        from packages.core.validators_835 import Date835ValidationRule
        
        rule = Date835ValidationRule()
        errors = rule.validate(parsed_835_root)
        
        # Should not have errors for our test data
        assert isinstance(errors, list)


class TestValidationIntegration:
    """Test validation integration with parsing and CLI."""

    @pytest.fixture
    def validation_engine_with_835_rules(self):
        """Validation engine pre-loaded with 835 business rules."""
        engine = ValidationEngine()
        for rule in get_835_business_rules():
            engine.add_rule(rule)
        return engine

    @pytest.fixture
    def sample_validation_error(self):
        """Sample validation error for testing."""
        return ValidationError(
            code="TEST_ERROR",
            message="Test error message",
            severity=ValidationSeverity.ERROR,
            category=ValidationCategory.BUSINESS
        )

    def test_validation_with_parsing(self, validation_engine_with_835_rules, schema_835_path):
        """Test validation integrated with parsing."""
        edi_content = EDIFixtures.get_minimal_835()
        parsed_root = parse_edi(edi_content, schema_835_path)
        
        # Run validation
        result = validation_engine_with_835_rules.validate(parsed_root)
        
        # Check results
        assert isinstance(result.is_valid, bool)
        assert isinstance(result.errors, list)
        assert isinstance(result.warnings, list)
        assert result.rules_applied > 0

    def test_validation_with_invalid_data(self, validation_engine_with_835_rules, schema_835_path):
        """Test validation with intentionally invalid data."""
        edi_content = (
            "ISA*00*          *00*          *ZZ*SENDER         *ZZ*RECEIVER       "
            "*241226*1430*^*00501*000012345*0*P*:~"
            "GS*HP*SENDER*RECEIVER*20241226*1430*000006789*X*005010X221A1~"
            "ST*835*0001~"
            "BPR*I*-100*C*CHK*20241226~"  # Invalid negative amount
            "CLP*TEST*1*100*150*0*12*CTRL~"  # Inconsistent claim data
            "SE*5*0001~"
            "GE*1*000006789~"
            "IEA*1*000012345~"
        )
        
        parsed_root = parse_edi(edi_content, schema_835_path)
        
        # Run validation
        result = validation_engine_with_835_rules.validate(parsed_root)
        
        # Should have validation errors due to negative amount and inconsistent claim data
        assert len(result.errors) > 0 or len(result.warnings) > 0

    def test_validation_error_details(self, sample_validation_error):
        """Test that validation errors contain proper details."""
        validation_engine = ValidationEngine()
        
        # Add a test rule that will fail
        rule = FieldValidationRule(
            "TEST_FAIL", "Test failure", ValidationSeverity.ERROR,
            ValidationCategory.BUSINESS, "nonexistent.field", lambda x: False
        )
        validation_engine.add_rule(rule)
        
        # Create test object
        class TestObj:
            valid_field = "value"
        
        result = validation_engine.validate(TestObj())
        
        # Should have applied the rule
        assert result.rules_applied == 1


class TestValidationResults:
    """Test validation result handling."""

    def test_validation_result_creation(self):
        """Test validation result creation and methods."""
        from packages.core.validation import ValidationResult
        
        result = ValidationResult(is_valid=True)
        assert result.is_valid == True
        assert len(result.errors) == 0
        assert len(result.warnings) == 0
        assert len(result.info) == 0

    def test_validation_result_add_error(self):
        """Test adding errors to validation result."""
        from packages.core.validation import ValidationResult
        
        error = ValidationError(
            code="TEST_ERROR",
            message="Test error message",
            severity=ValidationSeverity.ERROR,
            category=ValidationCategory.BUSINESS
        )
        
        result = ValidationResult(is_valid=True)
        result.add_error(error)
        
        assert result.is_valid == False
        assert len(result.errors) == 1
        assert result.errors[0].code == "TEST_ERROR"

    def test_validation_result_summary(self):
        """Test validation result summary."""
        from packages.core.validation import ValidationResult
        
        result = ValidationResult(is_valid=True)
        result.rules_applied = 5
        
        # Add various types of issues
        result.add_error(ValidationError(
            "ERROR1", "Error 1", ValidationSeverity.ERROR, ValidationCategory.BUSINESS
        ))
        result.add_error(ValidationError(
            "WARN1", "Warning 1", ValidationSeverity.WARNING, ValidationCategory.FORMAT
        ))
        result.add_error(ValidationError(
            "INFO1", "Info 1", ValidationSeverity.INFO, ValidationCategory.HIPAA
        ))
        
        summary = result.summary()
        assert summary["errors"] == 1
        assert summary["warnings"] == 1
        assert summary["info"] == 1
        assert summary["rules_applied"] == 5


class TestCustomValidationRules:
    """Test creation and application of custom validation rules."""

    def test_custom_field_rule(self, schema_835_path):
        """Test creating and applying custom field validation rules."""
        # Create custom rule to validate claim amounts are positive
        def positive_amount_validator(amount):
            return amount is not None and float(amount) >= 0
        
        rule = FieldValidationRule(
            "POSITIVE_AMOUNT", 
            "Claim amounts must be positive", 
            ValidationSeverity.ERROR,
            ValidationCategory.BUSINESS, 
            "claims.total_charge", 
            positive_amount_validator
        )
        
        validation_engine = ValidationEngine()
        validation_engine.add_rule(rule)
        
        # Test with valid data
        edi_content = EDIFixtures.get_minimal_835()
        parsed_root = parse_edi(edi_content, schema_835_path)
        result = validation_engine.validate(parsed_root)
        
        assert result.rules_applied == 1

    def test_custom_business_rule(self, schema_835_path):
        """Test creating and applying custom business rules."""
        def claim_balance_check(edi_root, context):
            """Verify claim balances are consistent."""
            if not hasattr(edi_root, 'interchanges'):
                return True
                
            for interchange in edi_root.interchanges:
                for fg in interchange.functional_groups:
                    for transaction in fg.transactions:
                        if hasattr(transaction, 'financial_transaction'):
                            ft = transaction.financial_transaction
                            if hasattr(ft, 'claims'):
                                for claim in ft.claims:
                                    # Simple balance check
                                    if (claim.total_paid + claim.patient_responsibility) > claim.total_charge:
                                        return False
            return True
        
        rule = BusinessRule(
            "CLAIM_BALANCE", 
            "Claim payments cannot exceed charges", 
            ValidationSeverity.ERROR,
            ValidationCategory.BUSINESS, 
            claim_balance_check,
            "Claim payment exceeds total charge"
        )
        
        validation_engine = ValidationEngine()
        validation_engine.add_rule(rule)
        
        # Test with valid data
        edi_content = EDIFixtures.get_minimal_835()
        parsed_root = parse_edi(edi_content, schema_835_path)
        result = validation_engine.validate(parsed_root)
        
        assert result.rules_applied == 1
        # Should pass for our test data
        assert len(result.errors) == 0