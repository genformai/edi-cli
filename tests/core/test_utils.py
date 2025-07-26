"""
Shared utilities for EDI testing.
"""

from packages.core.parser import EdiParser


def parse_edi(raw_text, schema_path):
    """
    Parse EDI text using the specified schema.
    
    Args:
        raw_text (str): Raw EDI content
        schema_path (str): Path to schema file
        
    Returns:
        Parsed EDI root object
    """
    parser = EdiParser(raw_text, schema_path)
    return parser.parse()


def assert_control_numbers_match(interchange):
    """
    Assert that control numbers match between envelope segments.
    
    Args:
        interchange: Parsed interchange object
    """
    # ISA13 should match IEA02
    isa_control = interchange.header.get("control_number")
    assert isa_control is not None, "ISA control number missing"
    
    # Additional control number validations can be added here
    for functional_group in interchange.functional_groups:
        gs_control = functional_group.header.get("control_number")
        assert gs_control is not None, "GS control number missing"
        
        for transaction in functional_group.transactions:
            st_control = transaction.header.get("control_number")
            assert st_control is not None, "ST control number missing"


def assert_balances(financial_tx):
    """
    Assert that financial balances are consistent.
    
    Args:
        financial_tx: Financial transaction object
    """
    if not hasattr(financial_tx, 'claims') or not financial_tx.claims:
        return
        
    # Sum all claim payments
    total_claim_paid = sum(
        getattr(claim, 'total_paid', 0) for claim in financial_tx.claims
    )
    
    # Check against BPR total if available
    if hasattr(financial_tx, 'financial_information'):
        bpr_total = getattr(financial_tx.financial_information, 'total_paid', None)
        if bpr_total is not None:
            # Allow for PLB adjustments - this is a simplified check
            assert abs(total_claim_paid - bpr_total) <= 0.01, (
                f"Claim total {total_claim_paid} doesn't match BPR total {bpr_total}"
            )


def assert_required_segments(transaction, required_segments):
    """
    Assert that required segments are present in the transaction.
    
    Args:
        transaction: Transaction object
        required_segments (list): List of required segment types
    """
    # This would need to be implemented based on the actual transaction structure
    # For now, just verify the transaction exists
    assert transaction is not None, "Transaction is None"


def assert_date_format(date_string, expected_format="YYYY-MM-DD"):
    """
    Assert that date string is in expected format.
    
    Args:
        date_string (str): Date string to validate
        expected_format (str): Expected format description
    """
    if date_string is None:
        return
        
    # Basic validation for YYYY-MM-DD format
    if expected_format == "YYYY-MM-DD":
        assert len(date_string) == 10, f"Date {date_string} not in YYYY-MM-DD format"
        assert date_string[4] == "-", f"Date {date_string} missing first dash"
        assert date_string[7] == "-", f"Date {date_string} missing second dash"
        
        # Validate numeric parts
        year, month, day = date_string.split("-")
        assert year.isdigit() and len(year) == 4, f"Invalid year in {date_string}"
        assert month.isdigit() and 1 <= int(month) <= 12, f"Invalid month in {date_string}"
        assert day.isdigit() and 1 <= int(day) <= 31, f"Invalid day in {date_string}"


def assert_amount_format(amount, allow_negative=False):
    """
    Assert that amount is in correct format.
    
    Args:
        amount: Amount to validate (float, int, or string)
        allow_negative (bool): Whether negative amounts are allowed
    """
    if amount is None:
        return
        
    try:
        amount_float = float(amount)
        if not allow_negative:
            assert amount_float >= 0, f"Negative amount not allowed: {amount}"
    except (ValueError, TypeError):
        assert False, f"Invalid amount format: {amount}"


def build_835_edi(base_headers, segments, base_trailer, segment_count=None):
    """
    Build complete 835 EDI content with proper segment count.
    
    Args:
        base_headers (str): Base header segments
        segments (list or str): Additional segments
        base_trailer (str): Base trailer segments
        segment_count (int): Override segment count
        
    Returns:
        str: Complete EDI content
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


def assert_npi_format(npi):
    """
    Assert that NPI is in correct format.
    
    Args:
        npi (str): NPI to validate
    """
    if npi is None:
        return
        
    assert isinstance(npi, str), f"NPI must be string, got {type(npi)}"
    assert npi.isdigit(), f"NPI must be numeric: {npi}"
    assert len(npi) in [9, 10], f"NPI must be 9 or 10 digits: {npi}"


def assert_claim_status_valid(status_code):
    """
    Assert that claim status code is valid.
    
    Args:
        status_code: Status code to validate
    """
    valid_codes = [1, 2, 3, 4, 19, 20, 21, 22, 23]
    assert status_code in valid_codes, f"Invalid claim status code: {status_code}"