"""
Enhanced EDI Test Fixtures.

This package provides a comprehensive fixture system for EDI testing,
including builders, scenarios, and realistic test data.
"""

# Import the legacy fixtures for backward compatibility
from ..core.fixtures.legacy_fixtures import EDIFixtures

# Import the modern builder system
from ..core.fixtures.builders.builder_835 import EDI835Builder
from ..core.fixtures.builders.builder_270 import EDI270Builder
from ..core.fixtures.builders.builder_276 import EDI276Builder
from ..core.fixtures.builders.builder_837p import EDI837PBuilder

# Import scenario-based fixtures
from ..core.fixtures.scenarios.payment_scenarios import PaymentScenarios
from ..core.fixtures.scenarios.claim_scenarios import ClaimScenarios
from ..core.fixtures.scenarios.error_scenarios import ErrorScenarios
from ..core.fixtures.scenarios.integration_scenarios import IntegrationScenarios

# Import data generators
from ..core.fixtures.base.generators import DataGenerator

__all__ = [
    # Legacy compatibility
    'EDIFixtures',
    
    # Modern builders
    'EDI835Builder',
    'EDI270Builder', 
    'EDI276Builder',
    'EDI837PBuilder',
    
    # Scenario-based fixtures
    'PaymentScenarios',
    'ClaimScenarios',
    'ErrorScenarios', 
    'IntegrationScenarios',
    
    # Data generation
    'DataGenerator'
]