"""
YAML-based Validation Rule Configuration Loader

This module enables defining validation rules in YAML format, making it easy for
users to customize validation logic without writing Python code.
"""

import yaml
import os
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass
from pathlib import Path

from .rules import BaseValidationRule, ValidationContext
from ..base.edi_ast import EdiRoot


@dataclass
class YamlRuleCondition:
    """Represents a condition in a YAML validation rule."""
    field_path: str
    operator: str  # eq, ne, gt, lt, gte, lte, in, not_in, exists, not_exists, matches, not_matches
    value: Any
    message: Optional[str] = None


@dataclass 
class YamlValidationRule:
    """Represents a validation rule defined in YAML."""
    name: str
    description: str
    severity: str = "error"
    transaction_types: List[str] = None
    enabled: bool = True
    conditions: List[YamlRuleCondition] = None
    custom_message: Optional[str] = None
    error_code: Optional[str] = None
    category: str = "business"  # structural, business, data, compliance


class YamlValidationRulePlugin(BaseValidationRule):
    """Validation rule plugin that executes YAML-defined rules."""
    
    def __init__(self, yaml_rule: YamlValidationRule):
        self.yaml_rule = yaml_rule
        super().__init__(
            rule_name=yaml_rule.name,
            supported_transactions=yaml_rule.transaction_types or ["835"],
            description=yaml_rule.description,
            severity=yaml_rule.severity
        )
    
    def validate_document(self, edi_root: EdiRoot, context: ValidationContext) -> List[Dict[str, Any]]:
        """Execute YAML-defined validation rule."""
        if not self.yaml_rule.enabled:
            return []
        
        errors = []
        
        # Process each transaction
        for i, interchange in enumerate(edi_root.interchanges):
            for j, functional_group in enumerate(interchange.functional_groups):
                for k, transaction in enumerate(functional_group.transactions):
                    tx_code = transaction.header.get("transaction_set_code", "")
                    
                    # Check if rule applies to this transaction type
                    if tx_code not in self.supported_transactions:
                        continue
                    
                    tx_path = f"interchange[{i}].functional_group[{j}].transaction[{k}]"
                    
                    # Execute conditions for this transaction
                    for condition in (self.yaml_rule.conditions or []):
                        if self._evaluate_condition(transaction, condition, context):
                            error = self._create_error_from_condition(condition, tx_path)
                            errors.append(error)
        
        return errors
    
    def _evaluate_condition(self, transaction, condition: YamlRuleCondition, context: ValidationContext) -> bool:
        """Evaluate a single condition against a transaction."""
        try:
            # Extract the value from the transaction using field path
            actual_value = self._extract_field_value(transaction, condition.field_path)
            
            # Apply the operator
            return self._apply_operator(actual_value, condition.operator, condition.value)
            
        except Exception:
            # If we can't evaluate the condition, assume it doesn't match
            return False
    
    def _extract_field_value(self, transaction, field_path: str) -> Any:
        """Extract a field value from a transaction using dot notation path."""
        # Start with transaction data if available
        current = transaction.transaction_data if hasattr(transaction, 'transaction_data') else transaction
        
        if not current:
            return None
        
        # Handle special case for header fields
        if field_path.startswith("header."):
            current = transaction.header
            field_path = field_path[7:]  # Remove "header."
        
        # Navigate the path
        parts = field_path.split('.')
        for part in parts:
            if part == "":
                continue
                
            # Handle array indexing like claims[0]
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
    
    def _apply_operator(self, actual: Any, operator: str, expected: Any) -> bool:
        """Apply comparison operator."""
        if operator == "exists":
            return actual is not None
        elif operator == "not_exists":
            return actual is None
        elif actual is None:
            return False  # Can't compare None values for other operators
        
        try:
            if operator == "eq":
                return actual == expected
            elif operator == "ne":
                return actual != expected
            elif operator == "gt":
                return float(actual) > float(expected)
            elif operator == "lt":
                return float(actual) < float(expected)
            elif operator == "gte":
                return float(actual) >= float(expected)
            elif operator == "lte":
                return float(actual) <= float(expected)
            elif operator == "in":
                return actual in expected if isinstance(expected, (list, tuple, set)) else False
            elif operator == "not_in":
                return actual not in expected if isinstance(expected, (list, tuple, set)) else True
            elif operator == "matches":
                import re
                return bool(re.search(str(expected), str(actual)))
            elif operator == "not_matches":
                import re
                return not bool(re.search(str(expected), str(actual)))
            else:
                return False
        except (ValueError, TypeError):
            return False
    
    def _create_error_from_condition(self, condition: YamlRuleCondition, path: str) -> Dict[str, Any]:
        """Create validation error from a condition."""
        message = condition.message or self.yaml_rule.custom_message or f"Validation failed for {condition.field_path}"
        code = self.yaml_rule.error_code or f"{self.yaml_rule.name.upper()}_FAILED"
        
        return self.create_error(
            message=message,
            code=code,
            path=path,
            context={
                'field_path': condition.field_path,
                'operator': condition.operator,
                'expected_value': condition.value,
                'rule_category': self.yaml_rule.category
            }
        )


class YamlValidationLoader:
    """Loads and parses YAML validation rule files."""
    
    def __init__(self):
        self.loaded_rules: Dict[str, YamlValidationRulePlugin] = {}
    
    def load_from_file(self, file_path: str) -> List[YamlValidationRulePlugin]:
        """Load validation rules from a YAML file."""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Validation rules file not found: {file_path}")
        
        with open(file_path, 'r', encoding='utf-8') as f:
            yaml_content = yaml.safe_load(f)
        
        return self.load_from_dict(yaml_content)
    
    def load_from_string(self, yaml_content: str) -> List[YamlValidationRulePlugin]:
        """Load validation rules from a YAML string."""
        yaml_dict = yaml.safe_load(yaml_content)
        return self.load_from_dict(yaml_dict)
    
    def load_from_dict(self, yaml_dict: Dict[str, Any]) -> List[YamlValidationRulePlugin]:
        """Load validation rules from a parsed YAML dictionary."""
        rules = []
        
        if 'rules' not in yaml_dict:
            raise ValueError("YAML validation file must contain a 'rules' section")
        
        for rule_dict in yaml_dict['rules']:
            try:
                yaml_rule = self._parse_rule_dict(rule_dict)
                plugin = YamlValidationRulePlugin(yaml_rule)
                rules.append(plugin)
                self.loaded_rules[yaml_rule.name] = plugin
            except Exception as e:
                raise ValueError(f"Error parsing rule {rule_dict.get('name', 'unknown')}: {str(e)}")
        
        return rules
    
    def _parse_rule_dict(self, rule_dict: Dict[str, Any]) -> YamlValidationRule:
        """Parse a single rule dictionary into a YamlValidationRule."""
        # Required fields
        name = rule_dict.get('name')
        if not name:
            raise ValueError("Rule must have a 'name' field")
        
        description = rule_dict.get('description', '')
        
        # Optional fields
        severity = rule_dict.get('severity', 'error')
        if severity not in ['error', 'warning', 'info']:
            raise ValueError(f"Invalid severity '{severity}'. Must be: error, warning, info")
        
        transaction_types = rule_dict.get('transaction_types', ['835'])
        if isinstance(transaction_types, str):
            transaction_types = [transaction_types]
        
        enabled = rule_dict.get('enabled', True)
        custom_message = rule_dict.get('message')
        error_code = rule_dict.get('error_code')
        category = rule_dict.get('category', 'business')
        
        # Parse conditions
        conditions = []
        conditions_list = rule_dict.get('conditions', [])
        
        for condition_dict in conditions_list:
            condition = self._parse_condition_dict(condition_dict)
            conditions.append(condition)
        
        return YamlValidationRule(
            name=name,
            description=description,
            severity=severity,
            transaction_types=transaction_types,
            enabled=enabled,
            conditions=conditions,
            custom_message=custom_message,
            error_code=error_code,
            category=category
        )
    
    def _parse_condition_dict(self, condition_dict: Dict[str, Any]) -> YamlRuleCondition:
        """Parse a condition dictionary into a YamlRuleCondition."""
        field_path = condition_dict.get('field')
        if not field_path:
            raise ValueError("Condition must have a 'field' parameter")
        
        operator = condition_dict.get('operator', 'eq')
        valid_operators = ['eq', 'ne', 'gt', 'lt', 'gte', 'lte', 'in', 'not_in', 
                          'exists', 'not_exists', 'matches', 'not_matches']
        if operator not in valid_operators:
            raise ValueError(f"Invalid operator '{operator}'. Must be one of: {', '.join(valid_operators)}")
        
        value = condition_dict.get('value')
        message = condition_dict.get('message')
        
        return YamlRuleCondition(
            field_path=field_path,
            operator=operator,
            value=value,
            message=message
        )
    
    def get_rule(self, rule_name: str) -> Optional[YamlValidationRulePlugin]:
        """Get a loaded rule by name."""
        return self.loaded_rules.get(rule_name)
    
    def list_rules(self) -> List[str]:
        """List all loaded rule names."""
        return list(self.loaded_rules.keys())