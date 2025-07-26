"""
EDI 837P (Professional Claims) AST Definitions

This module defines the Abstract Syntax Tree nodes for EDI 837P
Professional Claims transactions.
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from .ast import Node


@dataclass
class SubmitterInfo(Node):
    """Information about the submitter (billing entity)."""
    name: str
    entity_identifier_code: str = "41"  # Submitter
    id_code_qualifier: str = "46"       # Electronic Transmitter ID
    id_code: str = ""
    contact_name: Optional[str] = None
    contact_phone: Optional[str] = None
    contact_email: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        data = {
            "name": self.name,
            "entity_identifier_code": self.entity_identifier_code,
            "id_code_qualifier": self.id_code_qualifier,
            "id_code": self.id_code
        }
        if self.contact_name:
            data["contact_name"] = self.contact_name
        if self.contact_phone:
            data["contact_phone"] = self.contact_phone
        if self.contact_email:
            data["contact_email"] = self.contact_email
        return data


@dataclass 
class ReceiverInfo(Node):
    """Information about the receiver (payer)."""
    name: str
    entity_identifier_code: str = "40"  # Receiver
    id_code_qualifier: str = "46"       # Electronic Receiver ID
    id_code: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "entity_identifier_code": self.entity_identifier_code,
            "id_code_qualifier": self.id_code_qualifier,
            "id_code": self.id_code
        }


@dataclass
class BillingProviderInfo(Node):
    """Information about the billing provider."""
    name: str
    entity_identifier_code: str = "85"  # Billing Provider
    id_code_qualifier: str = "XX"       # NPI
    npi: str = ""
    tax_id_qualifier: str = "EI"        # Employer ID
    tax_id: str = ""
    address: Optional[Dict[str, str]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        data = {
            "name": self.name,
            "entity_identifier_code": self.entity_identifier_code,
            "id_code_qualifier": self.id_code_qualifier,
            "npi": self.npi,
            "tax_id_qualifier": self.tax_id_qualifier,
            "tax_id": self.tax_id
        }
        if self.address:
            data["address"] = self.address
        return data


@dataclass
class SubscriberInfo(Node):
    """Information about the subscriber (insured person)."""
    payer_responsibility_code: str      # P=Primary, S=Secondary, T=Tertiary
    member_id: str
    first_name: str
    last_name: str
    middle_name: Optional[str] = None
    name_suffix: Optional[str] = None
    id_code_qualifier: str = "MI"       # Member ID
    gender: Optional[str] = None        # M=Male, F=Female, U=Unknown
    date_of_birth: Optional[str] = None # CCYYMMDD format
    address: Optional[Dict[str, str]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        data = {
            "payer_responsibility_code": self.payer_responsibility_code,
            "member_id": self.member_id,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "id_code_qualifier": self.id_code_qualifier
        }
        
        if self.middle_name:
            data["middle_name"] = self.middle_name
        if self.name_suffix:
            data["name_suffix"] = self.name_suffix
        if self.gender:
            data["gender"] = self.gender
        if self.date_of_birth:
            data["date_of_birth"] = self.date_of_birth
        if self.address:
            data["address"] = self.address
            
        return data


@dataclass
class PatientInfo(Node):
    """Information about the patient (if different from subscriber)."""
    relationship_code: str              # 18=Self, 01=Spouse, 19=Child, etc.
    first_name: str
    last_name: str
    middle_name: Optional[str] = None
    name_suffix: Optional[str] = None
    gender: Optional[str] = None
    date_of_birth: Optional[str] = None
    address: Optional[Dict[str, str]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        data = {
            "relationship_code": self.relationship_code,
            "first_name": self.first_name,
            "last_name": self.last_name
        }
        
        if self.middle_name:
            data["middle_name"] = self.middle_name
        if self.name_suffix:
            data["name_suffix"] = self.name_suffix
        if self.gender:
            data["gender"] = self.gender
        if self.date_of_birth:
            data["date_of_birth"] = self.date_of_birth
        if self.address:
            data["address"] = self.address
            
        return data


@dataclass
class ClaimInfo837P(Node):
    """Professional claim information (CLM segment)."""
    claim_id: str
    total_charge: float
    place_of_service_code: str
    type_of_bill_code: Optional[str] = None
    signature_indicator: str = "Y"      # Y=Yes, N=No
    medicare_assignment: str = "A"      # A=Assigned, B=Assignment Accepted, C=Not Assigned
    benefits_assignment: str = "Y"      # Y=Benefits Assigned to Provider
    release_of_info: str = "Y"          # Y=Provider has on file, N=No
    
    def to_dict(self) -> Dict[str, Any]:
        data = {
            "claim_id": self.claim_id,
            "total_charge": self.total_charge,
            "place_of_service_code": self.place_of_service_code,
            "signature_indicator": self.signature_indicator,
            "medicare_assignment": self.medicare_assignment,
            "benefits_assignment": self.benefits_assignment,
            "release_of_info": self.release_of_info
        }
        
        if self.type_of_bill_code:
            data["type_of_bill_code"] = self.type_of_bill_code
            
        return data


@dataclass
class ServiceLine837P(Node):
    """Professional service line information (SV1 segment)."""
    line_number: str
    procedure_code: str                 # CPT/HCPCS code
    procedure_modifiers: List[str]      # Up to 4 modifiers
    charge_amount: float
    units: float
    diagnosis_pointers: List[str]       # References to diagnosis codes
    emergency_indicator: Optional[str] = None  # Y=Emergency
    copay_status: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        data = {
            "line_number": self.line_number,
            "procedure_code": self.procedure_code,
            "procedure_modifiers": self.procedure_modifiers,
            "charge_amount": self.charge_amount,
            "units": self.units,
            "diagnosis_pointers": self.diagnosis_pointers
        }
        
        if self.emergency_indicator:
            data["emergency_indicator"] = self.emergency_indicator
        if self.copay_status:
            data["copay_status"] = self.copay_status
            
        return data


@dataclass
class DiagnosisInfo(Node):
    """Diagnosis information (HI segment)."""
    qualifier: str                      # BK=Primary, BF=Secondary, etc.
    code: str                          # ICD-10-CM diagnosis code
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "qualifier": self.qualifier,
            "code": self.code
        }


@dataclass
class RenderingProviderInfo(Node):
    """Information about the rendering provider."""
    name: str
    npi: str
    entity_identifier_code: str = "82"  # Rendering Provider
    id_code_qualifier: str = "XX"       # NPI
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "entity_identifier_code": self.entity_identifier_code,
            "name": self.name,
            "id_code_qualifier": self.id_code_qualifier,
            "npi": self.npi
        }


@dataclass
class Transaction837P(Node):
    """837P Professional Claims Transaction."""
    header: Dict[str, str]
    submitter: Optional[SubmitterInfo] = None
    receiver: Optional[ReceiverInfo] = None
    billing_provider: Optional[BillingProviderInfo] = None
    subscriber: Optional[SubscriberInfo] = None
    patient: Optional[PatientInfo] = None  # Only if different from subscriber
    claim: Optional[ClaimInfo837P] = None
    diagnoses: List[DiagnosisInfo] = None
    service_lines: List[ServiceLine837P] = None
    rendering_provider: Optional[RenderingProviderInfo] = None
    
    def __post_init__(self):
        if self.diagnoses is None:
            self.diagnoses = []
        if self.service_lines is None:
            self.service_lines = []
    
    def to_dict(self) -> Dict[str, Any]:
        data = {"header": self.header}
        
        if self.submitter:
            data["submitter"] = self.submitter.to_dict()
        if self.receiver:
            data["receiver"] = self.receiver.to_dict()
        if self.billing_provider:
            data["billing_provider"] = self.billing_provider.to_dict()
        if self.subscriber:
            data["subscriber"] = self.subscriber.to_dict()
        if self.patient:
            data["patient"] = self.patient.to_dict()
        if self.claim:
            data["claim"] = self.claim.to_dict()
        if self.diagnoses:
            data["diagnoses"] = [dx.to_dict() for dx in self.diagnoses]
        if self.service_lines:
            data["service_lines"] = [svc.to_dict() for svc in self.service_lines]
        if self.rendering_provider:
            data["rendering_provider"] = self.rendering_provider.to_dict()
            
        return data