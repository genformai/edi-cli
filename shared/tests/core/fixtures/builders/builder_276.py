"""
EDI 276 (Claim Status Inquiry) builder.
"""

from typing import List, Optional
from datetime import date
from decimal import Decimal

from .edi_builder import EDIBuilder
from ..base.data_types import EntityInfo, Address
from ..base.generators import DataGenerator, NameGenerator


class EDI276Builder(EDIBuilder):
    """Builder for EDI 276 Claim Status Inquiry transactions."""
    
    def __init__(self):
        """Initialize 276 builder with appropriate defaults."""
        super().__init__()
        
        # Set 276-specific envelope defaults
        self.envelope.functional_id = "HI"  # Health Care Claim Status
        self.envelope.version = "005010X212"
        
        # 276-specific fields
        self.provider: Optional[EntityInfo] = None
        self.claim_inquiries: List[dict] = []
        self.patient_info: Optional[EntityInfo] = None
    
    def transaction_type(self) -> str:
        """Return transaction type.""" 
        return "276"
    
    def with_provider(
        self,
        name: str,
        npi: str = None,
        provider_type: str = "41"  # Submitter
    ) -> 'EDI276Builder':
        """Add submitting provider information."""
        if npi is None:
            npi = DataGenerator.generate_npi()
            
        self.provider = EntityInfo(
            name=name,
            entity_type="2",  # Organization
            id_qualifier="XX",  # NPI
            id_value=npi
        )
        
        return self
    
    def with_claim_inquiry(
        self,
        claim_number: str,
        service_date: date = None,
        total_charge: Decimal = None,
        patient_first_name: str = None,
        patient_last_name: str = None,
        patient_id: str = None
    ) -> 'EDI276Builder':
        """Add a claim status inquiry."""
        if service_date is None:
            service_date = DataGenerator.generate_date()
        
        if total_charge is None:
            total_charge = DataGenerator.generate_amount(100, 2000)
        
        if patient_first_name is None or patient_last_name is None:
            first, middle, last = NameGenerator.generate_person_name()
            patient_first_name = patient_first_name or first
            patient_last_name = patient_last_name or last
        
        if patient_id is None:
            patient_id = DataGenerator.generate_control_number(9)
        
        inquiry = {
            "claim_number": claim_number,
            "service_date": service_date, 
            "total_charge": total_charge,
            "patient_first_name": patient_first_name,
            "patient_last_name": patient_last_name,
            "patient_id": patient_id
        }
        
        self.claim_inquiries.append(inquiry)
        return self
    
    def with_multiple_claim_inquiries(self, count: int = 3) -> 'EDI276Builder':
        """Add multiple claim inquiries."""
        for i in range(count):
            claim_id = f"CLM{i+1:03d}{DataGenerator.generate_control_number(3)}"
            self.with_claim_inquiry(claim_number=claim_id)
        
        return self
    
    def with_patient(
        self,
        first_name: str,
        last_name: str,
        patient_id: str = None,
        dob: date = None
    ) -> 'EDI276Builder':
        """Add patient information for inquiries."""
        if patient_id is None:
            patient_id = DataGenerator.generate_control_number(9)
        
        self.patient_info = EntityInfo(
            name=f"{last_name}, {first_name}",
            entity_type="1",  # Person
            first_name=first_name,
            last_name=last_name,
            id_qualifier="MI",  # Member ID
            id_value=patient_id
        )
        
        if dob:
            date_str = dob.strftime("%Y%m%d")
            self.dates.append({
                "type": "patient_birth_date",
                "date": date_str
            })
        
        return self
    
    def get_transaction_segments(self) -> List[str]:
        """Get 276-specific transaction segments."""
        segments = []
        
        # BHT - Beginning of Hierarchical Transaction
        inquiry_date = date.today().strftime("%Y%m%d")
        inquiry_time = "1430"
        control_number = DataGenerator.generate_control_number()
        segments.append(f"BHT*0019*13*{control_number}*{inquiry_date}*{inquiry_time}~")
        
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
            segments.append(self.provider.to_nm1_segment("41"))  # Submitter
        elif self.payee:  # Use payee as provider if available
            segments.append(self.payee.to_nm1_segment("41"))
        else:
            # Default provider
            npi = DataGenerator.generate_npi()
            segments.append(f"NM1*41*2*PROVIDER CLINIC*****XX*{npi}~")
        
        # Add claim inquiries
        if not self.claim_inquiries:
            # Add default inquiry if none specified
            self.with_claim_inquiry(f"CLM{DataGenerator.generate_control_number(6)}")
        
        for inquiry in self.claim_inquiries:
            hl_count += 1
            
            # HL 3 - Billing Provider Hierarchical Level
            segments.append(f"HL*{hl_count}*2*19*0~")  # Information source
            
            # TRN - Trace Number (unique for each inquiry)
            trace_num = DataGenerator.generate_trace_number()[:10]
            segments.append(f"TRN*1*{trace_num}*{DataGenerator.generate_control_number()}~")
            
            # REF - Claim Number
            segments.append(f"REF*1K*{inquiry['claim_number']}~")
            
            # DTM - Service Date
            service_date_str = inquiry['service_date'].strftime("%Y%m%d")
            segments.append(f"DTM*232*{service_date_str}~")
            
            # AMT - Claim Amount (optional)
            if inquiry.get('total_charge'):
                segments.append(f"AMT*T3*{inquiry['total_charge']}~")
            
            # Patient information
            patient_first = inquiry.get('patient_first_name', 'JANE')
            patient_last = inquiry.get('patient_last_name', 'DOE')
            patient_id = inquiry.get('patient_id', DataGenerator.generate_control_number(9))
            
            segments.append(f"NM1*QC*1*{patient_last}*{patient_first}***MI*{patient_id}~")
            
            # Add patient date of birth if available
            for date_info in self.dates:
                if date_info["type"] == "patient_birth_date":
                    segments.append(f"DMG*D8*{date_info['date']}~")
                    break
        
        return segments
    
    @classmethod
    def minimal(cls) -> 'EDI276Builder':
        """Create minimal valid 276."""
        return (cls()
                .with_payer("INSURANCE COMPANY")
                .with_provider("PROVIDER CLINIC")
                .with_claim_inquiry(f"CLM{DataGenerator.generate_control_number(6)}"))
    
    @classmethod
    def standard(cls) -> 'EDI276Builder':
        """Create standard 276 with typical data."""
        return (cls()
                .with_payer("ACME HEALTH INSURANCE", DataGenerator.generate_payer_id())
                .with_provider(f"{NameGenerator.generate_company_name()} CLINIC")
                .with_multiple_claim_inquiries(2)
                .with_trace_number())
    
    @classmethod
    def batch_inquiry(cls, claim_count: int = 5) -> 'EDI276Builder':
        """Create 276 with multiple claim inquiries."""
        builder = (cls()
                   .with_payer("BATCH HEALTH INSURANCE")
                   .with_provider("MEDICAL GROUP ASSOCIATES")
                   .with_trace_number())
        
        # Add multiple claims with varying data
        for i in range(claim_count):
            claim_id = f"BATCH{i+1:03d}{DataGenerator.generate_control_number(4)}"
            service_date = DataGenerator.generate_date()
            charge = DataGenerator.generate_amount(50, 1500)
            
            builder.with_claim_inquiry(
                claim_number=claim_id,
                service_date=service_date,
                total_charge=charge
            )
        
        return builder