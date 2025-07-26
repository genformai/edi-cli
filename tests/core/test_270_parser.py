"""
Test cases for EDI 270 (Eligibility Inquiry) Parser.

This file contains comprehensive parser tests for 270 transaction processing.
"""

import pytest
from .test_utils import parse_edi, assert_control_numbers_match
from .fixtures import EDIFixtures


class Test270Parser:
    """Test cases for 270 parser functionality."""

    def test_parse_270_basic_eligibility_inquiry(self, schema_270_path):
        """Test parsing a basic 270 eligibility inquiry."""
        edi_content = EDIFixtures.get_270_eligibility_inquiry()
        
        result = parse_edi(edi_content, schema_270_path)
        
        # Verify basic structure
        assert len(result.interchanges) == 1
        interchange = result.interchanges[0]
        assert_control_numbers_match(interchange)
        
        # Verify functional group
        assert len(interchange.functional_groups) == 1
        functional_group = interchange.functional_groups[0]
        assert functional_group.header["functional_id_code"] == "HS"
        
        # Verify transaction
        assert len(functional_group.transactions) == 1
        transaction = functional_group.transactions[0]
        assert transaction.header["transaction_set_code"] == "270"

    def test_parse_270_with_multiple_inquiries(self, schema_270_path, base_isa_segment, base_envelope_trailer):
        """Test parsing 270 with multiple eligibility inquiries."""
        edi_content = (
            base_isa_segment +
            "GS*HS*SENDER*RECEIVER*20241226*1430*000006789*X*005010X279A1~"
            "ST*270*0001~"
            "BHT*0022*13*12345*20241226*1430~"
            "HL*1**20*1~"
            "NM1*PR*2*INSURANCE COMPANY*****PI*123456789~"
            "HL*2*1*21*1~"
            "NM1*1P*2*PROVIDER CLINIC*****XX*1234567890~"
            "HL*3*2*22*0~"
            "TRN*1*INQUIRY001*123456789~"
            "NM1*IL*1*DOE*JANE*A***MI*987654321~"
            "EQ*30~"
            "HL*4*2*22*0~"
            "TRN*1*INQUIRY002*123456789~"
            "NM1*IL*1*SMITH*JOHN*B***MI*123456789~"
            "EQ*30~"
            "SE*14*0001~"
            + base_envelope_trailer
        )
        
        result = parse_edi(edi_content, schema_270_path)
        
        # Verify structure
        assert len(result.interchanges) == 1
        transaction = result.interchanges[0].functional_groups[0].transactions[0]
        assert transaction.header["transaction_set_code"] == "270"

    def test_parse_270_malformed_data(self, schema_270_path):
        """Test 270 parser with malformed data."""
        edi_content = (
            "ISA*00*          *00*          *ZZ*SENDER         *ZZ*RECEIVER       "
            "*241226*1430*^*00501*000012345*0*P*:~"
            "GS*HS*SENDER*RECEIVER*20241226*1430*000006789*X*005010X279A1~"
            "ST*270*0001~"
            "INVALID*SEGMENT~"
            "BHT*0022*13*12345*20241226*1430~"
            "SE*3*0001~"
            "GE*1*000006789~"
            "IEA*1*000012345~"
        )
        
        result = parse_edi(edi_content, schema_270_path)
        
        # Should still parse valid segments
        assert len(result.interchanges) == 1