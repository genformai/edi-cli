"""
EDI 270 (Eligibility Inquiry) builder.
"""

from typing import List, Optional
from datetime import date

from .edi_builder import EDIBuilder
from ..base.data_types import EntityInfo, Address
from ..base.generators import DataGenerator, NameGenerator, AddressGenerator


class EDI270Builder(EDIBuilder):
    """Builder for EDI 270 Eligibility Inquiry transactions."""
    
    def __init__(self):
        """Initialize 270 builder with appropriate defaults."""
        super().__init__()
        
        # Set 270-specific envelope defaults
        self.envelope.functional_id = "HS"  # Health Care Services Review
        self.envelope.version = "005010X279A1"
        
        # 270-specific fields
        self.subscriber: Optional[EntityInfo] = None
        self.dependent: Optional[EntityInfo] = None
        self.provider: Optional[EntityInfo] = None
        self.inquiry_types: List[str] = []
        self.service_types: List[str] = []
    
    def transaction_type(self) -> str:
        """Return transaction type."""
        return "270"
    
    def with_subscriber(
        self,
        first_name: str,
        last_name: str,
        member_id: str = None,
        dob: date = None
    ) -> 'EDI270Builder':
        """Add subscriber (insured person) information."""
        if member_id is None:
            member_id = DataGenerator.generate_control_number(9)
        
        self.subscriber = EntityInfo(
            name=f"{last_name}, {first_name}",
            entity_type="1",  # Person
            first_name=first_name,
            last_name=last_name,
            id_qualifier="MI",  # Member ID
            id_value=member_id
        )
        
        if dob:
            date_str = dob.strftime("%Y%m%d")
            self.dates.append({
                "type": "birth_date",
                "date": date_str
            })
        
        return self
    
    def with_dependent(
        self,
        first_name: str,
        last_name: str,
        relationship: str = "01",  # Spouse
        dob: date = None
    ) -> 'EDI270Builder':
        """Add dependent information."""
        self.dependent = EntityInfo(
            name=f"{last_name}, {first_name}",
            entity_type="1",
            first_name=first_name,
            last_name=last_name,
            id_qualifier="",  # Usually no separate ID for dependent
            id_value=""
        )
        
        if dob:
            date_str = dob.strftime("%Y%m%d")
            self.dates.append({
                "type": "dependent_birth_date", 
                "date": date_str
            })
        
        return self
    
    def with_provider(
        self,
        name: str,
        npi: str = None,
        provider_type: str = "1P"  # Provider
    ) -> 'EDI270Builder':
        """Add information requesting provider."""
        if npi is None:
            npi = DataGenerator.generate_npi()
            
        self.provider = EntityInfo(
            name=name,
            entity_type="2",  # Organization
            id_qualifier="XX",  # NPI
            id_value=npi
        )
        
        return self
    
    def with_eligibility_inquiry(self, service_type: str = "30") -> 'EDI270Builder':
        """
        Add eligibility inquiry type.
        
        Common service types:
        30 = Health Benefit Plan Coverage
        88 = Pharmacy
        98 = Professional Physician Visit Office
        AL = Vision (Optometry)
        F1 = Medical Care
        """
        if service_type not in self.service_types:
            self.service_types.append(service_type)
        return self
    
    def with_benefit_inquiry(self, benefit_type: str = "1") -> 'EDI270Builder':
        """
        Add benefit inquiry type.
        
        Benefit types:
        1 = Active Coverage
        6 = Inactive
        8 = Termination of Benefits
        """
        if benefit_type not in self.inquiry_types:
            self.inquiry_types.append(benefit_type)
        return self
    
    def with_service_date_range(
        self,
        start_date: date = None,
        end_date: date = None
    ) -> 'EDI270Builder':
        """Add service date range for inquiry."""
        if start_date:
            date_str = start_date.strftime("%Y%m%d")
            self.dates.append({
                "type": "service_start",
                "date": date_str
            })
        
        if end_date:
            date_str = end_date.strftime("%Y%m%d")
            self.dates.append({
                "type": "service_end", 
                "date": date_str
            })
        
        return self
    
    def get_transaction_segments(self) -> List[str]:
        """Get 270-specific transaction segments."""
        segments = []
        
        # BHT - Beginning of Hierarchical Transaction
        inquiry_date = date.today().strftime("%Y%m%d")
        inquiry_time = "1430"
        segments.append(f"BHT*0022*13*{DataGenerator.generate_control_number()}*{inquiry_date}*{inquiry_time}~")
        
        # Hierarchical structure
        hl_count = 1
        
        # HL 1 - Information Source (Payer)
        segments.append(f"HL*{hl_count}**20*1~")
        
        if self.payer:
            segments.append(self.payer.to_nm1_segment("PR"))
        else:
            # Default payer
            segments.append("NM1*PR*2*INSURANCE COMPANY*****PI*123456789~")
        
        hl_count += 1
        
        # HL 2 - Information Receiver (Provider)
        segments.append(f"HL*{hl_count}*1*21*1~")
        
        if self.provider:
            segments.append(self.provider.to_nm1_segment("1P"))
        elif self.payee:  # Use payee as provider if available
            segments.append(self.payee.to_nm1_segment("1P"))
        else:
            # Default provider
            npi = DataGenerator.generate_npi()
            segments.append(f"NM1*1P*2*PROVIDER CLINIC*****XX*{npi}~")
        
        hl_count += 1
        
        # HL 3 - Subscriber
        has_dependent = self.dependent is not None
        segments.append(f"HL*{hl_count}*2*22*{'1' if has_dependent else '0'}~")
        
        # TRN - Trace number for this inquiry
        trace_num = None
        for ref in self.reference_numbers:
            if ref["type"] == "trace_number":
                trace_num = ref["value"]
                break
        
        if not trace_num:
            trace_num = DataGenerator.generate_trace_number()[:10]  # Max 10 chars for 270
        
        segments.append(f"TRN*1*{trace_num}*{DataGenerator.generate_control_number()}~")
        
        # Subscriber information
        if self.subscriber:
            segments.append(self.subscriber.to_nm1_segment("IL"))  # Insured/Subscriber
            
            # Add date of birth if available
            for date_info in self.dates:
                if date_info["type"] == "birth_date":
                    segments.append(f"DMG*D8*{date_info['date']}~")
                    break
        else:
            # Default subscriber
            first, middle, last = NameGenerator.generate_person_name()
            member_id = DataGenerator.generate_control_number(9)
            segments.append(f"NM1*IL*1*{last}*{first}*{middle}***MI*{member_id}~")
        
        # Service type inquiries
        if self.service_types:
            for service_type in self.service_types:
                segments.append(f"EQ*{service_type}~")
        else:
            # Default to general health benefit plan coverage
            segments.append("EQ*30~")
        
        # Service date range if specified
        for date_info in self.dates:
            if date_info["type"] == "service_start":
                segments.append(f"DTP*291*D8*{date_info['date']}~")
            elif date_info["type"] == "service_end":
                segments.append(f"DTP*292*D8*{date_info['date']}~")
        
        # HL 4 - Dependent (if present)
        if self.dependent:
            hl_count += 1
            segments.append(f"HL*{hl_count}*3*23*0~")  # Patient, child of subscriber
            
            segments.append(self.dependent.to_nm1_segment("QC"))  # Patient
            
            # Add dependent date of birth if available
            for date_info in self.dates:
                if date_info["type"] == "dependent_birth_date":
                    segments.append(f"DMG*D8*{date_info['date']}~")
                    break
            
            # Service type inquiries for dependent
            if self.service_types:
                for service_type in self.service_types:
                    segments.append(f"EQ*{service_type}~")
            else:
                segments.append("EQ*30~")
        
        return segments
    
    @classmethod
    def minimal(cls) -> 'EDI270Builder':
        """Create minimal valid 270."""
        return (cls()
                .with_payer("INSURANCE COMPANY")
                .with_provider("PROVIDER CLINIC")  
                .with_subscriber("JANE", "DOE")
                .with_eligibility_inquiry())
    
    @classmethod
    def standard(cls) -> 'EDI270Builder':
        """Create standard 270 with typical data."""
        first, middle, last = NameGenerator.generate_person_name()
        
        return (cls()
                .with_payer("ACME HEALTH INSURANCE", DataGenerator.generate_payer_id())
                .with_provider(f"{NameGenerator.generate_company_name()} CLINIC")
                .with_subscriber(first, last, DataGenerator.generate_control_number(9))
                .with_eligibility_inquiry("30")  # Health benefit plan coverage
                .with_eligibility_inquiry("98")  # Professional physician visit
                .with_trace_number())
    
    @classmethod
    def with_dependent(cls) -> 'EDI270Builder':
        """Create 270 with dependent inquiry."""
        sub_first, sub_middle, sub_last = NameGenerator.generate_person_name()
        dep_first, dep_middle, dep_last = NameGenerator.generate_person_name()
        
        return (cls()
                .with_payer("FAMILY HEALTH INSURANCE")
                .with_provider("FAMILY MEDICINE CLINIC")
                .with_subscriber(sub_first, sub_last)
                .with_dependent(dep_first, dep_last)
                .with_eligibility_inquiry("30")
                .with_trace_number())