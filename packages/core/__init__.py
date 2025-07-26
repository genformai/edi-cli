"""
EDI Core Processing Library.

This package provides a complete EDI parsing, validation, and processing framework
with support for multiple EDI transaction types organized in a modular structure.
"""

# Core components
from .parser import EdiParser
from .emitter import EdiEmitter

# Base classes and utilities
from .base import BaseParser, EdiRoot, Interchange, FunctionalGroup, Transaction
from .base import ValidationRule, ValidationError, ValidationSeverity, ValidationCategory

# Transaction-specific modules
from . import transactions

# Plugin system
from . import plugins

# Utilities
from . import utils

__all__ = [
    # Main components
    "EdiParser", 
    "EdiEmitter",
    
    # Base classes
    "BaseParser",
    "EdiRoot",
    "Interchange", 
    "FunctionalGroup",
    "Transaction",
    
    # Validation
    "ValidationRule",
    "ValidationError", 
    "ValidationSeverity",
    "ValidationCategory",
    
    # Modules
    "transactions",
    "plugins", 
    "utils"
]
