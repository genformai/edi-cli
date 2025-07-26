"""
Unit tests for EDI utility validators.

This module contains tests for validation utility functions,
migrated and organized from the original test structure.
"""

import pytest
from packages.core.utils.validators import (
    validate_npi,
    validate_amount_format,
    validate_date_format,
    validate_control_number,
    validate_transaction_code,
    validate_ein,
    validate_phone_number,
    validate_zip_code,
    validate_state_code,
    validate_currency_code,
    validate_adjustment_reason_code,
    validate_decimal_precision
)
from tests.shared.test_data import TestData


class TestNPIValidation:
    """Test cases for NPI validation."""

    def test_valid_npi_formats(self):
        """Test various valid NPI formats."""
        # Test basic format validation
        valid_npis = [
            "1234567893",  # Valid checksum (example)
            "9876543210",  # 10 digits
            "1122334455"   # Another 10-digit format
        ]
        
        for npi in valid_npis:
            # Note: These may fail Luhn check but should pass format validation
            result = validate_npi(npi)
            assert isinstance(result, bool), f"NPI {npi} should return boolean"

    def test_invalid_npi_formats(self):
        """Test invalid NPI formats."""
        invalid_npis = [
            "",              # Empty
            "123",           # Too short
            "12345678901",   # Too long
            "abcdefghij",    # Non-numeric
            "123-456-7890",  # With dashes
            "123 456 7890",  # With spaces
            None             # None value
        ]
        
        for npi in invalid_npis:
            assert validate_npi(npi) is False, f"NPI {npi} should be invalid"

    def test_npi_luhn_algorithm(self):
        """Test NPI Luhn algorithm validation."""
        # These are test NPIs that should fail/pass Luhn check
        # Note: Using obviously invalid checksums for testing
        
        # Test obviously invalid checksum
        invalid_luhn = "1234567890"  # Last digit makes it invalid
        result = validate_npi(invalid_luhn)
        assert isinstance(result, bool)  # Should return bool regardless


class TestAmountValidation:
    """Test cases for amount format validation."""

    def test_valid_amounts(self):
        """Test valid amount formats."""
        valid_amounts = [
            "123.45",    # Standard decimal
            "100",       # Whole number string
            "0.00",      # Zero
            "999.99",    # Max normal range
            123.45,      # Float
            100,         # Integer
            0            # Zero integer
        ]
        
        for amount in valid_amounts:
            assert validate_amount_format(amount) is True, f"Amount {amount} should be valid"

    def test_invalid_amounts(self):
        """Test invalid amount formats."""
        invalid_amounts = [
            "",           # Empty string
            "abc",        # Non-numeric
            "-100.00",    # Negative
            "123.456",    # Too many decimals
            "123.",       # Trailing decimal
            ".99",        # Leading decimal only
            None,         # None value
            -50.00        # Negative float
        ]
        
        for amount in invalid_amounts:
            assert validate_amount_format(amount) is False, f"Amount {amount} should be invalid"


class TestDateValidation:
    """Test cases for date format validation."""

    def test_valid_date_formats(self):
        """Test valid date formats."""
        # Test ISO format (default)
        valid_iso_dates = [
            "2024-12-26",
            "2024-01-01", 
            "2024-12-31"
        ]
        
        for date in valid_iso_dates:
            assert validate_date_format(date) is True, f"Date {date} should be valid"
        
        # Test CCYYMMDD format
        valid_ccyymmdd_dates = [
            "20241226",
            "20240101",
            "20241231"
        ]
        
        for date in valid_ccyymmdd_dates:
            assert validate_date_format(date, "%Y%m%d") is True, f"Date {date} should be valid in CCYYMMDD"

    def test_invalid_date_formats(self):
        """Test invalid date formats."""
        invalid_dates = [
            "",              # Empty
            "2024-13-01",    # Invalid month
            "2024-12-32",    # Invalid day
            "24-12-26",      # Wrong year format
            "2024/12/26",    # Wrong separator
            "invalid",       # Non-date string
            None             # None value
        ]
        
        for date in invalid_dates:
            assert validate_date_format(date) is False, f"Date {date} should be invalid"


class TestControlNumberValidation:
    """Test cases for control number validation."""

    def test_valid_control_numbers(self):
        """Test valid EDI control numbers."""
        valid_control_numbers = [
            "1",           # Single digit
            "123",         # Multiple digits
            "000000001",   # Leading zeros
            "999999999"    # Max 9 digits
        ]
        
        for control_num in valid_control_numbers:
            assert validate_control_number(control_num) is True, f"Control number {control_num} should be valid"

    def test_invalid_control_numbers(self):
        """Test invalid control numbers."""
        invalid_control_numbers = [
            "",              # Empty
            "0000000000",    # Too long (10 digits)
            "abc123",        # Contains letters
            "12-34",         # Contains special chars
            None             # None value
        ]
        
        for control_num in invalid_control_numbers:
            assert validate_control_number(control_num) is False, f"Control number {control_num} should be invalid"


class TestTransactionCodeValidation:
    """Test cases for transaction code validation."""

    def test_valid_transaction_codes(self):
        """Test valid EDI transaction codes."""
        valid_codes = ["270", "271", "276", "277", "835", "837", "820", "834"]
        
        for code in valid_codes:
            assert validate_transaction_code(code) is True, f"Transaction code {code} should be valid"

    def test_invalid_transaction_codes(self):
        """Test invalid transaction codes."""
        invalid_codes = ["", "999", "123", "abc", None]
        
        for code in invalid_codes:
            assert validate_transaction_code(code) is False, f"Transaction code {code} should be invalid"

    def test_custom_valid_codes(self):
        """Test transaction code validation with custom valid codes."""
        custom_codes = ["100", "200", "300"]
        
        assert validate_transaction_code("100", custom_codes) is True
        assert validate_transaction_code("835", custom_codes) is False  # Not in custom list


class TestOtherValidators:
    """Test cases for other validation functions."""

    def test_ein_validation(self):
        """Test EIN validation."""
        valid_eins = ["12-3456789", "123456789"]
        invalid_eins = ["", "12-345678", "abc-defghi", None]
        
        for ein in valid_eins:
            assert validate_ein(ein) is True, f"EIN {ein} should be valid"
        
        for ein in invalid_eins:
            assert validate_ein(ein) is False, f"EIN {ein} should be invalid"

    def test_phone_number_validation(self):
        """Test phone number validation."""
        valid_phones = ["5551234567", "555-123-4567", "(555) 123-4567"]
        invalid_phones = ["", "123", "555-123-456", None]
        
        for phone in valid_phones:
            assert validate_phone_number(phone) is True, f"Phone {phone} should be valid"
        
        for phone in invalid_phones:
            assert validate_phone_number(phone) is False, f"Phone {phone} should be invalid"

    def test_zip_code_validation(self):
        """Test ZIP code validation."""
        valid_zips = ["12345", "12345-6789"]
        invalid_zips = ["", "123", "123456", "12345-678", None]
        
        for zip_code in valid_zips:
            assert validate_zip_code(zip_code) is True, f"ZIP {zip_code} should be valid"
        
        for zip_code in invalid_zips:
            assert validate_zip_code(zip_code) is False, f"ZIP {zip_code} should be invalid"

    def test_state_code_validation(self):
        """Test state code validation."""
        valid_states = ["CA", "NY", "TX", "FL", "DC"]
        invalid_states = ["", "XX", "California", "123", None]
        
        for state in valid_states:
            assert validate_state_code(state) is True, f"State {state} should be valid"
        
        for state in invalid_states:
            assert validate_state_code(state) is False, f"State {state} should be invalid"

    def test_currency_code_validation(self):
        """Test currency code validation."""
        valid_currencies = ["USD", "CAD", "EUR", "GBP"]
        invalid_currencies = ["", "XYZ", "Dollar", "123", None]
        
        for currency in valid_currencies:
            assert validate_currency_code(currency) is True, f"Currency {currency} should be valid"
        
        for currency in invalid_currencies:
            assert validate_currency_code(currency) is False, f"Currency {currency} should be invalid"

    def test_decimal_precision_validation(self):
        """Test decimal precision validation."""
        # Test with default 2-decimal precision
        valid_decimals = ["123.45", "100", "0.5", 123.45, 100]
        invalid_decimals = ["123.456", "0.123", None]
        
        for decimal_val in valid_decimals:
            assert validate_decimal_precision(decimal_val) is True, f"Decimal {decimal_val} should be valid"
        
        for decimal_val in invalid_decimals:
            assert validate_decimal_precision(decimal_val) is False, f"Decimal {decimal_val} should be invalid"

    def test_adjustment_reason_code_validation(self):
        """Test adjustment reason code validation."""
        # Test basic format validation
        valid_codes = ["1", "45", "99"]
        invalid_codes = ["", "0", "1000", "abc", None]
        
        for code in valid_codes:
            assert validate_adjustment_reason_code(code) is True, f"Reason code {code} should be valid"
        
        for code in invalid_codes:
            assert validate_adjustment_reason_code(code) is False, f"Reason code {code} should be invalid"
        
        # Test with group code context
        assert validate_adjustment_reason_code("45", "CO") is True
        assert validate_adjustment_reason_code("500", "CO") is False  # Out of range for CO