"""
EDI 835 (Healthcare Claim Payment/Advice) Parser

This module provides parsing capabilities for EDI 835 Healthcare Claim Payment/Advice
transactions, building the AST structures defined in ast.py.
"""

from typing import List, Optional
import logging
from ...base.parser import BaseParser
from ...base.edi_ast import EdiRoot, Interchange, FunctionalGroup, Transaction
from .ast import (
    Transaction835,
    FinancialInformation,
    Payer,
    Payee,
    Claim,
    Adjustment,
    Service,
)

logger = logging.getLogger(__name__)


class Parser835(BaseParser):
    """Parser for EDI 835 Healthcare Claim Payment/Advice transactions."""

    def get_transaction_codes(self) -> List[str]:
        """Get the transaction codes this parser supports."""
        return ["835"]

    def parse(self) -> EdiRoot:
        """
        Parse the 835 transaction from EDI segments.

        Returns:
            EdiRoot: Parsed EDI document with 835 transaction

        Raises:
            ValueError: If unable to parse the transaction
        """
        try:
            logger.debug("Parsing 835 healthcare claim payment/advice transaction")
            
            root = EdiRoot()
            current_interchange = None
            current_functional_group = None
            current_transaction = None
            current_transaction_835 = None
            current_claim = None
            
            for segment in self.segments:
                if not segment:
                    continue
                    
                segment_id = segment[0]
                
                if segment_id == "ISA":
                    current_interchange = Interchange(
                        sender_id=self._get_element(segment, 6),
                        receiver_id=self._get_element(segment, 8),
                        date=self._format_date_yymmdd(self._get_element(segment, 9)),
                        time=self._format_time(self._get_element(segment, 10)),
                        control_number=self._get_element(segment, 13),
                    )
                    root.interchanges.append(current_interchange)
                
                elif segment_id == "GS" and current_interchange:
                    current_functional_group = FunctionalGroup(
                        functional_group_code=self._get_element(segment, 1),
                        sender_id=self._get_element(segment, 2),
                        receiver_id=self._get_element(segment, 3),
                        date=self._format_date_ccyymmdd(self._get_element(segment, 4)),
                        time=self._format_time(self._get_element(segment, 5)),
                        control_number=self._get_element(segment, 6),
                    )
                    current_interchange.functional_groups.append(current_functional_group)
                
                elif segment_id == "ST" and current_functional_group:
                    current_transaction = Transaction(
                        transaction_set_code=self._get_element(segment, 1),
                        control_number=self._get_element(segment, 2),
                    )
                    current_functional_group.transactions.append(current_transaction)
                    
                    current_transaction_835 = Transaction835(
                        header={
                            "transaction_set_identifier": self._get_element(segment, 1),
                            "transaction_set_control_number": self._get_element(segment, 2),
                        }
                    )
                    current_transaction.financial_transaction = current_transaction_835
                
                elif segment_id == "BPR" and current_transaction_835:
                    total_paid = self._safe_float(self._get_element(segment, 2))
                    payment_method = self._get_element(segment, 4)  # BPR04 is payment method (ACH, CHK, etc.)
                    # BPR11 contains the effective date (CCYYMMDD format)
                    payment_date_raw = self._get_element(segment, 11)
                    payment_date = self._format_date_ccyymmdd(payment_date_raw)
                    
                    current_transaction_835.financial_information = FinancialInformation(
                        total_paid=total_paid,
                        payment_method=payment_method,
                        payment_date=payment_date
                    )
                
                elif segment_id == "TRN" and current_transaction_835:
                    reference_value = self._get_element(segment, 2)
                    if reference_value:
                        current_transaction_835.reference_numbers.append({
                            "type": "trace_number",
                            "value": reference_value
                        })
                
                elif segment_id == "DTM" and current_transaction_835:
                    date_qualifier = self._get_element(segment, 1)
                    date_value = self._get_element(segment, 2)
                    if date_value:
                        date_type = "production_date" if date_qualifier == "405" else "other"
                        current_transaction_835.dates.append({
                            "type": date_type,
                            "date": self._format_date_ccyymmdd(date_value)
                        })
                
                elif segment_id == "N1" and current_transaction_835:
                    entity_code = self._get_element(segment, 1)
                    name = self._get_element(segment, 2)
                    
                    if entity_code == "PR":
                        current_transaction_835.payer = Payer(name=name)
                    elif entity_code == "PE":
                        current_transaction_835.payee = Payee(name=name, npi="")
                
                elif segment_id == "REF" and current_transaction_835 and current_transaction_835.payee:
                    reference_qualifier = self._get_element(segment, 1)
                    reference_value = self._get_element(segment, 2)
                    if reference_qualifier == "TJ" and reference_value:
                        current_transaction_835.payee.npi = reference_value
                
                elif segment_id == "CLP" and current_transaction_835:
                    current_claim = Claim(
                        claim_id=self._get_element(segment, 1),
                        status_code=self._safe_int(self._get_element(segment, 2), 1),
                        total_charge=self._safe_float(self._get_element(segment, 3)),
                        total_paid=self._safe_float(self._get_element(segment, 4)),
                        patient_responsibility=self._safe_float(self._get_element(segment, 5)),
                        payer_control_number=self._get_element(segment, 7),
                    )
                    current_transaction_835.claims.append(current_claim)
                
                elif segment_id == "CAS" and current_claim:
                    group_code = self._get_element(segment, 1)
                    reason_code = self._get_element(segment, 2)
                    amount = self._safe_float(self._get_element(segment, 3))
                    quantity = self._safe_float(self._get_element(segment, 4), 1.0)
                    
                    if group_code and reason_code:
                        adjustment = Adjustment(
                            group_code=group_code,
                            reason_code=reason_code,
                            amount=amount,
                            quantity=quantity,
                        )
                        current_claim.adjustments.append(adjustment)
                
                elif segment_id == "SVC" and current_claim:
                    service_code = self._get_element(segment, 1)
                    charge_amount = self._safe_float(self._get_element(segment, 2))
                    paid_amount = self._safe_float(self._get_element(segment, 3))
                    
                    service = Service(
                        service_code=service_code,
                        charge_amount=charge_amount,
                        paid_amount=paid_amount,
                        revenue_code="",
                        service_date="",
                    )
                    current_claim.services.append(service)
                
                elif segment_id == "DTM" and current_claim and current_claim.services:
                    date_qualifier = self._get_element(segment, 1)
                    date_value = self._get_element(segment, 2)
                    if date_qualifier == "472" and date_value:
                        current_claim.services[-1].service_date = self._format_date_ccyymmdd(date_value)
            
            logger.debug(f"Parsed 835 transaction with {len(current_transaction_835.claims) if current_transaction_835 else 0} claims")
            return root
            
        except Exception as e:
            logger.error(f"Error parsing 835 transaction: {e}")
            raise ValueError(f"Failed to parse 835 transaction: {e}")