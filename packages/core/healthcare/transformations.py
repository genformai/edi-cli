"""
Healthcare-Specific Data Transformations

This module provides healthcare-specific data transformation utilities for 
converting parsed EDI data into standardized formats, performing common 
healthcare calculations, and enabling integration with other healthcare systems.
"""

from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass
from datetime import datetime, timedelta
from decimal import Decimal
import re

from ..transactions.t835.ast import Transaction835, Claim as Claim835, Service as Service835
from ..transactions.t837p.ast import Transaction837P, ServiceLine837P, DiagnosisInfo
from ..transactions.t270.ast import Transaction270_271
from ..transactions.t276.ast import Transaction276_277


@dataclass
class StandardizedClaim:
    """Standardized claim representation across transaction types."""
    claim_id: str
    transaction_type: str  # 835, 837P, etc.
    patient_name: Optional[str] = None
    patient_id: Optional[str] = None
    provider_name: Optional[str] = None
    provider_npi: Optional[str] = None
    payer_name: Optional[str] = None
    service_date: Optional[str] = None
    total_charge: Optional[float] = None
    total_paid: Optional[float] = None
    patient_responsibility: Optional[float] = None
    status: Optional[str] = None
    diagnoses: List[str] = None
    procedure_codes: List[str] = None
    
    def __post_init__(self):
        if self.diagnoses is None:
            self.diagnoses = []
        if self.procedure_codes is None:
            self.procedure_codes = []
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "claim_id": self.claim_id,
            "transaction_type": self.transaction_type,
            "patient_name": self.patient_name,
            "patient_id": self.patient_id,
            "provider_name": self.provider_name,
            "provider_npi": self.provider_npi,
            "payer_name": self.payer_name,
            "service_date": self.service_date,
            "total_charge": self.total_charge,
            "total_paid": self.total_paid,
            "patient_responsibility": self.patient_responsibility,
            "status": self.status,
            "diagnoses": self.diagnoses,
            "procedure_codes": self.procedure_codes
        }


@dataclass
class PaymentSummary:
    """Payment summary across multiple claims and services."""
    total_claims: int
    total_charges: float
    total_payments: float
    total_adjustments: float
    total_patient_responsibility: float
    net_amount: float
    claims_paid: int
    claims_denied: int
    claims_pending: int
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_claims": self.total_claims,
            "total_charges": self.total_charges,
            "total_payments": self.total_payments,
            "total_adjustments": self.total_adjustments,
            "total_patient_responsibility": self.total_patient_responsibility,
            "net_amount": self.net_amount,
            "claims_paid": self.claims_paid,
            "claims_denied": self.claims_denied,
            "claims_pending": self.claims_pending
        }


class HealthcareTransformer:
    """Healthcare-specific data transformation utilities."""
    
    @staticmethod
    def standardize_claim_from_835(claim_835: Claim835, transaction: Transaction835) -> StandardizedClaim:
        """Convert an 835 claim to standardized format."""
        # Extract procedure codes from services
        procedure_codes = []
        if claim_835.services:
            for service in claim_835.services:
                if service.procedure_code:
                    procedure_codes.append(service.procedure_code)
                elif service.service_code:
                    # Extract procedure code from composite service code
                    proc_code = HealthcareTransformer._extract_procedure_code(service.service_code)
                    if proc_code:
                        procedure_codes.append(proc_code)
        
        return StandardizedClaim(
            claim_id=claim_835.claim_id,
            transaction_type="835",
            provider_name=transaction.payee.name if transaction.payee else None,
            provider_npi=transaction.payee.npi if transaction.payee else None,
            payer_name=transaction.payer.name if transaction.payer else None,
            total_charge=claim_835.total_charge,
            total_paid=claim_835.total_paid,
            patient_responsibility=claim_835.patient_responsibility,
            status=HealthcareTransformer._decode_claim_status(claim_835.status_code),
            procedure_codes=procedure_codes
        )
    
    @staticmethod
    def standardize_claim_from_837p(transaction: Transaction837P) -> StandardizedClaim:
        """Convert an 837P transaction to standardized format."""
        # Extract patient name
        patient_name = None
        patient_id = None
        if transaction.patient:
            patient_name = f"{transaction.patient.first_name} {transaction.patient.last_name}"
        elif transaction.subscriber:
            patient_name = f"{transaction.subscriber.first_name} {transaction.subscriber.last_name}"
            patient_id = transaction.subscriber.member_id
        
        # Extract diagnoses
        diagnoses = []
        if transaction.diagnoses:
            diagnoses = [dx.code for dx in transaction.diagnoses]
        
        # Extract procedure codes
        procedure_codes = []
        if transaction.service_lines:
            procedure_codes = [svc.procedure_code for svc in transaction.service_lines]
        
        return StandardizedClaim(
            claim_id=transaction.claim.claim_id if transaction.claim else "",
            transaction_type="837P",
            patient_name=patient_name,
            patient_id=patient_id,
            provider_name=transaction.billing_provider.name if transaction.billing_provider else None,
            provider_npi=transaction.billing_provider.npi if transaction.billing_provider else None,
            payer_name=transaction.receiver.name if transaction.receiver else None,
            total_charge=transaction.claim.total_charge if transaction.claim else None,
            diagnoses=diagnoses,
            procedure_codes=procedure_codes
        )
    
    @staticmethod
    def calculate_payment_summary(transaction: Transaction835) -> PaymentSummary:
        """Calculate comprehensive payment summary from 835 transaction."""
        if not transaction.claims:
            return PaymentSummary(0, 0.0, 0.0, 0.0, 0.0, 0.0, 0, 0, 0)
        
        total_claims = len(transaction.claims)
        total_charges = sum(claim.total_charge for claim in transaction.claims)
        total_payments = sum(claim.total_paid for claim in transaction.claims)
        total_patient_responsibility = sum(claim.patient_responsibility for claim in transaction.claims)
        
        # Calculate adjustments from claim adjustments
        total_adjustments = 0.0
        for claim in transaction.claims:
            if claim.adjustments:
                total_adjustments += sum(adj.amount for adj in claim.adjustments)
        
        # Add PLB adjustments
        if transaction.plb:
            for plb_entry in transaction.plb:
                if isinstance(plb_entry, dict) and 'adjustment_amount' in plb_entry:
                    total_adjustments += float(plb_entry['adjustment_amount'])
        
        # Count claim statuses
        claims_paid = 0
        claims_denied = 0
        claims_pending = 0
        
        for claim in transaction.claims:
            status = claim.status_code
            if status in ['1', '2', '3', '4']:  # Paid statuses
                claims_paid += 1
            elif status in ['5', '6', '7', '8']:  # Denied/rejected statuses
                claims_denied += 1
            else:
                claims_pending += 1
        
        net_amount = total_payments + total_adjustments + total_patient_responsibility
        
        return PaymentSummary(
            total_claims=total_claims,
            total_charges=total_charges,
            total_payments=total_payments,
            total_adjustments=total_adjustments,
            total_patient_responsibility=total_patient_responsibility,
            net_amount=net_amount,
            claims_paid=claims_paid,
            claims_denied=claims_denied,
            claims_pending=claims_pending
        )
    
    @staticmethod
    def extract_denial_reasons(claim: Claim835) -> List[Dict[str, Any]]:
        """Extract and decode denial/adjustment reasons from a claim."""
        reasons = []
        
        if claim.adjustments:
            for adj in claim.adjustments:
                reason_desc = HealthcareTransformer._decode_adjustment_reason(adj.reason_code)
                reasons.append({
                    "group_code": adj.group_code,
                    "reason_code": adj.reason_code,
                    "reason_description": reason_desc,
                    "amount": adj.amount,
                    "type": HealthcareTransformer._categorize_adjustment_group(adj.group_code)
                })
        
        return reasons
    
    @staticmethod
    def format_for_clearinghouse(transaction: Union[Transaction835, Transaction837P]) -> Dict[str, Any]:
        """Format transaction data for clearinghouse integration."""
        if isinstance(transaction, Transaction835):
            return HealthcareTransformer._format_835_for_clearinghouse(transaction)
        elif isinstance(transaction, Transaction837P):
            return HealthcareTransformer._format_837p_for_clearinghouse(transaction)
        else:
            raise ValueError(f"Unsupported transaction type: {type(transaction)}")
    
    @staticmethod
    def generate_claim_aging_report(claims: List[StandardizedClaim]) -> Dict[str, Any]:
        """Generate aging report for claims based on service dates."""
        aging_buckets = {
            "0-30": {"count": 0, "amount": 0.0},
            "31-60": {"count": 0, "amount": 0.0},
            "61-90": {"count": 0, "amount": 0.0},
            "91-120": {"count": 0, "amount": 0.0},
            "120+": {"count": 0, "amount": 0.0}
        }
        
        today = datetime.now()
        
        for claim in claims:
            if not claim.service_date or not claim.total_charge:
                continue
            
            try:
                service_date = datetime.strptime(claim.service_date, "%Y%m%d")
                days_old = (today - service_date).days
                
                if days_old <= 30:
                    bucket = "0-30"
                elif days_old <= 60:
                    bucket = "31-60"
                elif days_old <= 90:
                    bucket = "61-90"
                elif days_old <= 120:
                    bucket = "91-120"
                else:
                    bucket = "120+"
                
                aging_buckets[bucket]["count"] += 1
                aging_buckets[bucket]["amount"] += claim.total_charge
                
            except ValueError:
                # Skip claims with invalid dates
                continue
        
        return {
            "aging_buckets": aging_buckets,
            "total_claims": sum(bucket["count"] for bucket in aging_buckets.values()),
            "total_amount": sum(bucket["amount"] for bucket in aging_buckets.values())
        }
    
    @staticmethod
    def validate_npi(npi: str) -> bool:
        """Validate NPI (National Provider Identifier) using Luhn algorithm."""
        if not npi or len(npi) != 10 or not npi.isdigit():
            return False
        
        # NPI validation using Luhn algorithm
        digits = [int(d) for d in npi]
        checksum = 0
        
        # Process digits from right to left
        for i in range(len(digits) - 1, -1, -1):
            n = digits[i]
            if (len(digits) - i) % 2 == 0:  # Even position from right
                n *= 2
                if n > 9:
                    n = n // 10 + n % 10
            checksum += n
        
        return checksum % 10 == 0
    
    @staticmethod
    def normalize_provider_data(provider_info: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize provider information across different transaction types."""
        normalized = {
            "name": provider_info.get("name", "").strip().title(),
            "npi": provider_info.get("npi", "").strip(),
            "tax_id": provider_info.get("tax_id", "").strip(),
            "address": {}
        }
        
        # Validate NPI if present
        if normalized["npi"]:
            normalized["npi_valid"] = HealthcareTransformer.validate_npi(normalized["npi"])
        
        # Normalize address
        if "address" in provider_info and provider_info["address"]:
            addr = provider_info["address"]
            normalized["address"] = {
                "street": addr.get("street", "").strip().title(),
                "city": addr.get("city", "").strip().title(),
                "state": addr.get("state", "").strip().upper(),
                "zip": addr.get("zip", "").strip()
            }
        
        return normalized
    
    # Private helper methods
    
    @staticmethod
    def _extract_procedure_code(service_code: str) -> Optional[str]:
        """Extract procedure code from composite service code."""
        if not service_code:
            return None
        
        # Service code format: HC:99213 or similar
        parts = service_code.split(':')
        if len(parts) >= 2:
            return parts[1].strip()
        
        return service_code.strip()
    
    @staticmethod
    def _decode_claim_status(status_code: str) -> str:
        """Decode 835 claim status codes."""
        status_map = {
            "1": "Processed as Primary",
            "2": "Processed as Secondary", 
            "3": "Processed as Tertiary",
            "4": "Denied",
            "5": "Pended",
            "19": "Processed as Primary, Forwarded to Additional Payer(s)",
            "20": "Processed as Secondary, Forwarded to Additional Payer(s)",
            "21": "Processed as Tertiary, Forwarded to Additional Payer(s)",
            "22": "Reversal of Previous Payment",
            "23": "Not Our Claim, Forwarded to Additional Payer(s)",
            "25": "Predetermination Pricing Only - No Payment"
        }
        return status_map.get(status_code, f"Unknown Status ({status_code})")
    
    @staticmethod
    def _decode_adjustment_reason(reason_code: str) -> str:
        """Decode common adjustment reason codes."""
        # This is a subset of CARC (Claim Adjustment Reason Codes)
        reason_map = {
            "1": "Deductible Amount",
            "2": "Coinsurance Amount", 
            "3": "Co-payment Amount",
            "4": "The procedure code is inconsistent with the modifier used",
            "5": "The procedure code/bill type is inconsistent with the place of service",
            "11": "The diagnosis is inconsistent with the procedure",
            "12": "The diagnosis is inconsistent with the patient's age",
            "13": "The diagnosis is inconsistent with the patient's gender",
            "18": "Duplicate claim/service",
            "29": "The time limit for filing has expired",
            "50": "These are non-covered services because this is not deemed a 'medical necessity'",
            "96": "Non-covered charge(s)",
            "97": "The benefit for this service is included in the payment/allowance for another service/procedure",
            "109": "Claim not covered by this payer/contractor",
            "151": "Payment adjusted because the payer deems the information submitted does not support this many/frequency of services"
        }
        return reason_map.get(reason_code, f"Adjustment Reason {reason_code}")
    
    @staticmethod
    def _categorize_adjustment_group(group_code: str) -> str:
        """Categorize adjustment group codes."""
        group_map = {
            "CO": "Contractual Obligation",
            "CR": "Correction and Reversal", 
            "OA": "Other Adjustment",
            "PI": "Payer Initiated Reduction",
            "PR": "Patient Responsibility"
        }
        return group_map.get(group_code, f"Unknown Group ({group_code})")
    
    @staticmethod
    def _format_835_for_clearinghouse(transaction: Transaction835) -> Dict[str, Any]:
        """Format 835 transaction for clearinghouse integration."""
        standardized_claims = []
        
        if transaction.claims:
            for claim in transaction.claims:
                std_claim = HealthcareTransformer.standardize_claim_from_835(claim, transaction)
                standardized_claims.append(std_claim.to_dict())
        
        return {
            "transaction_type": "835",
            "payer": transaction.payer.to_dict() if transaction.payer else None,
            "payee": transaction.payee.to_dict() if transaction.payee else None,
            "payment_info": transaction.financial_information.to_dict() if transaction.financial_information else None,
            "claims": standardized_claims,
            "summary": HealthcareTransformer.calculate_payment_summary(transaction).to_dict()
        }
    
    @staticmethod
    def _format_837p_for_clearinghouse(transaction: Transaction837P) -> Dict[str, Any]:
        """Format 837P transaction for clearinghouse integration."""
        std_claim = HealthcareTransformer.standardize_claim_from_837p(transaction)
        
        return {
            "transaction_type": "837P",
            "submitter": transaction.submitter.to_dict() if transaction.submitter else None,
            "receiver": transaction.receiver.to_dict() if transaction.receiver else None,
            "billing_provider": transaction.billing_provider.to_dict() if transaction.billing_provider else None,
            "claim": std_claim.to_dict()
        }


# Utility functions for common healthcare calculations

def calculate_allowed_amount(charge_amount: float, payment_amount: float, patient_responsibility: float) -> float:
    """Calculate the allowed amount for a service."""
    return payment_amount + patient_responsibility

def calculate_write_off_amount(charge_amount: float, allowed_amount: float) -> float:
    """Calculate the write-off amount."""
    return max(0, charge_amount - allowed_amount)

def calculate_copay_percentage(payment_amount: float, allowed_amount: float) -> float:
    """Calculate the copay percentage."""
    if allowed_amount == 0:
        return 0.0
    return (payment_amount / allowed_amount) * 100

def format_currency(amount: Union[float, Decimal]) -> str:
    """Format amount as currency."""
    return f"${amount:,.2f}"

def format_date_edi_to_readable(edi_date: str) -> str:
    """Convert EDI date format (YYYYMMDD) to readable format."""
    if not edi_date or len(edi_date) != 8:
        return edi_date
    
    try:
        date_obj = datetime.strptime(edi_date, "%Y%m%d")
        return date_obj.strftime("%m/%d/%Y")
    except ValueError:
        return edi_date