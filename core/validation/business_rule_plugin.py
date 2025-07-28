"""
Business Rule Plugin for Integration with Validation Engine

This plugin integrates the enhanced business rule engine with the existing
validation framework, providing field-level validation and detailed error reporting.
"""

from typing import Dict, List, Any
from ..plugins.api import ValidationRulePlugin
from ..base.edi_ast import EdiRoot
from .business_rules_835 import create_835_business_rule_engine


class BusinessRuleValidationPlugin(ValidationRulePlugin):
    """Plugin that integrates business rule engine with validation framework."""
    
    def __init__(self):
        self.business_engine = create_835_business_rule_engine()
        self._rule_name = "enhanced_business_rules"
        self._supported_transactions = ["835"]
    
    @property
    def rule_name(self) -> str:
        return self._rule_name
    
    @property
    def supported_transactions(self) -> List[str]:
        return self._supported_transactions
    
    def validate(self, edi_root: EdiRoot, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Execute business rule validation on EDI document."""
        all_errors = []
        
        # Process each transaction
        for i, interchange in enumerate(edi_root.interchanges):
            for j, functional_group in enumerate(interchange.functional_groups):
                for k, transaction in enumerate(functional_group.transactions):
                    
                    # Get transaction code
                    tx_code = transaction.header.get("transaction_set_code", "")
                    if tx_code not in self.supported_transactions:
                        continue
                    
                    # Get transaction data
                    transaction_data = None
                    if hasattr(transaction, 'transaction_data') and transaction.transaction_data:
                        transaction_data = transaction.transaction_data
                    else:
                        transaction_data = transaction
                    
                    # Execute business rule validation
                    transaction_path = f"interchange[{i}].functional_group[{j}].transaction[{k}]"
                    
                    try:
                        business_errors = self.business_engine.validate_transaction(transaction_data)
                        
                        # Convert business errors to validation framework format
                        for error in business_errors:
                            formatted_error = self._format_business_error(error, transaction_path)
                            all_errors.append(formatted_error)
                            
                    except Exception as e:
                        # Handle validation engine errors
                        system_error = {
                            'severity': 'error',
                            'message': f'Business rule engine error: {str(e)}',
                            'code': 'BUSINESS_ENGINE_ERROR',
                            'path': transaction_path,
                            'context': {'exception': str(e)}
                        }
                        all_errors.append(system_error)
        
        return all_errors
    
    def _format_business_error(self, business_error: Dict[str, Any], transaction_path: str) -> Dict[str, Any]:
        """Format business engine error for validation framework."""
        
        # Extract key information
        severity = business_error.get('severity', 'error')
        message = business_error.get('message', 'Business rule validation failed')
        code = business_error.get('code', 'BUSINESS_RULE_ERROR')
        
        # Build path with field information if available
        path = transaction_path
        if 'field_path' in business_error:
            path = f"{transaction_path}.{business_error['field_path']}"
        elif 'claim_path' in business_error:
            path = f"{transaction_path}.{business_error['claim_path']}"
        elif 'claim_index' in business_error:
            path = f"{transaction_path}.claims[{business_error['claim_index']}]"
        
        # Build context with detailed information
        context = {
            'rule_category': business_error.get('rule_category', 'business'),
            'validation_type': 'business_rule'
        }
        
        # Add specific context based on error type
        if 'field_value' in business_error:
            context['field_value'] = business_error['field_value']
        
        if 'validator_type' in business_error:
            context['validator_type'] = business_error['validator_type']
        
        if 'parameters' in business_error:
            context['validation_parameters'] = business_error['parameters']
        
        # Add financial context for monetary errors
        if any(key in business_error for key in ['bpr_total', 'claims_total', 'difference']):
            context['financial_details'] = {
                k: business_error[k] for k in ['bpr_total', 'claims_total', 'difference', 'tolerance']
                if k in business_error
            }
        
        # Add calculation context
        if any(key in business_error for key in ['expected_value', 'actual_value']):
            context['calculation_details'] = {
                k: business_error[k] for k in ['expected_value', 'actual_value', 'calculation_type']
                if k in business_error
            }
        
        # Add adjustment context
        if 'adjustment_index' in business_error:
            context['adjustment_details'] = {
                'adjustment_index': business_error['adjustment_index'],
                'reason_code': business_error.get('reason_code'),
                'amount': business_error.get('amount')
            }
        
        # Add service line context
        if 'service_charge_total' in business_error or 'service_paid_total' in business_error:
            context['service_line_details'] = {
                k: business_error[k] for k in [
                    'service_charge_total', 'service_paid_total', 
                    'claim_charge_total', 'claim_paid_total'
                ] if k in business_error
            }
        
        # Add PLB context
        if 'plb_index' in business_error:
            context['plb_details'] = {
                'plb_index': business_error['plb_index'],
                'amount': business_error.get('amount'),
                'reason': business_error.get('reason')
            }
        
        return {
            'severity': severity,
            'message': message,
            'code': code,
            'path': path,
            'context': context
        }
    
    def get_business_rule_summary(self) -> Dict[str, Any]:
        """Get summary of business rules managed by this plugin."""
        return self.business_engine.list_business_rules()
    
    def validate_specific_field(self, edi_root: EdiRoot, field_path: str) -> List[Dict[str, Any]]:
        """Validate a specific field across all transactions."""
        all_errors = []
        
        for i, interchange in enumerate(edi_root.interchanges):
            for j, functional_group in enumerate(interchange.functional_groups):
                for k, transaction in enumerate(functional_group.transactions):
                    tx_code = transaction.header.get("transaction_set_code", "")
                    if tx_code not in self.supported_transactions:
                        continue
                    
                    transaction_data = getattr(transaction, 'transaction_data', transaction)
                    transaction_path = f"interchange[{i}].functional_group[{j}].transaction[{k}]"
                    
                    try:
                        field_errors = self.business_engine.validate_field(transaction_data, field_path)
                        
                        for error in field_errors:
                            formatted_error = self._format_business_error(error, transaction_path)
                            all_errors.append(formatted_error)
                            
                    except Exception as e:
                        system_error = {
                            'severity': 'error',
                            'message': f'Field validation error for {field_path}: {str(e)}',
                            'code': 'FIELD_VALIDATION_ERROR',
                            'path': f"{transaction_path}.{field_path}",
                            'context': {'exception': str(e)}
                        }
                        all_errors.append(system_error)
        
        return all_errors


class FieldLevelValidationPlugin(ValidationRulePlugin):
    """Specialized plugin for field-level validation reporting."""
    
    def __init__(self):
        self.business_engine = create_835_business_rule_engine()
        self._rule_name = "field_level_validation"
        self._supported_transactions = ["835"]
    
    @property
    def rule_name(self) -> str:
        return self._rule_name
    
    @property
    def supported_transactions(self) -> List[str]:
        return self._supported_transactions
    
    def validate(self, edi_root: EdiRoot, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Execute field-level validation with detailed reporting."""
        all_errors = []
        
        # Get field paths to validate from context
        field_paths = context.get('validate_fields', [])
        if not field_paths:
            # Default field paths for comprehensive validation
            field_paths = [
                'financial_information.total_paid',
                'financial_information.payment_method',
                'financial_information.payment_date',
                'payee.npi',
                'payee.tax_id',
                'claims[0].total_charge',
                'claims[0].total_paid',
                'claims[0].patient_responsibility',
                'claims[0].services[0].service_code',
                'claims[0].services[0].charge_amount',
                'claims[0].services[0].paid_amount'
            ]
        
        # Validate each field path
        for field_path in field_paths:
            try:
                field_errors = self._validate_single_field_path(edi_root, field_path)
                all_errors.extend(field_errors)
            except Exception as e:
                system_error = {
                    'severity': 'error',
                    'message': f'Field path validation error for {field_path}: {str(e)}',
                    'code': 'FIELD_PATH_ERROR',
                    'path': field_path,
                    'context': {'exception': str(e)}
                }
                all_errors.append(system_error)
        
        return all_errors
    
    def _validate_single_field_path(self, edi_root: EdiRoot, field_path: str) -> List[Dict[str, Any]]:
        """Validate a single field path across all transactions."""
        errors = []
        
        for i, interchange in enumerate(edi_root.interchanges):
            for j, functional_group in enumerate(interchange.functional_groups):
                for k, transaction in enumerate(functional_group.transactions):
                    tx_code = transaction.header.get("transaction_set_code", "")
                    if tx_code not in self.supported_transactions:
                        continue
                    
                    transaction_data = getattr(transaction, 'transaction_data', transaction)
                    transaction_path = f"interchange[{i}].functional_group[{j}].transaction[{k}]"
                    
                    # Get field validators for this path
                    validators = self.business_engine.get_field_validators_for_path(field_path)
                    
                    # Execute field validation
                    for validator in validators:
                        validator_errors = validator.validate(transaction_data)
                        
                        for error in validator_errors:
                            # Add detailed field-level context
                            error['field_path'] = field_path
                            error['transaction_path'] = transaction_path
                            error['validation_context'] = 'field_level'
                            
                            formatted_error = {
                                'severity': error.get('severity', 'error'),
                                'message': error.get('message', f'Field validation failed: {field_path}'),
                                'code': error.get('code', 'FIELD_VALIDATION_ERROR'),
                                'path': f"{transaction_path}.{field_path}",
                                'context': {
                                    'field_value': error.get('field_value'),
                                    'validator_type': error.get('validator_type'),
                                    'parameters': error.get('parameters', {}),
                                    'validation_level': 'field'
                                }
                            }
                            
                            errors.append(formatted_error)
        
        return errors