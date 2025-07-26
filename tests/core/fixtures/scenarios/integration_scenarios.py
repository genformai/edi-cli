"""
Integration scenarios for testing complex multi-transaction workflows and real-world EDI scenarios.
"""

from decimal import Decimal
from typing import Dict, Any, List, Tuple
from datetime import date, timedelta

from ..builders.builder_835 import EDI835Builder
from ..builders.builder_837p import EDI837pBuilder
from ..builders.builder_270 import EDI270Builder
from ..builders.builder_276 import EDI276Builder
from ..base.generators import DataGenerator, NameGenerator, AddressGenerator
from ..base.data_types import Address, ClaimStatus


class IntegrationScenarios:
    """Collection of complex integration scenarios for end-to-end testing."""
    
    @staticmethod
    def complete_patient_workflow() -> Dict[str, Any]:
        """Complete workflow: eligibility → claim submission → status inquiry → payment."""
        patient_first, patient_middle, patient_last = NameGenerator.generate_person_name()
        member_id = DataGenerator.generate_control_number(9)
        claim_id = DataGenerator.generate_claim_id()
        
        # Step 1: Eligibility inquiry
        eligibility = (EDI270Builder()
                      .with_payer("WORKFLOW INSURANCE", "WF123456789")
                      .with_provider("WORKFLOW MEDICAL CLINIC")
                      .with_subscriber(patient_first, patient_last, member_id)
                      .with_eligibility_inquiry("30")  # Health benefit plan
                      .with_eligibility_inquiry("98")  # Professional physician
                      .with_trace_number())
        
        # Step 2: Professional claim submission
        claim_submission = (EDI837pBuilder()
                           .with_billing_provider("WORKFLOW MEDICAL CLINIC")
                           .with_rendering_provider("WORKFLOW", "PHYSICIAN")
                           .with_payer("WORKFLOW INSURANCE")
                           .with_subscriber(patient_first, patient_last, member_id)
                           .with_claim(claim_id=claim_id, charge=Decimal("450.00"))
                           .with_diagnosis("I10")    # Hypertension
                           .with_diagnosis("E11.9")  # Diabetes
                           .with_office_visit("99214", Decimal("250.00"))
                           .with_lab_service("85025", Decimal("75.00"))
                           .with_service("80053", Decimal("125.00"), Decimal("125.00")))  # Comprehensive panel
        
        # Step 3: Claim status inquiry
        status_inquiry = (EDI276Builder()
                         .with_payer("WORKFLOW INSURANCE")
                         .with_provider("WORKFLOW MEDICAL CLINIC")
                         .with_claim_inquiry(claim_id, total_charge=Decimal("450.00"))
                         .with_patient(patient_first, patient_last, member_id)
                         .with_trace_number())
        
        # Step 4: Payment (835)
        payment = (EDI835Builder()
                  .with_payer("WORKFLOW INSURANCE", "WF123456789")
                  .with_payee("WORKFLOW MEDICAL CLINIC", DataGenerator.generate_npi())
                  .with_ach_payment(Decimal("382.50"))
                  .with_primary_claim(claim_id, Decimal("450.00"), Decimal("382.50"), Decimal("67.50"))
                  .with_adjustment("PR", "1", Decimal("50.00"))  # Deductible
                  .with_adjustment("PR", "2", Decimal("17.50"))  # Copayment
                  .with_trace_number())
        
        return {
            "eligibility_inquiry": eligibility,
            "claim_submission": claim_submission,
            "status_inquiry": status_inquiry,
            "payment_advice": payment
        }
    
    @staticmethod
    def multi_payer_coordination() -> Dict[str, Any]:
        """Coordination of benefits between primary and secondary payers."""
        patient_first, patient_middle, patient_last = NameGenerator.generate_person_name()
        claim_id = DataGenerator.generate_claim_id()
        total_charge = Decimal("1200.00")
        
        # Primary payer payment (70% coverage)
        primary_payment = total_charge * Decimal("0.70")
        primary_835 = (EDI835Builder()
                      .with_payer("PRIMARY HEALTH INSURANCE", "PRI123456789")
                      .with_payee("COORDINATION MEDICAL CENTER")
                      .with_ach_payment(primary_payment)
                      .with_primary_claim(claim_id, total_charge, primary_payment, Decimal("0"))
                      .with_custom_segment("MOA*MA*8~")  # Remark: COB
                      .with_trace_number())
        
        # Secondary payer payment (covers remaining after primary)
        remaining_after_primary = total_charge - primary_payment  # $360
        secondary_coverage = remaining_after_primary * Decimal("0.80")  # 80% of remaining
        patient_responsibility = remaining_after_primary - secondary_coverage
        
        secondary_835 = (EDI835Builder()
                        .with_payer("SECONDARY HEALTH INSURANCE", "SEC123456789")
                        .with_payee("COORDINATION MEDICAL CENTER")
                        .with_ach_payment(secondary_coverage)
                        .with_secondary_claim(
                            claim_id,
                            total_charge,
                            secondary_coverage,
                            patient_responsibility,
                            primary_payment  # Prior payer amount
                        )
                        .with_custom_segment("AMT*AU*840.00~")  # Prior payer paid
                        .with_adjustment("PR", "3", patient_responsibility)  # Patient coinsurance
                        .with_trace_number())
        
        return {
            "primary_payment": primary_835,
            "secondary_payment": secondary_835,
            "total_charge": total_charge,
            "primary_paid": primary_payment,
            "secondary_paid": secondary_coverage,
            "patient_owes": patient_responsibility
        }
    
    @staticmethod
    def claim_correction_workflow() -> Dict[str, Any]:
        """Original claim, denial, corrected resubmission, and final payment."""
        claim_id = DataGenerator.generate_claim_id()
        corrected_claim_id = f"{claim_id}C"
        
        # Step 1: Original claim submission (will be denied)
        original_claim = (EDI837pBuilder()
                         .with_billing_provider("CORRECTION MEDICAL GROUP")
                         .with_rendering_provider("CORRECTION", "PHYSICIAN")
                         .with_payer("CORRECTION INSURANCE")
                         .with_subscriber("CORRECTION", "PATIENT")
                         .with_claim(claim_id=claim_id, charge=Decimal("800.00"))
                         .with_diagnosis("Z99.99")  # Intentionally incorrect code
                         .with_office_visit("99215", Decimal("350.00"))
                         .with_service("73060", Decimal("450.00"), Decimal("450.00")))  # Knee X-ray
        
        # Step 2: Denial (835)
        denial = (EDI835Builder()
                 .with_payer("CORRECTION INSURANCE")
                 .with_payee("CORRECTION MEDICAL GROUP")
                 .with_no_payment()
                 .with_denied_claim(claim_id, Decimal("800.00"), "11")  # Diagnosis inconsistent
                 .with_adjustment("CO", "11", Decimal("800.00"))
                 .with_trace_number())
        
        # Step 3: Corrected claim resubmission
        corrected_claim = (EDI837pBuilder()
                          .with_billing_provider("CORRECTION MEDICAL GROUP")
                          .with_rendering_provider("CORRECTION", "PHYSICIAN")
                          .with_payer("CORRECTION INSURANCE")
                          .with_subscriber("CORRECTION", "PATIENT")
                          .with_claim(claim_id=corrected_claim_id, charge=Decimal("800.00"))
                          .with_diagnosis("M25.562")  # Correct diagnosis: Knee pain
                          .with_office_visit("99215", Decimal("350.00"))
                          .with_service("73060", Decimal("450.00"), Decimal("450.00"))
                          .with_custom_segment(f"REF*F8*{claim_id}~"))  # Reference original claim
        
        # Step 4: Payment for corrected claim
        corrected_payment = (EDI835Builder()
                           .with_payer("CORRECTION INSURANCE")
                           .with_payee("CORRECTION MEDICAL GROUP")
                           .with_ach_payment(Decimal("720.00"))
                           .with_primary_claim(corrected_claim_id, Decimal("800.00"), Decimal("720.00"), Decimal("80.00"))
                           .with_adjustment("CO", "45", Decimal("80.00"))  # Contractual adjustment
                           .with_trace_number())
        
        return {
            "original_submission": original_claim,
            "denial": denial,
            "corrected_submission": corrected_claim,
            "final_payment": corrected_payment
        }
    
    @staticmethod
    def high_volume_batch_processing() -> Dict[str, Any]:
        """Large batch processing scenario with multiple claims and payments."""
        batch_date = date.today().strftime("%Y%m%d")
        
        # Large batch payment covering 25 claims
        batch_builder = (EDI835Builder()
                        .with_payer("BATCH PROCESSING INSURANCE", "BATCH123456")
                        .with_payee("HIGH VOLUME MEDICAL GROUP", DataGenerator.generate_npi())
                        .with_ach_payment(Decimal("12750.00"))
                        .with_trace_number(f"BATCH{batch_date}"))
        
        # Add 25 claims with varying amounts and statuses
        total_paid = Decimal("0")
        for i in range(1, 26):
            claim_id = f"BATCH{i:03d}{batch_date}"
            
            if i <= 20:  # 20 paid claims
                charge = Decimal(str(200 + (i * 25)))  # $225, $250, $275, etc.
                paid = charge * Decimal("0.85")        # 85% payment rate
                patient_resp = charge - paid
                batch_builder.with_primary_claim(claim_id, charge, paid, patient_resp)
                total_paid += paid
                
            elif i <= 23:  # 3 denied claims
                charge = Decimal(str(300 + (i * 10)))
                batch_builder.with_denied_claim(claim_id, charge, "29")  # Not covered
                
            else:  # 2 pending claims (partial processing)
                charge = Decimal(str(400 + (i * 5)))
                batch_builder.with_claim(claim_id, ClaimStatus.PENDING, charge, Decimal("0"), Decimal("0"))
        
        # Multiple smaller payments from same payer (daily processing)
        daily_payments = []
        for day_offset in range(1, 4):  # 3 days of payments
            payment_date = (date.today() - timedelta(days=day_offset)).strftime("%Y%m%d")
            daily_payment = (EDI835Builder()
                           .with_payer("BATCH PROCESSING INSURANCE", "BATCH123456")
                           .with_payee("DAILY PROCESSING CLINIC")
                           .with_ach_payment(Decimal(str(1500 + (day_offset * 200))))
                           .with_multiple_claims(5)  # 5 claims per day
                           .with_trace_number(f"DAILY{payment_date}"))
            daily_payments.append(daily_payment)
        
        return {
            "large_batch": batch_builder,
            "daily_payments": daily_payments,
            "total_claims": 25,
            "paid_claims": 20,
            "denied_claims": 3,
            "pending_claims": 2
        }
    
    @staticmethod
    def specialty_provider_network() -> Dict[str, Any]:
        """Complex scenario involving multiple specialty providers."""
        patient_first, patient_middle, patient_last = NameGenerator.generate_person_name()
        member_id = DataGenerator.generate_control_number(9)
        
        # Primary care referral
        primary_care = (EDI837pBuilder()
                       .with_billing_provider("PRIMARY CARE ASSOCIATES")
                       .with_rendering_provider("PRIMARY", "PHYSICIAN")
                       .with_payer("NETWORK HEALTH INSURANCE")
                       .with_subscriber(patient_first, patient_last, member_id)
                       .with_claim(claim_id="PCP001", charge=Decimal("200.00"))
                       .with_diagnosis("R06.00")  # Shortness of breath
                       .with_office_visit("99214", Decimal("200.00")))
        
        # Cardiology consultation
        cardiology = (EDI837pBuilder()
                     .with_billing_provider("HEART SPECIALISTS")
                     .with_rendering_provider("CARDIAC", "SPECIALIST")
                     .with_payer("NETWORK HEALTH INSURANCE")
                     .with_subscriber(patient_first, patient_last, member_id)
                     .with_claim(claim_id="CARD001", charge=Decimal("850.00"))
                     .with_diagnosis("I25.10")  # Coronary artery disease
                     .with_office_visit("99243", Decimal("350.00"))  # Consultation
                     .with_service("93000", Decimal("150.00"), Decimal("150.00"))  # EKG
                     .with_service("93307", Decimal("350.00"), Decimal("350.00")))  # Echocardiogram
        
        # Diagnostic imaging (separate facility)
        imaging = (EDI837pBuilder()
                  .with_billing_provider("ADVANCED IMAGING CENTER")
                  .with_rendering_provider("RADIOLOGY", "SPECIALIST")
                  .with_payer("NETWORK HEALTH INSURANCE")
                  .with_subscriber(patient_first, patient_last, member_id)
                  .with_place_of_service("22")  # Outpatient hospital
                  .with_claim(claim_id="RAD001", charge=Decimal("1200.00"))
                  .with_diagnosis("I25.10")  # Same as cardiology
                  .with_service("75574", Decimal("1200.00"), Decimal("1200.00")))  # Cardiac CT
        
        # Combined payment covering all providers
        network_payment = (EDI835Builder()
                          .with_payer("NETWORK HEALTH INSURANCE", "NET123456789")
                          .with_payee("NETWORK PAYMENT PROCESSOR")  # Clearinghouse
                          .with_ach_payment(Decimal("1912.50"))
                          .with_primary_claim("PCP001", Decimal("200.00"), Decimal("170.00"), Decimal("30.00"))
                          .with_primary_claim("CARD001", Decimal("850.00"), Decimal("722.50"), Decimal("127.50"))
                          .with_primary_claim("RAD001", Decimal("1200.00"), Decimal("1020.00"), Decimal("180.00"))
                          .with_contractual_adjustment(amount=Decimal("337.50"))  # Total adjustments
                          .with_trace_number())
        
        return {
            "primary_care_claim": primary_care,
            "cardiology_claim": cardiology,
            "imaging_claim": imaging,
            "network_payment": network_payment,
            "total_charges": Decimal("2250.00"),
            "total_paid": Decimal("1912.50"),
            "patient_responsibility": Decimal("337.50")
        }
    
    @staticmethod
    def medicare_advantage_scenario() -> Dict[str, Any]:
        """Medicare Advantage plan with specific billing requirements."""
        # Medicare Advantage eligibility check
        eligibility = (EDI270Builder()
                      .with_payer("MEDICARE ADVANTAGE PLAN", "MA123456789")
                      .with_provider("SENIOR CARE CLINIC")
                      .with_subscriber("MEDICARE", "BENEFICIARY", "1234567890A")
                      .with_eligibility_inquiry("30")  # Health benefit
                      .with_eligibility_inquiry("1")   # Medical care
                      .with_trace_number())
        
        # Professional claim with Medicare-specific requirements
        claim = (EDI837pBuilder()
                .with_billing_provider("SENIOR CARE CLINIC")
                .with_rendering_provider("GERIATRIC", "SPECIALIST")
                .with_payer("MEDICARE ADVANTAGE PLAN")
                .with_subscriber("MEDICARE", "BENEFICIARY", "1234567890A")
                .with_claim(claim_id="MA001", charge=Decimal("450.00"))
                .with_diagnosis("I10")      # Hypertension
                .with_diagnosis("E11.9")    # Diabetes
                .with_diagnosis("M79.3")    # Arthritis
                .with_office_visit("99214", Decimal("200.00"))
                .with_service("36415", Decimal("25.00"), Decimal("25.00"))   # Blood draw
                .with_service("85025", Decimal("75.00"), Decimal("75.00"))   # CBC
                .with_service("80053", Decimal("150.00"), Decimal("150.00"))) # Comprehensive panel
        
        # Medicare payment with specific adjustments
        payment = (EDI835Builder()
                  .with_payer("MEDICARE ADVANTAGE PLAN", "MA123456789")
                  .with_payee("SENIOR CARE CLINIC")
                  .with_ach_payment(Decimal("360.00"))
                  .with_primary_claim("MA001", Decimal("450.00"), Decimal("360.00"), Decimal("90.00"))
                  .with_adjustment("CO", "45", Decimal("90.00"))  # Contractual
                  .with_custom_segment("MOA*MA*8~")  # Medicare remark codes
                  .with_trace_number())
        
        return {
            "eligibility_check": eligibility,
            "medicare_claim": claim,
            "medicare_payment": payment
        }
    
    @staticmethod
    def get_all_scenarios() -> Dict[str, Dict[str, Any]]:
        """Get all integration scenarios as a dictionary."""
        return {
            "complete_workflow": IntegrationScenarios.complete_patient_workflow(),
            "multi_payer_coordination": IntegrationScenarios.multi_payer_coordination(),
            "claim_correction": IntegrationScenarios.claim_correction_workflow(),
            "batch_processing": IntegrationScenarios.high_volume_batch_processing(),
            "specialty_network": IntegrationScenarios.specialty_provider_network(),
            "medicare_advantage": IntegrationScenarios.medicare_advantage_scenario()
        }