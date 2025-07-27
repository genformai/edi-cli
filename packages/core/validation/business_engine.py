"""
Enhanced Business Rule Engine for Field-Level Validation

This module provides sophisticated business rule validation capabilities with
field-level validation, mathematical computations, and detailed error reporting.
"""

from typing import Dict, List, Any, Optional, Callable, Union
from dataclasses import dataclass, field
from decimal import Decimal, InvalidOperation
from datetime import datetime, date
import re
import math
from enum import Enum

from ..base.edi_ast import EdiRoot
from .engine import ValidationError, ValidationSeverity


class BusinessRuleSeverity(Enum):
    """Business rule severity levels."""
    CRITICAL = "critical"  # Blocking business logic errors
    ERROR = "error"        # Standard business rule violations
    WARNING = "warning"    # Business logic concerns
    INFO = "info"         # Business insights/notifications


@dataclass
class FieldValidator:
    """Validates individual fields with business logic."""
    field_path: str
    validator_type: str
    parameters: Dict[str, Any] = field(default_factory=dict)
    error_message: str = ""
    severity: BusinessRuleSeverity = BusinessRuleSeverity.ERROR
    
    def validate(self, transaction_data: Any) -> List[Dict[str, Any]]:
        """Execute field validation and return errors."""
        errors = []
        
        try:
            # Extract field value
            value = self._extract_field_value(transaction_data, self.field_path)
            
            # Apply validation logic
            if not self._validate_field(value):
                errors.append({
                    'severity': self.severity.value,
                    'message': self.error_message or f"Field validation failed: {self.field_path}",
                    'code': f"FIELD_VALIDATION_{self.validator_type.upper()}",
                    'field_path': self.field_path,
                    'field_value': str(value) if value is not None else None,
                    'validator_type': self.validator_type,
                    'parameters': self.parameters
                })
        except Exception as e:
            errors.append({
                'severity': 'error',
                'message': f"Field validation error for {self.field_path}: {str(e)}",
                'code': 'FIELD_VALIDATION_ERROR',
                'field_path': self.field_path,
                'exception': str(e)
            })
        
        return errors
    
    def _extract_field_value(self, transaction_data: Any, field_path: str) -> Any:
        """Extract field value using dot notation path."""
        current = transaction_data
        
        # Handle header fields
        if field_path.startswith("header."):
            if hasattr(transaction_data, 'header'):
                current = transaction_data.header if hasattr(transaction_data, 'header') else None
            field_path = field_path[7:]  # Remove "header."
        
        if not current:
            return None
        
        # Navigate the path
        parts = field_path.split('.')
        for part in parts:
            if part == "":
                continue
            
            # Handle array indexing
            if '[' in part and ']' in part:
                field_name = part[:part.index('[')]
                index_str = part[part.index('[')+1:part.index(']')]
                
                try:
                    index = int(index_str)
                    if hasattr(current, field_name):
                        array_field = getattr(current, field_name)
                        if isinstance(array_field, list) and 0 <= index < len(array_field):
                            current = array_field[index]
                        else:
                            return None
                    elif isinstance(current, dict) and field_name in current:
                        array_field = current[field_name]
                        if isinstance(array_field, list) and 0 <= index < len(array_field):
                            current = array_field[index]
                        else:
                            return None
                    else:
                        return None
                except (ValueError, TypeError):
                    return None
            else:
                # Simple field access
                if hasattr(current, part):
                    current = getattr(current, part)
                elif isinstance(current, dict) and part in current:
                    current = current[part]
                else:
                    return None
        
        return current
    
    def _validate_field(self, value: Any) -> bool:
        """Apply specific validation logic based on validator type."""
        if self.validator_type == "currency_format":
            return self._validate_currency_format(value)
        elif self.validator_type == "date_format":
            return self._validate_date_format(value)
        elif self.validator_type == "npi_format":
            return self._validate_npi_format(value)
        elif self.validator_type == "tax_id_format":
            return self._validate_tax_id_format(value)
        elif self.validator_type == "range":
            return self._validate_range(value)
        elif self.validator_type == "enum":
            return self._validate_enum(value)
        elif self.validator_type == "regex":
            return self._validate_regex(value)
        elif self.validator_type == "required":
            return self._validate_required(value)
        elif self.validator_type == "conditional_required":
            return self._validate_conditional_required(value)
        else:
            return True
    
    def _validate_currency_format(self, value: Any) -> bool:
        """Validate currency format and reasonable amounts."""
        if value is None:
            return True
        
        try:
            decimal_value = Decimal(str(value))
            
            # Check for reasonable precision (max 2 decimal places for currency)
            if abs(decimal_value.as_tuple().exponent) > 2:
                return False
            
            # Check range if specified
            min_val = self.parameters.get('min_value', -999999999.99)
            max_val = self.parameters.get('max_value', 999999999.99)
            
            return min_val <= decimal_value <= max_val
            
        except (InvalidOperation, ValueError):
            return False
    
    def _validate_date_format(self, value: Any) -> bool:
        """Validate date format (CCYYMMDD or other specified formats)."""
        if value is None or value == "":
            return not self.parameters.get('required', False)
        
        date_format = self.parameters.get('format', '%Y%m%d')
        
        try:
            parsed_date = datetime.strptime(str(value), date_format).date()
            
            # Check date range if specified
            min_date = self.parameters.get('min_date')
            max_date = self.parameters.get('max_date')
            
            if min_date and parsed_date < min_date:
                return False
            if max_date and parsed_date > max_date:
                return False
            
            return True
            
        except ValueError:
            return False
    
    def _validate_npi_format(self, value: Any) -> bool:
        """Validate NPI format (10 digits)."""
        if value is None or value == "":
            return not self.parameters.get('required', False)
        
        return bool(re.match(r'^\d{10}$', str(value)))
    
    def _validate_tax_id_format(self, value: Any) -> bool:
        """Validate Tax ID format (EIN: XX-XXXXXXX or SSN: XXX-XX-XXXX)."""
        if value is None or value == "":
            return not self.parameters.get('required', False)
        
        value_str = str(value)
        
        # EIN format: XX-XXXXXXX
        if re.match(r'^\d{2}-\d{7}$', value_str):
            return True
        
        # SSN format: XXX-XX-XXXX
        if re.match(r'^\d{3}-\d{2}-\d{4}$', value_str):
            return True
        
        # Sometimes without dashes
        if re.match(r'^\d{9}$', value_str):
            return True
        
        return False
    
    def _validate_range(self, value: Any) -> bool:
        """Validate numeric range."""
        if value is None:
            return not self.parameters.get('required', False)
        
        try:
            numeric_value = float(value)
            min_val = self.parameters.get('min', float('-inf'))
            max_val = self.parameters.get('max', float('inf'))
            
            return min_val <= numeric_value <= max_val
            
        except (ValueError, TypeError):
            return False
    
    def _validate_enum(self, value: Any) -> bool:
        """Validate value is in allowed enumeration."""
        if value is None:
            return not self.parameters.get('required', False)
        
        allowed_values = self.parameters.get('values', [])
        return str(value) in [str(v) for v in allowed_values]
    
    def _validate_regex(self, value: Any) -> bool:
        """Validate against regular expression pattern."""
        if value is None:
            return not self.parameters.get('required', False)
        
        pattern = self.parameters.get('pattern', '.*')
        return bool(re.match(pattern, str(value)))
    
    def _validate_required(self, value: Any) -> bool:
        """Validate field is present and not empty."""
        return value is not None and str(value).strip() != ""
    
    def _validate_conditional_required(self, value: Any) -> bool:
        """Validate field is required under certain conditions."""
        # This would need additional context to evaluate conditions
        # For now, just check if present
        return value is not None


@dataclass
class BusinessRule:
    """Complex business rule with multiple field validations and calculations."""
    name: str
    description: str
    category: str
    severity: BusinessRuleSeverity
    field_validators: List[FieldValidator] = field(default_factory=list)
    cross_field_validations: List[Dict[str, Any]] = field(default_factory=list)
    custom_validation_function: Optional[Callable] = None
    enabled: bool = True
    
    def validate(self, transaction_data: Any) -> List[Dict[str, Any]]:
        """Execute complete business rule validation."""
        if not self.enabled:
            return []
        
        errors = []
        
        # Execute field validators
        for field_validator in self.field_validators:
            field_errors = field_validator.validate(transaction_data)
            errors.extend(field_errors)
        
        # Execute cross-field validations
        for cross_validation in self.cross_field_validations:
            cross_errors = self._execute_cross_field_validation(transaction_data, cross_validation)
            errors.extend(cross_errors)
        
        # Execute custom validation function
        if self.custom_validation_function:
            try:
                custom_errors = self.custom_validation_function(transaction_data)
                if custom_errors:
                    errors.extend(custom_errors)
            except Exception as e:
                errors.append({
                    'severity': 'error',
                    'message': f"Custom validation error in rule {self.name}: {str(e)}",
                    'code': 'CUSTOM_VALIDATION_ERROR',
                    'rule_name': self.name,
                    'exception': str(e)
                })
        
        return errors
    
    def _execute_cross_field_validation(self, transaction_data: Any, validation: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Execute cross-field validation logic."""
        errors = []
        validation_type = validation.get('type', '')
        
        try:
            if validation_type == 'balance_check':
                errors.extend(self._validate_balance_check(transaction_data, validation))
            elif validation_type == 'consistency_check':
                errors.extend(self._validate_consistency_check(transaction_data, validation))
            elif validation_type == 'calculation_check':
                errors.extend(self._validate_calculation_check(transaction_data, validation))
            elif validation_type == 'logical_check':
                errors.extend(self._validate_logical_check(transaction_data, validation))
                
        except Exception as e:
            errors.append({
                'severity': 'error',
                'message': f"Cross-field validation error: {str(e)}",
                'code': 'CROSS_FIELD_VALIDATION_ERROR',
                'validation_type': validation_type,
                'exception': str(e)
            })
        
        return errors
    
    def _validate_balance_check(self, transaction_data: Any, validation: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Validate financial balance across multiple fields."""
        errors = []
        
        total_field = validation.get('total_field', '')
        sum_fields = validation.get('sum_fields', [])
        tolerance = Decimal(str(validation.get('tolerance', '0.01')))
        
        # Extract values
        total_value = self._extract_currency_value(transaction_data, total_field)
        sum_value = Decimal('0')
        
        for sum_field in sum_fields:
            field_value = self._extract_currency_value(transaction_data, sum_field)
            if field_value is not None:
                sum_value += field_value
        
        # Check balance
        if total_value is not None and abs(total_value - sum_value) > tolerance:
            errors.append({
                'severity': validation.get('severity', 'warning'),
                'message': validation.get('message', f'Balance mismatch: {total_field} = {total_value}, sum = {sum_value}'),
                'code': validation.get('error_code', 'BALANCE_MISMATCH'),
                'total_field': total_field,
                'total_value': str(total_value),
                'sum_fields': sum_fields,
                'sum_value': str(sum_value),
                'difference': str(abs(total_value - sum_value))
            })
        
        return errors
    
    def _validate_consistency_check(self, transaction_data: Any, validation: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Validate consistency between related fields."""
        errors = []
        
        field1 = validation.get('field1', '')
        field2 = validation.get('field2', '')
        relationship = validation.get('relationship', 'equal')
        
        value1 = self._extract_field_value(transaction_data, field1)
        value2 = self._extract_field_value(transaction_data, field2)
        
        is_valid = False
        if relationship == 'equal':
            is_valid = value1 == value2
        elif relationship == 'not_equal':
            is_valid = value1 != value2
        elif relationship == 'greater_than':
            is_valid = self._safe_numeric_compare(value1, value2, lambda a, b: a > b)
        elif relationship == 'less_than':
            is_valid = self._safe_numeric_compare(value1, value2, lambda a, b: a < b)
        elif relationship == 'greater_equal':
            is_valid = self._safe_numeric_compare(value1, value2, lambda a, b: a >= b)
        elif relationship == 'less_equal':
            is_valid = self._safe_numeric_compare(value1, value2, lambda a, b: a <= b)
        
        if not is_valid:
            errors.append({
                'severity': validation.get('severity', 'warning'),
                'message': validation.get('message', f'Consistency check failed: {field1} {relationship} {field2}'),
                'code': validation.get('error_code', 'CONSISTENCY_CHECK_FAILED'),
                'field1': field1,
                'field1_value': str(value1) if value1 is not None else None,
                'field2': field2,
                'field2_value': str(value2) if value2 is not None else None,
                'relationship': relationship
            })
        
        return errors
    
    def _validate_calculation_check(self, transaction_data: Any, validation: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Validate mathematical calculations."""
        errors = []
        
        result_field = validation.get('result_field', '')
        calculation = validation.get('calculation', {})
        tolerance = Decimal(str(validation.get('tolerance', '0.01')))
        
        try:
            # Execute calculation
            calculated_value = self._execute_calculation(transaction_data, calculation)
            actual_value = self._extract_currency_value(transaction_data, result_field)
            
            if calculated_value is not None and actual_value is not None:
                if abs(calculated_value - actual_value) > tolerance:
                    errors.append({
                        'severity': validation.get('severity', 'warning'),
                        'message': validation.get('message', f'Calculation mismatch: expected {calculated_value}, got {actual_value}'),
                        'code': validation.get('error_code', 'CALCULATION_MISMATCH'),
                        'result_field': result_field,
                        'expected_value': str(calculated_value),
                        'actual_value': str(actual_value),
                        'difference': str(abs(calculated_value - actual_value))
                    })
                    
        except Exception as e:
            errors.append({
                'severity': 'error',
                'message': f'Calculation validation error: {str(e)}',
                'code': 'CALCULATION_ERROR',
                'result_field': result_field,
                'exception': str(e)
            })
        
        return errors
    
    def _validate_logical_check(self, transaction_data: Any, validation: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Validate logical business rules."""
        errors = []
        
        condition = validation.get('condition', {})
        
        try:
            if not self._evaluate_logical_condition(transaction_data, condition):
                errors.append({
                    'severity': validation.get('severity', 'info'),
                    'message': validation.get('message', 'Logical check failed'),
                    'code': validation.get('error_code', 'LOGICAL_CHECK_FAILED'),
                    'condition': condition
                })
                
        except Exception as e:
            errors.append({
                'severity': 'error',
                'message': f'Logical validation error: {str(e)}',
                'code': 'LOGICAL_VALIDATION_ERROR',
                'condition': condition,
                'exception': str(e)
            })
        
        return errors
    
    def _extract_field_value(self, transaction_data: Any, field_path: str) -> Any:
        """Extract field value using dot notation (same as FieldValidator)."""
        validator = FieldValidator(field_path, "dummy")
        return validator._extract_field_value(transaction_data, field_path)
    
    def _extract_currency_value(self, transaction_data: Any, field_path: str) -> Optional[Decimal]:
        """Extract currency value as Decimal."""
        value = self._extract_field_value(transaction_data, field_path)
        if value is None:
            return None
        
        try:
            return Decimal(str(value))
        except (InvalidOperation, ValueError):
            return None
    
    def _safe_numeric_compare(self, value1: Any, value2: Any, compare_func: Callable) -> bool:
        """Safely compare numeric values."""
        try:
            num1 = float(value1) if value1 is not None else None
            num2 = float(value2) if value2 is not None else None
            
            if num1 is None or num2 is None:
                return False
            
            return compare_func(num1, num2)
            
        except (ValueError, TypeError):
            return False
    
    def _execute_calculation(self, transaction_data: Any, calculation: Dict[str, Any]) -> Optional[Decimal]:
        """Execute mathematical calculation."""
        operation = calculation.get('operation', '')
        operands = calculation.get('operands', [])
        
        if operation == 'sum':
            total = Decimal('0')
            for operand in operands:
                value = self._extract_currency_value(transaction_data, operand)
                if value is not None:
                    total += value
            return total
        
        elif operation == 'subtract':
            if len(operands) >= 2:
                value1 = self._extract_currency_value(transaction_data, operands[0])
                value2 = self._extract_currency_value(transaction_data, operands[1])
                if value1 is not None and value2 is not None:
                    return value1 - value2
        
        elif operation == 'multiply':
            if len(operands) >= 2:
                result = Decimal('1')
                for operand in operands:
                    value = self._extract_currency_value(transaction_data, operand)
                    if value is not None:
                        result *= value
                    else:
                        return None
                return result
        
        elif operation == 'divide':
            if len(operands) >= 2:
                value1 = self._extract_currency_value(transaction_data, operands[0])
                value2 = self._extract_currency_value(transaction_data, operands[1])
                if value1 is not None and value2 is not None and value2 != 0:
                    return value1 / value2
        
        return None
    
    def _evaluate_logical_condition(self, transaction_data: Any, condition: Dict[str, Any]) -> bool:
        """Evaluate logical condition."""
        condition_type = condition.get('type', '')
        
        if condition_type == 'if_then':
            if_condition = condition.get('if', {})
            then_condition = condition.get('then', {})
            
            if self._evaluate_simple_condition(transaction_data, if_condition):
                return self._evaluate_simple_condition(transaction_data, then_condition)
            return True  # If condition not met, rule passes
        
        elif condition_type == 'and':
            conditions = condition.get('conditions', [])
            return all(self._evaluate_simple_condition(transaction_data, cond) for cond in conditions)
        
        elif condition_type == 'or':
            conditions = condition.get('conditions', [])
            return any(self._evaluate_simple_condition(transaction_data, cond) for cond in conditions)
        
        else:
            return self._evaluate_simple_condition(transaction_data, condition)
    
    def _evaluate_simple_condition(self, transaction_data: Any, condition: Dict[str, Any]) -> bool:
        """Evaluate simple field condition."""
        field_path = condition.get('field', '')
        operator = condition.get('operator', 'exists')
        expected_value = condition.get('value')
        
        actual_value = self._extract_field_value(transaction_data, field_path)
        
        if operator == 'exists':
            return actual_value is not None
        elif operator == 'not_exists':
            return actual_value is None
        elif operator == 'eq':
            return actual_value == expected_value
        elif operator == 'ne':
            return actual_value != expected_value
        elif operator == 'gt':
            return self._safe_numeric_compare(actual_value, expected_value, lambda a, b: a > b)
        elif operator == 'lt':
            return self._safe_numeric_compare(actual_value, expected_value, lambda a, b: a < b)
        elif operator == 'gte':
            return self._safe_numeric_compare(actual_value, expected_value, lambda a, b: a >= b)
        elif operator == 'lte':
            return self._safe_numeric_compare(actual_value, expected_value, lambda a, b: a <= b)
        elif operator == 'in':
            return actual_value in expected_value if isinstance(expected_value, (list, tuple)) else False
        elif operator == 'not_in':
            return actual_value not in expected_value if isinstance(expected_value, (list, tuple)) else True
        
        return True


class BusinessRuleEngine:
    """Enhanced business rule engine with field-level validation capabilities."""
    
    def __init__(self):
        self.business_rules: Dict[str, BusinessRule] = {}
        self.field_validators: Dict[str, List[FieldValidator]] = {}
        
    def register_business_rule(self, rule: BusinessRule):
        """Register a business rule."""
        self.business_rules[rule.name] = rule
        
        # Index field validators for quick lookup
        for field_validator in rule.field_validators:
            field_path = field_validator.field_path
            if field_path not in self.field_validators:
                self.field_validators[field_path] = []
            self.field_validators[field_path].append(field_validator)
    
    def validate_transaction(self, transaction_data: Any, rule_names: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """Validate transaction using business rules."""
        errors = []
        
        # Determine which rules to execute
        rules_to_execute = []
        if rule_names:
            rules_to_execute = [self.business_rules[name] for name in rule_names if name in self.business_rules]
        else:
            rules_to_execute = list(self.business_rules.values())
        
        # Execute business rules
        for rule in rules_to_execute:
            if rule.enabled:
                rule_errors = rule.validate(transaction_data)
                for error in rule_errors:
                    error['rule_name'] = rule.name
                    error['rule_category'] = rule.category
                errors.extend(rule_errors)
        
        return errors
    
    def validate_field(self, transaction_data: Any, field_path: str) -> List[Dict[str, Any]]:
        """Validate specific field using registered validators."""
        errors = []
        
        validators = self.field_validators.get(field_path, [])
        for validator in validators:
            field_errors = validator.validate(transaction_data)
            errors.extend(field_errors)
        
        return errors
    
    def get_field_validators_for_path(self, field_path: str) -> List[FieldValidator]:
        """Get all field validators for a specific path."""
        return self.field_validators.get(field_path, [])
    
    def list_business_rules(self) -> Dict[str, Dict[str, Any]]:
        """List all registered business rules."""
        return {
            name: {
                'description': rule.description,
                'category': rule.category,
                'severity': rule.severity.value,
                'enabled': rule.enabled,
                'field_validator_count': len(rule.field_validators),
                'cross_validation_count': len(rule.cross_field_validations),
                'has_custom_function': rule.custom_validation_function is not None
            }
            for name, rule in self.business_rules.items()
        }