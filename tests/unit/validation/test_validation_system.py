"""
Tests for the integrated validation system.

These tests verify that the validation framework works correctly
with the plugin architecture and provides comprehensive validation.
"""

import pytest
from decimal import Decimal
from typing import List, Dict, Any

from packages.core.validation import ValidationEngine, ValidationResult, ValidationError, ValidationContext
from packages.core.validation.rules import BaseValidationRule
from packages.core.validation.factory import create_validation_engine, create_validation_rule
from packages.core.validation.integration import ValidationIntegrationManager, setup_validation_integration
from packages.core.validation.rules_835 import (
    Transaction835StructureRule, 
    Transaction835DataValidationRule, 
    Transaction835BusinessRule
)
from packages.core.base.edi_ast import EdiRoot


class TestValidationEngine:
    """Test cases for the validation engine."""

    def test_validation_engine_creation(self):
        """Test that validation engine can be created."""
        engine = ValidationEngine()
        
        assert engine is not None
        assert len(engine.rule_plugins) == 0
        assert len(engine.global_rules) == 0

    def test_rule_registration(self):
        """Test validation rule registration."""
        engine = ValidationEngine()
        
        # Create a simple test rule
        class TestRule(BaseValidationRule):
            def __init__(self):
                super().__init__("test_rule", ["835"], "Test rule")
            
            def validate_document(self, edi_root, context):
                return []
        
        rule = TestRule()
        engine.register_rule_plugin(rule)
        
        assert "835" in engine.rule_plugins
        assert len(engine.rule_plugins["835"]) == 1
        assert engine.rule_plugins["835"][0] == rule

    def test_rule_enabling_disabling(self):
        """Test enabling and disabling validation rules."""
        engine = ValidationEngine()
        
        class TestRule(BaseValidationRule):
            def __init__(self):
                super().__init__("test_rule", ["835"])
            
            def validate_document(self, edi_root, context):
                return [{'message': 'Test error', 'code': 'TEST', 'severity': 'error'}]
        
        rule = TestRule()
        engine.register_rule_plugin(rule)
        
        # Rule should be enabled by default
        assert rule.rule_name in engine.enabled_rules
        
        # Disable rule
        engine.disable_rule(rule.rule_name)
        assert rule.rule_name in engine.disabled_rules
        assert rule.rule_name not in engine.enabled_rules
        
        # Re-enable rule
        engine.enable_rule(rule.rule_name)
        assert rule.rule_name in engine.enabled_rules
        assert rule.rule_name not in engine.disabled_rules

    def test_validation_execution(self):
        """Test validation execution with mock EDI document."""
        engine = ValidationEngine()
        
        class TestRule(BaseValidationRule):
            def __init__(self):
                super().__init__("test_rule", ["835"])
            
            def validate_document(self, edi_root, context):
                return [
                    {'message': 'Test error', 'code': 'TEST_ERROR', 'severity': 'error'},
                    {'message': 'Test warning', 'code': 'TEST_WARNING', 'severity': 'warning'}
                ]
        
        rule = TestRule()
        engine.register_rule_plugin(rule)
        
        # Create mock EDI document
        edi_root = EdiRoot()
        from packages.core.base.edi_ast import Interchange, FunctionalGroup, Transaction
        interchange = Interchange("SENDER", "RECEIVER", "20241226", "1430", "000000001")
        functional_group = FunctionalGroup("HP", "SENDER", "RECEIVER", "20241226", "1430", "000000001")
        transaction = Transaction("835", "0001")
        
        functional_group.transactions.append(transaction)
        interchange.functional_groups.append(functional_group)
        edi_root.interchanges.append(interchange)
        
        # Execute validation
        result = engine.validate(edi_root)
        
        assert isinstance(result, ValidationResult)
        assert not result.is_valid
        assert result.error_count == 1
        assert result.warning_count == 1
        assert len(result.executed_rules) == 1
        assert result.executed_rules[0] == "test_rule"


class TestValidationFactory:
    """Test cases for validation factory and builders."""

    def test_validation_engine_builder(self):
        """Test validation engine builder."""
        engine = create_validation_engine().build()
        
        assert isinstance(engine, ValidationEngine)

    def test_validation_rule_builder(self):
        """Test validation rule builder."""
        def test_validator(edi_root, context, config):
            return [{'message': 'Test', 'code': 'TEST', 'severity': 'error'}]
        
        rule = (create_validation_rule()
                .name("test_rule")
                .transactions(["835"])
                .description("Test rule")
                .severity("error")
                .validator(test_validator)
                .build())
        
        assert rule.rule_name == "test_rule"
        assert rule.supported_transactions == ["835"]
        assert rule.description == "Test rule"

    def test_engine_builder_with_rules(self):
        """Test building engine with rules."""
        def test_validator(edi_root, context, config):
            return []
        
        rule = (create_validation_rule()
                .name("test_rule")
                .transactions(["835"])
                .validator(test_validator)
                .build())
        
        engine = (create_validation_engine()
                 .add_rule(rule)
                 .enable_rule("test_rule")
                 .build())
        
        assert "835" in engine.rule_plugins
        assert "test_rule" in engine.enabled_rules


class Test835ValidationRules:
    """Test cases for 835-specific validation rules."""

    def test_835_structure_rule(self):
        """Test 835 structure validation rule."""
        rule = Transaction835StructureRule()
        
        assert rule.rule_name == "835_structure_validation"
        assert "835" in rule.supported_transactions

    def test_835_structure_validation_missing_data(self):
        """Test 835 structure validation with missing data."""
        rule = Transaction835StructureRule()
        
        # Create transaction without 835 data
        from packages.core.base.edi_ast import Transaction
        transaction = Transaction("835", "0001")
        
        errors = rule.validate_transaction_structure(transaction, "test_path")
        
        assert len(errors) == 1
        assert errors[0]['code'] == "835_MISSING_DATA"
        assert errors[0]['severity'] == "error"

    def test_835_data_validation_rule(self):
        """Test 835 data validation rule."""
        rule = Transaction835DataValidationRule()
        
        assert rule.rule_name == "835_data_validation"
        assert "835" in rule.supported_transactions

    def test_835_business_rule(self):
        """Test 835 business validation rule."""
        rule = Transaction835BusinessRule()
        
        assert rule.rule_name == "835_business_validation"
        assert "835" in rule.supported_transactions


class TestValidationIntegration:
    """Test cases for validation system integration."""

    def test_integration_manager_creation(self):
        """Test validation integration manager creation."""
        manager = ValidationIntegrationManager()
        
        assert manager is not None
        assert manager.is_validation_enabled()
        assert manager.validation_engine is not None

    def test_validation_enable_disable(self):
        """Test enabling and disabling validation."""
        manager = ValidationIntegrationManager()
        
        assert manager.is_validation_enabled()
        
        manager.disable_validation()
        assert not manager.is_validation_enabled()
        
        manager.enable_validation()
        assert manager.is_validation_enabled()

    def test_parse_and_validate_integration(self):
        """Test integrated parse and validate functionality."""
        manager = setup_validation_integration()
        
        # Test segments for 835
        segments = [
            ["ISA", "00", "", "00", "", "ZZ", "SENDER", "ZZ", "RECEIVER", "241226", "1430", "U", "00501", "000000001", "0", "P", ">"],
            ["GS", "HP", "SENDER", "RECEIVER", "20241226", "1430", "000000001", "X", "005010X221A1"],
            ["ST", "835", "0001"],
            ["BPR", "I", "1000.00", "C", "ACH", "", "", "", "", "", "", "20241226"],
            ["TRN", "1", "TRACE123", "1"],
            ["SE", "5", "0001"],
            ["GE", "1", "000000001"],
            ["IEA", "1", "000000001"]
        ]
        
        result = manager.parse_and_validate(segments)
        
        assert result['parse_success'] == True
        assert result['edi_root'] is not None
        assert result['validation_enabled'] == True
        assert result['validation_result'] is not None
        
        validation_result = result['validation_result']
        assert isinstance(validation_result, ValidationResult)

    def test_parse_and_validate_with_validation_disabled(self):
        """Test parse and validate with validation disabled."""
        manager = setup_validation_integration()
        manager.disable_validation()
        
        segments = [
            ["ISA", "00", "", "00", "", "ZZ", "SENDER", "ZZ", "RECEIVER", "241226", "1430", "U", "00501", "000000001", "0", "P", ">"],
            ["GS", "HP", "SENDER", "RECEIVER", "20241226", "1430", "000000001", "X", "005010X221A1"],
            ["ST", "835", "0001"],
            ["BPR", "I", "1000.00", "C", "ACH", "", "", "", "", "", "", "20241226"],
            ["SE", "4", "0001"],
            ["GE", "1", "000000001"],
            ["IEA", "1", "000000001"]
        ]
        
        result = manager.parse_and_validate(segments)
        
        assert result['parse_success'] == True
        assert result['validation_enabled'] == False
        assert result['validation_result'] is None

    def test_validation_context_handling(self):
        """Test validation with custom context."""
        # Create fresh manager to avoid registration conflicts
        from packages.core.plugins.api import PluginManager
        manager = ValidationIntegrationManager(PluginManager())
        manager.plugin_manager.load_builtin_plugins()
        
        segments = [
            ["ISA", "00", "", "00", "", "ZZ", "SENDER", "ZZ", "RECEIVER", "241226", "1430", "U", "00501", "000000001", "0", "P", ">"],
            ["GS", "HP", "SENDER", "RECEIVER", "20241226", "1430", "000000001", "X", "005010X221A1"],
            ["ST", "835", "0001"],
            ["BPR", "I", "1000.00", "C", "ACH", "", "", "", "", "", "", "20241226"],
            ["SE", "4", "0001"],
            ["GE", "1", "000000001"],
            ["IEA", "1", "000000001"]
        ]
        
        validation_context = {
            'strict_mode': True,
            'trading_partner_id': 'TEST_PARTNER',
            'custom_rules': {'tolerance': 0.01}
        }
        
        result = manager.parse_and_validate(segments, validation_context)
        
        assert result['parse_success'] == True
        assert result['validation_result'] is not None

    def test_validation_summary(self):
        """Test getting validation summary."""
        # Create fresh manager to avoid registration conflicts
        from packages.core.plugins.api import PluginManager
        manager = ValidationIntegrationManager(PluginManager())
        manager.plugin_manager.load_builtin_plugins()
        
        summary = manager.get_validation_summary()
        
        assert 'validation_enabled' in summary
        assert 'validation_engine_summary' in summary
        assert 'available_parsers' in summary
        assert summary['validation_enabled'] == True

    def test_custom_rule_addition(self):
        """Test adding custom validation rules."""
        manager = ValidationIntegrationManager()
        
        class CustomRule(BaseValidationRule):
            def __init__(self):
                super().__init__("custom_rule", ["835"], "Custom test rule")
            
            def validate_document(self, edi_root, context):
                return [{'message': 'Custom validation', 'code': 'CUSTOM', 'severity': 'warning'}]
        
        custom_rule = CustomRule()
        manager.add_validation_rule(custom_rule)
        
        # Verify rule was added
        assert "custom_rule" in manager.validation_engine.enabled_rules

    def test_error_handling_in_validation(self):
        """Test error handling during validation."""
        manager = ValidationIntegrationManager()
        
        class FailingRule(BaseValidationRule):
            def __init__(self):
                super().__init__("failing_rule", ["835"])
            
            def validate_document(self, edi_root, context):
                raise Exception("Test validation error")
        
        failing_rule = FailingRule()
        manager.add_validation_rule(failing_rule)
        
        # Create EDI document with 835 transaction to trigger the failing rule
        edi_root = EdiRoot()
        from packages.core.base.edi_ast import Interchange, FunctionalGroup, Transaction
        interchange = Interchange("SENDER", "RECEIVER", "20241226", "1430", "000000001")
        functional_group = FunctionalGroup("HP", "SENDER", "RECEIVER", "20241226", "1430", "000000001")
        transaction = Transaction("835", "0001")  # This will trigger the failing rule
        
        functional_group.transactions.append(transaction)
        interchange.functional_groups.append(functional_group)
        edi_root.interchanges.append(interchange)
        
        result = manager.validate_document(edi_root)
        
        # Should have system error
        assert not result.is_valid
        assert result.error_count >= 1
        
        # Find system error
        system_errors = [e for e in result.errors if e.code == "SYSTEM_ERROR"]
        assert len(system_errors) == 1