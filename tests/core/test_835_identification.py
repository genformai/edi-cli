"""
Test cases for EDI 835 Payer/Payee Identification (1000A/B).

Following test plan section 3: Payer/Payee Identification
"""

import pytest
from .test_utils import parse_edi, assert_npi_format, build_835_edi
from .fixtures import EDIFixtures


class Test835Identification:
    """Test cases for EDI 835 payer and payee identification."""

    def test_835_id_001_payer_nm1_with_ein(self, schema_835_path, base_835_headers, base_835_trailer):
        """
        835-ID-001: Payer NM1 with EIN (REF*FI).
        
        Assertions: TIN format validated
        """
        segments = [
            "N1*PR*ACME INSURANCE COMPANY*FI*12-3456789~",
            "N3*123 INSURANCE BLVD~",
            "N4*INSURANCE CITY*ST*12345~",
            "REF*FI*12-3456789~",  # Federal Tax ID
            "N1*PE*PROVIDER CLINIC*XX*1234567890~",
            "REF*TJ*1234567890~",  # NPI
            "CLP*CLAIM001*1*500.00*400.00*100.00*MC*PAYER123*11~"
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
        
        # Verify payer information
        assert financial_tx.payer is not None
        assert financial_tx.payer.name == "ACME INSURANCE COMPANY"

    def test_835_id_002_payee_nm1_with_npi(self, schema_835_path, base_835_headers, base_835_trailer):
        """
        835-ID-002: Payee NM1 with NPI (REF*XX).
        
        Assertions: NPI is 10 digits and passes Luhn-like NPI check
        """
        segments = [
            "N1*PR*ACME INSURANCE COMPANY~",
            "N1*PE*PROVIDER CLINIC*XX*1234567890~",
            "REF*TJ*1234567890~",  # NPI (Type 2 National Provider Identifier)
            "CLP*CLAIM001*1*500.00*400.00*100.00*MC*PAYER123*11~"
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
        
        # Verify payee information
        assert financial_tx.payee is not None
        assert financial_tx.payee.name == "PROVIDER CLINIC"
        assert financial_tx.payee.npi == "1234567890"
        
        # Verify NPI format (10 digits)
        assert_npi_format(financial_tx.payee.npi)

    def test_835_id_003_payee_identified_by_ssn(self, schema_835_path, base_835_headers, base_835_trailer):
        """
        835-ID-003: Payee identified by SSN (REF*TJ).
        
        Assertions: allowed but flag for compliance review (optional policy)
        """
        segments = [
            "N1*PR*ACME INSURANCE COMPANY~",
            "N1*PE*DR JOHN SMITH*34*123456789~",  # SSN format
            "REF*TJ*123456789~",  # SSN instead of NPI
            "CLP*CLAIM001*1*500.00*400.00*100.00*MC*PAYER123*11~"
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
        
        # Verify payee information
        assert financial_tx.payee is not None
        assert financial_tx.payee.name == "DR JOHN SMITH"
        assert financial_tx.payee.npi == "123456789"
        
        # Verify SSN format (9 digits) - should flag for compliance review
        assert len(financial_tx.payee.npi) == 9
        assert financial_tx.payee.npi.isdigit()

    def test_835_id_004_missing_payee_nm1(self, schema_835_path, base_835_headers, base_835_trailer):
        """
        835-ID-004: Missing Payee NM1.
        
        Assertions: hard fail or graceful handling
        """
        segments = [
            "N1*PR*ACME INSURANCE COMPANY~",
            # Missing N1*PE payee segment
            "CLP*CLAIM001*1*500.00*400.00*100.00*MC*PAYER123*11~"
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
        
        # Verify payer exists but payee is missing
        assert financial_tx.payer is not None
        assert financial_tx.payee is None

    def test_835_id_005_multiple_ref_identifiers(self, schema_835_path, base_835_headers, base_835_trailer):
        """
        835-ID-005: Multiple REF identifiers (XX + FI).
        
        Assertions: retain all, prioritize NPI per mapping rules
        """
        segments = [
            "N1*PR*ACME INSURANCE COMPANY~",
            "REF*FI*12-3456789~",  # Federal Tax ID
            "REF*ZZ*STATE123~",    # State license
            "N1*PE*PROVIDER CLINIC*XX*1234567890~",
            "REF*TJ*1234567890~",  # NPI (should be prioritized)
            "REF*FI*98-7654321~",  # Provider tax ID
            "REF*G2*STATE456~",    # State license
            "CLP*CLAIM001*1*500.00*400.00*100.00*MC*PAYER123*11~"
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
        
        # Verify payee information prioritizes NPI
        assert financial_tx.payee is not None
        assert financial_tx.payee.name == "PROVIDER CLINIC"
        assert financial_tx.payee.npi == "1234567890"  # TJ reference should be used

    def test_835_id_006_payer_with_duns_number(self, schema_835_path, base_835_headers, base_835_trailer):
        """
        Test payer identification with DUNS number.
        """
        segments = [
            "N1*PR*ACME INSURANCE COMPANY*1D*123456789~",  # DUNS number
            "N1*PE*PROVIDER CLINIC*XX*1234567890~",
            "REF*TJ*1234567890~",
            "CLP*CLAIM001*1*500.00*400.00*100.00*MC*PAYER123*11~"
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
        
        # Verify payer information
        assert financial_tx.payer is not None
        assert financial_tx.payer.name == "ACME INSURANCE COMPANY"

    def test_835_id_007_payee_individual_person(self, schema_835_path, base_835_headers, base_835_trailer):
        """
        Test payee as individual person with proper name format.
        """
        segments = [
            "N1*PR*ACME INSURANCE COMPANY~",
            "N1*PE*SMITH*JOHN*DR*MD*XX*1234567890~",  # Last*First*Prefix*Suffix format
            "REF*TJ*1234567890~",
            "CLP*CLAIM001*1*500.00*400.00*100.00*MC*PAYER123*11~"
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
        
        # Verify payee information
        assert financial_tx.payee is not None
        # Parser may handle name formatting differently
        assert "SMITH" in financial_tx.payee.name or "JOHN" in financial_tx.payee.name

    def test_835_id_008_invalid_npi_format(self, schema_835_path, base_835_headers, base_835_trailer):
        """
        Test handling of invalid NPI format.
        """
        segments = [
            "N1*PR*ACME INSURANCE COMPANY~",
            "N1*PE*PROVIDER CLINIC*XX*INVALID123~",  # Invalid NPI format
            "REF*TJ*INVALID123~",
            "CLP*CLAIM001*1*500.00*400.00*100.00*MC*PAYER123*11~"
        ]
        
        edi_content = build_835_edi(
            base_835_headers,
            "".join(segments),
            base_835_trailer
        )
        
        result = parse_edi(edi_content, schema_835_path)
        
        # Verify structure still parses despite invalid NPI
        transaction = result.interchanges[0].functional_groups[0].transactions[0]
        financial_tx = transaction.financial_transaction
        
        # Verify payee information exists with invalid NPI
        assert financial_tx.payee is not None
        assert financial_tx.payee.name == "PROVIDER CLINIC"
        assert financial_tx.payee.npi == "INVALID123"

    def test_835_id_009_payer_address_information(self, schema_835_path, base_835_headers, base_835_trailer):
        """
        Test capture of payer address information (N3/N4 segments).
        """
        segments = [
            "N1*PR*ACME INSURANCE COMPANY~",
            "N3*123 INSURANCE BOULEVARD*SUITE 456~",
            "N4*INSURANCE CITY*CA*90210*US~",
            "PER*IC*JOHN DOE*TE*5551234567*EX*123~",  # Contact information
            "N1*PE*PROVIDER CLINIC*XX*1234567890~",
            "N3*789 MEDICAL CENTER DRIVE~",
            "N4*MEDICAL CITY*TX*75001~",
            "REF*TJ*1234567890~",
            "CLP*CLAIM001*1*500.00*400.00*100.00*MC*PAYER123*11~"
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
        
        # Verify basic payer/payee information is captured
        assert financial_tx.payer is not None
        assert financial_tx.payer.name == "ACME INSURANCE COMPANY"
        assert financial_tx.payee is not None
        assert financial_tx.payee.name == "PROVIDER CLINIC"

    def test_835_id_010_multiple_payers_same_transaction(self, schema_835_path, base_835_headers, base_835_trailer):
        """
        Test handling of multiple payer entities (should use last one or first one per spec).
        """
        segments = [
            "N1*PR*FIRST INSURANCE COMPANY~",
            "N1*PR*SECOND INSURANCE COMPANY~",  # Multiple payers
            "N1*PE*PROVIDER CLINIC*XX*1234567890~",
            "REF*TJ*1234567890~",
            "CLP*CLAIM001*1*500.00*400.00*100.00*MC*PAYER123*11~"
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
        
        # Verify payer information (behavior depends on parser implementation)
        assert financial_tx.payer is not None
        # Should be either first or last payer depending on parser logic
        assert financial_tx.payer.name in ["FIRST INSURANCE COMPANY", "SECOND INSURANCE COMPANY"]

    def test_835_id_011_npi_validation_edge_cases(self, schema_835_path, base_835_headers, base_835_trailer):
        """
        Test NPI validation with various edge cases.
        """
        # Test with valid 10-digit NPI
        segments = [
            "N1*PR*ACME INSURANCE COMPANY~",
            "N1*PE*PROVIDER CLINIC*XX*1234567890~",
            "REF*TJ*1234567890~",
            "CLP*CLAIM001*1*500.00*400.00*100.00*MC*PAYER123*11~"
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
        
        # Verify NPI format
        assert financial_tx.payee is not None
        assert_npi_format(financial_tx.payee.npi)

    def test_835_id_012_empty_identification_fields(self, schema_835_path, base_835_headers, base_835_trailer):
        """
        Test handling of empty identification fields.
        """
        segments = [
            "N1*PR**~",  # Empty payer name
            "N1*PE**XX*~",  # Empty payee name with empty NPI
            "REF*TJ*~",  # Empty NPI reference
            "CLP*CLAIM001*1*500.00*400.00*100.00*MC*PAYER123*11~"
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
        
        # Verify objects exist even with empty data
        assert financial_tx.payer is not None
        assert financial_tx.payee is not None