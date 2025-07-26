"""
Tests for EDI 276/277 (Claim Status Inquiry/Response) Parser
"""

import pytest
from packages.core.parser import EdiParser
from packages.core.parser_276 import Parser276
from packages.core.ast_276 import (
    Transaction276, Transaction277, InformationSourceInfo276, InformationReceiverInfo276,
    ProviderInfo276, SubscriberInfo276, ClaimStatusInquiry, ClaimStatusInfo
)


@pytest.fixture
def sample_276_segments():
    """Sample 276 inquiry segments."""
    return [
        ["ST", "276", "0001"],
        ["BHT", "0010", "13", "CLMSTAT123", "20240326", "1430", "20"],
        ["HL", "1", "", "20", "1"],
        ["NM1", "PR", "2", "SAMPLE INSURANCE COMPANY", "", "", "", "", "PI", "66783"],
        ["HL", "2", "1", "21", "1"],
        ["NM1", "1P", "2", "SAMPLE MEDICAL CLINIC", "", "", "", "", "XX", "1234567890"],
        ["HL", "3", "2", "19", "1"],
        ["NM1", "85", "2", "BILLING PROVIDER CLINIC", "", "", "", "", "XX", "9876543210"],
        ["HL", "4", "3", "22", "0"],
        ["TRN", "1", "CLAIM123", "1234567890"],
        ["NM1", "IL", "1", "SMITH", "JOHN", "A", "", "", "MI", "MEMBER456"],
        ["DMG", "D8", "19800101", "M"],
        ["AMT", "T3", "250.00"],
        ["DTP", "472", "D8", "20240315"]
    ]


@pytest.fixture
def sample_277_segments():
    """Sample 277 response segments."""
    return [
        ["ST", "277", "0002"],
        ["BHT", "0010", "11", "CLMSTAT123", "20240326", "1500", "21"],
        ["HL", "1", "", "20", "1"],
        ["NM1", "PR", "2", "SAMPLE INSURANCE COMPANY", "", "", "", "", "PI", "66783"],
        ["HL", "4", "3", "22", "0"],
        ["TRN", "2", "CLAIM123", "1234567890"],
        ["NM1", "IL", "1", "SMITH", "JOHN", "A", "", "", "MI", "MEMBER456"],
        ["STC", "1", "A1", "20", "20240316", "C7", "250.00"],
        ["MSG", "CLAIM PROCESSED"],
        ["SVC", "HC:99213", "1", "100.00", "100.00"],
        ["STC", "1", "A2", "30", "20240316", "C7", "100.00"]
    ]


@pytest.fixture
def sample_276_edi():
    """Sample 276 EDI string."""
    return """ISA*00*          *00*          *ZZ*123456789      *ZZ*987654321      *240326*1430*^*00501*000000001*1*T*:~GS*HI*123456789*987654321*20240326*1430*1*X*005010X212~ST*276*0001~BHT*0010*13*CLMSTAT123*20240326*1430*20~HL*1**20*1~NM1*PR*2*SAMPLE INSURANCE COMPANY*****PI*66783~HL*4*3*22*0~TRN*1*CLAIM123*1234567890~NM1*IL*1*SMITH*JOHN*A***MI*MEMBER456~SE*8*0001~GE*1*1~IEA*1*000000001~"""


@pytest.fixture
def sample_277_edi():
    """Sample 277 EDI string."""
    return """ISA*00*          *00*          *ZZ*987654321      *ZZ*123456789      *240326*1500*^*00501*000000002*1*T*:~GS*HN*987654321*123456789*20240326*1500*2*X*005010X212~ST*277*0002~BHT*0010*11*CLMSTAT123*20240326*1500*21~HL*1**20*1~NM1*PR*2*SAMPLE INSURANCE COMPANY*****PI*66783~HL*4*3*22*0~TRN*2*CLAIM123*1234567890~NM1*IL*1*SMITH*JOHN*A***MI*MEMBER456~STC*1*A1*20*20240316*C7*250.00~MSG*CLAIM PROCESSED~SE*10*0002~GE*1*2~IEA*1*000000002~"""


@pytest.fixture
def sample_276_patient_segments():
    """Sample 276 segments with patient parsing."""
    return [
        ["ST", "276", "3001"],
        ["BHT", "0010", "13", "INQUIRY456", "20240325", "1200", "20"],
        ["HL", "1", "", "20", "1"],
        ["NM1", "PR", "2", "ABC INSURANCE", "", "", "", "", "PI", "12345"],
        ["HL", "4", "1", "22", "0"],
        ["TRN", "1", "CLM001", "REF12345"],
        ["NM1", "IL", "1", "DOE", "JANE", "", "", "", "MI", "MBR789"],
        ["DMG", "D8", "19900201", "F"],
        ["AMT", "T3", "150.00"],
        ["DTP", "472", "D8", "20240310"]
    ]


@pytest.fixture
def sample_276_serialization_segments():
    """Sample 276 segments for serialization test."""
    return [
        ["ST", "276", "0001"],
        ["BHT", "0010", "13", "CLMSTAT123", "20240326", "1430", "20"],
        ["HL", "1", "", "20", "1"],
        ["NM1", "PR", "2", "SAMPLE INSURANCE COMPANY", "", "", "", "", "PI", "66783"],
        ["HL", "4", "1", "22", "0"],
        ["TRN", "1", "CLAIM123", "1234567890"],
        ["NM1", "IL", "1", "SMITH", "JOHN", "A", "", "", "MI", "MEMBER456"],
        ["AMT", "T3", "250.00"],
        ["DTP", "472", "D8", "20240315"]
    ]


@pytest.fixture
def sample_277_serialization_segments():
    """Sample 277 segments for serialization test."""
    return [
        ["ST", "277", "0002"],
        ["BHT", "0010", "11", "CLMSTAT123", "20240326", "1500", "21"],
        ["HL", "1", "", "20", "1"],
        ["NM1", "PR", "2", "SAMPLE INSURANCE COMPANY", "", "", "", "", "PI", "66783"],
        ["HL", "4", "1", "22", "0"],
        ["TRN", "2", "CLAIM123", "1234567890"],
        ["NM1", "IL", "1", "SMITH", "JOHN", "A", "", "", "MI", "MEMBER456"],
        ["STC", "1", "A1", "20", "20240316", "C7", "100.00"],
        ["MSG", "CLAIM WAS PROCESSED SUCCESSFULLY"]
    ]


@pytest.fixture
def sample_277_service_segments():
    """Sample 277 segments with service line status."""
    return [
        ["ST", "277", "4001"],
        ["BHT", "0010", "11", "STATUS789", "20240328", "1000", "21"],
        ["HL", "1", "", "20", "1"],
        ["NM1", "PR", "2", "XYZ INSURANCE", "", "", "", "", "PI", "54321"],
        ["HL", "4", "1", "22", "0"],
        ["TRN", "2", "CLM999", "REF999"],
        ["NM1", "IL", "1", "PATIENT", "TEST", "", "", "", "MI", "PAT001"],
        ["STC", "1", "A3", "20", "20240325", "C7", "200.00"],
        ["SVC", "HC:99214", "1", "200.00", "180.00"],
        ["STC", "1", "A1", "30", "20240325", "C7", "180.00"],
        ["MSG", "SERVICE APPROVED WITH ADJUSTMENT"]
    ]


@pytest.fixture
def malformed_segments():
    """Malformed segments for error handling tests."""
    return [
        ["ST"],  # Missing elements
        ["TRN", "1"],  # Incomplete TRN segment
        ["STC", "1"]  # Incomplete STC segment
    ]


@pytest.fixture
def empty_segments():
    """Empty segments list for testing empty input."""
    return []


@pytest.fixture
def schema_276_path():
    """Schema path for 276 transactions."""
    return "packages/core/schemas/x12/276.json"


@pytest.fixture
def schema_277_path():
    """Schema path for 277 transactions."""
    return "packages/core/schemas/x12/277.json"


class TestParser276:
    """Test cases for 276/277 parser functionality."""

    def test_basic_276_parsing(self, sample_276_segments):
        """Test basic 276 inquiry parsing functionality."""
        parser = Parser276(sample_276_segments)
        transaction = parser.parse()
        
        # Verify transaction structure
        assert isinstance(transaction, Transaction276)
        assert transaction.header["transaction_set_identifier"] == "276"
        assert transaction.header["transaction_set_control_number"] == "0001"
        
        # Verify information source (payer)
        assert transaction.information_source is not None
        assert transaction.information_source.name == "SAMPLE INSURANCE COMPANY"
        assert transaction.information_source.id_code == "66783"
        
        # Verify information receiver (clinic)
        assert transaction.information_receiver is not None
        assert transaction.information_receiver.name == "SAMPLE MEDICAL CLINIC"
        assert transaction.information_receiver.npi == "1234567890"
        
        # Verify provider info
        assert transaction.provider is not None
        assert transaction.provider.name == "BILLING PROVIDER CLINIC"
        assert transaction.provider.npi == "9876543210"
        
        # Verify subscriber information
        assert transaction.subscriber is not None
        assert transaction.subscriber.member_id == "MEMBER456"
        assert transaction.subscriber.first_name == "JOHN"
        assert transaction.subscriber.last_name == "SMITH"
        assert transaction.subscriber.middle_name == "A"
        assert transaction.subscriber.date_of_birth == "19800101"
        assert transaction.subscriber.gender == "M"
        
        # Verify claim inquiries structure exists
        assert hasattr(transaction, 'claim_inquiries')
        assert isinstance(transaction.claim_inquiries, list)

    def test_basic_277_parsing(self, sample_277_segments):
        """Test basic 277 response parsing functionality."""
        parser = Parser276(sample_277_segments)
        transaction = parser.parse()
        
        # Verify transaction structure
        assert isinstance(transaction, Transaction277)
        assert transaction.header["transaction_set_identifier"] == "277"
        assert transaction.header["transaction_set_control_number"] == "0002"
        
        # Verify information source (payer)
        assert transaction.information_source is not None
        assert transaction.information_source.name == "SAMPLE INSURANCE COMPANY"
        assert transaction.information_source.id_code == "66783"
        
        # Verify subscriber information
        assert transaction.subscriber is not None
        assert transaction.subscriber.member_id == "MEMBER456"
        assert transaction.subscriber.first_name == "JOHN"
        assert transaction.subscriber.last_name == "SMITH"
        assert transaction.subscriber.middle_name == "A"
        
        # Verify claim status information structure
        assert len(transaction.claim_status_info) >= 1
        status_info = transaction.claim_status_info[0]
        assert status_info.status_code == "A1"
        assert status_info.status_category_code == "20"
        
        # Verify messages
        assert len(transaction.messages) == 1
        assert transaction.messages[0].message_text == "CLAIM PROCESSED"
        
        # Verify service line status
        assert len(transaction.service_line_status) == 1
        service_status = transaction.service_line_status[0]
        assert service_status.line_item_control_number == "1"
        assert service_status.status_code == "A2"
        assert service_status.status_category_code == "30"
        assert service_status.date_time_period == "20240316"

    def test_276_integration_with_main_parser(self, sample_276_edi, schema_276_path):
        """Test 276 parsing through main EdiParser."""
        parser = EdiParser(sample_276_edi, schema_276_path)
        root = parser.parse()
        
        # Verify structure
        assert len(root.interchanges) == 1
        interchange = root.interchanges[0]
        assert len(interchange.functional_groups) == 1
        
        functional_group = interchange.functional_groups[0]
        assert len(functional_group.transactions) == 1
        
        transaction = functional_group.transactions[0]
        assert transaction.header["transaction_set_code"] == "276"
        
        # Verify healthcare transaction is present
        assert transaction.healthcare_transaction is not None
        healthcare_tx = transaction.healthcare_transaction
        assert isinstance(healthcare_tx, Transaction276)
        
        # Verify parsed content
        assert healthcare_tx.information_source is not None
        assert healthcare_tx.information_source.name == "SAMPLE INSURANCE COMPANY"
        assert healthcare_tx.subscriber is not None
        assert healthcare_tx.subscriber.member_id == "MEMBER456"

    def test_277_integration_with_main_parser(self, sample_277_edi, schema_277_path):
        """Test 277 parsing through main EdiParser."""
        parser = EdiParser(sample_277_edi, schema_277_path)
        root = parser.parse()
        
        # Verify structure
        assert len(root.interchanges) == 1
        interchange = root.interchanges[0]
        assert len(interchange.functional_groups) == 1
        
        functional_group = interchange.functional_groups[0]
        assert len(functional_group.transactions) == 1
        
        transaction = functional_group.transactions[0]
        assert transaction.header["transaction_set_code"] == "277"
        
        # Verify healthcare transaction is present
        assert transaction.healthcare_transaction is not None
        healthcare_tx = transaction.healthcare_transaction
        assert isinstance(healthcare_tx, Transaction277)
        
        # Verify parsed content
        assert healthcare_tx.information_source is not None
        assert healthcare_tx.information_source.name == "SAMPLE INSURANCE COMPANY"
        assert healthcare_tx.subscriber is not None
        assert healthcare_tx.subscriber.member_id == "MEMBER456"
        assert len(healthcare_tx.claim_status_info) == 1
        assert len(healthcare_tx.messages) == 1

    def test_276_patient_parsing(self, sample_276_patient_segments):
        """Test parsing of patient information in 276."""
        parser = Parser276(sample_276_patient_segments)
        transaction = parser.parse()
        
        # Verify subscriber information
        assert transaction.subscriber is not None
        assert transaction.subscriber.member_id == "MBR789"
        assert transaction.subscriber.first_name == "JANE"
        assert transaction.subscriber.last_name == "DOE"
        assert transaction.subscriber.date_of_birth == "19900201"
        assert transaction.subscriber.gender == "F"
        
        # Verify claim inquiry structure
        assert hasattr(transaction, 'claim_inquiries')
        assert isinstance(transaction.claim_inquiries, list)

    def test_276_to_dict_serialization(self, sample_276_serialization_segments):
        """Test JSON serialization of 276 transaction."""
        parser = Parser276(sample_276_serialization_segments)
        transaction = parser.parse()
        
        # Test serialization
        data = transaction.to_dict()
        
        assert "header" in data
        assert data["header"]["transaction_set_identifier"] == "276"
        
        assert "information_source" in data
        assert data["information_source"]["name"] == "SAMPLE INSURANCE COMPANY"
        
        assert "subscriber" in data
        assert data["subscriber"]["member_id"] == "MEMBER456"
        assert data["subscriber"]["first_name"] == "JOHN"
        
        assert "claim_inquiries" in data
        assert isinstance(data["claim_inquiries"], list)

    def test_277_to_dict_serialization(self, sample_277_serialization_segments):
        """Test JSON serialization of 277 transaction."""
        parser = Parser276(sample_277_serialization_segments)
        transaction = parser.parse()
        
        # Test serialization
        data = transaction.to_dict()
        
        assert "header" in data
        assert data["header"]["transaction_set_identifier"] == "277"
        
        assert "information_source" in data
        assert data["information_source"]["name"] == "SAMPLE INSURANCE COMPANY"
        
        assert "subscriber" in data
        assert data["subscriber"]["member_id"] == "MEMBER456"
        
        assert "claim_status_info" in data
        assert len(data["claim_status_info"]) == 1
        
        status_info = data["claim_status_info"][0]
        assert status_info["entity_identifier_code"] == "1"
        assert status_info["status_code"] == "A1"
        assert status_info["status_category_code"] == "20"
        assert status_info["date_time_period"] == "20240316"
        assert status_info["monetary_amount"] == 100.00
        
        assert "messages" in data
        assert len(data["messages"]) == 1
        assert data["messages"][0]["message_text"] == "CLAIM WAS PROCESSED SUCCESSFULLY"

    def test_277_service_line_status(self, sample_277_service_segments):
        """Test parsing of service line status in 277."""
        parser = Parser276(sample_277_service_segments)
        transaction = parser.parse()
        
        # Verify claim status (should have 2 status records)
        assert len(transaction.claim_status_info) == 2
        status_info = transaction.claim_status_info[0]
        assert status_info.status_code == "A3"
        assert status_info.monetary_amount == 200.00
        
        # Verify service line status
        assert len(transaction.service_line_status) == 1
        service_status = transaction.service_line_status[0]
        assert service_status.line_item_control_number == "1"
        assert service_status.status_code == "A1"
        assert service_status.status_category_code == "30"
        assert service_status.date_time_period == "20240325"
        
        # Verify message
        assert len(transaction.messages) == 1
        assert transaction.messages[0].message_text == "SERVICE APPROVED WITH ADJUSTMENT"

    def test_empty_segments(self, empty_segments):
        """Test parser behavior with empty segments."""
        parser = Parser276(empty_segments)
        transaction = parser.parse()
        
        assert isinstance(transaction, Transaction276)
        assert transaction.header == {}
        assert transaction.information_source is None
        assert transaction.subscriber is None

    def test_malformed_segments(self, malformed_segments):
        """Test parser behavior with malformed segments."""
        parser = Parser276(malformed_segments)
        transaction = parser.parse()
        
        # Should not crash, but data will be minimal
        assert isinstance(transaction, Transaction276)
        # Parser should handle missing elements gracefully