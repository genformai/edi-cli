"""
Enhanced test cases for EDI 835 Payment/Reassociation using new fixture system.

This file demonstrates how to migrate from the old fixture system to the new
enhanced fixtures with realistic data and scenario-based testing.

Compare with test_835_payment.py to see the migration differences.
"""

import pytest
from decimal import Decimal

# New fixture system imports
from .fixtures import (
    EDI835Builder, PaymentScenarios, ClaimScenarios, ErrorScenarios,
    data_loader
)

# Test utilities (unchanged)
from .test_utils import parse_edi, assert_date_format, assert_amount_format


class Test835PaymentEnhanced:
    """Enhanced test cases using new fixture system."""

    def test_835_pmt_001_ach_payment_realistic(self, schema_835_path):
        """
        835-PMT-001: ACH payment with realistic data.
        
        Enhancement: Uses realistic payer names, NPIs, and addresses.
        """
        # Use pre-built scenario for standard ACH payment
        edi_content = PaymentScenarios.ach_payment_standard().build()
        
        result = parse_edi(edi_content, schema_835_path)
        
        # Verify structure (same assertions as before)
        transaction = result.interchanges[0].functional_groups[0].transactions[0]
        financial_tx = transaction.financial_transaction
        
        # Verify ACH payment details
        assert financial_tx.financial_information.total_paid > 0
        assert financial_tx.financial_information.payment_method == "ACH"
        assert_date_format(financial_tx.financial_information.payment_date)
        
        # Verify TRN (trace number) exists
        assert len(financial_tx.reference_numbers) > 0
        trace_refs = [ref for ref in financial_tx.reference_numbers if ref["type"] == "trace_number"]
        assert len(trace_refs) > 0

    def test_835_pmt_001_ach_payment_custom(self, schema_835_path):
        """
        Same test but built with custom builder for specific test requirements.
        """
        # Build custom ACH payment with specific values for test
        edi_content = (EDI835Builder()
                      .with_realistic_payer()
                      .with_realistic_payee()
                      .with_ach_payment(Decimal("1500.75"))
                      .with_primary_claim("CLAIM001", Decimal("200.00"), Decimal("150.75"), Decimal("49.25"))
                      .with_primary_claim("CLAIM002", Decimal("300.00"), Decimal("250.00"), Decimal("50.00"))
                      .with_primary_claim("CLAIM003", Decimal("1500.00"), Decimal("1100.00"), Decimal("400.00"))
                      .with_trace_number("EFT123456789")
                      .build())
        
        result = parse_edi(edi_content, schema_835_path)
        
        # Same verification logic
        transaction = result.interchanges[0].functional_groups[0].transactions[0]
        financial_tx = transaction.financial_transaction
        
        # Verify specific test values
        assert financial_tx.financial_information.total_paid == 1500.75
        assert financial_tx.financial_information.payment_method == "ACH"
        
        # Verify specific trace number
        trace_refs = [ref for ref in financial_tx.reference_numbers if ref["type"] == "trace_number"]
        assert len(trace_refs) > 0
        assert trace_refs[0]["value"] == "EFT123456789"

    def test_835_pmt_002_check_payment_scenario(self, schema_835_path):
        """
        835-PMT-002: Check payment using scenario.
        
        Enhancement: Uses realistic check payment scenario.
        """
        # Use pre-built check payment scenario
        edi_content = PaymentScenarios.check_payment_large().build()
        
        result = parse_edi(edi_content, schema_835_path)
        
        # Verify structure
        transaction = result.interchanges[0].functional_groups[0].transactions[0]
        financial_tx = transaction.financial_transaction
        
        # Verify check payment details
        assert financial_tx.financial_information.total_paid > 0
        assert financial_tx.financial_information.payment_method == "CHK"
        
        # Verify check number in trace
        trace_refs = [ref for ref in financial_tx.reference_numbers if ref["type"] == "trace_number"]
        assert len(trace_refs) > 0
        # Check number should be present
        assert any("CHK" in ref["value"] for ref in trace_refs)

    def test_835_pmt_003_no_payment_scenario(self, schema_835_path):
        """
        835-PMT-003: No payment using denial scenario.
        
        Enhancement: Uses realistic denial scenario with proper reason codes.
        """
        # Use pre-built denial scenario  
        edi_content = ClaimScenarios.denied_claim().build()
        
        result = parse_edi(edi_content, schema_835_path)
        
        # Verify structure
        transaction = result.interchanges[0].functional_groups[0].transactions[0]
        financial_tx = transaction.financial_transaction
        
        # Verify no payment
        assert financial_tx.financial_information.total_paid == 0.00
        assert financial_tx.financial_information.payment_method == "NON"
        
        # Verify claims exist with zero payment
        assert len(financial_tx.claims) >= 1
        for claim in financial_tx.claims:
            assert claim.total_paid == 0.00

    def test_835_pmt_004_negative_plb_realistic(self, schema_835_path):
        """
        835-PMT-004: Overpayment recovery with realistic scenario.
        
        Enhancement: Uses dedicated overpayment recovery scenario.
        """
        edi_content = PaymentScenarios.overpayment_recovery().build()
        
        result = parse_edi(edi_content, schema_835_path)
        
        # Verify structure
        transaction = result.interchanges[0].functional_groups[0].transactions[0]
        financial_tx = transaction.financial_transaction
        
        # Verify net payment exists (should be positive after recovery)
        assert financial_tx.financial_information.total_paid > 0
        
        # Note: PLB segments create complex balance calculations
        # The scenario handles this automatically with realistic amounts

    def test_835_pmt_005_wire_transfer_scenario(self, schema_835_path):
        """
        Test wire transfer using dedicated scenario.
        
        Enhancement: Uses realistic wire transfer scenario.
        """
        edi_content = PaymentScenarios.wire_transfer_urgent().build()
        
        result = parse_edi(edi_content, schema_835_path)
        
        # Verify structure
        transaction = result.interchanges[0].functional_groups[0].transactions[0]
        financial_tx = transaction.financial_transaction
        
        # Verify wire transfer details
        assert financial_tx.financial_information.total_paid > 0
        assert financial_tx.financial_information.payment_method == "FWT"
        
        # Verify wire reference number
        trace_refs = [ref for ref in financial_tx.reference_numbers if ref["type"] == "trace_number"]
        assert len(trace_refs) > 0
        assert any("WIRE" in ref["value"] for ref in trace_refs)

    def test_835_pmt_006_high_volume_batch(self, schema_835_path):
        """
        Test high-volume batch payment.
        
        Enhancement: Uses realistic batch scenario with multiple claims.
        """
        edi_content = PaymentScenarios.high_volume_batch().build()
        
        result = parse_edi(edi_content, schema_835_path)
        
        # Verify structure
        transaction = result.interchanges[0].functional_groups[0].transactions[0]
        financial_tx = transaction.financial_transaction
        
        # Verify batch characteristics
        assert financial_tx.financial_information.total_paid > 10000  # Large payment
        assert len(financial_tx.claims) >= 10  # Multiple claims
        
        # Verify batch trace number pattern
        trace_refs = [ref for ref in financial_tx.reference_numbers if ref["type"] == "trace_number"]
        assert len(trace_refs) > 0
        assert any("BATCH" in ref["value"] for ref in trace_refs)

    def test_835_pmt_007_coordination_of_benefits(self, schema_835_path):
        """
        Test coordination of benefits scenario.
        
        Enhancement: Uses realistic COB scenario with proper amounts.
        """
        edi_content = PaymentScenarios.coordination_of_benefits().build()
        
        result = parse_edi(edi_content, schema_835_path)
        
        # Verify structure
        transaction = result.interchanges[0].functional_groups[0].transactions[0]
        financial_tx = transaction.financial_transaction
        
        # Verify secondary payer characteristics
        assert financial_tx.financial_information.total_paid > 0
        
        # COB scenarios typically have lower payment amounts (secondary coverage)
        # and include prior payer information

    # Test with specific payer types

    def test_835_pmt_008_medicare_payment(self, schema_835_path):
        """
        Test Medicare payment with government payer.
        
        Enhancement: Uses realistic government payer data.
        """
        # Get realistic Medicare payer
        medicare_payer = data_loader.get_random_payer(payer_type="government")
        
        edi_content = (EDI835Builder()
                      .with_payer(medicare_payer['name'], medicare_payer['id'])
                      .with_realistic_payee()
                      .with_ach_payment(Decimal("850.00"))
                      .with_primary_claim(charge=Decimal("1000.00"), paid=Decimal("850.00"), patient_resp=Decimal("150.00"))
                      .with_adjustment("CO", "45", Decimal("150.00"))  # Medicare adjustment
                      .build())
        
        result = parse_edi(edi_content, schema_835_path)
        
        # Verify structure
        transaction = result.interchanges[0].functional_groups[0].transactions[0] 
        financial_tx = transaction.financial_transaction
        
        # Verify payment details
        assert financial_tx.financial_information.total_paid == 850.00
        
        # Payer should be government type (Medicare/Medicaid)
        assert any(name in medicare_payer['name'].upper() for name in ['MEDICARE', 'MEDICAID'])

    def test_835_pmt_009_commercial_insurance_payment(self, schema_835_path):
        """
        Test commercial insurance payment with realistic payer.
        
        Enhancement: Uses specific commercial payer characteristics.
        """
        # Get realistic commercial payer
        commercial_payer = data_loader.get_random_payer(payer_type="insurance")
        
        edi_content = (EDI835Builder()
                      .with_payer(commercial_payer['name'], commercial_payer['id'])
                      .with_realistic_payee()
                      .with_ach_payment(Decimal("1200.00"))
                      .with_primary_claim(charge=Decimal("1500.00"), paid=Decimal("1200.00"), patient_resp=Decimal("300.00"))
                      .with_adjustment("PR", "1", Decimal("200.00"))  # Deductible
                      .with_adjustment("PR", "2", Decimal("100.00"))  # Copay
                      .build())
        
        result = parse_edi(edi_content, schema_835_path)
        
        # Verify structure
        transaction = result.interchanges[0].functional_groups[0].transactions[0]
        financial_tx = transaction.financial_transaction
        
        # Verify payment details
        assert financial_tx.financial_information.total_paid == 1200.00
        
        # Should be commercial insurance name
        assert commercial_payer['name'] in ['AETNA BETTER HEALTH', 'ANTHEM BLUE CROSS', 'CIGNA HEALTHCARE', 'HUMANA INC', 'UNITEDHEALTH GROUP'] or 'BLUE CROSS' in commercial_payer['name']

    # Error condition tests

    def test_835_pmt_010_invalid_payment_data(self, schema_835_path):
        """
        Test invalid payment data handling.
        
        Enhancement: Uses dedicated error scenarios.
        """
        # Test negative amounts
        edi_content = ErrorScenarios.negative_payment_amounts().build()
        
        # Depending on parser behavior, this might parse or throw error
        try:
            result = parse_edi(edi_content, schema_835_path)
            # If it parses, verify it's marked as invalid somehow
        except Exception:
            # Expected for invalid data
            pass

    def test_835_pmt_011_missing_required_segments(self, schema_835_path):
        """
        Test missing required segments.
        
        Enhancement: Uses error scenario for missing data.
        """
        edi_content = ErrorScenarios.missing_required_segments().build()
        
        # Should either fail to parse or produce warnings
        try:
            result = parse_edi(edi_content, schema_835_path)
            # If parsed, verify limitations
        except Exception:
            # Expected for incomplete data
            pass

    # Fixture-based test examples

    @pytest.fixture
    def cardiology_payment_scenario(self):
        """Custom fixture for cardiology payments."""
        return (EDI835Builder()
               .with_realistic_payer()
               .with_provider("HEART SPECIALISTS", specialty="207RC0000X")
               .with_ach_payment(Decimal("1500.00"))
               .with_primary_claim(charge=Decimal("1800.00"), paid=Decimal("1500.00"), patient_resp=Decimal("300.00"))
               .with_diagnosis("I25.10")  # Coronary artery disease
               .with_service("93307", Decimal("800.00"))  # Echocardiogram
               .with_service("99243", Decimal("300.00")))  # Consultation

    def test_835_pmt_012_specialty_payment(self, schema_835_path, cardiology_payment_scenario):
        """
        Test specialty provider payment using custom fixture.
        
        Enhancement: Domain-specific test fixture.
        """
        edi_content = cardiology_payment_scenario.build()
        
        result = parse_edi(edi_content, schema_835_path)
        
        # Verify structure
        transaction = result.interchanges[0].functional_groups[0].transactions[0]
        financial_tx = transaction.financial_transaction
        
        # Verify specialty payment details
        assert financial_tx.financial_information.total_paid == 1500.00
        assert len(financial_tx.claims) >= 1

    # Performance and stress tests

    def test_835_pmt_013_large_payment_volume(self, schema_835_path):
        """
        Test processing large payment volumes.
        
        Enhancement: Realistic large-scale scenario.
        """
        # Use high-volume scenario
        edi_content = PaymentScenarios.high_volume_batch().build()
        
        result = parse_edi(edi_content, schema_835_path)
        
        # Verify can handle large number of claims
        transaction = result.interchanges[0].functional_groups[0].transactions[0]
        financial_tx = transaction.financial_transaction
        
        assert len(financial_tx.claims) >= 15
        assert financial_tx.financial_information.total_paid > 30000

    # Integration test examples

    def test_835_pmt_014_realistic_workflow_integration(self, schema_835_path):
        """
        Test realistic end-to-end payment workflow.
        
        Enhancement: Uses integration scenario for complete workflow.
        """
        from .fixtures.scenarios.integration_scenarios import IntegrationScenarios
        
        # Get complete workflow
        workflow = IntegrationScenarios.complete_patient_workflow()
        
        # Test the payment portion
        payment_edi = workflow["payment_advice"].build()
        
        result = parse_edi(payment_edi, schema_835_path)
        
        # Verify it integrates with other transaction types
        transaction = result.interchanges[0].functional_groups[0].transactions[0]
        financial_tx = transaction.financial_transaction
        
        assert financial_tx.financial_information.total_paid > 0
        assert len(financial_tx.claims) >= 1
        
        # Patient identifiers should match across workflow transactions
        # (Implementation would verify consistent patient/member IDs)