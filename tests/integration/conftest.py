"""
Integration test specific fixtures and configuration.

This file provides fixtures and configuration specific to integration tests.
"""

import pytest
from packages.core.parser import EdiParser
from tests.shared.test_data import TestData


@pytest.fixture
def end_to_end_parser():
    """Fixture for end-to-end parsing tests."""
    def _parse_complete_transaction(edi_content: str, schema_path: str):
        parser = EdiParser(edi_content, schema_path)
        return parser.parse()
    return _parse_complete_transaction


@pytest.fixture
def sample_transaction_files(test_data):
    """Fixture providing paths to sample transaction files."""
    return {
        "835_minimal": "tests/fixtures/samples/835_samples/835-minimal.edi",
        "835_multiple": "tests/fixtures/samples/835_samples/835-multiple-claims.edi",
        "835_full": "tests/fixtures/samples/835_samples/835.edi"
    }