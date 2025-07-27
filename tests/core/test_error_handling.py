"""
Tests for the standardized error handling system.
"""

import pytest
from unittest.mock import Mock

from packages.core.errors import (
    EDIError, EDIParseError, EDISegmentError, EDIValidationError,
    StandardErrorHandler, SilentErrorHandler, FailFastErrorHandler,
    create_parse_context, create_validation_context
)
from packages.core.base.enhanced_parser import EnhancedParser
from packages.core.interfaces import ParseResult, ParseOutput


class TestErrorHandling:
    """Test the error handling system."""
    
    def test_standard_error_handler(self):
        """Test StandardErrorHandler functionality."""
        handler = StandardErrorHandler(log_errors=False, raise_on_error=False)
        
        error = EDIError("Test error", "TEST_001")
        context = create_parse_context().operation("test").build()
        
        handler.handle_error(error, context)
        
        assert handler.has_errors()
        assert len(handler.get_errors()) == 1
        assert handler.should_continue(error)
        
        errors = handler.get_errors()
        assert errors[0].message == "Test error"
        assert errors[0].error_code == "TEST_001"
    
    def test_silent_error_handler(self):
        """Test SilentErrorHandler functionality."""
        handler = SilentErrorHandler()
        
        error = EDIParseError("Parse error", {"segment": "ST"})
        handler.handle_error(error)
        
        assert handler.has_errors()
        assert len(handler.get_errors()) == 1
        assert handler.should_continue(error)
    
    def test_fail_fast_error_handler(self):
        """Test FailFastErrorHandler functionality."""
        handler = FailFastErrorHandler()
        
        error = EDISegmentError("Segment error", "ST", 0)
        
        with pytest.raises(EDISegmentError):
            handler.handle_error(error)
        
        assert not handler.should_continue(error)
    
    def test_error_context_creation(self):
        """Test error context builders."""
        parse_context = (create_parse_context()
                        .operation("parsing")
                        .component("Parser835")
                        .parser_name("Parser835")
                        .transaction_code("835")
                        .build())
        
        assert parse_context.operation == "parsing"
        assert parse_context.component == "Parser835"
        assert parse_context.parser_name == "Parser835"
        assert parse_context.transaction_code == "835"
        
        validation_context = (create_validation_context()
                             .operation("validation")
                             .validation_rule("NPI_VALIDATION")
                             .validation_path("provider.npi")
                             .build())
        
        assert validation_context.operation == "validation"
        assert validation_context.validation_rule == "NPI_VALIDATION"
        assert validation_context.validation_path == "provider.npi"
    
    def test_error_hierarchy(self):
        """Test error exception hierarchy."""
        # Test base EDI error
        base_error = EDIError("Base error")
        assert base_error.error_code == "EDI_ERROR"
        assert str(base_error) == "Base error"
        
        # Test parse error
        parse_error = EDIParseError("Parse failed", {"line": 1})
        assert parse_error.error_code == "PARSE_ERROR"
        assert parse_error.segment_info["line"] == 1
        
        # Test segment error
        segment_error = EDISegmentError("Invalid ST", "ST", 0, 1, ["ST", "999"])
        assert segment_error.segment_id == "ST"
        assert segment_error.segment_position == 0
        assert segment_error.element_position == 1
        assert segment_error.segment_data == ["ST", "999"]
        
        # Test validation error
        validation_error = EDIValidationError("Validation failed", "NPI_CHECK", "provider.npi")
        assert validation_error.validation_rule == "NPI_CHECK"
        assert validation_error.validation_path == "provider.npi"
    
    def test_parse_output(self):
        """Test ParseOutput functionality."""
        # Successful parse
        success_output = ParseOutput(
            result=ParseResult.SUCCESS,
            data={"transaction": "835"},
            metadata={"parser": "Parser835"}
        )
        
        assert success_output.is_successful
        assert not success_output.has_errors
        assert success_output.data["transaction"] == "835"
        
        # Failed parse
        failure_output = ParseOutput(
            result=ParseResult.FAILURE,
            errors=[{"code": "PARSE_ERROR", "message": "Failed to parse"}]
        )
        
        assert not failure_output.is_successful
        assert failure_output.has_errors


class MockEnhancedParser(EnhancedParser):
    """Mock parser for testing."""
    
    def get_transaction_codes(self):
        return ["999"]
    
    def parse(self):
        # Simulate a parsing error
        segment = ["ST", "999", "0001"]
        if not self._handle_segment_error(segment, 0, "Invalid transaction code"):
            raise EDIParseError("Parsing failed")
        return {"transaction": "999"}


class TestEnhancedParser:
    """Test enhanced parser functionality."""
    
    def test_enhanced_parser_error_handling(self):
        """Test enhanced parser with error handling."""
        segments = [["ST", "999", "0001"]]
        handler = SilentErrorHandler()
        parser = MockEnhancedParser(segments, handler)
        
        result = parser.parse_with_error_handling()
        
        # Should return result despite errors
        assert result is not None
        assert handler.has_errors()
        
        error_summary = parser.get_error_summary()
        assert error_summary["total_errors"] == 1
    
    def test_enhanced_parser_strict_mode(self):
        """Test enhanced parser in strict mode."""
        segments = [["ST", "999", "0001"]]
        handler = FailFastErrorHandler()
        parser = MockEnhancedParser(segments, handler, strict_mode=True)
        
        # Should raise an error in strict mode
        with pytest.raises(EDISegmentError):
            parser.parse_with_error_handling()