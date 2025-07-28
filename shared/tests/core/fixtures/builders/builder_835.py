"""
EDI 835 (Electronic Remittance Advice) builder.
"""

from typing import List, Optional
from decimal import Decimal
from datetime import date

from .edi_builder import EDIBuilder
from ..base.data_types import (
    PaymentInfo, PaymentMethod, ClaimStatus, AdjustmentGroup,
    EntityInfo, Address
)
from ..base.generators import DataGenerator, NameGenerator, AddressGenerator


class EDI835Builder(EDIBuilder):
    """Builder for EDI 835 Electronic Remittance Advice transactions."""
    
    def __init__(self):
        """Initialize 835 builder with appropriate defaults."""
        super().__init__()
        
        # Set 835-specific envelope defaults
        self.envelope.functional_id = "HP"  # Health Care Payment
        self.envelope.version = "005010X221A1"
        
        # Initialize with default payment info
        self.payment = PaymentInfo()
    
    def transaction_type(self) -> str:
        """Return transaction type."""
        return "835"
    
    def with_ach_payment(
        self,
        amount: Decimal,
        routing_number: str = None,
        account_number: str = None,
        company_id: str = None
    ) -> 'EDI835Builder':
        """Configure ACH payment details."""
        if routing_number is None:
            routing_number = DataGenerator.generate_control_number(9)
        if account_number is None:
            account_number = DataGenerator.generate_control_number(10)
        if company_id is None:
            company_id = DataGenerator.generate_control_number(10)
            
        self.payment = PaymentInfo(
            transaction_type="I",
            amount=amount,
            payment_method=PaymentMethod.ACH,
            dfi_number=routing_number,
            account_number=account_number,
            originating_company_id=company_id
        )
        return self
    
    def with_check_payment(
        self,
        amount: Decimal,
        check_number: str = None
    ) -> 'EDI835Builder':
        """Configure check payment details."""
        if check_number is None:
            check_number = f"CHK{DataGenerator.generate_control_number(6)}"
            
        self.payment = PaymentInfo(
            transaction_type="I",
            amount=amount,
            payment_method=PaymentMethod.CHECK,
            originating_company_id=check_number
        )
        return self
    
    def with_wire_payment(
        self,
        amount: Decimal,
        wire_reference: str = None
    ) -> 'EDI835Builder':
        """Configure wire transfer payment details."""
        if wire_reference is None:
            wire_reference = f"WIRE{DataGenerator.generate_control_number(6)}"
            
        self.payment = PaymentInfo(
            transaction_type="I",
            amount=amount,
            payment_method=PaymentMethod.WIRE,
            originating_company_id=wire_reference
        )
        return self
    
    def with_no_payment(self) -> 'EDI835Builder':
        """Configure as advice-only (no payment)."""
        self.payment = PaymentInfo(
            transaction_type="H",
            amount=Decimal("0"),
            payment_method=PaymentMethod.NON
        )
        return self
    
    def with_primary_claim(
        self,
        claim_id: str = None,
        charge: Decimal = None,
        paid: Decimal = None,
        patient_resp: Decimal = None
    ) -> 'EDI835Builder':
        """Add a primary processed claim."""
        return self.with_claim(
            claim_id=claim_id,
            status=ClaimStatus.PRIMARY_PROCESSED.value,
            charge=charge,
            paid=paid,
            patient_resp=patient_resp
        )
    
    def with_secondary_claim(
        self,
        claim_id: str = None,
        charge: Decimal = None,
        paid: Decimal = None,
        patient_resp: Decimal = None,
        prior_payer_paid: Decimal = None
    ) -> 'EDI835Builder':
        """Add a secondary processed claim."""
        claim = self.with_claim(
            claim_id=claim_id,
            status=ClaimStatus.SECONDARY_PROCESSED.value,
            charge=charge,
            paid=paid,
            patient_resp=patient_resp
        )
        
        # Add coordination of benefits info
        if prior_payer_paid:
            self.with_custom_segment(f"AMT*A8*{prior_payer_paid}~")
        
        return claim
    
    def with_denied_claim(
        self,
        claim_id: str = None,
        charge: Decimal = None,
        denial_reason: str = "29"
    ) -> 'EDI835Builder':
        """Add a denied claim."""
        if charge is None:
            charge = DataGenerator.generate_amount(100, 1000)
            
        self.with_claim(
            claim_id=claim_id,
            status=ClaimStatus.DENIED.value,
            charge=charge,
            paid=Decimal("0"),
            patient_resp=Decimal("0")
        )
        
        # Add denial adjustment
        self.with_adjustment(
            AdjustmentGroup.CONTRACTUAL.value,
            denial_reason,
            charge
        )
        
        return self
    
    def with_reversal_claim(
        self,
        claim_id: str = None,
        amount: Decimal = None,
        original_claim_ref: str = None
    ) -> 'EDI835Builder':
        """Add a reversal/adjustment claim."""
        if amount is None:
            amount = DataGenerator.generate_amount(100, 1000)
            
        self.with_claim(
            claim_id=claim_id,
            status=ClaimStatus.REVERSAL.value,
            charge=-amount,
            paid=-amount,
            patient_resp=Decimal("0")
        )
        
        # Add reversal adjustment
        self.with_adjustment(
            AdjustmentGroup.OTHER.value,
            "94",  # Reversal of prior payment
            -amount
        )
        
        # Add reference to original claim
        if original_claim_ref:
            self.with_custom_segment(f"REF*F8*{original_claim_ref}~")
        
        return self
    
    def with_capitation_claim(
        self,
        claim_id: str = None
    ) -> 'EDI835Builder':
        """Add a capitation claim."""
        return self.with_claim(
            claim_id=claim_id,
            status=ClaimStatus.CAPITATION.value,
            charge=Decimal("0"),
            paid=Decimal("0"),
            patient_resp=Decimal("0")
        )
    
    def with_patient_responsibility_adjustment(
        self,
        reason_code: str = "1",
        amount: Decimal = None
    ) -> 'EDI835Builder':
        """Add patient responsibility adjustment."""
        if amount is None:
            amount = DataGenerator.generate_amount(10, 100)
            
        return self.with_adjustment(
            AdjustmentGroup.PATIENT_RESP.value,
            reason_code,
            amount
        )
    
    def with_contractual_adjustment(
        self,
        reason_code: str = "45",
        amount: Decimal = None
    ) -> 'EDI835Builder':
        """Add contractual adjustment."""
        if amount is None:
            amount = DataGenerator.generate_amount(10, 100)
            
        return self.with_adjustment(
            AdjustmentGroup.CONTRACTUAL.value,
            reason_code,
            amount
        )
    
    def with_realistic_payer(self, name: str = None) -> 'EDI835Builder':
        """Add realistic payer with address."""
        if name is None:
            name = f"{NameGenerator.generate_company_name()} INSURANCE"
        
        address = Address(
            line1=AddressGenerator.generate_street_address(),
            city=AddressGenerator.generate_city(),
            state=AddressGenerator.generate_state(),
            zip_code=DataGenerator.generate_zip_code()
        )
        
        return self.with_payer(
            name=name,
            id_value=DataGenerator.generate_ein(),
            id_qualifier="FI",
            address=address
        )
    
    def with_realistic_payee(self, name: str = None) -> 'EDI835Builder':
        """Add realistic payee with NPI and address."""
        if name is None:
            name = f"{NameGenerator.generate_company_name()} CLINIC"
        
        address = Address(
            line1=AddressGenerator.generate_street_address(),
            city=AddressGenerator.generate_city(),
            state=AddressGenerator.generate_state(),
            zip_code=DataGenerator.generate_zip_code()
        )
        
        return self.with_payee(
            name=name,
            npi=DataGenerator.generate_npi(),
            address=address
        )
    
    def with_multiple_claims(self, count: int = 3) -> 'EDI835Builder':
        """Add multiple realistic claims."""
        total_paid = Decimal("0")
        
        for i in range(count):
            charge = DataGenerator.generate_amount(100, 1000)
            paid = charge * Decimal("0.8")  # 80% payment rate
            patient_resp = charge - paid
            
            self.with_claim(
                claim_id=f"CLM{i+1:03d}",
                status=1,
                charge=charge,
                paid=paid,
                patient_resp=patient_resp
            )
            
            # Add some adjustments
            self.with_patient_responsibility_adjustment(
                amount=patient_resp * Decimal("0.5")
            )
            self.with_contractual_adjustment(
                amount=patient_resp * Decimal("0.5") 
            )
            
            total_paid += paid
        
        # Update payment amount to match claims
        if self.payment:
            self.payment.amount = total_paid
        
        return self
    
    def get_transaction_segments(self) -> List[str]:
        """Get 835-specific transaction segments."""
        segments = []
        
        # BPR - Beginning Segment for Payment Order/Remittance Advice
        if self.payment:
            segments.append(self.payment.to_bpr_segment())
        
        # TRN - Trace Number
        if self.reference_numbers:
            for ref in self.reference_numbers:
                if ref["type"] == "trace_number":
                    segments.append(f"TRN*1*{ref['value']}*{DataGenerator.generate_control_number()}~")
        else:
            # Add default trace number
            trace_num = DataGenerator.generate_trace_number()
            segments.append(f"TRN*1*{trace_num}*{DataGenerator.generate_control_number()}~")
        
        # DTM - Production Date (optional)
        if self.payment and self.payment.payment_date:
            date_str = self.payment.payment_date.strftime("%Y%m%d")
            segments.append(f"DTM*405*{date_str}~")
        
        # N1 - Payer Identification
        if self.payer:
            segments.append(self.payer.to_nm1_segment("PR"))
            if self.payer.address:
                segments.append(self.payer.address.to_n3_segment())
                segments.append(self.payer.address.to_n4_segment())
        
        # N1 - Payee Identification  
        if self.payee:
            segments.append(self.payee.to_nm1_segment("PE"))
            if self.payee.address:
                segments.append(self.payee.address.to_n3_segment())
                segments.append(self.payee.address.to_n4_segment())
            
            # REF - Payee Tax ID or NPI
            if self.payee.id_qualifier == "XX":  # NPI
                segments.append(f"REF*TJ*{self.payee.id_value}~")
            elif self.payee.id_qualifier == "FI":  # Tax ID
                segments.append(f"REF*FI*{self.payee.id_value}~")
        
        # Claims and adjustments
        for i, claim in enumerate(self.claims):
            # CLP - Claim Payment Information
            segments.append(claim.to_clp_segment())
            
            # Patient information (simplified)
            first, middle, last = NameGenerator.generate_person_name()
            patient_id = DataGenerator.generate_control_number(9)
            segments.append(f"NM1*QC*1*{last}*{first}*{middle}***MI*{patient_id}~")
            
            # Service dates
            service_date = DataGenerator.generate_date()
            date_str = service_date.strftime("%Y%m%d")
            segments.append(f"DTM*232*{date_str}~")
            
            # Claim adjustments (get adjustments for this claim)
            claim_adjustments = self.adjustments[i*2:(i+1)*2] if i*2 < len(self.adjustments) else []
            for adjustment in claim_adjustments:
                segments.append(adjustment.to_cas_segment())
            
            # Service lines for this claim
            claim_services = [s for s in self.services if s.procedure_code]  # Simplified association
            for service in claim_services[:1]:  # Max 1 service per claim for simplicity
                segments.append(service.to_svc_segment())
                segments.append(f"DTM*472*{date_str}~")
        
        return segments
    
    @classmethod
    def minimal(cls) -> 'EDI835Builder':
        """Create minimal valid 835."""
        return (cls()
                .with_no_payment()
                .with_payer("MINIMAL PAYER")
                .with_payee("MINIMAL PAYEE") 
                .with_claim(claim_id="MIN001", charge=Decimal("0"), paid=Decimal("0"), patient_resp=Decimal("0")))
    
    @classmethod
    def standard(cls) -> 'EDI835Builder':
        """Create standard 835 with typical data."""
        return (cls()
                .with_realistic_payer()
                .with_realistic_payee()
                .with_ach_payment(Decimal("1200.00"))
                .with_multiple_claims(2)
                .with_trace_number())
    
    @classmethod
    def complex(cls) -> 'EDI835Builder':
        """Create complex 835 with multiple scenarios."""
        builder = (cls()
                   .with_realistic_payer("ACME HEALTH INSURANCE")
                   .with_realistic_payee("MEDICAL CENTER CLINIC")
                   .with_ach_payment(Decimal("2100.00")))
        
        # Add various claim types
        builder.with_primary_claim("CLM001", Decimal("500.00"), Decimal("400.00"), Decimal("100.00"))
        builder.with_secondary_claim("CLM002", Decimal("700.00"), Decimal("600.00"), Decimal("100.00"))
        builder.with_denied_claim("CLM003", Decimal("300.00"))
        builder.with_reversal_claim("CLM004", Decimal("200.00"))
        
        return builder