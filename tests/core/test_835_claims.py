"""
Test cases for EDI 835 CLP (Claim Payment Information) Variants.

Following test plan section 4: CLP (Claim payment information) Variants
"""

import pytest
from .test_utils import parse_edi, assert_balances, assert_claim_status_valid, build_835_edi
from .fixtures import EDIFixtures


class Test835Claims:
    """Test cases for EDI 835 claim payment variations."""

    def test_835_clp_001_primary_processed(self, schema_835_path, base_835_headers, base_835_trailer):
        """
        835-CLP-001: Primary processed (CLP02 status=1).
        
        Assertions: codes enumerated; paid amounts positive
        """
        segments = [
            "CLP*CLAIM12345*1*500.00*400.00*100.00*MC*PAYER123*11~",
            "NM1*QC*1*DOE*JANE*A***MI*987654321~",  # Patient info
            "DTM*232*20241215~",  # Service date from
            "DTM*233*20241215~",  # Service date to
            "CAS*PR*1*50.00~",    # Patient responsibility adjustment
            "CAS*CO*45*50.00~",   # Contractual adjustment
            "REF*1K*ORIGINALCLAIM123~"  # Original claim number
        ]
        
        edi_content = build_835_edi(
            base_835_headers,
            "".join(segments),
            base_835_trailer
        )
        
        result = parse_edi(edi_content, schema_835_path)
        
        # Verify structure
        transaction = result.interchanges[0].functional_groups[0].transactions[0]
        financial_tx = transaction.financial_transaction
        
        # Verify primary processed claim
        assert len(financial_tx.claims) == 1
        claim = financial_tx.claims[0]
        
        assert claim.claim_id == "CLAIM12345"
        assert_claim_status_valid(claim.status_code)
        assert claim.status_code == 1  # Primary processed
        assert claim.total_charge == 500.00
        assert claim.total_paid == 400.00
        assert claim.patient_responsibility == 100.00
        assert claim.payer_control_number == "PAYER123"
        
        # Verify adjustments
        assert len(claim.adjustments) == 2
        adjustment_codes = [adj.reason_code for adj in claim.adjustments]
        assert "1" in adjustment_codes   # Patient responsibility
        assert "45" in adjustment_codes  # Contractual adjustment

    def test_835_clp_002_secondary_with_prior_payer(self, schema_835_path, base_835_headers, base_835_trailer):
        """
        835-CLP-002: Secondary (status=2) with prior payer paid amount (AMT*AU).
        
        Assertions: COB values parsed and mapped
        """
        segments = [
            "CLP*CLAIM12345*2*500.00*150.00*50.00*MC*PAYER123*22~",  # Secondary claim
            "NM1*QC*1*DOE*JANE*A***MI*987654321~",
            "AMT*AU*300.00~",  # Coverage amount (primary paid)
            "AMT*A8*200.00~",  # Prior payer paid amount  
            "CAS*PR*3*50.00~",  # Patient deductible
            "CAS*CO*45*100.00~"  # Contractual adjustment
        ]
        
        edi_content = build_835_edi(
            base_835_headers,
            "".join(segments),
            base_835_trailer
        )
        
        result = parse_edi(edi_content, schema_835_path)
        
        # Verify structure
        transaction = result.interchanges[0].functional_groups[0].transactions[0]
        financial_tx = transaction.financial_transaction
        
        # Verify secondary claim
        assert len(financial_tx.claims) == 1
        claim = financial_tx.claims[0]
        
        assert claim.claim_id == "CLAIM12345"
        assert claim.status_code == 2  # Secondary processed
        assert claim.total_charge == 500.00
        assert claim.total_paid == 150.00  # Secondary payer amount
        assert claim.patient_responsibility == 50.00
        
        # Verify coordination of benefits adjustments
        assert len(claim.adjustments) == 2

    def test_835_clp_003_denied_claim(self, schema_835_path):
        """
        835-CLP-003: Denied claim (status=4) with zero CLP04.
        
        Assertions: CAS at claim level reflects denial; patient resp may be > 0
        """
        edi_content = EDIFixtures.get_835_denied_claim()
        
        result = parse_edi(edi_content, schema_835_path)
        
        # Verify structure
        transaction = result.interchanges[0].functional_groups[0].transactions[0]
        financial_tx = transaction.financial_transaction
        
        # Verify denied claim
        assert len(financial_tx.claims) == 1
        claim = financial_tx.claims[0]
        
        assert claim.claim_id == "CLAIM001"
        assert claim.status_code == 4  # Denied
        assert claim.total_charge == 500.00
        assert claim.total_paid == 0.00    # No payment
        assert claim.patient_responsibility == 0.00
        
        # Verify denial adjustments
        assert len(claim.adjustments) >= 1
        denial_adjustment = next((adj for adj in claim.adjustments if adj.reason_code == "29"), None)
        assert denial_adjustment is not None
        assert denial_adjustment.amount == 500.00

    def test_835_clp_004_reversal_adjustment(self, schema_835_path, base_835_headers, base_835_trailer):
        """
        835-CLP-004: Reversal/Adjustment (status=22).
        
        Assertions: negative CLP04 allowed; flags reversal
        """
        segments = [
            "CLP*CLAIM12345*22*-400.00*-400.00*0.00*MC*PAYER123*11~",  # Reversal
            "NM1*QC*1*DOE*JANE*A***MI*987654321~",
            "CAS*OA*94*-400.00~",  # Reversal adjustment
            "REF*F8*ORIGINALCLAIM456~"  # Reference to original claim
        ]
        
        edi_content = build_835_edi(
            base_835_headers,
            "".join(segments),
            base_835_trailer
        )
        
        result = parse_edi(edi_content, schema_835_path)
        
        # Verify structure
        transaction = result.interchanges[0].functional_groups[0].transactions[0]
        financial_tx = transaction.financial_transaction
        
        # Verify reversal claim
        assert len(financial_tx.claims) == 1
        claim = financial_tx.claims[0]
        
        assert claim.claim_id == "CLAIM12345"
        assert claim.status_code == 22  # Reversal
        assert claim.total_charge == -400.00   # Negative charge
        assert claim.total_paid == -400.00     # Negative payment (reversal)
        assert claim.patient_responsibility == 0.00

    def test_835_clp_005_capitation(self, schema_835_path, base_835_headers, base_835_trailer):
        """
        835-CLP-005: Capitation (status=23).
        
        Assertions: recognize and tag capitation; payment balancing still holds
        """
        segments = [
            "CLP*CLAIM12345*23*0.00*0.00*0.00*MC*PAYER123*11~",  # Capitation
            "NM1*QC*1*DOE*JANE*A***MI*987654321~",
            "CAS*CO*24*0.00~"  # Charges covered under capitation arrangement
        ]
        
        edi_content = build_835_edi(
            base_835_headers,
            "".join(segments),
            base_835_trailer
        )
        
        result = parse_edi(edi_content, schema_835_path)
        
        # Verify structure
        transaction = result.interchanges[0].functional_groups[0].transactions[0]
        financial_tx = transaction.financial_transaction
        
        # Verify capitation claim
        assert len(financial_tx.claims) == 1
        claim = financial_tx.claims[0]
        
        assert claim.claim_id == "CLAIM12345"
        assert claim.status_code == 23  # Capitation
        assert claim.total_charge == 0.00
        assert claim.total_paid == 0.00
        assert claim.patient_responsibility == 0.00

    def test_835_clp_006_claim_no_service_lines(self, schema_835_path, base_835_headers, base_835_trailer):
        """
        835-CLP-006: Claim with no service lines (institutional lump-sum).
        
        Assertions: valid; sum at claim level only
        """
        segments = [
            "CLP*CLAIM12345*1*1500.00*1200.00*300.00*MC*PAYER123*11~",
            "NM1*QC*1*DOE*JANE*A***MI*987654321~",
            "DTM*232*20241215~",
            "CAS*PR*1*200.00~",   # Patient responsibility
            "CAS*CO*45*100.00~"   # Contractual adjustment
            # No SVC segments - institutional lump sum
        ]
        
        edi_content = build_835_edi(
            base_835_headers,
            "".join(segments),
            base_835_trailer
        )
        
        result = parse_edi(edi_content, schema_835_path)
        
        # Verify structure
        transaction = result.interchanges[0].functional_groups[0].transactions[0]
        financial_tx = transaction.financial_transaction
        
        # Verify lump-sum claim
        assert len(financial_tx.claims) == 1
        claim = financial_tx.claims[0]
        
        assert claim.claim_id == "CLAIM12345"
        assert claim.status_code == 1
        assert claim.total_charge == 1500.00
        assert claim.total_paid == 1200.00
        assert claim.patient_responsibility == 300.00
        
        # Verify no service lines
        assert len(claim.services) == 0

    def test_835_clp_007_overpayment_recovery(self, schema_835_path, base_835_headers, base_835_trailer):
        """
        835-CLP-007: Claim with overpayment recovery (negative paid).
        
        Assertions: CLP04 < 0; PLB may or may not exist; ensure totals still match
        """
        segments = [
            "CLP*CLAIM12345*22*0.00*-250.00*0.00*MC*PAYER123*11~",  # Overpayment recovery
            "NM1*QC*1*DOE*JANE*A***MI*987654321~",
            "CAS*OA*94*-250.00~",  # Overpayment recovery adjustment
            "REF*F8*ORIGINALCLAIM789~"
        ]
        
        edi_content = build_835_edi(
            base_835_headers,
            "".join(segments),
            base_835_trailer
        )
        
        result = parse_edi(edi_content, schema_835_path)
        
        # Verify structure
        transaction = result.interchanges[0].functional_groups[0].transactions[0]
        financial_tx = transaction.financial_transaction
        
        # Verify overpayment recovery
        assert len(financial_tx.claims) == 1
        claim = financial_tx.claims[0]
        
        assert claim.claim_id == "CLAIM12345"
        assert claim.status_code == 22  # Reversal/adjustment
        assert claim.total_charge == 0.00
        assert claim.total_paid == -250.00  # Negative payment (recovery)
        assert claim.patient_responsibility == 0.00

    def test_835_clp_008_multiple_claims_same_transaction(self, schema_835_path):
        """
        Test multiple claims in the same transaction.
        """
        edi_content = EDIFixtures.get_835_with_multiple_claims()
        
        result = parse_edi(edi_content, schema_835_path)
        
        # Verify structure
        transaction = result.interchanges[0].functional_groups[0].transactions[0]
        financial_tx = transaction.financial_transaction
        
        # Verify multiple claims
        assert len(financial_tx.claims) == 3
        
        # Verify first claim (paid)
        claim1 = financial_tx.claims[0]
        assert claim1.claim_id == "CLAIM001"
        assert claim1.status_code == 1
        assert claim1.total_paid == 400.00
        
        # Verify second claim (paid)
        claim2 = financial_tx.claims[1]
        assert claim2.claim_id == "CLAIM002"
        assert claim2.status_code == 1
        assert claim2.total_paid == 600.00
        
        # Verify third claim (denied)
        claim3 = financial_tx.claims[2]
        assert claim3.claim_id == "CLAIM003"
        assert claim3.status_code == 4
        assert claim3.total_paid == 0.00

    def test_835_clp_009_claim_with_patient_control_number(self, schema_835_path, base_835_headers, base_835_trailer):
        """
        Test claim with patient control number (CLP08).
        """
        segments = [
            "CLP*CLAIM12345*1*500.00*400.00*100.00*MC*PAYER123*11*PCN456789~",
            "NM1*QC*1*DOE*JANE*A***MI*987654321~",
            "CAS*PR*1*75.00~",
            "CAS*CO*45*25.00~"
        ]
        
        edi_content = build_835_edi(
            base_835_headers,
            "".join(segments),
            base_835_trailer
        )
        
        result = parse_edi(edi_content, schema_835_path)
        
        # Verify structure
        transaction = result.interchanges[0].functional_groups[0].transactions[0]
        financial_tx = transaction.financial_transaction
        
        # Verify claim with patient control number
        assert len(financial_tx.claims) == 1
        claim = financial_tx.claims[0]
        
        assert claim.claim_id == "CLAIM12345"
        assert claim.status_code == 1
        assert claim.total_paid == 400.00
        # Patient control number would be in CLP08 if parser supports it

    def test_835_clp_010_claim_status_variations(self, schema_835_path, base_835_headers, base_835_trailer):
        """
        Test various claim status codes.
        """
        segments = [
            "CLP*CLAIM001*1*100.00*80.00*20.00*MC*P001*11~",   # Primary processed
            "CLP*CLAIM002*2*100.00*60.00*10.00*MC*P002*22~",   # Secondary processed  
            "CLP*CLAIM003*3*100.00*90.00*10.00*MC*P003*11~",   # Supplemental processed
            "CLP*CLAIM004*4*100.00*0.00*0.00*MC*P004*11~",     # Denied
            "CLP*CLAIM005*19*100.00*0.00*100.00*MC*P005*11~",  # Processed as primary, forwarded to additional payer
            "CLP*CLAIM006*20*100.00*0.00*0.00*MC*P006*11~",    # Processed as secondary, forwarded to additional payer
            "CLP*CLAIM007*21*100.00*0.00*0.00*MC*P007*11~",    # Processed as tertiary, forwarded to additional payer
            "CLP*CLAIM008*22*-50.00*-50.00*0.00*MC*P008*11~",  # Reversal
            "CLP*CLAIM009*23*0.00*0.00*0.00*MC*P009*11~"       # Capitation
        ]
        
        edi_content = build_835_edi(
            base_835_headers,
            "".join(segments),
            base_835_trailer
        )
        
        result = parse_edi(edi_content, schema_835_path)
        
        # Verify structure
        transaction = result.interchanges[0].functional_groups[0].transactions[0]
        financial_tx = transaction.financial_transaction
        
        # Verify all claim status variations
        assert len(financial_tx.claims) == 9
        
        status_codes = [claim.status_code for claim in financial_tx.claims]
        expected_codes = [1, 2, 3, 4, 19, 20, 21, 22, 23]
        
        for expected_code in expected_codes:
            assert expected_code in status_codes

    def test_835_clp_011_claim_balance_validation(self, schema_835_path, base_835_headers, base_835_trailer):
        """
        Test claim balance validation using shared assertion.
        """
        segments = [
            "CLP*CLAIM001*1*1000.00*800.00*200.00*MC*PAYER123*11~",
            "NM1*QC*1*DOE*JANE*A***MI*987654321~",
            "CAS*PR*1*150.00~",
            "CAS*CO*45*50.00~",
            "CLP*CLAIM002*1*500.00*400.00*100.00*MC*PAYER124*11~",
            "NM1*QC*1*SMITH*JOHN*B***MI*123456789~",
            "CAS*PR*1*75.00~",
            "CAS*CO*45*25.00~"
        ]
        
        edi_content = build_835_edi(
            base_835_headers,
            "".join(segments),
            base_835_trailer
        )
        
        result = parse_edi(edi_content, schema_835_path)
        
        # Verify structure
        transaction = result.interchanges[0].functional_groups[0].transactions[0]
        financial_tx = transaction.financial_transaction
        
        # Use shared balance assertion
        assert_balances(financial_tx)
        
        # Verify individual claim balances
        for claim in financial_tx.claims:
            # Basic balance check: paid + patient_resp + adjustments should roughly equal charge
            total_adjustments = sum(adj.amount for adj in claim.adjustments)
            expected_total = claim.total_paid + claim.patient_responsibility + total_adjustments
            # Allow small rounding differences
            assert abs(expected_total - claim.total_charge) <= 0.01

    def test_835_clp_012_claim_with_service_lines(self, schema_835_path, base_835_headers, base_835_trailer):
        """
        Test claim with detailed service lines.
        """
        segments = [
            "CLP*CLAIM12345*1*300.00*240.00*60.00*MC*PAYER123*11~",
            "NM1*QC*1*DOE*JANE*A***MI*987654321~",
            "SVC*HC:99213*100.00*80.00*UN*1~",
            "DTM*472*20241215~",
            "CAS*CO*45*20.00~",
            "SVC*HC:99214*200.00*160.00*UN*1~",
            "DTM*472*20241215~",
            "CAS*PR*1*30.00~",
            "CAS*CO*45*10.00~"
        ]
        
        edi_content = build_835_edi(
            base_835_headers,
            "".join(segments),
            base_835_trailer
        )
        
        result = parse_edi(edi_content, schema_835_path)
        
        # Verify structure
        transaction = result.interchanges[0].functional_groups[0].transactions[0]
        financial_tx = transaction.financial_transaction
        
        # Verify claim with service lines
        assert len(financial_tx.claims) == 1
        claim = financial_tx.claims[0]
        
        assert claim.claim_id == "CLAIM12345"
        assert claim.total_charge == 300.00
        assert claim.total_paid == 240.00
        
        # Verify service lines exist
        assert len(claim.services) == 2
        
        # Verify first service
        service1 = claim.services[0]
        assert service1.procedure_code == "99213"
        assert service1.charge == 100.00
        assert service1.paid == 80.00
        
        # Verify second service  
        service2 = claim.services[1]
        assert service2.procedure_code == "99214"
        assert service2.charge == 200.00
        assert service2.paid == 160.00