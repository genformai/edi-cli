"""
Validation rules specific to EDI 835 (Electronic Remittance Advice) transactions.

These rules validate business logic, data integrity, and compliance
requirements specific to 835 transactions.
"""

from typing import List, Dict, Any
from decimal import Decimal, InvalidOperation

from .rules import BusinessValidationRule, DataValidationRule, StructuralValidationRule, ValidationContext
from ..base.edi_ast import EdiRoot, Transaction
from ..utils.validators import validate_npi, validate_amount_format


class Transaction835StructureRule(StructuralValidationRule):
    """Validates the structural integrity of 835 transactions."""
    
    def __init__(self):
        super().__init__(
            rule_name="835_structure_validation",
            supported_transactions=["835"],
            description="Validates required segments and structure for 835 transactions",
            severity="error"
        )
    
    def validate_transaction_structure(self, transaction: Transaction, path: str) -> List[Dict[str, Any]]:
        """Validate 835 transaction structure."""
        errors = []
        
        # Check transaction code
        if transaction.header.get("transaction_set_code") != "835":
            return errors  # Not our transaction type
        
        # Check if transaction has 835-specific data
        if not transaction.transaction_data:
            errors.append(self.create_error(
                message="835 transaction missing transaction data",
                code="835_MISSING_DATA",
                path=path
            ))
            return errors
        
        transaction_835 = transaction.transaction_data
        
        # Validate required financial information
        if not hasattr(transaction_835, 'financial_information') or not transaction_835.financial_information:
            errors.append(self.create_error(
                message="835 transaction missing required BPR (financial information) segment",
                code="835_MISSING_BPR",
                path=f"{path}.financial_information",
                segment_id="BPR"
            ))
        
        # Validate payer information
        if not hasattr(transaction_835, 'payer') or not transaction_835.payer:
            errors.append(self.create_error(
                message="835 transaction missing payer information",
                code="835_MISSING_PAYER",
                path=f"{path}.payer",
                severity="warning"
            ))
        
        # Validate payee information
        if not hasattr(transaction_835, 'payee') or not transaction_835.payee:
            errors.append(self.create_error(
                message="835 transaction missing payee information",
                code="835_MISSING_PAYEE",
                path=f"{path}.payee",
                severity="warning"
            ))
        
        return errors


class Transaction835DataValidationRule(DataValidationRule):
    """Validates data values and formats in 835 transactions."""
    
    def __init__(self):
        super().__init__(
            rule_name="835_data_validation",
            supported_transactions=["835"],
            description="Validates data formats and values in 835 transactions",
            severity="error"
        )
    
    def validate_data_values(self, edi_root: EdiRoot, context: ValidationContext) -> List[Dict[str, Any]]:
        """Validate data values in 835 transactions."""
        errors = []
        
        for i, interchange in enumerate(edi_root.interchanges):
            for j, functional_group in enumerate(interchange.functional_groups):
                for k, transaction in enumerate(functional_group.transactions):
                    if transaction.header.get("transaction_set_code") == "835":
                        tx_path = f"interchange[{i}].functional_group[{j}].transaction[{k}]"
                        errors.extend(self._validate_835_data(transaction, tx_path, context))
        
        return errors
    
    def _validate_835_data(self, transaction: Transaction, path: str, context: ValidationContext) -> List[Dict[str, Any]]:
        """Validate 835-specific data values."""
        errors = []
        
        if not transaction.transaction_data:
            return errors
        
        transaction_835 = transaction.transaction_data
        
        # Validate financial information
        if hasattr(transaction_835, 'financial_information') and transaction_835.financial_information:
            errors.extend(self._validate_financial_info(transaction_835.financial_information, f"{path}.financial_information"))
        
        # Validate payee NPI
        if hasattr(transaction_835, 'payee') and transaction_835.payee and hasattr(transaction_835.payee, 'npi'):
            if transaction_835.payee.npi and not validate_npi(transaction_835.payee.npi):
                errors.append(self.create_error(
                    message=f"Invalid payee NPI: {transaction_835.payee.npi}",
                    code="835_INVALID_PAYEE_NPI",
                    path=f"{path}.payee.npi",
                    value=transaction_835.payee.npi
                ))
        
        # Validate claims
        if hasattr(transaction_835, 'claims') and transaction_835.claims:
            for claim_idx, claim in enumerate(transaction_835.claims):
                claim_path = f"{path}.claims[{claim_idx}]"
                errors.extend(self._validate_claim_data(claim, claim_path, context))
        
        return errors
    
    def _validate_financial_info(self, financial_info, path: str) -> List[Dict[str, Any]]:
        """Validate financial information data."""
        errors = []
        
        # Validate total paid amount
        if hasattr(financial_info, 'total_paid'):
            try:
                amount = Decimal(str(financial_info.total_paid))
                if amount < 0:
                    errors.append(self.create_error(
                        message=f"Total paid amount cannot be negative: {amount}",
                        code="835_NEGATIVE_TOTAL_PAID",
                        path=f"{path}.total_paid",
                        value=str(amount),
                        severity="warning"
                    ))
            except (InvalidOperation, ValueError):
                errors.append(self.create_error(
                    message=f"Invalid total paid amount format: {financial_info.total_paid}",
                    code="835_INVALID_TOTAL_PAID_FORMAT",
                    path=f"{path}.total_paid",
                    value=str(financial_info.total_paid)
                ))
        
        # Validate payment method
        if hasattr(financial_info, 'payment_method'):
            valid_methods = ['ACH', 'CHK', 'FWT', 'BOP']
            if financial_info.payment_method not in valid_methods:
                errors.append(self.create_error(
                    message=f"Invalid payment method: {financial_info.payment_method}. Must be one of: {', '.join(valid_methods)}",
                    code="835_INVALID_PAYMENT_METHOD",
                    path=f"{path}.payment_method",
                    value=financial_info.payment_method,
                    severity="warning"
                ))
        
        return errors
    
    def _validate_claim_data(self, claim, path: str, context: ValidationContext) -> List[Dict[str, Any]]:
        """Validate claim-level data."""
        errors = []
        
        # Validate claim amounts
        if hasattr(claim, 'total_charge') and hasattr(claim, 'total_paid') and hasattr(claim, 'patient_responsibility'):
            try:
                charge = Decimal(str(claim.total_charge))
                paid = Decimal(str(claim.total_paid))
                patient_resp = Decimal(str(claim.patient_responsibility))
                
                # Check for negative amounts
                if charge < 0:
                    errors.append(self.create_error(
                        message=f"Claim charge amount cannot be negative: {charge}",
                        code="835_NEGATIVE_CLAIM_CHARGE",
                        path=f"{path}.total_charge",
                        value=str(charge)
                    ))
                
                if paid < 0:
                    errors.append(self.create_error(
                        message=f"Claim paid amount cannot be negative: {paid}",
                        code="835_NEGATIVE_CLAIM_PAID",
                        path=f"{path}.total_paid",
                        value=str(paid)
                    ))
                
                if patient_resp < 0:
                    errors.append(self.create_error(
                        message=f"Patient responsibility amount cannot be negative: {patient_resp}",
                        code="835_NEGATIVE_PATIENT_RESP",
                        path=f"{path}.patient_responsibility",
                        value=str(patient_resp)
                    ))
                
                # Validate financial balance (if in strict mode)
                if context.strict_mode:
                    total_accounted = paid + patient_resp
                    tolerance = Decimal('0.01')  # 1 cent tolerance
                    difference = abs(charge - total_accounted)
                    
                    if difference > tolerance:
                        errors.append(self.create_error(
                            message=f"Claim financial balance error: Charge ({charge}) does not equal Paid ({paid}) + Patient Responsibility ({patient_resp}). Difference: {difference}",
                            code="835_CLAIM_BALANCE_ERROR",
                            path=path,
                            context={
                                'charge': str(charge),
                                'paid': str(paid),
                                'patient_responsibility': str(patient_resp),
                                'difference': str(difference)
                            },
                            severity="warning"
                        ))
            
            except (InvalidOperation, ValueError) as e:
                errors.append(self.create_error(
                    message=f"Invalid claim amount format: {str(e)}",
                    code="835_INVALID_CLAIM_AMOUNT_FORMAT",
                    path=path
                ))
        
        # Validate claim status code
        if hasattr(claim, 'status_code'):
            valid_status_codes = [1, 2, 3, 4, 5, 19, 20, 21, 22, 23]
            if claim.status_code not in valid_status_codes:
                errors.append(self.create_error(
                    message=f"Invalid claim status code: {claim.status_code}. Must be one of: {', '.join(map(str, valid_status_codes))}",
                    code="835_INVALID_CLAIM_STATUS",
                    path=f"{path}.status_code",
                    value=str(claim.status_code),
                    severity="warning"
                ))
        
        return errors


class Transaction835BusinessRule(BusinessValidationRule):
    """Validates business logic for 835 transactions."""
    
    def __init__(self):
        super().__init__(
            rule_name="835_business_validation",
            supported_transactions=["835"],
            description="Validates business logic and rules for 835 transactions",
            severity="warning"
        )
    
    def validate_business_logic(self, edi_root: EdiRoot, context: ValidationContext) -> List[Dict[str, Any]]:
        """Validate business logic for 835 transactions."""
        errors = []
        
        for i, interchange in enumerate(edi_root.interchanges):
            for j, functional_group in enumerate(interchange.functional_groups):
                for k, transaction in enumerate(functional_group.transactions):
                    if transaction.header.get("transaction_set_code") == "835":
                        tx_path = f"interchange[{i}].functional_group[{j}].transaction[{k}]"
                        errors.extend(self._validate_835_business_rules(transaction, tx_path, context))
        
        return errors
    
    def _validate_835_business_rules(self, transaction: Transaction, path: str, context: ValidationContext) -> List[Dict[str, Any]]:
        """Validate 835-specific business rules."""
        errors = []
        
        if not transaction.transaction_data:
            return errors
        
        transaction_835 = transaction.transaction_data
        
        # Validate total paid vs claim payments
        if (hasattr(transaction_835, 'financial_information') and transaction_835.financial_information and
            hasattr(transaction_835, 'claims') and transaction_835.claims):
            
            errors.extend(self._validate_payment_totals(
                transaction_835.financial_information,
                transaction_835.claims,
                path,
                context
            ))
        
        # Validate claim completeness
        if hasattr(transaction_835, 'claims') and transaction_835.claims:
            for claim_idx, claim in enumerate(transaction_835.claims):
                claim_path = f"{path}.claims[{claim_idx}]"
                errors.extend(self._validate_claim_completeness(claim, claim_path, context))
        
        return errors
    
    def _validate_payment_totals(self, financial_info, claims, path: str, context: ValidationContext) -> List[Dict[str, Any]]:
        """Validate that total payment matches sum of claim payments."""
        errors = []
        
        try:
            total_paid = Decimal(str(financial_info.total_paid))
            claim_payments_sum = sum(Decimal(str(claim.total_paid)) for claim in claims if hasattr(claim, 'total_paid'))
            
            tolerance = Decimal('0.01')  # 1 cent tolerance
            difference = abs(total_paid - claim_payments_sum)
            
            if difference > tolerance:
                errors.append(self.create_error(
                    message=f"Total payment ({total_paid}) does not match sum of claim payments ({claim_payments_sum}). Difference: {difference}",
                    code="835_PAYMENT_TOTAL_MISMATCH",
                    path=path,
                    context={
                        'total_paid': str(total_paid),
                        'claim_payments_sum': str(claim_payments_sum),
                        'difference': str(difference),
                        'claim_count': len(claims)
                    }
                ))
        
        except (InvalidOperation, ValueError, AttributeError) as e:
            errors.append(self.create_error(
                message=f"Error validating payment totals: {str(e)}",
                code="835_PAYMENT_TOTAL_VALIDATION_ERROR",
                path=path
            ))
        
        return errors
    
    def _validate_claim_completeness(self, claim, path: str, context: ValidationContext) -> List[Dict[str, Any]]:
        """Validate that claims have required information for processing."""
        errors = []
        
        # Check for claim ID
        if not hasattr(claim, 'claim_id') or not claim.claim_id:
            errors.append(self.create_error(
                message="Claim missing required claim ID",
                code="835_MISSING_CLAIM_ID",
                path=f"{path}.claim_id"
            ))
        
        # Check for payer control number
        if not hasattr(claim, 'payer_control_number') or not claim.payer_control_number:
            errors.append(self.create_error(
                message="Claim missing payer control number",
                code="835_MISSING_PAYER_CONTROL_NUMBER",
                path=f"{path}.payer_control_number",
                severity="info"
            ))
        
        # Validate service lines if present
        if hasattr(claim, 'services') and claim.services:
            for svc_idx, service in enumerate(claim.services):
                svc_path = f"{path}.services[{svc_idx}]"
                
                # Check service code
                if not hasattr(service, 'service_code') or not service.service_code:
                    errors.append(self.create_error(
                        message="Service line missing service code",
                        code="835_MISSING_SERVICE_CODE",
                        path=f"{svc_path}.service_code"
                    ))
                
                # Check amounts are consistent
                if (hasattr(service, 'charge_amount') and hasattr(service, 'paid_amount') and
                    service.charge_amount is not None and service.paid_amount is not None):
                    try:
                        charge = Decimal(str(service.charge_amount))
                        paid = Decimal(str(service.paid_amount))
                        
                        if paid > charge:
                            errors.append(self.create_error(
                                message=f"Service paid amount ({paid}) exceeds charge amount ({charge})",
                                code="835_SERVICE_OVERPAYMENT",
                                path=svc_path,
                                context={
                                    'charge_amount': str(charge),
                                    'paid_amount': str(paid)
                                },
                                severity="info"
                            ))
                    except (InvalidOperation, ValueError):
                        pass  # Amount format errors handled by data validation rule
        
        return errors