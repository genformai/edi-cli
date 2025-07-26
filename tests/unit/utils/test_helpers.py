"""
Unit tests for EDI utility helpers.

This module contains tests for parsing helper utility functions.
"""

import pytest
from packages.core.utils.helpers import (
    get_element,
    safe_float,
    safe_int,
    parse_segment_header,
    find_segments,
    find_segment,
    split_edi_string,
    split_segment_elements,
    parse_edi_segments,
    extract_amount,
    is_empty_or_zero,
    normalize_identifier
)


class TestGetElement:
    """Test cases for get_element function."""

    def test_valid_element_access(self):
        """Test accessing valid elements from segments."""
        segment = ["ST", "835", "0001", "additional"]
        
        assert get_element(segment, 0) == "ST"
        assert get_element(segment, 1) == "835"
        assert get_element(segment, 2) == "0001"
        assert get_element(segment, 3) == "additional"

    def test_out_of_bounds_access(self):
        """Test accessing elements beyond segment length."""
        segment = ["ST", "835"]
        
        assert get_element(segment, 5) == ""  # Default empty string
        assert get_element(segment, 10, "DEFAULT") == "DEFAULT"  # Custom default

    def test_negative_index_access(self):
        """Test accessing with negative indices."""
        segment = ["ST", "835", "0001"]
        
        assert get_element(segment, -1) == ""  # Should return default

    def test_empty_segment(self):
        """Test accessing elements from empty segment."""
        empty_segment = []
        
        assert get_element(empty_segment, 0) == ""
        assert get_element(empty_segment, 0, "EMPTY") == "EMPTY"

    def test_whitespace_trimming(self):
        """Test that elements are trimmed of whitespace."""
        segment = ["  ST  ", " 835 ", "0001   "]
        
        assert get_element(segment, 0) == "ST"
        assert get_element(segment, 1) == "835"
        assert get_element(segment, 2) == "0001"


class TestSafeConversions:
    """Test cases for safe type conversion functions."""

    def test_safe_float_valid_conversions(self):
        """Test safe_float with valid inputs."""
        assert safe_float("123.45") == 123.45
        assert safe_float("100") == 100.0
        assert safe_float("0") == 0.0
        assert safe_float(123.45) == 123.45
        assert safe_float(100) == 100.0

    def test_safe_float_invalid_conversions(self):
        """Test safe_float with invalid inputs."""
        assert safe_float("invalid") == 0.0  # Default
        assert safe_float("") == 0.0
        assert safe_float(None) == 0.0
        assert safe_float("abc", 99.9) == 99.9  # Custom default

    def test_safe_int_valid_conversions(self):
        """Test safe_int with valid inputs."""
        assert safe_int("123") == 123
        assert safe_int("0") == 0
        assert safe_int(123) == 123
        assert safe_int(123.99) == 123  # Truncates decimal
        assert safe_int("123.0") == 123  # Handles float strings

    def test_safe_int_invalid_conversions(self):
        """Test safe_int with invalid inputs."""
        assert safe_int("invalid") == 0  # Default
        assert safe_int("") == 0
        assert safe_int(None) == 0
        assert safe_int("abc", -1) == -1  # Custom default


class TestSegmentParsing:
    """Test cases for segment parsing functions."""

    def test_parse_segment_header_st(self):
        """Test parsing ST segment header."""
        st_segment = ["ST", "835", "0001"]
        result = parse_segment_header(st_segment)
        
        assert result["segment_id"] == "ST"
        assert result["transaction_set_identifier"] == "835"
        assert result["control_number"] == "0001"

    def test_parse_segment_header_gs(self):
        """Test parsing GS segment header."""
        gs_segment = ["GS", "HP", "SENDER", "RECEIVER", "20241226", "1430", "000000001"]
        result = parse_segment_header(gs_segment)
        
        assert result["segment_id"] == "GS"
        assert result["functional_group_code"] == "HP"
        assert result["sender_id"] == "SENDER"
        assert result["receiver_id"] == "RECEIVER"
        assert result["date"] == "20241226"
        assert result["time"] == "1430"
        assert result["control_number"] == "000000001"

    def test_parse_segment_header_isa(self):
        """Test parsing ISA segment header."""
        isa_segment = ["ISA", "00", "", "00", "", "ZZ", "SENDER", "ZZ", "RECEIVER", "241226", "1430", "U", "00501", "000000001"]
        result = parse_segment_header(isa_segment)
        
        assert result["segment_id"] == "ISA"
        assert result["sender_id"] == "SENDER"
        assert result["receiver_id"] == "RECEIVER"

    def test_parse_segment_header_empty(self):
        """Test parsing empty segment."""
        result = parse_segment_header([])
        
        assert result["segment_id"] == ""
        assert "error" in result

    def test_find_segments(self):
        """Test finding segments by segment ID."""
        segments = [
            ["ISA", "..."],
            ["GS", "..."],
            ["ST", "835", "0001"],
            ["CLP", "CLAIM001"],
            ["CLP", "CLAIM002"],
            ["SE", "..."]
        ]
        
        clp_segments = find_segments(segments, "CLP")
        assert len(clp_segments) == 2
        assert clp_segments[0][1] == "CLAIM001"
        assert clp_segments[1][1] == "CLAIM002"
        
        # Test segment not found
        missing_segments = find_segments(segments, "NOTFOUND")
        assert len(missing_segments) == 0

    def test_find_segment(self):
        """Test finding first segment by segment ID."""
        segments = [
            ["ISA", "..."],
            ["GS", "..."],
            ["ST", "835", "0001"],
            ["CLP", "CLAIM001"],
            ["CLP", "CLAIM002"]
        ]
        
        st_segment = find_segment(segments, "ST")
        assert st_segment is not None
        assert st_segment[1] == "835"
        
        # Test segment not found
        missing_segment = find_segment(segments, "NOTFOUND")
        assert missing_segment is None


class TestEDIStringParsing:
    """Test cases for EDI string parsing functions."""

    def test_split_edi_string(self):
        """Test splitting EDI string into segments."""
        edi_string = "ST*835*0001~BPR*I*1000.00~SE*3*0001~"
        segments = split_edi_string(edi_string)
        
        expected_segments = ["ST*835*0001", "BPR*I*1000.00", "SE*3*0001"]
        assert segments == expected_segments

    def test_split_edi_string_empty(self):
        """Test splitting empty EDI string."""
        assert split_edi_string("") == []
        assert split_edi_string(None) == []

    def test_split_segment_elements(self):
        """Test splitting segment string into elements."""
        segment_string = "ST*835*0001"
        elements = split_segment_elements(segment_string)
        
        expected_elements = ["ST", "835", "0001"]
        assert elements == expected_elements

    def test_split_segment_elements_empty(self):
        """Test splitting empty segment string."""
        assert split_segment_elements("") == []

    def test_parse_edi_segments(self):
        """Test complete EDI string parsing into segments."""
        edi_string = "ST*835*0001~BPR*I*1000.00~"
        segments = parse_edi_segments(edi_string)
        
        expected_segments = [
            ["ST", "835", "0001"],
            ["BPR", "I", "1000.00"]
        ]
        assert segments == expected_segments


class TestUtilityFunctions:
    """Test cases for utility helper functions."""

    def test_extract_amount(self):
        """Test extracting monetary amounts from strings."""
        assert extract_amount("123.45") == 123.45
        assert extract_amount("100") == 100.0
        assert extract_amount("$123.45") == 123.45  # Should strip non-numeric
        assert extract_amount("") == 0.0  # Default
        assert extract_amount("invalid", 99.9) == 99.9  # Custom default

    def test_is_empty_or_zero(self):
        """Test checking for empty or zero values."""
        # Empty values
        assert is_empty_or_zero("") is True
        assert is_empty_or_zero(None) is True
        assert is_empty_or_zero("   ") is True  # Whitespace only
        
        # Zero values
        assert is_empty_or_zero("0") is True
        assert is_empty_or_zero("0.00") is True
        assert is_empty_or_zero(0) is True
        assert is_empty_or_zero(0.0) is True
        
        # Non-empty, non-zero values
        assert is_empty_or_zero("123.45") is False
        assert is_empty_or_zero("1") is False
        assert is_empty_or_zero(123.45) is False

    def test_normalize_identifier(self):
        """Test normalizing identifiers."""
        assert normalize_identifier("  claim001  ") == "CLAIM001"
        assert normalize_identifier("Test_ID") == "TEST_ID"
        assert normalize_identifier("lowercase") == "LOWERCASE"
        assert normalize_identifier("") == ""
        assert normalize_identifier(None) == ""