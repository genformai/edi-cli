"""
Test runner and quality assurance for the EDI fixture system.

This script runs comprehensive tests and generates quality reports
for the entire fixture system.
"""

import sys
import traceback
from typing import Dict, List, Tuple

from .validation import EDIValidator, FixtureQualityReport, assert_valid_edi
from . import (
    EDI835Builder, EDI270Builder, EDI276Builder, EDI837pBuilder,
    PaymentScenarios, ClaimScenarios, ErrorScenarios, IntegrationScenarios,
    data_loader
)


class FixtureTestRunner:
    """Comprehensive test runner for the fixture system."""
    
    def __init__(self):
        self.results = {
            'tests_run': 0,
            'tests_passed': 0,
            'tests_failed': 0,
            'errors': [],
            'warnings': []
        }
    
    def run_test(self, test_name: str, test_func) -> bool:
        """Run a single test and record results."""
        self.results['tests_run'] += 1
        
        try:
            test_func()
            self.results['tests_passed'] += 1
            print(f"✓ {test_name}")
            return True
        except Exception as e:
            self.results['tests_failed'] += 1
            self.results['errors'].append(f"{test_name}: {str(e)}")
            print(f"✗ {test_name}: {str(e)}")
            return False
    
    def test_builder_basic_functionality(self):
        """Test basic builder functionality."""
        # Test each builder can create minimal EDI
        builders = [
            ('EDI835Builder', EDI835Builder),
            ('EDI270Builder', EDI270Builder.minimal),
            ('EDI276Builder', EDI276Builder.minimal),
            ('EDI837pBuilder', EDI837pBuilder.minimal)
        ]
        
        for name, builder_class in builders:
            def test_builder():
                if callable(builder_class) and hasattr(builder_class, 'build'):
                    # It's already an instance
                    edi_content = builder_class().build()
                elif hasattr(builder_class, 'build'):
                    # It's a builder instance
                    edi_content = builder_class.build()
                else:
                    # It's a class, instantiate it
                    edi_content = builder_class().build()
                
                assert_valid_edi(edi_content, f"{name} basic build")
                assert len(edi_content) > 100, "EDI content too short"
                assert "ISA*" in edi_content, "Missing ISA segment"
                assert "ST*" in edi_content, "Missing ST segment"
            
            self.run_test(f"Builder {name} basic", test_builder)
    
    def test_realistic_data_integration(self):
        """Test integration with realistic data sources."""
        def test_realistic_payer():
            payer = data_loader.get_random_payer()
            edi_content = (EDI835Builder()
                          .with_payer(payer['name'], payer['id'])
                          .with_realistic_payee()
                          .with_ach_payment(Decimal("1000.00"))
                          .build())
            
            assert_valid_edi(edi_content, "Realistic payer integration")
            assert payer['name'] in edi_content
            assert payer['id'] in edi_content
        
        def test_realistic_provider():
            provider = data_loader.get_random_provider()
            edi_content = (EDI835Builder()
                          .with_realistic_payer()
                          .with_payee(provider['name'], provider['npi'])
                          .with_ach_payment(Decimal("1000.00"))
                          .build())
            
            assert_valid_edi(edi_content, "Realistic provider integration")
            assert provider['name'] in edi_content
            assert provider['npi'] in edi_content
        
        def test_procedure_codes():
            codes = data_loader.get_random_procedure_codes(count=2)
            total_charge = sum(Decimal(str(code['typical_charge'])) for code in codes)
            
            builder = (EDI835Builder()
                      .with_realistic_payer()
                      .with_realistic_payee()
                      .with_ach_payment(total_charge))
            
            for code in codes:
                builder.with_service(code['code'], Decimal(str(code['typical_charge'])), Decimal(str(code['typical_charge'])))
            
            edi_content = builder.build()
            assert_valid_edi(edi_content, "Procedure code integration")
            
            for code in codes:
                assert code['code'] in edi_content
        
        self.run_test("Realistic payer data", test_realistic_payer)
        self.run_test("Realistic provider data", test_realistic_provider)
        self.run_test("Procedure code data", test_procedure_codes)
    
    def test_payment_scenarios(self):
        """Test all payment scenarios."""
        scenarios = PaymentScenarios.get_all_scenarios()
        
        for name, scenario in scenarios.items():
            def test_scenario():
                edi_content = scenario.build()
                assert_valid_edi(edi_content, f"Payment scenario {name}")
                
                # Verify it's a payment transaction
                assert "ST*835*" in edi_content, "Not a valid 835 transaction"
                assert "BPR*" in edi_content, "Missing payment information"
            
            self.run_test(f"Payment scenario: {name}", test_scenario)
    
    def test_claim_scenarios(self):
        """Test all claim scenarios."""
        scenarios = ClaimScenarios.get_all_scenarios()
        
        for name, scenario in scenarios.items():
            if hasattr(scenario, 'build'):
                def test_scenario():
                    edi_content = scenario.build()
                    assert_valid_edi(edi_content, f"Claim scenario {name}")
                    
                    # Should contain transaction structure
                    assert "ST*" in edi_content, "Missing transaction header"
                
                self.run_test(f"Claim scenario: {name}", test_scenario)
    
    def test_integration_scenarios(self):
        """Test integration scenarios."""
        scenarios = IntegrationScenarios.get_all_scenarios()
        
        for name, scenario_data in scenarios.items():
            def test_integration():
                if isinstance(scenario_data, dict):
                    # Multi-transaction scenario
                    for tx_name, tx_scenario in scenario_data.items():
                        if hasattr(tx_scenario, 'build'):
                            edi_content = tx_scenario.build()
                            assert_valid_edi(edi_content, f"Integration {name}/{tx_name}")
                else:
                    # Single transaction scenario
                    if hasattr(scenario_data, 'build'):
                        edi_content = scenario_data.build()
                        assert_valid_edi(edi_content, f"Integration {name}")
            
            self.run_test(f"Integration scenario: {name}", test_integration)
    
    def test_error_scenarios(self):
        """Test error scenarios (should build but may be invalid)."""
        scenarios = ErrorScenarios.get_all_scenarios()
        
        for name, scenario in scenarios.items():
            def test_error_scenario():
                edi_content = scenario.build()
                
                # Should produce content
                assert isinstance(edi_content, str), "Should produce string content"
                assert len(edi_content) > 0, "Should not be empty"
                
                # May or may not be valid (that's the point of error scenarios)
                # Just verify it doesn't crash
            
            self.run_test(f"Error scenario: {name}", test_error_scenario)
    
    def test_data_source_quality(self):
        """Test quality of YAML data sources."""
        def test_payer_data():
            payers = data_loader.payers
            assert len(payers) >= 5, "Should have multiple payers"
            
            for payer in payers[:3]:  # Test first 3
                assert 'name' in payer, "Payer missing name"
                assert 'id' in payer, "Payer missing ID"
                assert 'type' in payer, "Payer missing type"
                assert len(payer['name']) > 0, "Payer name empty"
                assert len(payer['id']) >= 4, "Payer ID too short"
        
        def test_provider_data():
            providers = data_loader.providers
            assert len(providers) >= 5, "Should have multiple providers"
            
            for provider in providers[:3]:  # Test first 3
                assert 'name' in provider, "Provider missing name"
                assert 'npi' in provider, "Provider missing NPI"
                assert 'type' in provider, "Provider missing type"
                assert len(provider['npi']) == 10, f"Invalid NPI length: {provider['npi']}"
                assert provider['npi'].isdigit(), f"Invalid NPI format: {provider['npi']}"
        
        def test_procedure_codes():
            codes = data_loader.procedure_codes
            assert len(codes) >= 10, "Should have multiple procedure codes"
            
            for code in codes[:5]:  # Test first 5
                assert 'code' in code, "Procedure missing code"
                assert 'description' in code, "Procedure missing description" 
                assert 'typical_charge' in code, "Procedure missing charge"
                assert len(code['code']) == 5, f"Invalid CPT code length: {code['code']}"
                assert code['code'].isdigit(), f"Invalid CPT code format: {code['code']}"
                assert code['typical_charge'] > 0, "Procedure charge should be positive"
        
        def test_diagnosis_codes():
            codes = data_loader.diagnosis_codes
            assert len(codes) >= 10, "Should have multiple diagnosis codes"
            
            for code in codes[:5]:  # Test first 5
                assert 'code' in code, "Diagnosis missing code"
                assert 'description' in code, "Diagnosis missing description"
                assert 'category' in code, "Diagnosis missing category"
                assert len(code['code']) >= 3, f"Invalid ICD-10 code length: {code['code']}"
        
        self.run_test("Payer data quality", test_payer_data)
        self.run_test("Provider data quality", test_provider_data)
        self.run_test("Procedure code quality", test_procedure_codes)
        self.run_test("Diagnosis code quality", test_diagnosis_codes)
    
    def test_backward_compatibility(self):
        """Test backward compatibility with legacy fixtures."""
        def test_legacy_import():
            from .legacy_fixtures import EDIFixtures
            
            # Test original methods exist
            assert hasattr(EDIFixtures, 'get_minimal_835')
            assert hasattr(EDIFixtures, 'get_835_with_multiple_claims')
            assert hasattr(EDIFixtures, 'get_835_denied_claim')
            assert hasattr(EDIFixtures, 'get_270_eligibility_inquiry')
        
        def test_legacy_functionality():
            from .legacy_fixtures import EDIFixtures
            
            # Test original methods work
            minimal_835 = EDIFixtures.get_minimal_835()
            assert_valid_edi(minimal_835, "Legacy minimal 835")
            
            multiple_claims = EDIFixtures.get_835_with_multiple_claims()
            assert_valid_edi(multiple_claims, "Legacy multiple claims")
            
            denied_claim = EDIFixtures.get_835_denied_claim()
            assert_valid_edi(denied_claim, "Legacy denied claim")
            
            eligibility = EDIFixtures.get_270_eligibility_inquiry()
            assert_valid_edi(eligibility, "Legacy eligibility inquiry")
        
        self.run_test("Legacy import compatibility", test_legacy_import)
        self.run_test("Legacy functionality", test_legacy_functionality)
    
    def run_all_tests(self) -> Dict:
        """Run all fixture system tests."""
        print("=== Running EDI Fixture System Tests ===\n")
        
        # Run test suites
        self.test_builder_basic_functionality()
        self.test_realistic_data_integration()
        self.test_payment_scenarios()
        self.test_claim_scenarios()
        self.test_integration_scenarios()
        self.test_error_scenarios()
        self.test_data_source_quality()
        self.test_backward_compatibility()
        
        # Print summary
        print(f"\n=== Test Results ===")
        print(f"Tests Run: {self.results['tests_run']}")
        print(f"Tests Passed: {self.results['tests_passed']}")
        print(f"Tests Failed: {self.results['tests_failed']}")
        
        if self.results['tests_failed'] > 0:
            print(f"\nFailures:")
            for error in self.results['errors']:
                print(f"  - {error}")
        
        success_rate = (self.results['tests_passed'] / self.results['tests_run']) * 100
        print(f"Success Rate: {success_rate:.1f}%")
        
        return self.results


def run_quality_report():
    """Run and display comprehensive quality report."""
    print("\n=== Generating Quality Report ===\n")
    
    try:
        FixtureQualityReport.print_summary_report()
    except Exception as e:
        print(f"Error generating quality report: {e}")
        traceback.print_exc()


def main():
    """Main entry point for test runner."""
    print("EDI Fixture System - Comprehensive Test Suite")
    print("=" * 50)
    
    # Run tests
    runner = FixtureTestRunner()
    results = runner.run_all_tests()
    
    # Generate quality report
    run_quality_report()
    
    # Exit with appropriate code
    if results['tests_failed'] > 0:
        print(f"\n❌ {results['tests_failed']} tests failed")
        sys.exit(1)
    else:
        print(f"\n✅ All {results['tests_passed']} tests passed!")
        sys.exit(0)


if __name__ == '__main__':
    main()