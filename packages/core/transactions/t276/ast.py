"""
EDI 276/277 (Claim Status Inquiry/Response) AST Definitions

This module defines the Abstract Syntax Tree nodes for EDI 276/277
Claim Status Inquiry and Response transactions.
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from ...base.edi_ast import Node


@dataclass
class InformationSourceInfo276(Node):
    """Information about the information source (payer)."""
    name: str
    entity_identifier_code: str = "PR"  # Payer
    id_code_qualifier: str = "PI"       # Payor Identification
    id_code: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "entity_identifier_code": self.entity_identifier_code,
            "id_code_qualifier": self.id_code_qualifier,
            "id_code": self.id_code
        }


@dataclass
class InformationReceiverInfo276(Node):
    """Information about the information receiver (provider)."""
    name: str
    entity_identifier_code: str = "1P"  # Provider
    id_code_qualifier: str = "XX"       # NPI
    npi: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "entity_identifier_code": self.entity_identifier_code,  
            "id_code_qualifier": self.id_code_qualifier,
            "npi": self.npi
        }


@dataclass
class ProviderInfo276(Node):
    """Information about the provider submitting the inquiry."""
    name: str
    entity_identifier_code: str = "85"  # Billing Provider
    id_code_qualifier: str = "XX"       # NPI
    npi: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "entity_identifier_code": self.entity_identifier_code,
            "id_code_qualifier": self.id_code_qualifier,
            "npi": self.npi
        }


@dataclass
class SubscriberInfo276(Node):
    """Information about the subscriber for claim status inquiry."""
    member_id: str
    first_name: str
    last_name: str
    middle_name: Optional[str] = None
    name_suffix: Optional[str] = None
    id_code_qualifier: str = "MI"       # Member ID
    gender: Optional[str] = None        # M=Male, F=Female, U=Unknown
    date_of_birth: Optional[str] = None # CCYYMMDD format
    
    def to_dict(self) -> Dict[str, Any]:
        data = {
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
            
        return data


@dataclass
class PatientInfo276(Node):
    """Information about the patient (if different from subscriber)."""
    first_name: str
    last_name: str
    middle_name: Optional[str] = None
    name_suffix: Optional[str] = None
    relationship_code: str = "18"       # 18=Self, 01=Spouse, 19=Child
    gender: Optional[str] = None
    date_of_birth: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        data = {
            "first_name": self.first_name,
            "last_name": self.last_name,
            "relationship_code": self.relationship_code
        }
        
        if self.middle_name:
            data["middle_name"] = self.middle_name
        if self.name_suffix:
            data["name_suffix"] = self.name_suffix
        if self.gender:
            data["gender"] = self.gender
        if self.date_of_birth:
            data["date_of_birth"] = self.date_of_birth
            
        return data


@dataclass
class ClaimStatusInquiry(Node):
    """Claim status inquiry information."""
    claim_control_number: str           # Provider's claim control number
    total_claim_charge: Optional[float] = None
    date_of_service_from: Optional[str] = None  # CCYYMMDD format
    date_of_service_to: Optional[str] = None    # CCYYMMDD format
    place_of_service_code: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        data = {"claim_control_number": self.claim_control_number}
        
        if self.total_claim_charge is not None:
            data["total_claim_charge"] = self.total_claim_charge
        if self.date_of_service_from:
            data["date_of_service_from"] = self.date_of_service_from
        if self.date_of_service_to:
            data["date_of_service_to"] = self.date_of_service_to
        if self.place_of_service_code:
            data["place_of_service_code"] = self.place_of_service_code
            
        return data


@dataclass
class ClaimStatusInfo(Node):
    """Claim status information (STC segment) - for 277 responses."""
    entity_identifier_code: str         # 1=Provider, 2=Payer, etc.
    status_code: str                    # A1=Pended, A2=Processed, etc.
    status_category_code: str           # P1=Input Errors, P2=Adjudication
    date_time_period: Optional[str] = None
    action_code: Optional[str] = None
    monetary_amount: Optional[float] = None
    
    def to_dict(self) -> Dict[str, Any]:
        data = {
            "entity_identifier_code": self.entity_identifier_code,
            "status_code": self.status_code,
            "status_category_code": self.status_category_code
        }
        
        if self.date_time_period:
            data["date_time_period"] = self.date_time_period
        if self.action_code:
            data["action_code"] = self.action_code
        if self.monetary_amount is not None:
            data["monetary_amount"] = self.monetary_amount
            
        return data


@dataclass
class ServiceLineStatusInfo(Node):
    """Service line status information."""
    line_item_control_number: str
    status_code: str
    status_category_code: str
    entity_identifier_code: str = "1"   # Provider
    monetary_amount: Optional[float] = None
    date_time_period: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        data = {
            "line_item_control_number": self.line_item_control_number,
            "status_code": self.status_code,
            "status_category_code": self.status_category_code,
            "entity_identifier_code": self.entity_identifier_code
        }
        
        if self.monetary_amount is not None:
            data["monetary_amount"] = self.monetary_amount
        if self.date_time_period:
            data["date_time_period"] = self.date_time_period
            
        return data


@dataclass
class StatusMessage(Node):
    """Status message information (MSG segment)."""
    message_text: str
    
    def to_dict(self) -> Dict[str, Any]:
        return {"message_text": self.message_text}


@dataclass
class Transaction276(Node):
    """276 Claim Status Inquiry Transaction."""
    header: Dict[str, str]
    information_source: Optional[InformationSourceInfo276] = None
    information_receiver: Optional[InformationReceiverInfo276] = None
    provider: Optional[ProviderInfo276] = None
    subscriber: Optional[SubscriberInfo276] = None
    patient: Optional[PatientInfo276] = None
    claim_inquiries: List[ClaimStatusInquiry] = None
    
    def __post_init__(self):
        if self.claim_inquiries is None:
            self.claim_inquiries = []
    
    def to_dict(self) -> Dict[str, Any]:
        data = {"header": self.header}
        
        if self.information_source:
            data["information_source"] = self.information_source.to_dict()
        if self.information_receiver:
            data["information_receiver"] = self.information_receiver.to_dict()
        if self.provider:
            data["provider"] = self.provider.to_dict()
        if self.subscriber:
            data["subscriber"] = self.subscriber.to_dict()
        if self.patient:
            data["patient"] = self.patient.to_dict()
        if self.claim_inquiries:
            data["claim_inquiries"] = [inquiry.to_dict() for inquiry in self.claim_inquiries]
            
        return data


@dataclass
class Transaction277(Node):
    """277 Claim Status Response Transaction."""
    header: Dict[str, str]
    information_source: Optional[InformationSourceInfo276] = None
    information_receiver: Optional[InformationReceiverInfo276] = None
    provider: Optional[ProviderInfo276] = None
    subscriber: Optional[SubscriberInfo276] = None
    patient: Optional[PatientInfo276] = None
    claim_status_info: List[ClaimStatusInfo] = None
    service_line_status: List[ServiceLineStatusInfo] = None
    messages: List[StatusMessage] = None
    
    def __post_init__(self):
        if self.claim_status_info is None:
            self.claim_status_info = []
        if self.service_line_status is None:
            self.service_line_status = []
        if self.messages is None:
            self.messages = []
    
    def to_dict(self) -> Dict[str, Any]:
        data = {"header": self.header}
        
        if self.information_source:
            data["information_source"] = self.information_source.to_dict()
        if self.information_receiver:
            data["information_receiver"] = self.information_receiver.to_dict()
        if self.provider:
            data["provider"] = self.provider.to_dict()
        if self.subscriber:
            data["subscriber"] = self.subscriber.to_dict()
        if self.patient:
            data["patient"] = self.patient.to_dict()
        if self.claim_status_info:
            data["claim_status_info"] = [status.to_dict() for status in self.claim_status_info]
        if self.service_line_status:
            data["service_line_status"] = [svc.to_dict() for svc in self.service_line_status]
        if self.messages:
            data["messages"] = [msg.to_dict() for msg in self.messages]
            
        return data