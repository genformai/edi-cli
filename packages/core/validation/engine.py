"""
Validation Engine for EDI Documents

This module provides the core validation engine that processes EDI documents
through registered validation rules and returns detailed validation results.
"""

from typing import List, Dict, Any, Optional, Set
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
import logging

from ..base.edi_ast import EdiRoot
from ..plugins.api import ValidationRulePlugin

logger = logging.getLogger(__name__)


class ValidationSeverity(Enum):
    """Severity levels for validation errors."""
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


@dataclass
class ValidationError:
    """Represents a validation error or warning."""
    rule_name: str
    severity: ValidationSeverity
    message: str
    code: str
    path: str = ""  # Path to the problematic element (e.g., "interchange[0].functional_group[0].transaction[0]")
    segment_id: Optional[str] = None
    element_position: Optional[int] = None
    value: Optional[str] = None
    context: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        result = {
            'rule_name': self.rule_name,
            'severity': self.severity.value,
            'message': self.message,
            'code': self.code,
            'path': self.path
        }
        
        if self.segment_id:
            result['segment_id'] = self.segment_id
        if self.element_position is not None:
            result['element_position'] = self.element_position
        if self.value is not None:
            result['value'] = self.value
        if self.context:
            result['context'] = self.context
            
        return result


@dataclass
class ValidationResult:
    """Results of EDI document validation."""
    is_valid: bool
    errors: List[ValidationError] = field(default_factory=list)
    warnings: List[ValidationError] = field(default_factory=list)
    info: List[ValidationError] = field(default_factory=list)
    executed_rules: List[str] = field(default_factory=list)
    skipped_rules: List[str] = field(default_factory=list)
    execution_time_ms: float = 0.0
    validation_timestamp: datetime = field(default_factory=datetime.now)
    
    @property
    def error_count(self) -> int:
        """Number of errors."""
        return len(self.errors)
    
    @property
    def warning_count(self) -> int:
        """Number of warnings."""
        return len(self.warnings)
    
    @property
    def info_count(self) -> int:
        """Number of info messages."""
        return len(self.info)
    
    @property
    def total_issues(self) -> int:
        """Total number of validation issues."""
        return self.error_count + self.warning_count + self.info_count
    
    def add_error(self, error: ValidationError):
        """Add a validation error."""
        if error.severity == ValidationSeverity.ERROR:
            self.errors.append(error)
            self.is_valid = False
        elif error.severity == ValidationSeverity.WARNING:
            self.warnings.append(error)
        elif error.severity == ValidationSeverity.INFO:
            self.info.append(error)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            'is_valid': self.is_valid,
            'error_count': self.error_count,
            'warning_count': self.warning_count,
            'info_count': self.info_count,
            'total_issues': self.total_issues,
            'errors': [error.to_dict() for error in self.errors],
            'warnings': [warning.to_dict() for warning in self.warnings],
            'info': [info.to_dict() for info in self.info],
            'executed_rules': self.executed_rules,
            'skipped_rules': self.skipped_rules,
            'execution_time_ms': self.execution_time_ms,
            'validation_timestamp': self.validation_timestamp.isoformat()
        }


class ValidationEngine:
    """Core validation engine for EDI documents."""
    
    def __init__(self):
        self.rule_plugins: Dict[str, List[ValidationRulePlugin]] = {}
        self.global_rules: List[ValidationRulePlugin] = []
        self.enabled_rules: Set[str] = set()
        self.disabled_rules: Set[str] = set()
        
    def register_rule_plugin(self, plugin: ValidationRulePlugin):
        """Register a validation rule plugin."""
        for transaction_code in plugin.supported_transactions:
            if transaction_code not in self.rule_plugins:
                self.rule_plugins[transaction_code] = []
            self.rule_plugins[transaction_code].append(plugin)
        
        # Enable rule by default
        self.enabled_rules.add(plugin.rule_name)
        
        logger.info(f"Registered validation rule: {plugin.rule_name} for transactions: {plugin.supported_transactions}")
    
    def register_global_rule(self, plugin: ValidationRulePlugin):
        """Register a global validation rule that applies to all transactions."""
        self.global_rules.append(plugin)
        self.enabled_rules.add(plugin.rule_name)
        logger.info(f"Registered global validation rule: {plugin.rule_name}")
    
    def enable_rule(self, rule_name: str):
        """Enable a specific validation rule."""
        self.enabled_rules.add(rule_name)
        self.disabled_rules.discard(rule_name)
    
    def disable_rule(self, rule_name: str):
        """Disable a specific validation rule."""
        self.disabled_rules.add(rule_name)
        self.enabled_rules.discard(rule_name)
    
    def validate(self, edi_root: EdiRoot, context: Optional[Dict[str, Any]] = None) -> ValidationResult:
        """
        Validate an EDI document using registered rules.
        
        Args:
            edi_root: The EDI document to validate
            context: Additional validation context
            
        Returns:
            ValidationResult with all validation issues found
        """
        start_time = datetime.now()
        result = ValidationResult(is_valid=True)
        validation_context = context or {}
        
        # Collect all applicable rules
        applicable_rules = []
        transaction_codes = self._extract_transaction_codes(edi_root)
        
        # Add global rules
        for rule in self.global_rules:
            if self._is_rule_enabled(rule.rule_name):
                applicable_rules.append(rule)
        
        # Add transaction-specific rules
        for transaction_code in transaction_codes:
            if transaction_code in self.rule_plugins:
                for rule in self.rule_plugins[transaction_code]:
                    if self._is_rule_enabled(rule.rule_name):
                        applicable_rules.append(rule)
        
        # Execute validation rules
        for rule in applicable_rules:
            try:
                logger.debug(f"Executing validation rule: {rule.rule_name}")
                
                # Execute the rule
                rule_errors = rule.validate(edi_root, validation_context)
                
                # Convert to ValidationError objects
                for error_dict in rule_errors:
                    error = self._dict_to_validation_error(error_dict, rule.rule_name)
                    result.add_error(error)
                
                result.executed_rules.append(rule.rule_name)
                
            except Exception as e:
                logger.error(f"Error executing validation rule {rule.rule_name}: {e}")
                # Add system error
                system_error = ValidationError(
                    rule_name=rule.rule_name,
                    severity=ValidationSeverity.ERROR,
                    message=f"Validation rule execution failed: {str(e)}",
                    code="SYSTEM_ERROR",
                    context={"exception": str(e)}
                )
                result.add_error(system_error)
                result.executed_rules.append(rule.rule_name)
        
        # Calculate execution time
        end_time = datetime.now()
        result.execution_time_ms = (end_time - start_time).total_seconds() * 1000
        
        logger.info(f"Validation completed: {result.error_count} errors, {result.warning_count} warnings, "
                   f"{result.info_count} info messages in {result.execution_time_ms:.2f}ms")
        
        return result
    
    def _extract_transaction_codes(self, edi_root: EdiRoot) -> Set[str]:
        """Extract all transaction codes from the EDI document."""
        transaction_codes = set()
        
        for interchange in edi_root.interchanges:
            for functional_group in interchange.functional_groups:
                for transaction in functional_group.transactions:
                    if "transaction_set_code" in transaction.header:
                        transaction_codes.add(transaction.header["transaction_set_code"])
        
        return transaction_codes
    
    def _is_rule_enabled(self, rule_name: str) -> bool:
        """Check if a validation rule is enabled."""
        if rule_name in self.disabled_rules:
            return False
        return rule_name in self.enabled_rules
    
    def _dict_to_validation_error(self, error_dict: Dict[str, Any], rule_name: str) -> ValidationError:
        """Convert a dictionary to a ValidationError object."""
        # Map severity string to enum
        severity_str = error_dict.get('severity', 'error').lower()
        severity = ValidationSeverity.ERROR
        
        if severity_str == 'warning':
            severity = ValidationSeverity.WARNING
        elif severity_str == 'info':
            severity = ValidationSeverity.INFO
        
        return ValidationError(
            rule_name=rule_name,
            severity=severity,
            message=error_dict.get('message', 'Validation error'),
            code=error_dict.get('code', 'UNKNOWN'),
            path=error_dict.get('path', ''),
            segment_id=error_dict.get('segment_id'),
            element_position=error_dict.get('element_position'),
            value=error_dict.get('value'),
            context=error_dict.get('context', {})
        )
    
    def get_rule_summary(self) -> Dict[str, Any]:
        """Get summary of registered validation rules."""
        summary = {
            'total_rules': len(self.enabled_rules) + len(self.disabled_rules),
            'enabled_rules': len(self.enabled_rules),
            'disabled_rules': len(self.disabled_rules),
            'global_rules': len(self.global_rules),
            'transaction_specific_rules': {}
        }
        
        for transaction_code, rules in self.rule_plugins.items():
            summary['transaction_specific_rules'][transaction_code] = len(rules)
        
        return summary