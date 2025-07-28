"""
EDI 837P (Professional Healthcare Claim) builder.
"""

from typing import List, Optional
from datetime import date
from decimal import Decimal

from .edi_builder import EDIBuilder
from ..base.data_types import EntityInfo, Address, ServiceData
from ..base.generators import DataGenerator, NameGenerator, AddressGenerator


class EDI837pBuilder(EDIBuilder):
    """Builder for EDI 837P Professional Healthcare Claim transactions."""
    
    def __init__(self):
        """Initialize 837P builder with appropriate defaults."""
        super().__init__()
        
        # Set 837P-specific envelope defaults
        self.envelope.functional_id = "HC"  # Health Care Claim
        self.envelope.version = "005010X222A1"
        
        # 837P-specific fields
        self.billing_provider: Optional[EntityInfo] = None
        self.rendering_provider: Optional[EntityInfo] = None
        self.subscriber: Optional[EntityInfo] = None
        self.patient: Optional[EntityInfo] = None
        self.diagnosis_codes: List[str] = []
        self.place_of_service: str = "11"  # Office
    
    def transaction_type(self) -> str:
        """Return transaction type."""
        return "837"
    
    def with_billing_provider(
        self,
        name: str,
        npi: str = None,
        tax_id: str = None,
        address: Address = None
    ) -> 'EDI837pBuilder':
        """Add billing provider information."""
        if npi is None:
            npi = DataGenerator.generate_npi()
        if tax_id is None:
            tax_id = DataGenerator.generate_ein()
        
        self.billing_provider = EntityInfo(
            name=name,
            entity_type="2",  # Organization
            id_qualifier="XX",  # NPI
            id_value=npi,
            address=address
        )
        
        return self
    
    def with_rendering_provider(
        self, 
        first_name: str,
        last_name: str,
        npi: str = None,
        specialty: str = "207R00000X"  # Internal Medicine
    ) -> 'EDI837pBuilder':
        """Add rendering provider (physician) information."""
        if npi is None:
            npi = DataGenerator.generate_npi()
        
        self.rendering_provider = EntityInfo(
            name=f"{last_name}, {first_name}",
            entity_type="1",  # Person
            first_name=first_name,
            last_name=last_name,
            id_qualifier="XX",
            id_value=npi
        )
        
        return self
    
    def with_subscriber(
        self,
        first_name: str,
        last_name: str,
        member_id: str = None,
        group_number: str = None,
        dob: date = None,
        gender: str = "M"
    ) -> 'EDI837pBuilder':
        """Add subscriber (insured person) information."""
        if member_id is None:
            member_id = DataGenerator.generate_control_number(9)
        if group_number is None:
            group_number = f"GRP{DataGenerator.generate_control_number(6)}"
        
        self.subscriber = EntityInfo(
            name=f"{last_name}, {first_name}",
            entity_type="1",
            first_name=first_name,
            last_name=last_name,
            id_qualifier="MI",
            id_value=member_id
        )
        
        if dob:
            date_str = dob.strftime("%Y%m%d")
            self.dates.append({
                "type": "subscriber_birth_date",
                "date": date_str,
                "gender": gender
            })
        
        return self
    
    def with_patient(
        self,
        first_name: str,
        last_name: str,
        relationship_to_subscriber: str = "18",  # Self
        dob: date = None,
        gender: str = "M"
    ) -> 'EDI837pBuilder':
        """Add patient information (if different from subscriber)."""
        self.patient = EntityInfo(
            name=f"{last_name}, {first_name}",
            entity_type="1",
            first_name=first_name,
            last_name=last_name
        )
        
        if dob:
            date_str = dob.strftime("%Y%m%d")
            self.dates.append({
                "type": "patient_birth_date",
                "date": date_str,
                "gender": gender,
                "relationship": relationship_to_subscriber
            })
        
        return self
    
    def with_diagnosis(self, diagnosis_code: str) -> 'EDI837pBuilder':
        """Add a diagnosis code."""
        if diagnosis_code not in self.diagnosis_codes:
            self.diagnosis_codes.append(diagnosis_code)
        return self
    
    def with_multiple_diagnoses(self, codes: List[str] = None) -> 'EDI837pBuilder':
        """Add multiple diagnosis codes."""
        if codes is None:
            codes = [
                DataGenerator.generate_diagnosis_code(),
                DataGenerator.generate_diagnosis_code()
            ]
        
        for code in codes:
            self.with_diagnosis(code)
        
        return self
    
    def with_place_of_service(self, pos_code: str) -> 'EDI837pBuilder':
        """
        Set place of service code.
        
        Common codes:
        11 = Office
        21 = Inpatient Hospital  
        22 = Outpatient Hospital
        23 = Emergency Room
        """
        self.place_of_service = pos_code
        return self
    
    def with_office_visit(
        self,
        procedure_code: str = "99213",
        charge: Decimal = None
    ) -> 'EDI837pBuilder':
        """Add a typical office visit service."""
        if charge is None:
            charge = DataGenerator.generate_amount(100, 300)
        
        return self.with_service(
            procedure_code=procedure_code,
            charge=charge,
            paid=charge,  # For claim submission, paid = charge
            units=Decimal("1")
        )
    
    def with_lab_service(
        self,
        procedure_code: str = "80053",
        charge: Decimal = None
    ) -> 'EDI837pBuilder':
        """Add a laboratory service."""
        if charge is None:
            charge = DataGenerator.generate_amount(50, 150)
        
        return self.with_service(
            procedure_code=procedure_code,
            charge=charge,
            paid=charge,
            units=Decimal("1")
        )
    
    def get_transaction_segments(self) -> List[str]:
        """Get 837P-specific transaction segments."""
        segments = []
        
        # BHT - Beginning of Hierarchical Transaction
        creation_date = date.today().strftime("%Y%m%d")
        creation_time = "1430"
        control_number = DataGenerator.generate_control_number()
        segments.append(f"BHT*0019*00*{control_number}*{creation_date}*{creation_time}*CH~")
        
        # Submitter information (required)
        submitter_name = self.billing_provider.name if self.billing_provider else "BILLING COMPANY"
        submitter_id = DataGenerator.generate_control_number(9)
        segments.append(f"NM1*41*2*{submitter_name}*****46*{submitter_id}~")
        
        # Submitter contact info
        segments.append(f"PER*IC*CONTACT*TE*{DataGenerator.generate_phone()}~")
        
        # Receiver (clearinghouse/payer)
        receiver_name = self.payer.name if self.payer else "INSURANCE COMPANY"
        receiver_id = DataGenerator.generate_payer_id()
        segments.append(f"NM1*40*2*{receiver_name}*****46*{receiver_id}~")
        
        # Hierarchical structure
        hl_count = 1
        
        # HL 1 - Billing Provider
        segments.append(f"HL*{hl_count}**20*1~")
        
        # Provider specialty (PRV segment)
        specialty = "207R00000X"  # Internal Medicine
        segments.append(f"PRV*BI*PXC*{specialty}~")
        
        # Billing provider identification
        if self.billing_provider:
            segments.append(self.billing_provider.to_nm1_segment("85"))
            if self.billing_provider.address:
                segments.append(self.billing_provider.address.to_n3_segment())
                segments.append(self.billing_provider.address.to_n4_segment())
        else:
            # Default billing provider 
            npi = DataGenerator.generate_npi()
            segments.append(f"NM1*85*2*BILLING PROVIDER*****XX*{npi}~")
        
        # Tax identification
        tax_id = DataGenerator.generate_ein()
        segments.append(f"REF*EI*{tax_id}~")
        
        hl_count += 1
        
        # HL 2 - Subscriber 
        segments.append(f"HL*{hl_count}*1*22*1~")  # Subscriber level, has child
        
        # Subscriber information
        segments.append("SBR*P*18*GROUP123**CI****MB~")  # Primary, self, group insurance
        
        if self.subscriber:
            segments.append(self.subscriber.to_nm1_segment("IL"))
            
            # Add demographics
            for date_info in self.dates:
                if date_info["type"] == "subscriber_birth_date":
                    gender = date_info.get("gender", "M")
                    segments.append(f"DMG*D8*{date_info['date']}*{gender}~")
                    break
        else:
            # Default subscriber
            first, middle, last = NameGenerator.generate_person_name()
            member_id = DataGenerator.generate_control_number(9)
            segments.append(f"NM1*IL*1*{last}*{first}*{middle}***MI*{member_id}~")
        
        # Payer information
        if self.payer:
            segments.append(self.payer.to_nm1_segment("PR"))
        else:
            payer_id = DataGenerator.generate_payer_id()
            segments.append(f"NM1*PR*2*INSURANCE COMPANY*****PI*{payer_id}~")
        
        hl_count += 1
        
        # HL 3 - Patient (if different from subscriber)
        if self.patient:
            segments.append(f"HL*{hl_count}*2*23*0~")  # Patient level, no children
            
            segments.append("PAT*19~")  # Patient information
            segments.append(self.patient.to_nm1_segment("QC"))
            
            # Patient demographics
            for date_info in self.dates:
                if date_info["type"] == "patient_birth_date":
                    gender = date_info.get("gender", "M")
                    segments.append(f"DMG*D8*{date_info['date']}*{gender}~")
                    break
        else:
            # Patient is same as subscriber
            segments.append(f"HL*{hl_count}*2*23*0~")
            segments.append("PAT*19~")
        
        # Claim information
        if self.claims:
            claim = self.claims[0]  # Use first claim
            
            # CLM - Claim Information
            total_charge = sum(service.charge for service in self.services) if self.services else claim.total_charge
            
            segments.append(
                f"CLM*{claim.claim_id}*{total_charge}***{self.place_of_service}:B:1*Y*A*Y*I~"
            )
            
            # Claim dates
            service_date = DataGenerator.generate_date()
            date_str = service_date.strftime("%Y%m%d")
            segments.append(f"DTP*431*D8*{date_str}~")  # Claim service date
            
            # Diagnosis information
            if self.diagnosis_codes:
                # HI segment for diagnoses
                diag_segments = []
                for i, code in enumerate(self.diagnosis_codes[:12]):  # Max 12 diagnoses
                    qualifier = "BK" if i == 0 else "BF"  # Primary vs secondary
                    diag_segments.append(f"{qualifier}:{code}")
                segments.append(f"HI*{'.'.join(diag_segments)}~")
            
            # Rendering provider (if different from billing)
            if self.rendering_provider:
                segments.append(self.rendering_provider.to_nm1_segment("82"))
            
            # Service lines
            for i, service in enumerate(self.services, 1):
                segments.append(f"LX*{i}~")  # Service line number
                segments.append(service.to_svc_segment())
                segments.append(f"DTP*472*D8*{date_str}~")  # Service date
                
                # Link to diagnosis (first diagnosis)
                if self.diagnosis_codes:
                    segments.append("DX*1~")  # Points to first diagnosis
        
        return segments
    
    @classmethod
    def minimal(cls) -> 'EDI837pBuilder':
        """Create minimal valid 837P."""
        return (cls()
                .with_billing_provider("MINIMAL CLINIC")
                .with_payer("INSURANCE COMPANY")
                .with_subscriber("JANE", "DOE")
                .with_claim(claim_id="MIN001", charge=Decimal("100.00"))
                .with_diagnosis("Z00.00")
                .with_office_visit())
    
    @classmethod
    def standard(cls) -> 'EDI837pBuilder':
        """Create standard 837P with typical data."""
        first, middle, last = NameGenerator.generate_person_name()
        
        address = Address(
            line1=AddressGenerator.generate_street_address(),
            city=AddressGenerator.generate_city(),
            state=AddressGenerator.generate_state(),
            zip_code=DataGenerator.generate_zip_code()
        )
        
        return (cls()
                .with_billing_provider(f"{NameGenerator.generate_company_name()} CLINIC", address=address)
                .with_rendering_provider("JOHN", "SMITH")
                .with_payer("ACME HEALTH INSURANCE")
                .with_subscriber(first, last, dob=DataGenerator.generate_date())
                .with_claim(claim_id=DataGenerator.generate_claim_id(), charge=Decimal("250.00"))
                .with_multiple_diagnoses(["I10", "E11.9"])  # Hypertension, Diabetes
                .with_office_visit("99214", Decimal("175.00"))
                .with_lab_service("85025", Decimal("75.00")))
    
    @classmethod
    def emergency_visit(cls) -> 'EDI837pBuilder':
        """Create 837P for emergency department visit."""
        first, middle, last = NameGenerator.generate_person_name()
        
        return (cls()
                .with_billing_provider("CITY HOSPITAL")
                .with_rendering_provider("EMERGENCY", "PHYSICIAN")
                .with_payer("EMERGENCY INSURANCE")
                .with_subscriber(first, last)
                .with_place_of_service("23")  # Emergency Room
                .with_claim(claim_id=DataGenerator.generate_claim_id(), charge=Decimal("850.00"))
                .with_diagnosis("R06.02")  # Shortness of breath
                .with_service("99283", Decimal("450.00"), Decimal("450.00"))  # ER visit level 3
                .with_service("71020", Decimal("400.00"), Decimal("400.00")))  # Chest X-ray