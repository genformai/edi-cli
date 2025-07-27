"""
Standardized error handling for EDI processing.

This module provides consistent error types and handling patterns
across all EDI parsers and processing components.
"""

from .exceptions import (
    EDIError,
    EDIParseError,
    EDIValidationError,
    EDISegmentError,
    EDITransactionError,
    EDIPluginError,
    EDIConfigurationError,
    EDIDataError,
    EDIBusinessRuleError,
    EDIMultipleErrors,
    ErrorInfo
)

from .context import (
    ErrorContext, 
    ParseErrorContext, 
    ValidationErrorContext,
    PluginErrorContext,
    create_parse_context,
    create_validation_context,
    create_plugin_context
)

from .handler import (
    ErrorHandler, 
    StandardErrorHandler,
    SilentErrorHandler,
    FailFastErrorHandler,
    FilteringErrorHandler
)

__all__ = [
    # Exception classes
    'EDIError',
    'EDIParseError', 
    'EDIValidationError',
    'EDISegmentError',
    'EDITransactionError',
    'EDIPluginError',
    'EDIConfigurationError',
    'EDIDataError',
    'EDIBusinessRuleError',
    'EDIMultipleErrors',
    'ErrorInfo',
    
    # Context classes
    'ErrorContext',
    'ParseErrorContext',
    'ValidationErrorContext',
    'PluginErrorContext',
    'create_parse_context',
    'create_validation_context',
    'create_plugin_context',
    
    # Handler classes
    'ErrorHandler',
    'StandardErrorHandler',
    'SilentErrorHandler',
    'FailFastErrorHandler',
    'FilteringErrorHandler'
]