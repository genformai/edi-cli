"""
Error handler classes for managing EDI processing errors.

This module provides handlers that process and respond to errors
during EDI parsing, validation, and plugin operations.
"""

from typing import List, Dict, Any, Optional, Callable
import logging
from abc import ABC, abstractmethod

from .exceptions import EDIError, EDIMultipleErrors
from .context import ErrorContext


logger = logging.getLogger(__name__)


class ErrorHandler(ABC):
    """Abstract base class for error handlers."""
    
    @abstractmethod
    def handle_error(self, error: EDIError, context: Optional[ErrorContext] = None) -> None:
        """
        Handle a single EDI error.
        
        Args:
            error: The EDI error to handle
            context: Optional error context for additional information
        """
        pass
    
    @abstractmethod
    def handle_multiple_errors(self, errors: List[EDIError], 
                             context: Optional[ErrorContext] = None) -> None:
        """
        Handle multiple EDI errors.
        
        Args:
            errors: List of EDI errors to handle
            context: Optional error context for additional information
        """
        pass
    
    @abstractmethod
    def should_continue(self, error: EDIError) -> bool:
        """
        Determine if processing should continue after this error.
        
        Args:
            error: The error that occurred
            
        Returns:
            bool: True if processing should continue, False otherwise
        """
        pass


class StandardErrorHandler(ErrorHandler):
    """Standard implementation of error handler with logging and callbacks."""
    
    def __init__(self, 
                 log_errors: bool = True,
                 raise_on_error: bool = False,
                 error_callback: Optional[Callable[[EDIError, Optional[ErrorContext]], None]] = None,
                 max_errors: Optional[int] = None):
        """
        Initialize the standard error handler.
        
        Args:
            log_errors: Whether to log errors
            raise_on_error: Whether to raise exceptions on errors
            error_callback: Optional callback function for custom error handling
            max_errors: Maximum number of errors before stopping (None for unlimited)
        """
        self.log_errors = log_errors
        self.raise_on_error = raise_on_error
        self.error_callback = error_callback
        self.max_errors = max_errors
        self.error_count = 0
        self.collected_errors: List[EDIError] = []
    
    def handle_error(self, error: EDIError, context: Optional[ErrorContext] = None) -> None:
        """Handle a single EDI error."""
        self.error_count += 1
        self.collected_errors.append(error)
        
        if self.log_errors:
            self._log_error(error, context)
        
        if self.error_callback:
            try:
                self.error_callback(error, context)
            except Exception as e:
                logger.error(f"Error in error callback: {e}")
        
        if self.raise_on_error:
            raise error
    
    def handle_multiple_errors(self, errors: List[EDIError], 
                             context: Optional[ErrorContext] = None) -> None:
        """Handle multiple EDI errors."""
        if not errors:
            return
        
        for error in errors:
            self.handle_error(error, context)
        
        if self.raise_on_error and len(errors) > 1:
            # Raise a multiple errors exception
            multiple_error = EDIMultipleErrors(
                f"Multiple errors occurred ({len(errors)} errors)",
                errors
            )
            raise multiple_error
    
    def should_continue(self, error: EDIError) -> bool:
        """Determine if processing should continue after this error."""
        if self.max_errors is not None and self.error_count >= self.max_errors:
            return False
        
        # Don't continue if we're configured to raise on errors
        if self.raise_on_error:
            return False
        
        return True
    
    def reset(self) -> None:
        """Reset the error handler state."""
        self.error_count = 0
        self.collected_errors.clear()
    
    def get_errors(self) -> List[EDIError]:
        """Get all collected errors."""
        return self.collected_errors.copy()
    
    def has_errors(self) -> bool:
        """Check if any errors have been collected."""
        return len(self.collected_errors) > 0
    
    def _log_error(self, error: EDIError, context: Optional[ErrorContext] = None) -> None:
        """Log the error with appropriate level and context."""
        error_info = {
            'error_type': type(error).__name__,
            'error_code': error.error_code,
            'message': error.message
        }
        
        if context:
            error_info.update({
                'component': context.component,
                'operation': context.operation,
                'timestamp': context.timestamp.isoformat()
            })
            error_info.update(context.metadata)
        
        # Add specific error context
        if hasattr(error, 'context') and error.context:
            error_info.update(error.context)
        
        logger.error(f"EDI Error: {error.message}", extra=error_info)


class SilentErrorHandler(ErrorHandler):
    """Error handler that collects errors without logging or raising."""
    
    def __init__(self, max_errors: Optional[int] = None):
        self.max_errors = max_errors
        self.collected_errors: List[EDIError] = []
    
    def handle_error(self, error: EDIError, context: Optional[ErrorContext] = None) -> None:
        """Silently collect the error."""
        self.collected_errors.append(error)
    
    def handle_multiple_errors(self, errors: List[EDIError], 
                             context: Optional[ErrorContext] = None) -> None:
        """Silently collect multiple errors."""
        self.collected_errors.extend(errors)
    
    def should_continue(self, error: EDIError) -> bool:
        """Determine if processing should continue."""
        if self.max_errors is not None and len(self.collected_errors) >= self.max_errors:
            return False
        return True
    
    def get_errors(self) -> List[EDIError]:
        """Get all collected errors."""
        return self.collected_errors.copy()
    
    def has_errors(self) -> bool:
        """Check if any errors have been collected."""
        return len(self.collected_errors) > 0
    
    def reset(self) -> None:
        """Reset the error handler state."""
        self.collected_errors.clear()


class FailFastErrorHandler(ErrorHandler):
    """Error handler that raises on the first error encountered."""
    
    def handle_error(self, error: EDIError, context: Optional[ErrorContext] = None) -> None:
        """Immediately raise the error."""
        raise error
    
    def handle_multiple_errors(self, errors: List[EDIError], 
                             context: Optional[ErrorContext] = None) -> None:
        """Raise the first error or a multiple errors exception."""
        if not errors:
            return
        
        if len(errors) == 1:
            raise errors[0]
        else:
            raise EDIMultipleErrors(
                f"Multiple errors occurred ({len(errors)} errors)",
                errors
            )
    
    def should_continue(self, error: EDIError) -> bool:
        """Never continue after an error."""
        return False


class FilteringErrorHandler(ErrorHandler):
    """Error handler that filters errors based on criteria."""
    
    def __init__(self, 
                 base_handler: ErrorHandler,
                 error_filter: Callable[[EDIError], bool]):
        """
        Initialize filtering error handler.
        
        Args:
            base_handler: The underlying error handler
            error_filter: Function that returns True if error should be handled
        """
        self.base_handler = base_handler
        self.error_filter = error_filter
    
    def handle_error(self, error: EDIError, context: Optional[ErrorContext] = None) -> None:
        """Handle error only if it passes the filter."""
        if self.error_filter(error):
            self.base_handler.handle_error(error, context)
    
    def handle_multiple_errors(self, errors: List[EDIError], 
                             context: Optional[ErrorContext] = None) -> None:
        """Handle multiple errors, filtering each one."""
        filtered_errors = [error for error in errors if self.error_filter(error)]
        if filtered_errors:
            self.base_handler.handle_multiple_errors(filtered_errors, context)
    
    def should_continue(self, error: EDIError) -> bool:
        """Delegate to base handler if error passes filter."""
        if self.error_filter(error):
            return self.base_handler.should_continue(error)
        return True  # Continue if error is filtered out