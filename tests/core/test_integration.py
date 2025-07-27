"""
Integration tests for the complete EDI processing pipeline.

These tests verify that all components work together correctly:
- Parsing with error handling
- Validation integration
- Plugin architecture
- End-to-end processing
"""

import pytest
from decimal import Decimal

from packages.core.transactions.t835.parser import Parser835
from packages.core.plugins.implementations.plugin_835 import Plugin835
from packages.core.plugins.factory import GenericTransactionParserFactory
from packages.core.validation import ValidationEngine
from packages.core.validation.rules_835 import (
    Transaction835StructureRule,
    Transaction835DataValidationRule,
    Transaction835BusinessRule
)
from packages.core.validation.integration import parse_and_validate
from packages.core.errors import StandardErrorHandler, SilentErrorHandler
from packages.core.interfaces import parser_registry, ParseResult


class TestIntegration:
    """Test the complete EDI processing pipeline."""
    
    @pytest.fixture
    def valid_835_segments(self):
        """Valid 835 transaction segments."""
        return [
            ["ISA", "00", "", "00", "", "ZZ", "SENDER123", "ZZ", "RECEIVER456", "250101", "1200", "U", "00401", "000000001", "0", "P", ">"],
            ["GS", "HP", "SENDER123", "RECEIVER456", "20250101", "1200", "1", "X", "005010X221A1"],
            ["ST", "835", "0001"],
            ["BPR", "C", "1000.00", "C", "ACH", "", "", "", "", "", "", "20250101"],
            ["TRN", "1", "12345678901", "1234567890"],
            ["DTM", "405", "20250101"],
            ["N1", "PR", "EXAMPLE PAYER"],
            ["N1", "PE", "EXAMPLE PROVIDER"],
            ["REF", "TJ", "1234567890"],
            ["CLP", "CLAIM001", "1", "500.00", "450.00", "50.00", "12", "CTRL001"],
            ["CAS", "CO", "45", "25.00", "1"],
            ["CAS", "PR", "1", "25.00", "1"],
            ["SVC", "HC:99213", "200.00", "180.00"],
            ["DTM", "472", "20250101"],
            ["SVC", "HC:99214", "300.00", "270.00"],
            ["DTM", "472", "20250101"],
            ["SE", "15", "0001"],
            ["GE", "1", "1"],
            ["IEA", "1", "000000001"]
        ]
    
    @pytest.fixture
    def invalid_835_segments(self):
        """Invalid 835 transaction segments (missing required segments)."""
        return [
            ["ST", "835", "0001"],
            ["BPR", "C", "INVALID_AMOUNT", "C", "ACH"],  # Invalid amount
            ["N1", "PR", "EXAMPLE PAYER"],
            ["CLP", "CLAIM001", "1", "500.00", "450.00", "50.00"],  # Missing payer control number
            ["SE", "4", "0001"]
        ]
    
    def test_basic_parsing_integration(self, valid_835_segments):
        """Test basic parsing without error handling."""
        parser = Parser835(valid_835_segments)
        result = parser.parse()
        
        assert result is not None
        assert len(result.interchanges) == 1
        
        interchange = result.interchanges[0]
        assert interchange.sender_id == "SENDER123"
        assert interchange.receiver_id == "RECEIVER456"
        
        functional_group = interchange.functional_groups[0]
        assert functional_group.functional_group_code == "HP"
        
        transaction = functional_group.transactions[0]
        assert transaction.transaction_set_code == "835"
        
        transaction_835 = transaction.transaction_data
        assert transaction_835.financial_information.total_paid == 1000.00
        assert len(transaction_835.claims) == 1
        
        claim = transaction_835.claims[0]
        assert claim.claim_id == "CLAIM001"
        assert claim.total_charge == 500.00
        assert claim.total_paid == 450.00
        assert len(claim.services) == 2
    
    def test_enhanced_parsing_with_error_handling(self, valid_835_segments):
        """Test enhanced parsing with error handling."""
        handler = SilentErrorHandler()
        parser = Parser835(valid_835_segments, handler)
        
        result = parser.parse_with_error_handling()
        
        assert result is not None
        assert not handler.has_errors()
        
        error_summary = parser.get_error_summary()
        assert error_summary["total_errors"] == 0
    
    def test_parsing_with_errors(self, invalid_835_segments):
        """Test parsing with error handling on invalid data."""
        handler = StandardErrorHandler(log_errors=False, raise_on_error=False)
        parser = Parser835(invalid_835_segments, handler)
        
        result = parser.parse_with_error_handling()
        
        # Should still return a result (empty root) even with errors
        assert result is not None
        
        error_summary = parser.get_error_summary()
        # Should have errors due to missing required segments
        assert error_summary["total_errors"] > 0
    
    def test_plugin_integration(self, valid_835_segments):
        """Test plugin architecture integration."""
        factory = GenericTransactionParserFactory()
        plugin = Plugin835(factory)
        
        result = plugin.parse_transaction(valid_835_segments)
        
        assert result is not None
        assert plugin.can_handle_transaction("835")
        assert not plugin.can_handle_transaction("270")
        
        # Test plugin metadata
        metadata = plugin.get_metadata()
        assert metadata["name"] == "835_payment_advice"
        assert "835" in metadata["supported_transactions"]
    
    def test_validation_integration(self, valid_835_segments):
        """Test validation system integration."""
        # Parse first
        parser = Parser835(valid_835_segments)
        parsed_result = parser.parse()
        
        # Then validate
        engine = ValidationEngine()
        engine.register_rule(Transaction835StructureRule())
        engine.register_rule(Transaction835DataValidationRule())
        engine.register_rule(Transaction835BusinessRule())
        
        transaction_835 = parsed_result.interchanges[0].functional_groups[0].transactions[0].transaction_data
        validation_result = engine.validate(transaction_835)
        
        assert validation_result.is_valid
        assert len(validation_result.errors) == 0
    
    def test_parse_and_validate_integration(self, valid_835_segments):
        """Test integrated parse and validate function."""
        result = parse_and_validate(
            segments=valid_835_segments,
            transaction_code="835",
            validation_rules=["structure", "data", "business"]
        )
        
        assert result["parse_success"] is True
        assert result["validation_success"] is True
        assert result["parsed_data"] is not None
        assert len(result["validation_errors"]) == 0
    
    def test_parse_and_validate_with_errors(self, invalid_835_segments):
        """Test integrated parse and validate with invalid data."""
        result = parse_and_validate(
            segments=invalid_835_segments,
            transaction_code="835",
            validation_rules=["structure", "data"]
        )
        
        # Parse might succeed partially but validation should catch issues
        assert result["validation_success"] is False
        assert len(result["validation_errors"]) > 0
    
    def test_parser_registry_integration(self, valid_835_segments):
        """Test parser registry functionality."""
        # Register parser
        parser_registry.register_parser(["835"], Parser835)
        
        # Check registration
        assert "835" in parser_registry.get_supported_codes()
        assert parser_registry.get_parser("835") == Parser835
        
        # Create parser through registry
        parser = parser_registry.create_parser("835", valid_835_segments)
        assert parser is not None
        assert isinstance(parser, Parser835)
        
        # Test with unsupported code
        unsupported_parser = parser_registry.create_parser("999", valid_835_segments)
        assert unsupported_parser is None
    
    def test_end_to_end_processing(self, valid_835_segments):
        """Test complete end-to-end processing pipeline."""
        # Step 1: Parse with error handling
        handler = StandardErrorHandler(log_errors=False, raise_on_error=False)
        parser = Parser835(valid_835_segments, handler)
        parsed_result = parser.parse_with_error_handling()
        
        assert parsed_result is not None
        
        # Step 2: Extract transaction data
        transaction_835 = parsed_result.interchanges[0].functional_groups[0].transactions[0].transaction_data
        
        # Step 3: Validate
        engine = ValidationEngine()
        engine.register_rule(Transaction835StructureRule())
        engine.register_rule(Transaction835DataValidationRule())
        
        validation_result = engine.validate(transaction_835)
        
        # Step 4: Process business logic
        if validation_result.is_valid:
            # Extract key business data
            financial_info = transaction_835.financial_information
            claims = transaction_835.claims
            
            # Verify financial consistency
            total_claim_payments = sum(Decimal(str(claim.total_paid)) for claim in claims)
            assert abs(Decimal(str(financial_info.total_paid)) - total_claim_payments) < Decimal('0.01')
            
            # Verify claim structure
            for claim in claims:
                assert claim.claim_id
                assert claim.total_charge >= 0
                assert claim.total_paid >= 0
                assert len(claim.services) > 0
        
        # Step 5: Generate summary report
        processing_summary = {
            "parsing_successful": parsed_result is not None,
            "parsing_errors": parser.get_error_summary()["total_errors"],
            "validation_successful": validation_result.is_valid,
            "validation_errors": len(validation_result.errors),
            "claims_processed": len(transaction_835.claims),
            "total_payment": financial_info.total_paid,
            "services_processed": sum(len(claim.services) for claim in transaction_835.claims)
        }
        
        assert processing_summary["parsing_successful"]
        assert processing_summary["validation_successful"]
        assert processing_summary["claims_processed"] == 1
        assert processing_summary["services_processed"] == 2
        assert processing_summary["total_payment"] == 1000.00
    
    def test_error_recovery_scenarios(self):
        """Test error recovery in various scenarios."""
        # Scenario 1: Missing ISA segment
        segments_no_isa = [
            ["ST", "835", "0001"],
            ["BPR", "C", "1000.00", "C", "ACH"],
            ["SE", "2", "0001"]
        ]
        
        handler = SilentErrorHandler()
        parser = Parser835(segments_no_isa, handler)
        result = parser.parse_with_error_handling()
        
        # Should return empty result but not crash
        assert result is not None
        assert handler.has_errors()
        
        # Scenario 2: Invalid numeric data
        segments_invalid_numbers = [
            ["ISA", "00", "", "00", "", "ZZ", "SENDER", "ZZ", "RECEIVER", "250101", "1200", "U", "00401", "000000001", "0", "P", ">"],
            ["ST", "835", "0001"],
            ["BPR", "C", "NOT_A_NUMBER", "C", "ACH"],
            ["SE", "2", "0001"],
            ["IEA", "1", "000000001"]
        ]
        
        handler.reset()
        parser = Parser835(segments_invalid_numbers, handler)
        result = parser.parse_with_error_handling()
        
        # Should handle parsing errors gracefully
        assert result is not None