"""
Abstract Base Parser for EDI Transactions

This module defines the abstract base class that all EDI transaction parsers
should inherit from, providing a consistent interface and common functionality.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Union
import logging

logger = logging.getLogger(__name__)


class BaseParser(ABC):
    """
    Abstract base class for all EDI transaction parsers.
    
    This class defines the common interface and shared functionality that all
    transaction-specific parsers should implement and inherit.
    """
    
    def __init__(self, segments: List[List[str]]):
        """
        Initialize the parser with EDI segments.
        
        Args:
            segments: List of EDI segments, each segment is a list of elements
        """
        self.segments = segments
        self.current_index = 0
        
    @abstractmethod
    def parse(self) -> Any:
        """
        Parse the EDI transaction from segments.
        
        Returns:
            The parsed transaction object (type varies by parser implementation)
            
        Raises:
            ValueError: If unable to parse the transaction
        """
        pass
    
    @abstractmethod
    def get_transaction_codes(self) -> List[str]:
        """
        Get the transaction codes this parser supports.
        
        Returns:
            List of supported transaction codes (e.g., ["835"], ["270", "271"])
        """
        pass
    
    def _find_segment(self, segment_id: str) -> Optional[List[str]]:
        """
        Find the first segment with the given segment ID.
        
        Args:
            segment_id: The segment identifier to search for (e.g., "ST", "BHT")
            
        Returns:
            The first matching segment or None if not found
        """
        for segment in self.segments:
            if segment and segment[0] == segment_id:
                return segment
        return None
    
    def _find_all_segments(self, segment_id: str) -> List[List[str]]:
        """
        Find all segments with the given segment ID.
        
        Args:
            segment_id: The segment identifier to search for
            
        Returns:
            List of all matching segments
        """
        matching_segments = []
        for segment in self.segments:
            if segment and segment[0] == segment_id:
                matching_segments.append(segment)
        return matching_segments
    
    def _get_element(self, segment: List[str], index: int, default: str = "") -> str:
        """
        Safely get an element from a segment.
        
        Args:
            segment: The segment to extract from
            index: The element index
            default: Default value if element doesn't exist
            
        Returns:
            The element value or default
        """
        if segment and len(segment) > index:
            return segment[index].strip()
        return default
    
    def _parse_header(self, transaction: Any) -> None:
        """
        Parse common header information from ST segment.
        
        Args:
            transaction: The transaction object to populate
        """
        st_segment = self._find_segment("ST")
        if st_segment:
            transaction.header = {
                "transaction_set_identifier": self._get_element(st_segment, 1),
                "transaction_set_control_number": self._get_element(st_segment, 2),
            }
        else:
            transaction.header = {}
            
    def _safe_float(self, value: str, default: float = 0.0) -> float:
        """
        Safely convert a string to float.
        
        Args:
            value: String value to convert
            default: Default value if conversion fails
            
        Returns:
            Float value or default
        """
        try:
            return float(value) if value and value.strip() else default
        except (ValueError, TypeError):
            return default
            
    def _safe_int(self, value: str, default: int = 0) -> int:
        """
        Safely convert a string to integer.
        
        Args:
            value: String value to convert
            default: Default value if conversion fails
            
        Returns:
            Integer value or default
        """
        try:
            return int(value) if value and value.strip() else default
        except (ValueError, TypeError):
            return default
    
    def _format_date_ccyymmdd(self, date: str) -> str:
        """
        Format CCYYMMDD date to YYYY-MM-DD.
        
        Args:
            date: Date string in CCYYMMDD format
            
        Returns:
            Formatted date string or original if invalid
        """
        if date and len(date) == 8 and date.isdigit():
            return f"{date[0:4]}-{date[4:6]}-{date[6:8]}"
        return date
    
    def _format_date_yymmdd(self, date: str) -> str:
        """
        Format YYMMDD date to YYYY-MM-DD (assumes 20xx century).
        
        Args:
            date: Date string in YYMMDD format
            
        Returns:
            Formatted date string or original if invalid
        """
        if date and len(date) == 6 and date.isdigit():
            return f"20{date[0:2]}-{date[2:4]}-{date[4:6]}"
        return date
    
    def _format_time(self, time: str) -> str:
        """
        Format HHMM time to HH:MM.
        
        Args:
            time: Time string in HHMM format
            
        Returns:
            Formatted time string or original if invalid
        """
        if time and len(time) == 4 and time.isdigit():
            return f"{time[0:2]}:{time[2:4]}"
        return time
    
    def validate_segments(self, segments: List[List[str]]) -> bool:
        """
        Validate that the segments are appropriate for this parser.
        
        Args:
            segments: List of segments to validate
            
        Returns:
            True if segments are valid for this parser
        """
        if not segments:
            return False
            
        # Check for ST segment with supported transaction code
        st_segment = None
        for segment in segments:
            if segment and segment[0] == "ST":
                st_segment = segment
                break
                
        if not st_segment or len(st_segment) < 2:
            return False
            
        transaction_code = st_segment[1]
        return transaction_code in self.get_transaction_codes()