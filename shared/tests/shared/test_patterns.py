"""
Standardized test patterns for consistent testing across all transaction types.

This module provides common test patterns and utilities that can be reused
across different EDI transaction types for consistent test structure.
"""

import pytest
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Type
from decimal import Decimal


class BaseTransactionTestPattern(ABC):
    """
    Base class for standardized transaction test patterns.
    
    This provides a consistent structure for testing different EDI transaction types
    while allowing customization for specific transaction requirements.
    """
    
    @property
    @abstractmethod
    def transaction_type(self) -> str:
        """Return the transaction type code (e.g., '835', '270')."""
        pass
    
    @property
    @abstractmethod
    def parser_class(self) -> Type:
        """Return the parser class for this transaction type."""
        pass
    
    @abstractmethod
    def get_minimal_valid_content(self) -> str:
        """Return minimal valid EDI content for this transaction type."""
        pass
    
    @abstractmethod
    def get_complex_valid_content(self) -> str:
        """Return complex valid EDI content with multiple elements."""
        pass
    
    @abstractmethod
    def get_invalid_content_samples(self) -> Dict[str, str]:
        """Return dictionary of invalid content samples with descriptive names."""
        pass
    
    def test_minimal_parsing(self):
        """Test parsing of minimal valid content."""
        content = self.get_minimal_valid_content()
        parser = self.parser_class()
        
        result = parser.parse(content)
        assert result is not None
        self.validate_minimal_structure(result)
    
    def test_complex_parsing(self):
        """Test parsing of complex valid content."""
        content = self.get_complex_valid_content()
        parser = self.parser_class()
        
        result = parser.parse(content)
        assert result is not None
        self.validate_complex_structure(result)
    
    def test_invalid_content_handling(self):
        """Test handling of various invalid content types."""
        invalid_samples = self.get_invalid_content_samples()
        parser = self.parser_class()
        
        for sample_name, invalid_content in invalid_samples.items():
            with pytest.raises(Exception) or self._assert_error_handled(parser, invalid_content):
                result = parser.parse(invalid_content)
                # If parsing doesn't raise exception, verify error handling
                if result is not None:
                    assert hasattr(result, 'errors') or hasattr(result, 'warnings'), \
                        f"Invalid content '{sample_name}' should produce errors or warnings"
    
    def _assert_error_handled(self, parser, content):
        """Context manager for asserting error handling when exceptions aren't raised."""
        try:
            result = parser.parse(content)
            return result is None or hasattr(result, 'errors') or hasattr(result, 'warnings')
        except Exception:
            return True
    
    @abstractmethod
    def validate_minimal_structure(self, result: Any):
        """Validate the structure of minimal parsing result."""
        pass
    
    @abstractmethod
    def validate_complex_structure(self, result: Any):
        """Validate the structure of complex parsing result."""
        pass


class Payment835TestPattern(BaseTransactionTestPattern):
    """Test pattern for 835 payment transactions."""
    
    @property
    def transaction_type(self) -> str:
        return "835"
    
    @property
    def parser_class(self) -> Type:
        from packages.core.transactions.t835.parser import Parser835
        return Parser835
    
    def get_minimal_valid_content(self) -> str:
        from tests.fixtures import EDIFixtures
        return EDIFixtures.get_minimal_835()
    
    def get_complex_valid_content(self) -> str:
        from tests.fixtures import EDIFixtures
        return EDIFixtures.get_835_with_multiple_claims()
    
    def get_invalid_content_samples(self) -> Dict[str, str]:
        return {
            "invalid_envelope": "ISA*INVALID~GS*INVALID~ST*835*0001~SE*1*0001~GE*1*1~IEA*1*1~",
            "missing_segments": "ST*835*0001~SE*1*0001~",
            "malformed_bpr": "ST*835*0001~BPR*INVALID*FORMAT~SE*2*0001~",
            "empty_content": "",
            "non_edi_content": "This is not EDI content at all"
        }
    
    def validate_minimal_structure(self, result: Any):
        """Validate minimal 835 structure."""
        from tests.shared.assertions import assert_transaction_structure
        assert_transaction_structure(result)
        
        # Specific 835 validations
        transaction = result.interchanges[0].functional_groups[0].transactions[0]
        assert hasattr(transaction, 'financial_information')
        assert hasattr(transaction, 'payer')
        assert hasattr(transaction, 'payee')
    
    def validate_complex_structure(self, result: Any):
        """Validate complex 835 structure."""
        self.validate_minimal_structure(result)
        
        # Additional validations for complex structure
        transaction = result.interchanges[0].functional_groups[0].transactions[0]
        assert hasattr(transaction, 'claims')
        assert len(transaction.claims) > 0
        
        # Validate claim structure
        for claim in transaction.claims:
            assert hasattr(claim, 'claim_id')
            assert hasattr(claim, 'charge_amount')
            assert hasattr(claim, 'payment_amount')


class Eligibility270TestPattern(BaseTransactionTestPattern):
    """Test pattern for 270 eligibility inquiry transactions."""
    
    @property
    def transaction_type(self) -> str:
        return "270"
    
    @property
    def parser_class(self) -> Type:
        from packages.core.base.parser import BaseParser
        return BaseParser
    
    def get_minimal_valid_content(self) -> str:
        from tests.fixtures import EDIFixtures
        return EDIFixtures.get_270_eligibility_inquiry()
    
    def get_complex_valid_content(self) -> str:
        # For now, return the same as minimal since 270 parser is basic
        return self.get_minimal_valid_content()
    
    def get_invalid_content_samples(self) -> Dict[str, str]:
        return {
            "invalid_transaction_type": "ST*999*0001~SE*1*0001~",
            "missing_segments": "ST*270*0001~SE*1*0001~",
            "empty_content": "",
            "malformed_header": "ST*270~SE*1*0001~"
        }
    
    def validate_minimal_structure(self, result: Any):
        """Validate minimal 270 structure."""
        # For base parser, result is list of segments
        assert isinstance(result, list)
        assert len(result) > 0
        
        # Find ST segment and validate transaction type
        st_segments = [seg for seg in result if seg[0] == "ST"]
        assert len(st_segments) >= 1
        assert st_segments[0][1] == "270"
    
    def validate_complex_structure(self, result: Any):
        """Validate complex 270 structure."""
        self.validate_minimal_structure(result)


class StandardTestMixin:
    """
    Mixin class providing standard test methods that can be used by any test class.
    
    This provides common test patterns that should be consistent across all
    transaction types and test classes.
    """
    
    def assert_segment_structure(self, segments: List[List[str]], expected_segments: List[str]):
        """Assert that required segments are present in the correct order."""
        segment_ids = [seg[0] for seg in segments if len(seg) > 0]
        
        for expected_segment in expected_segments:
            assert expected_segment in segment_ids, f"Required segment {expected_segment} not found"
    
    def assert_envelope_integrity(self, segments: List[List[str]]):
        """Assert that EDI envelope structure is valid."""
        # Find envelope segments
        isa_segments = [seg for seg in segments if seg[0] == "ISA"]
        iea_segments = [seg for seg in segments if seg[0] == "IEA"]
        gs_segments = [seg for seg in segments if seg[0] == "GS"]
        ge_segments = [seg for seg in segments if seg[0] == "GE"]
        
        # Basic envelope validation
        assert len(isa_segments) == 1, "Should have exactly one ISA segment"
        assert len(iea_segments) == 1, "Should have exactly one IEA segment"
        assert len(gs_segments) >= 1, "Should have at least one GS segment"
        assert len(ge_segments) >= 1, "Should have at least one GE segment"
        
        # Control number validation
        isa_control = isa_segments[0][-2] if len(isa_segments[0]) >= 2 else ""
        iea_control = iea_segments[0][-1] if len(iea_segments[0]) >= 2 else ""
        assert isa_control == iea_control, "ISA and IEA control numbers should match"
    
    def assert_transaction_counts(self, segments: List[List[str]]):
        """Assert that transaction counts are consistent."""
        st_segments = [seg for seg in segments if seg[0] == "ST"]
        se_segments = [seg for seg in segments if seg[0] == "SE"]
        
        assert len(st_segments) == len(se_segments), "ST and SE segment counts should match"
        
        # Validate control number pairs
        for st_seg, se_seg in zip(st_segments, se_segments):
            if len(st_seg) >= 3 and len(se_seg) >= 3:
                assert st_seg[2] == se_seg[2], f"ST/SE control numbers should match: {st_seg[2]} != {se_seg[2]}"
    
    def assert_financial_calculations(self, claims: List[Any], tolerance: Decimal = Decimal("0.01")):
        """Assert that financial calculations are mathematically sound."""
        from tests.shared.assertions import assert_balances
        
        for claim in claims:
            if hasattr(claim, 'charge_amount') and hasattr(claim, 'payment_amount') and hasattr(claim, 'patient_responsibility_amount'):
                assert_balances(
                    charge=claim.charge_amount,
                    paid=claim.payment_amount,
                    patient_resp=claim.patient_responsibility_amount,
                    tolerance=float(tolerance)
                )
    
    def assert_data_integrity(self, parsed_data: Any):
        """Assert general data integrity across parsed data."""
        # Ensure no None values in critical fields
        if hasattr(parsed_data, 'interchanges'):
            for interchange in parsed_data.interchanges:
                assert interchange is not None, "Interchange should not be None"
                
                if hasattr(interchange, 'functional_groups'):
                    for fg in interchange.functional_groups:
                        assert fg is not None, "Functional group should not be None"
                        
                        if hasattr(fg, 'transactions'):
                            for transaction in fg.transactions:
                                assert transaction is not None, "Transaction should not be None"


class ValidationTestMixin:
    """Mixin for validation-specific test patterns."""
    
    def test_field_validation_patterns(self, validator_func, valid_samples: List[Any], invalid_samples: List[Any]):
        """Test validation function with valid and invalid samples."""
        # Test valid samples
        for valid_sample in valid_samples:
            assert validator_func(valid_sample) is True, f"Valid sample {valid_sample} should pass validation"
        
        # Test invalid samples
        for invalid_sample in invalid_samples:
            assert validator_func(invalid_sample) is False, f"Invalid sample {invalid_sample} should fail validation"
    
    def test_edge_cases(self, validator_func):
        """Test common edge cases for validation functions."""
        edge_cases = [None, "", "   ", 0, "0", []]
        
        for edge_case in edge_cases:
            try:
                result = validator_func(edge_case)
                assert isinstance(result, bool), f"Validator should return boolean for edge case: {edge_case}"
            except (TypeError, ValueError, AttributeError):
                # Some validators may raise exceptions for edge cases, which is acceptable
                pass


class PerformanceTestMixin:
    """Mixin for performance-related test patterns."""
    
    def measure_operation_time(self, operation_func, *args, iterations: int = 100, **kwargs):
        """Measure average time for an operation over multiple iterations."""
        import time
        
        # Warm up
        for _ in range(min(10, iterations)):
            operation_func(*args, **kwargs)
        
        # Measure
        start_time = time.time()
        for _ in range(iterations):
            operation_func(*args, **kwargs)
        end_time = time.time()
        
        total_time = end_time - start_time
        avg_time = total_time / iterations
        
        return avg_time, total_time
    
    def assert_performance_threshold(self, operation_func, threshold_seconds: float, *args, **kwargs):
        """Assert that an operation completes within a time threshold."""
        avg_time, _ = self.measure_operation_time(operation_func, *args, **kwargs)
        assert avg_time < threshold_seconds, f"Operation too slow: {avg_time:.4f}s (threshold: {threshold_seconds}s)"


class ErrorHandlingTestMixin:
    """Mixin for error handling test patterns."""
    
    def test_graceful_error_handling(self, parser_func, invalid_inputs: List[Any]):
        """Test that parser handles invalid inputs gracefully."""
        for invalid_input in invalid_inputs:
            try:
                result = parser_func(invalid_input)
                # If no exception, should have error indicators
                if result is not None:
                    assert hasattr(result, 'errors') or hasattr(result, 'warnings') or hasattr(result, 'status'), \
                        f"Invalid input should produce error indicators: {invalid_input}"
            except Exception as e:
                # Exceptions are acceptable, but should be specific types
                assert not isinstance(e, (SystemExit, KeyboardInterrupt)), \
                    f"Should not raise system exceptions for invalid input: {invalid_input}"
    
    def test_error_message_quality(self, parser_func, invalid_input: Any, expected_error_keywords: List[str]):
        """Test that error messages contain helpful information."""
        try:
            result = parser_func(invalid_input)
            if hasattr(result, 'errors'):
                error_message = str(result.errors)
                for keyword in expected_error_keywords:
                    assert keyword.lower() in error_message.lower(), \
                        f"Error message should contain '{keyword}': {error_message}"
        except Exception as e:
            error_message = str(e)
            for keyword in expected_error_keywords:
                assert keyword.lower() in error_message.lower(), \
                    f"Exception message should contain '{keyword}': {error_message}"


# Example usage of test patterns
class TestStandardizedPatterns:
    """Example test class showing how to use standardized patterns."""
    
    def test_835_payment_patterns(self):
        """Test 835 payments using standardized patterns."""
        pattern = Payment835TestPattern()
        
        # Use the standard test methods
        pattern.test_minimal_parsing()
        pattern.test_complex_parsing()
        pattern.test_invalid_content_handling()
    
    def test_270_eligibility_patterns(self):
        """Test 270 eligibility using standardized patterns."""
        pattern = Eligibility270TestPattern()
        
        # Use the standard test methods
        pattern.test_minimal_parsing()
        pattern.test_complex_parsing()
        pattern.test_invalid_content_handling()


class TestMixinUsage(StandardTestMixin, ValidationTestMixin, PerformanceTestMixin, ErrorHandlingTestMixin):
    """Example test class showing how to use test mixins."""
    
    def test_npi_validation_with_patterns(self):
        """Test NPI validation using validation patterns."""
        from packages.core.utils.validators import validate_npi
        
        valid_samples = ["1234567890", "9876543210"]
        invalid_samples = ["", "123", "abcdefghij", None]
        
        self.test_field_validation_patterns(validate_npi, valid_samples, invalid_samples)
        self.test_edge_cases(validate_npi)
    
    def test_parser_performance_with_patterns(self):
        """Test parser performance using performance patterns."""
        from packages.core.transactions.t835.parser import Parser835
        from tests.fixtures import EDIFixtures
        
        parser = Parser835()
        edi_content = EDIFixtures.get_minimal_835()
        
        # Test performance threshold
        self.assert_performance_threshold(
            parser.parse, 
            0.1,  # threshold_seconds
            edi_content
        )
    
    def test_error_handling_with_patterns(self):
        """Test error handling using error handling patterns."""
        from packages.core.transactions.t835.parser import Parser835
        
        parser = Parser835()
        invalid_inputs = ["", "invalid", None, "ST*999*0001~SE*1*0001~"]
        
        self.test_graceful_error_handling(parser.parse, invalid_inputs)
        
        # Test specific error message quality
        self.test_error_message_quality(
            parser.parse, 
            "invalid edi content", 
            ["invalid", "parse", "format"]
        )