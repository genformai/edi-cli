"""
Test suite for the EDI fixture system itself.

This module tests the fixture builders, scenarios, and data sources to ensure
they generate valid, consistent, and realistic EDI transactions.
"""

import pytest
from decimal import Decimal
from datetime import date

from . import (
    EDI835Builder, EDI270Builder, EDI276Builder, EDI837pBuilder,
    PaymentScenarios, ClaimScenarios, ErrorScenarios, IntegrationScenarios,
    data_loader, DataGenerator
)


class TestEDIBuilders:
    """Test the EDI builder classes."""
    
    def test_edi835_builder_minimal(self):
        """Test minimal 835 builder creates valid EDI."""
        builder = EDI835Builder()
        edi_content = builder.build()
        
        # Should contain basic EDI structure
        assert "ISA*" in edi_content
        assert "GS*" in edi_content
        assert "ST*835*" in edi_content
        assert "SE*" in edi_content
        assert "GE*" in edi_content
        assert "IEA*" in edi_content
        
        # Should end with proper terminator
        assert edi_content.endswith("~")
    
    def test_edi835_builder_fluent_api(self):
        """Test builder fluent API works correctly."""
        builder = (EDI835Builder()
                  .with_realistic_payer()
                  .with_realistic_payee()
                  .with_ach_payment(Decimal("1000.00"))
                  .with_primary_claim(charge=Decimal("1200.00"), paid=Decimal("1000.00")))
        
        # Should return builder instance for chaining
        assert isinstance(builder, EDI835Builder)
        
        # Should build valid EDI
        edi_content = builder.build()
        assert "BPR*I*1000.00" in edi_content
        assert "CLP*" in edi_content
    
    def test_edi270_builder_minimal(self):
        """Test minimal 270 builder creates valid EDI."""
        edi_content = EDI270Builder.minimal().build()
        
        # Should contain 270-specific structure
        assert "ST*270*" in edi_content
        assert "BHT*0022*13*" in edi_content
        assert "HL*" in edi_content
        assert "EQ*" in edi_content
    
    def test_edi276_builder_minimal(self):
        """Test minimal 276 builder creates valid EDI."""
        edi_content = EDI276Builder.minimal().build()
        
        # Should contain 276-specific structure
        assert "ST*276*" in edi_content
        assert "BHT*0019*13*" in edi_content
        assert "TRN*1*" in edi_content
        assert "REF*1K*" in edi_content
    
    def test_edi837p_builder_minimal(self):
        """Test minimal 837P builder creates valid EDI."""
        edi_content = EDI837pBuilder.minimal().build()
        
        # Should contain 837P-specific structure
        assert "ST*837*" in edi_content
        assert "BHT*0019*00*" in edi_content
        assert "CLM*" in edi_content
        assert "HI*" in edi_content  # Diagnosis segment
    
    def test_builder_control_numbers(self):
        """Test control number generation and setting."""
        builder = EDI835Builder()
        
        # Test random control numbers
        builder.with_random_control_numbers()
        edi_content = builder.build()
        
        # Should contain control numbers in ISA, GS, ST segments
        lines = edi_content.split('~')
        isa_line = next(line for line in lines if line.startswith('ISA*'))
        gs_line = next(line for line in lines if line.startswith('GS*'))
        st_line = next(line for line in lines if line.startswith('ST*'))
        
        # Extract control numbers
        isa_parts = isa_line.split('*')
        assert len(isa_parts[13]) > 0  # Interchange control number
        
        gs_parts = gs_line.split('*')
        assert len(gs_parts[6]) > 0  # Group control number
        
        st_parts = st_line.split('*')
        assert len(st_parts[2]) > 0  # Transaction control number


class TestScenarios:
    """Test the pre-built scenarios."""
    
    def test_payment_scenarios(self):
        """Test all payment scenarios generate valid EDI."""
        scenarios = PaymentScenarios.get_all_scenarios()
        
        assert len(scenarios) >= 8  # Should have multiple scenarios
        
        for name, scenario in scenarios.items():
            edi_content = scenario.build()
            
            # Basic EDI structure validation
            assert "ISA*" in edi_content, f"Scenario {name} missing ISA"
            assert "ST*835*" in edi_content, f"Scenario {name} missing ST"
            assert "BPR*" in edi_content, f"Scenario {name} missing BPR"
            assert edi_content.endswith("~"), f"Scenario {name} improper termination"
    
    def test_claim_scenarios(self):
        """Test all claim scenarios generate valid EDI."""
        scenarios = ClaimScenarios.get_all_scenarios()
        
        assert len(scenarios) >= 10  # Should have multiple scenarios
        
        for name, scenario in scenarios.items():
            if hasattr(scenario, 'build'):  # EDI builders
                edi_content = scenario.build()
                
                # Basic EDI structure validation
                assert "ISA*" in edi_content, f"Scenario {name} missing ISA"
                assert "ST*" in edi_content, f"Scenario {name} missing ST"
                assert edi_content.endswith("~"), f"Scenario {name} improper termination"
    
    def test_error_scenarios(self):
        """Test error scenarios generate EDI (even if invalid)."""
        scenarios = ErrorScenarios.get_all_scenarios()
        
        assert len(scenarios) >= 10  # Should have multiple error cases
        
        for name, scenario in scenarios.items():
            edi_content = scenario.build()
            
            # Should still be string content
            assert isinstance(edi_content, str), f"Scenario {name} not string"
            assert len(edi_content) > 0, f"Scenario {name} empty"
    
    def test_integration_scenarios(self):
        """Test integration scenarios generate multiple transaction types."""
        scenarios = IntegrationScenarios.get_all_scenarios()
        
        assert len(scenarios) >= 4  # Should have multiple integration scenarios
        
        # Test complete workflow
        if "complete_workflow" in scenarios:
            workflow = scenarios["complete_workflow"]
            
            # Should contain multiple transaction types
            assert "eligibility_inquiry" in workflow
            assert "claim_submission" in workflow
            assert "payment_advice" in workflow
            
            # Each should build valid EDI
            for tx_type, builder in workflow.items():
                if hasattr(builder, 'build'):
                    edi_content = builder.build()
                    assert "ISA*" in edi_content
                    assert "ST*" in edi_content


class TestDataSources:
    """Test the YAML data sources and data loader."""
    
    def test_payer_data_quality(self):
        """Test payer data is complete and realistic."""
        payers = data_loader.payers
        
        assert len(payers) >= 5  # Should have multiple payers
        
        for payer in payers:
            # Required fields
            assert 'name' in payer
            assert 'id' in payer
            assert 'type' in payer
            
            # Data quality
            assert len(payer['name']) > 0
            assert len(payer['id']) >= 4
            assert payer['type'] in ['insurance', 'government', 'hmo']
            
            # Address information
            if 'address' in payer:
                addr = payer['address']
                assert 'line1' in addr
                assert 'city' in addr
                assert 'state' in addr
                assert 'zip' in addr
    
    def test_provider_data_quality(self):
        """Test provider data is complete and realistic."""
        providers = data_loader.providers
        
        assert len(providers) >= 5  # Should have multiple providers
        
        for provider in providers:
            # Required fields
            assert 'name' in provider
            assert 'npi' in provider
            assert 'type' in provider
            
            # Data quality
            assert len(provider['name']) > 0
            assert len(provider['npi']) == 10  # NPI is 10 digits
            assert provider['npi'].isdigit()
            assert provider['type'] in ['individual', 'facility']
    
    def test_procedure_code_data_quality(self):
        """Test procedure code data is complete and realistic."""
        codes = data_loader.procedure_codes
        
        assert len(codes) >= 20  # Should have multiple codes
        
        for code in codes:
            # Required fields
            assert 'code' in code
            assert 'description' in code
            assert 'category' in code
            assert 'typical_charge' in code
            
            # Data quality
            assert len(code['code']) == 5  # CPT codes are 5 digits
            assert code['code'].isdigit()
            assert code['typical_charge'] > 0
            assert len(code['description']) > 10
    
    def test_diagnosis_code_data_quality(self):
        """Test diagnosis code data is complete and realistic."""
        codes = data_loader.diagnosis_codes
        
        assert len(codes) >= 20  # Should have multiple codes
        
        for code in codes:
            # Required fields
            assert 'code' in code
            assert 'description' in code
            assert 'category' in code
            assert 'severity' in code
            
            # Data quality
            assert len(code['code']) >= 3  # ICD-10 codes at least 3 chars
            assert len(code['description']) > 5
            assert code['severity'] in ['acute', 'chronic', 'symptom', 'routine', 'treatment']
    
    def test_data_loader_filtering(self):
        """Test data loader filtering capabilities."""
        # Test payer filtering
        insurance_payers = [p for p in data_loader.payers if p['type'] == 'insurance']
        government_payers = [p for p in data_loader.payers if p['type'] == 'government']
        
        assert len(insurance_payers) > 0
        assert len(government_payers) > 0
        
        # Test random selection with filtering
        random_insurance = data_loader.get_random_payer(payer_type="insurance")
        assert random_insurance['type'] == 'insurance'
        
        random_government = data_loader.get_random_payer(payer_type="government")
        assert random_government['type'] == 'government'
        
        # Test procedure code filtering
        office_visit_codes = data_loader.get_random_procedure_codes(category="office_visit", count=3)
        assert len(office_visit_codes) <= 3
        for code in office_visit_codes:
            assert code['category'] == 'office_visit'
    
    def test_realistic_data_generation(self):
        """Test realistic data generators produce valid output."""
        # Test realistic names
        payer_name = DataGenerator.generate_realistic_payer_name()
        assert isinstance(payer_name, str)
        assert len(payer_name) > 5
        
        provider_name = DataGenerator.generate_realistic_provider_name()
        assert isinstance(provider_name, str)
        assert len(provider_name) > 5
        
        # Test procedure/diagnosis codes
        procedure = DataGenerator.generate_procedure_code()
        diagnosis = DataGenerator.generate_diagnosis_code()
        
        assert len(procedure) == 5
        assert procedure.isdigit()
        assert len(diagnosis) >= 3


class TestDataGenerators:
    """Test the data generator utilities."""
    
    def test_npi_generation(self):
        """Test NPI generation follows proper format."""
        # Valid NPI
        npi = DataGenerator.generate_npi(valid=True)
        assert len(npi) == 10
        assert npi.isdigit()
        
        # Invalid NPI
        invalid_npi = DataGenerator.generate_npi(valid=False)
        assert "INVALID" in invalid_npi
    
    def test_control_number_generation(self):
        """Test control number generation."""
        # Default length
        control_num = DataGenerator.generate_control_number()
        assert len(control_num) == 9
        assert control_num.isdigit()
        
        # Custom length
        short_num = DataGenerator.generate_control_number(4)
        assert len(short_num) == 4
        assert short_num.isdigit()
    
    def test_amount_generation(self):
        """Test monetary amount generation."""
        # Default range
        amount = DataGenerator.generate_amount()
        assert isinstance(amount, Decimal)
        assert amount >= 0
        assert amount <= 10000
        
        # Custom range
        small_amount = DataGenerator.generate_amount(10.0, 100.0)
        assert small_amount >= 10
        assert small_amount <= 100
        
        # Check decimal places
        assert amount.as_tuple().exponent >= -2  # Max 2 decimal places
    
    def test_date_generation(self):
        """Test date generation."""
        # Default range (past year)
        generated_date = DataGenerator.generate_date()
        assert isinstance(generated_date, date)
        assert generated_date <= date.today()
        
        # Custom range
        start_date = date(2024, 1, 1)
        end_date = date(2024, 12, 31)
        custom_date = DataGenerator.generate_date(start_date, end_date)
        assert start_date <= custom_date <= end_date
    
    def test_id_generation(self):
        """Test various ID generation methods."""
        # SSN
        ssn = DataGenerator.generate_ssn()
        assert len(ssn) == 9
        assert ssn.isdigit()
        
        # EIN
        ein = DataGenerator.generate_ein()
        assert len(ein) == 10  # XX-XXXXXXX format
        assert '-' in ein
        
        # Claim ID
        claim_id = DataGenerator.generate_claim_id()
        assert claim_id.startswith("CLM")
        assert len(claim_id) > 3
        
        # Payer ID
        payer_id = DataGenerator.generate_payer_id()
        assert payer_id.startswith("PAY")
        assert len(payer_id) > 3


class TestEDIStructure:
    """Test EDI structure and validation."""
    
    def test_edi_segment_structure(self):
        """Test EDI segments have proper structure."""
        edi_content = EDI835Builder().with_realistic_payer().build()
        
        # Split into segments
        segments = [seg for seg in edi_content.split('~') if seg]
        
        # Each segment should end with ~ (except last empty one)
        for segment in segments[:-1]:  # Excluding last empty segment
            assert len(segment) > 0
            # Segments should contain data elements separated by *
            assert '*' in segment
    
    def test_edi_envelope_structure(self):
        """Test EDI envelope structure is correct."""
        edi_content = EDI835Builder().with_realistic_payer().build()
        segments = [seg for seg in edi_content.split('~') if seg]
        
        # Find envelope segments
        isa_segments = [seg for seg in segments if seg.startswith('ISA*')]
        gs_segments = [seg for seg in segments if seg.startswith('GS*')]
        st_segments = [seg for seg in segments if seg.startswith('ST*')]
        se_segments = [seg for seg in segments if seg.startswith('SE*')]
        ge_segments = [seg for seg in segments if seg.startswith('GE*')]
        iea_segments = [seg for seg in segments if seg.startswith('IEA*')]
        
        # Should have proper envelope structure
        assert len(isa_segments) == 1
        assert len(gs_segments) == 1
        assert len(st_segments) == 1
        assert len(se_segments) == 1
        assert len(ge_segments) == 1
        assert len(iea_segments) == 1
        
        # ISA should be first, IEA should be last
        assert segments[0].startswith('ISA*')
        assert segments[-1].startswith('IEA*')
    
    def test_control_number_consistency(self):
        """Test control numbers are consistent across segments."""
        builder = EDI835Builder().with_random_control_numbers()
        edi_content = builder.build()
        segments = [seg for seg in edi_content.split('~') if seg]
        
        # Extract control numbers
        isa_parts = segments[0].split('*')  # ISA segment
        gs_line = next(seg for seg in segments if seg.startswith('GS*'))
        gs_parts = gs_line.split('*')
        
        iea_line = next(seg for seg in segments if seg.startswith('IEA*'))
        iea_parts = iea_line.split('*')
        
        ge_line = next(seg for seg in segments if seg.startswith('GE*'))
        ge_parts = ge_line.split('*')
        
        # ISA control number should match IEA
        assert isa_parts[13] == iea_parts[2]
        
        # GS control number should match GE
        assert gs_parts[6] == ge_parts[2]


class TestBackwardCompatibility:
    """Test backward compatibility with legacy fixtures."""
    
    def test_legacy_fixtures_import(self):
        """Test legacy fixtures can be imported."""
        from .legacy_fixtures import EDIFixtures
        
        # Should have all original methods
        assert hasattr(EDIFixtures, 'get_minimal_835')
        assert hasattr(EDIFixtures, 'get_835_with_multiple_claims')
        assert hasattr(EDIFixtures, 'get_835_denied_claim')
        assert hasattr(EDIFixtures, 'get_270_eligibility_inquiry')
    
    def test_legacy_fixtures_functionality(self):
        """Test legacy fixtures produce valid EDI."""
        from .legacy_fixtures import EDIFixtures
        
        # Test each legacy method
        minimal_835 = EDIFixtures.get_minimal_835()
        assert "ST*835*" in minimal_835
        assert "BPR*" in minimal_835
        
        multiple_claims = EDIFixtures.get_835_with_multiple_claims()
        claim_count = multiple_claims.count('CLP*')
        assert claim_count >= 2
        
        denied_claim = EDIFixtures.get_835_denied_claim()
        assert "BPR*I*0.00" in denied_claim or "*NON" in denied_claim
        
        eligibility = EDIFixtures.get_270_eligibility_inquiry()
        assert "ST*270*" in eligibility
        assert "EQ*" in eligibility
    
    def test_legacy_compatibility_maintains_api(self):
        """Test legacy API is exactly preserved."""
        from .legacy_fixtures import EDIFixtures
        
        # Test static method signatures haven't changed
        import inspect
        
        # get_minimal_835 should take only self
        sig = inspect.signature(EDIFixtures.get_minimal_835)
        assert len(sig.parameters) == 0  # Static method, no self
        
        # All methods should return strings
        methods = [
            'get_minimal_835',
            'get_835_with_multiple_claims', 
            'get_835_denied_claim',
            'get_270_eligibility_inquiry'
        ]
        
        for method_name in methods:
            method = getattr(EDIFixtures, method_name)
            result = method()
            assert isinstance(result, str)
            assert len(result) > 0


@pytest.fixture
def sample_builder():
    """Fixture providing a configured builder for testing."""
    return (EDI835Builder()
           .with_realistic_payer()
           .with_realistic_payee()
           .with_ach_payment(Decimal("1000.00")))


class TestFixtureUsability:
    """Test fixture system usability and ergonomics."""
    
    def test_builder_chaining(self, sample_builder):
        """Test builder method chaining works smoothly."""
        # Should be able to continue chaining
        enhanced_builder = (sample_builder
                           .with_primary_claim(charge=Decimal("1200.00"), paid=Decimal("1000.00"))
                           .with_trace_number())
        
        edi_content = enhanced_builder.build()
        assert "CLP*" in edi_content
        assert "TRN*" in edi_content
    
    def test_scenario_ease_of_use(self):
        """Test scenarios are easy to use."""
        # Should be one-liner to get EDI
        edi_content = PaymentScenarios.ach_payment_standard().build()
        assert isinstance(edi_content, str)
        assert len(edi_content) > 100  # Should be substantial content
        
        # Should be easy to modify scenarios
        modified_scenario = (PaymentScenarios.ach_payment_standard()
                           .with_primary_claim("CUSTOM001", Decimal("500.00"), Decimal("450.00")))
        modified_edi = modified_scenario.build()
        assert "CUSTOM001" in modified_edi
    
    def test_data_loader_convenience(self):
        """Test data loader provides convenient access to realistic data."""
        # Should be easy to get realistic entities
        payer = data_loader.get_random_payer()
        provider = data_loader.get_random_provider()
        
        # Should be able to use directly in builders
        edi_content = (EDI835Builder()
                      .with_payer(payer['name'], payer['id'])
                      .with_payee(provider['name'], provider['npi'])
                      .with_ach_payment(Decimal("1000.00"))
                      .build())
        
        assert payer['name'] in edi_content
        assert provider['name'] in edi_content
        assert provider['npi'] in edi_content