"""
Standardized exception classes for EDI processing.

This module defines a hierarchy of exception classes that provide
consistent error handling across all EDI components.
"""

from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field


@dataclass
class ErrorInfo:
    """Detailed error information."""
    code: str
    message: str
    severity: str = "error"  # error, warning, info
    path: str = ""
    segment_id: Optional[str] = None
    element_position: Optional[int] = None
    value: Optional[str] = None
    context: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        result = {
            'code': self.code,
            'message': self.message,
            'severity': self.severity,
            'path': self.path
        }
        
        if self.segment_id:
            result['segment_id'] = self.segment_id
        if self.element_position is not None:
            result['element_position'] = self.element_position
        if self.value is not None:
            result['value'] = self.value
        if self.context:
            result['context'] = self.context
            
        return result


class EDIError(Exception):
    """Base exception class for all EDI-related errors."""
    
    def __init__(self, message: str, error_code: str = "EDI_ERROR", 
                 context: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.context = context or {}
        self.error_info = ErrorInfo(
            code=error_code,
            message=message,
            context=self.context
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary."""
        return {
            'type': self.__class__.__name__,
            'message': self.message,
            'error_code': self.error_code,
            'context': self.context
        }


class EDIParseError(EDIError):
    """Exception raised when parsing EDI segments fails."""
    
    def __init__(self, message: str, segment_info: Optional[Dict[str, Any]] = None, 
                 error_code: str = "PARSE_ERROR"):
        context = segment_info or {}
        super().__init__(message, error_code, context)
        self.segment_info = segment_info


class EDISegmentError(EDIParseError):
    """Exception raised for segment-specific parsing errors."""
    
    def __init__(self, message: str, segment_id: str, segment_position: int = -1,
                 element_position: Optional[int] = None, segment_data: Optional[List[str]] = None,
                 error_code: str = "SEGMENT_ERROR"):
        context = {
            'segment_id': segment_id,
            'segment_position': segment_position
        }
        
        if element_position is not None:
            context['element_position'] = element_position
        if segment_data:
            context['segment_data'] = segment_data
        
        super().__init__(message, context, error_code)
        self.segment_id = segment_id
        self.segment_position = segment_position
        self.element_position = element_position
        self.segment_data = segment_data


class EDITransactionError(EDIParseError):
    """Exception raised for transaction-level parsing errors."""
    
    def __init__(self, message: str, transaction_code: str, control_number: str = "",
                 error_code: str = "TRANSACTION_ERROR"):
        context = {
            'transaction_code': transaction_code,
            'control_number': control_number
        }
        super().__init__(message, context, error_code)
        self.transaction_code = transaction_code
        self.control_number = control_number


class EDIValidationError(EDIError):
    """Exception raised for validation failures."""
    
    def __init__(self, message: str, validation_rule: str = "", 
                 validation_path: str = "", error_code: str = "VALIDATION_ERROR"):
        context = {
            'validation_rule': validation_rule,
            'validation_path': validation_path
        }
        super().__init__(message, error_code, context)
        self.validation_rule = validation_rule
        self.validation_path = validation_path


class EDIPluginError(EDIError):
    """Exception raised for plugin-related errors."""
    
    def __init__(self, message: str, plugin_name: str = "", plugin_version: str = "",
                 error_code: str = "PLUGIN_ERROR"):
        context = {
            'plugin_name': plugin_name,
            'plugin_version': plugin_version
        }
        super().__init__(message, error_code, context)
        self.plugin_name = plugin_name
        self.plugin_version = plugin_version


class EDIConfigurationError(EDIError):
    """Exception raised for configuration-related errors."""
    
    def __init__(self, message: str, config_key: str = "", config_value: str = "",
                 error_code: str = "CONFIG_ERROR"):
        context = {
            'config_key': config_key,
            'config_value': config_value
        }
        super().__init__(message, error_code, context)
        self.config_key = config_key
        self.config_value = config_value


class EDIDataError(EDIError):
    """Exception raised for data format or content errors."""
    
    def __init__(self, message: str, field_name: str = "", field_value: str = "",
                 expected_format: str = "", error_code: str = "DATA_ERROR"):
        context = {
            'field_name': field_name,
            'field_value': field_value,
            'expected_format': expected_format
        }
        super().__init__(message, error_code, context)
        self.field_name = field_name
        self.field_value = field_value
        self.expected_format = expected_format


class EDIBusinessRuleError(EDIError):
    """Exception raised for business rule violations."""
    
    def __init__(self, message: str, rule_name: str = "", rule_description: str = "",
                 error_code: str = "BUSINESS_RULE_ERROR"):
        context = {
            'rule_name': rule_name,
            'rule_description': rule_description
        }
        super().__init__(message, error_code, context)
        self.rule_name = rule_name
        self.rule_description = rule_description


class EDIMultipleErrors(EDIError):
    """Exception that contains multiple EDI errors."""
    
    def __init__(self, message: str, errors: List[EDIError], 
                 error_code: str = "MULTIPLE_ERRORS"):
        context = {'error_count': len(errors)}
        super().__init__(message, error_code, context)
        self.errors = errors
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary including all sub-errors."""
        result = super().to_dict()
        result['errors'] = [error.to_dict() for error in self.errors]
        return result
    
    def get_errors_by_type(self, error_type: type) -> List[EDIError]:
        """Get all errors of a specific type."""
        return [error for error in self.errors if isinstance(error, error_type)]
    
    def has_error_type(self, error_type: type) -> bool:
        """Check if this collection contains errors of a specific type."""
        return any(isinstance(error, error_type) for error in self.errors)