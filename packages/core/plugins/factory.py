"""
Plugin Factory Architecture

This module provides factory interfaces for creating transaction parsers
and AST objects, reducing direct dependencies between plugins and core implementations.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, Type, Union
from ..base.edi_ast import EdiRoot, Transaction
from ..base.parser import BaseParser


class TransactionParserFactory(ABC):
    """Abstract factory for creating transaction parsers."""
    
    @abstractmethod
    def create_parser(self, segments: List[List[str]]) -> BaseParser:
        """Create a parser instance for the given segments."""
        pass
    
    @abstractmethod
    def get_supported_codes(self) -> List[str]:
        """Return list of transaction codes this factory supports."""
        pass
    
    @abstractmethod
    def create_edi_root(self) -> EdiRoot:
        """Create an empty EDI root structure."""
        pass
    
    @abstractmethod
    def create_transaction(self, transaction_code: str, control_number: str, transaction_data: Any = None) -> Transaction:
        """Create a generic transaction with the specified data."""
        pass


class ASTNodeFactory(ABC):
    """Abstract factory for creating transaction-specific AST nodes."""
    
    @abstractmethod
    def get_transaction_class(self) -> Type:
        """Return the transaction-specific AST class."""
        pass
    
    @abstractmethod
    def create_transaction_ast(self, header: Dict[str, str]) -> Any:
        """Create a transaction-specific AST object."""
        pass
    
    def validate_transaction_data(self, data: Any) -> bool:
        """Optional: Validate transaction data structure."""
        return True


class PluginContext:
    """Context object providing utilities and factories to plugins."""
    
    def __init__(self):
        self._parser_factories: Dict[str, TransactionParserFactory] = {}
        self._ast_factories: Dict[str, ASTNodeFactory] = {}
    
    def register_parser_factory(self, transaction_codes: List[str], factory: TransactionParserFactory):
        """Register a parser factory for specific transaction codes."""
        for code in transaction_codes:
            self._parser_factories[code] = factory
    
    def register_ast_factory(self, transaction_codes: List[str], factory: ASTNodeFactory):
        """Register an AST factory for specific transaction codes."""
        for code in transaction_codes:
            self._ast_factories[code] = factory
    
    def get_parser_factory(self, transaction_code: str) -> Optional[TransactionParserFactory]:
        """Get parser factory for a transaction code."""
        return self._parser_factories.get(transaction_code)
    
    def get_ast_factory(self, transaction_code: str) -> Optional[ASTNodeFactory]:
        """Get AST factory for a transaction code."""
        return self._ast_factories.get(transaction_code)


class GenericTransactionParserFactory(TransactionParserFactory):
    """Generic factory implementation using parser classes."""
    
    def __init__(self, parser_class: Type[BaseParser], transaction_codes: List[str]):
        self.parser_class = parser_class
        self.transaction_codes = transaction_codes
    
    def create_parser(self, segments: List[List[str]]) -> BaseParser:
        """Create parser instance."""
        return self.parser_class(segments)
    
    def get_supported_codes(self) -> List[str]:
        """Return supported transaction codes."""
        return self.transaction_codes.copy()
    
    def create_edi_root(self) -> EdiRoot:
        """Create EDI root structure."""
        from ..base.edi_ast import EdiRoot
        return EdiRoot()
    
    def create_transaction(self, transaction_code: str, control_number: str, transaction_data: Any = None) -> Transaction:
        """Create generic transaction."""
        from ..base.edi_ast import Transaction
        return Transaction(transaction_code, control_number, transaction_data)


class GenericASTNodeFactory(ASTNodeFactory):
    """Generic AST factory implementation."""
    
    def __init__(self, transaction_class: Type, create_func: callable = None):
        self.transaction_class = transaction_class
        self.create_func = create_func or (lambda header: transaction_class(header=header))
    
    def get_transaction_class(self) -> Type:
        """Return transaction class."""
        return self.transaction_class
    
    def create_transaction_ast(self, header: Dict[str, str]) -> Any:
        """Create transaction AST."""
        return self.create_func(header)


# Global plugin context
plugin_context = PluginContext()