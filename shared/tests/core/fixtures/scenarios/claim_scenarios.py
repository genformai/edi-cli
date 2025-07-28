"""
Claim-related EDI scenarios for testing different claim processing outcomes.
"""

from decimal import Decimal
from typing import Dict, Any
from datetime import date

from ..builders.builder_835 import EDI835Builder
from ..builders.builder_837p import EDI837pBuilder
from ..builders.builder_276 import EDI276Builder
from ..base.data_types import ClaimStatus
from ..base.generators import DataGenerator, NameGenerator


class ClaimScenarios:
    """Collection of claim-related EDI scenarios."""
    
    @staticmethod
    def fully_paid_claim() -> EDI835Builder:
        """Claim paid in full without adjustments."""
        return (EDI835Builder()
                .with_realistic_payer("FULL PAYMENT INSURANCE")
                .with_realistic_payee("COMPLETE CARE CLINIC")
                .with_ach_payment(Decimal("250.00"))
                .with_primary_claim("FULL001", Decimal("250.00"), Decimal("250.00"), Decimal("0"))
                .with_trace_number())
    
    @staticmethod
    def partial_payment_claim() -> EDI835Builder:
        """Claim with partial payment and patient responsibility."""
        return (EDI835Builder()
                .with_realistic_payer("PARTIAL PAY HEALTH")
                .with_realistic_payee("GENERAL PRACTICE")
                .with_ach_payment(Decimal("180.00"))
                .with_primary_claim("PART001", Decimal("250.00"), Decimal("180.00"), Decimal("70.00"))
                .with_contractual_adjustment(amount=Decimal("70.00"))
                .with_trace_number())
    
    @staticmethod
    def denied_claim() -> EDI835Builder:
        """Completely denied claim with reason codes."""
        return (EDI835Builder()
                .with_realistic_payer("STRICT REVIEW INSURANCE")
                .with_realistic_payee("SPECIALTY CLINIC")
                .with_no_payment()
                .with_denied_claim("DENY001", Decimal("500.00"), "29")  # Not covered
                .with_adjustment("CO", "29", Decimal("500.00"))
                .with_trace_number())
    
    @staticmethod
    def claim_with_deductible() -> EDI835Builder:
        """Claim with patient deductible applied."""
        return (EDI835Builder()
                .with_realistic_payer("DEDUCTIBLE HEALTH PLAN")
                .with_realistic_payee("PRIMARY CARE ASSOCIATES")
                .with_ach_payment(Decimal("200.00"))
                .with_primary_claim("DEDUCT001", Decimal("300.00"), Decimal("200.00"), Decimal("100.00"))
                .with_adjustment("PR", "1", Decimal("100.00"))  # Deductible
                .with_trace_number())
    
    @staticmethod
    def claim_with_copay() -> EDI835Builder:
        """Claim with copayment applied."""
        return (EDI835Builder()
                .with_realistic_payer("COPAY MANAGED CARE")
                .with_realistic_payee("FAMILY HEALTH CENTER")
                .with_ach_payment(Decimal("175.00"))
                .with_primary_claim("COPAY001", Decimal("200.00"), Decimal("175.00"), Decimal("25.00"))
                .with_adjustment("PR", "2", Decimal("25.00"))  # Copayment
                .with_trace_number())
    
    @staticmethod
    def claim_with_coinsurance() -> EDI835Builder:
        """Claim with coinsurance (percentage-based patient responsibility)."""
        charge = Decimal("1000.00")
        coinsurance_amount = charge * Decimal("0.20")  # 20% coinsurance
        paid_amount = charge - coinsurance_amount
        
        return (EDI835Builder()
                .with_realistic_payer("COINSURANCE HEALTH")
                .with_realistic_payee("SURGICAL ASSOCIATES")
                .with_ach_payment(paid_amount)
                .with_primary_claim("COINS001", charge, paid_amount, coinsurance_amount)
                .with_adjustment("PR", "3", coinsurance_amount)  # Coinsurance
                .with_trace_number())
    
    @staticmethod
    def bundled_services_claim() -> EDI835Builder:
        """Claim with multiple bundled services."""
        builder = (EDI835Builder()
                   .with_realistic_payer("BUNDLED PAYMENT INSURANCE")
                   .with_realistic_payee("COMPREHENSIVE MEDICAL GROUP")
                   .with_ach_payment(Decimal("450.00"))
                   .with_trace_number())
        
        # Primary service - paid
        builder.with_primary_claim("BUNDLE001", Decimal("300.00"), Decimal("300.00"), Decimal("0"))
        
        # Secondary services - bundled/denied
        builder.with_claim("BUNDLE002", ClaimStatus.BUNDLED, Decimal("150.00"), Decimal("0"), Decimal("0"))
        builder.with_adjustment("CO", "97", Decimal("150.00"))  # Bundled
        
        builder.with_claim("BUNDLE003", ClaimStatus.BUNDLED, Decimal("200.00"), Decimal("150.00"), Decimal("50.00"))
        builder.with_adjustment("CO", "97", Decimal("50.00"))  # Partial bundle
        
        return builder
    
    @staticmethod
    def claim_with_prior_authorization() -> EDI835Builder:
        """Claim requiring prior authorization."""
        return (EDI835Builder()
                .with_realistic_payer("PRIOR AUTH REQUIRED HEALTH")
                .with_realistic_payee("SPECIALIZED TREATMENT CENTER")
                .with_ach_payment(Decimal("2500.00"))
                .with_primary_claim("AUTH001", Decimal("2500.00"), Decimal("2500.00"), Decimal("0"))
                .with_custom_segment("REF*G1*AUTH123456~")  # Prior authorization number
                .with_trace_number())
    
    @staticmethod
    def claim_exceeding_benefit_maximum() -> EDI835Builder:
        """Claim that exceeds annual benefit maximum."""
        return (EDI835Builder()
                .with_realistic_payer("LIMITED BENEFIT INSURANCE")
                .with_realistic_payee("EXTENDED CARE FACILITY")
                .with_ach_payment(Decimal("1000.00"))
                .with_primary_claim("MAXOUT001", Decimal("1500.00"), Decimal("1000.00"), Decimal("500.00"))
                .with_adjustment("PR", "119", Decimal("500.00"))  # Benefit maximum reached
                .with_trace_number())
    
    @staticmethod
    def corrected_claim() -> EDI835Builder:
        """Corrected/adjusted claim replacing a previous claim."""
        return (EDI835Builder()
                .with_realistic_payer("CORRECTION PROCESSING INSURANCE")
                .with_realistic_payee("ACCURACY MEDICAL GROUP")
                .with_ach_payment(Decimal("350.00"))
                .with_primary_claim("CORRECT001", Decimal("400.00"), Decimal("350.00"), Decimal("50.00"))
                .with_custom_segment("REF*F8*ORIGINAL001~")  # Original claim reference
                .with_custom_segment("CAS*CO*23*50.00~")  # Impact of prior payer adjudication
                .with_trace_number())
    
    @staticmethod
    def high_dollar_claim() -> EDI835Builder:
        """High-value claim requiring special handling."""
        return (EDI835Builder()
                .with_realistic_payer("HIGH VALUE INSURANCE")
                .with_realistic_payee("MAJOR MEDICAL CENTER")
                .with_ach_payment(Decimal("85000.00"))
                .with_primary_claim("MAJOR001", Decimal("100000.00"), Decimal("85000.00"), Decimal("15000.00"))
                .with_adjustment("PR", "1", Decimal("5000.00"))   # Deductible
                .with_adjustment("PR", "3", Decimal("10000.00"))  # Coinsurance  
                .with_custom_segment("REF*D9*CASE2024001~")       # Case number
                .with_trace_number())
    
    @staticmethod
    def professional_claim_submission() -> EDI837pBuilder:
        """Standard professional healthcare claim for submission."""
        return (EDI837pBuilder()
                .with_billing_provider("PROFESSIONAL MEDICAL GROUP")
                .with_rendering_provider("JOHN", "SMITH")
                .with_payer("STANDARD HEALTH INSURANCE")
                .with_subscriber("JANE", "PATIENT")
                .with_claim(claim_id="PROF001", charge=Decimal("275.00"))
                .with_diagnosis("I10")  # Hypertension
                .with_office_visit("99214", Decimal("200.00"))
                .with_lab_service("85025", Decimal("75.00")))
    
    @staticmethod
    def emergency_claim_submission() -> EDI837pBuilder:
        """Emergency department claim submission."""
        return (EDI837pBuilder.emergency_visit()
                .with_diagnosis("R50.9")  # Fever
                .with_diagnosis("J44.1")  # COPD exacerbation
                .with_service("99283", Decimal("650.00"), Decimal("650.00"))  # ER visit level 3
                .with_service("71045", Decimal("200.00"), Decimal("200.00")))  # Chest X-ray
    
    @staticmethod
    def claim_status_inquiry() -> EDI276Builder:
        """Standard claim status inquiry."""
        return (EDI276Builder()
                .with_payer("INQUIRY HEALTH INSURANCE")
                .with_provider("FOLLOWUP MEDICAL CLINIC")
                .with_claim_inquiry("STATUS001", total_charge=Decimal("450.00"))
                .with_patient("JOHN", "INQUIRY")
                .with_trace_number())
    
    @staticmethod
    def batch_claim_inquiry() -> EDI276Builder:
        """Batch inquiry for multiple claims."""
        return EDI276Builder.batch_inquiry(claim_count=8)
    
    @staticmethod
    def get_all_scenarios() -> Dict[str, Any]:
        """Get all claim scenarios as a dictionary."""
        return {
            "fully_paid": ClaimScenarios.fully_paid_claim(),
            "partial_payment": ClaimScenarios.partial_payment_claim(),
            "denied": ClaimScenarios.denied_claim(),
            "with_deductible": ClaimScenarios.claim_with_deductible(),
            "with_copay": ClaimScenarios.claim_with_copay(),
            "with_coinsurance": ClaimScenarios.claim_with_coinsurance(),
            "bundled_services": ClaimScenarios.bundled_services_claim(),
            "prior_authorization": ClaimScenarios.claim_with_prior_authorization(),
            "benefit_maximum": ClaimScenarios.claim_exceeding_benefit_maximum(),
            "corrected": ClaimScenarios.corrected_claim(),
            "high_dollar": ClaimScenarios.high_dollar_claim(),
            "professional_submission": ClaimScenarios.professional_claim_submission(),
            "emergency_submission": ClaimScenarios.emergency_claim_submission(),
            "status_inquiry": ClaimScenarios.claim_status_inquiry(),
            "batch_inquiry": ClaimScenarios.batch_claim_inquiry()
        }