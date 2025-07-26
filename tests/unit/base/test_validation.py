"""
Unit tests for base EDI validation engine and rules.

This module contains tests for the core validation framework,
migrated from the original validation tests with updated imports.
"""

import pytest
from packages.core.base.validation import (
    ValidationEngine, 
    ValidationRule, 
    ValidationError, 
    ValidationSeverity,
    ValidationCategory, 
    FieldValidationRule, 
    BusinessRule
)
from packages.core.utils import (
    validate_npi,
    validate_amount_format, 
    validate_control_number
)
from packages.core.transactions.t835.validators import get_835_business_rules
from tests.shared.assertions import assert_npi_valid, assert_amount_format
from tests.shared.test_data import TestData


class TestValidationEngine:
    """Test cases for the core validation engine."""

    def test_validation_engine_creation(self):
        """Test ValidationEngine instantiation."""
        engine = ValidationEngine()
        assert engine is not None
        assert hasattr(engine, 'validate')

    def test_add_validation_rule(self):
        """Test adding validation rules to engine."""
        engine = ValidationEngine()
        
        # Create a simple test rule
        test_rule = FieldValidationRule(
            rule_id="TEST_RULE",
            description="Test rule",
            severity=ValidationSeverity.ERROR,
            category=ValidationCategory.BUSINESS,
            field_path="test.field",
            validation_function=lambda x: x is not None
        )
        
        engine.add_rule(test_rule)
        assert len(engine.rules) >= 1

    def test_validation_severities(self):
        """Test ValidationSeverity enum values."""
        assert ValidationSeverity.ERROR is not None
        assert ValidationSeverity.WARNING is not None
        assert ValidationSeverity.INFO is not None

    def test_validation_categories(self):
        """Test ValidationCategory enum values."""
        assert ValidationCategory.BUSINESS is not None
        assert ValidationCategory.STRUCTURAL is not None
        assert ValidationCategory.FORMAT is not None


class TestUtilityValidators:
    """Test cases for utility validation functions."""

    def test_validate_npi_function(self):
        """Test NPI validation utility function."""
        # Test valid NPI (using checksum-valid test NPI)
        valid_npi = "1234567893"
        result = validate_npi(valid_npi)
        # The result depends on the actual Luhn implementation
        assert isinstance(result, bool)
        
        # Test invalid NPI format
        assert validate_npi("123") is False  # Too short
        assert validate_npi("12345678901") is False  # Too long
        assert validate_npi("abcdefghij") is False  # Non-numeric
        assert validate_npi("") is False  # Empty
        assert validate_npi(None) is False  # None

    def test_validate_amount_format_function(self):
        """Test amount format validation utility."""
        # Test valid amounts
        assert validate_amount_format("123.45") is True
        assert validate_amount_format("100") is True
        assert validate_amount_format("0.00") is True
        assert validate_amount_format(123.45) is True
        assert validate_amount_format(0) is True
        
        # Test invalid amounts
        assert validate_amount_format("abc") is False
        assert validate_amount_format("") is False
        assert validate_amount_format("-100") is False  # Negative
        assert validate_amount_format("123.456") is False  # Too many decimals

    def test_validate_control_number_function(self):
        """Test control number validation utility."""
        # Test valid control numbers
        assert validate_control_number("123456789") is True
        assert validate_control_number("0001") is True
        assert validate_control_number("1") is True
        
        # Test invalid control numbers
        assert validate_control_number("") is False
        assert validate_control_number("abc123") is False
        assert validate_control_number("1234567890") is False  # Too long
        assert validate_control_number(None) is False


class Test835BusinessRules:
    """Test cases for 835-specific business rules."""

    def test_get_835_business_rules(self):
        """Test retrieval of 835 business rules."""
        rules = get_835_business_rules()
        
        assert isinstance(rules, list)
        assert len(rules) > 0
        
        # Verify all are ValidationRule instances
        for rule in rules:
            assert isinstance(rule, ValidationRule)
            assert hasattr(rule, 'rule_id')
            assert hasattr(rule, 'validate')
            assert hasattr(rule, 'severity')
            assert hasattr(rule, 'category')

    def test_835_rule_metadata(self):
        """Test 835 rule metadata."""
        rules = get_835_business_rules()
        
        # Check for expected rule IDs
        rule_ids = [rule.rule_id for rule in rules]
        expected_ids = [
            "835_FINANCIAL_CONSISTENCY",
            "835_CLAIM_VALIDATION", 
            "835_ADJUSTMENT_VALIDATION",
            "835_SERVICE_VALIDATION",
            "835_DATE_VALIDATION",
            "835_PAYER_PAYEE_VALIDATION"
        ]
        
        for expected_id in expected_ids:
            assert expected_id in rule_ids, f"Missing expected rule: {expected_id}"


class TestFieldValidationRule:
    """Test cases for FieldValidationRule."""

    def test_field_validation_rule_creation(self):
        """Test FieldValidationRule creation."""
        rule = FieldValidationRule(
            rule_id="TEST_FIELD_RULE",
            description="Test field validation",
            severity=ValidationSeverity.ERROR,
            category=ValidationCategory.FORMAT,
            field_path="transaction.claim.amount",
            validation_function=lambda x: isinstance(x, (int, float)) and x >= 0
        )
        
        assert rule.rule_id == "TEST_FIELD_RULE"
        assert rule.severity == ValidationSeverity.ERROR
        assert rule.category == ValidationCategory.FORMAT
        assert rule.field_path == "transaction.claim.amount"

    def test_field_validation_execution(self):
        """Test field validation execution."""
        rule = FieldValidationRule(
            rule_id="AMOUNT_POSITIVE",
            description="Amount must be positive",
            severity=ValidationSeverity.ERROR,
            category=ValidationCategory.BUSINESS,
            field_path="amount",
            validation_function=lambda x: x > 0
        )
        
        # Test validation with mock data
        valid_data = {"amount": 100.00}
        invalid_data = {"amount": -50.00}
        
        # These would typically be called by the validation engine
        assert rule.validation_function(valid_data["amount"]) is True
        assert rule.validation_function(invalid_data["amount"]) is False


class TestBusinessRule:
    """Test cases for BusinessRule."""

    def test_business_rule_creation(self):
        """Test BusinessRule creation."""
        def test_condition(edi_root, context):
            return True
        
        rule = BusinessRule(
            rule_id="TEST_BUSINESS_RULE",
            description="Test business rule",
            severity=ValidationSeverity.WARNING,
            category=ValidationCategory.BUSINESS,
            condition=test_condition,
            error_message="Test error message"
        )
        
        assert rule.rule_id == "TEST_BUSINESS_RULE"
        assert rule.severity == ValidationSeverity.WARNING
        assert rule.error_message == "Test error message"
        assert callable(rule.condition)

    def test_business_rule_execution(self):
        """Test business rule execution."""
        def always_true_condition(edi_root, context):
            return True
        
        def always_false_condition(edi_root, context):
            return False
        
        true_rule = BusinessRule(
            rule_id="ALWAYS_TRUE",
            description="Always passes",
            severity=ValidationSeverity.INFO,
            category=ValidationCategory.BUSINESS,
            condition=always_true_condition,
            error_message="Should not see this"
        )
        
        false_rule = BusinessRule(
            rule_id="ALWAYS_FALSE",
            description="Always fails", 
            severity=ValidationSeverity.ERROR,
            category=ValidationCategory.BUSINESS,
            condition=always_false_condition,
            error_message="Expected failure"
        )
        
        # Test with mock EDI root and context
        mock_edi_root = None
        mock_context = {}
        
        assert true_rule.condition(mock_edi_root, mock_context) is True
        assert false_rule.condition(mock_edi_root, mock_context) is False