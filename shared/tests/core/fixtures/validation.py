"""
Validation utilities for EDI fixture data quality and correctness.

This module provides validation functions to ensure generated EDI transactions
are syntactically correct, semantically valid, and contain realistic data.
"""

import re
from decimal import Decimal
from typing import List, Dict, Tuple, Optional
from datetime import datetime


class EDIValidationError(Exception):
    """Raised when EDI data fails validation."""
    pass


class EDIValidator:
    """Validates EDI transaction data for correctness and quality."""
    
    # EDI segment patterns
    SEGMENT_PATTERNS = {
        'ISA': r'ISA\*\d{2}\*.*\*\d{2}\*.*\*\w{2}\*.*\*\w{2}\*.*\*\d{6}\*\d{4}\*.*\*\d{5}\*\d{9}\*\d\*\w\*.*~',
        'GS': r'GS\*\w{1,2}\*.*\*.*\*\d{8}\*\d{4}\*.*\*\w\*.*~',
        'ST': r'ST\*\d{3}\*\w{1,9}~',
        'SE': r'SE\*\d+\*\w{1,9}~',
        'GE': r'GE\*\d+\*.*~',
        'IEA': r'IEA\*\d+\*\d{9}~'
    }
    
    # Transaction-specific patterns
    TRANSACTION_PATTERNS = {
        '835': {
            'BPR': r'BPR\*[IDC]\*[\d.]+\*C\*\w{3,4}\*.*~',
            'TRN': r'TRN\*\d\*.*\*.*~',
            'CLP': r'CLP\*.*\*\d\*[\d.]+\*[\d.]+\*[\d.]+\*.*~'
        },
        '270': {
            'BHT': r'BHT\*0022\*13\*.*\*\d{8}\*\d{4}~',
            'HL': r'HL\*\d+\*.*\*\d{2}\*[01]~',
            'EQ': r'EQ\*\w+~'
        },
        '276': {
            'BHT': r'BHT\*0019\*13\*.*\*\d{8}\*\d{4}~',
            'TRN': r'TRN\*1\*.*\*.*~',
            'REF': r'REF\*1K\*.*~'
        },
        '837': {
            'BHT': r'BHT\*0019\*00\*.*\*\d{8}\*\d{4}\*CH~',
            'CLM': r'CLM\*.*\*[\d.]+\*.*~',
            'HI': r'HI\*.*~'
        }
    }
    
    @classmethod
    def validate_edi_structure(cls, edi_content: str) -> List[str]:
        """
        Validate basic EDI structure.
        
        Returns:
            List of validation errors (empty if valid)
        """
        errors = []
        
        if not edi_content:
            errors.append("EDI content is empty")
            return errors
        
        if not edi_content.endswith('~'):
            errors.append("EDI content must end with segment terminator '~'")
        
        segments = [seg for seg in edi_content.split('~') if seg.strip()]
        
        if len(segments) < 6:
            errors.append("EDI must contain at least 6 segments (ISA, GS, ST, content, SE, GE, IEA)")
        
        # Check envelope structure
        if not segments[0].startswith('ISA*'):
            errors.append("First segment must be ISA")
        
        if not segments[-1].startswith('IEA*'):
            errors.append("Last segment must be IEA")
        
        # Find required segments
        has_gs = any(seg.startswith('GS*') for seg in segments)
        has_st = any(seg.startswith('ST*') for seg in segments)
        has_se = any(seg.startswith('SE*') for seg in segments)
        has_ge = any(seg.startswith('GE*') for seg in segments)
        
        if not has_gs:
            errors.append("Missing required GS segment")
        if not has_st:
            errors.append("Missing required ST segment")
        if not has_se:
            errors.append("Missing required SE segment")
        if not has_ge:
            errors.append("Missing required GE segment")
        
        return errors
    
    @classmethod
    def validate_segment_syntax(cls, edi_content: str) -> List[str]:
        """
        Validate individual segment syntax.
        
        Returns:
            List of syntax errors
        """
        errors = []
        segments = [seg for seg in edi_content.split('~') if seg.strip()]
        
        for i, segment in enumerate(segments):
            segment_id = segment.split('*')[0] if '*' in segment else segment
            
            # Check basic segment format
            if not segment:
                continue
                
            if not re.match(r'^[A-Z0-9]{2,3}\*', segment):
                errors.append(f"Segment {i+1}: Invalid segment ID format '{segment_id}'")
                continue
            
            # Validate known segment patterns
            if segment_id in cls.SEGMENT_PATTERNS:
                pattern = cls.SEGMENT_PATTERNS[segment_id]
                if not re.match(pattern, segment + '~'):
                    errors.append(f"Segment {i+1}: {segment_id} segment syntax invalid")
        
        return errors
    
    @classmethod
    def validate_control_numbers(cls, edi_content: str) -> List[str]:
        """
        Validate control number consistency.
        
        Returns:
            List of control number errors
        """
        errors = []
        segments = [seg for seg in edi_content.split('~') if seg.strip()]
        
        # Extract control numbers
        isa_control = None
        gs_control = None
        st_control = None
        
        for segment in segments:
            if segment.startswith('ISA*'):
                parts = segment.split('*')
                if len(parts) >= 14:
                    isa_control = parts[13]
            elif segment.startswith('GS*'):
                parts = segment.split('*')
                if len(parts) >= 7:
                    gs_control = parts[6]
            elif segment.startswith('ST*'):
                parts = segment.split('*')
                if len(parts) >= 3:
                    st_control = parts[2]
            elif segment.startswith('SE*'):
                parts = segment.split('*')
                if len(parts) >= 3:
                    if parts[2] != st_control:
                        errors.append(f"SE control number '{parts[2]}' doesn't match ST '{st_control}'")
            elif segment.startswith('GE*'):
                parts = segment.split('*')
                if len(parts) >= 3:
                    if parts[2] != gs_control:
                        errors.append(f"GE control number '{parts[2]}' doesn't match GS '{gs_control}'")
            elif segment.startswith('IEA*'):
                parts = segment.split('*')
                if len(parts) >= 3:
                    if parts[2] != isa_control:
                        errors.append(f"IEA control number '{parts[2]}' doesn't match ISA '{isa_control}'")
        
        return errors
    
    @classmethod
    def validate_transaction_content(cls, edi_content: str) -> List[str]:
        """
        Validate transaction-specific content.
        
        Returns:
            List of content validation errors
        """
        errors = []
        segments = [seg for seg in edi_content.split('~') if seg.strip()]
        
        # Determine transaction type
        transaction_type = None
        for segment in segments:
            if segment.startswith('ST*'):
                parts = segment.split('*')
                if len(parts) >= 2:
                    transaction_type = parts[1]
                break
        
        if not transaction_type:
            errors.append("Cannot determine transaction type from ST segment")
            return errors
        
        # Validate transaction-specific patterns
        if transaction_type in cls.TRANSACTION_PATTERNS:
            patterns = cls.TRANSACTION_PATTERNS[transaction_type]
            
            for segment_type, pattern in patterns.items():
                matching_segments = [seg for seg in segments if seg.startswith(f"{segment_type}*")]
                
                if not matching_segments:
                    errors.append(f"Missing required {segment_type} segment for {transaction_type} transaction")
                else:
                    for segment in matching_segments:
                        if not re.match(pattern, segment + '~'):
                            errors.append(f"Invalid {segment_type} segment format: {segment}")
        
        return errors
    
    @classmethod
    def validate_data_quality(cls, edi_content: str) -> List[str]:
        """
        Validate data quality and realism.
        
        Returns:
            List of data quality issues
        """
        warnings = []
        segments = [seg for seg in edi_content.split('~') if seg.strip()]
        
        for segment in segments:
            # Check for obvious test/placeholder data
            if any(placeholder in segment.upper() for placeholder in [
                'TEST', 'PLACEHOLDER', 'SAMPLE', 'DUMMY', 'FAKE', 'EXAMPLE'
            ]):
                warnings.append(f"Segment contains placeholder data: {segment[:50]}...")
            
            # Check for unrealistic amounts
            if segment.startswith(('BPR*', 'CLP*')):
                parts = segment.split('*')
                for i, part in enumerate(parts):
                    if re.match(r'^\d+\.\d+$', part):
                        try:
                            amount = Decimal(part)
                            if amount > 1000000:  # > $1M
                                warnings.append(f"Unusually large amount: ${amount}")
                            elif amount < 0:
                                warnings.append(f"Negative amount: ${amount}")
                        except:
                            pass
            
            # Check NPI format (should be 10 digits)
            npi_pattern = r'\*XX\*(\d+)'
            matches = re.findall(npi_pattern, segment)
            for npi in matches:
                if len(npi) != 10:
                    warnings.append(f"Invalid NPI length: {npi} (should be 10 digits)")
                elif not npi.isdigit():
                    warnings.append(f"Invalid NPI format: {npi} (should be all digits)")
        
        return warnings
    
    @classmethod
    def validate_transaction(cls, edi_content: str, strict: bool = False) -> Dict[str, List[str]]:
        """
        Perform comprehensive validation of an EDI transaction.
        
        Args:
            edi_content: EDI transaction content
            strict: If True, treat warnings as errors
            
        Returns:
            Dictionary with 'errors' and 'warnings' lists
        """
        result = {
            'errors': [],
            'warnings': []
        }
        
        # Structural validation
        result['errors'].extend(cls.validate_edi_structure(edi_content))
        result['errors'].extend(cls.validate_segment_syntax(edi_content))
        result['errors'].extend(cls.validate_control_numbers(edi_content))
        result['errors'].extend(cls.validate_transaction_content(edi_content))
        
        # Data quality validation
        quality_issues = cls.validate_data_quality(edi_content)
        if strict:
            result['errors'].extend(quality_issues)
        else:
            result['warnings'].extend(quality_issues)
        
        return result
    
    @classmethod
    def validate_realistic_data(cls, edi_content: str) -> Dict[str, List[str]]:
        """
        Validate that EDI contains realistic, production-like data.
        
        Returns:
            Dictionary with validation results
        """
        result = {
            'realistic_elements': [],
            'unrealistic_elements': []
        }
        
        segments = [seg for seg in edi_content.split('~') if seg.strip()]
        
        # Known realistic payer names (from YAML data)
        realistic_payers = [
            'AETNA', 'ANTHEM', 'BLUE CROSS', 'CIGNA', 'HUMANA', 
            'KAISER', 'MEDICARE', 'MEDICAID', 'UNITEDHEALTH'
        ]
        
        # Known realistic provider patterns
        realistic_provider_patterns = [
            r'.*CLINIC.*', r'.*HOSPITAL.*', r'.*MEDICAL.*', r'.*HEALTH.*',
            r'.*CENTER.*', r'.*ASSOCIATES.*', r'.*GROUP.*'
        ]
        
        for segment in segments:
            # Check for realistic payer names
            if segment.startswith('N1*PR*'):
                payer_name = segment.split('*')[2] if len(segment.split('*')) > 2 else ""
                if any(name in payer_name.upper() for name in realistic_payers):
                    result['realistic_elements'].append(f"Realistic payer: {payer_name}")
                else:
                    result['unrealistic_elements'].append(f"Generic payer name: {payer_name}")
            
            # Check for realistic provider names
            elif segment.startswith('N1*PE*'):
                provider_name = segment.split('*')[2] if len(segment.split('*')) > 2 else ""
                if any(re.match(pattern, provider_name.upper()) for pattern in realistic_provider_patterns):
                    result['realistic_elements'].append(f"Realistic provider: {provider_name}")
                else:
                    result['unrealistic_elements'].append(f"Generic provider name: {provider_name}")
            
            # Check for realistic procedure codes (5-digit CPT codes)
            elif 'HC:' in segment:
                codes = re.findall(r'HC:(\d{5})', segment)
                for code in codes:
                    # Common procedure code ranges
                    code_num = int(code)
                    if ((99200 <= code_num <= 99499) or  # E&M codes
                        (80000 <= code_num <= 89999) or  # Lab codes
                        (70000 <= code_num <= 79999)):   # Radiology codes
                        result['realistic_elements'].append(f"Valid CPT code: {code}")
                    else:
                        result['unrealistic_elements'].append(f"Unusual CPT code: {code}")
        
        return result


class FixtureQualityReport:
    """Generate quality reports for fixture system."""
    
    @staticmethod
    def generate_scenario_report() -> Dict[str, Dict]:
        """Generate quality report for all scenarios."""
        from . import PaymentScenarios, ClaimScenarios, ErrorScenarios
        
        report = {
            'payment_scenarios': {},
            'claim_scenarios': {},
            'error_scenarios': {},
            'summary': {
                'total_scenarios': 0,
                'valid_scenarios': 0,
                'scenarios_with_warnings': 0,
                'invalid_scenarios': 0
            }
        }
        
        # Test payment scenarios
        payment_scenarios = PaymentScenarios.get_all_scenarios()
        for name, scenario in payment_scenarios.items():
            edi_content = scenario.build()
            validation = EDIValidator.validate_transaction(edi_content)
            
            report['payment_scenarios'][name] = {
                'length': len(edi_content),
                'segment_count': len([s for s in edi_content.split('~') if s.strip()]),
                'errors': validation['errors'],
                'warnings': validation['warnings'],
                'is_valid': len(validation['errors']) == 0
            }
            
            report['summary']['total_scenarios'] += 1
            if len(validation['errors']) == 0:
                report['summary']['valid_scenarios'] += 1
            else:
                report['summary']['invalid_scenarios'] += 1
            
            if len(validation['warnings']) > 0:
                report['summary']['scenarios_with_warnings'] += 1
        
        # Test claim scenarios
        claim_scenarios = ClaimScenarios.get_all_scenarios()
        for name, scenario in claim_scenarios.items():
            if hasattr(scenario, 'build'):
                edi_content = scenario.build()
                validation = EDIValidator.validate_transaction(edi_content)
                
                report['claim_scenarios'][name] = {
                    'length': len(edi_content),
                    'segment_count': len([s for s in edi_content.split('~') if s.strip()]),
                    'errors': validation['errors'],
                    'warnings': validation['warnings'],
                    'is_valid': len(validation['errors']) == 0
                }
                
                report['summary']['total_scenarios'] += 1
                if len(validation['errors']) == 0:
                    report['summary']['valid_scenarios'] += 1
                else:
                    report['summary']['invalid_scenarios'] += 1
                
                if len(validation['warnings']) > 0:
                    report['summary']['scenarios_with_warnings'] += 1
        
        return report
    
    @staticmethod
    def generate_data_quality_report() -> Dict[str, Dict]:
        """Generate data quality report for YAML sources."""
        from . import data_loader
        
        report = {
            'payers': {
                'total_count': len(data_loader.payers),
                'types': {},
                'with_addresses': 0,
                'issues': []
            },
            'providers': {
                'total_count': len(data_loader.providers),
                'types': {},
                'specialties': {},
                'issues': []
            },
            'procedure_codes': {
                'total_count': len(data_loader.procedure_codes),
                'categories': {},
                'price_range': {'min': None, 'max': None, 'avg': None},
                'issues': []
            },
            'diagnosis_codes': {
                'total_count': len(data_loader.diagnosis_codes),
                'categories': {},
                'severities': {},
                'issues': []
            }
        }
        
        # Analyze payers
        for payer in data_loader.payers:
            payer_type = payer.get('type', 'unknown')
            report['payers']['types'][payer_type] = report['payers']['types'].get(payer_type, 0) + 1
            
            if 'address' in payer:
                report['payers']['with_addresses'] += 1
            
            # Check for issues
            if not payer.get('name'):
                report['payers']['issues'].append(f"Payer missing name: {payer.get('id')}")
            if not payer.get('id'):
                report['payers']['issues'].append(f"Payer missing ID: {payer.get('name')}")
        
        # Analyze providers
        for provider in data_loader.providers:
            provider_type = provider.get('type', 'unknown')
            report['providers']['types'][provider_type] = report['providers']['types'].get(provider_type, 0) + 1
            
            specialty = provider.get('specialty', 'unknown')
            report['providers']['specialties'][specialty] = report['providers']['specialties'].get(specialty, 0) + 1
            
            # Check NPI format
            npi = provider.get('npi', '')
            if not (npi.isdigit() and len(npi) == 10):
                report['providers']['issues'].append(f"Invalid NPI: {npi} for {provider.get('name')}")
        
        # Analyze procedure codes
        charges = []
        for code in data_loader.procedure_codes:
            category = code.get('category', 'unknown')
            report['procedure_codes']['categories'][category] = report['procedure_codes']['categories'].get(category, 0) + 1
            
            charge = code.get('typical_charge', 0)
            if isinstance(charge, (int, float)) and charge > 0:
                charges.append(charge)
            
            # Check CPT code format
            cpt_code = code.get('code', '')
            if not (cpt_code.isdigit() and len(cpt_code) == 5):
                report['procedure_codes']['issues'].append(f"Invalid CPT code: {cpt_code}")
        
        if charges:
            report['procedure_codes']['price_range'] = {
                'min': min(charges),
                'max': max(charges),
                'avg': sum(charges) / len(charges)
            }
        
        # Analyze diagnosis codes
        for code in data_loader.diagnosis_codes:
            category = code.get('category', 'unknown')
            report['diagnosis_codes']['categories'][category] = report['diagnosis_codes']['categories'].get(category, 0) + 1
            
            severity = code.get('severity', 'unknown')
            report['diagnosis_codes']['severities'][severity] = report['diagnosis_codes']['severities'].get(severity, 0) + 1
        
        return report
    
    @staticmethod
    def print_summary_report():
        """Print a summary report of fixture system quality."""
        print("=== EDI Fixture System Quality Report ===\n")
        
        # Scenario quality
        scenario_report = FixtureQualityReport.generate_scenario_report()
        summary = scenario_report['summary']
        
        print(f"Scenario Quality:")
        print(f"  Total Scenarios: {summary['total_scenarios']}")
        print(f"  Valid Scenarios: {summary['valid_scenarios']}")
        print(f"  Invalid Scenarios: {summary['invalid_scenarios']}")
        print(f"  With Warnings: {summary['scenarios_with_warnings']}")
        print(f"  Success Rate: {summary['valid_scenarios']/summary['total_scenarios']*100:.1f}%\n")
        
        # Data quality
        data_report = FixtureQualityReport.generate_data_quality_report()
        
        print(f"Data Source Quality:")
        print(f"  Payers: {data_report['payers']['total_count']} ({len(data_report['payers']['issues'])} issues)")
        print(f"  Providers: {data_report['providers']['total_count']} ({len(data_report['providers']['issues'])} issues)")
        print(f"  Procedure Codes: {data_report['procedure_codes']['total_count']} ({len(data_report['procedure_codes']['issues'])} issues)")
        print(f"  Diagnosis Codes: {data_report['diagnosis_codes']['total_count']} ({len(data_report['diagnosis_codes']['issues'])} issues)")
        
        price_range = data_report['procedure_codes']['price_range']
        if price_range['min'] is not None:
            print(f"  Price Range: ${price_range['min']:.2f} - ${price_range['max']:.2f} (avg: ${price_range['avg']:.2f})")
        
        print("\n=== Report Complete ===")


# Utility functions for common validation tasks

def validate_fixture_output(fixture_function, *args, **kwargs) -> bool:
    """
    Validate the output of a fixture function.
    
    Args:
        fixture_function: Function that returns EDI content
        *args, **kwargs: Arguments to pass to fixture function
        
    Returns:
        True if valid, False otherwise
    """
    try:
        if hasattr(fixture_function, 'build'):
            # It's a builder
            edi_content = fixture_function.build()
        else:
            # It's a function
            edi_content = fixture_function(*args, **kwargs)
        
        validation = EDIValidator.validate_transaction(edi_content)
        return len(validation['errors']) == 0
    except Exception:
        return False


def assert_valid_edi(edi_content: str, message: str = ""):
    """
    Assert that EDI content is valid, raising detailed error if not.
    
    Args:
        edi_content: EDI content to validate
        message: Optional message prefix for errors
    """
    validation = EDIValidator.validate_transaction(edi_content)
    
    if validation['errors']:
        error_msg = f"{message}\nEDI Validation Errors:\n"
        for error in validation['errors']:
            error_msg += f"  - {error}\n"
        
        if validation['warnings']:
            error_msg += "Warnings:\n"
            for warning in validation['warnings']:
                error_msg += f"  - {warning}\n"
        
        raise EDIValidationError(error_msg)


def check_realistic_data(edi_content: str) -> bool:
    """
    Check if EDI content contains realistic data.
    
    Returns:
        True if data appears realistic, False otherwise
    """
    realistic_data = EDIValidator.validate_realistic_data(edi_content)
    realistic_count = len(realistic_data['realistic_elements'])
    unrealistic_count = len(realistic_data['unrealistic_elements'])
    
    # Consider realistic if more realistic elements than unrealistic
    return realistic_count > unrealistic_count