"""
EDI 835 (Electronic Remittance Advice) Transaction Parser Plugin
"""

from typing import List, Type, Optional
from ..api import TransactionParserPlugin
from ...base.edi_ast import EdiRoot, Interchange, FunctionalGroup, Transaction
from ...transactions.t835.ast import (
    Transaction835,
    FinancialInformation,
    Payer,
    Payee,
    Claim,
    Adjustment,
    Service,
)
from ...utils import get_element, safe_float, safe_int, format_edi_date, format_edi_time



class Plugin835(TransactionParserPlugin):
    """Plugin for parsing EDI 835 Electronic Remittance Advice transactions."""
    
    @property
    def transaction_codes(self) -> List[str]:
        return ["835"]
    
    @property
    def plugin_name(self) -> str:
        return "EDI-835-Parser"
    
    @property
    def plugin_version(self) -> str:
        return "1.0.0"
    
    def get_transaction_class(self) -> Type:
        return Transaction835
    
    def get_schema_path(self) -> Optional[str]:
        return "schemas/835.json"
    
    def parse(self, segments: List[List[str]]) -> EdiRoot:
        """Parse 835 Electronic Remittance Advice transaction."""
        root = EdiRoot()
        current_interchange = None
        current_functional_group = None
        current_transaction = None
        current_transaction_835 = None
        current_claim = None
        
        for segment in segments:
            if not segment:
                continue
                
            segment_id = segment[0]
            
            if segment_id == "ISA":
                # Create new interchange
                current_interchange = Interchange(
                    sender_id=get_element(segment, 6),
                    receiver_id=get_element(segment, 8),
                    date=format_edi_date(get_element(segment, 9), "YYMMDD"),
                    time=format_edi_time(get_element(segment, 10), "HHMM"),
                    control_number=get_element(segment, 13),
                )
                root.interchanges.append(current_interchange)
            
            elif segment_id == "GS" and current_interchange:
                # Create new functional group
                current_functional_group = FunctionalGroup(
                    functional_group_code=get_element(segment, 1),
                    sender_id=get_element(segment, 2),
                    receiver_id=get_element(segment, 3),
                    date=format_edi_date(get_element(segment, 4), "CCYYMMDD"),
                    time=format_edi_time(get_element(segment, 5), "HHMM"),
                    control_number=get_element(segment, 6),
                )
                current_interchange.functional_groups.append(current_functional_group)
            
            elif segment_id == "ST" and current_functional_group:
                # Create new transaction
                current_transaction = Transaction(
                    transaction_set_code=get_element(segment, 1),
                    control_number=get_element(segment, 2),
                )
                current_functional_group.transactions.append(current_transaction)
                
                # Create 835-specific transaction
                current_transaction_835 = Transaction835(
                    header={
                        "transaction_set_identifier": get_element(segment, 1),
                        "transaction_set_control_number": get_element(segment, 2),
                    }
                )
                current_transaction.financial_transaction = current_transaction_835
            
            elif segment_id == "BPR" and current_transaction_835:
                # Financial Information
                total_paid = safe_float(get_element(segment, 2))
                payment_method = get_element(segment, 4)
                payment_date = format_edi_date(get_element(segment, 11), "CCYYMMDD")
                
                current_transaction_835.financial_information = FinancialInformation(
                    total_paid=total_paid,
                    payment_method=payment_method,
                    payment_date=payment_date
                )
            
            elif segment_id == "TRN" and current_transaction_835:
                # Reference Numbers
                trace_number = get_element(segment, 2)
                if trace_number:
                    current_transaction_835.reference_numbers.append({
                        "type": "trace_number",
                        "value": trace_number
                    })
            
            elif segment_id == "DTM" and current_transaction_835 and not current_claim:
                # Dates (only at transaction level, not service level)
                date_qualifier = get_element(segment, 1)
                date_value = get_element(segment, 2)
                if date_value:
                    date_type = "production_date" if date_qualifier == "405" else "other"
                    current_transaction_835.dates.append({
                        "type": date_type,
                        "date": format_edi_date(date_value, "CCYYMMDD")
                    })
            
            elif segment_id == "N1" and current_transaction_835:
                # Payer/Payee Information
                entity_code = get_element(segment, 1)
                name = get_element(segment, 2)
                
                if entity_code == "PR":  # Payer
                    current_transaction_835.payer = Payer(name=name)
                elif entity_code == "PE":  # Payee
                    npi = get_element(segment, 4)
                    current_transaction_835.payee = Payee(name=name, npi=npi)
            
            elif segment_id == "REF" and current_transaction_835 and current_transaction_835.payee:
                # Add NPI to payee if it's a payee NPI reference
                ref_qualifier = get_element(segment, 1)
                ref_value = get_element(segment, 2)
                if ref_qualifier == "TJ" and ref_value:
                    current_transaction_835.payee.npi = ref_value
            
            elif segment_id == "CLP" and current_transaction_835:
                # Start new claim
                current_claim = Claim(
                    claim_id=get_element(segment, 1),
                    status_code=safe_int(get_element(segment, 2), 1),
                    total_charge=safe_float(get_element(segment, 3)),
                    total_paid=safe_float(get_element(segment, 4)),
                    patient_responsibility=safe_float(get_element(segment, 5)),
                    payer_control_number=get_element(segment, 7),
                )
                current_transaction_835.claims.append(current_claim)
            
            elif segment_id == "CAS" and current_claim:
                # Claim Adjustments
                group_code = get_element(segment, 1)
                reason_code = get_element(segment, 2)
                amount_str = get_element(segment, 3)
                if group_code and reason_code and amount_str:
                    adjustment = Adjustment(
                        group_code=group_code,
                        reason_code=reason_code,
                        amount=safe_float(amount_str),
                        quantity=safe_float(get_element(segment, 4), 1.0),
                    )
                    current_claim.adjustments.append(adjustment)
            
            elif segment_id == "SVC" and current_claim:
                # Service Information
                service_code = get_element(segment, 1)
                charge_amount = safe_float(get_element(segment, 2))
                paid_amount = safe_float(get_element(segment, 3))
                revenue_code = get_element(segment, 4)
                
                service = Service(
                    service_code=service_code,
                    charge_amount=charge_amount,
                    paid_amount=paid_amount,
                    revenue_code=revenue_code,
                    service_date="",
                )
                current_claim.services.append(service)
            
            elif segment_id == "DTM" and current_claim and current_claim.services:
                # Set service date for the most recent service
                date_qualifier = get_element(segment, 1)
                date_value = get_element(segment, 2)
                if date_qualifier == "484" and date_value:
                    current_claim.services[-1].service_date = format_edi_date(date_value, "CCYYMMDD")
        
        return root
    
    def validate_segments(self, segments: List[List[str]]) -> bool:
        """Validate that segments contain required 835 structure."""
        if not segments:
            return False
        
        try:
            has_isa = any(get_element(seg, 0) == "ISA" for seg in segments if seg)
            has_st = any(get_element(seg, 0) == "ST" and get_element(seg, 1) == "835" for seg in segments if seg)
            has_bpr = any(get_element(seg, 0) == "BPR" for seg in segments if seg)
            
            return has_isa and has_st and has_bpr
        except (IndexError, AttributeError):
            return False