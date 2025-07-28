"""
Common parsing helper utilities for EDI processing.

This module provides utility functions for segment navigation,
type conversion, and common parsing operations used across
multiple EDI transaction parsers.
"""

from typing import List, Dict, Any, Optional, Union
import logging

logger = logging.getLogger(__name__)


def get_element(segment: List[str], index: int, default: str = "") -> str:
    """
    Safely get an element from a segment.
    
    Args:
        segment: The segment to extract from (list of elements)
        index: The element index (0-based)
        default: Default value if element doesn't exist
        
    Returns:
        The element value (stripped of whitespace) or default
        
    Examples:
        >>> segment = ["CLP", "CLAIM001", "1", "100.00", "80.00"]
        >>> get_element(segment, 1)
        "CLAIM001"
        >>> get_element(segment, 10, "N/A")
        "N/A"
    """
    if segment and len(segment) > index and index >= 0:
        element = segment[index]
        return element.strip() if isinstance(element, str) else str(element).strip()
    return default


def safe_float(value: Union[str, float, int], default: float = 0.0) -> float:
    """
    Safely convert a value to float.
    
    Args:
        value: Value to convert (string, float, or int)
        default: Default value if conversion fails
        
    Returns:
        Float value or default
        
    Examples:
        >>> safe_float("123.45")
        123.45
        >>> safe_float("invalid", 0.0)
        0.0
        >>> safe_float("")
        0.0
    """
    if value is None:
        return default
    
    # If already a number, return as float
    if isinstance(value, (int, float)):
        return float(value)
    
    # Handle string conversion
    if isinstance(value, str):
        value = value.strip()
        if not value:
            return default
        
        try:
            return float(value)
        except (ValueError, TypeError):
            return default
    
    # Fallback for other types
    try:
        return float(value)
    except (ValueError, TypeError):
        return default


def safe_int(value: Union[str, int, float], default: int = 0) -> int:
    """
    Safely convert a value to integer.
    
    Args:
        value: Value to convert (string, int, or float)
        default: Default value if conversion fails
        
    Returns:
        Integer value or default
        
    Examples:
        >>> safe_int("123")
        123
        >>> safe_int("123.99")  # Truncates decimal
        123
        >>> safe_int("invalid", -1)
        -1
    """
    if value is None:
        return default
    
    # If already an integer, return it
    if isinstance(value, int):
        return value
    
    # If float, convert to int (truncate decimal)
    if isinstance(value, float):
        return int(value)
    
    # Handle string conversion
    if isinstance(value, str):
        value = value.strip()
        if not value:
            return default
        
        try:
            # Try direct int conversion first
            return int(value)
        except ValueError:
            try:
                # Try float conversion then int (handles "123.0")
                return int(float(value))
            except (ValueError, TypeError):
                return default
    
    # Fallback for other types
    try:
        return int(value)
    except (ValueError, TypeError):
        return default


def parse_segment_header(segment: List[str]) -> Dict[str, str]:
    """
    Parse common header information from any segment.
    
    Args:
        segment: Segment to parse (first element should be segment ID)
        
    Returns:
        Dictionary with segment information
        
    Examples:
        >>> parse_segment_header(["ST", "835", "0001"])
        {"segment_id": "ST", "transaction_set_identifier": "835", "control_number": "0001"}
    """
    if not segment or len(segment) == 0:
        return {"segment_id": "", "error": "Empty segment"}
    
    segment_id = get_element(segment, 0)
    result = {"segment_id": segment_id}
    
    # Parse common segment types
    if segment_id == "ST":
        result.update({
            "transaction_set_identifier": get_element(segment, 1),
            "control_number": get_element(segment, 2)
        })
    elif segment_id == "SE":
        result.update({
            "segment_count": get_element(segment, 1),
            "control_number": get_element(segment, 2)
        })
    elif segment_id == "GS":
        result.update({
            "functional_group_code": get_element(segment, 1),
            "sender_id": get_element(segment, 2),
            "receiver_id": get_element(segment, 3),
            "date": get_element(segment, 4),
            "time": get_element(segment, 5),
            "control_number": get_element(segment, 6)
        })
    elif segment_id == "GE":
        result.update({
            "group_count": get_element(segment, 1),
            "control_number": get_element(segment, 2)
        })
    elif segment_id == "ISA":
        result.update({
            "sender_id": get_element(segment, 6),
            "receiver_id": get_element(segment, 8),
            "date": get_element(segment, 9),
            "time": get_element(segment, 10),
            "control_number": get_element(segment, 13)
        })
    elif segment_id == "IEA":
        result.update({
            "group_count": get_element(segment, 1),
            "control_number": get_element(segment, 2)
        })
    
    return result


def find_segments(segments: List[List[str]], segment_id: str) -> List[List[str]]:
    """
    Find all segments with a specific segment ID.
    
    Args:
        segments: List of all segments
        segment_id: Segment ID to search for (e.g., "CLP", "BPR")
        
    Returns:
        List of matching segments
        
    Examples:
        >>> segments = [["ST", "835", "0001"], ["BPR", "I", "100.00"], ["CLP", "CLAIM001"]]
        >>> find_segments(segments, "CLP")
        [["CLP", "CLAIM001"]]
    """
    return [segment for segment in segments if segment and get_element(segment, 0) == segment_id]


def find_segment(segments: List[List[str]], segment_id: str) -> Optional[List[str]]:
    """
    Find the first segment with a specific segment ID.
    
    Args:
        segments: List of all segments
        segment_id: Segment ID to search for
        
    Returns:
        First matching segment or None if not found
    """
    matching_segments = find_segments(segments, segment_id)
    return matching_segments[0] if matching_segments else None


def split_edi_string(edi_string: str, segment_delimiter: str = "~") -> List[str]:
    """
    Split EDI string into segments.
    
    Args:
        edi_string: Raw EDI content
        segment_delimiter: Segment delimiter (usually "~")
        
    Returns:
        List of segment strings
    """
    if not edi_string:
        return []
    
    segments = [seg.strip() for seg in edi_string.split(segment_delimiter) if seg.strip()]
    return segments


def split_segment_elements(segment_string: str, element_delimiter: str = "*") -> List[str]:
    """
    Split segment string into elements.
    
    Args:
        segment_string: Segment as string
        element_delimiter: Element delimiter (usually "*")
        
    Returns:
        List of element strings
    """
    if not segment_string:
        return []
    
    return segment_string.split(element_delimiter)


def parse_edi_segments(edi_string: str, segment_delimiter: str = "~", element_delimiter: str = "*") -> List[List[str]]:
    """
    Parse EDI string into list of segment elements.
    
    Args:
        edi_string: Raw EDI content
        segment_delimiter: Segment delimiter (usually "~")
        element_delimiter: Element delimiter (usually "*")
        
    Returns:
        List of segments, where each segment is a list of elements
        
    Examples:
        >>> parse_edi_segments("ST*835*0001~BPR*I*100.00~")
        [["ST", "835", "0001"], ["BPR", "I", "100.00"]]
    """
    segment_strings = split_edi_string(edi_string, segment_delimiter)
    return [split_segment_elements(seg, element_delimiter) for seg in segment_strings]


def extract_amount(amount_str: str, default: float = 0.0) -> float:
    """
    Extract monetary amount from EDI string, handling common formatting issues.
    
    Args:
        amount_str: Amount string from EDI
        default: Default value if parsing fails
        
    Returns:
        Parsed amount as float
        
    Examples:
        >>> extract_amount("123.45")
        123.45
        >>> extract_amount("123")
        123.0
        >>> extract_amount("0")
        0.0
    """
    if not amount_str:
        return default
    
    # Remove any non-numeric characters except decimal point and minus sign
    cleaned = ''.join(c for c in amount_str if c.isdigit() or c in '.-')
    
    return safe_float(cleaned, default)


def is_empty_or_zero(value: Union[str, float, int]) -> bool:
    """
    Check if a value is empty, zero, or represents zero.
    
    Args:
        value: Value to check
        
    Returns:
        True if value is empty/zero, False otherwise
        
    Examples:
        >>> is_empty_or_zero("")
        True
        >>> is_empty_or_zero("0.00")
        True
        >>> is_empty_or_zero("123.45")
        False
    """
    if value is None:
        return True
    
    if isinstance(value, str):
        value = value.strip()
        if not value:
            return True
    
    try:
        return float(value) == 0.0
    except (ValueError, TypeError):
        return True


def normalize_identifier(identifier: str) -> str:
    """
    Normalize an identifier by removing extra spaces and converting to uppercase.
    
    Args:
        identifier: Identifier to normalize
        
    Returns:
        Normalized identifier
        
    Examples:
        >>> normalize_identifier("  claim001  ")
        "CLAIM001"
    """
    if not identifier:
        return ""
    
    return identifier.strip().upper()