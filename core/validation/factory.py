"""
Validation Rule Factory for creating and managing validation rules.

This module provides factory classes for creating validation rules
and integrating them with the plugin architecture.
"""

from typing import Dict, List, Any, Optional, Type, Callable
from abc import ABC, abstractmethod

from .rules import BaseValidationRule, ValidationContext
from .engine import ValidationEngine
from ..base.edi_ast import EdiRoot


class ValidationRuleFactory(ABC):
    """Abstract factory for creating validation rules."""
    
    @abstractmethod
    def create_rule(self, config: Dict[str, Any]) -> BaseValidationRule:
        """Create a validation rule from configuration."""
        pass
    
    @abstractmethod
    def get_supported_rule_types(self) -> List[str]:
        """Get list of supported rule types."""
        pass


class GenericValidationRuleFactory(ValidationRuleFactory):
    """Generic factory for creating validation rules from configuration."""
    
    def __init__(self):
        self._rule_constructors: Dict[str, Callable] = {}
        self._rule_templates: Dict[str, Dict[str, Any]] = {}
    
    def register_rule_type(self, rule_type: str, constructor: Callable, 
                          template: Optional[Dict[str, Any]] = None):
        """Register a validation rule type with its constructor."""
        self._rule_constructors[rule_type] = constructor
        if template:
            self._rule_templates[rule_type] = template
    
    def create_rule(self, config: Dict[str, Any]) -> BaseValidationRule:
        """Create a validation rule from configuration."""
        rule_type = config.get('type')
        if not rule_type:
            raise ValueError("Rule configuration must specify 'type'")
        
        if rule_type not in self._rule_constructors:
            raise ValueError(f"Unknown rule type: {rule_type}")
        
        constructor = self._rule_constructors[rule_type]
        
        # Merge with template if available
        if rule_type in self._rule_templates:
            merged_config = self._rule_templates[rule_type].copy()
            merged_config.update(config)
            config = merged_config
        
        return constructor(config)
    
    def get_supported_rule_types(self) -> List[str]:
        """Get list of supported rule types."""
        return list(self._rule_constructors.keys())


class ConfigurableValidationRule(BaseValidationRule):
    """A validation rule that can be configured through a dictionary."""
    
    def __init__(self, config: Dict[str, Any]):
        rule_name = config.get('name', 'unnamed_rule')
        supported_transactions = config.get('transactions', ['*'])
        description = config.get('description', '')
        severity = config.get('severity', 'error')
        
        super().__init__(rule_name, supported_transactions, description, severity)
        
        self.config = config
        self.validation_function = config.get('validator')
        
        if not self.validation_function:
            raise ValueError("ConfigurableValidationRule requires a 'validator' function")
    
    def validate_document(self, edi_root: EdiRoot, context: ValidationContext) -> List[Dict[str, Any]]:
        """Execute the configured validation function."""
        return self.validation_function(edi_root, context, self.config)


class ValidationRuleBuilder:
    """Builder for creating validation rules with fluent interface."""
    
    def __init__(self):
        self._config = {}
    
    def name(self, rule_name: str) -> 'ValidationRuleBuilder':
        """Set the rule name."""
        self._config['name'] = rule_name
        return self
    
    def transactions(self, transaction_codes: List[str]) -> 'ValidationRuleBuilder':
        """Set supported transaction codes."""
        self._config['transactions'] = transaction_codes
        return self
    
    def description(self, desc: str) -> 'ValidationRuleBuilder':
        """Set rule description."""
        self._config['description'] = desc
        return self
    
    def severity(self, sev: str) -> 'ValidationRuleBuilder':
        """Set rule severity."""
        self._config['severity'] = sev
        return self
    
    def validator(self, func: Callable) -> 'ValidationRuleBuilder':
        """Set validation function."""
        self._config['validator'] = func
        return self
    
    def config(self, **kwargs) -> 'ValidationRuleBuilder':
        """Add configuration parameters."""
        self._config.update(kwargs)
        return self
    
    def build(self) -> ConfigurableValidationRule:
        """Build the validation rule."""
        return ConfigurableValidationRule(self._config.copy())


class ValidationEngineBuilder:
    """Builder for creating and configuring validation engines."""
    
    def __init__(self):
        self._engine = ValidationEngine()
        self._factory = GenericValidationRuleFactory()
    
    def add_rule(self, rule: BaseValidationRule) -> 'ValidationEngineBuilder':
        """Add a validation rule instance."""
        self._engine.register_rule_plugin(rule)
        return self
    
    def add_global_rule(self, rule: BaseValidationRule) -> 'ValidationEngineBuilder':
        """Add a global validation rule."""
        self._engine.register_global_rule(rule)
        return self
    
    def add_rule_from_config(self, config: Dict[str, Any]) -> 'ValidationEngineBuilder':
        """Add a validation rule from configuration."""
        rule = self._factory.create_rule(config)
        self._engine.register_rule_plugin(rule)
        return self
    
    def enable_rule(self, rule_name: str) -> 'ValidationEngineBuilder':
        """Enable a specific rule."""
        self._engine.enable_rule(rule_name)
        return self
    
    def disable_rule(self, rule_name: str) -> 'ValidationEngineBuilder':
        """Disable a specific rule."""
        self._engine.disable_rule(rule_name)
        return self
    
    def register_rule_type(self, rule_type: str, constructor: Callable) -> 'ValidationEngineBuilder':
        """Register a custom rule type."""
        self._factory.register_rule_type(rule_type, constructor)
        return self
    
    def build(self) -> ValidationEngine:
        """Build the validation engine."""
        return self._engine


def create_validation_engine() -> ValidationEngineBuilder:
    """Create a new validation engine builder."""
    return ValidationEngineBuilder()


def create_validation_rule() -> ValidationRuleBuilder:
    """Create a new validation rule builder."""
    return ValidationRuleBuilder()