"""
Enhanced parser interface with integrated error handling.

This module provides an enhanced parser base class that integrates
with the standardized error handling system.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Union
import logging

from .parser import BaseParser
from ..errors import (
    EDIError, EDIParseError, EDISegmentError, EDITransactionError,
    ErrorHandler, StandardErrorHandler,
    create_parse_context, ParseErrorContext
)
from ..utils import get_element

logger = logging.getLogger(__name__)


class EnhancedParser(BaseParser):
    """
    Enhanced parser with integrated error handling.
    
    This parser extends the base parser with standardized error handling,
    context tracking, and recovery mechanisms.
    """
    
    def __init__(self, 
                 segments: List[List[str]], 
                 error_handler: Optional[ErrorHandler] = None,
                 strict_mode: bool = False):
        """
        Initialize the enhanced parser.
        
        Args:
            segments: List of EDI segments to parse
            error_handler: Error handler for managing errors (defaults to StandardErrorHandler)
            strict_mode: Whether to operate in strict mode (fail fast on errors)
        """
        super().__init__(segments)
        self.error_handler = error_handler or StandardErrorHandler(
            log_errors=True,
            raise_on_error=strict_mode
        )
        self.strict_mode = strict_mode
        self.parse_context = create_parse_context().operation("parse").component(self.__class__.__name__)
    
    def parse_with_error_handling(self) -> Optional[Any]:
        """
        Parse with integrated error handling.
        
        Returns:
            Parsed transaction or None if parsing failed completely
        """
        try:
            self.parse_context = (self.parse_context
                                .segments(self.segments)
                                .parser_name(self.__class__.__name__))
            
            return self.parse()
        except EDIError as e:
            self.error_handler.handle_error(e, self.parse_context.build())
            if not self.error_handler.should_continue(e):
                return None
        except Exception as e:
            # Convert unexpected exceptions to EDI errors
            edi_error = EDIParseError(
                f"Unexpected error during parsing: {str(e)}",
                {"original_exception": str(e), "exception_type": type(e).__name__}
            )
            self.error_handler.handle_error(edi_error, self.parse_context.build())
            if not self.error_handler.should_continue(edi_error):
                return None
        
        return None
    
    def _handle_segment_error(self, segment: List[str], segment_index: int, 
                            error_message: str, element_position: Optional[int] = None) -> bool:
        """
        Handle a segment-specific error.
        
        Args:
            segment: The problematic segment
            segment_index: Index of the segment in the segments list
            error_message: Description of the error
            element_position: Optional position of problematic element
            
        Returns:
            True if processing should continue, False otherwise
        """
        context = (create_parse_context()
                  .segments(self.segments)
                  .current_segment_index(segment_index)
                  .parser_name(self.__class__.__name__)
                  .operation("parse_segment")
                  .component(self.__class__.__name__))
        
        segment_error = EDISegmentError(
            error_message,
            segment_id=get_element(segment, 0, "UNKNOWN"),
            segment_position=segment_index,
            element_position=element_position,
            segment_data=segment
        )
        
        self.error_handler.handle_error(segment_error, context.build())
        return self.error_handler.should_continue(segment_error)
    
    def _handle_transaction_error(self, transaction_code: str, control_number: str,
                                error_message: str) -> bool:
        """
        Handle a transaction-level error.
        
        Args:
            transaction_code: The transaction code being parsed
            control_number: Transaction control number
            error_message: Description of the error
            
        Returns:
            True if processing should continue, False otherwise
        """
        context = (create_parse_context()
                  .transaction_code(transaction_code)
                  .parser_name(self.__class__.__name__)
                  .operation("parse_transaction")
                  .component(self.__class__.__name__))
        
        transaction_error = EDITransactionError(
            error_message,
            transaction_code=transaction_code,
            control_number=control_number
        )
        
        self.error_handler.handle_error(transaction_error, context.build())
        return self.error_handler.should_continue(transaction_error)
    
    def _safe_parse_element(self, segment: List[str], element_index: int, 
                          element_name: str, segment_index: int = -1,
                          default: Any = "", converter: Optional[callable] = None) -> Any:
        """
        Safely parse an element with error handling.
        
        Args:
            segment: The segment containing the element
            element_index: Index of the element in the segment
            element_name: Name of the element for error reporting
            segment_index: Index of segment in segments list
            default: Default value if parsing fails
            converter: Optional converter function (e.g., float, int)
            
        Returns:
            Parsed element value or default on error
        """
        try:
            value = get_element(segment, element_index, "")
            if not value:
                return default
            
            if converter:
                return converter(value)
            return value
            
        except (ValueError, TypeError, IndexError) as e:
            error_message = f"Error parsing {element_name} at element {element_index}: {str(e)}"
            if self._handle_segment_error(segment, segment_index, error_message, element_index):
                return default
            else:
                raise EDISegmentError(
                    error_message,
                    segment_id=get_element(segment, 0, "UNKNOWN"),
                    segment_position=segment_index,
                    element_position=element_index,
                    segment_data=segment
                )
    
    def _validate_required_segment(self, segment_id: str, 
                                 context_description: str = "") -> Optional[List[str]]:
        """
        Validate that a required segment exists.
        
        Args:
            segment_id: ID of the required segment
            context_description: Additional context for error reporting
            
        Returns:
            The segment if found, None if missing (and error is handled)
            
        Raises:
            EDITransactionError: If segment is missing and strict mode is enabled
        """
        segment = self._find_segment(segment_id)
        if not segment:
            error_message = f"Required segment {segment_id} not found"
            if context_description:
                error_message += f" in {context_description}"
            
            transaction_error = EDITransactionError(
                error_message,
                transaction_code="UNKNOWN",
                control_number=""
            )
            
            self.error_handler.handle_error(transaction_error, self.parse_context.build())
            if not self.error_handler.should_continue(transaction_error):
                return None
            elif self.strict_mode:
                raise transaction_error
        
        return segment
    
    def get_error_summary(self) -> Dict[str, Any]:
        """
        Get a summary of errors encountered during parsing.
        
        Returns:
            Dictionary containing error statistics and details
        """
        if hasattr(self.error_handler, 'get_errors'):
            errors = self.error_handler.get_errors()
            return {
                'total_errors': len(errors),
                'error_types': {type(e).__name__: sum(1 for err in errors if type(err) == type(e)) 
                              for e in errors},
                'has_fatal_errors': any(isinstance(e, (EDITransactionError, EDIParseError)) 
                                      for e in errors),
                'errors': [e.to_dict() for e in errors]
            }
        return {'total_errors': 0, 'error_types': {}, 'has_fatal_errors': False, 'errors': []}
    
    def reset_error_state(self) -> None:
        """Reset the error handler state for reuse."""
        if hasattr(self.error_handler, 'reset'):
            self.error_handler.reset()


class ErrorAwareParserMixin:
    """
    Mixin class that adds error handling capabilities to existing parsers.
    
    This can be used to enhance existing parser classes without
    completely rewriting them.
    """
    
    def __init__(self, error_handler: Optional[ErrorHandler] = None):
        self.error_handler = error_handler or StandardErrorHandler()
    
    def with_error_handling(self, parse_method: callable) -> callable:
        """
        Decorator to add error handling to a parse method.
        
        Args:
            parse_method: The original parse method to wrap
            
        Returns:
            Wrapped parse method with error handling
        """
        def wrapped_parse(*args, **kwargs):
            try:
                return parse_method(*args, **kwargs)
            except EDIError as e:
                self.error_handler.handle_error(e)
                if not self.error_handler.should_continue(e):
                    return None
            except Exception as e:
                edi_error = EDIParseError(f"Unexpected parsing error: {str(e)}")
                self.error_handler.handle_error(edi_error)
                if not self.error_handler.should_continue(edi_error):
                    return None
            return None
        
        return wrapped_parse