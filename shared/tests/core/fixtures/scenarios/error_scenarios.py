"""
Error and invalid data scenarios for testing EDI transaction validation and error handling.
"""

from decimal import Decimal
from typing import Dict, Any
from datetime import date

from ..builders.builder_835 import EDI835Builder
from ..builders.builder_837p import EDI837pBuilder
from ..builders.builder_270 import EDI270Builder
from ..builders.builder_276 import EDI276Builder
from ..base.generators import DataGenerator


class ErrorScenarios:
    """Collection of error and invalid data scenarios for testing."""
    
    @staticmethod
    def invalid_npi_transaction() -> EDI835Builder:
        """Transaction with invalid NPI format."""
        return (EDI835Builder()
                .with_payer("ERROR TEST INSURANCE", "INVALID123")
                .with_payee("TEST CLINIC", "BADNPI456")
                .with_ach_payment(Decimal("100.00"))
                .with_primary_claim("ERR001", Decimal("100.00"), Decimal("100.00"), Decimal("0"))
                .with_trace_number())
    
    @staticmethod
    def missing_required_segments() -> EDI835Builder:
        """Transaction missing required segments (minimal data)."""
        builder = EDI835Builder()
        # Intentionally minimal - missing payer, payee details
        builder.with_payment(Decimal("50.00"), "CHK", "C")
        builder.with_claim("MINIMAL001", 1, Decimal("50.00"), Decimal("50.00"), Decimal("0"))
        return builder
    
    @staticmethod
    def negative_payment_amounts() -> EDI835Builder:
        """Transaction with invalid negative payment amounts."""
        return (EDI835Builder()
                .with_realistic_payer("NEGATIVE TEST INSURANCE")
                .with_realistic_payee("REVERSAL CLINIC")
                .with_payment(Decimal("-100.00"), "ACH", "I")  # Invalid negative payment
                .with_claim("NEG001", 1, Decimal("100.00"), Decimal("-100.00"), Decimal("0"))  # Invalid negative paid
                .with_trace_number())
    
    @staticmethod
    def exceeding_field_lengths() -> EDI835Builder:
        """Transaction with field values exceeding maximum lengths."""
        long_name = "A" * 100  # Exceeds typical 60-character limit
        long_claim_id = "CLAIM" + "X" * 50  # Exceeds typical 20-character limit
        
        return (EDI835Builder()
                .with_payer(long_name, "123456789")
                .with_payee(long_name, DataGenerator.generate_npi())
                .with_ach_payment(Decimal("200.00"))
                .with_primary_claim(long_claim_id, Decimal("200.00"), Decimal("200.00"), Decimal("0"))
                .with_trace_number())
    
    @staticmethod
    def invalid_date_formats() -> EDI837pBuilder:
        """Claim with invalid date formats."""
        builder = (EDI837pBuilder()
                   .with_billing_provider("DATE ERROR CLINIC")
                   .with_payer("DATE TEST INSURANCE")
                   .with_subscriber("JANE", "DOE")
                   .with_claim(claim_id="DATE001", charge=Decimal("150.00"))
                   .with_diagnosis("Z00.00")
                   .with_office_visit())
        
        # Add invalid date manually
        builder.dates.append({
            "type": "service_date",
            "date": "INVALID"  # Invalid date format
        })
        
        return builder
    
    @staticmethod
    def duplicate_claim_numbers() -> EDI835Builder:
        """Transaction with duplicate claim numbers."""
        return (EDI835Builder()
                .with_realistic_payer("DUPLICATE TEST INSURANCE")
                .with_realistic_payee("DUPLICATE CLINIC")
                .with_ach_payment(Decimal("300.00"))
                .with_primary_claim("DUP001", Decimal("150.00"), Decimal("150.00"), Decimal("0"))
                .with_primary_claim("DUP001", Decimal("150.00"), Decimal("150.00"), Decimal("0"))  # Duplicate
                .with_trace_number())
    
    @staticmethod
    def invalid_adjustment_codes() -> EDI835Builder:
        """Transaction with invalid adjustment reason codes."""
        return (EDI835Builder()
                .with_realistic_payer("ADJUSTMENT ERROR INSURANCE")
                .with_realistic_payee("ADJUSTMENT TEST CLINIC")
                .with_ach_payment(Decimal("100.00"))
                .with_primary_claim("ADJ001", Decimal("200.00"), Decimal("100.00"), Decimal("100.00"))
                .with_adjustment("XX", "999", Decimal("100.00"))  # Invalid codes
                .with_trace_number())
    
    @staticmethod
    def mismatched_payment_totals() -> EDI835Builder:
        """Transaction where claim payments don't match total payment."""
        return (EDI835Builder()
                .with_realistic_payer("MISMATCH INSURANCE")
                .with_realistic_payee("CALCULATION CLINIC")
                .with_ach_payment(Decimal("500.00"))  # Total payment
                # Claims total to $600, which doesn't match payment total
                .with_primary_claim("CALC001", Decimal("300.00"), Decimal("300.00"), Decimal("0"))
                .with_primary_claim("CALC002", Decimal("300.00"), Decimal("300.00"), Decimal("0"))
                .with_trace_number())
    
    @staticmethod
    def empty_transaction() -> EDI835Builder:
        """Completely empty transaction."""
        return EDI835Builder()  # No data added
    
    @staticmethod
    def invalid_control_numbers() -> EDI270Builder:
        """Eligibility inquiry with invalid control numbers."""
        builder = (EDI270Builder()
                   .with_payer("CONTROL ERROR INSURANCE")
                   .with_provider("CONTROL TEST CLINIC")
                   .with_subscriber("JANE", "DOE")
                   .with_eligibility_inquiry())
        
        # Override with invalid control numbers
        builder.envelope.control_number = "INVALID"  # Should be numeric
        builder.envelope.group_control_number = ""   # Empty
        
        return builder
    
    @staticmethod
    def circular_claim_references() -> EDI835Builder:
        """Claims with circular references (A references B, B references A)."""
        return (EDI835Builder()
                .with_realistic_payer("CIRCULAR REF INSURANCE")
                .with_realistic_payee("REFERENCE ERROR CLINIC")
                .with_ach_payment(Decimal("0"))
                .with_reversal_claim("CIRC001", Decimal("100.00"), "CIRC002")
                .with_reversal_claim("CIRC002", Decimal("100.00"), "CIRC001")  # Circular reference
                .with_trace_number())
    
    @staticmethod
    def malformed_segments() -> EDI835Builder:
        """Transaction with manually added malformed segments."""
        builder = (EDI835Builder()
                   .with_realistic_payer("MALFORMED TEST INSURANCE")
                   .with_realistic_payee("SEGMENT ERROR CLINIC")
                   .with_ach_payment(Decimal("100.00"))
                   .with_primary_claim("MALFORM001", Decimal("100.00"), Decimal("100.00"), Decimal("0"))
                   .with_trace_number())
        
        # Add malformed segments
        builder.custom_segments.extend([
            "INVALID_SEGMENT_NO_ASTERISKS",    # Missing separators
            "TOO*MANY*ASTERISKS*IN*THIS*SEGMENT*FOR*STANDARD*FORMAT",  # Too many elements
            "",  # Empty segment
            "MISSING_TERMINATOR*DATA*HERE"     # Missing ~ terminator
        ])
        
        return builder
    
    @staticmethod
    def invalid_entity_types() -> EDI276Builder:
        """Claim inquiry with invalid entity type codes."""
        return (EDI276Builder()
                .with_payer("ENTITY ERROR INSURANCE", "123456789")
                .with_provider("ENTITY TEST CLINIC")
                .with_claim_inquiry("ENTITY001")
                .with_patient("JANE", "DOE")
                .with_trace_number())
    
    @staticmethod
    def out_of_range_amounts() -> EDI835Builder:
        """Transaction with amounts outside valid ranges."""
        return (EDI835Builder()
                .with_realistic_payer("RANGE ERROR INSURANCE")
                .with_realistic_payee("AMOUNT TEST CLINIC")
                .with_ach_payment(Decimal("999999999.99"))  # Extremely large amount
                .with_primary_claim("RANGE001", Decimal("0.001"), Decimal("0.001"), Decimal("0"))  # Too precise
                .with_trace_number())
    
    @staticmethod
    def invalid_service_codes() -> EDI837pBuilder:
        """Professional claim with invalid procedure codes."""
        return (EDI837pBuilder()
                .with_billing_provider("PROCEDURE ERROR CLINIC")
                .with_payer("SERVICE CODE INSURANCE")
                .with_subscriber("JANE", "DOE")
                .with_claim(claim_id="PROC001", charge=Decimal("200.00"))
                .with_diagnosis("INVALID")  # Invalid diagnosis code
                .with_service("99999", Decimal("200.00"), Decimal("200.00")))  # Invalid procedure code
    
    @staticmethod
    def missing_trace_numbers() -> EDI276Builder:
        """Transaction missing required trace numbers."""
        builder = EDI276Builder()
        builder.with_payer("NO TRACE INSURANCE")
        builder.with_provider("TRACE ERROR CLINIC")
        builder.with_claim_inquiry("NOTRACE001")
        # Intentionally not adding trace number
        return builder
    
    @staticmethod
    def get_all_scenarios() -> Dict[str, Any]:
        """Get all error scenarios as a dictionary."""
        return {
            "invalid_npi": ErrorScenarios.invalid_npi_transaction(),
            "missing_segments": ErrorScenarios.missing_required_segments(),
            "negative_amounts": ErrorScenarios.negative_payment_amounts(),
            "long_fields": ErrorScenarios.exceeding_field_lengths(),
            "invalid_dates": ErrorScenarios.invalid_date_formats(),
            "duplicate_claims": ErrorScenarios.duplicate_claim_numbers(),
            "invalid_adjustments": ErrorScenarios.invalid_adjustment_codes(),
            "mismatched_totals": ErrorScenarios.mismatched_payment_totals(),
            "empty_transaction": ErrorScenarios.empty_transaction(),
            "invalid_controls": ErrorScenarios.invalid_control_numbers(),
            "circular_references": ErrorScenarios.circular_claim_references(),
            "malformed_segments": ErrorScenarios.malformed_segments(),
            "invalid_entities": ErrorScenarios.invalid_entity_types(),
            "out_of_range": ErrorScenarios.out_of_range_amounts(),
            "invalid_codes": ErrorScenarios.invalid_service_codes(),
            "missing_trace": ErrorScenarios.missing_trace_numbers()
        }