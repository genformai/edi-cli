"""
EDI 837P (Professional Claims) Transaction Parser Plugin - Refactored

This plugin uses the new factory-based architecture to reduce direct
dependencies on core implementation classes.
"""

from typing import Tuple
from ..base_plugin import FactoryBasedPlugin
from ..factory import TransactionParserFactory, ASTNodeFactory


class Plugin837P(FactoryBasedPlugin):
    """Plugin for parsing EDI 837P Professional Claims transactions."""
    
    def __init__(self):
        super().__init__(
            transaction_codes=["837"],
            plugin_name="EDI-837P-Parser",
            plugin_version="1.0.0",
            schema_path="schemas/837p.json"
        )
    
    def setup_factories(self) -> Tuple[TransactionParserFactory, ASTNodeFactory]:
        """Setup factories for 837P transaction parsing."""
        from ..factory import GenericTransactionParserFactory, GenericASTNodeFactory
        from ...transactions.t837p.ast import Transaction837P
        from ...base.parser import BaseParser
        
        # Create a stub parser for 837P until full implementation is ready
        class StubParser837P(BaseParser):
            def get_transaction_codes(self):
                return ["837"]
            
            def parse(self):
                from ...base.edi_ast import EdiRoot
                return EdiRoot()  # Return empty structure for now
        
        parser_factory = GenericTransactionParserFactory(StubParser837P, ["837"])
        ast_factory = GenericASTNodeFactory(Transaction837P)
        
        return parser_factory, ast_factory