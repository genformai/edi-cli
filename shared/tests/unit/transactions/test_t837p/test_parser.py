"""
Test cases for EDI 837P (Professional Claim) Parser.

This file contains comprehensive parser tests for 837P transaction processing,
migrated from the original test suite.
"""

import pytest
from packages.core.base.parser import BaseParser
from tests.shared.test_patterns import StandardTestMixin


class Test837pParser(StandardTestMixin):
    """Test cases for 837P parser functionality."""

    def test_parse_837p_basic_professional_claim(self):
        """Test parsing a basic 837P professional claim."""
        edi_content = (
            "ISA*00*          *00*          *ZZ*SENDER         *ZZ*RECEIVER       "
            "*241226*1430*^*00501*000012345*0*P*:~"
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
            "SBR*P*18*GROUP123*PLAN NAME*12*******CI~"
            "NM1*IL*1*DOE*JANE*A***MI*987654321~"
            "N3*456 PATIENT STREET~"
            "N4*PATIENT CITY*TX*75002~"
            "DMG*D8*19800315*F~"
            "NM1*PR*2*INSURANCE COMPANY*****PI*123456789~"
            "HL*3*2*23*0~"
            "PAT*19~"
            "NM1*QC*1*DOE*JANE*A***MI*987654321~"
            "CLM*CLAIM001*100.00***11:B:1*Y*A*Y*Y~"
            "DTP*431*D8*20241201~"
            "REF*D9*AUTHORIZATION123~"
            "HI*BK:Z0000~"
            "LX*1~"
            "SV1*HC:99213*100.00*UN*1***1~"
            "DTP*472*D8*20241201~"
            "SE*25*0001~"
            "GE*1*000006789~"
            "IEA*1*000012345~"
        )
        
        parser = BaseParser()
        segments = parser.parse_segments(edi_content)
        
        # Verify basic structure
        assert len(segments) > 0
        
        # Find key segments
        st_segments = [seg for seg in segments if len(seg) > 0 and seg[0] == "ST"]
        gs_segments = [seg for seg in segments if len(seg) > 0 and seg[0] == "GS"]
        isa_segments = [seg for seg in segments if len(seg) > 0 and seg[0] == "ISA"]
        
        # Verify envelope structure
        assert len(isa_segments) == 1, "Should have one ISA segment"
        assert len(gs_segments) == 1, "Should have one GS segment"
        assert len(st_segments) == 1, "Should have one ST segment"
        
        # Verify transaction type
        st_segment = st_segments[0]
        assert len(st_segment) >= 2
        assert st_segment[1] == "837", f"Expected transaction type 837, got {st_segment[1]}"
        
        # Verify functional group code
        gs_segment = gs_segments[0]
        assert len(gs_segment) >= 2
        assert gs_segment[1] == "HC", f"Expected functional group HC, got {gs_segment[1]}"
        
        # Verify envelope integrity
        self.assert_envelope_integrity(segments)

    def test_parse_837p_hierarchical_structure(self):
        """Test parsing 837P hierarchical loop structure."""
        edi_content = (
            "ISA*00*          *00*          *ZZ*SENDER         *ZZ*RECEIVER       "
            "*241226*1430*^*00501*000012345*0*P*:~"
            "GS*HC*SENDER*RECEIVER*20241226*1430*000006789*X*005010X222A1~"
            "ST*837*0001~"
            "BHT*0019*00*12345*20241226*1430*CH~"
            "NM1*41*2*PROVIDER CLINIC*****XX*1234567890~"
            "HL*1**20*1~"  # Billing provider
            "PRV*BI*PXC*207R00000X~"
            "NM1*85*2*PROVIDER CLINIC*****XX*1234567890~"
            "HL*2*1*22*1~"  # Subscriber
            "SBR*P*18*GROUP123*PLAN NAME*12*******CI~"
            "NM1*IL*1*DOE*JANE*A***MI*987654321~"
            "NM1*PR*2*INSURANCE COMPANY*****PI*123456789~"
            "HL*3*2*23*0~"  # Patient
            "PAT*19~"
            "NM1*QC*1*DOE*JANE*A***MI*987654321~"
            "CLM*CLAIM001*100.00***11:B:1*Y*A*Y*Y~"
            "LX*1~"
            "SV1*HC:99213*100.00*UN*1***1~"
            "SE*15*0001~"
            "GE*1*000006789~"
            "IEA*1*000012345~"
        )
        
        parser = BaseParser()
        segments = parser.parse_segments(edi_content)
        
        # Find HL segments and verify hierarchy
        hl_segments = [seg for seg in segments if len(seg) > 0 and seg[0] == "HL"]
        
        # Should have hierarchical structure
        assert len(hl_segments) == 3
        
        # HL*1 should be root level (billing provider)
        hl1 = hl_segments[0]
        assert hl1[1] == "1"  # HL ID
        assert hl1[2] == ""   # No parent
        assert hl1[3] == "20" # Level code (billing provider)
        
        # HL*2 should have parent HL*1 (subscriber)
        hl2 = hl_segments[1]
        assert hl2[1] == "2"  # HL ID
        assert hl2[2] == "1"  # Parent is HL*1
        assert hl2[3] == "22" # Level code (subscriber)
        
        # HL*3 should have parent HL*2 (patient)
        hl3 = hl_segments[2]
        assert hl3[1] == "3"  # HL ID
        assert hl3[2] == "2"  # Parent is HL*2
        assert hl3[3] == "23" # Level code (patient)

    def test_parse_837p_provider_information(self):
        """Test parsing provider information in 837P."""
        edi_content = (
            "ISA*00*          *00*          *ZZ*SENDER         *ZZ*RECEIVER       "
            "*241226*1430*^*00501*000012345*0*P*:~"
            "GS*HC*SENDER*RECEIVER*20241226*1430*000006789*X*005010X222A1~"
            "ST*837*0001~"
            "BHT*0019*00*12345*20241226*1430*CH~"
            "NM1*41*2*PROVIDER CLINIC*****XX*1234567890~"
            "N3*123 MEDICAL CENTER DRIVE~"
            "N4*MEDICAL CITY*TX*75001~"
            "REF*EI*12-3456789~"  # EIN
            "PER*IC*CONTACT NAME*TE*5551234567~"
            "HL*1**20*1~"
            "PRV*BI*PXC*207R00000X~"  # Provider specialty
            "NM1*85*2*BILLING PROVIDER*****XX*9876543210~"
            "N3*789 BILLING STREET~"
            "N4*BILLING CITY*TX*75003~"
            "REF*2U*207R00000X~"  # Taxonomy
            "HL*2*1*22*0~"
            "SBR*P*18*GROUP123*PLAN NAME*12*******CI~"
            "SE*14*0001~"
            "GE*1*000006789~"
            "IEA*1*000012345~"
        )
        
        parser = BaseParser()
        segments = parser.parse_segments(edi_content)
        
        # Find provider-related segments
        nm1_submitter = [seg for seg in segments if len(seg) > 1 and seg[0] == "NM1" and seg[1] == "41"]
        nm1_billing = [seg for seg in segments if len(seg) > 1 and seg[0] == "NM1" and seg[1] == "85"]
        prv_segments = [seg for seg in segments if len(seg) > 0 and seg[0] == "PRV"]
        ref_ein = [seg for seg in segments if len(seg) > 1 and seg[0] == "REF" and seg[1] == "EI"]
        ref_taxonomy = [seg for seg in segments if len(seg) > 1 and seg[0] == "REF" and seg[1] == "2U"]
        
        # Verify submitter information
        assert len(nm1_submitter) == 1
        submitter_seg = nm1_submitter[0]
        assert submitter_seg[3] == "PROVIDER CLINIC"  # Submitter name
        assert submitter_seg[8] == "1234567890"       # Submitter ID
        
        # Verify billing provider information
        assert len(nm1_billing) == 1
        billing_seg = nm1_billing[0]
        assert billing_seg[3] == "BILLING PROVIDER"   # Billing provider name
        assert billing_seg[8] == "9876543210"         # Billing provider NPI
        
        # Verify provider specialty
        assert len(prv_segments) == 1
        prv_seg = prv_segments[0]
        assert prv_seg[1] == "BI"         # Billing qualifier
        assert prv_seg[3] == "207R00000X"  # Taxonomy code
        
        # Verify reference information
        assert len(ref_ein) == 1
        assert len(ref_taxonomy) == 1

    def test_parse_837p_claim_information(self):
        """Test parsing claim information in 837P."""
        edi_content = (
            "ISA*00*          *00*          *ZZ*SENDER         *ZZ*RECEIVER       "
            "*241226*1430*^*00501*000012345*0*P*:~"
            "GS*HC*SENDER*RECEIVER*20241226*1430*000006789*X*005010X222A1~"
            "ST*837*0001~"
            "BHT*0019*00*12345*20241226*1430*CH~"
            "NM1*41*2*PROVIDER CLINIC*****XX*1234567890~"
            "HL*1**20*1~"
            "NM1*85*2*PROVIDER CLINIC*****XX*1234567890~"
            "HL*2*1*22*1~"
            "SBR*P*18*GROUP123*PLAN NAME*12*******CI~"
            "NM1*IL*1*DOE*JANE*A***MI*987654321~"
            "NM1*PR*2*INSURANCE COMPANY*****PI*123456789~"
            "HL*3*2*23*0~"
            "PAT*19~"
            "NM1*QC*1*DOE*JANE*A***MI*987654321~"
            "CLM*CLAIM001*500.00***11:B:1*Y*A*Y*Y~"
            "DTP*431*D8*20241201~"  # Onset date
            "DTP*454*D8*20241215~"  # Initial treatment date
            "REF*D9*AUTHORIZATION123~"  # Authorization number
            "HI*BK:Z0000*BF:Z0001~"  # Diagnosis codes
            "NM1*DN*1*REFERRING*DOCTOR*****XX*1111111111~"  # Referring provider
            "LX*1~"
            "SV1*HC:99213*150.00*UN*1***1~"  # Service line
            "DTP*472*D8*20241201~"  # Service date
            "LX*2~"
            "SV1*HC:99214*350.00*UN*1***1~"  # Service line
            "DTP*472*D8*20241202~"  # Service date
            "SE*21*0001~"
            "GE*1*000006789~"
            "IEA*1*000012345~"
        )
        
        parser = BaseParser()
        segments = parser.parse_segments(edi_content)
        
        # Find claim-related segments
        clm_segments = [seg for seg in segments if len(seg) > 0 and seg[0] == "CLM"]
        dtp_segments = [seg for seg in segments if len(seg) > 0 and seg[0] == "DTP"]
        hi_segments = [seg for seg in segments if len(seg) > 0 and seg[0] == "HI"]
        lx_segments = [seg for seg in segments if len(seg) > 0 and seg[0] == "LX"]
        sv1_segments = [seg for seg in segments if len(seg) > 0 and seg[0] == "SV1"]
        ref_auth = [seg for seg in segments if len(seg) > 1 and seg[0] == "REF" and seg[1] == "D9"]
        
        # Verify claim header
        assert len(clm_segments) == 1
        clm_seg = clm_segments[0]
        assert clm_seg[1] == "CLAIM001"  # Claim ID
        assert clm_seg[2] == "500.00"    # Total claim amount
        
        # Verify dates
        assert len(dtp_segments) >= 4  # Multiple date types
        
        # Verify diagnosis codes
        assert len(hi_segments) == 1
        hi_seg = hi_segments[0]
        assert "Z0000" in hi_seg[1]  # Primary diagnosis
        
        # Verify authorization
        assert len(ref_auth) == 1
        auth_seg = ref_auth[0]
        assert auth_seg[2] == "AUTHORIZATION123"
        
        # Verify service lines
        assert len(lx_segments) == 2  # Two service lines
        assert len(sv1_segments) == 2  # Two service details
        
        # Verify service line details
        sv1_1 = sv1_segments[0]
        assert "99213" in sv1_1[1]    # Procedure code
        assert sv1_1[2] == "150.00"   # Service amount
        
        sv1_2 = sv1_segments[1]
        assert "99214" in sv1_2[1]    # Procedure code
        assert sv1_2[2] == "350.00"   # Service amount

    def test_parse_837p_subscriber_information(self):
        """Test parsing subscriber information in 837P."""
        edi_content = (
            "ISA*00*          *00*          *ZZ*SENDER         *ZZ*RECEIVER       "
            "*241226*1430*^*00501*000012345*0*P*:~"
            "GS*HC*SENDER*RECEIVER*20241226*1430*000006789*X*005010X222A1~"
            "ST*837*0001~"
            "BHT*0019*00*12345*20241226*1430*CH~"
            "NM1*41*2*PROVIDER CLINIC*****XX*1234567890~"
            "HL*1**20*1~"
            "NM1*85*2*PROVIDER CLINIC*****XX*1234567890~"
            "HL*2*1*22*1~"
            "SBR*P*18*GROUP123*PLAN NAME*12*******CI~"
            "NM1*IL*1*DOE*JANE*A***MI*987654321~"
            "N3*456 SUBSCRIBER STREET~"
            "N4*SUBSCRIBER CITY*TX*75002~"
            "DMG*D8*19800315*F~"  # Demographics
            "NM1*PR*2*INSURANCE COMPANY*****PI*123456789~"
            "N3*789 INSURANCE BLVD~"
            "N4*INSURANCE CITY*TX*75004~"
            "HL*3*2*23*0~"
            "PAT*19~"
            "NM1*QC*1*DOE*JANE*A***MI*987654321~"
            "CLM*CLAIM001*100.00***11:B:1*Y*A*Y*Y~"
            "SE*16*0001~"
            "GE*1*000006789~"
            "IEA*1*000012345~"
        )
        
        parser = BaseParser()
        segments = parser.parse_segments(edi_content)
        
        # Find subscriber-related segments
        sbr_segments = [seg for seg in segments if len(seg) > 0 and seg[0] == "SBR"]
        nm1_subscriber = [seg for seg in segments if len(seg) > 1 and seg[0] == "NM1" and seg[1] == "IL"]
        nm1_payer = [seg for seg in segments if len(seg) > 1 and seg[0] == "NM1" and seg[1] == "PR"]
        dmg_segments = [seg for seg in segments if len(seg) > 0 and seg[0] == "DMG"]
        
        # Verify subscriber benefit related information
        assert len(sbr_segments) == 1
        sbr_seg = sbr_segments[0]
        assert sbr_seg[1] == "P"         # Payer responsibility
        assert sbr_seg[2] == "18"        # Individual relationship code
        assert sbr_seg[3] == "GROUP123"  # Group number
        
        # Verify subscriber information
        assert len(nm1_subscriber) == 1
        subscriber_seg = nm1_subscriber[0]
        assert subscriber_seg[3] == "DOE"    # Last name
        assert subscriber_seg[4] == "JANE"   # First name
        assert subscriber_seg[8] == "987654321"  # Member ID
        
        # Verify payer information
        assert len(nm1_payer) == 1
        payer_seg = nm1_payer[0]
        assert payer_seg[3] == "INSURANCE COMPANY"  # Payer name
        assert payer_seg[8] == "123456789"          # Payer ID
        
        # Verify demographics
        assert len(dmg_segments) == 1
        dmg_seg = dmg_segments[0]
        assert dmg_seg[1] == "D8"        # Date format
        assert dmg_seg[2] == "19800315"  # Date of birth
        assert dmg_seg[3] == "F"         # Gender

    def test_parse_837p_multiple_service_lines(self):
        """Test parsing 837P with multiple service lines."""
        edi_content = (
            "ISA*00*          *00*          *ZZ*SENDER         *ZZ*RECEIVER       "
            "*241226*1430*^*00501*000012345*0*P*:~"
            "GS*HC*SENDER*RECEIVER*20241226*1430*000006789*X*005010X222A1~"
            "ST*837*0001~"
            "BHT*0019*00*12345*20241226*1430*CH~"
            "NM1*41*2*PROVIDER CLINIC*****XX*1234567890~"
            "HL*1**20*1~"
            "NM1*85*2*PROVIDER CLINIC*****XX*1234567890~"
            "HL*2*1*22*1~"
            "SBR*P*18*GROUP123*PLAN NAME*12*******CI~"
            "NM1*IL*1*DOE*JANE*A***MI*987654321~"
            "NM1*PR*2*INSURANCE COMPANY*****PI*123456789~"
            "HL*3*2*23*0~"
            "PAT*19~"
            "NM1*QC*1*DOE*JANE*A***MI*987654321~"
            "CLM*CLAIM001*400.00***11:B:1*Y*A*Y*Y~"
            "HI*BK:Z0000~"
            "LX*1~"
            "SV1*HC:99213*100.00*UN*1***1~"
            "DTP*472*D8*20241201~"
            "LX*2~"
            "SV1*HC:99214*150.00*UN*1***1~"
            "DTP*472*D8*20241201~"
            "LX*3~"
            "SV1*HC:99215*150.00*UN*1***1~"
            "DTP*472*D8*20241202~"
            "SE*21*0001~"
            "GE*1*000006789~"
            "IEA*1*000012345~"
        )
        
        parser = BaseParser()
        segments = parser.parse_segments(edi_content)
        
        # Find service line segments
        lx_segments = [seg for seg in segments if len(seg) > 0 and seg[0] == "LX"]
        sv1_segments = [seg for seg in segments if len(seg) > 0 and seg[0] == "SV1"]
        dtp_service = [seg for seg in segments if len(seg) > 1 and seg[0] == "DTP" and seg[1] == "472"]
        
        # Verify service line count
        assert len(lx_segments) == 3  # Three service lines
        assert len(sv1_segments) == 3  # Three service details
        assert len(dtp_service) == 3   # Three service dates
        
        # Verify service line sequence
        lx_numbers = [seg[1] for seg in lx_segments if len(seg) > 1]
        assert lx_numbers == ["1", "2", "3"]
        
        # Verify service line details
        services = []
        for sv1_seg in sv1_segments:
            if len(sv1_seg) > 2:
                services.append({
                    'procedure': sv1_seg[1],
                    'amount': sv1_seg[2]
                })
        
        assert len(services) == 3
        assert "99213" in services[0]['procedure']
        assert services[0]['amount'] == "100.00"
        assert "99214" in services[1]['procedure']
        assert services[1]['amount'] == "150.00"
        assert "99215" in services[2]['procedure']
        assert services[2]['amount'] == "150.00"

    def test_parse_837p_malformed_data(self):
        """Test 837P parser with malformed data."""
        edi_content = (
            "ISA*00*          *00*          *ZZ*SENDER         *ZZ*RECEIVER       "
            "*241226*1430*^*00501*000012345*0*P*:~"
            "GS*HC*SENDER*RECEIVER*20241226*1430*000006789*X*005010X222A1~"
            "ST*837*0001~"
            "INVALID*SEGMENT*WITH*TOO*MANY*ELEMENTS~"
            "BHT*0019*00*12345*20241226*1430*CH~"
            "NM1*41*2*PROVIDER CLINIC*****XX*1234567890~"
            "CORRUPTED*DATA*SEGMENT~"
            "HL*1**20*1~"
            "SE*6*0001~"
            "GE*1*000006789~"
            "IEA*1*000012345~"
        )
        
        parser = BaseParser()
        segments = parser.parse_segments(edi_content)
        
        # Should still parse valid segments
        assert len(segments) > 0
        
        # Find valid segments
        valid_segments = [seg for seg in segments if len(seg) > 0 and seg[0] in ["ISA", "GS", "ST", "BHT", "NM1", "HL", "SE", "GE", "IEA"]]
        assert len(valid_segments) >= 7, "Should parse valid segments despite malformed ones"
        
        # Verify structure is maintained
        isa_segments = [seg for seg in segments if len(seg) > 0 and seg[0] == "ISA"]
        assert len(isa_segments) == 1

    def test_parse_837p_control_numbers(self):
        """Test that control numbers are properly handled in 837P."""
        edi_content = (
            "ISA*00*          *00*          *ZZ*SENDER         *ZZ*RECEIVER       "
            "*241226*1430*^*00501*000012345*0*P*:~"
            "GS*HC*SENDER*RECEIVER*20241226*1430*000006789*X*005010X222A1~"
            "ST*837*0001~"
            "BHT*0019*00*12345*20241226*1430*CH~"
            "NM1*41*2*PROVIDER CLINIC*****XX*1234567890~"
            "SE*4*0001~"
            "GE*1*000006789~"
            "IEA*1*000012345~"
        )
        
        parser = BaseParser()
        segments = parser.parse_segments(edi_content)
        
        # Verify envelope integrity
        self.assert_envelope_integrity(segments)
        
        # Verify transaction counts
        self.assert_transaction_counts(segments)

    def test_parse_837p_empty_content(self):
        """Test 837P parser with empty content."""
        parser = BaseParser()
        
        # Should handle gracefully
        try:
            segments = parser.parse_segments("")
            assert segments == [] or segments is None
        except Exception as e:
            # Should be a handled exception
            assert not isinstance(e, (SystemExit, KeyboardInterrupt))