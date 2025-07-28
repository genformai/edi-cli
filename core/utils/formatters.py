"""
Date and time formatting utilities for EDI parsing.

This module provides standardized date and time formatting functions
that are used across multiple EDI transaction parsers.
"""

import re
from typing import Optional


def format_edi_date(date_str: str, input_format: str = "CCYYMMDD") -> str:
    """
    Format EDI date strings to YYYY-MM-DD format.
    
    Args:
        date_str: Date string to format
        input_format: Input format ("CCYYMMDD", "YYMMDD", "MMDDYY", "MMDDCCYY")
        
    Returns:
        Formatted date string in YYYY-MM-DD format, or original string if invalid
        
    Examples:
        >>> format_edi_date("20241226", "CCYYMMDD")
        "2024-12-26"
        >>> format_edi_date("241226", "YYMMDD")
        "2024-12-26"
    """
    if not date_str or not date_str.strip():
        return date_str
    
    date_str = date_str.strip()
    
    # CCYYMMDD format (8 digits: 20241226)
    if input_format == "CCYYMMDD" and len(date_str) == 8 and date_str.isdigit():
        return f"{date_str[0:4]}-{date_str[4:6]}-{date_str[6:8]}"
    
    # YYMMDD format (6 digits: 241226, assumes 20xx century)
    elif input_format == "YYMMDD" and len(date_str) == 6 and date_str.isdigit():
        year = int(date_str[0:2])
        # Use sliding window: 00-29 = 20xx, 30-99 = 19xx
        century = "20" if year <= 29 else "19"
        return f"{century}{date_str[0:2]}-{date_str[2:4]}-{date_str[4:6]}"
    
    # MMDDYY format (6 digits: 122624)
    elif input_format == "MMDDYY" and len(date_str) == 6 and date_str.isdigit():
        year = int(date_str[4:6])
        century = "20" if year <= 29 else "19"
        return f"{century}{date_str[4:6]}-{date_str[0:2]}-{date_str[2:4]}"
    
    # MMDDCCYY format (8 digits: 12262024)
    elif input_format == "MMDDCCYY" and len(date_str) == 8 and date_str.isdigit():
        return f"{date_str[4:8]}-{date_str[0:2]}-{date_str[2:4]}"
    
    # Return original if format doesn't match
    return date_str


def format_edi_time(time_str: str, input_format: str = "HHMM") -> str:
    """
    Format EDI time strings to HH:MM format.
    
    Args:
        time_str: Time string to format
        input_format: Input format ("HHMM", "HHMMSS")
        
    Returns:
        Formatted time string in HH:MM format, or original string if invalid
        
    Examples:
        >>> format_edi_time("1430", "HHMM")
        "14:30"
        >>> format_edi_time("143045", "HHMMSS")
        "14:30:45"
    """
    if not time_str or not time_str.strip():
        return time_str
    
    time_str = time_str.strip()
    
    # HHMM format (4 digits: 1430)
    if input_format == "HHMM" and len(time_str) == 4 and time_str.isdigit():
        return f"{time_str[0:2]}:{time_str[2:4]}"
    
    # HHMMSS format (6 digits: 143045)
    elif input_format == "HHMMSS" and len(time_str) == 6 and time_str.isdigit():
        return f"{time_str[0:2]}:{time_str[2:4]}:{time_str[4:6]}"
    
    # Return original if format doesn't match
    return time_str


def format_date_ccyymmdd(date_str: str) -> str:
    """
    Legacy compatibility function for CCYYMMDD format.
    
    Args:
        date_str: Date string in CCYYMMDD format
        
    Returns:
        Formatted date string in YYYY-MM-DD format
        
    Note:
        This function is provided for backward compatibility.
        Use format_edi_date() for new code.
    """
    return format_edi_date(date_str, "CCYYMMDD")


def format_date_yymmdd(date_str: str) -> str:
    """
    Legacy compatibility function for YYMMDD format.
    
    Args:
        date_str: Date string in YYMMDD format
        
    Returns:
        Formatted date string in YYYY-MM-DD format
        
    Note:
        This function is provided for backward compatibility.
        Use format_edi_date() for new code.
    """
    return format_edi_date(date_str, "YYMMDD")


def validate_edi_date_format(date_str: str, input_format: str = "CCYYMMDD") -> bool:
    """
    Validate that a date string matches the expected EDI format.
    
    Args:
        date_str: Date string to validate
        input_format: Expected input format
        
    Returns:
        True if date string matches format, False otherwise
    """
    if not date_str or not date_str.strip():
        return False
    
    date_str = date_str.strip()
    
    format_patterns = {
        "CCYYMMDD": (8, r"^\d{8}$"),
        "YYMMDD": (6, r"^\d{6}$"),
        "MMDDYY": (6, r"^\d{6}$"),
        "MMDDCCYY": (8, r"^\d{8}$"),
        "HHMM": (4, r"^\d{4}$"),
        "HHMMSS": (6, r"^\d{6}$")
    }
    
    if input_format not in format_patterns:
        return False
    
    expected_length, pattern = format_patterns[input_format]
    
    return len(date_str) == expected_length and bool(re.match(pattern, date_str))


# Legacy function aliases for backward compatibility
_format_ccyymmdd = format_date_ccyymmdd
_format_yymmdd = format_date_yymmdd
_format_time = lambda time_str: format_edi_time(time_str, "HHMM")