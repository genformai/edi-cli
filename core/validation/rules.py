"""
Base validation rules and context for EDI validation.

This module provides base classes and utilities for creating
validation rules that integrate with the plugin architecture.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime

from ..base.edi_ast import EdiRoot, Transaction, Interchange, FunctionalGroup
from ..plugins.api import ValidationRulePlugin


@dataclass
class ValidationContext:
    """Context object containing validation configuration and runtime data."""
    strict_mode: bool = False
    ignore_warnings: bool = False
    custom_rules: Dict[str, Any] = field(default_factory=dict)
    business_rules: Dict[str, Any] = field(default_factory=dict)
    trading_partner_id: Optional[str] = None
    validation_profile: str = "default"
    timestamp: datetime = field(default_factory=datetime.now)
    
    def get_custom_rule(self, rule_name: str, default=None):
        """Get a custom rule value."""
        return self.custom_rules.get(rule_name, default)
    
    def get_business_rule(self, rule_name: str, default=None):
        """Get a business rule value."""
        return self.business_rules.get(rule_name, default)


class BaseValidationRule(ValidationRulePlugin):
    """Base class for validation rules with common functionality."""
    
    def __init__(self, rule_name: str, supported_transactions: List[str], 
                 description: str = "", severity: str = "error"):
        self._rule_name = rule_name
        self._supported_transactions = supported_transactions
        self._description = description
        self._severity = severity
    
    @property
    def rule_name(self) -> str:
        return self._rule_name
    
    @property
    def supported_transactions(self) -> List[str]:
        return self._supported_transactions.copy()
    
    @property
    def description(self) -> str:
        return self._description
    
    @property
    def default_severity(self) -> str:
        return self._severity
    
    def create_error(self, message: str, code: str, path: str = "", 
                    severity: Optional[str] = None, **kwargs) -> Dict[str, Any]:
        """Create a validation error dictionary."""
        error = {
            'message': message,
            'code': code,
            'path': path,
            'severity': severity or self.default_severity
        }
        
        # Add optional fields
        for key, value in kwargs.items():
            if value is not None:
                error[key] = value
        
        return error
    
    @abstractmethod
    def validate_document(self, edi_root: EdiRoot, context: ValidationContext) -> List[Dict[str, Any]]:
        """
        Validate the EDI document and return validation errors.
        
        Subclasses should implement this method instead of the base validate method.
        """
        pass
    
    def validate(self, edi_root: EdiRoot, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Implementation of ValidationRulePlugin.validate()."""
        # Convert context dict to ValidationContext
        validation_context = ValidationContext()
        
        # Map common context fields
        if 'strict_mode' in context:
            validation_context.strict_mode = context['strict_mode']
        if 'ignore_warnings' in context:
            validation_context.ignore_warnings = context['ignore_warnings']
        if 'custom_rules' in context:
            validation_context.custom_rules = context['custom_rules']
        if 'business_rules' in context:
            validation_context.business_rules = context['business_rules']
        if 'trading_partner_id' in context:
            validation_context.trading_partner_id = context['trading_partner_id']
        if 'validation_profile' in context:
            validation_context.validation_profile = context['validation_profile']
        
        return self.validate_document(edi_root, validation_context)


class StructuralValidationRule(BaseValidationRule):
    """Base class for rules that validate EDI document structure."""
    
    def validate_interchange_structure(self, interchange: Interchange, path: str) -> List[Dict[str, Any]]:
        """Validate interchange structure. Override in subclasses."""
        return []
    
    def validate_functional_group_structure(self, functional_group: FunctionalGroup, path: str) -> List[Dict[str, Any]]:
        """Validate functional group structure. Override in subclasses."""
        return []
    
    def validate_transaction_structure(self, transaction: Transaction, path: str) -> List[Dict[str, Any]]:
        """Validate transaction structure. Override in subclasses."""
        return []
    
    def validate_document(self, edi_root: EdiRoot, context: ValidationContext) -> List[Dict[str, Any]]:
        """Validate structural elements of the EDI document."""
        errors = []
        
        for i, interchange in enumerate(edi_root.interchanges):
            interchange_path = f"interchange[{i}]"
            errors.extend(self.validate_interchange_structure(interchange, interchange_path))
            
            for j, functional_group in enumerate(interchange.functional_groups):
                fg_path = f"{interchange_path}.functional_group[{j}]"
                errors.extend(self.validate_functional_group_structure(functional_group, fg_path))
                
                for k, transaction in enumerate(functional_group.transactions):
                    tx_path = f"{fg_path}.transaction[{k}]"
                    errors.extend(self.validate_transaction_structure(transaction, tx_path))
        
        return errors


class BusinessValidationRule(BaseValidationRule):
    """Base class for rules that validate business logic."""
    
    def validate_business_logic(self, edi_root: EdiRoot, context: ValidationContext) -> List[Dict[str, Any]]:
        """Validate business logic. Override in subclasses."""
        return []
    
    def validate_document(self, edi_root: EdiRoot, context: ValidationContext) -> List[Dict[str, Any]]:
        """Validate business rules of the EDI document."""
        return self.validate_business_logic(edi_root, context)


class DataValidationRule(BaseValidationRule):
    """Base class for rules that validate data values and formats."""
    
    def validate_data_values(self, edi_root: EdiRoot, context: ValidationContext) -> List[Dict[str, Any]]:
        """Validate data values and formats. Override in subclasses."""
        return []
    
    def validate_document(self, edi_root: EdiRoot, context: ValidationContext) -> List[Dict[str, Any]]:
        """Validate data values in the EDI document."""
        return self.validate_data_values(edi_root, context)


class ComplianceValidationRule(BaseValidationRule):
    """Base class for rules that validate compliance with standards."""
    
    def __init__(self, rule_name: str, supported_transactions: List[str], 
                 standard_version: str, description: str = "", severity: str = "error"):
        super().__init__(rule_name, supported_transactions, description, severity)
        self.standard_version = standard_version
    
    def validate_compliance(self, edi_root: EdiRoot, context: ValidationContext) -> List[Dict[str, Any]]:
        """Validate compliance with EDI standards. Override in subclasses."""
        return []
    
    def validate_document(self, edi_root: EdiRoot, context: ValidationContext) -> List[Dict[str, Any]]:
        """Validate compliance rules of the EDI document."""
        return self.validate_compliance(edi_root, context)