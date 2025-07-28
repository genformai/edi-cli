"""
Payment-related EDI scenarios for testing different payment methods and situations.
"""

from decimal import Decimal
from typing import Dict, Any

from ..builders.builder_835 import EDI835Builder
from ..base.data_types import PaymentMethod
from ..base.generators import DataGenerator


class PaymentScenarios:
    """Collection of payment-related EDI scenarios."""
    
    @staticmethod
    def ach_payment_standard() -> EDI835Builder:
        """Standard ACH payment scenario."""
        return (EDI835Builder()
                .with_realistic_payer("ACME HEALTH INSURANCE")
                .with_realistic_payee("MEDICAL CENTER CLINIC")
                .with_ach_payment(Decimal("1245.67"))
                .with_primary_claim(charge=Decimal("500.00"), paid=Decimal("400.00"), patient_resp=Decimal("100.00"))
                .with_primary_claim(charge=Decimal("745.67"), paid=Decimal("645.67"), patient_resp=Decimal("100.00"))
                .with_patient_responsibility_adjustment(amount=Decimal("100.00"))
                .with_contractual_adjustment(amount=Decimal("100.00"))
                .with_trace_number())
    
    @staticmethod  
    def check_payment_large() -> EDI835Builder:
        """Large check payment scenario."""
        return (EDI835Builder()
                .with_realistic_payer("NATIONAL HEALTH PLAN")
                .with_realistic_payee("REGIONAL MEDICAL GROUP")
                .with_check_payment(Decimal("15750.25"), "CHK9876543")
                .with_multiple_claims(8)
                .with_trace_number())
    
    @staticmethod
    def wire_transfer_urgent() -> EDI835Builder:
        """Wire transfer for urgent payment scenario."""
        return (EDI835Builder()
                .with_realistic_payer("EMERGENCY HEALTH FUND")
                .with_realistic_payee("TRAUMA CENTER")
                .with_wire_payment(Decimal("28900.00"), "WIRE2024001")
                .with_primary_claim("EMERGENCY001", Decimal("15000.00"), Decimal("12000.00"), Decimal("3000.00"))
                .with_primary_claim("EMERGENCY002", Decimal("13900.00"), Decimal("11100.00"), Decimal("2800.00"))
                .with_trace_number())
    
    @staticmethod
    def no_payment_advice_only() -> EDI835Builder:
        """Advice-only transaction with no payment."""
        return (EDI835Builder()
                .with_realistic_payer("REVIEW HEALTH PLAN")
                .with_realistic_payee("SPECIALIST CLINIC")
                .with_no_payment()
                .with_denied_claim("DENIED001", Decimal("250.00"), "29")
                .with_denied_claim("DENIED002", Decimal("180.00"), "96")
                .with_trace_number("ADVICE12345"))
    
    @staticmethod
    def mixed_claim_statuses() -> EDI835Builder:
        """Payment with mixed claim processing outcomes."""
        builder = (EDI835Builder()
                   .with_realistic_payer("COMPREHENSIVE INSURANCE")
                   .with_realistic_payee("FAMILY PRACTICE")
                   .with_ach_payment(Decimal("1850.00"))
                   .with_trace_number())
        
        # Add various claim types
        builder.with_primary_claim("PAID001", Decimal("600.00"), Decimal("480.00"), Decimal("120.00"))
        builder.with_secondary_claim("PAID002", Decimal("500.00"), Decimal("300.00"), Decimal("50.00"))
        builder.with_denied_claim("DENIED003", Decimal("200.00"))
        builder.with_reversal_claim("REVERSE004", Decimal("150.00"), "PAID001")
        builder.with_primary_claim("PAID005", Decimal("400.00"), Decimal("320.00"), Decimal("80.00"))
        
        return builder
    
    @staticmethod
    def coordination_of_benefits() -> EDI835Builder:
        """Secondary payer with coordination of benefits."""
        return (EDI835Builder()
                .with_realistic_payer("SECONDARY HEALTH PLAN")
                .with_realistic_payee("COORDINATED CARE CLINIC")
                .with_ach_payment(Decimal("450.00"))
                .with_secondary_claim(
                    "COB001", 
                    Decimal("1000.00"),    # Total charge
                    Decimal("450.00"),     # Secondary pays
                    Decimal("50.00"),      # Patient responsibility  
                    Decimal("500.00")      # Primary already paid
                )
                .with_custom_segment("AMT*AU*500.00~")  # Prior payer amount
                .with_adjustment("PR", "3", Decimal("50.00"))  # Deductible
                .with_trace_number())
    
    @staticmethod
    def overpayment_recovery() -> EDI835Builder:
        """Overpayment recovery scenario with negative amounts."""
        return (EDI835Builder()
                .with_realistic_payer("RECOVERY INSURANCE")
                .with_realistic_payee("MEDICAL ASSOCIATES")
                .with_ach_payment(Decimal("350.00"))  # Net after recovery
                .with_primary_claim("REGULAR001", Decimal("500.00"), Decimal("450.00"), Decimal("50.00"))
                .with_reversal_claim("RECOVERY002", Decimal("100.00"), "OVERPAID123")
                .with_custom_segment("PLB*1234567890*20241201*L6*-100.00~")  # Provider adjustment
                .with_trace_number())
    
    @staticmethod
    def zero_payment_adjustments_only() -> EDI835Builder:
        """Zero payment with only adjustments applied."""
        return (EDI835Builder()
                .with_realistic_payer("ADJUSTMENT HEALTH PLAN")
                .with_realistic_payee("BILLING SPECIALISTS")
                .with_payment(Decimal("0"), "NON", "H")  # Advice only
                .with_claim("ADJ001", 4, Decimal("300.00"), Decimal("0"), Decimal("0"))  # Denied
                .with_adjustment("CO", "29", Decimal("300.00"))  # Not covered
                .with_trace_number("ADJUST001"))
    
    @staticmethod
    def high_volume_batch() -> EDI835Builder:
        """High-volume batch payment scenario."""
        builder = (EDI835Builder()
                   .with_realistic_payer("BATCH PROCESSING INSURANCE")
                   .with_realistic_payee("LARGE MEDICAL GROUP")
                   .with_ach_payment(Decimal("45000.00"))
                   .with_trace_number("BATCH2024"))
        
        # Add 15 claims with varying amounts
        for i in range(1, 16):
            charge = Decimal(str(200 + (i * 50)))  # $250, $300, $350, etc.
            paid = charge * Decimal("0.85")  # 85% payment rate
            patient_resp = charge - paid
            
            builder.with_primary_claim(
                f"BATCH{i:03d}",
                charge, 
                paid,
                patient_resp
            )
        
        return builder
    
    @staticmethod
    def international_provider() -> EDI835Builder:
        """Payment to international provider."""
        return (EDI835Builder()
                .with_realistic_payer("GLOBAL HEALTH INSURANCE")
                .with_payee("INTERNATIONAL MEDICAL CENTER", DataGenerator.generate_npi())
                .with_wire_payment(Decimal("2250.00"), "INTL2024001")
                .with_primary_claim("INTL001", Decimal("1500.00"), Decimal("1275.00"), Decimal("225.00"))
                .with_primary_claim("INTL002", Decimal("1000.00"), Decimal("850.00"), Decimal("150.00"))
                .with_custom_segment("N4*VANCOUVER*BC*V6B2W2*CA~")  # International address
                .with_trace_number())
    
    @staticmethod
    def get_all_scenarios() -> Dict[str, EDI835Builder]:
        """Get all payment scenarios as a dictionary."""
        return {
            "ach_standard": PaymentScenarios.ach_payment_standard(),
            "check_large": PaymentScenarios.check_payment_large(),
            "wire_urgent": PaymentScenarios.wire_transfer_urgent(),
            "advice_only": PaymentScenarios.no_payment_advice_only(),
            "mixed_statuses": PaymentScenarios.mixed_claim_statuses(),
            "coordination_benefits": PaymentScenarios.coordination_of_benefits(),
            "overpayment_recovery": PaymentScenarios.overpayment_recovery(),
            "zero_payment": PaymentScenarios.zero_payment_adjustments_only(),
            "high_volume": PaymentScenarios.high_volume_batch(),
            "international": PaymentScenarios.international_provider()
        }