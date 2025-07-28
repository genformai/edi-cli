"""
EDI 270/271 (Eligibility Inquiry/Response) Transaction Parser Plugin - Refactored

This plugin uses the new factory-based architecture to reduce direct
dependencies on core implementation classes.
"""

from typing import Tuple
from ..base_plugin import FactoryBasedPlugin
from ..factory import TransactionParserFactory, ASTNodeFactory


class Plugin270271(FactoryBasedPlugin):
    """Plugin for parsing EDI 270/271 Eligibility Inquiry/Response transactions."""
    
    def __init__(self):
        super().__init__(
            transaction_codes=["270", "271"],
            plugin_name="EDI-270-271-Parser",
            plugin_version="1.0.0",
            schema_path="schemas/270_271.json"
        )
    
    def setup_factories(self) -> Tuple[TransactionParserFactory, ASTNodeFactory]:
        """Setup factories for 270/271 transaction parsing."""
        from ..factory import GenericTransactionParserFactory, GenericASTNodeFactory
        from ...transactions.t270.parser import Parser270
        from ...transactions.t270.ast import Transaction270
        
        parser_factory = GenericTransactionParserFactory(Parser270, ["270", "271"])
        ast_factory = GenericASTNodeFactory(Transaction270)
        
        return parser_factory, ast_factory