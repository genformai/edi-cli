"""
Shared test fixtures for EDI testing.

This module provides base fixture classes and common test data
that are used across multiple test modules.
"""

import pytest
from typing import Dict, Any, List
from pathlib import Path


class SharedTestFixtures:
    """Base class for shared test fixtures and utilities."""
    
    @staticmethod
    def get_schema_path(transaction_code: str) -> str:
        """Get the schema path for a transaction type."""
        schema_map = {
            "270": "packages/core/schemas/x12/270.json",
            "271": "packages/core/schemas/x12/271.json", 
            "276": "packages/core/schemas/x12/276.json",
            "277": "packages/core/schemas/x12/277.json",
            "835": "packages/core/schemas/x12/835.json",
            "837": "packages/core/schemas/x12/837.json"
        }
        
        if transaction_code not in schema_map:
            raise ValueError(f"Unknown transaction code: {transaction_code}")
            
        return schema_map[transaction_code]
    
    @staticmethod
    def get_sample_file_path(transaction_code: str, sample_name: str) -> str:
        """Get the path to a sample EDI file."""
        base_path = Path("tests/fixtures/samples")
        file_path = base_path / f"{transaction_code}_samples" / f"{sample_name}.edi"
        return str(file_path)
    
    @staticmethod
    def get_test_control_numbers() -> Dict[str, str]:
        """Get consistent test control numbers."""
        return {
            "interchange_control": "000000001",
            "group_control": "000000001", 
            "transaction_control": "0001"
        }
    
    @staticmethod
    def get_test_identifiers() -> Dict[str, str]:
        """Get consistent test identifiers."""
        return {
            "sender_id": "TESTSUBMITTER",
            "receiver_id": "TESTPAYER",
            "application_sender": "TESTAPP",
            "application_receiver": "TESTAPP"
        }


@pytest.fixture
def shared_fixtures():
    """Pytest fixture providing access to shared test fixtures."""
    return SharedTestFixtures()


@pytest.fixture
def test_control_numbers():
    """Pytest fixture providing test control numbers."""
    return SharedTestFixtures.get_test_control_numbers()


@pytest.fixture
def test_identifiers():
    """Pytest fixture providing test identifiers."""
    return SharedTestFixtures.get_test_identifiers()


@pytest.fixture(scope="session")
def schema_paths():
    """Session-scoped fixture providing all schema paths."""
    return {
        "270": SharedTestFixtures.get_schema_path("270"),
        "271": SharedTestFixtures.get_schema_path("271"),
        "276": SharedTestFixtures.get_schema_path("276"), 
        "277": SharedTestFixtures.get_schema_path("277"),
        "835": SharedTestFixtures.get_schema_path("835"),
        "837": SharedTestFixtures.get_schema_path("837")
    }