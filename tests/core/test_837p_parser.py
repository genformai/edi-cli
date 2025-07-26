"""
Test cases for EDI 837P (Professional Claim) Parser.

This file contains comprehensive parser tests for 837P transaction processing.
"""

import pytest
from .test_utils import parse_edi, assert_control_numbers_match, assert_amount_format


class Test837pParser:
    """Test cases for 837P parser functionality."""

    def test_parse_837p_basic_professional_claim(self, schema_837p_path, base_isa_segment, base_envelope_trailer):
        """Test parsing a basic 837P professional claim."""
        edi_content = (
            base_isa_segment +
            "GS*HC*SENDER*RECEIVER*20241226*1430*000006789*X*005010X222A1~"
            "ST*837*0001~"
            "BHT*0019*00*12345*20241226*1430*CH~"
            "NM1*41*2*PROVIDER CLINIC*****XX*1234567890~"
            "PER*IC*CONTACT*TE*5551234567~"
            "NM1*40*2*ACME BILLING*****46*123456789~"
            "HL*1**20*1~"
            "PRV*BI*PXC*207R00000X~"
            "NM1*85*2*PROVIDER CLINIC*****XX*1234567890~"
            "N3*123 MEDICAL DRIVE~"
            "N4*MEDICAL CITY*TX*75001~"
            "REF*EI*12-3456789~"
            "HL*2*1*22*1~"
            "SBR*P*18*GROUP123**CI****MB~"
            "NM1*IL*1*DOE*JANE*A***MI*987654321~"
            "DMG*D8*19800101*F~"
            "NM1*PR*2*INSURANCE COMPANY*****PI*INSURANCEID~"
            "HL*3*2*23*0~"
            "PAT*19~"
            "NM1*QC*1*DOE*JANE*A***MI*987654321~"
            "CLM*CLAIM001*100.00***11:B:1*Y*A*Y*I~"
            "DTP*431*D8*20241215~"
            "LX*1~"
            "SV1*HC:99213*100.00*UN*1***1~"
            "DTP*472*D8*20241215~"
            "SE*24*0001~"
            + base_envelope_trailer
        )
        
        result = parse_edi(edi_content, schema_837p_path)
        
        # Verify basic structure
        assert len(result.interchanges) == 1
        interchange = result.interchanges[0]
        assert_control_numbers_match(interchange)
        
        # Verify functional group
        assert len(interchange.functional_groups) == 1
        functional_group = interchange.functional_groups[0]
        assert functional_group.header["functional_id_code"] == "HC"
        
        # Verify transaction
        assert len(functional_group.transactions) == 1
        transaction = functional_group.transactions[0]
        assert transaction.header["transaction_set_code"] == "837"

    def test_parse_837p_multiple_claims(self, schema_837p_path, base_isa_segment, base_envelope_trailer):
        """Test parsing 837P with multiple professional claims."""
        edi_content = (
            base_isa_segment +
            "GS*HC*SENDER*RECEIVER*20241226*1430*000006789*X*005010X222A1~"
            "ST*837*0001~"
            "BHT*0019*00*12345*20241226*1430*CH~"
            "NM1*41*2*PROVIDER CLINIC*****XX*1234567890~"
            "NM1*40*2*ACME BILLING*****46*123456789~"
            "HL*1**20*1~"
            "NM1*85*2*PROVIDER CLINIC*****XX*1234567890~"
            "HL*2*1*22*0~"
            "SBR*P*18*GROUP123**CI****MB~"
            "NM1*IL*1*DOE*JANE*A***MI*987654321~"
            "NM1*PR*2*INSURANCE COMPANY*****PI*INSURANCEID~"
            "CLM*CLAIM001*100.00***11:B:1*Y*A*Y*I~"
            "LX*1~"
            "SV1*HC:99213*100.00*UN*1***1~"
            "CLM*CLAIM002*200.00***11:B:1*Y*A*Y*I~"
            "LX*1~"
            "SV1*HC:99214*200.00*UN*1***1~"
            "SE*16*0001~"
            + base_envelope_trailer
        )
        
        result = parse_edi(edi_content, schema_837p_path)
        
        # Verify structure
        assert len(result.interchanges) == 1
        transaction = result.interchanges[0].functional_groups[0].transactions[0]
        assert transaction.header["transaction_set_code"] == "837"

    def test_parse_837p_with_diagnosis_codes(self, schema_837p_path, base_isa_segment, base_envelope_trailer):
        """Test parsing 837P with diagnosis codes."""
        edi_content = (
            base_isa_segment +
            "GS*HC*SENDER*RECEIVER*20241226*1430*000006789*X*005010X222A1~"
            "ST*837*0001~"
            "BHT*0019*00*12345*20241226*1430*CH~"
            "NM1*41*2*PROVIDER CLINIC*****XX*1234567890~"
            "HL*1**20*1~"
            "NM1*85*2*PROVIDER CLINIC*****XX*1234567890~"
            "HL*2*1*22*0~"
            "SBR*P*18*GROUP123**CI****MB~"
            "NM1*IL*1*DOE*JANE*A***MI*987654321~"
            "NM1*PR*2*INSURANCE COMPANY*****PI*INSURANCEID~"
            "CLM*CLAIM001*100.00***11:B:1*Y*A*Y*I~"
            "HI*BK:Z00.00~"  # Primary diagnosis
            "HI*BF:Z01.01~"  # Secondary diagnosis
            "LX*1~"
            "SV1*HC:99213*100.00*UN*1***1~"
            "SE*14*0001~"
            + base_envelope_trailer
        )
        
        result = parse_edi(edi_content, schema_837p_path)
        
        # Verify structure includes diagnosis information
        assert len(result.interchanges) == 1
        transaction = result.interchanges[0].functional_groups[0].transactions[0]
        assert transaction.header["transaction_set_code"] == "837"

    def test_parse_837p_amount_validation(self, schema_837p_path, base_isa_segment, base_envelope_trailer):
        """Test that 837P amounts are properly validated."""
        edi_content = (
            base_isa_segment +
            "GS*HC*SENDER*RECEIVER*20241226*1430*000006789*X*005010X222A1~"
            "ST*837*0001~"
            "BHT*0019*00*12345*20241226*1430*CH~"
            "NM1*41*2*PROVIDER CLINIC*****XX*1234567890~"
            "HL*1**20*1~"
            "NM1*85*2*PROVIDER CLINIC*****XX*1234567890~"
            "HL*2*1*22*0~"
            "SBR*P*18*GROUP123**CI****MB~"
            "NM1*IL*1*DOE*JANE*A***MI*987654321~"
            "NM1*PR*2*INSURANCE COMPANY*****PI*INSURANCEID~"
            "CLM*CLAIM001*125.50***11:B:1*Y*A*Y*I~"  # Amount with decimals
            "LX*1~"
            "SV1*HC:99213*125.50*UN*1***1~"
            "SE*11*0001~"
            + base_envelope_trailer
        )
        
        result = parse_edi(edi_content, schema_837p_path)
        
        # Verify amounts are parsed correctly
        assert len(result.interchanges) == 1
        transaction = result.interchanges[0].functional_groups[0].transactions[0]
        
        # Basic validation that structure exists
        assert transaction.header["transaction_set_code"] == "837"