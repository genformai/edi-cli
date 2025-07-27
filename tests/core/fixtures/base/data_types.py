"""
Core data types for EDI fixture generation.
"""

from dataclasses import dataclass, field
from datetime import datetime, date
from decimal import Decimal
from typing import Dict, List, Optional, Union
from enum import Enum


class PaymentMethod(Enum):
    """Payment method types."""
    ACH = "ACH"
    CHECK = "CHK" 
    WIRE = "FWT"
    NON = "NON"  # No payment/advice only


class ClaimStatus(Enum):
    """Claim processing status codes."""
    PRIMARY_PROCESSED = 1
    SECONDARY_PROCESSED = 2
    SUPPLEMENTAL_PROCESSED = 3
    DENIED = 4
    PRIMARY_FORWARDED = 19
    SECONDARY_FORWARDED = 20
    TERTIARY_FORWARDED = 21
    REVERSAL = 22
    CAPITATION = 23


class AdjustmentGroup(Enum):
    """Adjustment reason code groups."""
    CONTRACTUAL = "CO"  # Contractual Obligation
    CORRECTION = "CR"   # Correction/Change
    OTHER = "OA"        # Other Adjustment
    PATIENT_RESP = "PR" # Patient Responsibility
    PAYER_INITIATED = "PI"  # Payer Initiated Reductions


@dataclass
class Address:
    """Physical address information."""
    line1: str
    line2: Optional[str] = None
    city: str = ""
    state: str = ""
    zip_code: str = ""
    country: str = "US"
    
    def to_n3_segment(self) -> str:
        """Generate N3 address segment."""
        if self.line2:
            return f"N3*{self.line1}*{self.line2}~"
        return f"N3*{self.line1}~"
    
    def to_n4_segment(self) -> str:
        """Generate N4 city/state/zip segment."""
        parts = [self.city, self.state, self.zip_code]
        if self.country != "US":
            parts.append(self.country)
        return f"N4*{'*'.join(filter(None, parts))}~"


@dataclass 
class ContactInfo:
    """Contact information."""
    name: str
    phone: Optional[str] = None
    email: Optional[str] = None
    fax: Optional[str] = None
    
    def to_per_segment(self, qualifier: str = "IC") -> str:
        """Generate PER contact segment."""
        parts = [qualifier, self.name]
        if self.phone:
            parts.extend(["TE", self.phone])
        if self.email:
            parts.extend(["EM", self.email])
        return f"PER*{'*'.join(parts)}~"


@dataclass
class EDIEnvelope:
    """EDI envelope structure (ISA/GS/ST wrapper)."""
    sender_id: str = "SENDER"
    receiver_id: str = "RECEIVER"
    sender_qualifier: str = "ZZ" 
    receiver_qualifier: str = "ZZ"
    
    # Control numbers
    interchange_control: str = "000012345"
    group_control: str = "000006789" 
    transaction_control: str = "0001"
    
    # Functional group info
    functional_id: str = "HP"  # Health Care Payment
    version: str = "005010X221A1"
    
    # Dates and times
    interchange_date: Optional[date] = None
    interchange_time: Optional[str] = None
    production_date: Optional[date] = None
    production_time: Optional[str] = None
    
    # Separators
    element_separator: str = "*"
    component_separator: str = "^"
    segment_terminator: str = "~"
    
    def __post_init__(self):
        """Set default dates if not provided.""" 
        today = date.today()
        if self.interchange_date is None:
            self.interchange_date = today
        if self.production_date is None:
            self.production_date = today
        if self.interchange_time is None:
            self.interchange_time = "1430"
        if self.production_time is None:
            self.production_time = "1430"
    
    def get_isa_segment(self) -> str:
        """Generate ISA interchange header."""
        date_str = self.interchange_date.strftime("%y%m%d")
        return (
            f"ISA*00*          *00*          "
            f"*{self.sender_qualifier}*{self.sender_id:<15}"
            f"*{self.receiver_qualifier}*{self.receiver_id:<15}"
            f"*{date_str}*{self.interchange_time}"
            f"*{self.component_separator}*00501*{self.interchange_control}"
            f"*0*P*{self.segment_terminator[0]}~"
        )
    
    def get_gs_segment(self) -> str:
        """Generate GS functional group header."""
        date_str = self.production_date.strftime("%Y%m%d")
        return (
            f"GS*{self.functional_id}*{self.sender_id}*{self.receiver_id}"
            f"*{date_str}*{self.production_time}*{self.group_control}"
            f"*X*{self.version}~"
        )
    
    def get_iea_segment(self) -> str:
        """Generate IEA interchange trailer."""
        return f"IEA*1*{self.interchange_control}~"
    
    def get_ge_segment(self, transaction_count: int = 1) -> str:
        """Generate GE functional group trailer."""
        return f"GE*{transaction_count}*{self.group_control}~"


@dataclass
class EntityInfo:
    """Entity information (payer, payee, patient, etc.)."""
    name: str
    entity_type: str = "2"  # 1=Person, 2=Organization
    id_qualifier: str = ""
    id_value: str = ""
    first_name: Optional[str] = None
    middle_name: Optional[str] = None
    last_name: Optional[str] = None
    prefix: Optional[str] = None
    suffix: Optional[str] = None
    address: Optional[Address] = None
    contact: Optional[ContactInfo] = None
    
    def to_nm1_segment(self, entity_code: str) -> str:
        """Generate NM1 entity name segment."""
        if self.entity_type == "1":  # Person
            parts = [
                entity_code, self.entity_type,
                self.last_name or self.name,
                self.first_name or "",
                self.middle_name or "",
                self.prefix or "",
                self.suffix or "",
                "",  # Name suffix
                self.id_qualifier,
                self.id_value
            ]
        else:  # Organization
            parts = [
                entity_code, self.entity_type, self.name,
                "", "", "", "", "",  # Name parts for person
                self.id_qualifier, self.id_value
            ]
        
        return f"NM1*{'*'.join(str(p) for p in parts)}~"


@dataclass
class ClaimData:
    """Claim-level information."""
    claim_id: str
    status: Union[ClaimStatus, int]
    total_charge: Decimal
    total_paid: Decimal
    patient_responsibility: Decimal
    frequency_code: str = "1" 
    provider_signature: str = "Y"
    assignment_accepted: str = "A"
    benefits_assignment: str = "Y"
    release_info: str = "I"
    claim_type: str = "MC"  # Medical Care
    payer_control_number: str = ""
    facility_code: str = "11"
    patient_control_number: Optional[str] = None
    
    def __post_init__(self):
        """Convert status enum to int if needed."""
        if isinstance(self.status, ClaimStatus):
            self.status = self.status.value
    
    def to_clp_segment(self) -> str:
        """Generate CLP claim payment information segment."""
        parts = [
            self.claim_id,
            str(self.status), 
            str(self.total_charge),
            str(self.total_paid),
            str(self.patient_responsibility),
            self.claim_type,
            self.payer_control_number,
            self.facility_code
        ]
        
        if self.patient_control_number:
            parts.append(self.patient_control_number)
            
        return f"CLP*{'*'.join(parts)}~"


@dataclass
class AdjustmentData:
    """Claim adjustment information."""
    group_code: Union[AdjustmentGroup, str]
    reason_code: str
    amount: Decimal
    quantity: Optional[Decimal] = None
    
    def __post_init__(self):
        """Convert group enum to string if needed."""
        if isinstance(self.group_code, AdjustmentGroup):
            self.group_code = self.group_code.value
    
    def to_cas_segment(self) -> str:
        """Generate CAS claim adjustment segment."""
        parts = [self.group_code, self.reason_code, str(self.amount)]
        if self.quantity is not None:
            parts.append(str(self.quantity))
        return f"CAS*{'*'.join(parts)}~"


@dataclass
class ServiceData:
    """Service line information."""
    procedure_code: str
    charge: Decimal
    paid: Decimal
    units: Decimal = Decimal("1")
    qualifier: str = "HC"  # HCPCS
    unit_type: str = "UN"  # Units
    
    def to_svc_segment(self) -> str:
        """Generate SVC service payment information segment."""
        return (
            f"SVC*{self.qualifier}:{self.procedure_code}"
            f"*{self.charge}*{self.paid}*{self.unit_type}*{self.units}~"
        )


@dataclass
class PaymentInfo:
    """Payment/remittance information."""
    transaction_type: str = "I"  # I=Payment, H=Advice only, D=Debit
    amount: Decimal = Decimal("0")
    credit_debit: str = "C"  # C=Credit, D=Debit
    payment_method: Union[PaymentMethod, str] = PaymentMethod.ACH
    payment_format: str = "CCP"  # Cash Concentration/Disbursement
    dfi_qualifier: str = "01"
    dfi_number: str = "123456789"
    account_qualifier: str = "DA"
    account_number: str = "987654321"
    originating_company_id: str = "9876543210"
    payment_date: Optional[date] = None
    
    def __post_init__(self):
        """Convert payment method enum to string if needed."""
        if isinstance(self.payment_method, PaymentMethod):
            self.payment_method = self.payment_method.value
        if self.payment_date is None:
            self.payment_date = date.today()
    
    def to_bpr_segment(self) -> str:
        """Generate BPR beginning segment for payment order/remittance."""
        date_str = self.payment_date.strftime("%Y%m%d")
        
        if self.payment_method == "NON":
            # No payment - advice only
            return f"BPR*H*{self.amount}*{self.credit_debit}*NON~"
        
        return (
            f"BPR*{self.transaction_type}*{self.amount}*{self.credit_debit}"
            f"*{self.payment_method}*{self.payment_format}*{self.dfi_qualifier}"
            f"*{self.dfi_number}*{self.account_qualifier}*{self.account_number}"
            f"*{self.originating_company_id}*{date_str}~"
        )