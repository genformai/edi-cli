"""
EDI 835 (Electronic Remittance Advice) Transaction Parser Plugin
"""

from typing import List, Type, Optional
from ..plugin_api import TransactionParserPlugin
from ..ast import EdiRoot, Interchange, FunctionalGroup, Transaction
from ..ast_835 import (
    Transaction835,
    FinancialInformation,
    Payer,
    Payee,
    Claim,
    Adjustment,
    Service,
)


def _format_yymmdd(date: str) -> str:
    """Formats YYMMDD to YYYY-MM-DD."""
    if len(date) == 6:
        return f"20{date[0:2]}-{date[2:4]}-{date[4:6]}"
    return date


def _format_ccyymmdd(date: str) -> str:
    """Formats CCYYMMDD to YYYY-MM-DD."""
    if len(date) == 8:
        return f"{date[0:4]}-{date[4:6]}-{date[6:8]}"
    return date


def _format_time(time: str) -> str:
    """Formats HHMM to HH:MM."""
    if len(time) == 4:
        return f"{time[0:2]}:{time[2:4]}"
    return time


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
                    sender_id=segment[6].strip() if len(segment) > 6 else "",
                    receiver_id=segment[8].strip() if len(segment) > 8 else "",
                    date=_format_yymmdd(segment[9]) if len(segment) > 9 else "",
                    time=_format_time(segment[10]) if len(segment) > 10 else "",
                    control_number=segment[13].strip() if len(segment) > 13 else "",
                )
                root.interchanges.append(current_interchange)
            
            elif segment_id == "GS" and current_interchange:
                # Create new functional group
                current_functional_group = FunctionalGroup(
                    functional_group_code=segment[1].strip() if len(segment) > 1 else "",
                    sender_id=segment[2].strip() if len(segment) > 2 else "",
                    receiver_id=segment[3].strip() if len(segment) > 3 else "",
                    date=_format_ccyymmdd(segment[4]) if len(segment) > 4 else "",
                    time=_format_time(segment[5]) if len(segment) > 5 else "",
                    control_number=segment[6].strip() if len(segment) > 6 else "",
                )
                current_interchange.functional_groups.append(current_functional_group)
            
            elif segment_id == "ST" and current_functional_group:
                # Create new transaction
                current_transaction = Transaction(
                    transaction_set_code=segment[1].strip() if len(segment) > 1 else "",
                    control_number=segment[2].strip() if len(segment) > 2 else "",
                )
                current_functional_group.transactions.append(current_transaction)
                
                # Create 835-specific transaction
                current_transaction_835 = Transaction835(
                    header={
                        "transaction_set_identifier": segment[1].strip() if len(segment) > 1 else "",
                        "transaction_set_control_number": segment[2].strip() if len(segment) > 2 else "",
                    }
                )
                current_transaction.financial_transaction = current_transaction_835
            
            elif segment_id == "BPR" and current_transaction_835:
                # Financial Information
                total_paid = float(segment[2]) if len(segment) > 2 and segment[2] else 0
                payment_method = segment[4] if len(segment) > 4 else ""
                payment_date = _format_ccyymmdd(segment[5]) if len(segment) > 5 and segment[5] else ""
                
                current_transaction_835.financial_information = FinancialInformation(
                    total_paid=total_paid,
                    payment_method=payment_method,
                    payment_date=payment_date
                )
            
            elif segment_id == "TRN" and current_transaction_835:
                # Reference Numbers
                if len(segment) > 2:
                    current_transaction_835.reference_numbers.append({
                        "type": "trace_number",
                        "value": segment[2].strip()
                    })
            
            elif segment_id == "DTM" and current_transaction_835 and not current_claim:
                # Dates (only at transaction level, not service level)
                if len(segment) > 2:
                    date_type = "production_date" if segment[1] == "405" else "other"
                    current_transaction_835.dates.append({
                        "type": date_type,
                        "date": _format_ccyymmdd(segment[2])
                    })
            
            elif segment_id == "N1" and current_transaction_835:
                # Payer/Payee Information
                entity_code = segment[1].strip() if len(segment) > 1 else ""
                name = segment[2].strip() if len(segment) > 2 else ""
                
                if entity_code == "PR":  # Payer
                    current_transaction_835.payer = Payer(name=name)
                elif entity_code == "PE":  # Payee
                    npi = segment[4].strip() if len(segment) > 4 else ""
                    current_transaction_835.payee = Payee(name=name, npi=npi)
            
            elif segment_id == "REF" and current_transaction_835 and current_transaction_835.payee:
                # Add NPI to payee if it's a payee NPI reference
                if len(segment) > 2 and segment[1] == "TJ":
                    current_transaction_835.payee.npi = segment[2].strip()
            
            elif segment_id == "CLP" and current_transaction_835:
                # Start new claim
                current_claim = Claim(
                    claim_id=segment[1].strip() if len(segment) > 1 else "",
                    status_code=int(segment[2]) if len(segment) > 2 and segment[2].isdigit() else 1,
                    total_charge=float(segment[3]) if len(segment) > 3 and segment[3] else 0,
                    total_paid=float(segment[4]) if len(segment) > 4 and segment[4] else 0,
                    patient_responsibility=float(segment[5]) if len(segment) > 5 and segment[5] else 0,
                    payer_control_number=segment[7].strip() if len(segment) > 7 else "",
                )
                current_transaction_835.claims.append(current_claim)
            
            elif segment_id == "CAS" and current_claim:
                # Claim Adjustments
                if len(segment) > 3:
                    adjustment = Adjustment(
                        group_code=segment[1].strip(),
                        reason_code=segment[2].strip(),
                        amount=float(segment[3]) if segment[3] else 0,
                        quantity=float(segment[4]) if len(segment) > 4 and segment[4] else 1,
                    )
                    current_claim.adjustments.append(adjustment)
            
            elif segment_id == "SVC" and current_claim:
                # Service Information
                service_code = segment[1].strip() if len(segment) > 1 else ""
                charge_amount = float(segment[2]) if len(segment) > 2 and segment[2] else 0
                paid_amount = float(segment[3]) if len(segment) > 3 and segment[3] else 0
                revenue_code = segment[4].strip() if len(segment) > 4 else ""
                
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
                if len(segment) > 2 and segment[1] == "484":
                    current_claim.services[-1].service_date = _format_ccyymmdd(segment[2])
        
        return root
    
    def validate_segments(self, segments: List[List[str]]) -> bool:
        """Validate that segments contain required 835 structure."""
        if not segments:
            return False
        
        try:
            has_isa = any(seg[0] == "ISA" for seg in segments if seg and len(seg) > 0)
            has_st = any(seg[0] == "ST" and len(seg) > 1 and seg[1].strip() == "835" for seg in segments if seg and len(seg) > 1)
            has_bpr = any(seg[0] == "BPR" for seg in segments if seg and len(seg) > 0)
            
            return has_isa and has_st and has_bpr
        except (IndexError, AttributeError):
            return False