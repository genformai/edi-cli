"""
Unit tests for EDI 835 Payment/Reassociation (BPR/TRN) processing.

This module contains comprehensive tests for payment and reassociation functionality,
consolidated from the original payment and payment_enhanced test files.
"""

import pytest
from packages.core.transactions.t835.parser import Parser835
from tests.shared.assertions import (
    assert_date_format,
    assert_amount_format,
    assert_balances
)
from tests.shared.test_data import TestData


class Test835Payments:
    """Test cases for EDI 835 payment and reassociation functionality."""

    @pytest.fixture
    def base_835_segments(self):
        """Fixture providing base 835 segments."""
        return [
            ["ISA", "00", "", "00", "", "ZZ", "SENDER", "ZZ", "RECEIVER", "241226", "1430", "U", "00501", "000000001", "0", "P", ">"],
            ["GS", "HP", "SENDER", "RECEIVER", "20241226", "1430", "000000001", "X", "005010X221A1"],
            ["ST", "835", "0001"]
        ]

    @pytest.fixture
    def base_835_trailer(self):
        """Fixture providing base 835 trailer segments."""
        return [
            ["SE", "15", "0001"],
            ["GE", "1", "000000001"],
            ["IEA", "1", "000000001"]
        ]

    def test_ach_payment_processing(self, base_835_segments, base_835_trailer):
        """
        Test ACH payment processing (BPR01=I, BPR04=ACH).
        
        Verifies:
        - ACH payment method identification
        - Payment amount validation
        - Trace number extraction
        - Date formatting
        """
        payment_segments = [
            ["BPR", "I", "1500.75", "C", "ACH", "CCP", "01", "123456789", "DA", "987654321", "9876543210", "20241226"],
            ["TRN", "1", "EFT123456789", "1234567890"],
            ["DTM", "405", "20241226"],
            ["N1", "PR", "INSURANCE COMPANY"],
            ["N1", "PE", "PROVIDER NAME"],
            ["REF", "TJ", "1234567890"]
        ]
        
        all_segments = base_835_segments + payment_segments + base_835_trailer
        parser = Parser835(all_segments)
        result = parser.parse()
        
        # Verify payment information
        financial_tx = result.interchanges[0].functional_groups[0].transactions[0].financial_transaction
        financial_info = financial_tx.financial_information
        
        assert financial_info is not None
        assert financial_info.total_paid == 1500.75
        assert financial_info.payment_method == "ACH"
        assert_date_format(financial_info.payment_date)
        assert_amount_format(financial_info.total_paid)
        
        # Verify trace number
        assert len(financial_tx.reference_numbers) >= 1
        trace_ref = financial_tx.reference_numbers[0]
        assert trace_ref["type"] == "trace_number"
        assert trace_ref["value"] == "EFT123456789"
        
        # Verify payer/payee
        assert financial_tx.payer is not None
        assert financial_tx.payer.name == "INSURANCE COMPANY"
        assert financial_tx.payee is not None
        assert financial_tx.payee.name == "PROVIDER NAME"
        assert financial_tx.payee.npi == "1234567890"

    def test_check_payment_processing(self, base_835_segments, base_835_trailer):
        """
        Test check payment processing (BPR01=I, BPR04=CHK).
        """
        payment_segments = [
            ["BPR", "I", "2500.00", "C", "CHK", "", "", "", "", "", "", "20241227"],
            ["TRN", "1", "CHECK987654", "1234567890"],
            ["DTM", "405", "20241227"],
            ["N1", "PR", "CHECK PAYER COMPANY"],
            ["N1", "PE", "CHECK PROVIDER"]
        ]
        
        all_segments = base_835_segments + payment_segments + base_835_trailer
        parser = Parser835(all_segments)
        result = parser.parse()
        
        # Verify check payment
        financial_info = result.interchanges[0].functional_groups[0].transactions[0].financial_transaction.financial_information
        
        assert financial_info.total_paid == 2500.00
        assert financial_info.payment_method == "CHK"
        assert_date_format(financial_info.payment_date)

    def test_zero_payment_notification(self, base_835_segments, base_835_trailer):
        """
        Test zero payment notification (BPR02=0.00).
        """
        payment_segments = [
            ["BPR", "H", "0.00", "C", "ACH", "", "", "", "", "", "", "20241228"],
            ["TRN", "1", "ZERO123", "1234567890"],
            ["DTM", "405", "20241228"],
            ["N1", "PR", "ZERO PAYMENT PAYER"],
            ["N1", "PE", "ZERO PAYMENT PROVIDER"]
        ]
        
        all_segments = base_835_segments + payment_segments + base_835_trailer
        parser = Parser835(all_segments)
        result = parser.parse()
        
        # Verify zero payment
        financial_info = result.interchanges[0].functional_groups[0].transactions[0].financial_transaction.financial_information
        
        assert financial_info.total_paid == 0.00
        assert financial_info.payment_method == "ACH"

    def test_multiple_trace_numbers(self, base_835_segments, base_835_trailer):
        """
        Test handling of multiple trace/reference numbers.
        """
        payment_segments = [
            ["BPR", "I", "1000.00", "C", "ACH", "", "", "", "", "", "", "20241226"],
            ["TRN", "1", "PRIMARY123", "1234567890"],
            ["TRN", "1", "SECONDARY456", "1234567890"],
            ["DTM", "405", "20241226"],
            ["REF", "EV", "ADDITIONAL789"],
            ["N1", "PR", "MULTI TRACE PAYER"]
        ]
        
        all_segments = base_835_segments + payment_segments + base_835_trailer
        parser = Parser835(all_segments)
        result = parser.parse()
        
        # Verify multiple trace numbers
        financial_tx = result.interchanges[0].functional_groups[0].transactions[0].financial_transaction
        
        assert len(financial_tx.reference_numbers) >= 2
        trace_values = [ref["value"] for ref in financial_tx.reference_numbers]
        assert "PRIMARY123" in trace_values
        assert "SECONDARY456" in trace_values

    def test_payment_with_production_date(self, base_835_segments, base_835_trailer):
        """
        Test payment with production date (DTM*405).
        """
        payment_segments = [
            ["BPR", "I", "750.50", "C", "ACH", "", "", "", "", "", "", "20241226"],
            ["TRN", "1", "PROD123", "1234567890"],
            ["DTM", "405", "20241225"],  # Production date
            ["DTM", "009", "20241226"],  # Processing date
            ["N1", "PR", "PRODUCTION PAYER"]
        ]
        
        all_segments = base_835_segments + payment_segments + base_835_trailer
        parser = Parser835(all_segments)
        result = parser.parse()
        
        # Verify dates
        financial_tx = result.interchanges[0].functional_groups[0].transactions[0].financial_transaction
        
        assert len(financial_tx.dates) >= 1
        production_date = next((d for d in financial_tx.dates if d["type"] == "production_date"), None)
        assert production_date is not None
        assert_date_format(production_date["date"])

    def test_payment_method_variations(self, base_835_segments, base_835_trailer):
        """
        Test different payment method variations.
        """
        test_cases = [
            ("ACH", "Automated Clearing House"),
            ("CHK", "Check"),
            ("FWT", "Federal Wire Transfer"),
            ("BOP", "Financial Institution Option")
        ]
        
        for payment_method, description in test_cases:
            payment_segments = [
                ["BPR", "I", "100.00", "C", payment_method, "", "", "", "", "", "", "20241226"],
                ["TRN", "1", f"TRACE_{payment_method}", "1234567890"]
            ]
            
            all_segments = base_835_segments + payment_segments + base_835_trailer
            parser = Parser835(all_segments)
            result = parser.parse()
            
            # Verify payment method
            financial_info = result.interchanges[0].functional_groups[0].transactions[0].financial_transaction.financial_information
            assert financial_info.payment_method == payment_method

    def test_payment_with_banking_details(self, base_835_segments, base_835_trailer):
        """
        Test payment with complete banking details in BPR segment.
        """
        payment_segments = [
            ["BPR", "I", "5000.00", "C", "ACH", "CCP", "01", "123456789", "DA", "987654321", "PAYERACCOUNT", "20241226"],
            ["TRN", "1", "BANK123456", "1234567890"],
            ["DTM", "405", "20241226"]
        ]
        
        all_segments = base_835_segments + payment_segments + base_835_trailer
        parser = Parser835(all_segments)
        result = parser.parse()
        
        # Verify payment processed successfully with banking details
        financial_info = result.interchanges[0].functional_groups[0].transactions[0].financial_transaction.financial_information
        
        assert financial_info.total_paid == 5000.00
        assert financial_info.payment_method == "ACH"
        assert_date_format(financial_info.payment_date)

    def test_invalid_payment_amount(self, base_835_segments, base_835_trailer):
        """
        Test handling of invalid payment amounts.
        """
        payment_segments = [
            ["BPR", "I", "INVALID", "C", "ACH", "", "", "", "", "", "", "20241226"],
            ["TRN", "1", "INVALID123", "1234567890"]
        ]
        
        all_segments = base_835_segments + payment_segments + base_835_trailer
        parser = Parser835(all_segments)
        result = parser.parse()
        
        # Parser should handle gracefully, likely defaulting to 0.0
        financial_info = result.interchanges[0].functional_groups[0].transactions[0].financial_transaction.financial_information
        assert financial_info.total_paid == 0.0

    def test_payment_date_formats(self, base_835_segments, base_835_trailer):
        """
        Test various payment date formats.
        """
        test_dates = [
            "20241226",  # Standard CCYYMMDD
            "20241231",  # Year end
            "20240229",  # Leap year
        ]
        
        for test_date in test_dates:
            payment_segments = [
                ["BPR", "I", "100.00", "C", "ACH", "", "", "", "", "", "", test_date],
                ["TRN", "1", f"DATE_{test_date}", "1234567890"]
            ]
            
            all_segments = base_835_segments + payment_segments + base_835_trailer
            parser = Parser835(all_segments)
            result = parser.parse()
            
            # Verify date formatting
            financial_info = result.interchanges[0].functional_groups[0].transactions[0].financial_transaction.financial_information
            assert_date_format(financial_info.payment_date)

    def test_payment_with_claims_reconciliation(self, base_835_segments, base_835_trailer):
        """
        Test payment reconciliation with claim amounts.
        """
        payment_segments = [
            ["BPR", "I", "450.00", "C", "ACH", "", "", "", "", "", "", "20241226"],
            ["TRN", "1", "RECONCILE123", "1234567890"],
            ["CLP", "CLAIM001", "1", "200.00", "150.00", "50.00", "MC", "PAYER123", "11"],
            ["CLP", "CLAIM002", "1", "400.00", "300.00", "100.00", "MC", "PAYER124", "11"]
        ]
        
        all_segments = base_835_segments + payment_segments + base_835_trailer
        parser = Parser835(all_segments)
        result = parser.parse()
        
        # Verify payment reconciliation
        financial_tx = result.interchanges[0].functional_groups[0].transactions[0].financial_transaction
        
        # Calculate total claim payments
        total_claim_payments = sum(claim.total_paid for claim in financial_tx.claims)
        
        # Should match BPR payment amount
        assert financial_tx.financial_information.total_paid == 450.00
        assert total_claim_payments == 450.00  # 150.00 + 300.00

    def test_negative_payment_adjustment(self, base_835_segments, base_835_trailer):
        """
        Test handling of negative payment (recoupment).
        """
        payment_segments = [
            ["BPR", "I", "-250.00", "C", "ACH", "", "", "", "", "", "", "20241226"],
            ["TRN", "1", "RECOUP123", "1234567890"],
            ["DTM", "405", "20241226"]
        ]
        
        all_segments = base_835_segments + payment_segments + base_835_trailer
        parser = Parser835(all_segments)
        result = parser.parse()
        
        # Verify negative payment
        financial_info = result.interchanges[0].functional_groups[0].transactions[0].financial_transaction.financial_information
        assert financial_info.total_paid == -250.00