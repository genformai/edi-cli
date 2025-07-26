"""
Tests for EDI 270/271 (Eligibility Inquiry/Response) Parser
"""

import pytest
from packages.core.parser import EdiParser
from packages.core.parser_270 import Parser270
from packages.core.ast_270 import (
    Transaction270, Transaction271, InformationSourceInfo, InformationReceiverInfo,
    SubscriberEligibilityInfo, EligibilityInquiry, EligibilityBenefit
)


class TestParser270:
    """Test cases for 270/271 parser functionality."""

    def test_basic_270_parsing(self):
        """Test basic 270 inquiry parsing functionality."""
        # Sample 270 segments
        segments = [
            ["ST", "270", "0001"],
            ["BHT", "0022", "13", "INQUIRY123", "20240326", "1430", "EH"],
            ["HL", "1", "", "20", "1"],
            ["NM1", "PR", "2", "SAMPLE INSURANCE COMPANY", "", "", "", "", "PI", "66783"],
            ["HL", "2", "1", "21", "1"],
            ["NM1", "1P", "2", "SAMPLE MEDICAL CLINIC", "", "", "", "", "XX", "1234567890"],
            ["HL", "3", "2", "22", "0"],
            ["NM1", "IL", "1", "DOE", "JANE", "M", "", "", "MI", "MEMBER123"],
            ["DMG", "D8", "19850215", "F"],
            ["EQ", "30"]
        ]
        
        parser = Parser270(segments)
        transaction = parser.parse()
        
        # Verify transaction structure
        assert isinstance(transaction, Transaction270)
        assert transaction.header["transaction_set_identifier"] == "270"
        assert transaction.header["transaction_set_control_number"] == "0001"
        
        # Verify information source (payer)
        assert transaction.information_source is not None
        assert transaction.information_source.name == "SAMPLE INSURANCE COMPANY"
        assert transaction.information_source.id_code == "66783"
        
        # Verify information receiver (provider)
        assert transaction.information_receiver is not None
        assert transaction.information_receiver.name == "SAMPLE MEDICAL CLINIC"
        assert transaction.information_receiver.npi == "1234567890"
        
        # Verify subscriber information
        assert transaction.subscriber is not None
        assert transaction.subscriber.member_id == "MEMBER123"
        assert transaction.subscriber.first_name == "JANE"
        assert transaction.subscriber.last_name == "DOE"
        assert transaction.subscriber.middle_name == "M"
        assert transaction.subscriber.date_of_birth == "19850215"
        assert transaction.subscriber.gender == "F"
        
        # Verify eligibility inquiries
        assert len(transaction.eligibility_inquiries) == 1
        assert transaction.eligibility_inquiries[0].service_type_code == "30"

    def test_basic_271_parsing(self):
        """Test basic 271 response parsing functionality."""
        # Sample 271 segments
        segments = [
            ["ST", "271", "0002"],
            ["BHT", "0022", "11", "INQUIRY123", "20240326", "1500", "RT"],
            ["HL", "1", "", "20", "1"],
            ["NM1", "PR", "2", "SAMPLE INSURANCE COMPANY", "", "", "", "", "PI", "66783"],
            ["HL", "2", "1", "21", "1"],
            ["NM1", "1P", "2", "SAMPLE MEDICAL CLINIC", "", "", "", "", "XX", "1234567890"],
            ["HL", "3", "2", "22", "0"],
            ["NM1", "IL", "1", "DOE", "JANE", "M", "", "", "MI", "MEMBER123"],
            ["DMG", "D8", "19850215", "F"],
            ["EB", "1", "IND", "30", "", "", "1", "100.00", "", "", "", "Y", "Y"],
            ["EB", "B", "IND", "1", "", "", "1", "25.00", "", "", "", "Y", "Y"],
            ["MSG", "MEMBER IS ELIGIBLE FOR BENEFITS"]
        ]
        
        parser = Parser270(segments)
        transaction = parser.parse()
        
        # Verify transaction structure
        assert isinstance(transaction, Transaction271)
        assert transaction.header["transaction_set_identifier"] == "271"
        assert transaction.header["transaction_set_control_number"] == "0002"
        
        # Verify subscriber information
        assert transaction.subscriber is not None
        assert transaction.subscriber.member_id == "MEMBER123"
        assert transaction.subscriber.first_name == "JANE"
        assert transaction.subscriber.last_name == "DOE"
        
        # Verify eligibility benefits
        assert len(transaction.eligibility_benefits) == 2
        
        benefit1 = transaction.eligibility_benefits[0]
        assert benefit1.eligibility_code == "1"
        assert benefit1.coverage_level_code == "IND"
        assert benefit1.service_type_code == "30"
        assert benefit1.monetary_amount == 100.00
        assert benefit1.in_plan_network == "Y"
        
        benefit2 = transaction.eligibility_benefits[1]
        assert benefit2.eligibility_code == "B"
        assert benefit2.monetary_amount == 25.00
        
        # Verify messages
        assert len(transaction.messages) == 1
        assert transaction.messages[0].message_text == "MEMBER IS ELIGIBLE FOR BENEFITS"

    def test_270_integration_with_main_parser(self):
        """Test 270 parsing through main EdiParser."""
        sample_270 = """ISA*00*          *00*          *ZZ*123456789      *ZZ*987654321      *240326*1430*^*00501*000000001*1*T*:~GS*HS*123456789*987654321*20240326*1430*1*X*005010X279A1~ST*270*0001~BHT*0022*13*INQUIRY123*20240326*1430*EH~HL*1**20*1~NM1*PR*2*SAMPLE INSURANCE COMPANY*****PI*66783~HL*2*1*21*1~NM1*1P*2*SAMPLE MEDICAL CLINIC*****XX*1234567890~HL*3*2*22*0~NM1*IL*1*DOE*JANE*M***MI*MEMBER123~EQ*30~SE*11*0001~GE*1*1~IEA*1*000000001~"""
        
        schema_path = "packages/core/schemas/x12/270.json"
        parser = EdiParser(sample_270, schema_path)
        root = parser.parse()
        
        # Verify structure
        assert len(root.interchanges) == 1
        interchange = root.interchanges[0]
        assert len(interchange.functional_groups) == 1
        
        functional_group = interchange.functional_groups[0]
        assert len(functional_group.transactions) == 1
        
        transaction = functional_group.transactions[0]
        assert transaction.header["transaction_set_code"] == "270"
        
        # Verify healthcare transaction is present
        assert transaction.healthcare_transaction is not None
        healthcare_tx = transaction.healthcare_transaction
        assert isinstance(healthcare_tx, Transaction270)
        
        # Verify parsed content
        assert healthcare_tx.information_source is not None
        assert healthcare_tx.information_source.name == "SAMPLE INSURANCE COMPANY"
        assert healthcare_tx.subscriber is not None
        assert healthcare_tx.subscriber.member_id == "MEMBER123"

    def test_271_integration_with_main_parser(self):
        """Test 271 parsing through main EdiParser."""
        sample_271 = """ISA*00*          *00*          *ZZ*987654321      *ZZ*123456789      *240326*1500*^*00501*000000002*1*T*:~GS*HB*987654321*123456789*20240326*1500*2*X*005010X279A1~ST*271*0002~BHT*0022*11*INQUIRY123*20240326*1500*RT~HL*1**20*1~NM1*PR*2*SAMPLE INSURANCE COMPANY*****PI*66783~HL*2*1*21*1~NM1*1P*2*SAMPLE MEDICAL CLINIC*****XX*1234567890~HL*3*2*22*0~NM1*IL*1*DOE*JANE*M***MI*MEMBER123~EB*1*IND*30***1*100.00***Y*Y~MSG*MEMBER IS ELIGIBLE FOR BENEFITS~SE*13*0002~GE*1*2~IEA*1*000000002~"""
        
        schema_path = "packages/core/schemas/x12/271.json"
        parser = EdiParser(sample_271, schema_path)
        root = parser.parse()
        
        # Verify structure
        assert len(root.interchanges) == 1
        interchange = root.interchanges[0]
        assert len(interchange.functional_groups) == 1
        
        functional_group = interchange.functional_groups[0]
        assert len(functional_group.transactions) == 1
        
        transaction = functional_group.transactions[0]
        assert transaction.header["transaction_set_code"] == "271"
        
        # Verify healthcare transaction is present
        assert transaction.healthcare_transaction is not None
        healthcare_tx = transaction.healthcare_transaction
        assert isinstance(healthcare_tx, Transaction271)
        
        # Verify parsed content
        assert healthcare_tx.information_source is not None
        assert healthcare_tx.information_source.name == "SAMPLE INSURANCE COMPANY"
        assert healthcare_tx.subscriber is not None
        assert healthcare_tx.subscriber.member_id == "MEMBER123"
        assert len(healthcare_tx.eligibility_benefits) == 1
        assert len(healthcare_tx.messages) == 1

    def test_270_dependent_parsing(self):
        """Test parsing of dependent information in 270."""
        segments = [
            ["ST", "270", "0001"],
            ["BHT", "0022", "13", "INQUIRY123", "20240326", "1430", "EH"],
            ["HL", "3", "2", "22", "1"],  # Subscriber with child
            ["NM1", "IL", "1", "DOE", "JANE", "M", "", "", "MI", "MEMBER123"],
            ["HL", "4", "3", "23", "0"],  # Dependent
            ["NM1", "03", "1", "DOE", "JOHN", "", "", "", "", ""],
            ["DMG", "D8", "20100315", "M"],
            ["EQ", "30"]
        ]
        
        parser = Parser270(segments)
        transaction = parser.parse()
        
        assert transaction.subscriber is not None
        assert transaction.subscriber.member_id == "MEMBER123"
        
        assert transaction.dependent is not None
        assert transaction.dependent.first_name == "JOHN"
        assert transaction.dependent.last_name == "DOE"
        assert transaction.dependent.date_of_birth == "20100315"
        assert transaction.dependent.gender == "M"

    def test_270_to_dict_serialization(self):
        """Test JSON serialization of 270 transaction."""
        segments = [
            ["ST", "270", "0001"],
            ["BHT", "0022", "13", "INQUIRY123", "20240326", "1430", "EH"],
            ["HL", "1", "", "20", "1"],
            ["NM1", "PR", "2", "SAMPLE INSURANCE COMPANY", "", "", "", "", "PI", "66783"],
            ["HL", "3", "2", "22", "0"],
            ["NM1", "IL", "1", "DOE", "JANE", "M", "", "", "MI", "MEMBER123"],
            ["EQ", "30", "IND", "HLT"]
        ]
        
        parser = Parser270(segments)
        transaction = parser.parse()
        
        # Test serialization
        data = transaction.to_dict()
        
        assert "header" in data
        assert data["header"]["transaction_set_identifier"] == "270"
        
        assert "information_source" in data
        assert data["information_source"]["name"] == "SAMPLE INSURANCE COMPANY"
        
        assert "subscriber" in data
        assert data["subscriber"]["member_id"] == "MEMBER123"
        assert data["subscriber"]["first_name"] == "JANE"
        
        assert "eligibility_inquiries" in data
        assert len(data["eligibility_inquiries"]) == 1
        assert data["eligibility_inquiries"][0]["service_type_code"] == "30"
        assert data["eligibility_inquiries"][0]["coverage_level_code"] == "IND"
        assert data["eligibility_inquiries"][0]["insurance_type_code"] == "HLT"

    def test_271_to_dict_serialization(self):
        """Test JSON serialization of 271 transaction."""
        segments = [
            ["ST", "271", "0002"],
            ["BHT", "0022", "11", "INQUIRY123", "20240326", "1500", "RT"],
            ["HL", "3", "2", "22", "0"],
            ["NM1", "IL", "1", "DOE", "JANE", "M", "", "", "MI", "MEMBER123"],
            ["EB", "1", "IND", "30", "HEALTH", "", "1", "100.00", "80.5", "", "", "Y", "Y"],
            ["MSG", "BENEFITS AVAILABLE"]
        ]
        
        parser = Parser270(segments)
        transaction = parser.parse()
        
        # Test serialization
        data = transaction.to_dict()
        
        assert "header" in data
        assert data["header"]["transaction_set_identifier"] == "271"
        
        assert "subscriber" in data
        assert data["subscriber"]["member_id"] == "MEMBER123"
        
        assert "eligibility_benefits" in data
        assert len(data["eligibility_benefits"]) == 1
        
        benefit = data["eligibility_benefits"][0]
        assert benefit["eligibility_code"] == "1"
        assert benefit["coverage_level_code"] == "IND"
        assert benefit["service_type_code"] == "30"
        assert benefit["insurance_type_code"] == "HEALTH"
        assert benefit["time_period_qualifier"] == "1"
        assert benefit["monetary_amount"] == 100.00
        assert benefit["percentage"] == 80.5
        assert benefit["authorization_required"] == "Y"
        assert benefit["in_plan_network"] == "Y"
        
        assert "messages" in data
        assert len(data["messages"]) == 1
        assert data["messages"][0]["message_text"] == "BENEFITS AVAILABLE"

    def test_empty_segments(self):
        """Test parser behavior with empty segments."""
        parser = Parser270([])
        transaction = parser.parse()
        
        assert isinstance(transaction, Transaction270)
        assert transaction.header == {}
        assert transaction.information_source is None
        assert transaction.subscriber is None

    def test_malformed_segments(self):
        """Test parser behavior with malformed segments."""
        segments = [
            ["ST"],  # Missing elements
            ["NM1", "PR"],  # Incomplete NM1 segment
            ["EB", "1"]  # Incomplete EB segment
        ]
        
        parser = Parser270(segments)
        transaction = parser.parse()
        
        # Should not crash, but data will be minimal
        assert isinstance(transaction, Transaction270)
        # Parser should handle missing elements gracefully