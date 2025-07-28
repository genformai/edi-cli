"""
Shared test data for EDI testing.

This module provides common test data constants and sample data
used across multiple test modules.
"""

from typing import Dict, List, Any


class TestData:
    """Container for shared test data constants."""
    
    # Common test dates
    DATES = {
        "service_date": "2024-12-26",
        "service_date_ccyymmdd": "20241226",
        "payment_date": "2024-12-27", 
        "payment_date_ccyymmdd": "20241227",
        "production_date": "2024-12-28",
        "production_date_ccyymmdd": "20241228"
    }
    
    # Common test amounts  
    AMOUNTS = {
        "small_charge": 50.00,
        "medium_charge": 250.00,
        "large_charge": 1000.00,
        "small_payment": 40.00,
        "medium_payment": 200.00,
        "large_payment": 800.00,
        "patient_responsibility": 10.00,
        "copay_amount": 25.00,
        "deductible_amount": 100.00
    }
    
    # Test NPIs (valid format but test-only)
    NPIS = {
        "provider_npi": "1234567893",  # Checksum valid
        "billing_npi": "9876543210",   # Different valid NPI
        "rendering_npi": "1122334455", # Another valid NPI
        "facility_npi": "5544332211"   # Facility NPI
    }
    
    # Test identifiers
    IDENTIFIERS = {
        "claim_id": "TESTCLAIM001",
        "patient_id": "TESTPAT001", 
        "subscriber_id": "TESTSUB001",
        "group_number": "TESTGRP001",
        "policy_number": "TESTPOL001",
        "trace_number": "TESTTRACE001"
    }
    
    # Common diagnosis codes
    DIAGNOSIS_CODES = {
        "diabetes": "E11.9",
        "hypertension": "I10", 
        "back_pain": "M54.9",
        "chest_pain": "R06.02",
        "headache": "R51"
    }
    
    # Common procedure codes
    PROCEDURE_CODES = {
        "office_visit_new": "99201",
        "office_visit_established": "99213", 
        "comprehensive_exam": "99396",
        "x_ray_chest": "71020",
        "blood_glucose": "82947"
    }
    
    # Test payer information
    PAYERS = {
        "primary_payer": {
            "name": "TEST INSURANCE COMPANY",
            "id": "12345",
            "address": "123 PAYER ST",
            "city": "PAYERVILLE",
            "state": "NY", 
            "zip": "12345"
        },
        "secondary_payer": {
            "name": "SECONDARY TEST INSURANCE", 
            "id": "67890",
            "address": "456 SECONDARY AVE",
            "city": "SECONDARY CITY",
            "state": "CA",
            "zip": "67890"
        }
    }
    
    # Test provider information
    PROVIDERS = {
        "billing_provider": {
            "name": "TEST MEDICAL GROUP",
            "npi": NPIS["billing_npi"],
            "tax_id": "123456789",
            "address": "789 MEDICAL DR",
            "city": "MEDICALTOWN", 
            "state": "FL",
            "zip": "33101"
        },
        "rendering_provider": {
            "name": "DR JANE SMITH",
            "npi": NPIS["rendering_npi"], 
            "specialty": "Family Medicine",
            "address": "789 MEDICAL DR STE 100",
            "city": "MEDICALTOWN",
            "state": "FL", 
            "zip": "33101"
        }
    }
    
    # Test patient information
    PATIENTS = {
        "primary_patient": {
            "last_name": "DOE",
            "first_name": "JOHN",
            "middle_initial": "A",
            "member_id": IDENTIFIERS["patient_id"],
            "birth_date": "1980-05-15",
            "gender": "M",
            "address": "123 PATIENT ST",
            "city": "PATIENTVILLE", 
            "state": "TX",
            "zip": "75001"
        },
        "secondary_patient": {
            "last_name": "SMITH", 
            "first_name": "JANE",
            "middle_initial": "B",
            "member_id": "TESTPAT002",
            "birth_date": "1975-08-22",
            "gender": "F",
            "address": "456 PATIENT AVE",
            "city": "PATIENTVILLE",
            "state": "TX",
            "zip": "75002"
        }
    }
    
    @classmethod
    def get_test_date(cls, date_type: str, format_type: str = "iso") -> str:
        """
        Get a test date in the specified format.
        
        Args:
            date_type: Type of date (service_date, payment_date, etc.)
            format_type: Format type (iso, ccyymmdd)
            
        Returns:
            Formatted date string
        """
        if format_type == "ccyymmdd":
            date_key = f"{date_type}_ccyymmdd"
        else:
            date_key = date_type
            
        if date_key not in cls.DATES:
            raise ValueError(f"Unknown date type: {date_type}")
            
        return cls.DATES[date_key]
    
    @classmethod
    def get_test_amount(cls, amount_type: str) -> float:
        """
        Get a test amount by type.
        
        Args:
            amount_type: Type of amount (small_charge, medium_payment, etc.)
            
        Returns:
            Amount as float
        """
        if amount_type not in cls.AMOUNTS:
            raise ValueError(f"Unknown amount type: {amount_type}")
            
        return cls.AMOUNTS[amount_type]