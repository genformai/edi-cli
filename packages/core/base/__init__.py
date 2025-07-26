"""
Base classes and utilities for EDI processing.

This module provides the core abstractions and base classes that all
EDI transaction parsers and validators build upon.
"""

from .parser import BaseParser
from .edi_ast import EdiRoot, Interchange, FunctionalGroup, Transaction
from .validation import ValidationRule, ValidationError, ValidationSeverity, ValidationCategory, BusinessRule

__all__ = [
    'BaseParser',
    'EdiRoot',
    'Interchange', 
    'FunctionalGroup',
    'Transaction',
    'ValidationRule',
    'ValidationError',
    'ValidationSeverity',
    'ValidationCategory',
    'BusinessRule'
]