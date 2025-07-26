"""
Migration examples showing how to convert from old fixtures to new fixture system.

This file demonstrates concrete examples of migrating existing test cases
to use the enhanced fixture architecture.
"""

from decimal import Decimal
import pytest

# Old way (still works)
from .legacy_fixtures import EDIFixtures

# New way (recommended)
from . import (
    EDI835Builder, PaymentScenarios, ClaimScenarios, ErrorScenarios,
    data_loader
)


class MigrationExamples:
    """Examples showing migration from old to new fixture system."""
    
    # EXAMPLE 1: Simple fixture replacement
    
    def test_old_way_minimal_835(self):
        """Old way: Using static fixture."""
        # This still works but is less flexible
        edi_content = EDIFixtures.get_minimal_835()
        
        # Test logic would go here
        assert "BPR*I*1000.00" in edi_content
        assert "INSURANCE COMPANY" in edi_content
    
    def test_new_way_minimal_835(self):
        """New way: Using builder pattern."""
        # More flexible and realistic
        edi_content = (EDI835Builder()
                      .with_realistic_payer()
                      .with_realistic_payee()
                      .with_ach_payment(Decimal("1000.00"))
                      .with_primary_claim(charge=Decimal("1200.00"), paid=Decimal("1000.00"))
                      .build())
        
        # Same test logic, but now with realistic data
        assert "BPR*I*1000.00" in edi_content
        # Payer name will be realistic like "AETNA BETTER HEALTH"
        assert len([line for line in edi_content.split('~') if 'N1*PR*' in line]) > 0
    
    # EXAMPLE 2: Scenario-based testing
    
    def test_old_way_multiple_claims(self):
        """Old way: Using static multi-claim fixture."""
        edi_content = EDIFixtures.get_835_with_multiple_claims()
        
        # Count claims
        claim_lines = [line for line in edi_content.split('~') if line.startswith('CLP*')]
        assert len(claim_lines) == 3
    
    def test_new_way_multiple_claims_scenario(self):
        """New way: Using pre-built scenario."""
        edi_content = PaymentScenarios.mixed_claim_statuses().build()
        
        # Same test logic but with more realistic and varied data
        claim_lines = [line for line in edi_content.split('~') if line.startswith('CLP*')]
        assert len(claim_lines) >= 3  # Scenario might have more claims
    
    def test_new_way_multiple_claims_custom(self):
        """New way: Building custom multi-claim scenario."""
        builder = (EDI835Builder()
                  .with_realistic_payer()
                  .with_realistic_payee()
                  .with_ach_payment(Decimal("2400.00")))
        
        # Add specific claims for test case
        builder.with_primary_claim("TEST001", Decimal("800.00"), Decimal("720.00"), Decimal("80.00"))
        builder.with_primary_claim("TEST002", Decimal("900.00"), Decimal("810.00"), Decimal("90.00"))
        builder.with_denied_claim("TEST003", Decimal("600.00"), "29")
        
        edi_content = builder.build()
        
        # Verify specific test conditions
        assert "CLP*TEST001*1*800.00*720.00*80.00" in edi_content
        assert "CLP*TEST002*1*900.00*810.00*90.00" in edi_content
        assert "CLP*TEST003*4*600.00*0.00*0.00" in edi_content
    
    # EXAMPLE 3: Converting specific test case from actual test file
    
    def test_old_way_payment_method_check(self):
        """Old way: Manual segment construction for check payment."""
        # This is how test_835_pmt_002_check_payment currently works
        segments = [
            "BPR*I*850.25*C*CHK*CCP*01*123456789*DA*987654321*CHK001234*20241226~",
            "TRN*1*CHK001234*1234567890~",
            "N1*PR*INSURANCE COMPANY~", 
            "N1*PE*PROVIDER NAME~",
            "REF*TJ*1234567890~",
            "CLP*CLAIM001*1*1000.00*850.25*149.75*MC*456789*11~"
        ]
        
        # Would need to wrap with headers/trailers
        content = "".join(segments)
        
        assert "BPR*I*850.25*C*CHK" in content
        assert "CHK001234" in content
    
    def test_new_way_payment_method_check(self):
        """New way: Using builder for check payment."""
        edi_content = (EDI835Builder()
                      .with_realistic_payer()
                      .with_realistic_payee()
                      .with_check_payment(Decimal("850.25"), "CHK001234")
                      .with_primary_claim("CLAIM001", Decimal("1000.00"), Decimal("850.25"), Decimal("149.75"))
                      .with_trace_number("CHK001234")
                      .build())
        
        # Same assertions work
        assert "BPR*I*850.25*C*CHK" in edi_content
        assert "CHK001234" in edi_content
        # But now has complete EDI structure with realistic payer/payee names
    
    def test_new_way_payment_method_check_scenario(self):
        """New way: Using pre-built check payment scenario."""
        edi_content = PaymentScenarios.check_payment_large().build()
        
        # Test that it's a check payment
        assert "*CHK*" in edi_content
        # Extract and verify check reference
        bpr_lines = [line for line in edi_content.split('~') if line.startswith('BPR*')]
        assert len(bpr_lines) > 0
        bpr_parts = bpr_lines[0].split('*')
        assert bpr_parts[4] == "CHK"  # Payment method
    
    # EXAMPLE 4: Error condition testing
    
    def test_old_way_denied_claim(self):
        """Old way: Using static denied claim fixture."""
        edi_content = EDIFixtures.get_835_denied_claim()
        
        # Verify no payment
        assert "BPR*I*0.00*C*NON" in edi_content
        assert "CAS*CO*29*500.00" in edi_content
    
    def test_new_way_denied_claim_scenario(self):
        """New way: Using denial scenario."""
        edi_content = ClaimScenarios.denied_claim().build()
        
        # Same test logic but with more realistic context
        assert "*NON" in edi_content or "BPR*I*0.00" in edi_content
        # Adjustment reasons will be present
        assert "CAS*" in edi_content
    
    def test_new_way_error_conditions(self):
        """New way: Using dedicated error scenarios."""
        # Test various error conditions
        invalid_npi = ErrorScenarios.invalid_npi_transaction().build()
        assert "INVALID" in invalid_npi or "BAD" in invalid_npi
        
        missing_segments = ErrorScenarios.missing_required_segments().build()
        # This will have minimal required data
        
        negative_amounts = ErrorScenarios.negative_payment_amounts().build()
        assert "*-" in negative_amounts  # Should contain negative amount
    
    # EXAMPLE 5: Using realistic data
    
    def test_new_way_realistic_payers(self):
        """Demonstrate using realistic payer data."""
        # Get specific payer types
        insurance_payer = data_loader.get_random_payer(payer_type="insurance")
        government_payer = data_loader.get_random_payer(payer_type="government")
        
        # Build EDI with specific payer
        edi_content = (EDI835Builder()
                      .with_payer(insurance_payer['name'], insurance_payer['id'])
                      .with_realistic_payee()
                      .with_ach_payment(Decimal("1000.00"))
                      .with_primary_claim(charge=Decimal("1200.00"), paid=Decimal("1000.00"))
                      .build())
        
        # Will contain actual payer name like "AETNA BETTER HEALTH"
        assert insurance_payer['name'] in edi_content
        assert insurance_payer['id'] in edi_content
        
        # Government payer example
        gov_edi = (EDI835Builder()
                  .with_payer(government_payer['name'], government_payer['id'])
                  .with_realistic_payee()
                  .with_ach_payment(Decimal("500.00"))
                  .with_primary_claim(charge=Decimal("600.00"), paid=Decimal("500.00"))
                  .build())
        
        # Might contain "MEDICARE PART B" or "MEDICAID"
        assert government_payer['name'] in gov_edi
    
    def test_new_way_realistic_procedures(self):
        """Demonstrate using realistic procedure and diagnosis codes."""
        # Get related diagnosis and procedure
        diagnosis, procedure, charge = data_loader.get_related_diagnosis_and_procedure("cardiovascular")
        
        # Build EDI with realistic medical codes
        edi_content = (EDI835Builder()
                      .with_realistic_payer()
                      .with_realistic_payee()
                      .with_ach_payment(charge * Decimal("0.85"))  # 85% payment
                      .with_primary_claim(charge=charge, paid=charge * Decimal("0.85"))
                      .with_custom_segment(f"SVC*HC:{procedure}*{charge}*{charge * Decimal('0.85')}*UN*1~")
                      .build())
        
        # Contains real procedure code like "99214" or "93307"
        assert procedure in edi_content
        # May also contain diagnosis reference depending on transaction type
    
    # EXAMPLE 6: Integration testing
    
    def test_new_way_complete_workflow(self):
        """Demonstrate complete patient workflow testing."""
        from .scenarios.integration_scenarios import IntegrationScenarios
        
        # Get complete workflow
        workflow = IntegrationScenarios.complete_patient_workflow()
        
        # Test each step
        eligibility_270 = workflow["eligibility_inquiry"].build()
        assert "ST*270*" in eligibility_270
        assert "EQ*30" in eligibility_270  # Health benefit inquiry
        
        claim_837 = workflow["claim_submission"].build()
        assert "ST*837*" in claim_837
        assert "CLM*" in claim_837  # Claim information
        
        status_276 = workflow["status_inquiry"].build()
        assert "ST*276*" in status_276
        assert "TRN*1*" in status_276  # Trace number
        
        payment_835 = workflow["payment_advice"].build()
        assert "ST*835*" in payment_835
        assert "BPR*I*" in payment_835  # Payment info
        
        # All should reference same patient
        # (Implementation would extract and compare patient identifiers)


# Pytest fixtures for demonstration
@pytest.fixture
def realistic_payer():
    """Fixture providing realistic payer data."""
    return data_loader.get_random_payer()


@pytest.fixture  
def cardiology_scenario():
    """Fixture providing cardiology-specific EDI scenario."""
    return (EDI835Builder()
           .with_realistic_payer()
           .with_provider("HEART SPECIALISTS", specialty="207RC0000X")
           .with_ach_payment(Decimal("1500.00"))
           .with_primary_claim(charge=Decimal("1800.00"), paid=Decimal("1500.00"))
           .with_diagnosis("I25.10")  # Coronary artery disease
           .with_service("93307", Decimal("800.00"))  # Echocardiogram
           .with_service("99243", Decimal("300.00"))) # Consultation


class DemonstrateMigrationPatterns:
    """Show common migration patterns for different test types."""
    
    def test_with_realistic_fixture(self, realistic_payer):
        """Show how to use realistic data fixtures."""
        edi_content = (EDI835Builder()
                      .with_payer(realistic_payer['name'], realistic_payer['id'])
                      .with_realistic_payee()
                      .with_ach_payment(Decimal("1000.00"))
                      .build())
        
        assert realistic_payer['name'] in edi_content
    
    def test_with_custom_scenario_fixture(self, cardiology_scenario):
        """Show how to use custom scenario fixtures."""
        edi_content = cardiology_scenario.build()
        
        assert "I25.10" in edi_content  # Diagnosis
        assert "93307" in edi_content   # Procedure
        assert "HEART SPECIALISTS" in edi_content