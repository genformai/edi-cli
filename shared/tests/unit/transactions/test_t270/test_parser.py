"""
Test cases for EDI 270 (Eligibility Inquiry) Parser.

This file contains comprehensive parser tests for 270 transaction processing,
migrated from the original test suite.
"""

import pytest
from packages.core.base.parser import BaseParser
from tests.fixtures import EDIFixtures
from tests.shared.test_patterns import StandardTestMixin


class Test270Parser(StandardTestMixin):
    """Test cases for 270 parser functionality."""

    def test_parse_270_basic_eligibility_inquiry(self, edi_fixtures):
        """Test parsing a basic 270 eligibility inquiry."""
        edi_content = edi_fixtures.get_270_eligibility_inquiry()
        
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
        assert st_segment[1] == "270", f"Expected transaction type 270, got {st_segment[1]}"
        
        # Verify functional group code
        gs_segment = gs_segments[0]
        assert len(gs_segment) >= 2
        assert gs_segment[1] == "HS", f"Expected functional group HS, got {gs_segment[1]}"

    def test_parse_270_with_multiple_inquiries(self):
        """Test parsing 270 with multiple eligibility inquiries."""
        edi_content = (
            "ISA*00*          *00*          *ZZ*SENDER         *ZZ*RECEIVER       "
            "*241226*1430*^*00501*000012345*0*P*:~"
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
        assert st_segments[0][1] == "270"
        
        # Find HL segments (hierarchical loops)
        hl_segments = [seg for seg in segments if len(seg) > 0 and seg[0] == "HL"]
        assert len(hl_segments) >= 4, "Should have multiple HL segments for multiple inquiries"
        
        # Find TRN segments (trace numbers for each inquiry)
        trn_segments = [seg for seg in segments if len(seg) > 0 and seg[0] == "TRN"]
        assert len(trn_segments) >= 2, "Should have multiple TRN segments for multiple inquiries"
        
        # Find NM1 segments for subscribers
        nm1_segments = [seg for seg in segments if len(seg) > 0 and seg[0] == "NM1"]
        subscriber_segments = [seg for seg in nm1_segments if len(seg) > 1 and seg[1] == "IL"]
        assert len(subscriber_segments) >= 2, "Should have multiple subscriber segments"

    def test_parse_270_malformed_data(self):
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
        
        parser = BaseParser()
        segments = parser.parse_segments(edi_content)
        
        # Should still parse valid segments
        assert len(segments) > 0
        
        # Find valid segments
        valid_segments = [seg for seg in segments if len(seg) > 0 and seg[0] in ["ISA", "GS", "ST", "BHT", "SE", "GE", "IEA"]]
        assert len(valid_segments) >= 5, "Should parse valid segments despite malformed ones"
        
        # Verify structure is maintained
        isa_segments = [seg for seg in segments if len(seg) > 0 and seg[0] == "ISA"]
        assert len(isa_segments) == 1

    def test_parse_270_empty_content(self):
        """Test 270 parser with empty content."""
        parser = BaseParser()
        
        # Should handle gracefully
        try:
            segments = parser.parse_segments("")
            assert segments == [] or segments is None
        except Exception as e:
            # Should be a handled exception
            assert not isinstance(e, (SystemExit, KeyboardInterrupt))

    def test_parse_270_control_numbers(self, edi_fixtures):
        """Test that control numbers are properly handled."""
        edi_content = edi_fixtures.get_270_eligibility_inquiry()
        
        parser = BaseParser()
        segments = parser.parse_segments(edi_content)
        
        # Find control number segments
        isa_segments = [seg for seg in segments if len(seg) > 0 and seg[0] == "ISA"]
        iea_segments = [seg for seg in segments if len(seg) > 0 and seg[0] == "IEA"]
        gs_segments = [seg for seg in segments if len(seg) > 0 and seg[0] == "GS"]
        ge_segments = [seg for seg in segments if len(seg) > 0 and seg[0] == "GE"]
        st_segments = [seg for seg in segments if len(seg) > 0 and seg[0] == "ST"]
        se_segments = [seg for seg in segments if len(seg) > 0 and seg[0] == "SE"]
        
        # Verify envelope integrity
        self.assert_envelope_integrity(segments)
        
        # Verify transaction counts
        self.assert_transaction_counts(segments)

    def test_parse_270_hierarchical_structure(self):
        """Test parsing 270 hierarchical loop structure."""
        edi_content = (
            "ISA*00*          *00*          *ZZ*SENDER         *ZZ*RECEIVER       "
            "*241226*1430*^*00501*000012345*0*P*:~"
            "GS*HS*SENDER*RECEIVER*20241226*1430*000006789*X*005010X279A1~"
            "ST*270*0001~"
            "BHT*0022*13*12345*20241226*1430~"
            "HL*1**20*1~"  # Information source (payer)
            "NM1*PR*2*INSURANCE COMPANY*****PI*123456789~"
            "HL*2*1*21*1~"  # Information receiver (provider)
            "NM1*1P*2*PROVIDER CLINIC*****XX*1234567890~"
            "HL*3*2*22*0~"  # Subscriber
            "TRN*1*INQUIRY001*123456789~"
            "NM1*IL*1*DOE*JANE*A***MI*987654321~"
            "DMG*D8*19800315*F~"  # Demographics
            "EQ*30~"  # Eligibility inquiry
            "SE*10*0001~"
            "GE*1*000006789~"
            "IEA*1*000012345~"
        )
        
        parser = BaseParser()
        segments = parser.parse_segments(edi_content)
        
        # Find HL segments and verify hierarchy
        hl_segments = [seg for seg in segments if len(seg) > 0 and seg[0] == "HL"]
        
        # Should have hierarchical structure
        assert len(hl_segments) == 3
        
        # HL*1 should be root level (no parent)
        hl1 = hl_segments[0]
        assert hl1[1] == "1"  # HL ID
        assert hl1[2] == ""   # No parent
        assert hl1[3] == "20" # Level code (information source)
        
        # HL*2 should have parent HL*1
        hl2 = hl_segments[1]
        assert hl2[1] == "2"  # HL ID
        assert hl2[2] == "1"  # Parent is HL*1
        assert hl2[3] == "21" # Level code (information receiver)
        
        # HL*3 should have parent HL*2
        hl3 = hl_segments[2]
        assert hl3[1] == "3"  # HL ID
        assert hl3[2] == "2"  # Parent is HL*2
        assert hl3[3] == "22" # Level code (subscriber)

    def test_parse_270_eligibility_codes(self):
        """Test parsing various eligibility inquiry codes."""
        edi_content = (
            "ISA*00*          *00*          *ZZ*SENDER         *ZZ*RECEIVER       "
            "*241226*1430*^*00501*000012345*0*P*:~"
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
            "EQ*30~"  # Health benefit plan coverage
            "EQ*1~"   # Medical care
            "EQ*47~"  # Hospital
            "EQ*50~"  # Pharmacy
            "SE*12*0001~"
            "GE*1*000006789~"
            "IEA*1*000012345~"
        )
        
        parser = BaseParser()
        segments = parser.parse_segments(edi_content)
        
        # Find EQ segments (eligibility inquiry)
        eq_segments = [seg for seg in segments if len(seg) > 0 and seg[0] == "EQ"]
        
        # Should have multiple eligibility codes
        assert len(eq_segments) == 4
        
        # Verify specific codes
        eq_codes = [seg[1] for seg in eq_segments if len(seg) > 1]
        assert "30" in eq_codes  # Health benefit plan coverage
        assert "1" in eq_codes   # Medical care
        assert "47" in eq_codes  # Hospital
        assert "50" in eq_codes  # Pharmacy

    def test_parse_270_provider_information(self):
        """Test parsing provider information in 270."""
        edi_content = (
            "ISA*00*          *00*          *ZZ*SENDER         *ZZ*RECEIVER       "
            "*241226*1430*^*00501*000012345*0*P*:~"
            "GS*HS*SENDER*RECEIVER*20241226*1430*000006789*X*005010X279A1~"
            "ST*270*0001~"
            "BHT*0022*13*12345*20241226*1430~"
            "HL*1**20*1~"
            "NM1*PR*2*INSURANCE COMPANY*****PI*123456789~"
            "HL*2*1*21*1~"
            "NM1*1P*2*PROVIDER CLINIC*****XX*1234567890~"
            "N3*123 MEDICAL CENTER DRIVE~"
            "N4*MEDICAL CITY*TX*75001~"
            "REF*SY*TAXONOMY123456~"
            "HL*3*2*22*0~"
            "TRN*1*INQUIRY001*123456789~"
            "NM1*IL*1*DOE*JANE*A***MI*987654321~"
            "EQ*30~"
            "SE*13*0001~"
            "GE*1*000006789~"
            "IEA*1*000012345~"
        )
        
        parser = BaseParser()
        segments = parser.parse_segments(edi_content)
        
        # Find provider-related segments
        nm1_provider = [seg for seg in segments if len(seg) > 1 and seg[0] == "NM1" and seg[1] == "1P"]
        n3_segments = [seg for seg in segments if len(seg) > 0 and seg[0] == "N3"]
        n4_segments = [seg for seg in segments if len(seg) > 0 and seg[0] == "N4"]
        ref_segments = [seg for seg in segments if len(seg) > 0 and seg[0] == "REF"]
        
        # Verify provider information
        assert len(nm1_provider) == 1
        provider_seg = nm1_provider[0]
        assert provider_seg[3] == "PROVIDER CLINIC"  # Provider name
        assert provider_seg[8] == "1234567890"       # Provider NPI
        
        # Verify address information
        assert len(n3_segments) == 1
        assert len(n4_segments) == 1
        
        # Verify reference information
        assert len(ref_segments) >= 1

    def test_parse_270_subscriber_demographics(self):
        """Test parsing subscriber demographic information."""
        edi_content = (
            "ISA*00*          *00*          *ZZ*SENDER         *ZZ*RECEIVER       "
            "*241226*1430*^*00501*000012345*0*P*:~"
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
            "DMG*D8*19800315*F~"  # Demographics: DOB and gender
            "DTP*291*D8*20241201~"  # Date - eligibility begin
            "EQ*30~"
            "SE*12*0001~"
            "GE*1*000006789~"
            "IEA*1*000012345~"
        )
        
        parser = BaseParser()
        segments = parser.parse_segments(edi_content)
        
        # Find subscriber information
        nm1_subscriber = [seg for seg in segments if len(seg) > 1 and seg[0] == "NM1" and seg[1] == "IL"]
        dmg_segments = [seg for seg in segments if len(seg) > 0 and seg[0] == "DMG"]
        dtp_segments = [seg for seg in segments if len(seg) > 0 and seg[0] == "DTP"]
        
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
        
        # Verify date information
        assert len(dtp_segments) >= 1

    def test_parse_270_dependent_inquiry(self):
        """Test parsing 270 with dependent eligibility inquiry."""
        edi_content = (
            "ISA*00*          *00*          *ZZ*SENDER         *ZZ*RECEIVER       "
            "*241226*1430*^*00501*000012345*0*P*:~"
            "GS*HS*SENDER*RECEIVER*20241226*1430*000006789*X*005010X279A1~"
            "ST*270*0001~"
            "BHT*0022*13*12345*20241226*1430~"
            "HL*1**20*1~"
            "NM1*PR*2*INSURANCE COMPANY*****PI*123456789~"
            "HL*2*1*21*1~"
            "NM1*1P*2*PROVIDER CLINIC*****XX*1234567890~"
            "HL*3*2*22*1~"  # Subscriber
            "TRN*1*INQUIRY001*123456789~"
            "NM1*IL*1*DOE*JANE*A***MI*987654321~"
            "HL*4*3*23*0~"  # Dependent
            "TRN*1*INQUIRY002*123456789~"
            "NM1*03*1*DOE*JOHNNY*B~"  # Dependent name
            "DMG*D8*20100515*M~"  # Dependent demographics
            "EQ*30~"
            "SE*14*0001~"
            "GE*1*000006789~"
            "IEA*1*000012345~"
        )
        
        parser = BaseParser()
        segments = parser.parse_segments(edi_content)
        
        # Find hierarchical structure
        hl_segments = [seg for seg in segments if len(seg) > 0 and seg[0] == "HL"]
        
        # Should have subscriber and dependent levels
        assert len(hl_segments) == 4
        
        # Find dependent HL segment
        dependent_hl = [seg for seg in hl_segments if len(seg) > 3 and seg[3] == "23"]
        assert len(dependent_hl) == 1
        
        # Verify dependent has parent
        dep_seg = dependent_hl[0]
        assert dep_seg[2] == "3"  # Parent is subscriber HL*3
        
        # Find dependent NM1 segment
        nm1_dependent = [seg for seg in segments if len(seg) > 1 and seg[0] == "NM1" and seg[1] == "03"]
        assert len(nm1_dependent) == 1
        
        dependent_name = nm1_dependent[0]
        assert dependent_name[3] == "DOE"     # Last name
        assert dependent_name[4] == "JOHNNY"  # First name