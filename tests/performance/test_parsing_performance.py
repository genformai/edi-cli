"""
Performance tests for EDI parsing operations.

This module contains performance regression tests and benchmarks
for critical EDI parsing operations.
"""

import pytest
import time
from decimal import Decimal
from packages.core.parser_835 import Parser835
from tests.fixtures import EDIFixtures, IntegrationScenarios


class TestParsingPerformance:
    """Performance tests for EDI parsing operations."""

    def test_simple_835_parsing_performance(self):
        """Test performance of simple 835 parsing."""
        edi_content = EDIFixtures.get_minimal_835()
        parser = Parser835()
        
        # Warm up
        parser.parse(edi_content)
        
        # Measure performance
        start_time = time.time()
        iterations = 100
        
        for _ in range(iterations):
            result = parser.parse(edi_content)
            assert result is not None
        
        end_time = time.time()
        total_time = end_time - start_time
        avg_time = total_time / iterations
        
        # Performance assertion (adjust threshold as needed)
        assert avg_time < 0.1, f"Simple 835 parsing too slow: {avg_time:.4f}s per parse"
        print(f"Simple 835 parsing: {avg_time:.4f}s per parse ({iterations} iterations)")

    def test_complex_835_parsing_performance(self):
        """Test performance of complex 835 parsing with multiple claims."""
        edi_content = EDIFixtures.get_835_with_multiple_claims()
        parser = Parser835()
        
        # Warm up
        parser.parse(edi_content)
        
        # Measure performance
        start_time = time.time()
        iterations = 50
        
        for _ in range(iterations):
            result = parser.parse(edi_content)
            assert result is not None
            assert len(result.interchanges[0].functional_groups[0].transactions[0].claims) >= 2
        
        end_time = time.time()
        total_time = end_time - start_time
        avg_time = total_time / iterations
        
        # Performance assertion
        assert avg_time < 0.5, f"Complex 835 parsing too slow: {avg_time:.4f}s per parse"
        print(f"Complex 835 parsing: {avg_time:.4f}s per parse ({iterations} iterations)")

    def test_large_batch_parsing_performance(self):
        """Test performance of large batch file parsing."""
        edi_content = EDIFixtures.get_high_volume_batch()
        parser = Parser835()
        
        # Measure performance
        start_time = time.time()
        result = parser.parse(edi_content)
        end_time = time.time()
        
        parsing_time = end_time - start_time
        
        # Validate result
        assert result is not None
        transaction = result.interchanges[0].functional_groups[0].transactions[0]
        claim_count = len(transaction.claims)
        
        # Performance assertions
        assert parsing_time < 2.0, f"Large batch parsing too slow: {parsing_time:.4f}s"
        assert claim_count >= 5, "Should have processed multiple claims"
        
        # Calculate throughput
        claims_per_second = claim_count / parsing_time
        print(f"Large batch parsing: {parsing_time:.4f}s for {claim_count} claims ({claims_per_second:.1f} claims/sec)")

    @pytest.mark.slow
    def test_memory_usage_stability(self):
        """Test memory usage stability over repeated parsing operations."""
        edi_content = EDIFixtures.get_835_with_multiple_claims()
        parser = Parser835()
        
        import gc
        
        # Initial memory measurement
        gc.collect()
        initial_objects = len(gc.get_objects())
        
        # Parse multiple times
        iterations = 100
        for i in range(iterations):
            result = parser.parse(edi_content)
            assert result is not None
            
            # Force garbage collection every 10 iterations
            if i % 10 == 0:
                gc.collect()
        
        # Final memory measurement
        gc.collect()
        final_objects = len(gc.get_objects())
        
        # Memory usage should not grow significantly
        object_growth = final_objects - initial_objects
        growth_ratio = object_growth / initial_objects
        
        assert growth_ratio < 0.1, f"Memory usage grew too much: {growth_ratio:.2%} ({object_growth} objects)"
        print(f"Memory stability: {object_growth} objects growth over {iterations} iterations ({growth_ratio:.2%})")

    def test_concurrent_parsing_performance(self):
        """Test performance under concurrent parsing load."""
        import threading
        import queue
        
        edi_content = EDIFixtures.get_minimal_835()
        results_queue = queue.Queue()
        error_queue = queue.Queue()
        
        def parse_worker(worker_id, iterations):
            """Worker function for concurrent parsing."""
            try:
                parser = Parser835()
                worker_start = time.time()
                
                for i in range(iterations):
                    result = parser.parse(edi_content)
                    assert result is not None
                
                worker_end = time.time()
                worker_time = worker_end - worker_start
                results_queue.put((worker_id, worker_time, iterations))
                
            except Exception as e:
                error_queue.put((worker_id, str(e)))
        
        # Start multiple worker threads
        threads = []
        num_workers = 4
        iterations_per_worker = 25
        
        start_time = time.time()
        
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
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # Collect results
        results = []
        while not results_queue.empty():
            results.append(results_queue.get())
        
        errors = []
        while not error_queue.empty():
            errors.append(error_queue.get())
        
        # Validate results
        assert len(errors) == 0, f"Concurrent parsing errors: {errors}"
        assert len(results) == num_workers, "Not all workers completed"
        
        total_iterations = sum(result[2] for result in results)
        overall_throughput = total_iterations / total_time
        
        # Performance assertion
        assert overall_throughput > 100, f"Concurrent throughput too low: {overall_throughput:.1f} parses/sec"
        print(f"Concurrent parsing: {total_iterations} parses in {total_time:.4f}s ({overall_throughput:.1f} parses/sec)")


class TestValidationPerformance:
    """Performance tests for validation operations."""

    def test_npi_validation_performance(self):
        """Test NPI validation performance."""
        from packages.core.utils.validators import validate_npi
        
        test_npis = [
            "1234567893",
            "9876543210", 
            "1122334455",
            "invalid_npi",
            "",
            "123"
        ] * 1000  # Repeat for performance testing
        
        start_time = time.time()
        
        for npi in test_npis:
            result = validate_npi(npi)
            assert isinstance(result, bool)
        
        end_time = time.time()
        total_time = end_time - start_time
        validations_per_second = len(test_npis) / total_time
        
        # Performance assertion
        assert validations_per_second > 10000, f"NPI validation too slow: {validations_per_second:.0f} validations/sec"
        print(f"NPI validation: {validations_per_second:.0f} validations/sec")

    def test_amount_validation_performance(self):
        """Test amount validation performance."""
        from packages.core.utils.validators import validate_amount_format
        
        test_amounts = [
            "123.45",
            "1000.00",
            "0.00",
            "invalid",
            "",
            123.45,
            0
        ] * 1000
        
        start_time = time.time()
        
        for amount in test_amounts:
            result = validate_amount_format(amount)
            assert isinstance(result, bool)
        
        end_time = time.time()
        total_time = end_time - start_time
        validations_per_second = len(test_amounts) / total_time
        
        # Performance assertion
        assert validations_per_second > 10000, f"Amount validation too slow: {validations_per_second:.0f} validations/sec"
        print(f"Amount validation: {validations_per_second:.0f} validations/sec")


class TestFormattingPerformance:
    """Performance tests for formatting operations."""

    def test_date_formatting_performance(self):
        """Test date formatting performance."""
        from packages.core.utils.formatters import format_edi_date
        
        test_dates = [
            "20241226",
            "241226", 
            "122624",
            "12262024",
            "invalid"
        ] * 1000
        
        start_time = time.time()
        
        for date in test_dates:
            result = format_edi_date(date)
            assert isinstance(result, str)
        
        end_time = time.time()
        total_time = end_time - start_time
        formats_per_second = len(test_dates) / total_time
        
        # Performance assertion
        assert formats_per_second > 5000, f"Date formatting too slow: {formats_per_second:.0f} formats/sec"
        print(f"Date formatting: {formats_per_second:.0f} formats/sec")

    def test_time_formatting_performance(self):
        """Test time formatting performance."""
        from packages.core.utils.formatters import format_edi_time
        
        test_times = [
            "1430",
            "143045",
            "0900",
            "invalid"
        ] * 1000
        
        start_time = time.time()
        
        for time_val in test_times:
            result = format_edi_time(time_val)
            assert isinstance(result, str)
        
        end_time = time.time()
        total_time = end_time - start_time
        formats_per_second = len(test_times) / total_time
        
        # Performance assertion
        assert formats_per_second > 5000, f"Time formatting too slow: {formats_per_second:.0f} formats/sec"
        print(f"Time formatting: {formats_per_second:.0f} formats/sec")


@pytest.mark.benchmark
class TestRegressionBenchmarks:
    """Regression benchmark tests to catch performance degradation."""

    def test_baseline_835_parsing_benchmark(self):
        """Baseline benchmark for 835 parsing performance."""
        edi_content = EDIFixtures.get_minimal_835()
        parser = Parser835()
        
        # Warm up
        for _ in range(10):
            parser.parse(edi_content)
        
        # Benchmark
        start_time = time.time()
        iterations = 1000
        
        for _ in range(iterations):
            result = parser.parse(edi_content)
        
        end_time = time.time()
        total_time = end_time - start_time
        avg_time = total_time / iterations
        
        # Store benchmark result (in a real scenario, this would be compared against historical data)
        benchmark_data = {
            "test": "baseline_835_parsing",
            "avg_time_ms": avg_time * 1000,
            "iterations": iterations,
            "total_time_s": total_time
        }
        
        print(f"Benchmark - 835 parsing: {avg_time * 1000:.2f}ms per parse")
        
        # Basic performance assertion
        assert avg_time < 0.01, f"Baseline performance regression: {avg_time:.4f}s per parse"