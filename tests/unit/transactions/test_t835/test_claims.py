"""
Unit tests for EDI 835 CLP (Claim Payment Information) processing.

This module contains comprehensive tests for claim payment variations,
migrated and consolidated from the original test structure.
"""

import pytest
from packages.core.transactions.t835.parser import Parser835
from tests.shared.assertions import (
    assert_balances, 
    assert_claim_status_valid,
    assert_amount_format,
    assert_date_format
)
from tests.shared.test_data import TestData


class Test835Claims:
    """Test cases for EDI 835 claim payment variations."""

    @pytest.fixture
    def base_835_segments(self):
        """Fixture providing base 835 segments."""
        return [
            ["ISA", "00", "", "00", "", "ZZ", "SENDER", "ZZ", "RECEIVER", "241226", "1430", "U", "00501", "000000001", "0", "P", ">"],
            ["GS", "HP", "SENDER", "RECEIVER", "20241226", "1430", "000000001", "X", "005010X221A1"],
            ["ST", "835", "0001"],
            ["BPR", "I", "1000.00", "C", "ACH", "", "", "", "", "", "", "20241226"],
            ["TRN", "1", "TRACE123", "1"]
        ]

    @pytest.fixture
    def base_835_trailer(self):
        """Fixture providing base 835 trailer segments."""
        return [
            ["SE", "10", "0001"],
            ["GE", "1", "000000001"],
            ["IEA", "1", "000000001"]
        ]

    def test_claim_primary_processed(self, base_835_segments, base_835_trailer):
        """
        Test primary processed claim (CLP02 status=1).
        
        Verifies:
        - Claim status code is valid
        - Paid amounts are positive
        - Financial balances are consistent
        """
        claim_segments = [
            ["CLP", "CLAIM12345", "1", "500.00", "400.00", "100.00", "MC", "PAYER123", "11"],
            ["NM1", "QC", "1", "DOE", "JANE", "A", "", "", "MI", "987654321"],
            ["DTM", "232", "20241215"],
            ["DTM", "233", "20241215"],
            ["CAS", "PR", "1", "50.00"],
            ["CAS", "CO", "45", "50.00"]
        ]
        
        all_segments = base_835_segments + claim_segments + base_835_trailer
        parser = Parser835(all_segments)
        result = parser.parse()
        
        # Verify claim structure
        financial_tx = result.interchanges[0].functional_groups[0].transactions[0].financial_transaction
        assert len(financial_tx.claims) == 1
        
        claim = financial_tx.claims[0]
        assert claim.claim_id == "CLAIM12345"
        assert_claim_status_valid(claim.status_code)
        assert claim.status_code == 1  # Primary processed
        
        # Verify amounts
        assert claim.total_charge == 500.00
        assert claim.total_paid == 400.00
        assert claim.patient_responsibility == 100.00
        assert_amount_format(claim.total_charge)
        assert_amount_format(claim.total_paid)
        assert_amount_format(claim.patient_responsibility)
        
        # Verify financial balance
        assert_balances(claim.total_charge, claim.total_paid, claim.patient_responsibility)
        
        # Verify adjustments
        assert len(claim.adjustments) == 2
        adjustment_codes = [adj.reason_code for adj in claim.adjustments]
        assert "1" in adjustment_codes   # Patient responsibility
        assert "45" in adjustment_codes  # Contractual adjustment

    def test_claim_secondary_processed(self, base_835_segments, base_835_trailer):
        """
        Test secondary processed claim (CLP02 status=2).
        """
        claim_segments = [
            ["CLP", "CLAIM22222", "2", "300.00", "240.00", "60.00", "MC", "SECONDARY123", "11"],
            ["NM1", "QC", "1", "SMITH", "JOHN", "B", "", "", "MI", "MEMBER456"],
            ["DTM", "232", "20241210"],
            ["CAS", "PR", "2", "60.00"]
        ]
        
        all_segments = base_835_segments + claim_segments + base_835_trailer
        parser = Parser835(all_segments)
        result = parser.parse()
        
        # Verify secondary claim
        claim = result.interchanges[0].functional_groups[0].transactions[0].financial_transaction.claims[0]
        
        assert claim.claim_id == "CLAIM22222"
        assert claim.status_code == 2  # Secondary processed
        assert_claim_status_valid(claim.status_code)
        
        # Verify balances for secondary claim
        assert_balances(claim.total_charge, claim.total_paid, claim.patient_responsibility)

    def test_claim_denied(self, base_835_segments, base_835_trailer):
        """
        Test denied claim (CLP02 status=4).
        """
        claim_segments = [
            ["CLP", "CLAIM44444", "4", "750.00", "0.00", "0.00", "MC", "DENIED123", "11"],
            ["NM1", "QC", "1", "JOHNSON", "MARY", "C", "", "", "MI", "MEMBER789"],
            ["CAS", "CO", "16", "750.00"]  # Denial reason
        ]
        
        all_segments = base_835_segments + claim_segments + base_835_trailer
        parser = Parser835(all_segments)
        result = parser.parse()
        
        # Verify denied claim
        claim = result.interchanges[0].functional_groups[0].transactions[0].financial_transaction.claims[0]
        
        assert claim.claim_id == "CLAIM44444"
        assert claim.status_code == 4  # Denied
        assert_claim_status_valid(claim.status_code)
        
        # Denied claims should have zero payment
        assert claim.total_paid == 0.00
        assert claim.patient_responsibility == 0.00
        
        # Should have denial adjustment
        assert len(claim.adjustments) >= 1
        denial_adjustment = claim.adjustments[0]
        assert denial_adjustment.group_code == "CO"
        assert denial_adjustment.amount == 750.00

    def test_claim_with_multiple_adjustments(self, base_835_segments, base_835_trailer):
        """
        Test claim with multiple adjustment groups.
        """
        claim_segments = [
            ["CLP", "CLAIM55555", "1", "1000.00", "700.00", "150.00", "MC", "MULTI123", "11"],
            ["NM1", "QC", "1", "WILLIAMS", "DAVID", "E", "", "", "MI", "MEMBER999"],
            ["CAS", "CO", "45", "100.00"],    # Contractual adjustment
            ["CAS", "PR", "1", "100.00"],     # Patient responsibility
            ["CAS", "PR", "2", "50.00"],      # Additional patient responsibility
            ["CAS", "OA", "23", "50.00"]      # Other adjustment
        ]
        
        all_segments = base_835_segments + claim_segments + base_835_trailer
        parser = Parser835(all_segments)
        result = parser.parse()
        
        # Verify multiple adjustments
        claim = result.interchanges[0].functional_groups[0].transactions[0].financial_transaction.claims[0]
        
        assert len(claim.adjustments) == 4
        
        # Verify different adjustment groups
        group_codes = [adj.group_code for adj in claim.adjustments]
        assert "CO" in group_codes  # Contractual obligation
        assert "PR" in group_codes  # Patient responsibility
        assert "OA" in group_codes  # Other adjustment
        
        # Verify adjustment amounts
        total_adjustments = sum(adj.amount for adj in claim.adjustments)
        assert total_adjustments == 300.00  # 100 + 100 + 50 + 50

    def test_claim_zero_payment(self, base_835_segments, base_835_trailer):
        """
        Test claim with zero payment but not denied.
        """
        claim_segments = [
            ["CLP", "CLAIM00000", "1", "200.00", "0.00", "200.00", "MC", "ZERO123", "11"],
            ["NM1", "QC", "1", "BROWN", "LISA", "F", "", "", "MI", "MEMBER111"],
            ["CAS", "PR", "1", "200.00"]  # All patient responsibility
        ]
        
        all_segments = base_835_segments + claim_segments + base_835_trailer
        parser = Parser835(all_segments)
        result = parser.parse()
        
        # Verify zero payment claim
        claim = result.interchanges[0].functional_groups[0].transactions[0].financial_transaction.claims[0]
        
        assert claim.status_code == 1  # Still processed as primary
        assert claim.total_paid == 0.00
        assert claim.patient_responsibility == 200.00
        
        # Financial balance should still be valid
        assert_balances(claim.total_charge, claim.total_paid, claim.patient_responsibility)

    def test_claim_with_services(self, base_835_segments, base_835_trailer):
        """
        Test claim with service line details.
        """
        claim_segments = [
            ["CLP", "CLAIM77777", "1", "350.00", "280.00", "70.00", "MC", "SERVICE123", "11"],
            ["NM1", "QC", "1", "DAVIS", "ROBERT", "G", "", "", "MI", "MEMBER222"],
            ["SVC", "HC:99213", "175.00", "140.00", "", "1"],
            ["DTM", "472", "20241215"],
            ["SVC", "HC:85025", "175.00", "140.00", "", "1"],
            ["DTM", "472", "20241215"],
            ["CAS", "CO", "45", "70.00"]
        ]
        
        all_segments = base_835_segments + claim_segments + base_835_trailer
        parser = Parser835(all_segments)
        result = parser.parse()
        
        # Verify claim with services
        claim = result.interchanges[0].functional_groups[0].transactions[0].financial_transaction.claims[0]
        
        assert len(claim.services) == 2
        
        # Verify service details
        service1 = claim.services[0]
        assert service1.service_code == "HC:99213"
        assert service1.charge_amount == 175.00
        assert service1.paid_amount == 140.00
        assert_date_format(service1.service_date)
        
        service2 = claim.services[1]
        assert service2.service_code == "HC:85025"
        assert service2.charge_amount == 175.00
        assert service2.paid_amount == 140.00
        assert_date_format(service2.service_date)
        
        # Verify service totals match claim totals
        total_service_charges = sum(s.charge_amount for s in claim.services)
        total_service_payments = sum(s.paid_amount for s in claim.services)
        
        assert total_service_charges == claim.total_charge
        assert total_service_payments == claim.total_paid

    def test_multiple_claims_in_transaction(self, base_835_segments, base_835_trailer):
        """
        Test transaction with multiple claims.
        """
        claim_segments = [
            # First claim
            ["CLP", "CLAIM11111", "1", "250.00", "200.00", "50.00", "MC", "FIRST123", "11"],
            ["NM1", "QC", "1", "PATIENT", "ONE", "", "", "", "MI", "MEMBER001"],
            ["CAS", "PR", "1", "50.00"],
            
            # Second claim
            ["CLP", "CLAIM22222", "1", "300.00", "250.00", "50.00", "MC", "SECOND123", "11"],
            ["NM1", "QC", "1", "PATIENT", "TWO", "", "", "", "MI", "MEMBER002"],
            ["CAS", "PR", "1", "50.00"],
            
            # Third claim  
            ["CLP", "CLAIM33333", "4", "400.00", "0.00", "0.00", "MC", "THIRD123", "11"],
            ["NM1", "QC", "1", "PATIENT", "THREE", "", "", "", "MI", "MEMBER003"],
            ["CAS", "CO", "16", "400.00"]
        ]
        
        all_segments = base_835_segments + claim_segments + base_835_trailer
        parser = Parser835(all_segments)
        result = parser.parse()
        
        # Verify multiple claims
        financial_tx = result.interchanges[0].functional_groups[0].transactions[0].financial_transaction
        assert len(financial_tx.claims) == 3
        
        # Verify individual claims
        claim1 = financial_tx.claims[0]
        assert claim1.claim_id == "CLAIM11111"
        assert claim1.status_code == 1
        assert claim1.total_paid == 200.00
        
        claim2 = financial_tx.claims[1]
        assert claim2.claim_id == "CLAIM22222"
        assert claim2.status_code == 1
        assert claim2.total_paid == 250.00
        
        claim3 = financial_tx.claims[2]
        assert claim3.claim_id == "CLAIM33333"
        assert claim3.status_code == 4  # Denied
        assert claim3.total_paid == 0.00

    def test_invalid_claim_status(self, base_835_segments, base_835_trailer):
        """
        Test handling of invalid claim status codes.
        """
        claim_segments = [
            ["CLP", "CLAIMINVALID", "99", "100.00", "50.00", "50.00", "MC", "INVALID123", "11"],
            ["NM1", "QC", "1", "INVALID", "CLAIM", "", "", "", "MI", "MEMBER999"]
        ]
        
        all_segments = base_835_segments + claim_segments + base_835_trailer
        parser = Parser835(all_segments)
        result = parser.parse()
        
        # Parser should still create the claim even with invalid status
        claim = result.interchanges[0].functional_groups[0].transactions[0].financial_transaction.claims[0]
        assert claim.status_code == 99
        
        # But assertion helper should catch invalid status
        with pytest.raises(AssertionError):
            assert_claim_status_valid(claim.status_code)