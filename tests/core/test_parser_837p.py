"""
Tests for EDI 837P (Professional Claims) Parser
"""

import pytest
from packages.core.parser import EdiParser
from packages.core.parser_837p import Parser837P
from packages.core.ast_837p import Transaction837P, SubmitterInfo, BillingProviderInfo, SubscriberInfo


class TestParser837P:
    """Test cases for 837P parser functionality."""

    def test_basic_837p_parsing(self):
        """Test basic 837P parsing functionality."""
        # Sample 837P segments
        segments = [
            ["ST", "837", "0001"],
            ["BHT", "0019", "00", "SAMPLE837", "20240326", "1430", "CH"],
            ["HL", "1", "", "20", "1"],
            ["NM1", "41", "2", "SAMPLE BILLING SERVICE", "", "", "", "", "46", "TGJ23"],
            ["HL", "2", "1", "22", "0"],
            ["NM1", "85", "2", "SAMPLE MEDICAL CLINIC", "", "", "", "", "XX", "1234567890"],
            ["CLM", "CLAIM123", "150.00", "", "", "11", "Y", "A", "Y", "Y"],
            ["HI", "BK:Z87891", "BF:M79.3"],
            ["LX", "1"],
            ["SV1", "HC:99213", "100.00", "UN", "1", "", "", "1", "50.00", "Y"],
            ["NM1", "82", "1", "SMITH", "DR", "ROBERT", "", "", "XX", "9876543210"]
        ]
        
        parser = Parser837P(segments)
        transaction = parser.parse()
        
        # Verify transaction structure
        assert isinstance(transaction, Transaction837P)
        assert transaction.header["transaction_set_identifier"] == "837"
        assert transaction.header["transaction_set_control_number"] == "0001"
        
        # Verify billing provider
        assert transaction.billing_provider is not None
        assert transaction.billing_provider.name == "SAMPLE MEDICAL CLINIC"
        assert transaction.billing_provider.npi == "1234567890"
        
        # Verify claim information
        assert transaction.claim is not None
        assert transaction.claim.claim_id == "CLAIM123"
        assert transaction.claim.total_charge == 150.00
        
        # Verify diagnosis information
        assert len(transaction.diagnoses) == 2
        assert transaction.diagnoses[0].qualifier == "BK"
        assert transaction.diagnoses[0].code == "Z87891"
        
        # Verify service lines
        assert len(transaction.service_lines) == 1
        assert transaction.service_lines[0].procedure_code == "99213"
        assert transaction.service_lines[0].charge_amount == 100.00
        
        # Verify rendering provider
        assert transaction.rendering_provider is not None
        assert transaction.rendering_provider.name == "SMITH"
        assert transaction.rendering_provider.npi == "9876543210"

    def test_837p_integration_with_main_parser(self):
        """Test 837P parsing through main EdiParser."""
        sample_837 = """ISA*00*          *00*          *ZZ*123456789      *ZZ*987654321      *240326*1430*^*00501*000000001*1*T*:~GS*HC*123456789*987654321*20240326*1430*1*X*005010X222A1~ST*837*0001~BHT*0019*00*SAMPLE837*20240326*1430*CH~HL*1**22*1~NM1*85*2*SAMPLE MEDICAL CLINIC*****XX*1234567890~CLM*CLAIM123*150.00*11*1*Y*A*Y*Y~HI*BK:Z87891~LX*1~SV1*HC:99213*100.00*UN*1***1~SE*7*0001~GE*1*1~IEA*1*000000001~"""
        
        schema_path = "packages/core/schemas/x12/837.json"
        parser = EdiParser(sample_837, schema_path)
        root = parser.parse()
        
        # Verify structure
        assert len(root.interchanges) == 1
        interchange = root.interchanges[0]
        assert len(interchange.functional_groups) == 1
        
        functional_group = interchange.functional_groups[0]
        assert len(functional_group.transactions) == 1
        
        transaction = functional_group.transactions[0]
        assert transaction.header["transaction_set_code"] == "837"
        
        # Verify healthcare transaction is present
        assert transaction.healthcare_transaction is not None
        healthcare_tx = transaction.healthcare_transaction
        assert isinstance(healthcare_tx, Transaction837P)
        
        # Verify parsed content
        assert healthcare_tx.billing_provider is not None
        assert healthcare_tx.billing_provider.name == "SAMPLE MEDICAL CLINIC"
        assert healthcare_tx.claim is not None
        assert healthcare_tx.claim.claim_id == "CLAIM123"

    def test_837p_submitter_parsing(self):
        """Test parsing of submitter information."""
        segments = [
            ["HL", "1", "", "20", "1"],
            ["NM1", "41", "2", "SAMPLE BILLING SERVICE", "", "", "", "", "46", "TGJ23"],
            ["PER", "IC", "JOHN DOE", "TE", "5551234567", "EM", "john@sample.com"]
        ]
        
        parser = Parser837P(segments)
        transaction = parser.parse()
        
        assert transaction.submitter is not None
        assert transaction.submitter.name == "SAMPLE BILLING SERVICE"
        assert transaction.submitter.id_code == "TGJ23"
        assert transaction.submitter.contact_name == "JOHN DOE"
        assert transaction.submitter.contact_phone == "5551234567"
        assert transaction.submitter.contact_email == "john@sample.com"

    def test_837p_subscriber_parsing(self):
        """Test parsing of subscriber information."""
        segments = [
            ["HL", "2", "1", "23", "0"],
            ["SBR", "P", "18", "GROUP123", "SAMPLE INSURANCE GROUP", "CI", "", "", "MI", "MEMBER123"],
            ["NM1", "IL", "1", "DOE", "JANE", "M", "", "", "MI", "MEMBER123"],
            ["DMG", "D8", "19850215", "F"]
        ]
        
        parser = Parser837P(segments)
        transaction = parser.parse()
        
        assert transaction.subscriber is not None
        assert transaction.subscriber.payer_responsibility_code == "P"
        assert transaction.subscriber.member_id == "MEMBER123"
        assert transaction.subscriber.first_name == "JANE"
        assert transaction.subscriber.last_name == "DOE"
        assert transaction.subscriber.middle_name == "M"
        assert transaction.subscriber.date_of_birth == "19850215"
        assert transaction.subscriber.gender == "F"

    def test_837p_to_dict_serialization(self):
        """Test JSON serialization of 837P transaction."""
        segments = [
            ["ST", "837", "0001"],
            ["BHT", "0019", "00", "SAMPLE837", "20240326", "1430", "CH"],
            ["HL", "1", "", "22", "0"],
            ["NM1", "85", "2", "SAMPLE MEDICAL CLINIC", "", "", "", "", "XX", "1234567890"],
            ["CLM", "CLAIM123", "150.00", "", "", "11", "Y", "A", "Y", "Y"],
            ["LX", "1"],
            ["SV1", "HC:99213", "100.00", "UN", "1", "", "", "1"]
        ]
        
        parser = Parser837P(segments)
        transaction = parser.parse()
        
        # Test serialization
        data = transaction.to_dict()
        
        assert "header" in data
        assert data["header"]["transaction_set_identifier"] == "837"
        
        assert "billing_provider" in data
        assert data["billing_provider"]["name"] == "SAMPLE MEDICAL CLINIC"
        assert data["billing_provider"]["npi"] == "1234567890"
        
        assert "claim" in data
        assert data["claim"]["claim_id"] == "CLAIM123"
        assert data["claim"]["total_charge"] == 150.00
        
        assert "service_lines" in data
        assert len(data["service_lines"]) == 1
        assert data["service_lines"][0]["procedure_code"] == "99213"

    def test_empty_segments(self):
        """Test parser behavior with empty segments."""
        parser = Parser837P([])
        transaction = parser.parse()
        
        assert isinstance(transaction, Transaction837P)
        assert transaction.header == {}
        assert transaction.submitter is None
        assert transaction.billing_provider is None
        assert transaction.claim is None

    def test_malformed_segments(self):
        """Test parser behavior with malformed segments."""
        segments = [
            ["ST"],  # Missing elements
            ["NM1", "85"],  # Incomplete NM1 segment
            ["CLM", "CLAIM123"]  # Incomplete CLM segment
        ]
        
        parser = Parser837P(segments)
        transaction = parser.parse()
        
        # Should not crash, but data will be minimal
        assert isinstance(transaction, Transaction837P)
        # Parser should handle missing elements gracefully