"""
Global pytest configuration and fixtures.

This module provides shared configuration and fixtures that are available
to all test modules in the test suite.
"""

import pytest
import sys
import os
from pathlib import Path
from decimal import Decimal
from typing import Dict, Any, Generator

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Import existing shared fixtures
from tests.shared.fixtures import schema_paths, test_control_numbers, test_identifiers
from tests.shared.test_data import TestData


@pytest.fixture(scope="session")
def project_root_path():
    """Provide the project root path."""
    return project_root


@pytest.fixture(scope="session")
def test_data_dir():
    """Provide the test data directory path."""
    return Path(__file__).parent / "data"


@pytest.fixture(scope="session")
def test_data():
    """Session-scoped fixture providing access to shared test data."""
    return TestData


@pytest.fixture(scope="function")
def sample_edi_segments():
    """Provide sample EDI segments for basic testing."""
    return [
        ["ISA", "00", "          ", "00", "          ", "ZZ", "SENDER         ", "ZZ", "RECEIVER       ", "241226", "1430", "^", "00501", "000012345", "0", "P", ":"],
        ["GS", "HP", "SENDER", "RECEIVER", "20241226", "1430", "000006789", "X", "005010X221A1"],
        ["ST", "835", "0001"],
        ["BPR", "I", "1000.00", "C", "ACH", "CCP", "01", "123456789", "DA", "987654321", "9876543210", "20241226"],
        ["TRN", "1", "12345", "1234567890"],
        ["N1", "PR", "INSURANCE COMPANY"],
        ["N1", "PE", "PROVIDER NAME", "XX", "1234567890"],
        ["CLP", "CLAIM001", "1", "1200.00", "1000.00", "200.00", "", "", "", ""],
        ["SE", "8", "0001"],
        ["GE", "1", "000006789"],
        ["IEA", "1", "000012345"]
    ]


@pytest.fixture(scope="function")
def minimal_835_segments():
    """Provide minimal valid 835 segments."""
    return [
        ["ST", "835", "0001"],
        ["BPR", "I", "1000.00", "C", "ACH"],
        ["TRN", "1", "12345"],
        ["N1", "PR", "PAYER"],
        ["N1", "PE", "PAYEE"],
        ["CLP", "CLAIM001", "1", "1000.00", "1000.00", "0.00"],
        ["SE", "6", "0001"]
    ]


@pytest.fixture(scope="function")
def parser_835():
    """Provide an 835 parser instance."""
    from packages.core.parser_835 import Parser835
    return lambda segments=None: Parser835()


@pytest.fixture(scope="function")
def base_parser():
    """Provide a base parser instance."""
    from packages.core.base.parser import BaseParser
    return BaseParser()


@pytest.fixture(scope="function")
def edi_fixtures():
    """Provide EDI fixtures instance."""
    from tests.core.fixtures.legacy_fixtures import EDIFixtures
    return EDIFixtures


@pytest.fixture(scope="function")
def test_amounts():
    """Provide common test amounts as Decimal objects."""
    return {
        "zero": Decimal("0.00"),
        "small": Decimal("50.00"),
        "medium": Decimal("500.00"),
        "large": Decimal("5000.00"),
        "precise": Decimal("123.45"),
        "whole": Decimal("1000.00")
    }


@pytest.fixture(scope="function")
def test_dates():
    """Provide common test dates in various formats."""
    return {
        "ccyymmdd": "20241226",
        "yymmdd": "241226",
        "mmddyy": "122624",
        "mmddccyy": "12262024",
        "iso": "2024-12-26",
        "invalid": "invalid_date"
    }


@pytest.fixture(scope="function")
def test_npis():
    """Provide test NPI numbers for validation testing."""
    return {
        "valid_format": "1234567890",
        "valid_format_2": "9876543210",
        "too_short": "123456789",
        "too_long": "12345678901",
        "non_numeric": "abcdefghij",
        "with_dashes": "123-456-7890",
        "empty": "",
        "none": None
    }


@pytest.fixture(scope="function")
def performance_config():
    """Provide performance test configuration."""
    return {
        "simple_parse_threshold": 0.1,  # seconds
        "complex_parse_threshold": 0.5,  # seconds
        "validation_throughput_min": 1000,  # operations per second
        "memory_growth_threshold": 0.1,  # 10% max growth
        "concurrent_workers": 4
    }


@pytest.fixture(scope="session")
def temp_test_dir(tmp_path_factory):
    """Provide a temporary directory for test files."""
    return tmp_path_factory.mktemp("edi_tests")


@pytest.fixture(scope="function")
def mock_file_content():
    """Provide mock file content for testing file operations."""
    return {
        "valid_835": """ISA*00*          *00*          *ZZ*SENDER         *ZZ*RECEIVER       *241226*1430*^*00501*000012345*0*P*:~
GS*HP*SENDER*RECEIVER*20241226*1430*000006789*X*005010X221A1~
ST*835*0001~
BPR*I*1000.00*C*ACH*CCP*01*123456789*DA*987654321*9876543210*20241226~
TRN*1*12345*1234567890~
N1*PR*INSURANCE COMPANY~
N1*PE*PROVIDER NAME*XX*1234567890~
CLP*CLAIM001*1*1200.00*1000.00*200.00~
SE*8*0001~
GE*1*000006789~
IEA*1*000012345~""",
        "invalid_format": "This is not valid EDI content",
        "empty": "",
        "malformed_segments": "ST*835*0001~INVALID~SE*2*0001~"
    }


# Configure pytest markers
def pytest_configure(config):
    """Configure custom pytest markers."""
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests"
    )
    config.addinivalue_line(
        "markers", "performance: marks tests as performance tests"
    )
    config.addinivalue_line(
        "markers", "benchmark: marks tests as benchmark tests"
    )
    config.addinivalue_line(
        "markers", "unit: marks tests as unit tests"
    )


# Session-scoped fixtures for expensive operations
@pytest.fixture(scope="session")
def compiled_test_data():
    """Provide compiled test data that's expensive to generate."""
    from tests.core.fixtures.scenarios.payment_scenarios import PaymentScenarios
    from tests.core.fixtures.scenarios.claim_scenarios import ClaimScenarios
    
    # Generate comprehensive test scenarios once per session
    payment_scenarios = PaymentScenarios()
    claim_scenarios = ClaimScenarios()
    
    return {
        "payment_scenarios": payment_scenarios.get_all_scenarios(),
        "claim_scenarios": claim_scenarios.get_all_scenarios()
    }


@pytest.fixture(scope="function")
def error_expectations():
    """Provide expected error types and messages for validation testing."""
    return {
        "invalid_npi": {
            "error_types": [ValueError, TypeError],
            "keywords": ["npi", "invalid", "format"]
        },
        "invalid_amount": {
            "error_types": [ValueError, TypeError],
            "keywords": ["amount", "invalid", "format", "decimal"]
        },
        "invalid_date": {
            "error_types": [ValueError, TypeError],
            "keywords": ["date", "invalid", "format"]
        },
        "malformed_edi": {
            "error_types": [ValueError, SyntaxError, AttributeError],
            "keywords": ["edi", "malformed", "segment", "parse"]
        }
    }


# Custom assertion helpers available to all tests
@pytest.fixture(scope="session")
def custom_assertions():
    """Provide custom assertion helpers."""
    from tests.shared.assertions import (
        assert_balances,
        assert_transaction_structure,
        assert_financial_integrity
    )
    
    return {
        "assert_balances": assert_balances,
        "assert_transaction_structure": assert_transaction_structure,
        "assert_financial_integrity": assert_financial_integrity
    }


# Hook for test collection modification
def pytest_collection_modifyitems(config, items):
    """Modify test collection to add markers based on test paths."""
    for item in items:
        # Add markers based on test file location
        if "integration" in str(item.fspath):
            item.add_marker(pytest.mark.integration)
        elif "performance" in str(item.fspath):
            item.add_marker(pytest.mark.performance)
        elif "unit" in str(item.fspath):
            item.add_marker(pytest.mark.unit)
        
        # Add slow marker for tests with certain patterns
        if "benchmark" in item.name or "performance" in item.name:
            item.add_marker(pytest.mark.slow)


# Import shared fixtures to make them available globally
__all__ = [
    'schema_paths',
    'test_control_numbers', 
    'test_identifiers',
    'test_data',
    'project_root_path',
    'test_data_dir',
    'sample_edi_segments',
    'minimal_835_segments',
    'parser_835',
    'base_parser',
    'edi_fixtures',
    'test_amounts',
    'test_dates',
    'test_npis',
    'performance_config',
    'temp_test_dir',
    'mock_file_content',
    'compiled_test_data',
    'error_expectations',
    'custom_assertions'
]