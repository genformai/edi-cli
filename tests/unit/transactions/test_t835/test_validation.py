"""
Unit tests for EDI 835 validation rules.

This module contains tests for 835-specific validation rules,
migrated from the original validation tests.
"""

import pytest
from packages.core.transactions.t835.validators import (
    Financial835ValidationRule,
    Claim835ValidationRule,
    Adjustment835ValidationRule,
    Service835ValidationRule,
    Date835ValidationRule,
    PayerPayee835ValidationRule,
    get_835_business_rules
)
from packages.core.base.validation import ValidationSeverity, ValidationCategory
from packages.core.base.edi_ast import EdiRoot, Interchange, FunctionalGroup, Transaction
from packages.core.transactions.t835.ast import (
    Transaction835,
    FinancialInformation,
    Payer,
    Payee, 
    Claim,
    Adjustment,
    Service
)


class Test835Validation:
    """Test cases for EDI 835 validation rules."""

    @pytest.fixture
    def sample_edi_root(self):
        """Fixture providing a sample EdiRoot with 835 transaction."""
        # Create basic structure
        root = EdiRoot()
        interchange = Interchange(
            sender_id="SENDER",
            receiver_id="RECEIVER", 
            date="2024-12-26",
            time="14:30",
            control_number="000000001"
        )
        
        functional_group = FunctionalGroup(
            functional_group_code="HP",
            sender_id="SENDER",
            receiver_id="RECEIVER",
            date="2024-12-26", 
            time="14:30",
            control_number="000000001"
        )
        
        transaction = Transaction(
            transaction_set_code="835",
            control_number="0001"
        )
        
        # Create 835 transaction with sample data
        transaction_835 = Transaction835(header={
            "transaction_set_identifier": "835",
            "transaction_set_control_number": "0001"
        })
        
        # Add financial information
        transaction_835.financial_information = FinancialInformation(
            total_paid=400.00,
            payment_method="ACH",
            payment_date="2024-12-26"
        )
        
        # Add payer/payee
        transaction_835.payer = Payer(name="TEST PAYER")
        transaction_835.payee = Payee(name="TEST PROVIDER", npi="1234567893")
        
        # Add sample claim
        claim = Claim(
            claim_id="TESTCLAIM001",
            status_code=1,
            total_charge=500.00,
            total_paid=400.00,
            patient_responsibility=100.00,
            payer_control_number="PAYER123"
        )
        
        # Add sample service
        service = Service(
            service_code="HC:99213",
            charge_amount=500.00,
            paid_amount=400.00,
            revenue_code="",
            service_date="2024-12-15"
        )
        claim.services = [service]
        
        # Add sample adjustment
        adjustment = Adjustment(
            group_code="PR",
            reason_code="1",
            amount=100.00,
            quantity=1.0
        )
        claim.adjustments = [adjustment]
        
        transaction_835.claims = [claim]
        transaction.financial_transaction = transaction_835
        
        # Build hierarchy
        functional_group.transactions = [transaction]
        interchange.functional_groups = [functional_group]
        root.interchanges = [interchange]
        
        return root

    def test_financial_validation_rule(self, sample_edi_root):
        """Test Financial835ValidationRule."""
        rule = Financial835ValidationRule()
        
        # Test valid financial consistency
        result = rule.validate(sample_edi_root, {})
        assert len(result) == 0  # No errors means validation passed
        
        # Test invalid financial consistency
        # Modify claim to have inconsistent totals
        claim = sample_edi_root.interchanges[0].functional_groups[0].transactions[0].financial_transaction.claims[0]
        claim.total_paid = 300.00  # Should be 400.00 to match financial info
        
        result = rule.validate(sample_edi_root, {})
        assert len(result) > 0  # Errors mean validation failed

    def test_claim_validation_rule(self, sample_edi_root):
        """Test Claim835ValidationRule."""
        rule = Claim835ValidationRule()
        
        # Test valid claim
        result = rule.validate(sample_edi_root, {})
        assert len(result) == 0  # No errors means validation passed
        
        # Test invalid claim - negative amounts
        claim = sample_edi_root.interchanges[0].functional_groups[0].transactions[0].financial_transaction.claims[0]
        claim.total_charge = -100.00
        
        result = rule.validate(sample_edi_root, {})
        assert len(result) > 0  # Errors mean validation failed
        
        # Reset and test paid > charge
        claim.total_charge = 100.00
        claim.total_paid = 200.00  # More than charge
        
        result = rule.validate(sample_edi_root, {})
        assert len(result) > 0  # Errors mean validation failed

    def test_adjustment_validation_rule(self, sample_edi_root):
        """Test Adjustment835ValidationRule."""
        rule = Adjustment835ValidationRule()
        
        # Test valid adjustment
        result = rule.validate(sample_edi_root, {})
        assert len(result) == 0  # No errors means validation passed
        
        # Test invalid adjustment - invalid group code
        adjustment = sample_edi_root.interchanges[0].functional_groups[0].transactions[0].financial_transaction.claims[0].adjustments[0]
        adjustment.group_code = "INVALID"
        
        result = rule.validate(sample_edi_root, {})
        assert len(result) > 0  # Errors mean validation failed
        
        # Reset and test negative amount
        adjustment.group_code = "PR"
        adjustment.amount = -50.00
        
        result = rule.validate(sample_edi_root, {})
        assert len(result) > 0  # Errors mean validation failed

    def test_service_validation_rule(self, sample_edi_root):
        """Test Service835ValidationRule."""
        rule = Service835ValidationRule()
        
        # Test valid service
        result = rule.validate(sample_edi_root, {})
        assert len(result) == 0  # No errors means validation passed
        
        # Test invalid service - negative amounts
        service = sample_edi_root.interchanges[0].functional_groups[0].transactions[0].financial_transaction.claims[0].services[0]
        service.charge_amount = -100.00
        
        result = rule.validate(sample_edi_root, {})
        assert len(result) > 0  # Errors mean validation failed
        
        # Reset and test paid > charge
        service.charge_amount = 100.00
        service.paid_amount = 200.00
        
        result = rule.validate(sample_edi_root, {})
        assert len(result) > 0  # Errors mean validation failed

    def test_date_validation_rule(self, sample_edi_root):
        """Test Date835ValidationRule.""" 
        rule = Date835ValidationRule()
        
        # Test valid dates
        result = rule.validate(sample_edi_root, {})
        assert len(result) == 0  # No errors means validation passed
        
        # Test invalid date format
        interchange = sample_edi_root.interchanges[0]
        interchange.date = "INVALID_DATE"
        
        result = rule.validate(sample_edi_root, {})
        assert len(result) > 0  # Errors mean validation failed

    def test_payer_payee_validation_rule(self, sample_edi_root):
        """Test PayerPayee835ValidationRule."""
        rule = PayerPayee835ValidationRule()
        
        # Test valid payer/payee
        result = rule.validate(sample_edi_root, {})
        assert len(result) == 0  # No errors means validation passed
        
        # Test missing payer name
        transaction_835 = sample_edi_root.interchanges[0].functional_groups[0].transactions[0].financial_transaction
        transaction_835.payer.name = ""
        
        result = rule.validate(sample_edi_root, {})
        assert len(result) > 0  # Errors mean validation failed
        
        # Reset and test invalid NPI
        transaction_835.payer.name = "TEST PAYER"
        transaction_835.payee.npi = "INVALID_NPI"
        
        result = rule.validate(sample_edi_root, {})
        assert len(result) > 0  # Errors mean validation failed

    def test_get_835_business_rules(self):
        """Test get_835_business_rules function."""
        rules = get_835_business_rules()
        
        assert isinstance(rules, list)
        assert len(rules) > 0
        
        # Verify all rules are ValidationRule instances
        for rule in rules:
            assert hasattr(rule, 'validate')
            assert hasattr(rule, 'rule_id')
            assert hasattr(rule, 'severity')
            assert hasattr(rule, 'category')
        
        # Verify specific rules are included
        rule_ids = [rule.rule_id for rule in rules]
        assert "835_FINANCIAL_CONSISTENCY" in rule_ids
        assert "835_CLAIM_VALIDATION" in rule_ids
        assert "835_ADJUSTMENT_VALIDATION" in rule_ids
        assert "835_SERVICE_VALIDATION" in rule_ids
        assert "835_DATE_VALIDATION" in rule_ids
        assert "835_PAYER_PAYEE_VALIDATION" in rule_ids

    def test_validation_rule_metadata(self):
        """Test validation rule metadata and configuration."""
        # Test financial rule metadata
        financial_rule = Financial835ValidationRule()
        assert financial_rule.rule_id == "835_FINANCIAL_CONSISTENCY"
        assert financial_rule.severity == ValidationSeverity.ERROR
        assert financial_rule.category == ValidationCategory.BUSINESS
        assert "Financial amounts must be consistent" in financial_rule.description
        
        # Test claim rule metadata  
        claim_rule = Claim835ValidationRule()
        assert claim_rule.rule_id == "835_CLAIM_VALIDATION"
        assert claim_rule.severity == ValidationSeverity.ERROR
        assert claim_rule.category == ValidationCategory.BUSINESS
        
        # Test adjustment rule metadata
        adjustment_rule = Adjustment835ValidationRule()
        assert adjustment_rule.rule_id == "835_ADJUSTMENT_VALIDATION"
        assert adjustment_rule.severity == ValidationSeverity.WARNING
        assert adjustment_rule.category == ValidationCategory.BUSINESS

    def test_empty_transaction_validation(self):
        """Test validation with empty/minimal transaction."""
        # Create minimal EdiRoot
        root = EdiRoot()
        interchange = Interchange("SENDER", "RECEIVER", "2024-12-26", "14:30", "000000001")
        functional_group = FunctionalGroup("HP", "SENDER", "RECEIVER", "2024-12-26", "14:30", "000000001")
        transaction = Transaction("835", "0001")
        
        # Minimal 835 transaction
        transaction_835 = Transaction835(header={"transaction_set_identifier": "835"})
        transaction.financial_transaction = transaction_835
        
        functional_group.transactions = [transaction]
        interchange.functional_groups = [functional_group]
        root.interchanges = [interchange]
        
        # Test rules with minimal data
        rules = get_835_business_rules()
        
        for rule in rules:
            # Most rules should handle empty data gracefully
            try:
                result = rule.validate(root, {})
                assert isinstance(result, list)  # Should return list of errors
            except Exception as e:
                pytest.fail(f"Rule {rule.rule_id} failed on empty data: {e}")

    def test_multiple_claims_validation(self, sample_edi_root):
        """Test validation with multiple claims."""
        transaction_835 = sample_edi_root.interchanges[0].functional_groups[0].transactions[0].financial_transaction
        
        # Add second claim
        claim2 = Claim(
            claim_id="TESTCLAIM002",
            status_code=1,
            total_charge=300.00,
            total_paid=250.00,
            patient_responsibility=50.00,
            payer_control_number="PAYER456"
        )
        
        service2 = Service(
            service_code="HC:85025",
            charge_amount=300.00,
            paid_amount=250.00,
            revenue_code="",
            service_date="2024-12-15"
        )
        claim2.services = [service2]
        
        adjustment2 = Adjustment(
            group_code="PR",
            reason_code="1",
            amount=50.00,
            quantity=1.0
        )
        claim2.adjustments = [adjustment2]
        
        transaction_835.claims.append(claim2)
        
        # Update financial total to match both claims
        transaction_835.financial_information.total_paid = 650.00  # 400 + 250
        
        # Test validation with multiple claims
        financial_rule = Financial835ValidationRule()
        result = financial_rule.validate(sample_edi_root, {})
        assert len(result) == 0  # No errors means validation passed