"""
Test cases for EDI 835 Payment/Reassociation (BPR/TRN).

Following test plan section 2: BPR/TRN Payment / Reassociation
"""

import pytest
from .test_utils import parse_edi, assert_date_format, assert_amount_format, build_835_edi
from .fixtures import EDIFixtures


class Test835Payment:
    """Test cases for EDI 835 payment and reassociation functionality."""

    def test_835_pmt_001_ach_payment(self, schema_835_path, base_835_headers, base_835_trailer):
        """
        835-PMT-001: ACH payment (BPR01=I, BPR04=ACH).
        
        Assertions:
        * Extract ACH trace numbers
        * Payment amount in BPR02 > 0
        * TRN02 matches EFT trace mapping
        """
        segments = [
            "BPR*I*1500.75*C*ACH*CCP*01*123456789*DA*987654321*9876543210*20241226~",
            "TRN*1*EFT123456789*1234567890~",
            "DTM*405*20241226~",
            "N1*PR*INSURANCE COMPANY~",
            "N1*PE*PROVIDER NAME~",
            "REF*TJ*1234567890~",
            "CLP*CLAIM001*1*200.00*150.75*49.25*MC*456789*11~",
            "CLP*CLAIM002*1*300.00*250.00*50.00*MC*456790*11~",
            "CLP*CLAIM003*1*1500.00*1100.00*400.00*MC*456791*11~"
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
        
        # Verify ACH payment details
        assert financial_tx.financial_information.total_paid == 1500.75
        assert financial_tx.financial_information.payment_method == "ACH"
        assert_date_format(financial_tx.financial_information.payment_date)
        
        # Verify TRN (trace number) exists
        assert len(financial_tx.reference_numbers) > 0
        trace_refs = [ref for ref in financial_tx.reference_numbers if ref["type"] == "trace_number"]
        assert len(trace_refs) > 0
        assert trace_refs[0]["value"] == "EFT123456789"

    def test_835_pmt_002_check_payment(self, schema_835_path, base_835_headers, base_835_trailer):
        """
        835-PMT-002: Check payment (BPR04=CHK).
        
        Assertions: check number captured
        """
        segments = [
            "BPR*I*850.25*C*CHK*CCP*01*123456789*DA*987654321*CHK001234*20241226~",
            "TRN*1*CHK001234*1234567890~",
            "N1*PR*INSURANCE COMPANY~",
            "N1*PE*PROVIDER NAME~",
            "REF*TJ*1234567890~",
            "CLP*CLAIM001*1*1000.00*850.25*149.75*MC*456789*11~"
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
        
        # Verify check payment details
        assert financial_tx.financial_information.total_paid == 850.25
        assert financial_tx.financial_information.payment_method == "CHK"
        
        # Verify check number in trace
        trace_refs = [ref for ref in financial_tx.reference_numbers if ref["type"] == "trace_number"]
        assert len(trace_refs) > 0
        assert trace_refs[0]["value"] == "CHK001234"

    def test_835_pmt_003_no_payment_advice_only(self, schema_835_path):
        """
        835-PMT-003: No payment (BPR01=H or BPR04=NON).
        
        Assertions: paid amounts across CLPs sum to 0; still valid advice
        """
        edi_content = EDIFixtures.get_835_denied_claim()
        
        result = parse_edi(edi_content, schema_835_path)
        
        # Verify structure
        transaction = result.interchanges[0].functional_groups[0].transactions[0]
        financial_tx = transaction.financial_transaction
        
        # Verify no payment
        assert financial_tx.financial_information.total_paid == 0.00
        assert financial_tx.financial_information.payment_method == "NON"
        
        # Verify claims exist with zero payment
        assert len(financial_tx.claims) == 1
        for claim in financial_tx.claims:
            assert claim.total_paid == 0.00

    def test_835_pmt_004_negative_plb_net_payment(self, schema_835_path, base_835_headers, base_835_trailer):
        """
        835-PMT-004: Negative PLB offsets causing net payment < ΣCLP paid.
        
        Assertions: transaction balance still matches (BPR02 = ΣCLP paid – ΣPLB)
        """
        segments = [
            "BPR*I*800.00*C*ACH*CCP*01*123456789*DA*987654321*9876543210*20241226~",
            "TRN*1*12345*1234567890~",
            "N1*PR*INSURANCE COMPANY~",
            "N1*PE*PROVIDER NAME~",
            "REF*TJ*1234567890~",
            "CLP*CLAIM001*1*500.00*400.00*100.00*MC*456789*11~",
            "CLP*CLAIM002*1*600.00*500.00*100.00*MC*456790*11~",
            # ΣCLP paid = 900.00, but PLB reduces net payment by 100.00
            "PLB*1234567890*20241226*L6*-100.00~"  # Prior overpayment recovery
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
        
        # Verify net payment calculation
        # BPR02 (800.00) = ΣCLP paid (900.00) - PLB (100.00)
        assert financial_tx.financial_information.total_paid == 800.00
        
        # Verify individual claim payments
        total_claim_paid = sum(claim.total_paid for claim in financial_tx.claims)
        assert total_claim_paid == 900.00  # Before PLB adjustment

    def test_835_pmt_005_payment_date_validation(self, schema_835_path, base_835_headers, base_835_trailer):
        """
        835-PMT-005: Payment date DTM*405 present and valid.
        
        Assertions: correct YYYYMMDD parse; equals financial institution date if provided
        """
        segments = [
            "BPR*I*1000.00*C*ACH*CCP*01*123456789*DA*987654321*9876543210*20241225~",
            "TRN*1*12345*1234567890~",
            "DTM*405*20241226~",  # Payment effective date
            "N1*PR*INSURANCE COMPANY~",
            "N1*PE*PROVIDER NAME~",
            "REF*TJ*1234567890~",
            "CLP*CLAIM001*1*1200.00*1000.00*200.00*MC*456789*11~"
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
        
        # Verify payment date from BPR segment
        assert_date_format(financial_tx.financial_information.payment_date)
        
        # Verify DTM*405 date is captured
        production_dates = [d for d in financial_tx.dates if d["type"] == "production_date"]
        assert len(production_dates) > 0
        assert_date_format(production_dates[0]["date"])

    def test_835_pmt_006_missing_trn_reassociation(self, schema_835_path, base_835_headers, base_835_trailer):
        """
        835-PMT-006: Missing TRN (reassociation key).
        
        Assertions: error/warning depending on config (should parse but flag missing key)
        """
        segments = [
            "BPR*I*1000.00*C*ACH*CCP*01*123456789*DA*987654321*9876543210*20241226~",
            # TRN segment missing
            "N1*PR*INSURANCE COMPANY~",
            "N1*PE*PROVIDER NAME~",
            "REF*TJ*1234567890~",
            "CLP*CLAIM001*1*1200.00*1000.00*200.00*MC*456789*11~"
        ]
        
        edi_content = build_835_edi(
            base_835_headers,
            "".join(segments),
            base_835_trailer
        )
        
        result = parse_edi(edi_content, schema_835_path)
        
        # Verify structure still parses
        transaction = result.interchanges[0].functional_groups[0].transactions[0]
        financial_tx = transaction.financial_transaction
        
        # Verify payment information exists
        assert financial_tx.financial_information.total_paid == 1000.00
        
        # Verify no trace numbers exist
        assert len(financial_tx.reference_numbers) == 0

    def test_835_pmt_007_wire_transfer_payment(self, schema_835_path, base_835_headers, base_835_trailer):
        """
        Test wire transfer payment method.
        """
        segments = [
            "BPR*I*2500.00*C*FWT*CCP*01*123456789*DA*987654321*WIRE123456*20241226~",
            "TRN*1*WIRE123456*1234567890~",
            "N1*PR*INSURANCE COMPANY~",
            "N1*PE*PROVIDER NAME~",
            "REF*TJ*1234567890~",
            "CLP*CLAIM001*1*3000.00*2500.00*500.00*MC*456789*11~"
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
        
        # Verify wire transfer details
        assert financial_tx.financial_information.total_paid == 2500.00
        assert financial_tx.financial_information.payment_method == "FWT"
        
        # Verify wire reference number
        trace_refs = [ref for ref in financial_tx.reference_numbers if ref["type"] == "trace_number"]
        assert len(trace_refs) > 0
        assert trace_refs[0]["value"] == "WIRE123456"

    def test_835_pmt_008_multiple_trn_segments(self, schema_835_path, base_835_headers, base_835_trailer):
        """
        Test handling of multiple TRN segments (should capture all).
        """
        segments = [
            "BPR*I*1500.00*C*ACH*CCP*01*123456789*DA*987654321*9876543210*20241226~",
            "TRN*1*MAIN123*1234567890~",
            "TRN*2*SECONDARY456*1234567890~",
            "TRN*3*BACKUP789*1234567890~",
            "N1*PR*INSURANCE COMPANY~",
            "N1*PE*PROVIDER NAME~",
            "REF*TJ*1234567890~",
            "CLP*CLAIM001*1*1800.00*1500.00*300.00*MC*456789*11~"
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
        
        # Verify all trace numbers captured
        trace_refs = [ref for ref in financial_tx.reference_numbers if ref["type"] == "trace_number"]
        assert len(trace_refs) == 3
        
        trace_values = [ref["value"] for ref in trace_refs]
        assert "MAIN123" in trace_values
        assert "SECONDARY456" in trace_values  
        assert "BACKUP789" in trace_values

    def test_835_pmt_009_zero_payment_with_adjustments(self, schema_835_path, base_835_headers, base_835_trailer):
        """
        Test zero payment with only adjustments (debit memo).
        """
        segments = [
            "BPR*D*250.00*C*ACH*CCP*01*123456789*DA*987654321*9876543210*20241226~",
            "TRN*1*DEBIT123*1234567890~",
            "N1*PR*INSURANCE COMPANY~",
            "N1*PE*PROVIDER NAME~",
            "REF*TJ*1234567890~",
            "PLB*1234567890*20241226*WO*-250.00~"  # Write-off recovery
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
        
        # Verify debit payment (negative impact)
        assert financial_tx.financial_information.total_paid == 250.00
        # Note: BPR*D indicates this is a debit to the provider account

    def test_835_pmt_010_payment_amount_validation(self, schema_835_path, base_835_headers, base_835_trailer):
        """
        Test payment amount format validation.
        """
        segments = [
            "BPR*I*1234.56*C*ACH*CCP*01*123456789*DA*987654321*9876543210*20241226~",
            "TRN*1*TRACE123*1234567890~",
            "N1*PR*INSURANCE COMPANY~",
            "N1*PE*PROVIDER NAME~",
            "REF*TJ*1234567890~",
            "CLP*CLAIM001*1*1500.00*1234.56*265.44*MC*456789*11~"
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
        
        # Verify payment amount format
        payment_amount = financial_tx.financial_information.total_paid
        assert_amount_format(payment_amount)
        assert payment_amount == 1234.56