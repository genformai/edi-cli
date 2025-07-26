"""
Enhanced EDI test fixture system.

This package provides a comprehensive fixture system for EDI transaction testing with:
- Builder pattern for constructing test data
- Scenario-based fixtures for common testing patterns  
- YAML-based realistic data sources
- Transaction-specific builders for 835, 270, 276, and 837P
- Error scenarios for validation testing
- Integration scenarios for complex workflows

Usage:
    from tests.core.fixtures import EDI835Builder, PaymentScenarios, data_loader
    
    # Build custom fixture
    payment = EDI835Builder().with_realistic_payer().with_ach_payment(Decimal("500")).build()
    
    # Use pre-built scenario
    scenario = PaymentScenarios.ach_payment_standard()
    
    # Load realistic data
    payer = data_loader.get_random_payer()
"""

from .builders.edi_builder import EDIBuilder
from .builders.builder_835 import EDI835Builder
from .builders.builder_270 import EDI270Builder
from .builders.builder_276 import EDI276Builder
from .builders.builder_837p import EDI837pBuilder

from .scenarios.payment_scenarios import PaymentScenarios
from .scenarios.claim_scenarios import ClaimScenarios
from .scenarios.error_scenarios import ErrorScenarios
from .scenarios.integration_scenarios import IntegrationScenarios

from .data import data_loader

from .base.generators import DataGenerator, NameGenerator, AddressGenerator

try:
    from .legacy_fixtures import EDIFixtures  # Backward compatibility
    _has_legacy = True
except ImportError:
    _has_legacy = False

__all__ = [
    'EDIBuilder',
    'EDI835Builder', 
    'EDI270Builder',
    'EDI276Builder',
    'EDI837pBuilder',
    'PaymentScenarios',
    'ClaimScenarios', 
    'ErrorScenarios',
    'IntegrationScenarios',
    'data_loader',
    'DataGenerator',
    'NameGenerator', 
    'AddressGenerator'
]

if _has_legacy:
    __all__.append('EDIFixtures')