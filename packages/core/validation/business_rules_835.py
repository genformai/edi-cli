"""
Enhanced Business Rules for EDI 835 Healthcare Claim Payment/Advice

This module defines comprehensive business rules using the enhanced business rule engine
with field-level validation and detailed error reporting.
"""

from decimal import Decimal
from datetime import datetime, date
from typing import Dict, List, Any, Optional
import re

from .business_engine import (
    BusinessRule, 
    FieldValidator, 
    BusinessRuleSeverity, 
    BusinessRuleEngine
)


def create_835_business_rule_engine() -> BusinessRuleEngine:
    """Create and configure business rule engine with 835-specific rules."""
    engine = BusinessRuleEngine()
    
    # Register comprehensive business rules
    engine.register_business_rule(create_financial_balance_rule())
    engine.register_business_rule(create_claim_payment_validation_rule())
    engine.register_business_rule(create_currency_format_rule())
    engine.register_business_rule(create_date_validation_rule())
    engine.register_business_rule(create_identifier_validation_rule())
    engine.register_business_rule(create_service_line_validation_rule())
    engine.register_business_rule(create_adjustment_validation_rule())
    engine.register_business_rule(create_provider_level_adjustment_rule())
    engine.register_business_rule(create_claim_consistency_rule())
    engine.register_business_rule(create_business_logic_rule())
    
    return engine


def create_financial_balance_rule() -> BusinessRule:
    """Create comprehensive financial balance validation rule."""
    
    def validate_financial_balance(transaction_data: Any) -> List[Dict[str, Any]]:
        """Custom validation for complex financial balance checks."""
        errors = []
        
        try:
            # Extract BPR total paid amount
            bpr_total = None
            if hasattr(transaction_data, 'financial_information'):
                fi = transaction_data.financial_information
                if hasattr(fi, 'total_paid'):
                    bpr_total = Decimal(str(fi.total_paid))
            
            # Calculate sum of claim payments
            claims_total = Decimal('0')
            if hasattr(transaction_data, 'claims'):
                for claim in transaction_data.claims:
                    if hasattr(claim, 'total_paid'):
                        try:
                            claim_paid = Decimal(str(claim.total_paid))
                            claims_total += claim_paid
                        except (ValueError, TypeError):
                            continue
            
            # Check balance with tolerance
            tolerance = Decimal('0.01')
            if bpr_total is not None and abs(bpr_total - claims_total) > tolerance:
                difference = abs(bpr_total - claims_total)
                errors.append({
                    'severity': 'warning',
                    'message': f'Financial imbalance: BPR total ${bpr_total} vs claims total ${claims_total}, difference ${difference}',
                    'code': '835_FINANCIAL_IMBALANCE',
                    'bpr_total': str(bpr_total),
                    'claims_total': str(claims_total),
                    'difference': str(difference),
                    'tolerance': str(tolerance)
                })
            
            # Check for Provider Level Adjustments (PLB) impact
            plb_total = Decimal('0')
            if hasattr(transaction_data, 'plb'):
                for plb in transaction_data.plb:
                    if hasattr(plb, 'amount'):
                        try:
                            plb_amount = Decimal(str(plb.amount))
                            plb_total += plb_amount
                        except (ValueError, TypeError):
                            continue
            
            # Adjusted balance check including PLB
            if plb_total != 0:
                adjusted_total = claims_total + plb_total
                if bpr_total is not None and abs(bpr_total - adjusted_total) > tolerance:
                    errors.append({
                        'severity': 'info',
                        'message': f'PLB adjustments may explain balance difference: PLB total ${plb_total}',
                        'code': '835_PLB_BALANCE_INFO',
                        'plb_total': str(plb_total),
                        'adjusted_claims_total': str(adjusted_total)
                    })
                    
        except Exception as e:
            errors.append({
                'severity': 'error',
                'message': f'Financial balance validation error: {str(e)}',
                'code': '835_FINANCIAL_VALIDATION_ERROR',
                'exception': str(e)
            })
        
        return errors
    
    return BusinessRule(
        name="comprehensive_financial_balance",
        description="Comprehensive financial balance validation with PLB adjustments",
        category="financial",
        severity=BusinessRuleSeverity.WARNING,
        field_validators=[
            FieldValidator(
                field_path="financial_information.total_paid",
                validator_type="currency_format",
                parameters={'min_value': 0, 'max_value': 999999999.99},
                error_message="BPR total paid amount must be valid currency format",
                severity=BusinessRuleSeverity.ERROR
            )
        ],
        cross_field_validations=[
            {
                'type': 'balance_check',
                'total_field': 'financial_information.total_paid',
                'sum_fields': ['claims[0].total_paid', 'claims[1].total_paid', 'claims[2].total_paid'],
                'tolerance': '0.01',
                'severity': 'warning',
                'message': 'BPR total does not match sum of claim payments',
                'error_code': '835_FINANCIAL_IMBALANCE'
            }
        ],
        custom_validation_function=validate_financial_balance
    )


def create_claim_payment_validation_rule() -> BusinessRule:
    """Create claim-level payment validation rule."""
    
    def validate_claim_overpayment(transaction_data: Any) -> List[Dict[str, Any]]:
        """Check for overpayments where paid > charged."""
        errors = []
        
        try:
            if hasattr(transaction_data, 'claims'):
                for i, claim in enumerate(transaction_data.claims):
                    claim_path = f"claims[{i}]"
                    
                    total_charge = None
                    total_paid = None
                    
                    if hasattr(claim, 'total_charge'):
                        try:
                            total_charge = Decimal(str(claim.total_charge))
                        except (ValueError, TypeError):
                            continue
                    
                    if hasattr(claim, 'total_paid'):
                        try:
                            total_paid = Decimal(str(claim.total_paid))
                        except (ValueError, TypeError):
                            continue
                    
                    # Check for overpayment
                    if total_charge is not None and total_paid is not None and total_paid > total_charge:
                        overpayment = total_paid - total_charge
                        errors.append({
                            'severity': 'warning',
                            'message': f'Claim overpayment detected: paid ${total_paid} > charged ${total_charge}',
                            'code': '835_CLAIM_OVERPAYMENT',
                            'claim_path': claim_path,
                            'total_charge': str(total_charge),
                            'total_paid': str(total_paid),
                            'overpayment': str(overpayment)
                        })
                    
                    # Check for zero payment without adjustments
                    if total_paid is not None and total_paid == 0:
                        has_adjustments = False
                        if hasattr(claim, 'adjustments') and claim.adjustments:
                            has_adjustments = len(claim.adjustments) > 0
                        
                        if not has_adjustments:
                            errors.append({
                                'severity': 'info',
                                'message': 'Zero payment claim should have adjustment explanations',
                                'code': '835_ZERO_PAYMENT_NO_ADJUSTMENTS',
                                'claim_path': claim_path,
                                'total_paid': str(total_paid)
                            })
                            
        except Exception as e:
            errors.append({
                'severity': 'error',
                'message': f'Claim payment validation error: {str(e)}',
                'code': '835_CLAIM_VALIDATION_ERROR',
                'exception': str(e)
            })
        
        return errors
    
    return BusinessRule(
        name="claim_payment_validation",
        description="Validate claim payment amounts and logic",
        category="claim_validation",
        severity=BusinessRuleSeverity.WARNING,
        field_validators=[
            FieldValidator(
                field_path="claims[0].total_charge",
                validator_type="currency_format",
                parameters={'min_value': 0},
                error_message="Claim charge amount must be valid positive currency",
                severity=BusinessRuleSeverity.ERROR
            ),
            FieldValidator(
                field_path="claims[0].total_paid",
                validator_type="currency_format",
                parameters={'min_value': 0},
                error_message="Claim paid amount must be valid non-negative currency",
                severity=BusinessRuleSeverity.ERROR
            )
        ],
        custom_validation_function=validate_claim_overpayment
    )


def create_currency_format_rule() -> BusinessRule:
    """Create comprehensive currency format validation rule."""
    return BusinessRule(
        name="currency_format_validation",
        description="Validate all currency fields follow proper format",
        category="data_format",
        severity=BusinessRuleSeverity.ERROR,
        field_validators=[
            FieldValidator(
                field_path="financial_information.total_paid",
                validator_type="currency_format",
                error_message="BPR total paid must be valid currency format (max 2 decimal places)",
                severity=BusinessRuleSeverity.ERROR
            ),
            FieldValidator(
                field_path="claims[0].total_charge",
                validator_type="currency_format",
                error_message="Claim charge amount must be valid currency format",
                severity=BusinessRuleSeverity.ERROR
            ),
            FieldValidator(
                field_path="claims[0].total_paid",
                validator_type="currency_format",
                error_message="Claim paid amount must be valid currency format",
                severity=BusinessRuleSeverity.ERROR
            ),
            FieldValidator(
                field_path="claims[0].patient_responsibility",
                validator_type="currency_format",
                error_message="Patient responsibility must be valid currency format",
                severity=BusinessRuleSeverity.WARNING
            )
        ]
    )


def create_date_validation_rule() -> BusinessRule:
    """Create date format validation rule."""
    today = date.today()
    future_limit = date(today.year + 1, 12, 31)  # Allow up to next year end
    past_limit = date(today.year - 10, 1, 1)     # Allow up to 10 years back
    
    return BusinessRule(
        name="date_format_validation",
        description="Validate date fields follow CCYYMMDD format and are reasonable",
        category="data_format",
        severity=BusinessRuleSeverity.WARNING,
        field_validators=[
            FieldValidator(
                field_path="financial_information.payment_date",
                validator_type="date_format",
                parameters={
                    'format': '%Y%m%d',
                    'min_date': past_limit,
                    'max_date': future_limit
                },
                error_message="Payment date must be CCYYMMDD format and within reasonable range",
                severity=BusinessRuleSeverity.WARNING
            ),
            FieldValidator(
                field_path="dates[0].date",
                validator_type="date_format",
                parameters={
                    'format': '%Y-%m-%d',
                    'min_date': past_limit,
                    'max_date': future_limit
                },
                error_message="Transaction dates must be in valid format and reasonable range",
                severity=BusinessRuleSeverity.INFO
            )
        ]
    )


def create_identifier_validation_rule() -> BusinessRule:
    """Create identifier format validation rule."""
    return BusinessRule(
        name="identifier_format_validation",
        description="Validate NPI, Tax ID, and other identifier formats",
        category="data_format",
        severity=BusinessRuleSeverity.WARNING,
        field_validators=[
            FieldValidator(
                field_path="payee.npi",
                validator_type="npi_format",
                error_message="Payee NPI must be exactly 10 digits when present",
                severity=BusinessRuleSeverity.WARNING
            ),
            FieldValidator(
                field_path="payer.npi",
                validator_type="npi_format",
                error_message="Payer NPI must be exactly 10 digits when present",
                severity=BusinessRuleSeverity.WARNING
            ),
            FieldValidator(
                field_path="payee.tax_id",
                validator_type="tax_id_format",
                error_message="Payee Tax ID must be valid EIN or SSN format",
                severity=BusinessRuleSeverity.INFO
            ),
            FieldValidator(
                field_path="financial_information.payment_method",
                validator_type="enum",
                parameters={'values': ['ACH', 'BOP', 'CHK', 'FWT', 'NON']},
                error_message="Payment method must be valid code (ACH, BOP, CHK, FWT, NON)",
                severity=BusinessRuleSeverity.ERROR
            )
        ]
    )


def create_service_line_validation_rule() -> BusinessRule:
    """Create service line validation rule."""
    
    def validate_service_line_totals(transaction_data: Any) -> List[Dict[str, Any]]:
        """Validate that service line amounts add up to claim totals."""
        errors = []
        
        try:
            if hasattr(transaction_data, 'claims'):
                for i, claim in enumerate(transaction_data.claims):
                    if hasattr(claim, 'services') and claim.services:
                        # Calculate service line totals
                        service_charge_total = Decimal('0')
                        service_paid_total = Decimal('0')
                        
                        for service in claim.services:
                            if hasattr(service, 'charge_amount'):
                                try:
                                    service_charge_total += Decimal(str(service.charge_amount))
                                except (ValueError, TypeError):
                                    pass
                            
                            if hasattr(service, 'paid_amount'):
                                try:
                                    service_paid_total += Decimal(str(service.paid_amount))
                                except (ValueError, TypeError):
                                    pass
                        
                        # Compare with claim totals
                        claim_charge = None
                        claim_paid = None
                        
                        if hasattr(claim, 'total_charge'):
                            try:
                                claim_charge = Decimal(str(claim.total_charge))
                            except (ValueError, TypeError):
                                pass
                        
                        if hasattr(claim, 'total_paid'):
                            try:
                                claim_paid = Decimal(str(claim.total_paid))
                            except (ValueError, TypeError):
                                pass
                        
                        # Check charge total
                        tolerance = Decimal('0.01')
                        if (claim_charge is not None and 
                            abs(service_charge_total - claim_charge) > tolerance):
                            errors.append({
                                'severity': 'info',
                                'message': f'Service line charges (${service_charge_total}) do not match claim total (${claim_charge})',
                                'code': '835_SERVICE_CHARGE_MISMATCH',
                                'claim_index': i,
                                'service_charge_total': str(service_charge_total),
                                'claim_charge_total': str(claim_charge),
                                'difference': str(abs(service_charge_total - claim_charge))
                            })
                        
                        # Check paid total
                        if (claim_paid is not None and 
                            abs(service_paid_total - claim_paid) > tolerance):
                            errors.append({
                                'severity': 'info',
                                'message': f'Service line payments (${service_paid_total}) do not match claim total (${claim_paid})',
                                'code': '835_SERVICE_PAID_MISMATCH',
                                'claim_index': i,
                                'service_paid_total': str(service_paid_total),
                                'claim_paid_total': str(claim_paid),
                                'difference': str(abs(service_paid_total - claim_paid))
                            })
                            
        except Exception as e:
            errors.append({
                'severity': 'error',
                'message': f'Service line validation error: {str(e)}',
                'code': '835_SERVICE_VALIDATION_ERROR',
                'exception': str(e)
            })
        
        return errors
    
    return BusinessRule(
        name="service_line_validation",
        description="Validate service line amounts and totals",
        category="service_validation",
        severity=BusinessRuleSeverity.INFO,
        field_validators=[
            FieldValidator(
                field_path="claims[0].services[0].service_code",
                validator_type="regex",
                parameters={'pattern': r'^[A-Z0-9]{1,48}$'},
                error_message="Service code must be valid format",
                severity=BusinessRuleSeverity.WARNING
            ),
            FieldValidator(
                field_path="claims[0].services[0].charge_amount",
                validator_type="currency_format",
                error_message="Service charge amount must be valid currency",
                severity=BusinessRuleSeverity.ERROR
            ),
            FieldValidator(
                field_path="claims[0].services[0].paid_amount",
                validator_type="currency_format",
                error_message="Service paid amount must be valid currency",
                severity=BusinessRuleSeverity.ERROR
            )
        ],
        custom_validation_function=validate_service_line_totals
    )


def create_adjustment_validation_rule() -> BusinessRule:
    """Create claim adjustment validation rule."""
    
    def validate_adjustment_reasons(transaction_data: Any) -> List[Dict[str, Any]]:
        """Validate adjustment reason codes and amounts."""
        errors = []
        
        try:
            if hasattr(transaction_data, 'claims'):
                for i, claim in enumerate(transaction_data.claims):
                    if hasattr(claim, 'adjustments') and claim.adjustments:
                        for j, adjustment in enumerate(claim.adjustments):
                            # Validate adjustment reason code format
                            if hasattr(adjustment, 'reason_code'):
                                reason_code = str(adjustment.reason_code)
                                if not re.match(r'^[A-Z0-9]{1,5}$', reason_code):
                                    errors.append({
                                        'severity': 'warning',
                                        'message': f'Invalid adjustment reason code format: {reason_code}',
                                        'code': '835_INVALID_ADJUSTMENT_CODE',
                                        'claim_index': i,
                                        'adjustment_index': j,
                                        'reason_code': reason_code
                                    })
                            
                            # Validate adjustment amount
                            if hasattr(adjustment, 'amount'):
                                try:
                                    adj_amount = Decimal(str(adjustment.amount))
                                    if adj_amount == 0:
                                        errors.append({
                                            'severity': 'info',
                                            'message': 'Zero adjustment amount may be unnecessary',
                                            'code': '835_ZERO_ADJUSTMENT',
                                            'claim_index': i,
                                            'adjustment_index': j
                                        })
                                except (ValueError, TypeError):
                                    errors.append({
                                        'severity': 'error',
                                        'message': f'Invalid adjustment amount format',
                                        'code': '835_INVALID_ADJUSTMENT_AMOUNT',
                                        'claim_index': i,
                                        'adjustment_index': j,
                                        'amount': str(adjustment.amount)
                                    })
                                    
        except Exception as e:
            errors.append({
                'severity': 'error',
                'message': f'Adjustment validation error: {str(e)}',
                'code': '835_ADJUSTMENT_VALIDATION_ERROR',
                'exception': str(e)
            })
        
        return errors
    
    return BusinessRule(
        name="adjustment_validation",
        description="Validate claim adjustment codes and amounts",
        category="adjustment_validation",
        severity=BusinessRuleSeverity.WARNING,
        custom_validation_function=validate_adjustment_reasons
    )


def create_provider_level_adjustment_rule() -> BusinessRule:
    """Create provider level adjustment (PLB) validation rule."""
    
    def validate_plb_adjustments(transaction_data: Any) -> List[Dict[str, Any]]:
        """Validate provider level adjustments."""
        errors = []
        
        try:
            if hasattr(transaction_data, 'plb') and transaction_data.plb:
                for i, plb in enumerate(transaction_data.plb):
                    # Validate PLB amount
                    if hasattr(plb, 'amount'):
                        try:
                            plb_amount = Decimal(str(plb.amount))
                            
                            # Flag unusual PLB amounts
                            if abs(plb_amount) > Decimal('50000'):
                                errors.append({
                                    'severity': 'warning',
                                    'message': f'Unusually large PLB adjustment: ${plb_amount}',
                                    'code': '835_LARGE_PLB_ADJUSTMENT',
                                    'plb_index': i,
                                    'amount': str(plb_amount)
                                })
                            
                            if plb_amount == 0:
                                errors.append({
                                    'severity': 'info',
                                    'message': 'Zero PLB adjustment may be unnecessary',
                                    'code': '835_ZERO_PLB_ADJUSTMENT',
                                    'plb_index': i
                                })
                                
                        except (ValueError, TypeError):
                            errors.append({
                                'severity': 'error',
                                'message': 'Invalid PLB amount format',
                                'code': '835_INVALID_PLB_AMOUNT',
                                'plb_index': i,
                                'amount': str(plb.amount)
                            })
                    
                    # Validate PLB reason
                    if hasattr(plb, 'reason'):
                        reason = str(plb.reason)
                        if not reason or reason.strip() == "":
                            errors.append({
                                'severity': 'warning',
                                'message': 'PLB adjustment should include reason description',
                                'code': '835_PLB_MISSING_REASON',
                                'plb_index': i
                            })
                            
        except Exception as e:
            errors.append({
                'severity': 'error',
                'message': f'PLB validation error: {str(e)}',
                'code': '835_PLB_VALIDATION_ERROR',
                'exception': str(e)
            })
        
        return errors
    
    return BusinessRule(
        name="provider_level_adjustment_validation",
        description="Validate provider level adjustments (PLB)",
        category="plb_validation",
        severity=BusinessRuleSeverity.INFO,
        custom_validation_function=validate_plb_adjustments
    )


def create_claim_consistency_rule() -> BusinessRule:
    """Create claim consistency validation rule."""
    return BusinessRule(
        name="claim_consistency_validation",
        description="Validate consistency across claim fields",
        category="consistency",
        severity=BusinessRuleSeverity.WARNING,
        cross_field_validations=[
            {
                'type': 'consistency_check',
                'field1': 'claims[0].total_charge',
                'field2': 'claims[0].total_paid',
                'relationship': 'greater_equal',
                'severity': 'warning',
                'message': 'Claim charge amount should be greater than or equal to paid amount',
                'error_code': '835_CHARGE_PAID_INCONSISTENCY'
            },
            {
                'type': 'logical_check',
                'condition': {
                    'type': 'if_then',
                    'if': {'field': 'claims[0].total_paid', 'operator': 'eq', 'value': 0},
                    'then': {'field': 'claims[0].adjustments', 'operator': 'exists'}
                },
                'severity': 'info',
                'message': 'Claims with zero payment should have adjustment explanations',
                'error_code': '835_ZERO_PAYMENT_LOGIC'
            }
        ]
    )


def create_business_logic_rule() -> BusinessRule:
    """Create comprehensive business logic validation rule."""
    
    def validate_business_logic(transaction_data: Any) -> List[Dict[str, Any]]:
        """Comprehensive business logic validation."""
        errors = []
        
        try:
            # Check for high-value transactions
            if hasattr(transaction_data, 'financial_information'):
                fi = transaction_data.financial_information
                if hasattr(fi, 'total_paid'):
                    try:
                        total_amount = Decimal(str(fi.total_paid))
                        if total_amount > Decimal('100000'):
                            errors.append({
                                'severity': 'info',
                                'message': f'High-value transaction: ${total_amount} - may require additional review',
                                'code': '835_HIGH_VALUE_TRANSACTION',
                                'total_amount': str(total_amount)
                            })
                    except (ValueError, TypeError):
                        pass
            
            # Check claim volume
            if hasattr(transaction_data, 'claims'):
                claim_count = len(transaction_data.claims)
                if claim_count > 100:
                    errors.append({
                        'severity': 'info',
                        'message': f'High claim volume: {claim_count} claims in single 835 transaction',
                        'code': '835_HIGH_CLAIM_VOLUME',
                        'claim_count': claim_count
                    })
                elif claim_count == 0:
                    errors.append({
                        'severity': 'warning',
                        'message': 'No claims found in 835 transaction',
                        'code': '835_NO_CLAIMS',
                        'claim_count': claim_count
                    })
            
            # Validate patient responsibility logic
            if hasattr(transaction_data, 'claims'):
                for i, claim in enumerate(transaction_data.claims):
                    if hasattr(claim, 'patient_responsibility'):
                        try:
                            patient_resp = Decimal(str(claim.patient_responsibility))
                            if patient_resp < 0:
                                errors.append({
                                    'severity': 'error',
                                    'message': 'Patient responsibility cannot be negative',
                                    'code': '835_NEGATIVE_PATIENT_RESPONSIBILITY',
                                    'claim_index': i,
                                    'patient_responsibility': str(patient_resp)
                                })
                        except (ValueError, TypeError):
                            pass
                            
        except Exception as e:
            errors.append({
                'severity': 'error',
                'message': f'Business logic validation error: {str(e)}',
                'code': '835_BUSINESS_LOGIC_ERROR',
                'exception': str(e)
            })
        
        return errors
    
    return BusinessRule(
        name="comprehensive_business_logic",
        description="Comprehensive business logic validation",
        category="business_logic",
        severity=BusinessRuleSeverity.INFO,
        custom_validation_function=validate_business_logic
    )