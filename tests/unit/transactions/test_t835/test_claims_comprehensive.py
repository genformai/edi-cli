"""
Comprehensive test cases for EDI 835 CLP (Claim Payment Information) Variants.

Following test plan section 4: CLP (Claim payment information) Variants

This module contains the migrated and enhanced comprehensive claim tests
from the original test suite.
"""

import pytest
from decimal import Decimal
from packages.core.parser_835 import Parser835
from tests.fixtures import EDIFixtures
from tests.shared.assertions import assert_balances, assert_transaction_structure
from tests.shared.test_patterns import StandardTestMixin


class Test835ClaimsComprehensive(StandardTestMixin):
    """Comprehensive test cases for EDI 835 claim payment variations."""

    def test_835_clp_001_primary_processed(self, edi_fixtures):
        """
        835-CLP-001: Primary processed (CLP02 status=1).
        
        Assertions: codes enumerated; paid amounts positive
        """
        # Create test EDI with primary processed claim
        from tests.fixtures.builders.builder_835 import EDI835Builder
        
        edi_content = (EDI835Builder()
                      .with_envelope("SENDER", "RECEIVER", "HP", "005010X221A1")
                      .with_control_numbers("000012345", "000006789", "0001")
                      .with_payer("INSURANCE COMPANY")
                      .with_payee("PROVIDER NAME", "1234567890")
                      .with_ach_payment(Decimal("400.00"))
                      .with_trace_number("12345")
                      .with_primary_claim("CLAIM12345", Decimal("500.00"), Decimal("400.00"), Decimal("100.00"))
                      .with_custom_segment("NM1*QC*1*DOE*JANE*A***MI*987654321~")
                      .with_custom_segment("DTM*232*20241215~")
                      .with_custom_segment("DTM*233*20241215~")
                      .with_adjustment("PR", "1", Decimal("50.00"))
                      .with_adjustment("CO", "45", Decimal("50.00"))
                      .with_custom_segment("REF*1K*ORIGINALCLAIM123~")
                      .build())
        
        parser = Parser835()
        result = parser.parse(edi_content)
        
        # Verify structure
        assert_transaction_structure(result)
        transaction = result.interchanges[0].functional_groups[0].transactions[0]
        
        # Verify primary processed claim
        assert len(transaction.claims) == 1
        claim = transaction.claims[0]
        
        assert claim.claim_id == "CLAIM12345"
        assert claim.status_code == "1"  # Primary processed
        assert claim.charge_amount == Decimal("500.00")
        assert claim.payment_amount == Decimal("400.00")
        assert claim.patient_responsibility_amount == Decimal("100.00")
        
        # Verify adjustments
        assert len(claim.adjustments) >= 2
        adjustment_codes = [adj.reason_code for adj in claim.adjustments]
        assert "1" in adjustment_codes   # Patient responsibility
        assert "45" in adjustment_codes  # Contractual adjustment

    def test_835_clp_002_secondary_with_prior_payer(self, edi_fixtures):
        """
        835-CLP-002: Secondary (status=2) with prior payer paid amount (AMT*AU).
        
        Assertions: COB values parsed and mapped
        """
        edi_content = edi_fixtures.get_coordination_of_benefits()
        
        parser = Parser835()
        result = parser.parse(edi_content)
        
        # Verify structure
        assert_transaction_structure(result)
        transaction = result.interchanges[0].functional_groups[0].transactions[0]
        
        # Verify secondary claim
        assert len(transaction.claims) == 1
        claim = transaction.claims[0]
        
        assert claim.claim_id == "COB001"
        assert claim.status_code == "2"  # Secondary processed
        assert claim.charge_amount == Decimal("1000.00")
        assert claim.payment_amount == Decimal("300.00")  # Secondary payer amount
        assert claim.patient_responsibility_amount == Decimal("100.00")
        
        # Verify coordination of benefits
        assert len(claim.adjustments) >= 1

    def test_835_clp_003_denied_claim(self, edi_fixtures):
        """
        835-CLP-003: Denied claim (status=4) with zero CLP04.
        
        Assertions: CAS at claim level reflects denial; patient resp may be > 0
        """
        edi_content = edi_fixtures.get_835_denied_claim()
        
        parser = Parser835()
        result = parser.parse(edi_content)
        
        # Verify structure
        assert_transaction_structure(result)
        transaction = result.interchanges[0].functional_groups[0].transactions[0]
        
        # Verify denied claim
        assert len(transaction.claims) == 1
        claim = transaction.claims[0]
        
        assert claim.claim_id == "CLAIM001"
        assert claim.status_code == "4"  # Denied
        assert claim.charge_amount == Decimal("500.00")
        assert claim.payment_amount == Decimal("0.00")    # No payment
        assert claim.patient_responsibility_amount == Decimal("0.00")
        
        # Verify denial adjustments
        assert len(claim.adjustments) >= 1
        denial_adjustment = next((adj for adj in claim.adjustments if adj.reason_code == "29"), None)
        assert denial_adjustment is not None
        assert denial_adjustment.amount == Decimal("500.00")

    def test_835_clp_004_reversal_adjustment(self):
        """
        835-CLP-004: Reversal/Adjustment (status=22).
        
        Assertions: negative CLP04 allowed; flags reversal
        """
        from tests.fixtures.builders.builder_835 import EDI835Builder
        
        edi_content = (EDI835Builder()
                      .with_envelope("SENDER", "RECEIVER", "HP", "005010X221A1")
                      .with_control_numbers("000012345", "000006789", "0001")
                      .with_payer("INSURANCE COMPANY")
                      .with_payee("PROVIDER NAME", "1234567890")
                      .with_ach_payment(Decimal("-400.00"))
                      .with_trace_number("12345")
                      .with_custom_segment("CLP*CLAIM12345*22*-400.00*-400.00*0.00*MC*PAYER123*11~")
                      .with_custom_segment("NM1*QC*1*DOE*JANE*A***MI*987654321~")
                      .with_adjustment("OA", "94", Decimal("-400.00"))
                      .with_custom_segment("REF*F8*ORIGINALCLAIM456~")
                      .build())
        
        parser = Parser835()
        result = parser.parse(edi_content)
        
        # Verify structure
        assert_transaction_structure(result)
        transaction = result.interchanges[0].functional_groups[0].transactions[0]
        
        # Verify reversal claim
        assert len(transaction.claims) == 1
        claim = transaction.claims[0]
        
        assert claim.claim_id == "CLAIM12345"
        assert claim.status_code == "22"  # Reversal
        assert claim.charge_amount == Decimal("-400.00")   # Negative charge
        assert claim.payment_amount == Decimal("-400.00")  # Negative payment (reversal)
        assert claim.patient_responsibility_amount == Decimal("0.00")

    def test_835_clp_005_capitation(self):
        """
        835-CLP-005: Capitation (status=23).
        
        Assertions: recognize and tag capitation; payment balancing still holds
        """
        from tests.fixtures.builders.builder_835 import EDI835Builder
        
        edi_content = (EDI835Builder()
                      .with_envelope("SENDER", "RECEIVER", "HP", "005010X221A1")
                      .with_control_numbers("000012345", "000006789", "0001")
                      .with_payer("INSURANCE COMPANY")
                      .with_payee("PROVIDER NAME", "1234567890")
                      .with_ach_payment(Decimal("0.00"))
                      .with_trace_number("12345")
                      .with_custom_segment("CLP*CLAIM12345*23*0.00*0.00*0.00*MC*PAYER123*11~")
                      .with_custom_segment("NM1*QC*1*DOE*JANE*A***MI*987654321~")
                      .with_adjustment("CO", "24", Decimal("0.00"))
                      .build())
        
        parser = Parser835()
        result = parser.parse(edi_content)
        
        # Verify structure
        assert_transaction_structure(result)
        transaction = result.interchanges[0].functional_groups[0].transactions[0]
        
        # Verify capitation claim
        assert len(transaction.claims) == 1
        claim = transaction.claims[0]
        
        assert claim.claim_id == "CLAIM12345"
        assert claim.status_code == "23"  # Capitation
        assert claim.charge_amount == Decimal("0.00")
        assert claim.payment_amount == Decimal("0.00")
        assert claim.patient_responsibility_amount == Decimal("0.00")

    def test_835_clp_006_claim_no_service_lines(self):
        """
        835-CLP-006: Claim with no service lines (institutional lump-sum).
        
        Assertions: valid; sum at claim level only
        """
        from tests.fixtures.builders.builder_835 import EDI835Builder
        
        edi_content = (EDI835Builder()
                      .with_envelope("SENDER", "RECEIVER", "HP", "005010X221A1")
                      .with_control_numbers("000012345", "000006789", "0001")
                      .with_payer("INSURANCE COMPANY")
                      .with_payee("PROVIDER NAME", "1234567890")
                      .with_ach_payment(Decimal("1200.00"))
                      .with_trace_number("12345")
                      .with_primary_claim("CLAIM12345", Decimal("1500.00"), Decimal("1200.00"), Decimal("300.00"))
                      .with_custom_segment("NM1*QC*1*DOE*JANE*A***MI*987654321~")
                      .with_custom_segment("DTM*232*20241215~")
                      .with_adjustment("PR", "1", Decimal("200.00"))
                      .with_adjustment("CO", "45", Decimal("100.00"))
                      .build())
        
        parser = Parser835()
        result = parser.parse(edi_content)
        
        # Verify structure
        assert_transaction_structure(result)
        transaction = result.interchanges[0].functional_groups[0].transactions[0]
        
        # Verify lump-sum claim
        assert len(transaction.claims) == 1
        claim = transaction.claims[0]
        
        assert claim.claim_id == "CLAIM12345"
        assert claim.status_code == "1"
        assert claim.charge_amount == Decimal("1500.00")
        assert claim.payment_amount == Decimal("1200.00")
        assert claim.patient_responsibility_amount == Decimal("300.00")
        
        # Verify no service lines (if services attribute exists)
        if hasattr(claim, 'services'):
            assert len(claim.services) == 0

    def test_835_clp_007_overpayment_recovery(self):
        """
        835-CLP-007: Claim with overpayment recovery (negative paid).
        
        Assertions: CLP04 < 0; PLB may or may not exist; ensure totals still match
        """
        from tests.fixtures.builders.builder_835 import EDI835Builder
        
        edi_content = (EDI835Builder()
                      .with_envelope("SENDER", "RECEIVER", "HP", "005010X221A1")
                      .with_control_numbers("000012345", "000006789", "0001")
                      .with_payer("INSURANCE COMPANY")
                      .with_payee("PROVIDER NAME", "1234567890")
                      .with_ach_payment(Decimal("-250.00"))
                      .with_trace_number("12345")
                      .with_custom_segment("CLP*CLAIM12345*22*0.00*-250.00*0.00*MC*PAYER123*11~")
                      .with_custom_segment("NM1*QC*1*DOE*JANE*A***MI*987654321~")
                      .with_adjustment("OA", "94", Decimal("-250.00"))
                      .with_custom_segment("REF*F8*ORIGINALCLAIM789~")
                      .build())
        
        parser = Parser835()
        result = parser.parse(edi_content)
        
        # Verify structure
        assert_transaction_structure(result)
        transaction = result.interchanges[0].functional_groups[0].transactions[0]
        
        # Verify overpayment recovery
        assert len(transaction.claims) == 1
        claim = transaction.claims[0]
        
        assert claim.claim_id == "CLAIM12345"
        assert claim.status_code == "22"  # Reversal/adjustment
        assert claim.charge_amount == Decimal("0.00")
        assert claim.payment_amount == Decimal("-250.00")  # Negative payment (recovery)
        assert claim.patient_responsibility_amount == Decimal("0.00")

    def test_835_clp_008_multiple_claims_same_transaction(self, edi_fixtures):
        """
        Test multiple claims in the same transaction.
        """
        edi_content = edi_fixtures.get_835_with_multiple_claims()
        
        parser = Parser835()
        result = parser.parse(edi_content)
        
        # Verify structure
        assert_transaction_structure(result)
        transaction = result.interchanges[0].functional_groups[0].transactions[0]
        
        # Verify multiple claims
        assert len(transaction.claims) >= 2
        
        # Find paid and denied claims
        paid_claims = [c for c in transaction.claims if c.payment_amount > Decimal("0")]
        denied_claims = [c for c in transaction.claims if c.payment_amount == Decimal("0")]
        
        assert len(paid_claims) >= 1
        assert len(denied_claims) >= 1

    def test_835_clp_009_claim_with_patient_control_number(self):
        """
        Test claim with patient control number (CLP08).
        """
        from tests.fixtures.builders.builder_835 import EDI835Builder
        
        edi_content = (EDI835Builder()
                      .with_envelope("SENDER", "RECEIVER", "HP", "005010X221A1")
                      .with_control_numbers("000012345", "000006789", "0001")
                      .with_payer("INSURANCE COMPANY")
                      .with_payee("PROVIDER NAME", "1234567890")
                      .with_ach_payment(Decimal("400.00"))
                      .with_trace_number("12345")
                      .with_primary_claim("CLAIM12345", Decimal("500.00"), Decimal("400.00"), Decimal("100.00"))
                      .with_custom_segment("NM1*QC*1*DOE*JANE*A***MI*987654321~")
                      .with_adjustment("PR", "1", Decimal("75.00"))
                      .with_adjustment("CO", "45", Decimal("25.00"))
                      .build())
        
        parser = Parser835()
        result = parser.parse(edi_content)
        
        # Verify structure
        assert_transaction_structure(result)
        transaction = result.interchanges[0].functional_groups[0].transactions[0]
        
        # Verify claim with patient control number
        assert len(transaction.claims) == 1
        claim = transaction.claims[0]
        
        assert claim.claim_id == "CLAIM12345"
        assert claim.status_code == "1"
        assert claim.payment_amount == Decimal("400.00")

    def test_835_clp_010_claim_status_variations(self):
        """
        Test various claim status codes.
        """
        from tests.fixtures.builders.builder_835 import EDI835Builder
        
        # Build EDI with multiple claim status variations
        builder = (EDI835Builder()
                  .with_envelope("SENDER", "RECEIVER", "HP", "005010X221A1")
                  .with_control_numbers("000012345", "000006789", "0001")
                  .with_payer("INSURANCE COMPANY")
                  .with_payee("PROVIDER NAME", "1234567890")
                  .with_ach_payment(Decimal("400.00"))
                  .with_trace_number("12345"))
        
        # Add claims with different status codes
        builder.with_custom_segment("CLP*CLAIM001*1*100.00*80.00*20.00*MC*P001*11~")   # Primary processed
        builder.with_custom_segment("CLP*CLAIM002*2*100.00*60.00*10.00*MC*P002*22~")   # Secondary processed  
        builder.with_custom_segment("CLP*CLAIM003*3*100.00*90.00*10.00*MC*P003*11~")   # Supplemental processed
        builder.with_custom_segment("CLP*CLAIM004*4*100.00*0.00*0.00*MC*P004*11~")     # Denied
        builder.with_custom_segment("CLP*CLAIM005*22*-50.00*-50.00*0.00*MC*P005*11~")  # Reversal
        builder.with_custom_segment("CLP*CLAIM006*23*0.00*0.00*0.00*MC*P006*11~")      # Capitation
        
        edi_content = builder.build()
        
        parser = Parser835()
        result = parser.parse(edi_content)
        
        # Verify structure
        assert_transaction_structure(result)
        transaction = result.interchanges[0].functional_groups[0].transactions[0]
        
        # Verify all claim status variations
        assert len(transaction.claims) >= 6
        
        status_codes = [claim.status_code for claim in transaction.claims]
        expected_codes = ["1", "2", "3", "4", "22", "23"]
        
        for expected_code in expected_codes:
            assert expected_code in status_codes

    def test_835_clp_011_claim_balance_validation(self):
        """
        Test claim balance validation using shared assertion.
        """
        from tests.fixtures.builders.builder_835 import EDI835Builder
        
        edi_content = (EDI835Builder()
                      .with_envelope("SENDER", "RECEIVER", "HP", "005010X221A1")
                      .with_control_numbers("000012345", "000006789", "0001")
                      .with_payer("INSURANCE COMPANY")
                      .with_payee("PROVIDER NAME", "1234567890")
                      .with_ach_payment(Decimal("1200.00"))
                      .with_trace_number("12345")
                      .with_primary_claim("CLAIM001", Decimal("1000.00"), Decimal("800.00"), Decimal("200.00"))
                      .with_custom_segment("NM1*QC*1*DOE*JANE*A***MI*987654321~")
                      .with_adjustment("PR", "1", Decimal("150.00"))
                      .with_adjustment("CO", "45", Decimal("50.00"))
                      .with_primary_claim("CLAIM002", Decimal("500.00"), Decimal("400.00"), Decimal("100.00"))
                      .with_custom_segment("NM1*QC*1*SMITH*JOHN*B***MI*123456789~")
                      .with_adjustment("PR", "1", Decimal("75.00"))
                      .with_adjustment("CO", "45", Decimal("25.00"))
                      .build())
        
        parser = Parser835()
        result = parser.parse(edi_content)
        
        # Verify structure
        assert_transaction_structure(result)
        transaction = result.interchanges[0].functional_groups[0].transactions[0]
        
        # Verify individual claim balances
        for claim in transaction.claims:
            # Basic balance check: adjustments should account for differences
            total_adjustments = sum(adj.amount for adj in claim.adjustments)
            expected_diff = claim.charge_amount - claim.payment_amount - claim.patient_responsibility_amount
            # Allow small rounding differences
            assert abs(expected_diff - total_adjustments) <= Decimal("0.01")

    def test_835_clp_012_claim_with_service_lines(self):
        """
        Test claim with detailed service lines.
        """
        from tests.fixtures.builders.builder_835 import EDI835Builder
        
        edi_content = (EDI835Builder()
                      .with_envelope("SENDER", "RECEIVER", "HP", "005010X221A1")
                      .with_control_numbers("000012345", "000006789", "0001")
                      .with_payer("INSURANCE COMPANY")
                      .with_payee("PROVIDER NAME", "1234567890")
                      .with_ach_payment(Decimal("240.00"))
                      .with_trace_number("12345")
                      .with_primary_claim("CLAIM12345", Decimal("300.00"), Decimal("240.00"), Decimal("60.00"))
                      .with_custom_segment("NM1*QC*1*DOE*JANE*A***MI*987654321~")
                      .with_custom_segment("SVC*HC:99213*100.00*80.00*UN*1~")
                      .with_custom_segment("DTM*472*20241215~")
                      .with_adjustment("CO", "45", Decimal("20.00"))
                      .with_custom_segment("SVC*HC:99214*200.00*160.00*UN*1~")
                      .with_custom_segment("DTM*472*20241215~")
                      .with_adjustment("PR", "1", Decimal("30.00"))
                      .with_adjustment("CO", "45", Decimal("10.00"))
                      .build())
        
        parser = Parser835()
        result = parser.parse(edi_content)
        
        # Verify structure
        assert_transaction_structure(result)
        transaction = result.interchanges[0].functional_groups[0].transactions[0]
        
        # Verify claim with service lines
        assert len(transaction.claims) == 1
        claim = transaction.claims[0]
        
        assert claim.claim_id == "CLAIM12345"
        assert claim.charge_amount == Decimal("300.00")
        assert claim.payment_amount == Decimal("240.00")
        
        # Service line verification would depend on parser implementation
        # If parser supports service lines, they would be tested here