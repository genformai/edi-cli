"""
Standardized interfaces for EDI processing components.

This package provides consistent interfaces and protocols for
parsers, validators, and other EDI processing components.
"""

from .parser_interface import (
    EDIParser,
    StandardizedParser,
    ParseResult,
    ParseOutput,
    ParserRegistry,
    parser_registry
)

__all__ = [
    'EDIParser',
    'StandardizedParser', 
    'ParseResult',
    'ParseOutput',
    'ParserRegistry',
    'parser_registry'
]