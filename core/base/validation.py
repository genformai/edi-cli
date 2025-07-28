"""
EDI Validation Engine

This module provides comprehensive validation capabilities for EDI documents,
including business rules, HIPAA compliance, and custom validation logic.
"""

from typing import Dict, List, Any, Optional, Union, Callable
from dataclasses import dataclass, field
from enum import Enum
import re
import yaml
from pathlib import Path
from datetime import datetime, date
import logging

logger = logging.getLogger(__name__)


class ValidationSeverity(Enum):
    """Validation error severity levels."""
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


class ValidationCategory(Enum):
    """Categories of validation rules."""
    STRUCTURAL = "structural"
    BUSINESS = "business"
    HIPAA = "hipaa"
    FORMAT = "format"
    CUSTOM = "custom"


@dataclass
class ValidationError:
    """Represents a validation error or warning."""
    code: str
    message: str
    severity: ValidationSeverity
    category: ValidationCategory
    segment: Optional[str] = None
    element: Optional[str] = None
    field_path: Optional[str] = None
    value: Optional[Any] = None
    expected: Optional[Any] = None
    rule_id: Optional[str] = None


@dataclass
class ValidationResult:
    """Results of validation process."""
    is_valid: bool
    errors: List[ValidationError] = field(default_factory=list)
    warnings: List[ValidationError] = field(default_factory=list)
    info: List[ValidationError] = field(default_factory=list)
    rules_applied: int = 0
    
    def add_error(self, error: ValidationError):
        """Add a validation error."""
        if error.severity == ValidationSeverity.ERROR:
            self.errors.append(error)
            self.is_valid = False
        elif error.severity == ValidationSeverity.WARNING:
            self.warnings.append(error)
        else:
            self.info.append(error)
    
    def get_all_issues(self) -> List[ValidationError]:
        """Get all validation issues sorted by severity."""
        return self.errors + self.warnings + self.info
    
    def summary(self) -> Dict[str, int]:
        """Get summary of validation results."""
        return {
            "errors": len(self.errors),
            "warnings": len(self.warnings),
            "info": len(self.info),
            "rules_applied": self.rules_applied
        }


class ValidationRule:
    """Base class for validation rules."""
    
    def __init__(self, rule_id: str, description: str, severity: ValidationSeverity, 
                 category: ValidationCategory):
        self.rule_id = rule_id
        self.description = description
        self.severity = severity
        self.category = category
    
    def validate(self, edi_root, context: Dict[str, Any] = None) -> List[ValidationError]:
        """
        Validate the EDI document.
        
        Args:
            edi_root: Parsed EDI document
            context: Additional context for validation
            
        Returns:
            List of validation errors
        """
        raise NotImplementedError


class FieldValidationRule(ValidationRule):
    """Rule for validating specific fields."""
    
    def __init__(self, rule_id: str, description: str, severity: ValidationSeverity,
                 category: ValidationCategory, field_path: str, 
                 validator: Callable[[Any], bool], expected_format: str = None):
        super().__init__(rule_id, description, severity, category)
        self.field_path = field_path
        self.validator = validator
        self.expected_format = expected_format
    
    def validate(self, edi_root, context: Dict[str, Any] = None) -> List[ValidationError]:
        """Validate a specific field."""
        errors = []
        
        # Navigate to the field using the path
        try:
            value = self._get_field_value(edi_root, self.field_path)
            if value is not None and not self.validator(value):
                errors.append(ValidationError(
                    code=self.rule_id,
                    message=self.description,
                    severity=self.severity,
                    category=self.category,
                    field_path=self.field_path,
                    value=value,
                    expected=self.expected_format,
                    rule_id=self.rule_id
                ))
        except Exception as e:
            logger.warning(f"Error validating field {self.field_path}: {e}")
        
        return errors
    
    def _get_field_value(self, obj, path: str):
        """Navigate object hierarchy using dot notation."""
        parts = path.split('.')
        current = obj
        
        for part in parts:
            if hasattr(current, part):
                current = getattr(current, part)
            elif isinstance(current, dict) and part in current:
                current = current[part]
            elif isinstance(current, list) and part.isdigit():
                current = current[int(part)]
            else:
                return None
        
        return current


class BusinessRule(ValidationRule):
    """Complex business logic validation rule."""
    
    def __init__(self, rule_id: str, description: str, severity: ValidationSeverity,
                 category: ValidationCategory, condition: Callable, error_message: str):
        super().__init__(rule_id, description, severity, category)
        self.condition = condition
        self.error_message = error_message
    
    def validate(self, edi_root, context: Dict[str, Any] = None) -> List[ValidationError]:
        """Validate business rule."""
        errors = []
        
        try:
            if not self.condition(edi_root, context or {}):
                errors.append(ValidationError(
                    code=self.rule_id,
                    message=self.error_message,
                    severity=self.severity,
                    category=self.category,
                    rule_id=self.rule_id
                ))
        except Exception as e:
            logger.error(f"Error in business rule {self.rule_id}: {e}")
            errors.append(ValidationError(
                code=f"{self.rule_id}_ERROR",
                message=f"Rule execution failed: {str(e)}",
                severity=ValidationSeverity.ERROR,
                category=ValidationCategory.CUSTOM,
                rule_id=self.rule_id
            ))
        
        return errors


class ValidationEngine:
    """Main validation engine that applies rules to EDI documents."""
    
    def __init__(self):
        self.rules: List[ValidationRule] = []
        self.rule_sets: Dict[str, List[ValidationRule]] = {}
    
    def add_rule(self, rule: ValidationRule):
        """Add a validation rule."""
        self.rules.append(rule)
    
    def add_rule_set(self, name: str, rules: List[ValidationRule]):
        """Add a named set of rules."""
        self.rule_sets[name] = rules
    
    def load_rules_from_yaml(self, yaml_path: str) -> int:
        """Load validation rules from YAML configuration."""
        try:
            with open(yaml_path, 'r') as f:
                config = yaml.safe_load(f)
            
            loaded_count = 0
            for rule_config in config.get('rules', []):
                rule = self._create_rule_from_config(rule_config)
                if rule:
                    self.add_rule(rule)
                    loaded_count += 1
            
            return loaded_count
        except Exception as e:
            logger.error(f"Failed to load rules from {yaml_path}: {e}")
            return 0
    
    def _create_rule_from_config(self, config: Dict[str, Any]) -> Optional[ValidationRule]:
        """Create a validation rule from YAML configuration."""
        try:
            rule_type = config.get('type', 'field')
            rule_id = config['id']
            description = config['description']
            severity = ValidationSeverity(config.get('severity', 'error'))
            category = ValidationCategory(config.get('category', 'business'))
            
            if rule_type == 'field':
                field_path = config['field_path']
                validation_type = config.get('validation_type', 'required')
                
                if validation_type == 'required':
                    validator = lambda x: x is not None and str(x).strip() != ''
                elif validation_type == 'regex':
                    pattern = re.compile(config['pattern'])
                    validator = lambda x: pattern.match(str(x)) if x else False
                elif validation_type == 'length':
                    min_len = config.get('min_length', 0)
                    max_len = config.get('max_length', float('inf'))
                    validator = lambda x: min_len <= len(str(x)) <= max_len if x else False
                elif validation_type == 'numeric':
                    validator = lambda x: str(x).replace('.', '').replace('-', '').isdigit() if x else False
                elif validation_type == 'custom':
                    validator_name = config.get('validator')
                    if validator_name == 'validate_npi':
                        validator = validate_npi
                    elif validator_name == 'validate_amount_format':
                        validator = validate_amount_format
                    elif validator_name == 'validate_control_number':
                        validator = validate_control_number
                    else:
                        logger.warning(f"Unknown custom validator: {validator_name}")
                        return None
                else:
                    logger.warning(f"Unknown validation type: {validation_type}")
                    return None
                
                return FieldValidationRule(
                    rule_id, description, severity, category,
                    field_path, validator, config.get('expected_format')
                )
            
            # Add more rule types as needed
            return None
            
        except Exception as e:
            logger.error(f"Failed to create rule from config: {e}")
            return None
    
    def validate(self, edi_root, rule_set: Optional[str] = None, 
                context: Dict[str, Any] = None) -> ValidationResult:
        """
        Validate an EDI document.
        
        Args:
            edi_root: Parsed EDI document
            rule_set: Optional rule set name to use
            context: Additional context for validation
            
        Returns:
            ValidationResult with all issues found
        """
        result = ValidationResult(is_valid=True)
        
        # Determine which rules to apply
        rules_to_apply = self.rule_sets.get(rule_set, self.rules) if rule_set else self.rules
        
        for rule in rules_to_apply:
            try:
                errors = rule.validate(edi_root, context)
                for error in errors:
                    result.add_error(error)
                result.rules_applied += 1
            except Exception as e:
                logger.error(f"Error applying rule {rule.rule_id}: {e}")
                result.add_error(ValidationError(
                    code=f"RULE_ERROR_{rule.rule_id}",
                    message=f"Rule execution failed: {str(e)}",
                    severity=ValidationSeverity.ERROR,
                    category=ValidationCategory.CUSTOM,
                    rule_id=rule.rule_id
                ))
        
        return result


# Built-in validation functions
def validate_date_format(date_str: str, format_str: str = "%Y-%m-%d") -> bool:
    """Validate date format."""
    try:
        datetime.strptime(date_str, format_str)
        return True
    except:
        return False


def validate_npi(npi: str) -> bool:
    """Validate National Provider Identifier (NPI)."""
    if not npi or len(npi) != 10 or not npi.isdigit():
        return False
    
    # Luhn algorithm check
    total = 0
    for i, digit in enumerate(npi):
        n = int(digit)
        if i % 2 == 0:
            n *= 2
            if n > 9:
                n = n // 10 + n % 10
        total += n
    
    return total % 10 == 0


def validate_amount_format(amount: Union[str, float, int]) -> bool:
    """Validate monetary amount format."""
    try:
        if isinstance(amount, (int, float)):
            return amount >= 0
        amount_str = str(amount).replace(',', '')
        float_amount = float(amount_str)
        return float_amount >= 0 and len(amount_str.split('.')[-1]) <= 2
    except:
        return False


def validate_control_number(control_num: str) -> bool:
    """Validate control number format."""
    return bool(control_num and len(control_num.strip()) > 0 and len(control_num) <= 9)