"""
Legacy fixtures for backward compatibility.

This module provides the same API as the original fixtures.py but uses the new
builder system under the hood. This allows existing tests to continue working
while gradually migrating to the new fixture system.
"""

from decimal import Decimal
from typing import Dict, List

from .builders.builder_835 import EDI835Builder
from .builders.builder_270 import EDI270Builder
from .base.generators import DataGenerator


class EDIFixtures:
    """
    Container for common EDI test fixtures.
    
    This class maintains backward compatibility with the original EDIFixtures
    while using the new builder system internally.
    """
    
    @staticmethod
    def get_minimal_835() -> str:
        """Get minimal valid 835 EDI content."""
        builder = (EDI835Builder()
                  .with_envelope("SENDER", "RECEIVER", "HP", "005010X221A1")
                  .with_control_numbers("000012345", "000006789", "0001")
                  .with_payer("INSURANCE COMPANY")
                  .with_payee("PROVIDER NAME", "1234567890")
                  .with_ach_payment(Decimal("1000.00"))
                  .with_primary_claim("CLAIM001", Decimal("1200.00"), Decimal("1000.00"), Decimal("200.00"))
                  .with_trace_number("12345"))
        
        return builder.build()
    
    @staticmethod
    def get_835_with_multiple_claims() -> str:
        """Get 835 EDI with multiple claims."""
        builder = (EDI835Builder()
                  .with_envelope("SENDER", "RECEIVER", "HP", "005010X221A1")
                  .with_control_numbers("000012345", "000006789", "0001")
                  .with_payer("INSURANCE COMPANY")
                  .with_payee("PROVIDER NAME", "1234567890")
                  .with_ach_payment(Decimal("1500.00"))
                  .with_trace_number("12345"))
        
        # Add multiple claims with specific patient info and adjustments
        builder.with_primary_claim("CLAIM001", Decimal("500.00"), Decimal("400.00"), Decimal("100.00"))
        builder.with_custom_segment("NM1*QC*1*DOE*JANE*A***MI*987654321~")
        builder.with_adjustment("PR", "1", Decimal("50.00"))
        builder.with_adjustment("CO", "45", Decimal("50.00"))
        
        builder.with_primary_claim("CLAIM002", Decimal("700.00"), Decimal("600.00"), Decimal("100.00"))
        builder.with_custom_segment("NM1*QC*1*SMITH*JOHN*B***MI*123456789~")
        builder.with_adjustment("PR", "1", Decimal("75.00"))
        builder.with_adjustment("CO", "45", Decimal("25.00"))
        
        builder.with_denied_claim("CLAIM003", Decimal("300.00"), "29")
        builder.with_custom_segment("NM1*QC*1*BROWN*MARY*C***MI*555666777~")
        
        return builder.build()
    
    @staticmethod
    def get_835_denied_claim() -> str:
        """Get 835 EDI with denied claim."""
        builder = (EDI835Builder()
                  .with_envelope("SENDER", "RECEIVER", "HP", "005010X221A1")
                  .with_control_numbers("000012345", "000006789", "0001")
                  .with_payer("INSURANCE COMPANY")
                  .with_payee("PROVIDER NAME", "1234567890")
                  .with_no_payment()
                  .with_trace_number("ADVICE123"))
        
        builder.with_denied_claim("CLAIM001", Decimal("500.00"), "29")
        builder.with_custom_segment("NM1*QC*1*DOE*JANE*A***MI*987654321~")
        
        return builder.build()
    
    @staticmethod
    def get_270_eligibility_inquiry() -> str:
        """Get sample 270 eligibility inquiry."""
        builder = (EDI270Builder()
                  .with_envelope("SENDER", "RECEIVER", "HS", "005010X279A1")
                  .with_control_numbers("000012345", "000006789", "0001")
                  .with_payer("INSURANCE COMPANY", "123456789")
                  .with_provider("PROVIDER CLINIC", "1234567890")
                  .with_subscriber("JANE", "DOE", "987654321")
                  .with_eligibility_inquiry("30")
                  .with_trace_number("INQUIRY123"))
        
        return builder.build()
    
    @staticmethod
    def get_invalid_envelope() -> str:
        """Get EDI with invalid envelope structure."""
        # Create a builder and then manually corrupt the output
        builder = (EDI835Builder()
                  .with_envelope("SENDER", "RECEIVER", "HP", "005010X221A1")
                  .with_control_numbers("000012345", "000006789", "0001")
                  .with_ach_payment(Decimal("1000.00")))
        
        # Build normally then replace with corrupted version
        segments = [
            "ISA*00*          *00*          *ZZ*SENDER         *ZZ*RECEIVER       *241226*1430*^*00501*000012345*0*P*:~",
            "GS*HP*SENDER*RECEIVER*20241226*1430*000006789*X*005010X221A1~",
            "ST*835*0001~",
            "BPR*I*1000.00*C*ACH*CCP*01*123456789*DA*987654321*9876543210*20241226~",
            "SE*2*0002~",  # Mismatched control number (should be 0001)
            "GE*1*000006789~", 
            "IEA*1*000012345~"
        ]
        
        return "".join(segments)
    
    @staticmethod
    def get_sample_addresses() -> Dict[str, List[str]]:
        """Get sample address segments."""
        return {
            'payer_address': [
                "N3*123 INSURANCE BOULEVARD*SUITE 456~",
                "N4*INSURANCE CITY*CA*90210*US~"
            ],
            'payee_address': [
                "N3*789 MEDICAL CENTER DRIVE~",
                "N4*MEDICAL CITY*TX*75001~"
            ]
        }
    
    @staticmethod
    def get_sample_adjustments() -> Dict[str, str]:
        """Get sample adjustment segments."""
        return {
            'patient_responsibility': "CAS*PR*1*50.00~",
            'contractual_adjustment': "CAS*CO*45*50.00~", 
            'denial_adjustment': "CAS*CO*29*500.00~",
            'coinsurance': "CAS*PR*2*25.00~",
            'deductible': "CAS*PR*3*100.00~"
        }
    
    @staticmethod
    def get_sample_service_lines() -> List[str]:
        """Get sample service line segments."""
        return [
            "SVC*HC:99213*100.00*80.00*UN*1~",
            "DTM*472*20241215~",
            "CAS*CO*45*20.00~",
            "SVC*HC:99214*200.00*150.00*UN*1~",
            "DTM*472*20241215~",
            "CAS*PR*1*30.00~",
            "CAS*CO*45*20.00~"
        ]
    
    # Additional methods for enhanced backward compatibility
    
    @staticmethod
    def get_simple_ach_payment() -> str:
        """Get simple ACH payment 835."""
        return (EDI835Builder()
                .with_realistic_payer()
                .with_realistic_payee()
                .with_ach_payment(Decimal("1000.00"))
                .with_primary_claim(charge=Decimal("1200.00"), paid=Decimal("1000.00"), patient_resp=Decimal("200.00"))
                .with_trace_number()
                .build())
    
    @staticmethod
    def get_check_payment() -> str:
        """Get check payment 835."""
        return (EDI835Builder()
                .with_realistic_payer()
                .with_realistic_payee()
                .with_check_payment(Decimal("750.00"), "CHK123456")
                .with_primary_claim(charge=Decimal("900.00"), paid=Decimal("750.00"), patient_resp=Decimal("150.00"))
                .with_trace_number()
                .build())
    
    @staticmethod
    def get_coordination_of_benefits() -> str:
        """Get coordination of benefits 835."""
        return (EDI835Builder()
                .with_realistic_payer("SECONDARY HEALTH PLAN")
                .with_realistic_payee()
                .with_ach_payment(Decimal("300.00"))
                .with_secondary_claim(
                    "COB001",
                    Decimal("1000.00"),  # Total charge
                    Decimal("300.00"),   # Secondary payment
                    Decimal("100.00"),   # Patient responsibility  
                    Decimal("600.00")    # Primary already paid
                )
                .with_custom_segment("AMT*AU*600.00~")  # Prior payer amount
                .with_trace_number()
                .build())
    
    @staticmethod
    def get_high_volume_batch() -> str:
        """Get high volume batch payment."""
        builder = (EDI835Builder()
                  .with_realistic_payer("BATCH PROCESSING INSURANCE")
                  .with_realistic_payee("LARGE MEDICAL GROUP")
                  .with_ach_payment(Decimal("15000.00"))
                  .with_trace_number())
        
        # Add 10 claims
        for i in range(1, 11):
            charge = Decimal(str(200 + (i * 50)))
            paid = charge * Decimal("0.85")
            patient_resp = charge - paid
            builder.with_primary_claim(f"BATCH{i:03d}", charge, paid, patient_resp)
        
        return builder.build()
    
    @staticmethod
    def get_provider_adjustment() -> str:
        """Get 835 with provider-level adjustments (PLB)."""
        return (EDI835Builder()
                .with_realistic_payer()
                .with_realistic_payee()
                .with_ach_payment(Decimal("450.00"))
                .with_primary_claim(charge=Decimal("500.00"), paid=Decimal("450.00"), patient_resp=Decimal("50.00"))
                .with_custom_segment("PLB*1234567890*20241201*L6*-50.00~")  # Provider adjustment
                .with_trace_number()
                .build())
    
    @classmethod
    def get_all_fixtures(cls) -> Dict[str, str]:
        """Get all available fixtures as a dictionary."""
        return {
            "minimal_835": cls.get_minimal_835(),
            "multiple_claims": cls.get_835_with_multiple_claims(),
            "denied_claim": cls.get_835_denied_claim(),
            "eligibility_inquiry": cls.get_270_eligibility_inquiry(),
            "invalid_envelope": cls.get_invalid_envelope(),
            "simple_ach": cls.get_simple_ach_payment(),
            "check_payment": cls.get_check_payment(),
            "coordination_benefits": cls.get_coordination_of_benefits(),
            "high_volume": cls.get_high_volume_batch(),
            "provider_adjustment": cls.get_provider_adjustment()
        }