"""
Data generators for EDI test fixtures.
"""

import random
import string
from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import List, Optional
import uuid


class DataGenerator:
    """Utility class for generating realistic test data."""
    
    # Common procedure codes
    PROCEDURE_CODES = [
        "99213", "99214", "99215", "99203", "99204", "99205",  # Office visits
        "99281", "99282", "99283", "99284", "99285",          # Emergency dept
        "36415", "85025", "80053", "80061",                   # Lab procedures
    ]
    
    # Common diagnosis codes (ICD-10)
    DIAGNOSIS_CODES = [
        "Z00.00", "Z01.419", "I10", "E11.9", "M79.3",        # Common conditions
        "R06.02", "R50.9", "K59.00", "M25.50", "G43.909"     # Symptoms
    ]
    
    # Adjustment reason codes
    ADJUSTMENT_CODES = {
        "CO": ["45", "96", "97", "151", "204"],  # Contractual
        "PR": ["1", "2", "3", "4", "5"],         # Patient responsibility
        "OA": ["23", "94", "109", "140"]         # Other adjustments
    }
    
    @staticmethod
    def generate_npi(valid: bool = True) -> str:
        """Generate a National Provider Identifier."""
        if not valid:
            return "INVALID123"
        
        # Generate 9 random digits
        digits = [random.randint(0, 9) for _ in range(9)]
        
        # Simple check digit calculation (not actual Luhn)
        # For testing purposes, we'll use a basic algorithm
        check_digit = sum(digits) % 10
        digits.append(check_digit)
        
        return ''.join(str(d) for d in digits)
    
    @staticmethod
    def generate_control_number(length: int = 9) -> str:
        """Generate a control number."""
        return ''.join(random.choices(string.digits, k=length))
    
    @staticmethod
    def generate_claim_id(prefix: str = "CLM") -> str:
        """Generate a claim identifier."""
        suffix = ''.join(random.choices(string.digits, k=6))
        return f"{prefix}{suffix}"
    
    @staticmethod
    def generate_payer_id(prefix: str = "PAY") -> str:
        """Generate a payer identifier."""
        suffix = ''.join(random.choices(string.digits, k=6))
        return f"{prefix}{suffix}"
    
    @staticmethod
    def generate_amount(min_amount: float = 0.0, max_amount: float = 10000.0) -> Decimal:
        """Generate a monetary amount."""
        amount = random.uniform(min_amount, max_amount)
        return Decimal(str(round(amount, 2)))
    
    @staticmethod
    def generate_date(
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> date:
        """Generate a random date within range."""
        if start_date is None:
            start_date = date.today() - timedelta(days=365)
        if end_date is None:
            end_date = date.today()
        
        time_between = end_date - start_date
        days_between = time_between.days
        random_days = random.randrange(days_between)
        
        return start_date + timedelta(days=random_days)
    
    @staticmethod
    def generate_ssn() -> str:
        """Generate a Social Security Number (for testing only)."""
        # Format: XXX-XX-XXXX
        area = random.randint(100, 999)
        group = random.randint(10, 99)
        serial = random.randint(1000, 9999)
        return f"{area:03d}{group:02d}{serial:04d}"
    
    @staticmethod
    def generate_ein() -> str:
        """Generate an Employer Identification Number."""
        # Format: XX-XXXXXXX
        prefix = random.randint(10, 99)
        suffix = random.randint(1000000, 9999999)
        return f"{prefix:02d}-{suffix:07d}"
    
    @staticmethod
    def generate_procedure_code() -> str:
        """Generate a procedure code."""
        # Try to use YAML data if available, fallback to hardcoded list
        try:
            from ..data.data_loader import data_loader
            codes = data_loader.get_random_procedure_codes(count=1)
            return codes[0]['code']
        except (ImportError, Exception):
            return random.choice(DataGenerator.PROCEDURE_CODES)
    
    @staticmethod
    def generate_diagnosis_code() -> str:
        """Generate a diagnosis code."""
        # Try to use YAML data if available, fallback to hardcoded list
        try:
            from ..data.data_loader import data_loader
            codes = data_loader.get_random_diagnosis_codes(count=1)
            return codes[0]['code']
        except (ImportError, Exception):
            return random.choice(DataGenerator.DIAGNOSIS_CODES)
    
    @staticmethod
    def generate_realistic_payer_name() -> str:
        """Generate a realistic payer name using YAML data."""
        try:
            from ..data.data_loader import data_loader
            payer = data_loader.get_random_payer()
            return payer['name']
        except (ImportError, Exception):
            return NameGenerator.generate_company_name() + " INSURANCE"
    
    @staticmethod
    def generate_realistic_provider_name() -> str:
        """Generate a realistic provider name using YAML data."""
        try:
            from ..data.data_loader import data_loader
            provider = data_loader.get_random_provider()
            return provider['name']
        except (ImportError, Exception):
            return NameGenerator.generate_company_name() + " CLINIC"
    
    @staticmethod
    def generate_adjustment_code(group: str = "CO") -> str:
        """Generate an adjustment reason code."""
        return random.choice(DataGenerator.ADJUSTMENT_CODES.get(group, ["45"]))
    
    @staticmethod
    def generate_phone() -> str:
        """Generate a phone number."""
        area = random.randint(200, 999)
        exchange = random.randint(200, 999)
        number = random.randint(1000, 9999)
        return f"{area:03d}{exchange:03d}{number:04d}"
    
    @staticmethod
    def generate_email(domain: str = "example.com") -> str:
        """Generate an email address."""
        username = ''.join(random.choices(string.ascii_lowercase, k=8))
        return f"{username}@{domain}"
    
    @staticmethod 
    def generate_zip_code() -> str:
        """Generate a ZIP code."""
        if random.choice([True, False]):
            # ZIP+4 format
            zip5 = random.randint(10000, 99999)
            plus4 = random.randint(1000, 9999)
            return f"{zip5:05d}-{plus4:04d}"
        else:
            # Standard 5-digit ZIP
            return f"{random.randint(10000, 99999):05d}"
    
    @staticmethod
    def generate_trace_number() -> str:
        """Generate a trace number for transactions."""
        return str(uuid.uuid4()).replace('-', '')[:15]


class NameGenerator:
    """Generate realistic names for testing."""
    
    FIRST_NAMES = [
        "James", "Mary", "John", "Patricia", "Robert", "Jennifer", "Michael", "Linda",
        "William", "Elizabeth", "David", "Barbara", "Richard", "Susan", "Joseph", "Jessica"
    ]
    
    LAST_NAMES = [
        "Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis",
        "Rodriguez", "Martinez", "Hernandez", "Lopez", "Gonzalez", "Wilson", "Anderson", "Thomas"
    ]
    
    COMPANY_SUFFIXES = [
        "INSURANCE", "HEALTH PLAN", "MEDICAL CENTER", "CLINIC", "HOSPITAL",
        "HEALTHCARE", "FAMILY MEDICINE", "SPECIALISTS", "ASSOCIATES"
    ]
    
    COMPANY_PREFIXES = [
        "ACME", "GENERAL", "NATIONAL", "UNITED", "AMERICAN", "REGIONAL",
        "COMMUNITY", "CENTRAL", "WESTERN", "EASTERN", "NORTHERN", "SOUTHERN"
    ]
    
    @staticmethod
    def generate_person_name() -> tuple[str, str, str]:
        """Generate first, middle, last name."""
        first = random.choice(NameGenerator.FIRST_NAMES)
        middle = random.choice(string.ascii_uppercase)
        last = random.choice(NameGenerator.LAST_NAMES)
        return first, middle, last
    
    @staticmethod
    def generate_company_name() -> str:
        """Generate a company name."""
        prefix = random.choice(NameGenerator.COMPANY_PREFIXES)
        suffix = random.choice(NameGenerator.COMPANY_SUFFIXES)
        return f"{prefix} {suffix}"


class AddressGenerator:
    """Generate realistic addresses for testing."""
    
    STREET_NAMES = [
        "MAIN", "FIRST", "SECOND", "PARK", "WASHINGTON", "MAPLE", "OAK", "PINE",
        "ELM", "CEDAR", "SPRING", "HILL", "CHURCH", "SCHOOL", "HIGH", "BROADWAY"
    ]
    
    STREET_TYPES = ["ST", "AVE", "BLVD", "DR", "LN", "RD", "WAY", "PL", "CT"]
    
    CITIES = [
        "Springfield", "Franklin", "Georgetown", "Clinton", "Riverside", "Fairview",
        "Midway", "Oak Grove", "Five Points", "Pleasant Hill", "Mount Pleasant", "Centerville"
    ]
    
    STATES = [
        "AL", "AK", "AZ", "AR", "CA", "CO", "CT", "DE", "FL", "GA", "HI", "ID",
        "IL", "IN", "IA", "KS", "KY", "LA", "ME", "MD", "MA", "MI", "MN", "MS",
        "MO", "MT", "NE", "NV", "NH", "NJ", "NM", "NY", "NC", "ND", "OH", "OK",
        "OR", "PA", "RI", "SC", "SD", "TN", "TX", "UT", "VT", "VA", "WA", "WV", "WI", "WY"
    ]
    
    @staticmethod
    def generate_street_address() -> str:
        """Generate a street address."""
        number = random.randint(1, 9999)
        street = random.choice(AddressGenerator.STREET_NAMES)
        street_type = random.choice(AddressGenerator.STREET_TYPES)
        return f"{number} {street} {street_type}"
    
    @staticmethod
    def generate_city() -> str:
        """Generate a city name."""
        return random.choice(AddressGenerator.CITIES)
    
    @staticmethod
    def generate_state() -> str:
        """Generate a state abbreviation."""
        return random.choice(AddressGenerator.STATES)