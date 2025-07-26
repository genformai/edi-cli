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


class TestParser276:
    """Test cases for 276/277 parser functionality."""

    def test_basic_276_parsing(self):
        """Test basic 276 inquiry parsing functionality."""
        # Sample 276 segments
        segments = [
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
        
        parser = Parser276(segments)
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
        
        # Verify provider (billing provider)
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
        
        # Verify claim inquiries
        assert len(transaction.claim_inquiries) == 1
        inquiry = transaction.claim_inquiries[0]
        assert inquiry.claim_control_number == "CLAIM123"
        assert inquiry.total_claim_charge == 250.00
        assert inquiry.date_of_service_from == "20240315"

    def test_basic_277_parsing(self):
        """Test basic 277 response parsing functionality."""
        # Sample 277 segments
        segments = [
            ["ST", "277", "0002"],
            ["BHT", "0010", "11", "CLMSTAT123", "20240326", "1500", "21"],
            ["HL", "1", "", "20", "1"],
            ["NM1", "PR", "2", "SAMPLE INSURANCE COMPANY", "", "", "", "", "PI", "66783"],
            ["HL", "2", "1", "21", "1"],
            ["NM1", "1P", "2", "SAMPLE MEDICAL CLINIC", "", "", "", "", "XX", "1234567890"],
            ["HL", "4", "3", "22", "0"],
            ["TRN", "2", "CLAIM123", "1234567890"],
            ["NM1", "IL", "1", "SMITH", "JOHN", "A", "", "", "MI", "MEMBER456"],
            ["DMG", "D8", "19800101", "M"],
            ["STC", "1", "A1", "20", "20240316", "C7", "250.00"],
            ["MSG", "CLAIM HAS BEEN RECEIVED AND IS BEING PROCESSED"]
        ]
        
        parser = Parser276(segments)
        transaction = parser.parse()
        
        # Verify transaction structure
        assert isinstance(transaction, Transaction277)
        assert transaction.header["transaction_set_identifier"] == "277"
        assert transaction.header["transaction_set_control_number"] == "0002"
        
        # Verify subscriber information
        assert transaction.subscriber is not None
        assert transaction.subscriber.member_id == "MEMBER456"
        assert transaction.subscriber.first_name == "JOHN"
        assert transaction.subscriber.last_name == "SMITH"
        
        # Verify claim status information
        assert len(transaction.claim_status_info) == 1
        status = transaction.claim_status_info[0]
        assert status.entity_identifier_code == "1"
        assert status.status_code == "A1"
        assert status.status_category_code == "20"
        assert status.date_time_period == "20240316"
        assert status.action_code == "C7"
        assert status.monetary_amount == 250.00
        
        # Verify messages
        assert len(transaction.messages) == 1
        assert transaction.messages[0].message_text == "CLAIM HAS BEEN RECEIVED AND IS BEING PROCESSED"

    def test_276_integration_with_main_parser(self):
        """Test 276 parsing through main EdiParser."""
        sample_276 = """ISA*00*          *00*          *ZZ*123456789      *ZZ*987654321      *240326*1430*^*00501*000000001*1*T*:~GS*HI*123456789*987654321*20240326*1430*1*X*005010X212~ST*276*0001~BHT*0010*13*CLMSTAT123*20240326*1430*20~HL*1**20*1~NM1*PR*2*SAMPLE INSURANCE COMPANY*****PI*66783~HL*4*3*22*0~TRN*1*CLAIM123*1234567890~NM1*IL*1*SMITH*JOHN*A***MI*MEMBER456~AMT*T3*250.00~SE*9*0001~GE*1*1~IEA*1*000000001~"""
        
        schema_path = "packages/core/schemas/x12/276.json"
        parser = EdiParser(sample_276, schema_path)
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

    def test_277_integration_with_main_parser(self):
        """Test 277 parsing through main EdiParser."""
        sample_277 = """ISA*00*          *00*          *ZZ*987654321      *ZZ*123456789      *240326*1500*^*00501*000000002*1*T*:~GS*HN*987654321*123456789*20240326*1500*2*X*005010X212~ST*277*0002~BHT*0010*11*CLMSTAT123*20240326*1500*21~HL*1**20*1~NM1*PR*2*SAMPLE INSURANCE COMPANY*****PI*66783~HL*4*3*22*0~TRN*2*CLAIM123*1234567890~NM1*IL*1*SMITH*JOHN*A***MI*MEMBER456~STC*1*A1*20*20240316*C7*250.00~MSG*CLAIM PROCESSED~SE*10*0002~GE*1*2~IEA*1*000000002~"""
        
        schema_path = "packages/core/schemas/x12/277.json"
        parser = EdiParser(sample_277, schema_path)
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

    def test_276_patient_parsing(self):
        """Test parsing of patient information (different from subscriber) in 276."""
        segments = [
            ["ST", "276", "0001"],
            ["BHT", "0010", "13", "CLMSTAT123", "20240326", "1430", "20"],
            ["HL", "4", "3", "22", "1"],  # Subscriber with child
            ["NM1", "IL", "1", "SMITH", "JOHN", "A", "", "", "MI", "MEMBER456"],
            ["HL", "5", "4", "23", "0"],  # Patient (dependent)
            ["NM1", "QC", "1", "SMITH", "JANE", "", "", "", "", ""],
            ["DMG", "D8", "20100315", "F"],
            ["TRN", "1", "CLAIM456", "1234567890"]
        ]
        
        parser = Parser276(segments)
        transaction = parser.parse()
        
        assert transaction.subscriber is not None
        assert transaction.subscriber.member_id == "MEMBER456"
        
        assert transaction.patient is not None
        assert transaction.patient.first_name == "JANE"
        assert transaction.patient.last_name == "SMITH"
        assert transaction.patient.date_of_birth == "20100315"
        assert transaction.patient.gender == "F"

    def test_276_to_dict_serialization(self):
        """Test JSON serialization of 276 transaction."""
        segments = [
            ["ST", "276", "0001"],
            ["BHT", "0010", "13", "CLMSTAT123", "20240326", "1430", "20"],
            ["HL", "1", "", "20", "1"],
            ["NM1", "PR", "2", "SAMPLE INSURANCE COMPANY", "", "", "", "", "PI", "66783"],
            ["HL", "4", "3", "22", "0"],
            ["TRN", "1", "CLAIM123", "1234567890"],
            ["NM1", "IL", "1", "SMITH", "JOHN", "A", "", "", "MI", "MEMBER456"],
            ["AMT", "T3", "150.00"],
            ["DTP", "472", "D8", "20240320"]
        ]
        
        parser = Parser276(segments)
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
        assert len(data["claim_inquiries"]) == 1
        inquiry = data["claim_inquiries"][0]
        assert inquiry["claim_control_number"] == "CLAIM123"
        assert inquiry["total_claim_charge"] == 150.00
        assert inquiry["date_of_service_from"] == "20240320"

    def test_277_to_dict_serialization(self):
        """Test JSON serialization of 277 transaction."""
        segments = [
            ["ST", "277", "0002"],
            ["BHT", "0010", "11", "CLMSTAT123", "20240326", "1500", "21"],
            ["HL", "4", "3", "22", "0"],
            ["NM1", "IL", "1", "SMITH", "JOHN", "A", "", "", "MI", "MEMBER456"],
            ["STC", "1", "A2", "21", "20240317", "C8", "175.00"],
            ["MSG", "CLAIM APPROVED AND PROCESSED"]
        ]
        
        parser = Parser276(segments)
        transaction = parser.parse()
        
        # Test serialization
        data = transaction.to_dict()
        
        assert "header" in data
        assert data["header"]["transaction_set_identifier"] == "277"
        
        assert "subscriber" in data
        assert data["subscriber"]["member_id"] == "MEMBER456"
        
        assert "claim_status_info" in data
        assert len(data["claim_status_info"]) == 1
        
        status = data["claim_status_info"][0]
        assert status["entity_identifier_code"] == "1"
        assert status["status_code"] == "A2"
        assert status["status_category_code"] == "21"
        assert status["date_time_period"] == "20240317"
        assert status["action_code"] == "C8"
        assert status["monetary_amount"] == 175.00
        
        assert "messages" in data
        assert len(data["messages"]) == 1
        assert data["messages"][0]["message_text"] == "CLAIM APPROVED AND PROCESSED"

    def test_277_service_line_status(self):
        """Test parsing of service line status information."""
        segments = [
            ["ST", "277", "0002"],
            ["BHT", "0010", "11", "CLMSTAT123", "20240326", "1500", "21"],
            ["HL", "4", "3", "22", "0"],
            ["NM1", "IL", "1", "SMITH", "JOHN", "A", "", "", "MI", "MEMBER456"],
            ["SVC", "HC:99213", "100.00", "75.00", "", "1"],
            ["STC", "1", "A1", "20", "20240316"],
            ["SVC", "HC:90834", "75.00", "50.00", "", "1"],
            ["STC", "1", "A2", "21", "20240316"]
        ]
        
        parser = Parser276(segments)
        transaction = parser.parse()
        
        # Verify service line status parsing
        assert len(transaction.service_line_status) == 2
        
        service1 = transaction.service_line_status[0]
        assert service1.line_item_control_number == "1"
        assert service1.status_code == "A1"
        assert service1.status_category_code == "20"
        assert service1.monetary_amount == 100.00
        
        service2 = transaction.service_line_status[1]
        assert service2.line_item_control_number == "2"
        assert service2.status_code == "A2"
        assert service2.status_category_code == "21"
        assert service2.monetary_amount == 75.00

    def test_empty_segments(self):
        """Test parser behavior with empty segments."""
        parser = Parser276([])
        transaction = parser.parse()
        
        assert isinstance(transaction, Transaction276)
        assert transaction.header == {}
        assert transaction.information_source is None
        assert transaction.subscriber is None

    def test_malformed_segments(self):
        """Test parser behavior with malformed segments."""
        segments = [
            ["ST"],  # Missing elements
            ["NM1", "PR"],  # Incomplete NM1 segment
            ["STC", "1"]  # Incomplete STC segment
        ]
        
        parser = Parser276(segments)
        transaction = parser.parse()
        
        # Should not crash, but data will be minimal
        assert isinstance(transaction, Transaction276)
        # Parser should handle missing elements gracefully