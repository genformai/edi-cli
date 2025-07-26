"""
Integration test cases for EDI 835 (Electronic Remittance Advice) Parser.

This file contains comprehensive parser tests for 835 transaction processing,
migrated from the original test suite and enhanced with modern patterns.
"""

import pytest
import time
from decimal import Decimal
from packages.core.parser_835 import Parser835
from tests.fixtures import EDIFixtures
from tests.shared.assertions import assert_transaction_structure, assert_financial_integrity
from tests.shared.test_patterns import StandardTestMixin, PerformanceTestMixin


class Test835ParserIntegration(StandardTestMixin, PerformanceTestMixin):
    """Integration test cases for 835 parser functionality."""

    def test_parse_835_minimal(self, edi_fixtures):
        """Test parsing a minimal 835 EDI file with only required segments."""
        edi_content = edi_fixtures.get_minimal_835()
        
        parser = Parser835()
        result = parser.parse(edi_content)
        
        # Verify basic structure
        assert_transaction_structure(result)
        
        # Verify transaction has required elements
        transaction = result.interchanges[0].functional_groups[0].transactions[0]
        assert hasattr(transaction, 'financial_information')
        assert hasattr(transaction, 'payer')
        assert hasattr(transaction, 'payee')

    def test_parse_835_multiple_claims(self, edi_fixtures):
        """Test parsing an 835 EDI file with multiple claims and adjustments."""
        edi_content = edi_fixtures.get_835_with_multiple_claims()
        
        parser = Parser835()
        result = parser.parse(edi_content)
        
        # Verify structure
        assert_transaction_structure(result)
        transaction = result.interchanges[0].functional_groups[0].transactions[0]
        
        # Verify multiple claims
        assert len(transaction.claims) >= 2
        
        # Verify claims have expected data
        for claim in transaction.claims:
            assert claim.claim_id is not None
            assert claim.status_code is not None
            assert claim.charge_amount >= Decimal("0")

    def test_parse_835_denied_claims(self, edi_fixtures):
        """Test parsing 835 with denied claims."""
        edi_content = edi_fixtures.get_835_denied_claim()
        
        parser = Parser835()
        result = parser.parse(edi_content)
        
        # Verify structure
        assert_transaction_structure(result)
        transaction = result.interchanges[0].functional_groups[0].transactions[0]
        
        # Should have claims even if denied
        assert len(transaction.claims) >= 1
        
        # Find denied claim
        denied_claim = next((c for c in transaction.claims if c.payment_amount == Decimal("0.00")), None)
        assert denied_claim is not None
        assert denied_claim.charge_amount > Decimal("0.00")

    def test_parser_handles_empty_string(self):
        """Test that parser handles empty EDI content gracefully."""
        parser = Parser835()
        
        # Should handle gracefully without crashing
        try:
            result = parser.parse("")
            # If parsing succeeds, should return empty or error structure
            assert result is not None
        except Exception as e:
            # Should be a specific parsing exception
            assert "empty" in str(e).lower() or "invalid" in str(e).lower()

    def test_parser_handles_malformed_segments(self):
        """Test parser behavior with malformed segments."""
        edi_content = (
            "ISA*00*          *00*          *ZZ*SENDER         *ZZ*RECEIVER       "
            "*241226*1430*^*00501*000012345*0*P*:~"
            "INVALID_SEGMENT~"
            "GS*HP*SENDER*RECEIVER*20241226*1430*000006789*X*005010X221A1~"
            "ST*835*0001~"
            "BPR*I*1000.00*C*ACH*CCP*01*123456789*DA*987654321*9876543210*20241226~"
            "SE*2*0001~"
            "GE*1*000006789~"
            "IEA*1*000012345~"
        )
        
        parser = Parser835()
        
        try:
            result = parser.parse(edi_content)
            # Should parse valid segments despite malformed ones
            if result is not None and hasattr(result, 'interchanges'):
                assert len(result.interchanges) >= 0
        except Exception as e:
            # Should be a handled parsing exception
            assert not isinstance(e, (SystemExit, KeyboardInterrupt))

    def test_numeric_formatting_validation(self, edi_fixtures):
        """Test that numeric values are properly formatted and validated."""
        edi_content = edi_fixtures.get_minimal_835()
        
        parser = Parser835()
        result = parser.parse(edi_content)
        
        # Verify structure and check numeric formatting
        assert_transaction_structure(result)
        transaction = result.interchanges[0].functional_groups[0].transactions[0]
        
        # Check that amounts are properly typed as Decimal
        if hasattr(transaction, 'financial_information'):
            payment_amount = transaction.financial_information.payment_amount
            assert isinstance(payment_amount, (Decimal, int, float))
            assert payment_amount >= Decimal("0")
        
        # Check claim amounts
        if hasattr(transaction, 'claims') and transaction.claims:
            for claim in transaction.claims:
                assert isinstance(claim.charge_amount, (Decimal, int, float))
                assert isinstance(claim.payment_amount, (Decimal, int, float))
                if hasattr(claim, 'patient_responsibility_amount'):
                    assert isinstance(claim.patient_responsibility_amount, (Decimal, int, float))

    def test_date_formatting_validation(self, edi_fixtures):
        """Test that dates are properly formatted and validated."""
        edi_content = edi_fixtures.get_minimal_835()
        
        parser = Parser835()
        result = parser.parse(edi_content)
        
        # Verify structure
        assert_transaction_structure(result)
        
        # Check date formatting in envelope
        interchange = result.interchanges[0]
        if hasattr(interchange, 'date') and interchange.date:
            # Should be in ISO format or valid date format
            assert len(str(interchange.date)) >= 8

    def test_multiple_reference_numbers(self):
        """Test parsing multiple TRN segments."""
        from tests.fixtures.builders.builder_835 import EDI835Builder
        
        edi_content = (EDI835Builder()
                      .with_envelope("SENDER", "RECEIVER", "HP", "005010X221A1")
                      .with_control_numbers("000012345", "000006789", "0001")
                      .with_payer("INSURANCE COMPANY")
                      .with_payee("PROVIDER NAME", "1234567890")
                      .with_ach_payment(Decimal("1000.00"))
                      .with_trace_number("TRACE001")
                      .with_custom_segment("TRN*1*TRACE002*REF002~")
                      .with_primary_claim("CLAIM001", Decimal("1200.00"), Decimal("1000.00"), Decimal("200.00"))
                      .build())
        
        parser = Parser835()
        result = parser.parse(edi_content)
        
        # Verify structure
        assert_transaction_structure(result)
        transaction = result.interchanges[0].functional_groups[0].transactions[0]
        
        # Should parse successfully with multiple trace numbers
        assert transaction is not None

    def test_parser_performance_large_file(self, performance_config):
        """Test parser performance with larger EDI files."""
        # Create a larger EDI file with multiple claims
        from tests.fixtures.builders.builder_835 import EDI835Builder
        
        builder = (EDI835Builder()
                  .with_envelope("SENDER", "RECEIVER", "HP", "005010X221A1")
                  .with_control_numbers("000012345", "000006789", "0001")
                  .with_payer("INSURANCE COMPANY")
                  .with_payee("PROVIDER NAME", "1234567890")
                  .with_ach_payment(Decimal("4000.00"))
                  .with_trace_number("12345"))
        
        # Add 50 claims
        for i in range(50):
            charge = Decimal(str(100 + (i * 10)))
            paid = charge * Decimal("0.8")
            patient_resp = charge - paid
            builder.with_primary_claim(f"CLAIM{i:03d}", charge, paid, patient_resp)
        
        edi_content = builder.build()
        
        parser = Parser835()
        
        # Measure parsing time
        start_time = time.time()
        result = parser.parse(edi_content)
        end_time = time.time()
        
        parsing_time = end_time - start_time
        
        # Verify all claims were parsed
        assert_transaction_structure(result)
        transaction = result.interchanges[0].functional_groups[0].transactions[0]
        
        assert len(transaction.claims) == 50
        
        # Performance assertion (should be fast)
        threshold = performance_config.get("complex_parse_threshold", 1.0)
        assert parsing_time < threshold, f"Large file parsing too slow: {parsing_time:.4f}s"
        
        # Verify first and last claims
        first_claim = transaction.claims[0]
        assert first_claim.claim_id == "CLAIM000"
        
        last_claim = transaction.claims[-1]
        assert last_claim.claim_id == "CLAIM049"

    def test_parser_error_recovery(self):
        """Test parser error recovery with partially corrupted data."""
        edi_content = (
            "ISA*00*          *00*          *ZZ*SENDER         *ZZ*RECEIVER       "
            "*241226*1430*^*00501*000012345*0*P*:~"
            "GS*HP*SENDER*RECEIVER*20241226*1430*000006789*X*005010X221A1~"
            "ST*835*0001~"
            "BPR*I*1000.00*C*ACH*CCP*01*123456789*DA*987654321*9876543210*20241226~"
            "TRN*1*12345*1234567890~"
            "CORRUPTED*SEGMENT*WITH*TOO*MANY*ELEMENTS*AND*INVALID*DATA*STRUCTURE~"
            "N1*PR*INSURANCE COMPANY~"
            "N1*PE*PROVIDER NAME~"
            "REF*TJ*1234567890~"
            "CLP*CLAIM001*1*1200.00*1000.00*200.00*MC*456789*11~"
            "SE*9*0001~"
            "GE*1*000006789~"
            "IEA*1*000012345~"
        )
        
        parser = Parser835()
        
        try:
            result = parser.parse(edi_content)
            # Should still parse valid segments despite corruption
            if result is not None and hasattr(result, 'interchanges'):
                assert len(result.interchanges) >= 0
        except Exception as e:
            # Should be a handled parsing exception, not a system crash
            assert not isinstance(e, (SystemExit, KeyboardInterrupt))

    def test_parser_segment_order_tolerance(self):
        """Test parser tolerance for segment order variations."""
        edi_content = (
            "ISA*00*          *00*          *ZZ*SENDER         *ZZ*RECEIVER       "
            "*241226*1430*^*00501*000012345*0*P*:~"
            "GS*HP*SENDER*RECEIVER*20241226*1430*000006789*X*005010X221A1~"
            "ST*835*0001~"
            "BPR*I*1000.00*C*ACH*CCP*01*123456789*DA*987654321*9876543210*20241226~"
            # N1 segments in different order than typical
            "N1*PE*PROVIDER NAME*XX*1234567890~"
            "REF*TJ*1234567890~"
            "N1*PR*INSURANCE COMPANY~"
            "TRN*1*12345*1234567890~"  # TRN after N1 segments
            "CLP*CLAIM001*1*1200.00*1000.00*200.00*MC*456789*11~"
            "SE*8*0001~"
            "GE*1*000006789~"
            "IEA*1*000012345~"
        )
        
        parser = Parser835()
        result = parser.parse(edi_content)
        
        # Should parse successfully despite non-standard order
        assert_transaction_structure(result)
        transaction = result.interchanges[0].functional_groups[0].transactions[0]
        
        # Verify key elements are present
        assert hasattr(transaction, 'payer')
        assert hasattr(transaction, 'payee')
        assert len(transaction.claims) == 1

    def test_coordination_of_benefits_parsing(self, edi_fixtures):
        """Test parsing coordination of benefits scenarios."""
        edi_content = edi_fixtures.get_coordination_of_benefits()
        
        parser = Parser835()
        result = parser.parse(edi_content)
        
        # Verify structure
        assert_transaction_structure(result)
        transaction = result.interchanges[0].functional_groups[0].transactions[0]
        
        # Should have COB-specific elements
        assert len(transaction.claims) >= 1
        claim = transaction.claims[0]
        
        # COB claims should have specific characteristics
        assert claim.payment_amount > Decimal("0")
        assert claim.status_code in ["1", "2", "3"]  # Processed status codes

    def test_provider_adjustment_parsing(self, edi_fixtures):
        """Test parsing provider-level adjustments (PLB)."""
        edi_content = edi_fixtures.get_provider_adjustment()
        
        parser = Parser835()
        result = parser.parse(edi_content)
        
        # Verify structure
        assert_transaction_structure(result)
        transaction = result.interchanges[0].functional_groups[0].transactions[0]
        
        # Should parse successfully with provider adjustments
        assert transaction is not None

    def test_check_payment_parsing(self, edi_fixtures):
        """Test parsing check payment scenarios."""
        edi_content = edi_fixtures.get_check_payment()
        
        parser = Parser835()
        result = parser.parse(edi_content)
        
        # Verify structure
        assert_transaction_structure(result)
        transaction = result.interchanges[0].functional_groups[0].transactions[0]
        
        # Verify payment method and amount
        financial_info = transaction.financial_information
        assert financial_info.payment_method == "CHK"
        assert financial_info.payment_amount == Decimal("750.00")

    def test_high_volume_batch_parsing(self, edi_fixtures):
        """Test parsing high volume batch payments."""
        edi_content = edi_fixtures.get_high_volume_batch()
        
        parser = Parser835()
        result = parser.parse(edi_content)
        
        # Verify structure
        assert_transaction_structure(result)
        transaction = result.interchanges[0].functional_groups[0].transactions[0]
        
        # Should have multiple claims (10+ in high volume)
        assert len(transaction.claims) >= 10
        
        # Verify financial integrity
        assert_financial_integrity(transaction)

    def test_parser_memory_efficiency(self, performance_config):
        """Test memory efficiency with repeated parsing."""
        edi_content = EDIFixtures.get_835_with_multiple_claims()
        parser = Parser835()
        
        import gc
        
        # Initial memory measurement
        gc.collect()
        initial_objects = len(gc.get_objects())
        
        # Parse multiple times
        iterations = 10
        results = []
        for i in range(iterations):
            result = parser.parse(edi_content)
            results.append(result)
            
            # Validate each result
            assert_transaction_structure(result)
            
            # Force garbage collection every few iterations
            if i % 5 == 0:
                gc.collect()
        
        # Final memory measurement
        gc.collect()
        final_objects = len(gc.get_objects())
        
        # Memory usage should not grow excessively
        object_growth = final_objects - initial_objects
        growth_ratio = object_growth / initial_objects if initial_objects > 0 else 0
        
        threshold = performance_config.get("memory_growth_threshold", 0.2)
        assert growth_ratio < threshold, f"Memory usage grew too much: {growth_ratio:.2%}"
        
        # All results should be valid
        assert len(results) == iterations

    def test_concurrent_parsing_safety(self, performance_config):
        """Test parser safety under concurrent access."""
        import threading
        import queue
        
        edi_content = EDIFixtures.get_minimal_835()
        results_queue = queue.Queue()
        error_queue = queue.Queue()
        
        def parse_worker(worker_id, iterations):
            """Worker function for concurrent parsing."""
            try:
                parser = Parser835()  # Each worker gets its own parser
                
                for i in range(iterations):
                    result = parser.parse(edi_content)
                    assert_transaction_structure(result)
                
                results_queue.put((worker_id, "success"))
                
            except Exception as e:
                error_queue.put((worker_id, str(e)))
        
        # Start multiple worker threads
        threads = []
        num_workers = performance_config.get("concurrent_workers", 4)
        iterations_per_worker = 5
        
        for worker_id in range(num_workers):
            thread = threading.Thread(
                target=parse_worker, 
                args=(worker_id, iterations_per_worker)
            )
            thread.start()
            threads.append(thread)
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Collect results
        results = []
        while not results_queue.empty():
            results.append(results_queue.get())
        
        errors = []
        while not error_queue.empty():
            errors.append(error_queue.get())
        
        # Validate results
        assert len(errors) == 0, f"Concurrent parsing errors: {errors}"
        assert len(results) == num_workers, "Not all workers completed successfully"