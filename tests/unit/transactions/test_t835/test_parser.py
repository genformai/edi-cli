"""
Unit tests for EDI 835 (Electronic Remittance Advice) Parser.

This module contains comprehensive parser tests for 835 transaction processing,
migrated and consolidated from the original test structure.
"""

import pytest
from packages.core.transactions.t835.parser import Parser835
from packages.core.base.edi_ast import EdiRoot
from tests.shared.assertions import (
    assert_date_format, 
    assert_amount_format, 
    assert_segment_structure
)
from tests.core.fixtures.builders.builder_835 import EDI835Builder


class Test835Parser:
    """Test cases for 835 parser functionality."""

    @pytest.fixture
    def parser_835(self):
        """Fixture providing a 835 parser instance."""
        def _create_parser(segments):
            return Parser835(segments)
        return _create_parser

    @pytest.fixture
    def minimal_835_segments(self):
        """Fixture providing minimal valid 835 segments."""
        return [
            ["ISA", "00", "", "00", "", "ZZ", "SENDER", "ZZ", "RECEIVER", "241226", "1430", "U", "00501", "000000001", "0", "P", ">"],
            ["GS", "HP", "SENDER", "RECEIVER", "20241226", "1430", "000000001", "X", "005010X221A1"],
            ["ST", "835", "0001"],
            ["BPR", "I", "1000.00", "C", "ACH", "", "", "", "", "", "", "20241226"],
            ["TRN", "1", "TRACE123", "1"],
            ["SE", "5", "0001"],
            ["GE", "1", "000000001"],
            ["IEA", "1", "000000001"]
        ]

    def test_parse_minimal_835(self, parser_835, minimal_835_segments):
        """Test parsing a minimal 835 EDI transaction."""
        parser = parser_835(minimal_835_segments)
        result = parser.parse()
        
        # Verify basic structure
        assert isinstance(result, EdiRoot)
        assert len(result.interchanges) == 1
        
        interchange = result.interchanges[0]
        assert interchange.sender_id == "SENDER"
        assert interchange.receiver_id == "RECEIVER"
        assert_date_format(interchange.date)
        
        # Verify functional group
        assert len(interchange.functional_groups) == 1
        functional_group = interchange.functional_groups[0]
        assert functional_group.functional_group_code == "HP"
        
        # Verify transaction
        assert len(functional_group.transactions) == 1
        transaction = functional_group.transactions[0]
        assert transaction.transaction_set_code == "835"
        assert transaction.control_number == "0001"

    def test_parse_835_with_financial_info(self, parser_835):
        """Test parsing 835 with financial information (BPR segment)."""
        segments = [
            ["ISA", "00", "", "00", "", "ZZ", "SENDER", "ZZ", "RECEIVER", "241226", "1430", "U", "00501", "000000001", "0", "P", ">"],
            ["GS", "HP", "SENDER", "RECEIVER", "20241226", "1430", "000000001", "X", "005010X221A1"],
            ["ST", "835", "0001"],
            ["BPR", "I", "1500.75", "C", "ACH", "", "", "", "", "", "", "20241227"],
            ["TRN", "1", "TRACE456", "1"],
            ["DTM", "405", "20241226"],
            ["SE", "6", "0001"],
            ["GE", "1", "000000001"],
            ["IEA", "1", "000000001"]
        ]
        
        parser = parser_835(segments)
        result = parser.parse()
        
        # Verify financial information
        transaction = result.interchanges[0].functional_groups[0].transactions[0]
        financial_transaction = transaction.financial_transaction
        
        assert financial_transaction is not None
        financial_info = financial_transaction.financial_information
        assert financial_info is not None
        assert financial_info.total_paid == 1500.75
        assert financial_info.payment_method == "ACH"
        assert_date_format(financial_info.payment_date)

    def test_parse_835_with_payer_payee(self, parser_835):
        """Test parsing 835 with payer and payee information."""
        segments = [
            ["ISA", "00", "", "00", "", "ZZ", "SENDER", "ZZ", "RECEIVER", "241226", "1430", "U", "00501", "000000001", "0", "P", ">"],
            ["GS", "HP", "SENDER", "RECEIVER", "20241226", "1430", "000000001", "X", "005010X221A1"],
            ["ST", "835", "0001"],
            ["BPR", "I", "1000.00", "C", "ACH", "", "", "", "", "", "", "20241226"],
            ["TRN", "1", "TRACE123", "1"],
            ["N1", "PR", "TEST PAYER", "", "PI", "12345"],
            ["N1", "PE", "TEST PROVIDER", "", "XX", "1234567890"],
            ["REF", "TJ", "1234567890"],
            ["SE", "8", "0001"],
            ["GE", "1", "000000001"],
            ["IEA", "1", "000000001"]
        ]
        
        parser = parser_835(segments)
        result = parser.parse()
        
        # Verify payer/payee information
        financial_transaction = result.interchanges[0].functional_groups[0].transactions[0].financial_transaction
        
        assert financial_transaction.payer is not None
        assert financial_transaction.payer.name == "TEST PAYER"
        
        assert financial_transaction.payee is not None
        assert financial_transaction.payee.name == "TEST PROVIDER"
        assert financial_transaction.payee.npi == "1234567890"

    def test_parse_835_with_claims(self, parser_835):
        """Test parsing 835 with claim information."""
        segments = [
            ["ISA", "00", "", "00", "", "ZZ", "SENDER", "ZZ", "RECEIVER", "241226", "1430", "U", "00501", "000000001", "0", "P", ">"],
            ["GS", "HP", "SENDER", "RECEIVER", "20241226", "1430", "000000001", "X", "005010X221A1"],
            ["ST", "835", "0001"],
            ["BPR", "I", "1000.00", "C", "ACH", "", "", "", "", "", "", "20241226"],
            ["TRN", "1", "TRACE123", "1"],
            ["CLP", "CLAIM001", "1", "500.00", "400.00", "100.00", "MC", "PAYER123", "11"],
            ["NM1", "QC", "1", "DOE", "JOHN", "", "", "", "MI", "MEMBER123"],
            ["DTM", "232", "20241215"],
            ["CAS", "PR", "1", "50.00"],
            ["CAS", "CO", "45", "50.00"],
            ["SE", "10", "0001"],
            ["GE", "1", "000000001"],
            ["IEA", "1", "000000001"]
        ]
        
        parser = parser_835(segments)
        result = parser.parse()
        
        # Verify claim information
        financial_transaction = result.interchanges[0].functional_groups[0].transactions[0].financial_transaction
        
        assert len(financial_transaction.claims) == 1
        claim = financial_transaction.claims[0]
        
        assert claim.claim_id == "CLAIM001"
        assert claim.status_code == 1
        assert claim.total_charge == 500.00
        assert claim.total_paid == 400.00
        assert claim.patient_responsibility == 100.00
        assert claim.payer_control_number == "PAYER123"
        
        # Verify adjustments
        assert len(claim.adjustments) == 2
        assert claim.adjustments[0].group_code == "PR"
        assert claim.adjustments[0].reason_code == "1"
        assert claim.adjustments[0].amount == 50.00
        
        assert claim.adjustments[1].group_code == "CO"
        assert claim.adjustments[1].reason_code == "45"
        assert claim.adjustments[1].amount == 50.00

    def test_parse_835_with_services(self, parser_835):
        """Test parsing 835 with service line information."""
        segments = [
            ["ISA", "00", "", "00", "", "ZZ", "SENDER", "ZZ", "RECEIVER", "241226", "1430", "U", "00501", "000000001", "0", "P", ">"],
            ["GS", "HP", "SENDER", "RECEIVER", "20241226", "1430", "000000001", "X", "005010X221A1"],
            ["ST", "835", "0001"],
            ["BPR", "I", "1000.00", "C", "ACH", "", "", "", "", "", "", "20241226"],
            ["TRN", "1", "TRACE123", "1"],
            ["CLP", "CLAIM001", "1", "500.00", "400.00", "100.00", "MC", "PAYER123", "11"],
            ["SVC", "HC:99213", "250.00", "200.00", "", "1"],
            ["DTM", "472", "20241215"],
            ["SVC", "HC:85025", "250.00", "200.00", "", "1"],
            ["DTM", "472", "20241215"],
            ["SE", "10", "0001"],
            ["GE", "1", "000000001"],
            ["IEA", "1", "000000001"]
        ]
        
        parser = parser_835(segments)
        result = parser.parse()
        
        # Verify service information
        financial_transaction = result.interchanges[0].functional_groups[0].transactions[0].financial_transaction
        claim = financial_transaction.claims[0]
        
        assert len(claim.services) == 2
        
        service1 = claim.services[0]
        assert service1.service_code == "HC:99213"
        assert service1.charge_amount == 250.00
        assert service1.paid_amount == 200.00
        assert_date_format(service1.service_date)
        
        service2 = claim.services[1]
        assert service2.service_code == "HC:85025"
        assert service2.charge_amount == 250.00
        assert service2.paid_amount == 200.00
        assert_date_format(service2.service_date)

    def test_parse_835_invalid_segments(self, parser_835):
        """Test parsing 835 with invalid or missing segments."""
        # Test with empty segments
        with pytest.raises(ValueError):
            parser = parser_835([])
            parser.parse()
        
        # Test with malformed segments
        invalid_segments = [
            ["ISA"],  # Incomplete ISA
            ["ST", "835"],  # Incomplete ST
        ]
        
        with pytest.raises(ValueError):
            parser = parser_835(invalid_segments)
            parser.parse()

    def test_get_transaction_codes(self, parser_835):
        """Test that parser returns correct transaction codes."""
        parser = parser_835([])
        codes = parser.get_transaction_codes()
        assert codes == ["835"]

    def test_validate_segments(self, parser_835, minimal_835_segments):
        """Test segment validation."""
        parser = parser_835(minimal_835_segments)
        
        # Valid segments should pass
        assert parser.validate_segments(minimal_835_segments) is True
        
        # Invalid segments should fail
        invalid_segments = [
            ["ST", "270", "0001"]  # Wrong transaction code
        ]
        assert parser.validate_segments(invalid_segments) is False