"""
Test cases for EDI 835 (Electronic Remittance Advice) Parser.

This file contains comprehensive parser tests for 835 transaction processing.
"""

import pytest
import json
from .test_utils import parse_edi, assert_date_format, assert_amount_format
from .fixtures import EDIFixtures


class Test835Parser:
    """Test cases for 835 parser functionality."""

    def test_parse_835_edi_file(self, edi_835_file, edi_835_json_file, schema_835_path):
        """Test parsing a complete 835 EDI file with all standard segments."""
        with open(edi_835_file, 'r') as f:
            edi_content = f.read()
        
        result = parse_edi(edi_content, schema_835_path)
        
        # Verify basic structure
        assert len(result.interchanges) == 1
        interchange = result.interchanges[0]
        assert len(interchange.functional_groups) == 1
        functional_group = interchange.functional_groups[0]
        assert len(functional_group.transactions) >= 1

    def test_parse_835_minimal(self, schema_835_path):
        """Test parsing a minimal 835 EDI file with only required segments."""
        edi_content = EDIFixtures.get_minimal_835()
        
        result = parse_edi(edi_content, schema_835_path)
        
        # Verify basic structure
        assert len(result.interchanges) == 1
        interchange = result.interchanges[0]
        assert len(interchange.functional_groups) == 1
        functional_group = interchange.functional_groups[0]
        assert len(functional_group.transactions) == 1
        
        # Verify transaction has required elements
        transaction = functional_group.transactions[0]
        assert transaction.header["transaction_set_code"] == "835"
        assert transaction.financial_transaction is not None

    def test_parse_835_multiple_claims(self, schema_835_path):
        """Test parsing an 835 EDI file with multiple claims and adjustments."""
        edi_content = EDIFixtures.get_835_with_multiple_claims()
        
        result = parse_edi(edi_content, schema_835_path)
        
        # Verify structure
        transaction = result.interchanges[0].functional_groups[0].transactions[0]
        financial_tx = transaction.financial_transaction
        
        # Verify multiple claims
        assert len(financial_tx.claims) == 3
        
        # Verify claims have expected data
        for claim in financial_tx.claims:
            assert claim.claim_id is not None
            assert claim.status_code is not None
            assert claim.total_charge >= 0
            assert_amount_format(claim.total_charge)

    def test_parse_835_no_payer_payee(self, schema_835_path, base_835_headers, base_835_trailer):
        """Test parsing an 835 EDI file without payer/payee information."""
        # Create EDI without N1 segments
        edi_content = (
            base_835_headers +
            "CLP*CLAIM001*1*1200.00*1000.00*200.00*MC*456789*11~"
            + base_835_trailer.replace("{{segment_count}}", "8")
        )
        
        result = parse_edi(edi_content, schema_835_path)
        
        # Verify structure still parses
        assert len(result.interchanges) == 1
        transaction = result.interchanges[0].functional_groups[0].transactions[0]
        financial_tx = transaction.financial_transaction
        
        # Should have claims even without payer/payee
        assert len(financial_tx.claims) == 1

    def test_parser_handles_empty_string(self, schema_835_path):
        """Test that parser handles empty EDI content gracefully."""
        result = parse_edi("", schema_835_path)
        
        expected = {
            "interchanges": []
        }
        
        # Should return empty structure
        assert len(result.interchanges) == 0

    def test_parser_handles_malformed_segments(self, schema_835_path):
        """Test parser behavior with malformed segments."""
        edi_content = (
            "ISA*00*          *00*          *ZZ*SENDER         *ZZ*RECEIVER       "
            "*241226*1430*^*00501*000012345*0*P*:~"
            "INVALID_SEGMENT~"
            "GS*HP*SENDER*RECEIVER*20241226*1430*000006789*X*005010X221A1~"
            "ST*835*0001~"
            "BPR*I*1000.00*C*ACH*CCP*01*123456789*DA*987654321*9876543210*20241226~"
            "SE*2*0001~"
            "GE*1*000006789~"
            "IEA*1*000012345~"
        )
        
        result = parse_edi(edi_content, schema_835_path)
        
        # Should still parse the valid ISA segment
        assert len(result.interchanges) == 1
        assert result.interchanges[0].header["sender_id"] == "SENDER"

    def test_numeric_formatting(self, schema_835_path):
        """Test that numeric values are properly formatted as integers when whole numbers."""
        edi_content = EDIFixtures.get_minimal_835()
        
        result = parse_edi(edi_content, schema_835_path)
        
        # Verify structure and check numeric formatting
        transaction = result.interchanges[0].functional_groups[0].transactions[0]
        financial_tx = transaction.financial_transaction
        
        # Check that amounts are properly formatted
        if hasattr(financial_tx, 'financial_information'):
            payment_amount = financial_tx.financial_information.total_paid
            assert_amount_format(payment_amount)
        
        # Check claim amounts
        if financial_tx.claims:
            for claim in financial_tx.claims:
                assert_amount_format(claim.total_charge)
                assert_amount_format(claim.total_paid)
                if claim.patient_responsibility is not None:
                    assert_amount_format(claim.patient_responsibility)

    def test_date_formatting(self, schema_835_path, base_835_headers, base_835_trailer):
        """Test that dates are properly formatted from EDI format to ISO format."""
        segments = [
            "DTM*405*20241215~",  # Payment effective date
            "CLP*CLAIM001*1*1200.00*1000.00*200.00*MC*456789*11~"
        ]
        
        edi_content = (
            base_835_headers +
            "".join(segments) +
            base_835_trailer.replace("{{segment_count}}", "9")
        )
        
        result = parse_edi(edi_content, schema_835_path)
        
        # Check ISA date formatting (should be YYYY-MM-DD)
        interchange = result.interchanges[0]
        if "date" in interchange.header:
            assert_date_format(interchange.header["date"])
        
        # Check GS date formatting (should be YYYY-MM-DD)  
        functional_group = interchange.functional_groups[0]
        if "date" in functional_group.header:
            assert_date_format(functional_group.header["date"])
        
        # Check DTM date formatting
        transaction = functional_group.transactions[0]
        if hasattr(transaction, 'dates') and transaction.dates:
            for date_info in transaction.dates:
                if "date" in date_info:
                    assert_date_format(date_info["date"])

    def test_multiple_reference_numbers(self, schema_835_path, base_835_headers, base_835_trailer):
        """Test parsing multiple TRN segments."""
        segments = [
            "TRN*1*TRACE001*REF001~",
            "TRN*1*TRACE002*REF002~",
            "CLP*CLAIM001*1*1200.00*1000.00*200.00*MC*456789*11~"
        ]
        
        edi_content = (
            base_835_headers +
            "".join(segments) +
            base_835_trailer.replace("{{segment_count}}", "10")
        )
        
        result = parse_edi(edi_content, schema_835_path)
        
        transaction = result.interchanges[0].functional_groups[0].transactions[0]
        financial_tx = transaction.financial_transaction
        
        # Should have multiple reference numbers
        if hasattr(financial_tx, 'reference_numbers'):
            trace_refs = [ref for ref in financial_tx.reference_numbers 
                         if ref.get("type") == "trace_number"]
            assert len(trace_refs) >= 2

    def test_parser_performance_large_file(self, schema_835_path):
        """Test parser performance with larger EDI files."""
        # Create a larger EDI file with multiple claims
        base_edi = (
            "ISA*00*          *00*          *ZZ*SENDER         *ZZ*RECEIVER       "
            "*241226*1430*^*00501*000012345*0*P*:~"
            "GS*HP*SENDER*RECEIVER*20241226*1430*000006789*X*005010X221A1~"
            "ST*835*0001~"
            "BPR*I*5000.00*C*ACH*CCP*01*123456789*DA*987654321*9876543210*20241226~"
            "TRN*1*12345*1234567890~"
            "N1*PR*INSURANCE COMPANY~"
            "N1*PE*PROVIDER NAME~"
            "REF*TJ*1234567890~"
        )
        
        # Add 50 claims
        claims = []
        for i in range(50):
            claims.append(f"CLP*CLAIM{i:03d}*1*100.00*80.00*20.00*MC*PAYER{i:03d}*11~")
            claims.append(f"NM1*QC*1*PATIENT{i:03d}*FIRST*A***MI*{i:09d}~")
            claims.append("CAS*PR*1*15.00~")
            claims.append("CAS*CO*45*5.00~")
        
        edi_content = (
            base_edi +
            "".join(claims) +
            f"SE*{4 + len(claims)}*0001~"
            "GE*1*000006789~"
            "IEA*1*000012345~"
        )
        
        result = parse_edi(edi_content, schema_835_path)
        
        # Verify all claims were parsed
        transaction = result.interchanges[0].functional_groups[0].transactions[0]
        financial_tx = transaction.financial_transaction
        
        assert len(financial_tx.claims) == 50
        
        # Verify first and last claims
        first_claim = financial_tx.claims[0]
        assert first_claim.claim_id == "CLAIM000"
        
        last_claim = financial_tx.claims[-1]
        assert last_claim.claim_id == "CLAIM049"

    def test_parser_error_recovery(self, schema_835_path):
        """Test parser error recovery with partially corrupted data."""
        edi_content = (
            "ISA*00*          *00*          *ZZ*SENDER         *ZZ*RECEIVER       "
            "*241226*1430*^*00501*000012345*0*P*:~"
            "GS*HP*SENDER*RECEIVER*20241226*1430*000006789*X*005010X221A1~"
            "ST*835*0001~"
            "BPR*I*1000.00*C*ACH*CCP*01*123456789*DA*987654321*9876543210*20241226~"
            "TRN*1*12345*1234567890~"
            "CORRUPTED*SEGMENT*WITH*TOO*MANY*ELEMENTS*AND*INVALID*DATA*STRUCTURE~"
            "N1*PR*INSURANCE COMPANY~"
            "N1*PE*PROVIDER NAME~"
            "REF*TJ*1234567890~"
            "CLP*CLAIM001*1*1200.00*1000.00*200.00*MC*456789*11~"
            "SE*9*0001~"
            "GE*1*000006789~"
            "IEA*1*000012345~"
        )
        
        result = parse_edi(edi_content, schema_835_path)
        
        # Should still parse valid segments despite corruption
        assert len(result.interchanges) == 1
        transaction = result.interchanges[0].functional_groups[0].transactions[0]
        assert transaction.financial_transaction is not None

    def test_parser_segment_order_tolerance(self, schema_835_path):
        """Test parser tolerance for segment order variations."""
        edi_content = (
            "ISA*00*          *00*          *ZZ*SENDER         *ZZ*RECEIVER       "
            "*241226*1430*^*00501*000012345*0*P*:~"
            "GS*HP*SENDER*RECEIVER*20241226*1430*000006789*X*005010X221A1~"
            "ST*835*0001~"
            "BPR*I*1000.00*C*ACH*CCP*01*123456789*DA*987654321*9876543210*20241226~"
            # N1 segments in different order than typical
            "N1*PE*PROVIDER NAME*XX*1234567890~"
            "REF*TJ*1234567890~"
            "N1*PR*INSURANCE COMPANY~"
            "TRN*1*12345*1234567890~"  # TRN after N1 segments
            "CLP*CLAIM001*1*1200.00*1000.00*200.00*MC*456789*11~"
            "SE*8*0001~"
            "GE*1*000006789~"
            "IEA*1*000012345~"
        )
        
        result = parse_edi(edi_content, schema_835_path)
        
        # Should parse successfully despite non-standard order
        assert len(result.interchanges) == 1
        transaction = result.interchanges[0].functional_groups[0].transactions[0]
        financial_tx = transaction.financial_transaction
        
        # Verify key elements are present
        assert financial_tx.payer is not None
        assert financial_tx.payee is not None
        assert len(financial_tx.claims) == 1