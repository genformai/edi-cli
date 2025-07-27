"""
EDI 276/277 (Claim Status Inquiry/Response) Transaction Parser Plugin - Refactored

This plugin uses the new factory-based architecture to reduce direct
dependencies on core implementation classes.
"""

from typing import Tuple
from ..base_plugin import FactoryBasedPlugin
from ..factory import TransactionParserFactory, ASTNodeFactory


class Plugin276277(FactoryBasedPlugin):
    """Plugin for parsing EDI 276/277 Claim Status Inquiry/Response transactions."""
    
    def __init__(self):
        super().__init__(
            transaction_codes=["276", "277"],
            plugin_name="EDI-276-277-Parser",
            plugin_version="1.0.0",
            schema_path="schemas/276_277.json"
        )
    
    def setup_factories(self) -> Tuple[TransactionParserFactory, ASTNodeFactory]:
        """Setup factories for 276/277 transaction parsing."""
        from ..factory import GenericTransactionParserFactory, GenericASTNodeFactory
        from ...base.parser import BaseParser
        
        # Create a stub parser for 276/277 until full implementation is ready
        class StubParser276277(BaseParser):
            def get_transaction_codes(self):
                return ["276", "277"]
            
            def parse(self):
                from ...base.edi_ast import EdiRoot
                return EdiRoot()  # Return empty structure for now
        
        # Create a stub AST class for 276/277
        class Transaction276277:
            def __init__(self, header=None):
                self.header = header or {}
            
            def to_dict(self):
                return {"header": self.header}
        
        parser_factory = GenericTransactionParserFactory(StubParser276277, ["276", "277"])
        ast_factory = GenericASTNodeFactory(Transaction276277)
        
        return parser_factory, ast_factory