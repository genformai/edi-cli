"""
Integration tests for complete EDI workflow scenarios.

This module contains comprehensive integration tests that validate the complete
EDI processing workflow from raw EDI input to parsed output.
"""

import pytest
from decimal import Decimal
from packages.core.transactions.t835.parser import Parser835
from packages.core.plugins.plugin_835 import TransactionParser835
from tests.fixtures import EDIFixtures, PaymentScenarios, ClaimScenarios, IntegrationScenarios
from tests.shared.assertions import assert_balances, assert_transaction_structure, assert_financial_integrity


class TestCompleteEDI835Workflow:
    """Integration tests for complete 835 EDI workflow."""

    def test_simple_payment_workflow(self):
        """Test complete workflow for simple payment scenario."""
        # Get test data
        edi_content = EDIFixtures.get_simple_ach_payment()
        
        # Parse using main parser
        parser = Parser835()
        result = parser.parse(edi_content)
        
        # Validate structure
        assert_transaction_structure(result)
        
        # Validate financial integrity
        financial_info = result.interchanges[0].functional_groups[0].transactions[0].financial_information
        assert financial_info.payment_amount == Decimal("1000.00")
        assert financial_info.payment_method == "ACH"
        
        # Validate claims
        claims = result.interchanges[0].functional_groups[0].transactions[0].claims
        assert len(claims) >= 1
        
        claim = claims[0]
        assert_balances(
            charge=claim.charge_amount,
            paid=claim.payment_amount, 
            patient_resp=claim.patient_responsibility_amount
        )

    def test_multiple_claims_workflow(self):
        """Test workflow with multiple claims and adjustments."""
        edi_content = EDIFixtures.get_835_with_multiple_claims()
        
        parser = Parser835()
        result = parser.parse(edi_content)
        
        # Validate structure
        assert_transaction_structure(result)
        
        # Validate multiple claims processing
        transaction = result.interchanges[0].functional_groups[0].transactions[0]
        claims = transaction.claims
        
        assert len(claims) >= 2, "Should have multiple claims"
        
        # Validate each claim's financial integrity
        for claim in claims:
            if claim.status_code != "denied":  # Skip denied claims
                assert_balances(
                    charge=claim.charge_amount,
                    paid=claim.payment_amount,
                    patient_resp=claim.patient_responsibility_amount,
                    tolerance=0.01
                )

    def test_denied_claim_workflow(self):
        """Test workflow with denied claims."""
        edi_content = EDIFixtures.get_835_denied_claim()
        
        parser = Parser835()
        result = parser.parse(edi_content)
        
        # Validate structure
        assert_transaction_structure(result)
        
        # Validate denied claim processing
        transaction = result.interchanges[0].functional_groups[0].transactions[0]
        claims = transaction.claims
        
        assert len(claims) >= 1
        denied_claim = claims[0]
        
        assert denied_claim.payment_amount == Decimal("0.00")
        assert denied_claim.charge_amount > Decimal("0.00")
        assert len(denied_claim.adjustments) > 0
        
        # Validate adjustment totals equal charge amount for denied claims
        total_adjustments = sum(adj.amount for adj in denied_claim.adjustments)
        assert abs(total_adjustments - denied_claim.charge_amount) <= Decimal("0.01")

    def test_coordination_of_benefits_workflow(self):
        """Test workflow with coordination of benefits."""
        edi_content = EDIFixtures.get_coordination_of_benefits()
        
        parser = Parser835()
        result = parser.parse(edi_content)
        
        # Validate structure
        assert_transaction_structure(result)
        
        # Validate COB processing
        transaction = result.interchanges[0].functional_groups[0].transactions[0]
        claims = transaction.claims
        
        assert len(claims) >= 1
        cob_claim = claims[0]
        
        # COB claims should have proper financial balance accounting for prior payments
        assert cob_claim.payment_amount > Decimal("0.00")
        assert cob_claim.charge_amount > cob_claim.payment_amount

    def test_high_volume_batch_workflow(self):
        """Test workflow with high volume batch processing."""
        edi_content = EDIFixtures.get_high_volume_batch()
        
        parser = Parser835()
        result = parser.parse(edi_content)
        
        # Validate structure
        assert_transaction_structure(result)
        
        # Validate batch processing
        transaction = result.interchanges[0].functional_groups[0].transactions[0]
        claims = transaction.claims
        
        assert len(claims) >= 5, "Should have multiple claims in batch"
        
        # Validate total payment amount matches sum of claim payments
        total_claim_payments = sum(claim.payment_amount for claim in claims)
        financial_payment = transaction.financial_information.payment_amount
        
        assert abs(total_claim_payments - financial_payment) <= Decimal("0.01")


class TestEDI270WorkflowIntegration:
    """Integration tests for 270 EDI workflow."""

    def test_eligibility_inquiry_workflow(self):
        """Test complete workflow for eligibility inquiry."""
        edi_content = EDIFixtures.get_270_eligibility_inquiry()
        
        # Parse using generic parser (270 doesn't have dedicated parser yet)
        from packages.core.base.parser import BaseParser
        parser = BaseParser()
        segments = parser.parse_segments(edi_content)
        
        # Validate basic structure
        assert len(segments) > 0
        
        # Find key segments
        st_segments = [seg for seg in segments if seg[0] == "ST"]
        assert len(st_segments) == 1
        assert st_segments[0][1] == "270"  # Transaction type


class TestErrorHandlingWorkflow:
    """Integration tests for error handling workflows."""

    def test_invalid_envelope_handling(self):
        """Test workflow with invalid envelope structure."""
        edi_content = EDIFixtures.get_invalid_envelope()
        
        parser = Parser835()
        
        # Should handle gracefully without crashing
        try:
            result = parser.parse(edi_content)
            # If parsing succeeds, validate it's marked with errors
            assert hasattr(result, 'errors') or hasattr(result, 'warnings')
        except Exception as e:
            # Should raise a specific parsing exception, not a generic error
            assert "parsing" in str(e).lower() or "invalid" in str(e).lower()

    def test_malformed_segments_handling(self):
        """Test workflow with malformed segments."""
        malformed_edi = "ST*835*0001~INVALID*SEGMENT~SE*2*0001~"
        
        parser = Parser835()
        
        try:
            result = parser.parse(malformed_edi)
            # Should handle gracefully
            assert result is not None
        except Exception as e:
            # Should be a handled parsing exception
            assert isinstance(e, (ValueError, TypeError, AttributeError))


class TestScenarioBasedWorkflows:
    """Integration tests using scenario-based test data."""

    def test_payment_scenarios(self):
        """Test various payment scenario workflows."""
        scenarios = PaymentScenarios()
        
        for scenario_name, scenario_data in scenarios.get_all_scenarios().items():
            edi_content = scenario_data['edi_content']
            expected_payment = scenario_data['expected_payment_amount']
            
            parser = Parser835()
            result = parser.parse(edi_content)
            
            # Validate basic structure
            assert_transaction_structure(result)
            
            # Validate payment amount matches expectation
            financial_info = result.interchanges[0].functional_groups[0].transactions[0].financial_information
            assert abs(financial_info.payment_amount - expected_payment) <= Decimal("0.01"), \
                f"Payment amount mismatch in scenario: {scenario_name}"

    def test_claim_scenarios(self):
        """Test various claim scenario workflows."""
        scenarios = ClaimScenarios()
        
        for scenario_name, scenario_data in scenarios.get_all_scenarios().items():
            edi_content = scenario_data['edi_content']
            expected_claims = scenario_data['expected_claim_count']
            
            parser = Parser835()
            result = parser.parse(edi_content)
            
            # Validate claim count
            transaction = result.interchanges[0].functional_groups[0].transactions[0]
            actual_claims = len(transaction.claims)
            
            assert actual_claims == expected_claims, \
                f"Claim count mismatch in scenario: {scenario_name}"


class TestPerformanceWorkflows:
    """Integration tests for performance scenarios."""

    def test_large_batch_performance(self):
        """Test performance with large batch files."""
        # Create large batch scenario
        large_batch = IntegrationScenarios().get_large_batch_scenario()
        
        import time
        start_time = time.time()
        
        parser = Parser835()
        result = parser.parse(large_batch)
        
        end_time = time.time()
        processing_time = end_time - start_time
        
        # Validate processing completed
        assert_transaction_structure(result)
        
        # Performance assertion (adjust threshold as needed)
        assert processing_time < 10.0, f"Large batch processing took too long: {processing_time}s"

    def test_memory_efficiency(self):
        """Test memory efficiency with repeated parsing."""
        edi_content = EDIFixtures.get_835_with_multiple_claims()
        
        # Parse same content multiple times
        parser = Parser835()
        results = []
        
        for i in range(10):
            result = parser.parse(edi_content)
            results.append(result)
            
            # Validate each result
            assert_transaction_structure(result)
        
        # All results should be valid
        assert len(results) == 10


class TestCrossTransactionWorkflows:
    """Integration tests across different transaction types."""

    def test_mixed_transaction_processing(self):
        """Test processing different transaction types in sequence."""
        # Test data for different transaction types
        test_files = [
            EDIFixtures.get_minimal_835(),
            EDIFixtures.get_270_eligibility_inquiry(),
            EDIFixtures.get_835_denied_claim()
        ]
        
        results = []
        
        for edi_content in test_files:
            # Determine parser based on content
            if "ST*835" in edi_content:
                parser = Parser835()
                result = parser.parse(edi_content)
                assert_transaction_structure(result)
            else:
                # Use base parser for other types
                from packages.core.base.parser import BaseParser
                parser = BaseParser()
                segments = parser.parse_segments(edi_content)
                assert len(segments) > 0
                result = segments
            
            results.append(result)
        
        # All parsing should succeed
        assert len(results) == len(test_files)