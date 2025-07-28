"""
Unit tests for EDI 835 AST (Abstract Syntax Tree) classes.

This module contains tests for the 835 transaction AST classes,
ensuring proper data structure and validation.
"""

import pytest
from packages.core.transactions.t835.ast import (
    Transaction835,
    FinancialInformation,
    Payer,
    Payee,
    Claim,
    Adjustment,
    Service
)
from tests.shared.assertions import assert_amount_format, assert_date_format, assert_npi_valid
from tests.shared.test_data import TestData


class Test835AST:
    """Test cases for EDI 835 AST classes."""

    def test_financial_information_creation(self):
        """Test FinancialInformation class creation and validation."""
        financial_info = FinancialInformation(
            total_paid=1500.75,
            payment_method="ACH",
            payment_date="2024-12-26"
        )
        
        assert financial_info.total_paid == 1500.75
        assert financial_info.payment_method == "ACH"
        assert financial_info.payment_date == "2024-12-26"
        
        # Test serialization
        data_dict = financial_info.to_dict()
        assert data_dict["total_paid"] == 1500.75
        assert data_dict["payment_method"] == "ACH"
        assert data_dict["payment_date"] == "2024-12-26"

    def test_payer_creation(self):
        """Test Payer class creation and validation."""
        payer = Payer(name="TEST INSURANCE COMPANY")
        
        assert payer.name == "TEST INSURANCE COMPANY"
        
        # Test serialization
        data_dict = payer.to_dict()
        assert data_dict["name"] == "TEST INSURANCE COMPANY"

    def test_payee_creation_with_npi(self):
        """Test Payee class creation with NPI validation."""
        payee = Payee(
            name="TEST MEDICAL GROUP",
            npi="1234567893"  # Valid test NPI
        )
        
        assert payee.name == "TEST MEDICAL GROUP"
        assert payee.npi == "1234567893"
        
        # Test NPI validation (if implemented in class)
        if hasattr(payee, 'validate_npi'):
            assert payee.validate_npi()

    def test_claim_creation(self):
        """Test Claim class creation and validation."""
        claim = Claim(
            claim_id="TESTCLAIM001",
            status_code=1,
            total_charge=500.00,
            total_paid=400.00,
            patient_responsibility=100.00,
            payer_control_number="PAYER123"
        )
        
        assert claim.claim_id == "TESTCLAIM001"
        assert claim.status_code == 1
        assert claim.total_charge == 500.00
        assert claim.total_paid == 400.00
        assert claim.patient_responsibility == 100.00
        assert claim.payer_control_number == "PAYER123"
        
        # Verify amounts format
        assert_amount_format(claim.total_charge)
        assert_amount_format(claim.total_paid)
        assert_amount_format(claim.patient_responsibility)

    def test_adjustment_creation(self):
        """Test Adjustment class creation and validation."""
        adjustment = Adjustment(
            group_code="CO",
            reason_code="45",
            amount=50.00,
            quantity=1.0
        )
        
        assert adjustment.group_code == "CO"
        assert adjustment.reason_code == "45"
        assert adjustment.amount == 50.00
        assert adjustment.quantity == 1.0
        
        assert_amount_format(adjustment.amount)

    def test_service_creation(self):
        """Test Service class creation and validation."""
        service = Service(
            service_code="HC:99213",
            charge_amount=250.00,
            paid_amount=200.00,
            revenue_code="011",
            service_date="2024-12-15"
        )
        
        assert service.service_code == "HC:99213"
        assert service.charge_amount == 250.00
        assert service.paid_amount == 200.00
        assert service.revenue_code == "011"
        assert service.service_date == "2024-12-15"
        
        assert_amount_format(service.charge_amount)
        assert_amount_format(service.paid_amount)
        if service.service_date:
            assert_date_format(service.service_date)

    def test_transaction_835_creation(self):
        """Test Transaction835 main class creation."""
        header = {
            "transaction_set_identifier": "835",
            "transaction_set_control_number": "0001"
        }
        
        transaction = Transaction835(header=header)
        
        assert transaction.header["transaction_set_identifier"] == "835"
        assert transaction.header["transaction_set_control_number"] == "0001"
        
        # Verify default collections are initialized
        assert isinstance(transaction.claims, list)
        assert isinstance(transaction.reference_numbers, list)
        assert isinstance(transaction.dates, list)
        assert len(transaction.claims) == 0

    def test_transaction_835_with_complete_data(self):
        """Test Transaction835 with complete data structure."""
        # Create financial information
        financial_info = FinancialInformation(
            total_paid=1000.00,
            payment_method="ACH",
            payment_date="2024-12-26"
        )
        
        # Create payer and payee
        payer = Payer(name="TEST PAYER")
        payee = Payee(name="TEST PROVIDER", npi="1234567893")
        
        # Create claim with adjustments and services
        adjustment = Adjustment(
            group_code="CO",
            reason_code="45", 
            amount=50.00,
            quantity=1.0
        )
        
        service = Service(
            service_code="HC:99213",
            charge_amount=250.00,
            paid_amount=200.00,
            revenue_code="",
            service_date="2024-12-15"
        )
        
        claim = Claim(
            claim_id="TESTCLAIM001",
            status_code=1,
            total_charge=250.00,
            total_paid=200.00,
            patient_responsibility=50.00,
            payer_control_number="PAYER123"
        )
        claim.adjustments = [adjustment]
        claim.services = [service]
        
        # Create complete transaction
        transaction = Transaction835(
            header={
                "transaction_set_identifier": "835",
                "transaction_set_control_number": "0001"
            }
        )
        transaction.financial_information = financial_info
        transaction.payer = payer
        transaction.payee = payee
        transaction.claims = [claim]
        
        # Verify complete structure
        assert transaction.financial_information.total_paid == 1000.00
        assert transaction.payer.name == "TEST PAYER"
        assert transaction.payee.name == "TEST PROVIDER"
        assert len(transaction.claims) == 1
        assert len(transaction.claims[0].adjustments) == 1
        assert len(transaction.claims[0].services) == 1

    def test_claim_financial_consistency(self):
        """Test financial consistency within claims."""
        # Create claim with service
        service = Service(
            service_code="HC:99213",
            charge_amount=250.00,
            paid_amount=200.00,
            revenue_code="",
            service_date="2024-12-15"
        )
        
        claim = Claim(
            claim_id="TESTCLAIM001",
            status_code=1,
            total_charge=250.00,
            total_paid=200.00,
            patient_responsibility=50.00,
            payer_control_number="PAYER123"
        )
        claim.services = [service]
        
        # Verify claim totals match service totals
        total_service_charges = sum(s.charge_amount for s in claim.services)
        total_service_payments = sum(s.paid_amount for s in claim.services)
        
        assert total_service_charges == claim.total_charge
        assert total_service_payments == claim.total_paid

    def test_multiple_adjustments_per_claim(self):
        """Test claims with multiple adjustments."""
        adjustments = [
            Adjustment(group_code="CO", reason_code="45", amount=25.00, quantity=1.0),
            Adjustment(group_code="PR", reason_code="1", amount=25.00, quantity=1.0),
            Adjustment(group_code="PR", reason_code="2", amount=10.00, quantity=1.0)
        ]
        
        claim = Claim(
            claim_id="TESTCLAIM002",
            status_code=1,
            total_charge=300.00,
            total_paid=240.00,
            patient_responsibility=60.00,
            payer_control_number="PAYER456"
        )
        claim.adjustments = adjustments
        
        # Verify adjustment totals
        total_adjustments = sum(adj.amount for adj in claim.adjustments)
        assert total_adjustments == 60.00  # 25 + 25 + 10
        
        # Verify adjustment groups
        group_codes = [adj.group_code for adj in claim.adjustments]
        assert "CO" in group_codes
        assert "PR" in group_codes

    def test_empty_collections_initialization(self):
        """Test that collections are properly initialized as empty."""
        transaction = Transaction835(header={})
        
        assert transaction.claims == []
        assert transaction.reference_numbers == []
        assert transaction.dates == []
        assert transaction.payer is None
        assert transaction.payee is None
        assert transaction.financial_information is None
        
        # Should be able to append to collections
        transaction.claims.append(Claim(
            claim_id="TEST",
            status_code=1,
            total_charge=100.00,
            total_paid=80.00,
            patient_responsibility=20.00,
            payer_control_number="TEST123"
        ))
        
        assert len(transaction.claims) == 1

    def test_ast_node_inheritance(self):
        """Test that AST classes properly inherit from Node base class."""
        financial_info = FinancialInformation(
            total_paid=100.00,
            payment_method="ACH",
            payment_date="2024-12-26"
        )
        
        # Should have to_dict method from Node base class
        assert hasattr(financial_info, 'to_dict')
        
        # to_dict should return a dictionary
        result = financial_info.to_dict()
        assert isinstance(result, dict)
        assert 'total_paid' in result