"""
EDI 835 Specific Validation Rules

This module contains business rules and validation logic specific to
EDI 835 Electronic Remittance Advice transactions.
"""

from typing import Dict, List, Any, Optional
from .validation import ValidationRule, ValidationError, ValidationSeverity, ValidationCategory, BusinessRule
from .ast import EdiRoot
from .utils import validate_npi
import logging

logger = logging.getLogger(__name__)


class Financial835ValidationRule(BusinessRule):
    """Validation rules for 835 financial information consistency."""
    
    def __init__(self):
        super().__init__(
            rule_id="835_FINANCIAL_CONSISTENCY",
            description="Financial amounts must be consistent across transaction",
            severity=ValidationSeverity.ERROR,
            category=ValidationCategory.BUSINESS,
            condition=self._validate_financial_consistency,
            error_message="Financial information is inconsistent"
        )
    
    def _validate_financial_consistency(self, edi_root: EdiRoot, context: Dict[str, Any]) -> bool:
        """Validate that financial amounts are consistent."""
        try:
            for interchange in edi_root.interchanges:
                for fg in interchange.functional_groups:
                    for transaction in fg.transactions:
                        if not transaction.financial_information:
                            continue
                        
                        total_paid = transaction.financial_information.total_paid
                        
                        # Calculate sum of all claim payments
                        claims_total = sum(
                            claim.total_paid for claim in transaction.claims
                            if claim.total_paid is not None
                        )
                        
                        # Allow small rounding differences (1 cent)
                        if abs(total_paid - claims_total) > 0.01:
                            return False
            
            return True
        except Exception as e:
            logger.error(f"Error in financial consistency check: {e}")
            return False


class Claim835ValidationRule(BusinessRule):
    """Validation rules for 835 claim-level information."""
    
    def __init__(self):
        super().__init__(
            rule_id="835_CLAIM_VALIDATION",
            description="Claim information must be valid and consistent",
            severity=ValidationSeverity.ERROR,
            category=ValidationCategory.BUSINESS,
            condition=self._validate_claims,
            error_message="Invalid claim information found"
        )
    
    def _validate_claims(self, edi_root: EdiRoot, context: Dict[str, Any]) -> bool:
        """Validate claim-level information."""
        try:
            for interchange in edi_root.interchanges:
                for fg in interchange.functional_groups:
                    for transaction in fg.transactions:
                        for claim in transaction.claims:
                            # Validate claim amounts
                            if claim.total_charge < 0 or claim.total_paid < 0:
                                return False
                            
                            # Validate that paid amount doesn't exceed charge
                            if claim.total_paid > claim.total_charge:
                                return False
                            
                            # Validate status code
                            if claim.status_code < 1 or claim.status_code > 22:
                                return False
                            
                            # Validate service amounts consistency
                            if claim.services:
                                service_charge_total = sum(s.charge_amount for s in claim.services)
                                service_paid_total = sum(s.paid_amount for s in claim.services)
                                
                                # Allow small rounding differences
                                if abs(claim.total_charge - service_charge_total) > 0.01:
                                    return False
                                if abs(claim.total_paid - service_paid_total) > 0.01:
                                    return False
            
            return True
        except Exception as e:
            logger.error(f"Error in claim validation: {e}")
            return False


class Adjustment835ValidationRule(BusinessRule):
    """Validation rules for 835 adjustment information."""
    
    def __init__(self):
        super().__init__(
            rule_id="835_ADJUSTMENT_VALIDATION",
            description="Adjustment information must be valid",
            severity=ValidationSeverity.WARNING,
            category=ValidationCategory.BUSINESS,
            condition=self._validate_adjustments,
            error_message="Invalid adjustment information found"
        )
    
    def _validate_adjustments(self, edi_root: EdiRoot, context: Dict[str, Any]) -> bool:
        """Validate adjustment information."""
        try:
            valid_group_codes = {'CO', 'CR', 'OA', 'PI', 'PR'}
            
            for interchange in edi_root.interchanges:
                for fg in interchange.functional_groups:
                    for transaction in fg.transactions:
                        for claim in transaction.claims:
                            for adjustment in claim.adjustments:
                                # Validate group code
                                if adjustment.group_code not in valid_group_codes:
                                    return False
                                
                                # Validate amounts
                                if adjustment.amount < 0 or adjustment.quantity < 0:
                                    return False
                                
                                # Validate reason code format
                                if not adjustment.reason_code or len(adjustment.reason_code) > 5:
                                    return False
            
            return True
        except Exception as e:
            logger.error(f"Error in adjustment validation: {e}")
            return False


class Service835ValidationRule(BusinessRule):
    """Validation rules for 835 service line information."""
    
    def __init__(self):
        super().__init__(
            rule_id="835_SERVICE_VALIDATION",
            description="Service line information must be valid",
            severity=ValidationSeverity.ERROR,
            category=ValidationCategory.BUSINESS,
            condition=self._validate_services,
            error_message="Invalid service information found"
        )
    
    def _validate_services(self, edi_root: EdiRoot, context: Dict[str, Any]) -> bool:
        """Validate service line information."""
        try:
            for interchange in edi_root.interchanges:
                for fg in interchange.functional_groups:
                    for transaction in fg.transactions:
                        for claim in transaction.claims:
                            for service in claim.services:
                                # Validate amounts
                                if service.charge_amount < 0 or service.paid_amount < 0:
                                    return False
                                
                                # Validate that paid doesn't exceed charge
                                if service.paid_amount > service.charge_amount:
                                    return False
                                
                                # Validate service code format
                                if not service.service_code:
                                    return False
                                
                                # Basic HCPCS/CPT code format validation
                                service_code = service.service_code.replace('HC:', '').replace('AD:', '')
                                if len(service_code) < 3:
                                    return False
            
            return True
        except Exception as e:
            logger.error(f"Error in service validation: {e}")
            return False


class Date835ValidationRule(BusinessRule):
    """Validation rules for 835 date information."""
    
    def __init__(self):
        super().__init__(
            rule_id="835_DATE_VALIDATION",
            description="Date information must be valid and logical",
            severity=ValidationSeverity.WARNING,
            category=ValidationCategory.BUSINESS,
            condition=self._validate_dates,
            error_message="Invalid date information found"
        )
    
    def _validate_dates(self, edi_root: EdiRoot, context: Dict[str, Any]) -> bool:
        """Validate date information."""
        try:
            from datetime import datetime
            
            for interchange in edi_root.interchanges:
                # Validate interchange date
                try:
                    interchange_date = datetime.strptime(interchange.header['date'], '%Y-%m-%d')
                except ValueError:
                    return False
                
                for fg in interchange.functional_groups:
                    # Validate functional group date
                    try:
                        fg_date = datetime.strptime(fg.header['date'], '%Y-%m-%d')
                    except ValueError:
                        return False
                    
                    for transaction in fg.transactions:
                        if transaction.financial_information:
                            # Validate payment date
                            try:
                                payment_date = datetime.strptime(
                                    transaction.financial_information.payment_date, '%Y-%m-%d'
                                )
                            except ValueError:
                                return False
                        
                        # Validate service dates
                        for claim in transaction.claims:
                            for service in claim.services:
                                if service.service_date:
                                    try:
                                        service_date = datetime.strptime(service.service_date, '%Y-%m-%d')
                                        # Service date should not be in the future
                                        if service_date > datetime.now():
                                            return False
                                    except ValueError:
                                        return False
            
            return True
        except Exception as e:
            logger.error(f"Error in date validation: {e}")
            return False


class PayerPayee835ValidationRule(BusinessRule):
    """Validation rules for 835 payer and payee information."""
    
    def __init__(self):
        super().__init__(
            rule_id="835_PAYER_PAYEE_VALIDATION",
            description="Payer and payee information must be valid",
            severity=ValidationSeverity.WARNING,
            category=ValidationCategory.BUSINESS,
            condition=self._validate_payer_payee,
            error_message="Invalid payer or payee information"
        )
    
    def _validate_payer_payee(self, edi_root: EdiRoot, context: Dict[str, Any]) -> bool:
        """Validate payer and payee information."""
        try:
            for interchange in edi_root.interchanges:
                for fg in interchange.functional_groups:
                    for transaction in fg.transactions:
                        # Validate payer information
                        if transaction.payer:
                            if not transaction.payer.name or len(transaction.payer.name.strip()) == 0:
                                return False
                        
                        # Validate payee information
                        if transaction.payee:
                            if not transaction.payee.name or len(transaction.payee.name.strip()) == 0:
                                return False
                            
                            # Validate NPI if present
                            if transaction.payee.npi:
                                if not validate_npi(transaction.payee.npi):
                                    return False
            
            return True
        except Exception as e:
            logger.error(f"Error in payer/payee validation: {e}")
            return False
    


def get_835_business_rules() -> List[ValidationRule]:
    """Get all 835-specific business validation rules."""
    return [
        Financial835ValidationRule(),
        Claim835ValidationRule(),
        Adjustment835ValidationRule(),
        Service835ValidationRule(),
        Date835ValidationRule(),
        PayerPayee835ValidationRule(),
    ]