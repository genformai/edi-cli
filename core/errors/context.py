"""
Error context classes for providing detailed error information.

This module provides context classes that capture the state and
environment when errors occur during EDI processing.
"""

from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class ErrorContext:
    """Base context class for error information."""
    timestamp: datetime = field(default_factory=datetime.now)
    operation: str = ""
    component: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def add_metadata(self, key: str, value: Any):
        """Add metadata to the context."""
        self.metadata[key] = value
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert context to dictionary."""
        return {
            'timestamp': self.timestamp.isoformat(),
            'operation': self.operation,
            'component': self.component,
            'metadata': self.metadata
        }


@dataclass
class ParseErrorContext(ErrorContext):
    """Context for parsing errors."""
    segments: List[List[str]] = field(default_factory=list)
    current_segment_index: int = -1
    transaction_code: str = ""
    parser_name: str = ""
    
    @property
    def current_segment(self) -> Optional[List[str]]:
        """Get the current segment being processed."""
        if 0 <= self.current_segment_index < len(self.segments):
            return self.segments[self.current_segment_index]
        return None
    
    @property
    def segment_count(self) -> int:
        """Get total number of segments."""
        return len(self.segments)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert context to dictionary."""
        result = super().to_dict()
        result.update({
            'segment_count': self.segment_count,
            'current_segment_index': self.current_segment_index,
            'transaction_code': self.transaction_code,
            'parser_name': self.parser_name
        })
        
        if self.current_segment:
            result['current_segment'] = self.current_segment
        
        return result


@dataclass
class ValidationErrorContext(ErrorContext):
    """Context for validation errors."""
    validation_rule: str = ""
    validation_path: str = ""
    document_type: str = ""
    strict_mode: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert context to dictionary."""
        result = super().to_dict()
        result.update({
            'validation_rule': self.validation_rule,
            'validation_path': self.validation_path,
            'document_type': self.document_type,
            'strict_mode': self.strict_mode
        })
        return result


@dataclass
class PluginErrorContext(ErrorContext):
    """Context for plugin errors."""
    plugin_name: str = ""
    plugin_version: str = ""
    plugin_type: str = ""
    transaction_codes: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert context to dictionary."""
        result = super().to_dict()
        result.update({
            'plugin_name': self.plugin_name,
            'plugin_version': self.plugin_version,
            'plugin_type': self.plugin_type,
            'transaction_codes': self.transaction_codes
        })
        return result


class ErrorContextBuilder:
    """Builder for creating error contexts."""
    
    def __init__(self, context_type: type = ErrorContext):
        self.context_type = context_type
        self._data = {}
    
    def operation(self, operation: str) -> 'ErrorContextBuilder':
        """Set the operation name."""
        self._data['operation'] = operation
        return self
    
    def component(self, component: str) -> 'ErrorContextBuilder':
        """Set the component name."""
        self._data['component'] = component
        return self
    
    def metadata(self, **kwargs) -> 'ErrorContextBuilder':
        """Add metadata."""
        if 'metadata' not in self._data:
            self._data['metadata'] = {}
        self._data['metadata'].update(kwargs)
        return self
    
    def segments(self, segments: List[List[str]]) -> 'ErrorContextBuilder':
        """Set segments (for ParseErrorContext)."""
        self._data['segments'] = segments
        return self
    
    def current_segment_index(self, index: int) -> 'ErrorContextBuilder':
        """Set current segment index (for ParseErrorContext)."""
        self._data['current_segment_index'] = index
        return self
    
    def transaction_code(self, code: str) -> 'ErrorContextBuilder':
        """Set transaction code."""
        self._data['transaction_code'] = code
        return self
    
    def parser_name(self, name: str) -> 'ErrorContextBuilder':
        """Set parser name."""
        self._data['parser_name'] = name
        return self
    
    def validation_rule(self, rule: str) -> 'ErrorContextBuilder':
        """Set validation rule (for ValidationErrorContext)."""
        self._data['validation_rule'] = rule
        return self
    
    def validation_path(self, path: str) -> 'ErrorContextBuilder':
        """Set validation path (for ValidationErrorContext)."""
        self._data['validation_path'] = path
        return self
    
    def plugin_name(self, name: str) -> 'ErrorContextBuilder':
        """Set plugin name (for PluginErrorContext)."""
        self._data['plugin_name'] = name
        return self
    
    def plugin_version(self, version: str) -> 'ErrorContextBuilder':
        """Set plugin version (for PluginErrorContext)."""
        self._data['plugin_version'] = version
        return self
    
    def build(self) -> ErrorContext:
        """Build the error context."""
        return self.context_type(**self._data)


def create_parse_context() -> ErrorContextBuilder:
    """Create a parse error context builder."""
    return ErrorContextBuilder(ParseErrorContext)


def create_validation_context() -> ErrorContextBuilder:
    """Create a validation error context builder."""
    return ErrorContextBuilder(ValidationErrorContext)


def create_plugin_context() -> ErrorContextBuilder:
    """Create a plugin error context builder."""
    return ErrorContextBuilder(PluginErrorContext)