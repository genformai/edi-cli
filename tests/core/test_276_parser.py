"""
Test cases for EDI 276 (Claim Status Inquiry) Parser.

This file contains comprehensive parser tests for 276 transaction processing.
"""

import pytest
from .test_utils import parse_edi, assert_control_numbers_match


class Test276Parser:
    """Test cases for 276 parser functionality."""

    def test_parse_276_basic_claim_status_inquiry(self, schema_276_path, base_isa_segment, base_envelope_trailer):
        """Test parsing a basic 276 claim status inquiry."""
        edi_content = (
            base_isa_segment +
            "GS*HI*SENDER*RECEIVER*20241226*1430*000006789*X*005010X212~"
            "ST*276*0001~"
            "BHT*0019*13*12345*20241226*1430~"
            "HL*1**20*1~"
            "NM1*PR*2*INSURANCE COMPANY*****PI*123456789~"
            "HL*2*1*21*1~"
            "NM1*41*2*PROVIDER CLINIC*****XX*1234567890~"
            "HL*3*2*19*0~"
            "TRN*1*INQUIRY123*123456789~"
            "REF*1K*CLAIMNUMBER001~"
            "DTM*232*20241215~"
            "SE*10*0001~"
            + base_envelope_trailer
        )
        
        result = parse_edi(edi_content, schema_276_path)
        
        # Verify basic structure
        assert len(result.interchanges) == 1
        interchange = result.interchanges[0]
        assert_control_numbers_match(interchange)
        
        # Verify functional group
        assert len(interchange.functional_groups) == 1
        functional_group = interchange.functional_groups[0]
        assert functional_group.header["functional_id_code"] == "HI"
        
        # Verify transaction
        assert len(functional_group.transactions) == 1
        transaction = functional_group.transactions[0]
        assert transaction.header["transaction_set_code"] == "276"

    def test_parse_276_multiple_claim_inquiries(self, schema_276_path, base_isa_segment, base_envelope_trailer):
        """Test parsing 276 with multiple claim status inquiries."""
        edi_content = (
            base_isa_segment +
            "GS*HI*SENDER*RECEIVER*20241226*1430*000006789*X*005010X212~"
            "ST*276*0001~"
            "BHT*0019*13*12345*20241226*1430~"
            "HL*1**20*1~"
            "NM1*PR*2*INSURANCE COMPANY*****PI*123456789~"
            "HL*2*1*21*1~"
            "NM1*41*2*PROVIDER CLINIC*****XX*1234567890~"
            "HL*3*2*19*0~"
            "TRN*1*INQUIRY001*123456789~"
            "REF*1K*CLAIMNUMBER001~"
            "DTM*232*20241215~"
            "HL*4*2*19*0~"
            "TRN*1*INQUIRY002*123456789~"
            "REF*1K*CLAIMNUMBER002~"
            "DTM*232*20241216~"
            "SE*16*0001~"
            + base_envelope_trailer
        )
        
        result = parse_edi(edi_content, schema_276_path)
        
        # Verify structure
        assert len(result.interchanges) == 1
        transaction = result.interchanges[0].functional_groups[0].transactions[0]
        assert transaction.header["transaction_set_code"] == "276"

    def test_parse_276_empty_inquiry(self, schema_276_path):
        """Test 276 parser with minimal inquiry data."""
        edi_content = (
            "ISA*00*          *00*          *ZZ*SENDER         *ZZ*RECEIVER       "
            "*241226*1430*^*00501*000012345*0*P*:~"
            "GS*HI*SENDER*RECEIVER*20241226*1430*000006789*X*005010X212~"
            "ST*276*0001~"
            "BHT*0019*13*12345*20241226*1430~"
            "SE*3*0001~"
            "GE*1*000006789~"
            "IEA*1*000012345~"
        )
        
        result = parse_edi(edi_content, schema_276_path)
        
        # Should parse basic structure
        assert len(result.interchanges) == 1
        transaction = result.interchanges[0].functional_groups[0].transactions[0]
        assert transaction.header["transaction_set_code"] == "276"