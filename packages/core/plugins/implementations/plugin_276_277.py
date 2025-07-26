"""
EDI 276/277 (Claim Status Inquiry/Response) Transaction Parser Plugin
"""

from typing import List, Type, Optional
from ..api import TransactionParserPlugin
from ...base.edi_ast import EdiRoot
from ...transactions.t276.ast import Transaction276, Transaction277
from ..parser_276 import Parser276


class Plugin276277(TransactionParserPlugin):
    """Plugin for parsing EDI 276/277 Claim Status Inquiry/Response transactions."""
    
    @property
    def transaction_codes(self) -> List[str]:
        return ["276", "277"]
    
    @property
    def plugin_name(self) -> str:
        return "EDI-276-277-Parser"
    
    @property
    def plugin_version(self) -> str:
        return "1.0.0"
    
    def get_transaction_class(self) -> Type:
        # Return base class since this handles both 276 and 277
        return Transaction276
    
    def get_schema_path(self) -> Optional[str]:
        return "schemas/276_277.json"
    
    def parse(self, segments: List[List[str]]) -> EdiRoot:
        """Parse 276/277 Claim Status transactions using existing parser."""
        from ...base.edi_ast import Interchange, FunctionalGroup, Transaction
        
        parser = Parser276(segments)
        transaction_obj = parser.parse()
        
        # Create EdiRoot structure
        root = EdiRoot()
        
        # Create basic interchange structure
        interchange = Interchange(
            sender_id=segments[0][6].strip() if len(segments) > 0 and len(segments[0]) > 6 else "",
            receiver_id=segments[0][8].strip() if len(segments) > 0 and len(segments[0]) > 8 else "",
            date=segments[0][9] if len(segments) > 0 and len(segments[0]) > 9 else "",
            time=segments[0][10] if len(segments) > 0 and len(segments[0]) > 10 else "",
            control_number=segments[0][13].strip() if len(segments) > 0 and len(segments[0]) > 13 else "",
        )
        root.interchanges.append(interchange)
        
        # Create functional group
        gs_segment = next((seg for seg in segments if seg[0] == "GS"), None)
        functional_group = FunctionalGroup(
            functional_group_code=gs_segment[1].strip() if gs_segment and len(gs_segment) > 1 else "",
            sender_id=gs_segment[2].strip() if gs_segment and len(gs_segment) > 2 else "",
            receiver_id=gs_segment[3].strip() if gs_segment and len(gs_segment) > 3 else "",
            date=gs_segment[4] if gs_segment and len(gs_segment) > 4 else "",
            time=gs_segment[5] if gs_segment and len(gs_segment) > 5 else "",
            control_number=gs_segment[6].strip() if gs_segment and len(gs_segment) > 6 else "",
        )
        interchange.functional_groups.append(functional_group)
        
        # Create transaction
        st_segment = next((seg for seg in segments if seg[0] == "ST"), None)
        transaction = Transaction(
            transaction_set_code=st_segment[1].strip() if st_segment and len(st_segment) > 1 else "",
            control_number=st_segment[2].strip() if st_segment and len(st_segment) > 2 else "",
        )
        transaction.healthcare_transaction = transaction_obj
        functional_group.transactions.append(transaction)
        
        return root
    
    def validate_segments(self, segments: List[List[str]]) -> bool:
        """Validate that segments contain required 276/277 structure."""
        has_isa = any(seg[0] == "ISA" for seg in segments if seg)
        has_st = any(seg[0] == "ST" and len(seg) > 1 and seg[1] in ["276", "277"] for seg in segments if seg)
        has_bht = any(seg[0] == "BHT" for seg in segments if seg)
        
        return has_isa and has_st and has_bht