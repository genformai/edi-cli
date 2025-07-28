"""
EDI 835 (Electronic Remittance Advice) Transaction Parser Plugin - Refactored

This plugin uses the new factory-based architecture to reduce direct
dependencies on core implementation classes.
"""

from typing import Tuple
from ..base_plugin import FactoryBasedPlugin
from ..factory import TransactionParserFactory, ASTNodeFactory


class Plugin835(FactoryBasedPlugin):
    """Plugin for parsing EDI 835 Electronic Remittance Advice transactions."""
    
    def __init__(self):
        super().__init__(
            transaction_codes=["835"],
            plugin_name="EDI-835-Parser",
            plugin_version="1.0.0",
            schema_path="schemas/835.json"
        )
    
    def setup_factories(self) -> Tuple[TransactionParserFactory, ASTNodeFactory]:
        """Setup factories for 835 transaction parsing."""
        from ..factory import GenericTransactionParserFactory, GenericASTNodeFactory
        from ...transactions.t835.parser import Parser835
        from ...transactions.t835.ast import Transaction835
        
        parser_factory = GenericTransactionParserFactory(Parser835, ["835"])
        ast_factory = GenericASTNodeFactory(Transaction835)
        
        return parser_factory, ast_factory