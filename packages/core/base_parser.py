"""
Abstract Base Parser for EDI Transactions

This module defines the abstract base class that all EDI transaction parsers
should inherit from, providing a consistent interface and common functionality.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Union
import logging
from .utils import get_element, safe_float, safe_int, format_edi_date, format_edi_time

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
            if segment and get_element(segment, 0) == segment_id:
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
            if segment and get_element(segment, 0) == segment_id:
                matching_segments.append(segment)
        return matching_segments
    
    def _get_element(self, segment: List[str], index: int, default: str = "") -> str:
        """
        Safely get an element from a segment.
        DEPRECATED: Use utils.get_element() instead.
        """
        return get_element(segment, index, default)
    
    def _parse_header(self, transaction: Any) -> None:
        """
        Parse common header information from ST segment.
        
        Args:
            transaction: The transaction object to populate
        """
        st_segment = self._find_segment("ST")
        if st_segment:
            transaction.header = {
                "transaction_set_identifier": get_element(st_segment, 1),
                "transaction_set_control_number": get_element(st_segment, 2),
            }
        else:
            transaction.header = {}
            
    def _safe_float(self, value: str, default: float = 0.0) -> float:
        """
        Safely convert a string to float.
        DEPRECATED: Use utils.safe_float() instead.
        """
        return safe_float(value, default)
            
    def _safe_int(self, value: str, default: int = 0) -> int:
        """
        Safely convert a string to integer.
        DEPRECATED: Use utils.safe_int() instead.
        """
        return safe_int(value, default)
    
    def _format_date_ccyymmdd(self, date: str) -> str:
        """
        Format CCYYMMDD date to YYYY-MM-DD.
        DEPRECATED: Use utils.format_edi_date() instead.
        """
        return format_edi_date(date, "CCYYMMDD")
    
    def _format_date_yymmdd(self, date: str) -> str:
        """
        Format YYMMDD date to YYYY-MM-DD (assumes 20xx century).
        DEPRECATED: Use utils.format_edi_date() instead.
        """
        return format_edi_date(date, "YYMMDD")
    
    def _format_time(self, time: str) -> str:
        """
        Format HHMM time to HH:MM.
        DEPRECATED: Use utils.format_edi_time() instead.
        """
        return format_edi_time(time, "HHMM")
    
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
            if segment and get_element(segment, 0) == "ST":
                st_segment = segment
                break
                
        if not st_segment or len(st_segment) < 2:
            return False
            
        transaction_code = get_element(st_segment, 1)
        return transaction_code in self.get_transaction_codes()