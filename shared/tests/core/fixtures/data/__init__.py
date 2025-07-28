"""
YAML-based data sources for EDI testing.

This module provides realistic test data loaded from YAML files including
payers, providers, procedure codes, and diagnosis codes.
"""

from .data_loader import DataLoader, data_loader

__all__ = [
    'DataLoader',
    'data_loader'
]