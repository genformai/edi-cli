"""
Unit tests for EDI utility formatters.

This module contains tests for date and time formatting utility functions.
"""

import pytest
from packages.core.utils.formatters import (
    format_edi_date,
    format_edi_time,
    format_date_ccyymmdd,
    format_date_yymmdd,
    validate_edi_date_format
)


class TestEDIDateFormatting:
    """Test cases for EDI date formatting functions."""

    def test_format_edi_date_ccyymmdd(self):
        """Test formatting CCYYMMDD dates."""
        # Valid CCYYMMDD format
        assert format_edi_date("20241226", "CCYYMMDD") == "2024-12-26"
        assert format_edi_date("20240101", "CCYYMMDD") == "2024-01-01"
        assert format_edi_date("20241231", "CCYYMMDD") == "2024-12-31"

    def test_format_edi_date_yymmdd(self):
        """Test formatting YYMMDD dates."""
        # Valid YYMMDD format (assumes 20xx century for <= 29, 19xx for >= 30)
        assert format_edi_date("241226", "YYMMDD") == "2024-12-26"
        assert format_edi_date("001231", "YYMMDD") == "2000-12-31"
        assert format_edi_date("291231", "YYMMDD") == "2029-12-31"
        assert format_edi_date("301231", "YYMMDD") == "1930-12-31"
        assert format_edi_date("991231", "YYMMDD") == "1999-12-31"

    def test_format_edi_date_mmddyy(self):
        """Test formatting MMDDYY dates.""" 
        assert format_edi_date("122624", "MMDDYY") == "2024-12-26"
        assert format_edi_date("010100", "MMDDYY") == "2000-01-01"
        assert format_edi_date("123129", "MMDDYY") == "2029-12-31"
        assert format_edi_date("123130", "MMDDYY") == "1930-12-31"

    def test_format_edi_date_mmddccyy(self):
        """Test formatting MMDDCCYY dates."""
        assert format_edi_date("12262024", "MMDDCCYY") == "2024-12-26"
        assert format_edi_date("01011999", "MMDDCCYY") == "1999-01-01"
        assert format_edi_date("12312025", "MMDDCCYY") == "2025-12-31"

    def test_format_edi_date_invalid_input(self):
        """Test formatting with invalid date inputs."""
        # Invalid length
        assert format_edi_date("2024", "CCYYMMDD") == "2024"  # Returns original
        assert format_edi_date("24122", "YYMMDD") == "24122"  # Returns original
        
        # Non-numeric
        assert format_edi_date("ABCDABCD", "CCYYMMDD") == "ABCDABCD"
        assert format_edi_date("AB1226", "YYMMDD") == "AB1226"
        
        # Empty or None
        assert format_edi_date("", "CCYYMMDD") == ""
        assert format_edi_date("   ", "CCYYMMDD") == "   "

    def test_format_edi_date_default_format(self):
        """Test formatting with default CCYYMMDD format."""
        assert format_edi_date("20241226") == "2024-12-26"  # Default format
        assert format_edi_date("invalid") == "invalid"  # Returns original if invalid


class TestEDITimeFormatting:
    """Test cases for EDI time formatting functions."""

    def test_format_edi_time_hhmm(self):
        """Test formatting HHMM time."""
        assert format_edi_time("1430", "HHMM") == "14:30"
        assert format_edi_time("0900", "HHMM") == "09:00"
        assert format_edi_time("2359", "HHMM") == "23:59"
        assert format_edi_time("0000", "HHMM") == "00:00"

    def test_format_edi_time_hhmmss(self):
        """Test formatting HHMMSS time."""
        assert format_edi_time("143045", "HHMMSS") == "14:30:45"
        assert format_edi_time("090000", "HHMMSS") == "09:00:00"
        assert format_edi_time("235959", "HHMMSS") == "23:59:59"
        assert format_edi_time("000000", "HHMMSS") == "00:00:00"

    def test_format_edi_time_invalid_input(self):
        """Test formatting with invalid time inputs."""
        # Invalid length
        assert format_edi_time("143", "HHMM") == "143"  # Returns original
        assert format_edi_time("14304", "HHMMSS") == "14304"  # Returns original
        
        # Non-numeric
        assert format_edi_time("AB30", "HHMM") == "AB30"
        assert format_edi_time("14AB45", "HHMMSS") == "14AB45"
        
        # Empty
        assert format_edi_time("", "HHMM") == ""
        assert format_edi_time("   ", "HHMM") == "   "

    def test_format_edi_time_default_format(self):
        """Test formatting with default HHMM format."""
        assert format_edi_time("1430") == "14:30"  # Default format


class TestLegacyFormatFunctions:
    """Test cases for legacy format compatibility functions."""

    def test_format_date_ccyymmdd_legacy(self):
        """Test legacy CCYYMMDD format function."""
        assert format_date_ccyymmdd("20241226") == "2024-12-26"
        assert format_date_ccyymmdd("invalid") == "invalid"

    def test_format_date_yymmdd_legacy(self):
        """Test legacy YYMMDD format function."""
        assert format_date_yymmdd("241226") == "2024-12-26"
        assert format_date_yymmdd("301226") == "1930-12-26"  # 30+ assumes 19xx
        assert format_date_yymmdd("invalid") == "invalid"


class TestDateFormatValidation:
    """Test cases for date format validation."""

    def test_validate_edi_date_format_ccyymmdd(self):
        """Test CCYYMMDD format validation."""
        assert validate_edi_date_format("20241226", "CCYYMMDD") is True
        assert validate_edi_date_format("20240101", "CCYYMMDD") is True
        
        # Invalid formats
        assert validate_edi_date_format("2024126", "CCYYMMDD") is False  # Wrong length
        assert validate_edi_date_format("ABCDABCD", "CCYYMMDD") is False  # Non-numeric
        assert validate_edi_date_format("", "CCYYMMDD") is False  # Empty

    def test_validate_edi_date_format_yymmdd(self):
        """Test YYMMDD format validation."""
        assert validate_edi_date_format("241226", "YYMMDD") is True
        assert validate_edi_date_format("000101", "YYMMDD") is True
        
        # Invalid formats
        assert validate_edi_date_format("24126", "YYMMDD") is False  # Wrong length
        assert validate_edi_date_format("AB1226", "YYMMDD") is False  # Non-numeric

    def test_validate_edi_date_format_time(self):
        """Test time format validation."""
        assert validate_edi_date_format("1430", "HHMM") is True
        assert validate_edi_date_format("143045", "HHMMSS") is True
        
        # Invalid formats
        assert validate_edi_date_format("143", "HHMM") is False  # Wrong length
        assert validate_edi_date_format("AB30", "HHMM") is False  # Non-numeric

    def test_validate_edi_date_format_unknown(self):
        """Test validation with unknown format."""
        assert validate_edi_date_format("20241226", "UNKNOWN") is False


class TestEdgeCases:
    """Test cases for edge cases and boundary conditions."""

    def test_year_boundary_conditions(self):
        """Test year boundary conditions for YYMMDD format."""
        # Test boundary years (29/30 cutoff)
        assert format_edi_date("291231", "YYMMDD") == "2029-12-31"  # 29 -> 20xx
        assert format_edi_date("301231", "YYMMDD") == "1930-12-31"  # 30 -> 19xx
        
        # Test extreme years
        assert format_edi_date("001231", "YYMMDD") == "2000-12-31"  # 00 -> 2000
        assert format_edi_date("991231", "YYMMDD") == "1999-12-31"  # 99 -> 1999

    def test_leap_year_dates(self):
        """Test formatting with leap year dates."""
        # Leap year date
        assert format_edi_date("20240229", "CCYYMMDD") == "2024-02-29"
        assert format_edi_date("240229", "YYMMDD") == "2024-02-29"
        
        # Format validation should pass for leap year
        assert validate_edi_date_format("20240229", "CCYYMMDD") is True
        assert validate_edi_date_format("240229", "YYMMDD") is True

    def test_whitespace_handling(self):
        """Test handling of whitespace in inputs."""
        # Leading/trailing whitespace
        assert format_edi_date("  20241226  ", "CCYYMMDD") == "2024-12-26"
        assert format_edi_time("  1430  ", "HHMM") == "14:30"
        
        # Whitespace-only strings
        assert format_edi_date("        ", "CCYYMMDD") == "        "
        assert format_edi_time("    ", "HHMM") == "    "

    def test_none_input_handling(self):
        """Test handling of None inputs."""
        # Note: These depend on actual implementation
        # The functions should handle None gracefully
        try:
            result = format_edi_date(None, "CCYYMMDD")
            assert result is None or result == ""
        except (TypeError, AttributeError):
            # Some implementations might raise exceptions for None
            pass
        
        try:
            result = format_edi_time(None, "HHMM")
            assert result is None or result == ""
        except (TypeError, AttributeError):
            pass