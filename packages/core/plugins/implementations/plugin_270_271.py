"""
EDI 270/271 (Eligibility Inquiry/Response) Transaction Parser Plugin
"""

from typing import List, Type, Optional
from ..api import TransactionParserPlugin
from ...base.edi_ast import EdiRoot
from ...transactions.t270.ast import Transaction270, Transaction271
from ..parser_270 import Parser270


class Plugin270271(TransactionParserPlugin):
    """Plugin for parsing EDI 270/271 Eligibility Inquiry/Response transactions."""
    
    @property
    def transaction_codes(self) -> List[str]:
        return ["270", "271"]
    
    @property
    def plugin_name(self) -> str:
        return "EDI-270-271-Parser"
    
    @property
    def plugin_version(self) -> str:
        return "1.0.0"
    
    def get_transaction_class(self) -> Type:
        # Return base class since this handles both 270 and 271
        return Transaction270
    
    def get_schema_path(self) -> Optional[str]:
        return "schemas/270_271.json"
    
    def parse(self, segments: List[List[str]]) -> EdiRoot:
        """Parse 270/271 Eligibility transactions using existing parser."""
        from ...base.edi_ast import Interchange, FunctionalGroup, Transaction
        
        parser = Parser270(segments)
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
        """Validate that segments contain required 270/271 structure."""
        has_isa = any(seg[0] == "ISA" for seg in segments if seg)
        has_st = any(seg[0] == "ST" and len(seg) > 1 and seg[1] in ["270", "271"] for seg in segments if seg)
        has_bht = any(seg[0] == "BHT" for seg in segments if seg)
        
        return has_isa and has_st and has_bht