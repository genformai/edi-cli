"""
Custom EDI Transaction Parser Plugin: TestPlugin

This is a template plugin for parsing EDI transactions 999.
Customize the parsing logic in the parse_transaction method.
"""

from typing import List, Dict, Any, Type
import sys
import os

# Add packages to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from core.plugins.base_plugin import SimpleParserPlugin
from core.base.parser import BaseParser
from core.base.edi_ast import EdiRoot, Interchange, FunctionalGroup, Transaction, Node
from dataclasses import dataclass


@dataclass
class TestPluginTransaction(Node):
    """AST node for TestPlugin transaction data."""
    header: Dict[str, str]
    # Add your custom fields here
    custom_field: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "header": self.header,
            "custom_field": self.custom_field
        }


class TestPluginParser(BaseParser):
    """Parser for TestPlugin transactions."""
    
    def get_transaction_codes(self) -> List[str]:
        return ['999']
    
    def parse(self) -> EdiRoot:
        """Parse the transaction and return EdiRoot structure."""
        # Extract transaction type from ST segment
        st_segment = self._find_segment("ST")
        transaction_code = st_segment[1] if st_segment and len(st_segment) > 1 else ""
        
        # Parse your transaction data
        transaction_data = self._parse_transaction(transaction_code)
        
        # Wrap in EdiRoot structure
        return self._wrap_in_edi_structure(transaction_data)
    
    def _parse_transaction(self, transaction_code: str) -> TestPluginTransaction:
        """Parse transaction-specific data."""
        # Parse header
        header = {}
        st_segment = self._find_segment("ST")
        if st_segment:
            header["transaction_set_identifier"] = st_segment[1] if len(st_segment) > 1 else ""
            header["transaction_set_control_number"] = st_segment[2] if len(st_segment) > 2 else ""
        
        # Create transaction object
        transaction = TestPluginTransaction(header=header)
        
        # TODO: Add your custom parsing logic here
        # Example: Parse specific segments for your transaction type
        # custom_segments = self._find_all_segments("YOUR_SEGMENT_ID")
        # transaction.custom_field = self._process_custom_segments(custom_segments)
        
        return transaction
    
    def _wrap_in_edi_structure(self, transaction_data) -> EdiRoot:
        """Wrap parsed data in EDI envelope structure."""
        root = EdiRoot()
        
        # Create basic envelope structure
        isa_segment = self._find_segment("ISA")
        gs_segment = self._find_segment("GS") 
        st_segment = self._find_segment("ST")
        
        # Create interchange
        if isa_segment:
            interchange = Interchange(
                sender_id=isa_segment[6] if len(isa_segment) > 6 else "",
                receiver_id=isa_segment[8] if len(isa_segment) > 8 else "",
                date=isa_segment[9] if len(isa_segment) > 9 else "",
                time=isa_segment[10] if len(isa_segment) > 10 else "",
                control_number=isa_segment[13] if len(isa_segment) > 13 else ""
            )
        else:
            interchange = Interchange("", "", "", "", "")
        
        # Create functional group
        if gs_segment:
            functional_group = FunctionalGroup(
                functional_group_code=gs_segment[1] if len(gs_segment) > 1 else "",
                sender_id=gs_segment[2] if len(gs_segment) > 2 else "",
                receiver_id=gs_segment[3] if len(gs_segment) > 3 else "",
                date=gs_segment[4] if len(gs_segment) > 4 else "",
                time=gs_segment[5] if len(gs_segment) > 5 else "",
                control_number=gs_segment[6] if len(gs_segment) > 6 else ""
            )
        else:
            functional_group = FunctionalGroup("", "", "", "", "", "")
        
        # Create transaction wrapper
        if st_segment:
            transaction = Transaction(
                transaction_set_code=st_segment[1] if len(st_segment) > 1 else "",
                control_number=st_segment[2] if len(st_segment) > 2 else "",
                transaction_data=transaction_data
            )
        else:
            transaction = Transaction("", "", transaction_data)
        
        # Assemble structure
        functional_group.transactions.append(transaction)
        interchange.functional_groups.append(functional_group)
        root.interchanges.append(interchange)
        
        return root


class TestPluginPlugin(SimpleParserPlugin):
    """Plugin wrapper for TestPlugin parser."""
    
    def __init__(self):
        super().__init__(
            parser_class=TestPluginParser,
            transaction_class=TestPluginTransaction,
            transaction_codes=['999'],
            plugin_name="TestPlugin",
            plugin_version="1.0.0"
        )


# Export the plugin class for automatic discovery
__all__ = ['TestPluginPlugin']
