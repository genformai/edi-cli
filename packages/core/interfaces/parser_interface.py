"""
Standardized parser interface for EDI processing.

This module provides the unified interface for all EDI parsers
with consistent error handling and validation.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Protocol, runtime_checkable
from dataclasses import dataclass
from enum import Enum

from ..errors import ErrorHandler, StandardErrorHandler
from ..base.enhanced_parser import EnhancedParser


class ParseResult(Enum):
    """Result status of parsing operation."""
    SUCCESS = "success"
    SUCCESS_WITH_WARNINGS = "success_with_warnings"
    PARTIAL_SUCCESS = "partial_success"
    FAILURE = "failure"


@dataclass
class ParseOutput:
    """Container for parse results and metadata."""
    result: ParseResult
    data: Optional[Any] = None
    errors: List[Dict[str, Any]] = None
    warnings: List[Dict[str, Any]] = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.errors is None:
            self.errors = []
        if self.warnings is None:
            self.warnings = []
        if self.metadata is None:
            self.metadata = {}
    
    @property
    def is_successful(self) -> bool:
        """Check if parsing was successful."""
        return self.result in [ParseResult.SUCCESS, ParseResult.SUCCESS_WITH_WARNINGS]
    
    @property
    def has_errors(self) -> bool:
        """Check if there are any errors."""
        return len(self.errors) > 0
    
    @property
    def has_warnings(self) -> bool:
        """Check if there are any warnings."""
        return len(self.warnings) > 0


@runtime_checkable
class EDIParser(Protocol):
    """Protocol defining the interface for EDI parsers."""
    
    def get_transaction_codes(self) -> List[str]:
        """Get supported transaction codes."""
        ...
    
    def parse(self) -> Any:
        """Parse the EDI transaction."""
        ...
    
    def validate_segments(self, segments: List[List[str]]) -> bool:
        """Validate that segments are appropriate for this parser."""
        ...


class StandardizedParser(ABC):
    """
    Abstract base class for standardized EDI parsers.
    
    This class provides a unified interface that all transaction-specific
    parsers should implement, with integrated error handling and validation.
    """
    
    def __init__(self, 
                 segments: List[List[str]],
                 error_handler: Optional[ErrorHandler] = None,
                 strict_mode: bool = False,
                 metadata: Optional[Dict[str, Any]] = None):
        """
        Initialize the standardized parser.
        
        Args:
            segments: EDI segments to parse
            error_handler: Custom error handler
            strict_mode: Whether to fail fast on errors
            metadata: Additional metadata for parsing context
        """
        self.segments = segments
        self.error_handler = error_handler or StandardErrorHandler()
        self.strict_mode = strict_mode
        self.metadata = metadata or {}
        self._parse_metadata = {
            'parser_class': self.__class__.__name__,
            'segment_count': len(segments),
            'strict_mode': strict_mode
        }
    
    @abstractmethod
    def get_transaction_codes(self) -> List[str]:
        """Get the transaction codes this parser supports."""
        pass
    
    @abstractmethod
    def _parse_implementation(self) -> Any:
        """
        Implementation-specific parsing logic.
        
        This method should contain the actual parsing logic
        for the specific transaction type.
        """
        pass
    
    def parse_with_result(self) -> ParseOutput:
        """
        Parse with comprehensive result reporting.
        
        Returns:
            ParseOutput containing results, errors, and metadata
        """
        try:
            # Validate segments first
            if not self.validate_segments(self.segments):
                return ParseOutput(
                    result=ParseResult.FAILURE,
                    errors=[{
                        'code': 'INVALID_SEGMENTS',
                        'message': 'Segments are not valid for this parser',
                        'parser': self.__class__.__name__
                    }],
                    metadata=self._parse_metadata
                )
            
            # Perform parsing
            parsed_data = self._parse_implementation()
            
            # Collect error information
            error_summary = self._get_error_summary()
            
            # Determine result status
            if error_summary['total_errors'] == 0:
                result_status = ParseResult.SUCCESS
            elif error_summary['has_fatal_errors']:
                result_status = ParseResult.FAILURE if parsed_data is None else ParseResult.PARTIAL_SUCCESS
            else:
                result_status = ParseResult.SUCCESS_WITH_WARNINGS
            
            return ParseOutput(
                result=result_status,
                data=parsed_data,
                errors=error_summary.get('errors', []),
                warnings=[],  # Can be enhanced to separate warnings from errors
                metadata={**self._parse_metadata, **error_summary}
            )
            
        except Exception as e:
            return ParseOutput(
                result=ParseResult.FAILURE,
                errors=[{
                    'code': 'UNEXPECTED_ERROR',
                    'message': f'Unexpected error during parsing: {str(e)}',
                    'exception_type': type(e).__name__
                }],
                metadata=self._parse_metadata
            )
    
    def parse(self) -> Any:
        """
        Standard parse method for backward compatibility.
        
        Returns:
            Parsed data or None on failure
        """
        result = self.parse_with_result()
        return result.data if result.is_successful else None
    
    def validate_segments(self, segments: List[List[str]]) -> bool:
        """
        Validate segments for this parser.
        
        Args:
            segments: Segments to validate
            
        Returns:
            True if segments are valid for this parser
        """
        if not segments:
            return False
        
        # Find ST segment
        st_segment = None
        for segment in segments:
            if segment and len(segment) > 1 and segment[0] == "ST":
                st_segment = segment
                break
        
        if not st_segment:
            return False
        
        transaction_code = st_segment[1] if len(st_segment) > 1 else ""
        return transaction_code in self.get_transaction_codes()
    
    def _get_error_summary(self) -> Dict[str, Any]:
        """Get error summary from error handler."""
        if hasattr(self.error_handler, 'get_errors'):
            errors = self.error_handler.get_errors()
            return {
                'total_errors': len(errors),
                'error_types': {},
                'has_fatal_errors': False,
                'errors': [e.to_dict() for e in errors]
            }
        return {
            'total_errors': 0,
            'error_types': {},
            'has_fatal_errors': False,
            'errors': []
        }


class ParserRegistry:
    """Registry for managing EDI parsers."""
    
    def __init__(self):
        self._parsers: Dict[str, type] = {}
    
    def register_parser(self, transaction_codes: List[str], parser_class: type) -> None:
        """
        Register a parser for specific transaction codes.
        
        Args:
            transaction_codes: Transaction codes this parser handles
            parser_class: Parser class to register
        """
        for code in transaction_codes:
            self._parsers[code] = parser_class
    
    def get_parser(self, transaction_code: str) -> Optional[type]:
        """
        Get parser class for a transaction code.
        
        Args:
            transaction_code: Transaction code to find parser for
            
        Returns:
            Parser class or None if not found
        """
        return self._parsers.get(transaction_code)
    
    def get_supported_codes(self) -> List[str]:
        """Get all supported transaction codes."""
        return list(self._parsers.keys())
    
    def create_parser(self, 
                     transaction_code: str,
                     segments: List[List[str]],
                     error_handler: Optional[ErrorHandler] = None,
                     strict_mode: bool = False) -> Optional[Any]:
        """
        Create a parser instance for the given transaction code.
        
        Args:
            transaction_code: Transaction code to parse
            segments: EDI segments
            error_handler: Custom error handler
            strict_mode: Whether to operate in strict mode
            
        Returns:
            Parser instance or None if no parser found
        """
        parser_class = self.get_parser(transaction_code)
        if not parser_class:
            return None
        
        # Check if parser supports enhanced interface
        if issubclass(parser_class, (EnhancedParser, StandardizedParser)):
            return parser_class(segments, error_handler, strict_mode)
        else:
            # Legacy parser
            return parser_class(segments)


# Global parser registry instance
parser_registry = ParserRegistry()