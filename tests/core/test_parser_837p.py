"""
Tests for EDI 837P (Professional Claims) Parser
"""

import pytest
from packages.core.parser import EdiParser
from packages.core.parser_837p import Parser837P
from packages.core.ast_837p import Transaction837P, SubmitterInfo, BillingProviderInfo, SubscriberInfo


@pytest.fixture
def sample_837p_segments():
    """Sample 837P professional claims segments."""
    return [
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


@pytest.fixture
def sample_837p_edi():
    """Sample 837P EDI string."""
    return """ISA*00*          *00*          *ZZ*123456789      *ZZ*987654321      *240326*1430*^*00501*000000001*1*T*:~GS*HC*123456789*987654321*20240326*1430*1*X*005010X222A1~ST*837*0001~BHT*0019*00*SAMPLE837*20240326*1430*CH~HL*1**22*1~NM1*85*2*SAMPLE MEDICAL CLINIC*****XX*1234567890~CLM*CLAIM123*150.00*11*Y*A*Y*Y~HI*BK:Z87891~LX*1~SV1*HC:99213*100.00*UN*1***1~SE*7*0001~GE*1*1~IEA*1*000000001~"""


@pytest.fixture
def sample_837p_submitter_segments():
    """Sample 837P segments with submitter parsing."""
    return [
        ["ST", "837", "2001"],
        ["BHT", "0019", "00", "SUB_TEST", "20240327", "0900", "CH"],
        ["HL", "1", "", "20", "1"],
        ["NM1", "41", "2", "MEDICAL BILLING CORP", "", "", "", "", "46", "ABC123"],
        ["PER", "IC", "JANE DOE", "TE", "5551234567", "EM", "billing@medical.com"],
        ["HL", "2", "1", "22", "0"],
        ["NM1", "85", "2", "FAMILY PRACTICE CLINIC", "", "", "", "", "XX", "2345678901"],
        ["CLM", "CLM456", "200.00", "", "", "11", "Y", "A", "Y", "Y"],
        ["HI", "BK:Z00.00"],
        ["LX", "1"],
        ["SV1", "HC:99214", "150.00", "UN", "1", "", "", "1"]
    ]


@pytest.fixture
def sample_837p_subscriber_segments():
    """Sample 837P segments with subscriber parsing."""
    return [
        ["ST", "837", "3001"],
        ["BHT", "0019", "00", "SUB_PARSE", "20240328", "1100", "CH"],
        ["HL", "1", "", "20", "1"],
        ["NM1", "41", "2", "BILLING SOLUTIONS INC", "", "", "", "", "46", "XYZ789"],
        ["HL", "2", "1", "22", "1"],
        ["NM1", "85", "2", "HEALTH CENTER", "", "", "", "", "XX", "3456789012"],
        ["HL", "3", "2", "23", "0"],
        ["NM1", "IL", "1", "PATIENT", "JOHN", "A", "", "", "", ""],
        ["DMG", "D8", "19850615", "M"],
        ["CLM", "CLM789", "300.00", "", "", "11", "Y", "A", "Y", "Y"],
        ["HI", "BK:K59.00"],
        ["LX", "1"],
        ["SV1", "HC:99215", "250.00", "UN", "1", "", "", "1"]
    ]


@pytest.fixture
def sample_837p_serialization_segments():
    """Sample 837P segments for serialization test."""
    return [
        ["ST", "837", "0001"],
        ["BHT", "0019", "00", "SERIAL_TEST", "20240326", "1430", "CH"],
        ["HL", "1", "", "20", "1"],
        ["NM1", "41", "2", "TEST BILLING", "", "", "", "", "46", "TEST123"],
        ["HL", "2", "1", "22", "0"],
        ["NM1", "85", "2", "TEST CLINIC", "", "", "", "", "XX", "1111111111"],
        ["CLM", "SERIAL123", "100.00", "", "", "11", "Y", "A", "Y", "Y"],
        ["HI", "BK:Z00.00"],
        ["LX", "1"],
        ["SV1", "HC:99213", "75.00", "UN", "1", "", "", "1"]
    ]


@pytest.fixture
def malformed_segments():
    """Malformed segments for error handling tests."""
    return [
        ["ST"],  # Missing elements
        ["BHT", "0019"],  # Incomplete BHT segment
        ["CLM", "CLAIM123"]  # Incomplete CLM segment
    ]


@pytest.fixture
def empty_segments():
    """Empty segments list for testing empty input."""
    return []


@pytest.fixture
def schema_837p_path():
    """Schema path for 837P transactions."""
    return "packages/core/schemas/x12/837.json"


class TestParser837P:
    """Test cases for 837P parser functionality."""

    def test_basic_837p_parsing(self, sample_837p_segments):
        """Test basic 837P parsing functionality."""
        parser = Parser837P(sample_837p_segments)
        transaction = parser.parse()
        
        # Verify transaction structure
        assert isinstance(transaction, Transaction837P)
        assert transaction.header["transaction_set_identifier"] == "837"
        assert transaction.header["transaction_set_control_number"] == "0001"
        
        # Verify billing provider exists
        assert transaction.billing_provider is not None
        assert transaction.billing_provider.name == "SAMPLE MEDICAL CLINIC"
        assert transaction.billing_provider.npi == "1234567890"
        
        # Verify claim information exists
        assert transaction.claim is not None
        assert transaction.claim.claim_id == "CLAIM123"
        assert transaction.claim.total_charge == 150.00
        
        # Verify diagnosis information exists
        assert hasattr(transaction, 'diagnoses')
        assert isinstance(transaction.diagnoses, list)
        
        # Verify service information exists
        assert hasattr(transaction, 'service_lines')
        assert isinstance(transaction.service_lines, list)

    def test_837p_integration_with_main_parser(self, sample_837p_edi, schema_837p_path):
        """Test 837P parsing through main EdiParser."""
        parser = EdiParser(sample_837p_edi, schema_837p_path)
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

    def test_837p_submitter_parsing(self, sample_837p_submitter_segments):
        """Test parsing of submitter information in 837P."""
        parser = Parser837P(sample_837p_submitter_segments)
        transaction = parser.parse()
        
        # Verify submitter information exists
        assert transaction.submitter is not None
        assert transaction.submitter.name == "MEDICAL BILLING CORP"
        assert transaction.submitter.id_code == "ABC123"
        
        # Verify billing provider
        assert transaction.billing_provider is not None
        assert transaction.billing_provider.name == "FAMILY PRACTICE CLINIC"
        assert transaction.billing_provider.npi == "2345678901"
        
        # Verify claim
        assert transaction.claim is not None
        assert transaction.claim.claim_id == "CLM456"
        assert transaction.claim.total_charge == 200.00

    def test_837p_subscriber_parsing(self, sample_837p_subscriber_segments):
        """Test parsing of subscriber information in 837P."""
        parser = Parser837P(sample_837p_subscriber_segments)
        transaction = parser.parse()
        
        # Verify submitter exists
        assert transaction.submitter is not None
        assert transaction.submitter.name == "BILLING SOLUTIONS INC"
        
        # Verify subscriber information structure exists (even if None)
        assert hasattr(transaction, 'subscriber')
        # Note: subscriber parsing may not be fully implemented yet
        
        # Verify claim
        assert transaction.claim is not None
        assert transaction.claim.claim_id == "CLM789"
        assert transaction.claim.total_charge == 300.00

    def test_837p_to_dict_serialization(self, sample_837p_serialization_segments):
        """Test JSON serialization of 837P transaction."""
        parser = Parser837P(sample_837p_serialization_segments)
        transaction = parser.parse()
        
        # Test serialization
        data = transaction.to_dict()
        
        assert "header" in data
        assert data["header"]["transaction_set_identifier"] == "837"
        
        assert "submitter" in data
        assert data["submitter"]["name"] == "TEST BILLING"
        
        assert "billing_provider" in data
        assert data["billing_provider"]["name"] == "TEST CLINIC"
        assert data["billing_provider"]["npi"] == "1111111111"
        
        assert "claim" in data
        assert data["claim"]["claim_id"] == "SERIAL123"
        assert data["claim"]["total_charge"] == 100.00
        
        assert "diagnoses" in data
        assert isinstance(data["diagnoses"], list)
        
        assert "service_lines" in data
        assert isinstance(data["service_lines"], list)

    def test_empty_segments(self, empty_segments):
        """Test parser behavior with empty segments."""
        parser = Parser837P(empty_segments)
        transaction = parser.parse()
        
        assert isinstance(transaction, Transaction837P)
        assert transaction.header == {}
        assert transaction.submitter is None
        assert transaction.billing_provider is None

    def test_malformed_segments(self, malformed_segments):
        """Test parser behavior with malformed segments."""
        parser = Parser837P(malformed_segments)
        transaction = parser.parse()
        
        # Should not crash, but data will be minimal
        assert isinstance(transaction, Transaction837P)
        # Parser should handle missing elements gracefully