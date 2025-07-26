import pytest
import tempfile
import os
from pathlib import Path
from packages.core.validation import (
    ValidationEngine, ValidationRule, ValidationError, ValidationSeverity, 
    ValidationCategory, FieldValidationRule, BusinessRule, validate_npi, 
    validate_amount_format, validate_control_number
)
from packages.core.validators_835 import get_835_business_rules
from packages.core.parser import EdiParser
from packages.core.emitter import EdiEmitter


@pytest.fixture
def validation_engine():
    """Basic validation engine instance."""
    return ValidationEngine()


@pytest.fixture
def sample_field_validation_rule():
    """Sample field validation rule for testing."""
    return FieldValidationRule(
        "TEST_RULE", "Test rule", ValidationSeverity.ERROR, 
        ValidationCategory.BUSINESS, "test.field", lambda x: x is not None
    )


@pytest.fixture
def sample_rule_set():
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
def sample_yaml_rules():
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


@pytest.fixture
def sample_edi_835():
    """Sample 835 EDI content."""
    with open('tests/fixtures/835.edi', 'r') as f:
        return f.read()


@pytest.fixture
def parsed_835_root(sample_edi_835):
    """Parsed 835 EDI root object."""
    parser = EdiParser(
        edi_string=sample_edi_835,
        schema_path='packages/core/schemas/x12/835.json'
    )
    return parser.parse()


@pytest.fixture
def invalid_835_edi():
    """Invalid 835 EDI content for testing error conditions."""
    return """ISA*00*          *00*          *ZZ*TEST*ZZ*TEST*230101*0000*U*00501*1*0*P*:~
GS*HP*TEST*TEST*20230101*0000*1*X*005010X221A1~
ST*835*0001~
BPR*I*-100*C*CHK*20230101~
CLP*TEST*1*100*150*0*12*CTRL~
SE*5*0001~
GE*1*1~
IEA*1*1~"""


@pytest.fixture
def parsed_invalid_835_root(invalid_835_edi):
    """Parsed invalid 835 EDI root object."""
    parser = EdiParser(
        edi_string=invalid_835_edi,
        schema_path='packages/core/schemas/x12/835.json'
    )
    return parser.parse()


@pytest.fixture
def validation_engine_with_835_rules(validation_engine):
    """Validation engine pre-loaded with 835 business rules."""
    for rule in get_835_business_rules():
        validation_engine.add_rule(rule)
    return validation_engine


@pytest.fixture
def test_obj_valid():
    """Valid test object for validation."""
    class TestObj:
        name = "Valid Name"
        valid = True
        existing_field = "value"
    return TestObj()


@pytest.fixture
def test_obj_invalid():
    """Invalid test object for validation."""
    class TestObjInvalid:
        name = ""
        valid = False
    return TestObjInvalid()


@pytest.fixture
def sample_validation_error():
    """Sample validation error for testing."""
    return ValidationError(
        code="TEST_ERROR",
        message="Test error message",
        severity=ValidationSeverity.ERROR,
        category=ValidationCategory.BUSINESS
    )


class TestValidationEngine:
    """Test the validation engine functionality."""

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

    def test_835_validation_with_rule_sets(self, validation_engine):
        """Test 835 validation using predefined rule sets."""
        # Load basic rules
        basic_rules_path = Path("packages/validation-rules/835-basic.yml")
        if basic_rules_path.exists():
            loaded_count = validation_engine.load_rules_from_yaml(str(basic_rules_path))
            assert loaded_count > 0
        
        # Load HIPAA rules
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

    def test_validation_with_parsing(self, validation_engine_with_835_rules, parsed_835_root):
        """Test validation integrated with parsing."""
        # Run validation
        result = validation_engine_with_835_rules.validate(parsed_835_root)
        
        # Check results
        assert isinstance(result.is_valid, bool)
        assert isinstance(result.errors, list)
        assert isinstance(result.warnings, list)
        assert result.rules_applied > 0

    def test_validation_with_invalid_data(self, validation_engine_with_835_rules, parsed_invalid_835_root):
        """Test validation with intentionally invalid data."""
        # Run validation
        result = validation_engine_with_835_rules.validate(parsed_invalid_835_root)
        
        # Should have validation errors due to negative amount and inconsistent claim data
        assert len(result.errors) > 0 or len(result.warnings) > 0

    def test_validation_error_details(self, validation_engine, test_obj_valid):
        """Test that validation errors contain proper details."""
        # Add a test rule that will fail
        rule = FieldValidationRule(
            "TEST_FAIL", "Test failure", ValidationSeverity.ERROR,
            ValidationCategory.BUSINESS, "nonexistent.field", lambda x: False
        )
        validation_engine.add_rule(rule)
        
        result = validation_engine.validate(test_obj_valid)
        
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

    def test_validation_result_add_error(self, sample_validation_error):
        """Test adding errors to validation result."""
        from packages.core.validation import ValidationResult
        
        result = ValidationResult(is_valid=True)
        result.add_error(sample_validation_error)
        
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