"""
Common test fixtures and sample data for EDI testing.

This module provides backward compatibility with the original fixtures API
while using the enhanced fixture system under the hood.

For new development, use the enhanced fixture system directly:
    from tests.core.fixtures import EDI835Builder, PaymentScenarios

For migration guidance, see: tests/core/fixtures/MIGRATION.md
"""

# Import the backward-compatible implementation
from .fixtures.legacy_fixtures import EDIFixtures

__all__ = ['EDIFixtures']