"""
Common validation utilities for EDI processing.

This module provides standardized validation functions that are used
across multiple EDI transaction parsers and validation rules.
"""

import re
from datetime import datetime
from decimal import Decimal, InvalidOperation
from typing import Union, Optional, List
import logging

logger = logging.getLogger(__name__)


def validate_npi(npi: str) -> bool:
    """
    Validate National Provider Identifier (NPI) using Luhn algorithm.
    
    Args:
        npi: NPI string to validate
        
    Returns:
        True if NPI is valid, False otherwise
        
    Examples:
        >>> validate_npi("1234567893")  # Valid NPI
        True
        >>> validate_npi("1234567890")  # Invalid NPI
        False
        >>> validate_npi("123")  # Wrong length
        False
    """
    if not npi or not isinstance(npi, str):
        return False
    
    # Remove any spaces or formatting
    npi = npi.strip().replace(" ", "").replace("-", "")
    
    # NPI must be exactly 10 digits
    if len(npi) != 10 or not npi.isdigit():
        return False
    
    # Apply Luhn algorithm
    try:
        total = 0
        for i, digit in enumerate(npi):
            n = int(digit)
            # Double every second digit from right (odd positions in 0-indexed)
            if i % 2 == 0:
                n *= 2
                # If doubling results in two digits, add them together
                if n > 9:
                    n = n // 10 + n % 10
            total += n
        
        # Valid if total is divisible by 10
        return total % 10 == 0
    except (ValueError, TypeError):
        return False


def validate_amount_format(amount: Union[str, float, int, Decimal]) -> bool:
    """
    Validate that an amount is in proper format for EDI.
    
    Args:
        amount: Amount to validate
        
    Returns:
        True if amount is valid, False otherwise
        
    Examples:
        >>> validate_amount_format("123.45")
        True
        >>> validate_amount_format("123")
        True
        >>> validate_amount_format("abc")
        False
        >>> validate_amount_format("")
        False
    """
    if amount is None:
        return False
    
    # Handle different input types
    if isinstance(amount, (int, float)):
        return amount >= 0
    
    if isinstance(amount, Decimal):
        return amount >= 0
    
    if isinstance(amount, str):
        amount = amount.strip()
        if not amount:
            return False
        
        # Check for valid decimal format
        if not re.match(r'^\d+(\.\d{1,2})?$', amount):
            return False
        
        try:
            value = float(amount)
            return value >= 0
        except (ValueError, TypeError):
            return False
    
    return False


def validate_date_format(date_str: str, format_str: str = "%Y-%m-%d") -> bool:
    """
    Validate date string against a specific format.
    
    Args:
        date_str: Date string to validate
        format_str: Expected date format (default: YYYY-MM-DD)
        
    Returns:
        True if date is valid, False otherwise
        
    Examples:
        >>> validate_date_format("2024-12-26")
        True
        >>> validate_date_format("2024-13-26")  # Invalid month
        False
        >>> validate_date_format("20241226", "%Y%m%d")
        True
    """
    if not date_str or not isinstance(date_str, str):
        return False
    
    try:
        datetime.strptime(date_str.strip(), format_str)
        return True
    except (ValueError, TypeError):
        return False


def validate_control_number(control_num: str) -> bool:
    """
    Validate EDI control number format.
    
    Args:
        control_num: Control number to validate
        
    Returns:
        True if control number is valid, False otherwise
        
    Examples:
        >>> validate_control_number("123456789")
        True
        >>> validate_control_number("0001")
        True
        >>> validate_control_number("")
        False
        >>> validate_control_number("abc123")
        False
    """
    if not control_num or not isinstance(control_num, str):
        return False
    
    control_num = control_num.strip()
    
    # Control number should be 1-9 digits
    return bool(control_num and control_num.isdigit() and 1 <= len(control_num) <= 9)


def validate_transaction_code(transaction_code: str, valid_codes: Optional[List[str]] = None) -> bool:
    """
    Validate EDI transaction set identifier code.
    
    Args:
        transaction_code: Transaction code to validate
        valid_codes: List of valid codes (if None, uses common EDI codes)
        
    Returns:
        True if transaction code is valid, False otherwise
        
    Examples:
        >>> validate_transaction_code("835")
        True
        >>> validate_transaction_code("999")
        False
    """
    if not transaction_code or not isinstance(transaction_code, str):
        return False
    
    if valid_codes is None:
        # Common X12 transaction codes
        valid_codes = [
            "270", "271",  # Eligibility Inquiry/Response
            "276", "277",  # Claim Status Inquiry/Response
            "835",         # Electronic Remittance Advice
            "837",         # Healthcare Claim
            "820",         # Payment Order/Remittance Advice
            "834",         # Benefit Enrollment and Maintenance
            "999",         # Implementation Acknowledgment
            "997"          # Functional Acknowledgment
        ]
    
    return transaction_code.strip() in valid_codes


def validate_ein(ein: str) -> bool:
    """
    Validate Employer Identification Number (EIN) format.
    
    Args:
        ein: EIN to validate
        
    Returns:
        True if EIN format is valid, False otherwise
        
    Examples:
        >>> validate_ein("12-3456789")
        True
        >>> validate_ein("123456789")
        True
        >>> validate_ein("12-345678")  # Too short
        False
    """
    if not ein or not isinstance(ein, str):
        return False
    
    ein = ein.strip().replace("-", "").replace(" ", "")
    
    # EIN should be exactly 9 digits
    return len(ein) == 9 and ein.isdigit()


def validate_phone_number(phone: str) -> bool:
    """
    Validate phone number format for EDI.
    
    Args:
        phone: Phone number to validate
        
    Returns:
        True if phone number format is valid, False otherwise
        
    Examples:
        >>> validate_phone_number("5551234567")
        True
        >>> validate_phone_number("555-123-4567")
        True
        >>> validate_phone_number("123")  # Too short
        False
    """
    if not phone or not isinstance(phone, str):
        return False
    
    # Remove common formatting characters
    cleaned = re.sub(r'[^\d]', '', phone.strip())
    
    # Should be 10 digits (US format)
    return len(cleaned) == 10 and cleaned.isdigit()


def validate_zip_code(zip_code: str) -> bool:
    """
    Validate ZIP code format.
    
    Args:
        zip_code: ZIP code to validate
        
    Returns:
        True if ZIP code format is valid, False otherwise
        
    Examples:
        >>> validate_zip_code("12345")
        True
        >>> validate_zip_code("12345-6789")
        True
        >>> validate_zip_code("1234")  # Too short
        False
    """
    if not zip_code or not isinstance(zip_code, str):
        return False
    
    zip_code = zip_code.strip()
    
    # 5-digit ZIP or 5+4 ZIP format
    return bool(re.match(r'^\d{5}(-\d{4})?$', zip_code))


def validate_state_code(state_code: str) -> bool:
    """
    Validate US state code.
    
    Args:
        state_code: State code to validate
        
    Returns:
        True if state code is valid, False otherwise
        
    Examples:
        >>> validate_state_code("CA")
        True
        >>> validate_state_code("XX")
        False
    """
    if not state_code or not isinstance(state_code, str):
        return False
    
    # Standard US state codes
    valid_states = {
        "AL", "AK", "AZ", "AR", "CA", "CO", "CT", "DE", "FL", "GA",
        "HI", "ID", "IL", "IN", "IA", "KS", "KY", "LA", "ME", "MD",
        "MA", "MI", "MN", "MS", "MO", "MT", "NE", "NV", "NH", "NJ",
        "NM", "NY", "NC", "ND", "OH", "OK", "OR", "PA", "RI", "SC",
        "SD", "TN", "TX", "UT", "VT", "VA", "WA", "WV", "WI", "WY",
        "DC"  # District of Columbia
    }
    
    return state_code.strip().upper() in valid_states


def validate_currency_code(currency_code: str) -> bool:
    """
    Validate currency code format (ISO 4217).
    
    Args:
        currency_code: Currency code to validate
        
    Returns:
        True if currency code is valid, False otherwise
        
    Examples:
        >>> validate_currency_code("USD")
        True
        >>> validate_currency_code("EUR")
        True
        >>> validate_currency_code("XYZ")
        False
    """
    if not currency_code or not isinstance(currency_code, str):
        return False
    
    # Common currency codes for healthcare EDI
    valid_currencies = {
        "USD",  # US Dollar
        "CAD",  # Canadian Dollar
        "EUR",  # Euro
        "GBP",  # British Pound
        "JPY",  # Japanese Yen
        "AUD",  # Australian Dollar
        "CHF",  # Swiss Franc
        "CNY",  # Chinese Yuan
        "MXN"   # Mexican Peso
    }
    
    return currency_code.strip().upper() in valid_currencies


def validate_adjustment_reason_code(reason_code: str, group_code: str = None) -> bool:
    """
    Validate adjustment reason code format and value.
    
    Args:
        reason_code: Reason code to validate
        group_code: Optional group code context (CO, PR, OA, PI)
        
    Returns:
        True if reason code is valid, False otherwise
        
    Examples:
        >>> validate_adjustment_reason_code("45", "CO")
        True
        >>> validate_adjustment_reason_code("999", "CO")
        False
    """
    if not reason_code or not isinstance(reason_code, str):
        return False
    
    reason_code = reason_code.strip()
    
    # Reason codes are typically 1-3 digit numbers
    if not reason_code.isdigit() or len(reason_code) > 3:
        return False
    
    code_num = int(reason_code)
    
    # Basic range validation (1-999)
    if not (1 <= code_num <= 999):
        return False
    
    # Additional validation based on group code
    if group_code:
        group_code = group_code.strip().upper()
        
        # Common valid ranges by group
        group_ranges = {
            "CO": range(1, 300),    # Contractual Obligation
            "PR": range(1, 50),     # Patient Responsibility  
            "OA": range(1, 200),    # Other Adjustments
            "PI": range(1, 100)     # Payer Initiated
        }
        
        if group_code in group_ranges:
            return code_num in group_ranges[group_code]
    
    return True


def validate_decimal_precision(value: Union[str, float, Decimal], max_precision: int = 2) -> bool:
    """
    Validate that a decimal value doesn't exceed maximum precision.
    
    Args:
        value: Value to validate
        max_precision: Maximum decimal places allowed
        
    Returns:
        True if precision is valid, False otherwise
        
    Examples:
        >>> validate_decimal_precision("123.45", 2)
        True
        >>> validate_decimal_precision("123.456", 2)
        False
    """
    if value is None:
        return False
    
    try:
        if isinstance(value, str):
            if not value.strip():
                return False
            decimal_val = Decimal(value.strip())
        elif isinstance(value, (int, float)):
            decimal_val = Decimal(str(value))
        elif isinstance(value, Decimal):
            decimal_val = value
        else:
            return False
        
        # Check decimal places
        if decimal_val % 1 == 0:  # No decimal places
            return True
        
        # Count decimal places
        decimal_str = str(decimal_val)
        if '.' in decimal_str:
            decimal_places = len(decimal_str.split('.')[1])
            return decimal_places <= max_precision
        
        return True
        
    except (InvalidOperation, ValueError, TypeError):
        return False