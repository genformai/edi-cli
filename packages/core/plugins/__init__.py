"""
EDI Transaction Parser Plugins.

This package provides the plugin system for EDI transaction parsing,
including the plugin API and concrete plugin implementations.
"""

from .api import TransactionParserPlugin

__all__ = [
    'TransactionParserPlugin'
]