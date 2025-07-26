"""
Tests for EDI 835 (Electronic Remittance Advice) Parser
"""

import pytest
import json
from packages.core.parser import EdiParser
from packages.core.emitter import EdiEmitter


@pytest.fixture
def edi_835_file():
    """Path to complete 835 EDI test file."""
    return "tests/fixtures/835.edi"


@pytest.fixture
def edi_835_json_file():
    """Path to expected JSON output for complete 835 EDI test."""
    return "tests/fixtures/835.json"


@pytest.fixture
def edi_835_minimal_file():
    """Path to minimal 835 EDI test file."""
    return "tests/fixtures/835-minimal.edi"


@pytest.fixture
def edi_835_minimal_json_file():
    """Path to expected JSON output for minimal 835 EDI test."""
    return "tests/fixtures/835-minimal.json"


@pytest.fixture
def edi_835_multiple_claims_file():
    """Path to 835 EDI test file with multiple claims."""
    return "tests/fixtures/835-multiple-claims.edi"


@pytest.fixture
def edi_835_multiple_claims_json_file():
    """Path to expected JSON output for multiple claims 835 EDI test."""
    return "tests/fixtures/835-multiple-claims.json"


@pytest.fixture
def edi_835_no_payer_payee_file():
    """Path to 835 EDI test file without payer/payee information."""
    return "tests/fixtures/835-no-payer-payee.edi"


@pytest.fixture
def edi_835_no_payer_payee_json_file():
    """Path to expected JSON output for no payer/payee 835 EDI test."""
    return "tests/fixtures/835-no-payer-payee.json"


@pytest.fixture
def sample_empty_edi():
    """Empty EDI content for testing empty string handling."""
    return ""


@pytest.fixture
def sample_malformed_edi():
    """Malformed EDI content for testing error handling."""
    return "ISA*00*          *00*          *ZZ*TEST*ZZ*TEST*230101*0000*U*00501*1*0*P*:~INVALID_SEGMENT~"


@pytest.fixture
def sample_numeric_test_edi():
    """EDI content for testing numeric formatting."""
    return """ISA*00*          *00*          *ZZ*TEST*ZZ*TEST*230101*0000*U*00501*1*0*P*:~
GS*HP*TEST*TEST*20230101*0000*1*X*005010X221A1~
ST*835*0001~
BPR*I*100.00*C*CHK*20230101~
CLP*TEST*1*50.00*25.50*24.50*12*CTRL~
SVC*HC:TEST*50.00*25.50*1~
SE*6*0001~
GE*1*1~
IEA*1*1~"""


@pytest.fixture
def sample_date_test_edi():
    """EDI content for testing date formatting."""
    return """ISA*00*          *00*          *ZZ*TEST*ZZ*TEST*230101*1230*U*00501*1*0*P*:~
GS*HP*TEST*TEST*20230101*1230*1*X*005010X221A1~
ST*835*0001~
BPR*I*100*C*CHK*20230101~
DTM*405*20230315~
SE*5*0001~
GE*1*1~
IEA*1*1~"""


@pytest.fixture
def sample_multiple_reference_edi():
    """EDI content for testing multiple reference numbers."""
    return """ISA*00*          *00*          *ZZ*TEST*ZZ*TEST*230101*0000*U*00501*1*0*P*:~
GS*HP*TEST*TEST*20230101*0000*1*X*005010X221A1~
ST*835*0001~
BPR*I*100*C*CHK*20230101~
TRN*1*TRACE001*REF001~
TRN*1*TRACE002*REF002~
SE*6*0001~
GE*1*1~
IEA*1*1~"""


@pytest.fixture
def schema_835_path():
    """Schema path for 835 transactions."""
    return "packages/core/schemas/x12/835.json"

class TestParser835:
    """Test cases for 835 parser functionality."""

    def test_parse_835_edi_file(self, edi_835_file, edi_835_json_file, schema_835_path):
        """Test parsing a complete 835 EDI file with all standard segments."""
        with open(edi_835_file, 'r') as f:
            edi_content = f.read()
        parser = EdiParser(edi_string=edi_content, schema_path=schema_835_path)
        edi_root = parser.parse()
        emitter = EdiEmitter(edi_root)
        json_output = emitter.to_json(pretty=True)

        with open(edi_835_json_file, 'r') as f:
            expected_json = f.read()

        assert json_output == expected_json

    def test_parse_835_minimal(self, edi_835_minimal_file, edi_835_minimal_json_file, schema_835_path):
        """Test parsing a minimal 835 EDI file with only required segments."""
        with open(edi_835_minimal_file, 'r') as f:
            edi_content = f.read()
        parser = EdiParser(edi_string=edi_content, schema_path=schema_835_path)
        edi_root = parser.parse()
        emitter = EdiEmitter(edi_root)
        json_output = emitter.to_json(pretty=True)

        with open(edi_835_minimal_json_file, 'r') as f:
            expected_json = f.read()

        assert json_output == expected_json

    def test_parse_835_multiple_claims(self, edi_835_multiple_claims_file, edi_835_multiple_claims_json_file, schema_835_path):
        """Test parsing an 835 EDI file with multiple claims and adjustments."""
        with open(edi_835_multiple_claims_file, 'r') as f:
            edi_content = f.read()
        parser = EdiParser(edi_string=edi_content, schema_path=schema_835_path)
        edi_root = parser.parse()
        emitter = EdiEmitter(edi_root)
        json_output = emitter.to_json(pretty=True)

        with open(edi_835_multiple_claims_json_file, 'r') as f:
            expected_json = f.read()

        assert json_output == expected_json

    def test_parse_835_no_payer_payee(self, edi_835_no_payer_payee_file, edi_835_no_payer_payee_json_file, schema_835_path):
        """Test parsing an 835 EDI file without payer/payee information."""
        with open(edi_835_no_payer_payee_file, 'r') as f:
            edi_content = f.read()
        parser = EdiParser(edi_string=edi_content, schema_path=schema_835_path)
        edi_root = parser.parse()
        emitter = EdiEmitter(edi_root)
        json_output = emitter.to_json(pretty=True)

        with open(edi_835_no_payer_payee_json_file, 'r') as f:
            expected_json = f.read()

        assert json_output == expected_json

    def test_parser_handles_empty_string(self, sample_empty_edi, schema_835_path):
        """Test that parser handles empty EDI content gracefully."""
        parser = EdiParser(edi_string=sample_empty_edi, schema_path=schema_835_path)
        edi_root = parser.parse()
        emitter = EdiEmitter(edi_root)
        json_output = emitter.to_json(pretty=True)
        
        expected = {
            "interchanges": []
        }
        
        assert json.loads(json_output) == expected

    def test_parser_handles_malformed_segments(self, sample_malformed_edi, schema_835_path):
        """Test parser behavior with malformed segments."""
        parser = EdiParser(edi_string=sample_malformed_edi, schema_path=schema_835_path)
        edi_root = parser.parse()
        
        # Should still parse the valid ISA segment
        assert len(edi_root.interchanges) == 1
        assert edi_root.interchanges[0].header["sender_id"] == "TEST"

    def test_numeric_formatting(self, sample_numeric_test_edi, schema_835_path):
        """Test that numeric values are properly formatted as integers when whole numbers."""
        parser = EdiParser(edi_string=sample_numeric_test_edi, schema_path=schema_835_path)
        edi_root = parser.parse()
        emitter = EdiEmitter(edi_root)
        json_output = emitter.to_json()
        
        parsed_data = json.loads(json_output)
        
        # Check that whole numbers are integers
        financial_info = parsed_data["interchanges"][0]["functional_groups"][0]["transactions"][0]["financial_information"]
        assert financial_info["total_paid"] == 100  # Should be int, not float
        
        # Check that non-whole numbers remain floats
        claim = parsed_data["interchanges"][0]["functional_groups"][0]["transactions"][0]["claims"][0]
        assert claim["total_paid"] == 25.5  # Should remain float
        assert claim["patient_responsibility"] == 24.5  # Should remain float

    def test_date_formatting(self, sample_date_test_edi, schema_835_path):
        """Test that dates are properly formatted from EDI format to ISO format."""
        parser = EdiParser(edi_string=sample_date_test_edi, schema_path=schema_835_path)
        edi_root = parser.parse()
        emitter = EdiEmitter(edi_root)
        json_output = emitter.to_json()
        
        parsed_data = json.loads(json_output)
        
        # Check ISA date formatting (YYMMDD -> YYYY-MM-DD)
        interchange = parsed_data["interchanges"][0]
        assert interchange["header"]["date"] == "2023-01-01"
        assert interchange["header"]["time"] == "12:30"
        
        # Check GS date formatting (CCYYMMDD -> YYYY-MM-DD)  
        functional_group = interchange["functional_groups"][0]
        assert functional_group["header"]["date"] == "2023-01-01"
        assert functional_group["header"]["time"] == "12:30"
        
        # Check DTM date formatting
        transaction = functional_group["transactions"][0]
        assert transaction["dates"][0]["date"] == "2023-03-15"

    def test_multiple_reference_numbers(self, sample_multiple_reference_edi, schema_835_path):
        """Test parsing multiple TRN segments."""
        parser = EdiParser(edi_string=sample_multiple_reference_edi, schema_path=schema_835_path)
        edi_root = parser.parse()
        emitter = EdiEmitter(edi_root)
        json_output = emitter.to_json()
        
        parsed_data = json.loads(json_output)
        transaction = parsed_data["interchanges"][0]["functional_groups"][0]["transactions"][0]
        
        # Should have two reference numbers
        assert len(transaction["reference_numbers"]) == 2
        assert transaction["reference_numbers"][0]["value"] == "TRACE001"
        assert transaction["reference_numbers"][1]["value"] == "TRACE002"
