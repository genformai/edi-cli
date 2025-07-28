"""
Sample EDI 850 (Purchase Order) Plugin

This demonstrates how to create a custom transaction parser plugin
for edi-cli to support new transaction types.
"""

import sys
import os
from typing import List, Dict, Any, Type
from dataclasses import dataclass

# Add packages to path for plugin development
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'packages'))

from core.plugins.base_plugin import SimpleParserPlugin
from core.base.parser import BaseParser
from core.base.edi_ast import EdiRoot, Interchange, FunctionalGroup, Transaction, Node


@dataclass
class PurchaseOrderHeader(Node):
    """Purchase order header information."""
    po_number: str = ""
    po_date: str = ""
    buyer_party: str = ""
    seller_party: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "po_number": self.po_number,
            "po_date": self.po_date,
            "buyer_party": self.buyer_party,
            "seller_party": self.seller_party
        }


@dataclass
class LineItem(Node):
    """Purchase order line item."""
    line_number: str = ""
    product_id: str = ""
    quantity: float = 0.0
    unit_price: float = 0.0
    description: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "line_number": self.line_number,
            "product_id": self.product_id,
            "quantity": self.quantity,
            "unit_price": self.unit_price,
            "description": self.description,
            "total": self.quantity * self.unit_price
        }


@dataclass
class Transaction850(Node):
    """EDI 850 Purchase Order transaction."""
    header: Dict[str, str]
    po_header: PurchaseOrderHeader = None
    line_items: List[LineItem] = None
    
    def __post_init__(self):
        if self.po_header is None:
            self.po_header = PurchaseOrderHeader()
        if self.line_items is None:
            self.line_items = []
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "header": self.header,
            "purchase_order": self.po_header.to_dict(),
            "line_items": [item.to_dict() for item in self.line_items],
            "summary": {
                "total_lines": len(self.line_items),
                "total_amount": sum(item.quantity * item.unit_price for item in self.line_items)
            }
        }


class Parser850(BaseParser):
    """Parser for EDI 850 Purchase Order transactions."""
    
    def get_transaction_codes(self) -> List[str]:
        return ["850"]
    
    def parse(self) -> EdiRoot:
        """Parse EDI 850 transaction."""
        # Parse transaction data
        transaction_data = self._parse_850_transaction()
        
        # Wrap in EdiRoot structure for CLI compatibility
        return self._wrap_in_edi_structure(transaction_data)
    
    def _parse_850_transaction(self) -> Transaction850:
        """Parse 850-specific transaction data."""
        # Parse header
        header = {}
        st_segment = self._find_segment("ST")
        if st_segment:
            header["transaction_set_identifier"] = st_segment[1] if len(st_segment) > 1 else ""
            header["transaction_set_control_number"] = st_segment[2] if len(st_segment) > 2 else ""
        
        # Parse BEG segment (Beginning Segment for Purchase Order)
        beg_segment = self._find_segment("BEG")
        if beg_segment:
            header["transaction_set_purpose_code"] = beg_segment[1] if len(beg_segment) > 1 else ""
            header["purchase_order_type_code"] = beg_segment[2] if len(beg_segment) > 2 else ""
            header["purchase_order_number"] = beg_segment[3] if len(beg_segment) > 3 else ""
            header["date"] = beg_segment[5] if len(beg_segment) > 5 else ""
        
        # Create transaction object
        transaction = Transaction850(header=header)
        
        # Parse purchase order header
        self._parse_po_header(transaction)
        
        # Parse line items
        self._parse_line_items(transaction)
        
        return transaction
    
    def _parse_po_header(self, transaction: Transaction850):
        """Parse purchase order header information."""
        po_header = PurchaseOrderHeader()
        
        # Get PO number and date from BEG segment
        beg_segment = self._find_segment("BEG")
        if beg_segment:
            po_header.po_number = beg_segment[3] if len(beg_segment) > 3 else ""
            po_header.po_date = beg_segment[5] if len(beg_segment) > 5 else ""
        
        # Parse N1 segments for buyer/seller information
        n1_segments = self._find_all_segments("N1")
        for n1_segment in n1_segments:
            if len(n1_segment) > 2:
                entity_id = n1_segment[1]
                entity_name = n1_segment[2]
                
                if entity_id == "BY":  # Buying Party
                    po_header.buyer_party = entity_name
                elif entity_id == "SE":  # Selling Party
                    po_header.seller_party = entity_name
        
        transaction.po_header = po_header
    
    def _parse_line_items(self, transaction: Transaction850):
        """Parse purchase order line items."""
        po1_segments = self._find_all_segments("PO1")
        
        for po1_segment in po1_segments:
            if len(po1_segment) > 1:
                line_item = LineItem()
                
                # PO1 segment format: PO1*line_number*quantity*unit*unit_price*basis*product_id_qualifier*product_id
                line_item.line_number = po1_segment[1] if len(po1_segment) > 1 else ""
                
                if len(po1_segment) > 2 and po1_segment[2]:
                    try:
                        line_item.quantity = float(po1_segment[2])
                    except ValueError:
                        pass
                
                if len(po1_segment) > 4 and po1_segment[4]:
                    try:
                        line_item.unit_price = float(po1_segment[4])
                    except ValueError:
                        pass
                
                line_item.product_id = po1_segment[7] if len(po1_segment) > 7 else ""
                
                # Look for PID segment (Product/Item Description) after this PO1
                pid_segment = self._find_next_segment_after("PID", po1_segment)
                if pid_segment and len(pid_segment) > 5:
                    line_item.description = pid_segment[5]
                
                transaction.line_items.append(line_item)
    
    def _find_next_segment_after(self, segment_id: str, after_segment: List[str]) -> List[str]:
        """Find the next segment with given ID after the specified segment."""
        try:
            start_index = self.segments.index(after_segment) + 1
            for i in range(start_index, len(self.segments)):
                segment = self.segments[i]
                if segment and segment[0] == segment_id:
                    return segment
                # Stop at next PO1 segment to avoid crossing line items
                elif segment and segment[0] == "PO1":
                    break
        except (ValueError, IndexError):
            pass
        return None
    
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


class Sample850Plugin(SimpleParserPlugin):
    """Plugin wrapper for EDI 850 Purchase Order parser."""
    
    def __init__(self):
        super().__init__(
            parser_class=Parser850,
            transaction_class=Transaction850,
            transaction_codes=["850"],
            plugin_name="Sample-850-PurchaseOrder",
            plugin_version="1.0.0"
        )


# Export plugin class for automatic discovery
__all__ = ['Sample850Plugin']