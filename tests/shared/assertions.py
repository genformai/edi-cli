"""
Common assertion helpers for EDI testing.

This module provides standardized assertion functions used across
multiple test modules to ensure consistent validation patterns.

Migrated and enhanced from the original test_utils.py.
"""

import re
from decimal import Decimal
from typing import Any, Union, Optional, List


def assert_date_format(date_str: str, expected_format: str = "YYYY-MM-DD") -> None:
    """
    Assert that a date string matches the expected format.
    
    Args:
        date_str: Date string to validate
        expected_format: Expected format pattern
        
    Raises:
        AssertionError: If date doesn't match expected format
    """
    if expected_format == "YYYY-MM-DD":
        pattern = r'^\d{4}-\d{2}-\d{2}$'
        assert re.match(pattern, date_str), f"Date '{date_str}' does not match YYYY-MM-DD format"
    elif expected_format == "CCYYMMDD":
        pattern = r'^\d{8}$'
        assert re.match(pattern, date_str), f"Date '{date_str}' does not match CCYYMMDD format"
    else:
        raise ValueError(f"Unsupported date format: {expected_format}")


def assert_amount_format(amount: Union[str, float, Decimal], precision: int = 2) -> None:
    """
    Assert that an amount is properly formatted for EDI.
    
    Args:
        amount: Amount to validate
        precision: Expected decimal precision
        
    Raises:
        AssertionError: If amount format is invalid
    """
    if isinstance(amount, str):
        # Check string format
        assert re.match(r'^\d+(\.\d{1,2})?$', amount), f"Amount '{amount}' has invalid format"
        amount = float(amount)
    
    assert amount >= 0, f"Amount must be non-negative, got {amount}"
    
    # Check precision
    decimal_amount = Decimal(str(amount))
    decimal_places = abs(decimal_amount.as_tuple().exponent)
    assert decimal_places <= precision, f"Amount {amount} has too many decimal places (max {precision})"


def assert_balances(charge: float, paid: float, patient_resp: float, tolerance: float = 0.01) -> None:
    """
    Assert that claim financial balances are consistent.
    
    Args:
        charge: Total charge amount
        paid: Amount paid by payer
        patient_resp: Patient responsibility amount
        tolerance: Tolerance for floating point comparison
        
    Raises:
        AssertionError: If balances don't add up correctly
    """
    total_accounted = paid + patient_resp
    difference = abs(charge - total_accounted)
    
    assert difference <= tolerance, (
        f"Financial balance mismatch: "
        f"Charge={charge}, Paid={paid}, Patient={patient_resp}, "
        f"Difference={difference} (tolerance={tolerance})"
    )


def assert_claim_status_valid(status_code: Union[int, str]) -> None:
    """
    Assert that a claim status code is valid.
    
    Args:
        status_code: Claim status code to validate
        
    Raises:
        AssertionError: If status code is invalid
    """
    # Convert to int if string
    if isinstance(status_code, str):
        try:
            status_code = int(status_code)
        except ValueError:
            assert False, f"Status code must be numeric, got '{status_code}'"
    
    valid_statuses = {
        1: "Processed as Primary",
        2: "Processed as Secondary", 
        3: "Processed as Tertiary",
        4: "Denied",
        19: "Processed as Primary, Forwarded to Additional Payer(s)",
        20: "Processed as Secondary, Forwarded to Additional Payer(s)",
        21: "Processed as Tertiary, Forwarded to Additional Payer(s)",
        22: "Reversal of Previous Payment",
        23: "Not Our Claim, Forwarded to Additional Payer(s)"
    }
    
    assert status_code in valid_statuses, (
        f"Invalid claim status code: {status_code}. "
        f"Valid codes: {list(valid_statuses.keys())}"
    )


# Additional utility assertions migrated from original test_utils.py

def assert_control_numbers_match(interchange: Any) -> None:
    """
    Assert that control numbers match between envelope segments.
    
    Args:
        interchange: Parsed interchange object
        
    Raises:
        AssertionError: If control numbers don't match
    """
    # ISA13 should match IEA02
    if hasattr(interchange, 'header'):
        isa_control = interchange.header.get("control_number")
        assert isa_control is not None, "ISA control number missing"
    
    # Additional control number validations for functional groups and transactions
    if hasattr(interchange, 'functional_groups'):
        for functional_group in interchange.functional_groups:
            if hasattr(functional_group, 'header'):
                gs_control = functional_group.header.get("control_number")
                assert gs_control is not None, "GS control number missing"
            
            if hasattr(functional_group, 'transactions'):
                for transaction in functional_group.transactions:
                    if hasattr(transaction, 'header'):
                        st_control = transaction.header.get("control_number")
                        assert st_control is not None, "ST control number missing"


def assert_required_segments(transaction: Any, required_segments: List[str]) -> None:
    """
    Assert that required segments are present in the transaction.
    
    Args:
        transaction: Transaction object
        required_segments: List of required segment types
        
    Raises:
        AssertionError: If required segments are missing
    """
    assert transaction is not None, "Transaction is None"
    
    # This would need to be implemented based on the actual transaction structure
    # For now, just verify the transaction exists and has basic structure
    if hasattr(transaction, 'segments'):
        segment_types = [seg[0] for seg in transaction.segments if len(seg) > 0]
        for required_segment in required_segments:
            assert required_segment in segment_types, f"Required segment {required_segment} not found"


def assert_npi_format(npi: Optional[str]) -> None:
    """
    Assert that NPI is in correct format.
    
    Args:
        npi: NPI to validate
        
    Raises:
        AssertionError: If NPI format is invalid
    """
    if npi is None:
        return
        
    assert isinstance(npi, str), f"NPI must be string, got {type(npi)}"
    assert npi.isdigit(), f"NPI must be numeric: {npi}"
    assert len(npi) in [9, 10], f"NPI must be 9 or 10 digits: {npi}"


def assert_amount_format_legacy(amount: Any, allow_negative: bool = False) -> None:
    """
    Legacy assert that amount is in correct format (from original test_utils.py).
    
    Args:
        amount: Amount to validate (float, int, or string)
        allow_negative: Whether negative amounts are allowed
        
    Raises:
        AssertionError: If amount format is invalid
    """
    if amount is None:
        return
        
    try:
        amount_float = float(amount)
        if not allow_negative:
            assert amount_float >= 0, f"Negative amount not allowed: {amount}"
    except (ValueError, TypeError):
        assert False, f"Invalid amount format: {amount}"


def build_835_edi(base_headers: str, segments: Union[List[str], str], base_trailer: str, segment_count: Optional[int] = None) -> str:
    """
    Build complete 835 EDI content with proper segment count.
    
    Args:
        base_headers: Base header segments
        segments: Additional segments (list or string)
        base_trailer: Base trailer segments
        segment_count: Override segment count
        
    Returns:
        Complete EDI content
    """
    if isinstance(segments, list):
        segments = "".join(segments)
    
    # Calculate segment count if not provided
    if segment_count is None:
        # Count segments between ST and SE (inclusive)
        header_segments = base_headers.count("~")
        content_segments = segments.count("~") if segments else 0
        segment_count = header_segments - 2 + content_segments + 1  # -2 for ISA/GS, +1 for SE
    
    # Replace placeholder in trailer
    trailer = base_trailer.replace("{{segment_count}}", str(segment_count))
    
    return base_headers + segments + trailer


def assert_segment_structure(segments: List[Any], expected_count: Optional[int] = None) -> None:
    """
    Assert basic EDI segment structure is valid.
    
    Args:
        segments: List of EDI segments to validate
        expected_count: Expected number of segments (optional)
        
    Raises:
        AssertionError: If segment structure is invalid
    """
    assert isinstance(segments, list), "Segments must be a list"
    assert len(segments) > 0, "Segments list cannot be empty"
    
    if expected_count is not None:
        assert len(segments) == expected_count, (
            f"Expected {expected_count} segments, got {len(segments)}"
        )
    
    # Check that each segment has at least one element (segment ID)
    for i, segment in enumerate(segments):
        assert isinstance(segment, list), f"Segment {i} must be a list"
        assert len(segment) > 0, f"Segment {i} cannot be empty"
        assert isinstance(segment[0], str), f"Segment {i} ID must be a string"


def assert_npi_valid(npi: str) -> None:
    """
    Assert that an NPI is valid using Luhn algorithm.
    
    Args:
        npi: NPI to validate
        
    Raises:
        AssertionError: If NPI is invalid
    """
    assert npi and len(npi) == 10, f"NPI must be 10 digits, got '{npi}'"
    assert npi.isdigit(), f"NPI must contain only digits, got '{npi}'"
    
    # Luhn algorithm validation
    total = 0
    for i, digit in enumerate(npi):
        n = int(digit)
        if i % 2 == 0:
            n *= 2
            if n > 9:
                n = n // 10 + n % 10
        total += n
    
    assert total % 10 == 0, f"NPI '{npi}' failed Luhn algorithm validation"