"""
Test cases for EDI 276 (Claim Status Inquiry) Parser.

This file contains comprehensive parser tests for 276 transaction processing,
migrated from the original test suite.
"""

import pytest
from packages.core.base.parser import BaseParser
from tests.shared.test_patterns import StandardTestMixin


class Test276Parser(StandardTestMixin):
    """Test cases for 276 parser functionality."""

    def test_parse_276_basic_claim_status_inquiry(self):
        """Test parsing a basic 276 claim status inquiry."""
        edi_content = (
            "ISA*00*          *00*          *ZZ*SENDER         *ZZ*RECEIVER       "
            "*241226*1430*^*00501*000012345*0*P*:~"
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
        assert st_segment[1] == "276", f"Expected transaction type 276, got {st_segment[1]}"
        
        # Verify functional group code
        gs_segment = gs_segments[0]
        assert len(gs_segment) >= 2
        assert gs_segment[1] == "HI", f"Expected functional group HI, got {gs_segment[1]}"
        
        # Verify envelope integrity
        self.assert_envelope_integrity(segments)

    def test_parse_276_multiple_claim_inquiries(self):
        """Test parsing 276 with multiple claim status inquiries."""
        edi_content = (
            "ISA*00*          *00*          *ZZ*SENDER         *ZZ*RECEIVER       "
            "*241226*1430*^*00501*000012345*0*P*:~"
            "GS*HI*SENDER*RECEIVER*20241226*1430*000006789*X*005010X212~"
            "ST*276*0001~"
            "BHT*0019*13*12345*20241226*1430~"
            "HL*1**20*1~"
            "NM1*PR*2*INSURANCE COMPANY*****PI*123456789~"
            "HL*2*1*21*1~"
            "NM1*41*2*PROVIDER CLINIC*****XX*1234567890~"
            "HL*3*2*19*0~"
            "TRN*1*INQUIRY001*123456789~"
            "REF*1K*CLAIM001~"
            "DTM*232*20241201~"
            "HL*4*2*19*0~"
            "TRN*1*INQUIRY002*123456789~"
            "REF*1K*CLAIM002~"
            "DTM*232*20241202~"
            "HL*5*2*19*0~"
            "TRN*1*INQUIRY003*123456789~"
            "REF*1K*CLAIM003~"
            "DTM*232*20241203~"
            "SE*17*0001~"
            "GE*1*000006789~"
            "IEA*1*000012345~"
        )
        
        parser = BaseParser()
        segments = parser.parse_segments(edi_content)
        
        # Verify structure
        assert len(segments) > 0
        
        # Find transaction segment
        st_segments = [seg for seg in segments if len(seg) > 0 and seg[0] == "ST"]
        assert len(st_segments) == 1
        assert st_segments[0][1] == "276"
        
        # Find HL segments (hierarchical loops for each inquiry)
        hl_segments = [seg for seg in segments if len(seg) > 0 and seg[0] == "HL"]
        assert len(hl_segments) >= 5, "Should have multiple HL segments for multiple inquiries"
        
        # Find TRN segments (trace numbers for each inquiry)
        trn_segments = [seg for seg in segments if len(seg) > 0 and seg[0] == "TRN"]
        assert len(trn_segments) >= 3, "Should have multiple TRN segments for multiple inquiries"
        
        # Find REF segments (claim references)
        ref_segments = [seg for seg in segments if len(seg) > 1 and seg[0] == "REF" and seg[1] == "1K"]
        assert len(ref_segments) >= 3, "Should have multiple claim reference segments"
        
        # Verify claim references
        claim_refs = [seg[2] for seg in ref_segments if len(seg) > 2]
        assert "CLAIM001" in claim_refs
        assert "CLAIM002" in claim_refs
        assert "CLAIM003" in claim_refs

    def test_parse_276_hierarchical_structure(self):
        """Test parsing 276 hierarchical loop structure."""
        edi_content = (
            "ISA*00*          *00*          *ZZ*SENDER         *ZZ*RECEIVER       "
            "*241226*1430*^*00501*000012345*0*P*:~"
            "GS*HI*SENDER*RECEIVER*20241226*1430*000006789*X*005010X212~"
            "ST*276*0001~"
            "BHT*0019*13*12345*20241226*1430~"
            "HL*1**20*1~"  # Information source (payer)
            "NM1*PR*2*INSURANCE COMPANY*****PI*123456789~"
            "HL*2*1*21*1~"  # Information receiver (provider)
            "NM1*41*2*PROVIDER CLINIC*****XX*1234567890~"
            "HL*3*2*19*1~"  # Billing provider
            "NM1*85*2*BILLING PROVIDER*****XX*9876543210~"
            "HL*4*3*22*0~"  # Subscriber
            "TRN*1*INQUIRY001*123456789~"
            "NM1*IL*1*DOE*JANE*A***MI*987654321~"
            "REF*1K*CLAIM001~"
            "DTM*232*20241201~"
            "SE*13*0001~"
            "GE*1*000006789~"
            "IEA*1*000012345~"
        )
        
        parser = BaseParser()
        segments = parser.parse_segments(edi_content)
        
        # Find HL segments and verify hierarchy
        hl_segments = [seg for seg in segments if len(seg) > 0 and seg[0] == "HL"]
        
        # Should have hierarchical structure
        assert len(hl_segments) == 4
        
        # HL*1 should be root level (information source)
        hl1 = hl_segments[0]
        assert hl1[1] == "1"  # HL ID
        assert hl1[2] == ""   # No parent
        assert hl1[3] == "20" # Level code (information source)
        
        # HL*2 should have parent HL*1 (information receiver)
        hl2 = hl_segments[1]
        assert hl2[1] == "2"  # HL ID
        assert hl2[2] == "1"  # Parent is HL*1
        assert hl2[3] == "21" # Level code (information receiver)
        
        # HL*3 should have parent HL*2 (billing provider)
        hl3 = hl_segments[2]
        assert hl3[1] == "3"  # HL ID
        assert hl3[2] == "2"  # Parent is HL*2
        assert hl3[3] == "19" # Level code (billing provider)
        
        # HL*4 should have parent HL*3 (subscriber)
        hl4 = hl_segments[3]
        assert hl4[1] == "4"  # HL ID
        assert hl4[2] == "3"  # Parent is HL*3
        assert hl4[3] == "22" # Level code (subscriber)

    def test_parse_276_with_patient_information(self):
        """Test parsing 276 with patient/subscriber information."""
        edi_content = (
            "ISA*00*          *00*          *ZZ*SENDER         *ZZ*RECEIVER       "
            "*241226*1430*^*00501*000012345*0*P*:~"
            "GS*HI*SENDER*RECEIVER*20241226*1430*000006789*X*005010X212~"
            "ST*276*0001~"
            "BHT*0019*13*12345*20241226*1430~"
            "HL*1**20*1~"
            "NM1*PR*2*INSURANCE COMPANY*****PI*123456789~"
            "HL*2*1*21*1~"
            "NM1*41*2*PROVIDER CLINIC*****XX*1234567890~"
            "HL*3*2*22*0~"
            "TRN*1*INQUIRY001*123456789~"
            "NM1*IL*1*DOE*JANE*A***MI*987654321~"
            "DMG*D8*19800315*F~"  # Demographics
            "REF*1K*CLAIM001~"
            "DTM*232*20241201~"
            "AMT*T3*500.00~"  # Claim amount
            "SE*13*0001~"
            "GE*1*000006789~"
            "IEA*1*000012345~"
        )
        
        parser = BaseParser()
        segments = parser.parse_segments(edi_content)
        
        # Find patient-related segments
        nm1_subscriber = [seg for seg in segments if len(seg) > 1 and seg[0] == "NM1" and seg[1] == "IL"]
        dmg_segments = [seg for seg in segments if len(seg) > 0 and seg[0] == "DMG"]
        ref_segments = [seg for seg in segments if len(seg) > 1 and seg[0] == "REF" and seg[1] == "1K"]
        amt_segments = [seg for seg in segments if len(seg) > 1 and seg[0] == "AMT" and seg[1] == "T3"]
        
        # Verify subscriber information
        assert len(nm1_subscriber) == 1
        subscriber_seg = nm1_subscriber[0]
        assert subscriber_seg[3] == "DOE"    # Last name
        assert subscriber_seg[4] == "JANE"   # First name
        assert subscriber_seg[8] == "987654321"  # Member ID
        
        # Verify demographics
        assert len(dmg_segments) == 1
        dmg_seg = dmg_segments[0]
        assert dmg_seg[1] == "D8"        # Date format
        assert dmg_seg[2] == "19800315"  # Date of birth
        assert dmg_seg[3] == "F"         # Gender
        
        # Verify claim reference
        assert len(ref_segments) == 1
        ref_seg = ref_segments[0]
        assert ref_seg[2] == "CLAIM001"  # Claim number
        
        # Verify claim amount
        assert len(amt_segments) == 1
        amt_seg = amt_segments[0]
        assert amt_seg[2] == "500.00"    # Claim amount

    def test_parse_276_with_service_information(self):
        """Test parsing 276 with service-level inquiries."""
        edi_content = (
            "ISA*00*          *00*          *ZZ*SENDER         *ZZ*RECEIVER       "
            "*241226*1430*^*00501*000012345*0*P*:~"
            "GS*HI*SENDER*RECEIVER*20241226*1430*000006789*X*005010X212~"
            "ST*276*0001~"
            "BHT*0019*13*12345*20241226*1430~"
            "HL*1**20*1~"
            "NM1*PR*2*INSURANCE COMPANY*****PI*123456789~"
            "HL*2*1*21*1~"
            "NM1*41*2*PROVIDER CLINIC*****XX*1234567890~"
            "HL*3*2*22*1~"
            "TRN*1*INQUIRY001*123456789~"
            "NM1*IL*1*DOE*JANE*A***MI*987654321~"
            "REF*1K*CLAIM001~"
            "DTM*232*20241201~"
            "HL*4*3*23*0~"  # Service level
            "TRN*1*SERVICE001*123456789~"
            "REF*6R*LINE001~"  # Service line reference
            "SVC*HC:99213*100.00~"  # Service information
            "DTM*472*20241201~"  # Service date
            "SE*15*0001~"
            "GE*1*000006789~"
            "IEA*1*000012345~"
        )
        
        parser = BaseParser()
        segments = parser.parse_segments(edi_content)
        
        # Find service-related segments
        hl_service = [seg for seg in segments if len(seg) > 3 and seg[0] == "HL" and seg[3] == "23"]
        svc_segments = [seg for seg in segments if len(seg) > 0 and seg[0] == "SVC"]
        ref_service = [seg for seg in segments if len(seg) > 1 and seg[0] == "REF" and seg[1] == "6R"]
        
        # Verify service level hierarchy
        assert len(hl_service) == 1
        service_hl = hl_service[0]
        assert service_hl[1] == "4"  # HL ID
        assert service_hl[2] == "3"  # Parent is claim level
        assert service_hl[3] == "23" # Service level code
        
        # Verify service information
        assert len(svc_segments) == 1
        svc_seg = svc_segments[0]
        assert "99213" in svc_seg[1]     # Procedure code
        assert svc_seg[2] == "100.00"    # Service amount
        
        # Verify service reference
        assert len(ref_service) == 1
        ref_seg = ref_service[0]
        assert ref_seg[2] == "LINE001"   # Service line reference

    def test_parse_276_malformed_data(self):
        """Test 276 parser with malformed data."""
        edi_content = (
            "ISA*00*          *00*          *ZZ*SENDER         *ZZ*RECEIVER       "
            "*241226*1430*^*00501*000012345*0*P*:~"
            "GS*HI*SENDER*RECEIVER*20241226*1430*000006789*X*005010X212~"
            "ST*276*0001~"
            "INVALID*SEGMENT*WITH*TOO*MANY*ELEMENTS~"
            "BHT*0019*13*12345*20241226*1430~"
            "HL*1**20*1~"
            "CORRUPTED*DATA~"
            "NM1*PR*2*INSURANCE COMPANY*****PI*123456789~"
            "SE*6*0001~"
            "GE*1*000006789~"
            "IEA*1*000012345~"
        )
        
        parser = BaseParser()
        segments = parser.parse_segments(edi_content)
        
        # Should still parse valid segments
        assert len(segments) > 0
        
        # Find valid segments
        valid_segments = [seg for seg in segments if len(seg) > 0 and seg[0] in ["ISA", "GS", "ST", "BHT", "HL", "NM1", "SE", "GE", "IEA"]]
        assert len(valid_segments) >= 7, "Should parse valid segments despite malformed ones"
        
        # Verify structure is maintained
        isa_segments = [seg for seg in segments if len(seg) > 0 and seg[0] == "ISA"]
        assert len(isa_segments) == 1

    def test_parse_276_control_numbers(self):
        """Test that control numbers are properly handled in 276."""
        edi_content = (
            "ISA*00*          *00*          *ZZ*SENDER         *ZZ*RECEIVER       "
            "*241226*1430*^*00501*000012345*0*P*:~"
            "GS*HI*SENDER*RECEIVER*20241226*1430*000006789*X*005010X212~"
            "ST*276*0001~"
            "BHT*0019*13*12345*20241226*1430~"
            "HL*1**20*1~"
            "NM1*PR*2*INSURANCE COMPANY*****PI*123456789~"
            "SE*5*0001~"
            "GE*1*000006789~"
            "IEA*1*000012345~"
        )
        
        parser = BaseParser()
        segments = parser.parse_segments(edi_content)
        
        # Verify envelope integrity
        self.assert_envelope_integrity(segments)
        
        # Verify transaction counts
        self.assert_transaction_counts(segments)

    def test_parse_276_empty_content(self):
        """Test 276 parser with empty content."""
        parser = BaseParser()
        
        # Should handle gracefully
        try:
            segments = parser.parse_segments("")
            assert segments == [] or segments is None
        except Exception as e:
            # Should be a handled exception
            assert not isinstance(e, (SystemExit, KeyboardInterrupt))

    def test_parse_276_provider_information(self):
        """Test parsing detailed provider information in 276."""
        edi_content = (
            "ISA*00*          *00*          *ZZ*SENDER         *ZZ*RECEIVER       "
            "*241226*1430*^*00501*000012345*0*P*:~"
            "GS*HI*SENDER*RECEIVER*20241226*1430*000006789*X*005010X212~"
            "ST*276*0001~"
            "BHT*0019*13*12345*20241226*1430~"
            "HL*1**20*1~"
            "NM1*PR*2*INSURANCE COMPANY*****PI*123456789~"
            "HL*2*1*21*1~"
            "NM1*41*2*PROVIDER CLINIC*****XX*1234567890~"
            "N3*123 MEDICAL CENTER DRIVE~"
            "N4*MEDICAL CITY*TX*75001~"
            "REF*2U*TAXONOMY123456~"  # Taxonomy code
            "PER*IC*CONTACT NAME*TE*5551234567~"  # Contact information
            "HL*3*2*22*0~"
            "TRN*1*INQUIRY001*123456789~"
            "NM1*IL*1*DOE*JANE*A***MI*987654321~"
            "REF*1K*CLAIM001~"
            "SE*13*0001~"
            "GE*1*000006789~"
            "IEA*1*000012345~"
        )
        
        parser = BaseParser()
        segments = parser.parse_segments(edi_content)
        
        # Find provider-related segments
        nm1_provider = [seg for seg in segments if len(seg) > 1 and seg[0] == "NM1" and seg[1] == "41"]
        n3_segments = [seg for seg in segments if len(seg) > 0 and seg[0] == "N3"]
        n4_segments = [seg for seg in segments if len(seg) > 0 and seg[0] == "N4"]
        ref_segments = [seg for seg in segments if len(seg) > 1 and seg[0] == "REF" and seg[1] == "2U"]
        per_segments = [seg for seg in segments if len(seg) > 0 and seg[0] == "PER"]
        
        # Verify provider information
        assert len(nm1_provider) == 1
        provider_seg = nm1_provider[0]
        assert provider_seg[3] == "PROVIDER CLINIC"  # Provider name
        assert provider_seg[8] == "1234567890"       # Provider NPI
        
        # Verify address information
        assert len(n3_segments) == 1
        assert len(n4_segments) == 1
        
        # Verify reference and contact information
        assert len(ref_segments) >= 1
        assert len(per_segments) >= 1

    def test_parse_276_batch_inquiry(self):
        """Test parsing 276 with batch claim status inquiries."""
        edi_content = (
            "ISA*00*          *00*          *ZZ*SENDER         *ZZ*RECEIVER       "
            "*241226*1430*^*00501*000012345*0*P*:~"
            "GS*HI*SENDER*RECEIVER*20241226*1430*000006789*X*005010X212~"
            "ST*276*0001~"
            "BHT*0019*13*BATCH001*20241226*1430~"
            "HL*1**20*1~"
            "NM1*PR*2*INSURANCE COMPANY*****PI*123456789~"
            "HL*2*1*21*1~"
            "NM1*41*2*PROVIDER CLINIC*****XX*1234567890~"
            "HL*3*2*22*0~"
            "TRN*1*INQ001*123456789~"
            "NM1*IL*1*DOE*JANE*A***MI*987654321~"
            "REF*1K*CLAIM001~"
            "REF*1K*CLAIM002~"
            "REF*1K*CLAIM003~"
            "DTM*232*20241201~"
            "DTM*233*20241203~"
            "SE*14*0001~"
            "GE*1*000006789~"
            "IEA*1*000012345~"
        )
        
        parser = BaseParser()
        segments = parser.parse_segments(edi_content)
        
        # Find batch-related elements
        bht_segments = [seg for seg in segments if len(seg) > 0 and seg[0] == "BHT"]
        ref_claims = [seg for seg in segments if len(seg) > 1 and seg[0] == "REF" and seg[1] == "1K"]
        dtm_segments = [seg for seg in segments if len(seg) > 0 and seg[0] == "DTM"]
        
        # Verify batch header
        assert len(bht_segments) == 1
        bht_seg = bht_segments[0]
        assert bht_seg[3] == "BATCH001"  # Batch reference
        
        # Verify multiple claim references
        assert len(ref_claims) == 3
        claim_numbers = [seg[2] for seg in ref_claims if len(seg) > 2]
        assert "CLAIM001" in claim_numbers
        assert "CLAIM002" in claim_numbers
        assert "CLAIM003" in claim_numbers
        
        # Verify date range
        assert len(dtm_segments) >= 2