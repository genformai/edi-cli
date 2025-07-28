"""
EDI 270/271 (Eligibility Inquiry/Response) AST Definitions

This module defines the Abstract Syntax Tree nodes for EDI 270/271
Eligibility Inquiry and Response transactions.
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from ...base.edi_ast import Node


@dataclass
class InformationSourceInfo(Node):
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
class InformationReceiverInfo(Node):
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
class SubscriberEligibilityInfo(Node):
    """Information about the subscriber for eligibility inquiry."""
    member_id: str
    first_name: str
    last_name: str
    middle_name: Optional[str] = None
    name_suffix: Optional[str] = None
    id_code_qualifier: str = "MI"       # Member ID
    gender: Optional[str] = None        # M=Male, F=Female, U=Unknown
    date_of_birth: Optional[str] = None # CCYYMMDD format
    relationship_code: str = "18"       # 18=Self
    
    def to_dict(self) -> Dict[str, Any]:
        data = {
            "member_id": self.member_id,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "id_code_qualifier": self.id_code_qualifier,
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
class DependentEligibilityInfo(Node):
    """Information about a dependent for eligibility inquiry."""
    first_name: str
    last_name: str
    middle_name: Optional[str] = None
    name_suffix: Optional[str] = None
    relationship_code: str = "01"       # 01=Spouse, 19=Child, etc.
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
class EligibilityInquiry(Node):
    """Eligibility inquiry information (EQ segment)."""
    service_type_code: str              # 30=Health Benefit Plan Coverage, etc.
    coverage_level_code: Optional[str] = None  # IND=Individual, FAM=Family
    insurance_type_code: Optional[str] = None  # HLT=Health, DEN=Dental, etc.
    
    def to_dict(self) -> Dict[str, Any]:
        data = {"service_type_code": self.service_type_code}
        
        if self.coverage_level_code:
            data["coverage_level_code"] = self.coverage_level_code
        if self.insurance_type_code:
            data["insurance_type_code"] = self.insurance_type_code
            
        return data


@dataclass
class EligibilityBenefit(Node):
    """Eligibility benefit information (EB segment) - for 271 responses."""
    eligibility_code: str               # Y=Yes, N=No, U=Unknown
    coverage_level_code: str            # IND=Individual, FAM=Family
    service_type_code: str              # 30=Health Benefit Plan Coverage
    insurance_type_code: Optional[str] = None
    plan_coverage_description: Optional[str] = None
    time_period_qualifier: Optional[str] = None
    monetary_amount: Optional[float] = None
    percentage: Optional[float] = None
    quantity_qualifier: Optional[str] = None
    quantity: Optional[float] = None
    authorization_required: Optional[str] = None  # Y=Yes, N=No
    in_plan_network: Optional[str] = None         # Y=Yes, N=No
    
    def to_dict(self) -> Dict[str, Any]:
        data = {
            "eligibility_code": self.eligibility_code,
            "coverage_level_code": self.coverage_level_code,
            "service_type_code": self.service_type_code
        }
        
        if self.insurance_type_code:
            data["insurance_type_code"] = self.insurance_type_code
        if self.plan_coverage_description:
            data["plan_coverage_description"] = self.plan_coverage_description
        if self.time_period_qualifier:
            data["time_period_qualifier"] = self.time_period_qualifier
        if self.monetary_amount is not None:
            data["monetary_amount"] = self.monetary_amount
        if self.percentage is not None:
            data["percentage"] = self.percentage
        if self.quantity_qualifier:
            data["quantity_qualifier"] = self.quantity_qualifier
        if self.quantity is not None:
            data["quantity"] = self.quantity
        if self.authorization_required:
            data["authorization_required"] = self.authorization_required
        if self.in_plan_network:
            data["in_plan_network"] = self.in_plan_network
            
        return data


@dataclass
class EligibilityMessage(Node):
    """Eligibility message information (MSG segment)."""
    message_text: str
    
    def to_dict(self) -> Dict[str, Any]:
        return {"message_text": self.message_text}


@dataclass
class Transaction270(Node):
    """270 Eligibility Inquiry Transaction."""
    header: Dict[str, str]
    information_source: Optional[InformationSourceInfo] = None
    information_receiver: Optional[InformationReceiverInfo] = None
    subscriber: Optional[SubscriberEligibilityInfo] = None
    dependent: Optional[DependentEligibilityInfo] = None
    eligibility_inquiries: List[EligibilityInquiry] = None
    
    def __post_init__(self):
        if self.eligibility_inquiries is None:
            self.eligibility_inquiries = []
    
    def to_dict(self) -> Dict[str, Any]:
        data = {"header": self.header}
        
        if self.information_source:
            data["information_source"] = self.information_source.to_dict()
        if self.information_receiver:
            data["information_receiver"] = self.information_receiver.to_dict()
        if self.subscriber:
            data["subscriber"] = self.subscriber.to_dict()
        if self.dependent:
            data["dependent"] = self.dependent.to_dict()
        if self.eligibility_inquiries:
            data["eligibility_inquiries"] = [eq.to_dict() for eq in self.eligibility_inquiries]
            
        return data


@dataclass 
class Transaction271(Node):
    """271 Eligibility Response Transaction."""
    header: Dict[str, str]
    information_source: Optional[InformationSourceInfo] = None
    information_receiver: Optional[InformationReceiverInfo] = None
    subscriber: Optional[SubscriberEligibilityInfo] = None
    dependent: Optional[DependentEligibilityInfo] = None
    eligibility_benefits: List[EligibilityBenefit] = None
    messages: List[EligibilityMessage] = None
    
    def __post_init__(self):
        if self.eligibility_benefits is None:
            self.eligibility_benefits = []
        if self.messages is None:
            self.messages = []
    
    def to_dict(self) -> Dict[str, Any]:
        data = {"header": self.header}
        
        if self.information_source:
            data["information_source"] = self.information_source.to_dict()
        if self.information_receiver:
            data["information_receiver"] = self.information_receiver.to_dict()
        if self.subscriber:
            data["subscriber"] = self.subscriber.to_dict()
        if self.dependent:
            data["dependent"] = self.dependent.to_dict()
        if self.eligibility_benefits:
            data["eligibility_benefits"] = [eb.to_dict() for eb in self.eligibility_benefits]
        if self.messages:
            data["messages"] = [msg.to_dict() for msg in self.messages]
            
        return data