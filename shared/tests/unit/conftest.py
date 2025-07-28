"""
Unit test specific fixtures and configuration.

This file provides fixtures and configuration specific to unit tests.
"""

import pytest
from packages.core.parser import EdiParser


@pytest.fixture
def edi_parser():
    """Fixture providing an EDI parser instance."""
    def _create_parser(edi_content: str, schema_path: str):
        return EdiParser(edi_content, schema_path)
    return _create_parser


@pytest.fixture
def parse_edi():
    """
    Fixture providing a simple EDI parsing function.
    
    Returns:
        Function that takes edi_content and schema_path and returns parsed result
    """
    def _parse(edi_content: str, schema_path: str):
        parser = EdiParser(edi_content, schema_path)
        return parser.parse()
    return _parse