"""
Base EDI builder with fluent API for constructing test fixtures.
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from decimal import Decimal

from ..base.data_types import (
    EDIEnvelope, EntityInfo, ClaimData, AdjustmentData, 
    ServiceData, PaymentInfo, Address, ContactInfo
)
from ..base.generators import DataGenerator


class EDIBuilder(ABC):
    """
    Abstract base class for EDI builders using fluent API pattern.
    
    Provides common functionality for building EDI transactions with
    method chaining and validation.
    """
    
    def __init__(self):
        """Initialize builder with defaults."""
        self.envelope = EDIEnvelope()
        self.payer: Optional[EntityInfo] = None
        self.payee: Optional[EntityInfo] = None
        self.claims: List[ClaimData] = []
        self.adjustments: List[AdjustmentData] = []
        self.services: List[ServiceData] = []
        self.payment: Optional[PaymentInfo] = None
        self.reference_numbers: List[Dict[str, str]] = []
        self.dates: List[Dict[str, str]] = []
        self._validation_enabled = True
        self._custom_segments: List[str] = []
    
    def with_envelope(
        self, 
        sender: str = None,
        receiver: str = None,
        functional_id: str = None,
        version: str = None
    ) -> 'EDIBuilder':
        """Configure envelope information."""
        if sender:
            self.envelope.sender_id = sender
        if receiver:
            self.envelope.receiver_id = receiver
        if functional_id:
            self.envelope.functional_id = functional_id
        if version:
            self.envelope.version = version
        return self
    
    def with_control_numbers(
        self,
        interchange: str = None,
        group: str = None, 
        transaction: str = None
    ) -> 'EDIBuilder':
        """Set specific control numbers."""
        if interchange:
            self.envelope.interchange_control = interchange
        if group:
            self.envelope.group_control = group
        if transaction:
            self.envelope.transaction_control = transaction
        return self
    
    def with_random_control_numbers(self) -> 'EDIBuilder':
        """Generate random control numbers."""
        self.envelope.interchange_control = DataGenerator.generate_control_number()
        self.envelope.group_control = DataGenerator.generate_control_number()
        self.envelope.transaction_control = DataGenerator.generate_control_number(4)
        return self
    
    def with_payer(
        self,
        name: str,
        id_value: str = None,
        id_qualifier: str = "PI",
        address: Address = None
    ) -> 'EDIBuilder':
        """Add payer information."""
        if id_value is None:
            id_value = DataGenerator.generate_payer_id()
        
        self.payer = EntityInfo(
            name=name,
            entity_type="2",
            id_qualifier=id_qualifier,
            id_value=id_value,
            address=address
        )
        return self
    
    def with_payee(
        self,
        name: str,
        npi: str = None,
        address: Address = None
    ) -> 'EDIBuilder':
        """Add payee information."""
        if npi is None:
            npi = DataGenerator.generate_npi()
            
        self.payee = EntityInfo(
            name=name,
            entity_type="2", 
            id_qualifier="XX",
            id_value=npi,
            address=address
        )
        return self
    
    def with_claim(
        self,
        claim_id: str = None,
        status: int = 1,
        charge: Decimal = None,
        paid: Decimal = None,
        patient_resp: Decimal = None
    ) -> 'EDIBuilder':
        """Add a claim."""
        if claim_id is None:
            claim_id = DataGenerator.generate_claim_id()
        if charge is None:
            charge = DataGenerator.generate_amount(100, 1000)
        if paid is None:
            paid = charge * Decimal("0.8")  # 80% payment rate
        if patient_resp is None:
            patient_resp = charge - paid
            
        claim = ClaimData(
            claim_id=claim_id,
            status=status,
            total_charge=charge,
            total_paid=paid,
            patient_responsibility=patient_resp
        )
        self.claims.append(claim)
        return self
    
    def with_adjustment(
        self,
        group_code: str,
        reason_code: str,
        amount: Decimal
    ) -> 'EDIBuilder':
        """Add a claim adjustment."""
        adjustment = AdjustmentData(
            group_code=group_code,
            reason_code=reason_code,
            amount=amount
        )
        self.adjustments.append(adjustment)
        return self
    
    def with_service(
        self,
        procedure_code: str,
        charge: Decimal,
        paid: Decimal,
        units: Decimal = Decimal("1")
    ) -> 'EDIBuilder':
        """Add a service line."""
        service = ServiceData(
            procedure_code=procedure_code,
            charge=charge,
            paid=paid,
            units=units
        )
        self.services.append(service)
        return self
    
    def with_payment(
        self,
        amount: Decimal,
        method: str = "ACH",
        transaction_type: str = "I"
    ) -> 'EDIBuilder':
        """Add payment information."""
        self.payment = PaymentInfo(
            amount=amount,
            payment_method=method,
            transaction_type=transaction_type
        )
        return self
    
    def with_reference(
        self,
        ref_type: str,
        ref_value: str
    ) -> 'EDIBuilder':
        """Add a reference number."""
        self.reference_numbers.append({
            "type": ref_type,
            "value": ref_value
        })
        return self
    
    def with_trace_number(self, trace_number: str = None) -> 'EDIBuilder':
        """Add a trace number."""
        if trace_number is None:
            trace_number = DataGenerator.generate_trace_number()
        return self.with_reference("trace_number", trace_number)
    
    def with_custom_segment(self, segment: str) -> 'EDIBuilder':
        """Add a custom EDI segment."""
        if not segment.endswith('~'):
            segment += '~'
        self._custom_segments.append(segment)
        return self
    
    def disable_validation(self) -> 'EDIBuilder':
        """Disable validation for testing error scenarios."""
        self._validation_enabled = False
        return self
    
    def enable_validation(self) -> 'EDIBuilder':
        """Enable validation (default)."""
        self._validation_enabled = True
        return self
    
    def validate(self) -> List[str]:
        """
        Validate the current builder state.
        
        Returns:
            List of validation error messages
        """
        errors = []
        
        if not self._validation_enabled:
            return errors
        
        # Check required components
        if self.transaction_type() == "835":
            if not self.payment:
                errors.append("835 transactions require payment information")
            if not self.claims:
                errors.append("835 transactions require at least one claim")
        
        # Validate claim balances
        for claim in self.claims:
            if claim.total_paid + claim.patient_responsibility > claim.total_charge:
                errors.append(f"Claim {claim.claim_id}: paid + patient responsibility exceeds charge")
        
        # Validate payment amount matches claim totals
        if self.payment and self.claims:
            total_claim_paid = sum(claim.total_paid for claim in self.claims)
            if abs(self.payment.amount - total_claim_paid) > Decimal("0.01"):
                errors.append(f"Payment amount {self.payment.amount} does not match total claim payments {total_claim_paid}")
        
        return errors
    
    @abstractmethod
    def transaction_type(self) -> str:
        """Return the transaction type (e.g., '835', '270')."""
        pass
    
    @abstractmethod
    def get_transaction_segments(self) -> List[str]:
        """Get transaction-specific segments."""
        pass
    
    def build(self) -> str:
        """
        Build the complete EDI transaction.
        
        Returns:
            Complete EDI string
            
        Raises:
            ValueError: If validation fails
        """
        # Validate if enabled
        if self._validation_enabled:
            errors = self.validate()
            if errors:
                raise ValueError(f"Validation failed: {'; '.join(errors)}")
        
        segments = []
        
        # Add envelope headers
        segments.append(self.envelope.get_isa_segment())
        segments.append(self.envelope.get_gs_segment())
        
        # Add transaction header
        segments.append(f"ST*{self.transaction_type()}*{self.envelope.transaction_control}~")
        
        # Add transaction-specific segments
        transaction_segments = self.get_transaction_segments()
        segments.extend(transaction_segments)
        
        # Add custom segments
        segments.extend(self._custom_segments)
        
        # Calculate segment count (ST to SE inclusive)
        segment_count = len(transaction_segments) + len(self._custom_segments) + 2  # +2 for ST and SE
        
        # Add transaction trailer
        segments.append(f"SE*{segment_count}*{self.envelope.transaction_control}~")
        
        # Add envelope trailers
        segments.append(self.envelope.get_ge_segment())
        segments.append(self.envelope.get_iea_segment())
        
        return "".join(segments)
    
    def build_minimal(self) -> str:
        """Build minimal valid EDI transaction."""
        # Temporarily disable validation and add minimal required data
        original_validation = self._validation_enabled
        self._validation_enabled = False
        
        try:
            # Ensure minimal required data exists
            if self.transaction_type() == "835" and not self.payment:
                self.with_payment(Decimal("0"), "NON")
            
            return self.build()
        finally:
            self._validation_enabled = original_validation
    
    def __str__(self) -> str:
        """String representation shows transaction type and key info."""
        info = [f"{self.transaction_type()} Transaction"]
        
        if self.payer:
            info.append(f"Payer: {self.payer.name}")
        if self.payee:
            info.append(f"Payee: {self.payee.name}")
        if self.claims:
            info.append(f"Claims: {len(self.claims)}")
        if self.payment:
            info.append(f"Payment: {self.payment.amount}")
            
        return " | ".join(info)