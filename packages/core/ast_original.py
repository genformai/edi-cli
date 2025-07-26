from typing import List, Dict, Any, Optional

class Node:
    def to_dict(self) -> Dict[str, Any]:
        raise NotImplementedError

class EdiRoot(Node):
    def __init__(self):
        self.interchanges: List[Interchange] = []

    def to_dict(self) -> Dict[str, Any]:
        return {"interchanges": [interchange.to_dict() for interchange in self.interchanges]}

class Interchange(Node):
    def __init__(self, sender_id: str, receiver_id: str, date: str, time: str, control_number: str):
        self.header = {
            "sender_id": sender_id,
            "receiver_id": receiver_id,
            "date": date,
            "time": time,
            "control_number": control_number,
        }
        self.functional_groups: List[FunctionalGroup] = []

    def to_dict(self) -> Dict[str, Any]:
        return {
            "header": self.header,
            "functional_groups": [group.to_dict() for group in self.functional_groups],
        }

class FunctionalGroup(Node):
    def __init__(self, functional_group_code: str, sender_id: str, receiver_id: str, date: str, time: str, control_number: str):
        self.header = {
            "functional_group_code": functional_group_code,
            "sender_id": sender_id,
            "receiver_id": receiver_id,
            "date": date,
            "time": time,
            "control_number": control_number,
        }
        self.transactions: List[Transaction] = []

    def to_dict(self) -> Dict[str, Any]:
        return {
            "header": self.header,
            "transactions": [transaction.to_dict() for transaction in self.transactions],
        }

class Transaction(Node):
    def __init__(self, transaction_set_code: str, control_number: str):
        self.header = {
            "transaction_set_code": transaction_set_code,
            "control_number": control_number,
        }
        self.financial_information: Optional[FinancialInformation] = None
        self.reference_numbers: List[Dict[str, str]] = []
        self.dates: List[Dict[str, str]] = []
        self.payer: Optional[Payer] = None
        self.payee: Optional[Payee] = None
        self.claims: List[Claim] = []
        self.healthcare_transaction: Optional[Any] = None  # For 837P, 270/271, etc.

    def to_dict(self) -> Dict[str, Any]:
        data = {"header": self.header}
        if self.financial_information:
            data["financial_information"] = self.financial_information.to_dict()
        if self.reference_numbers:
            data["reference_numbers"] = self.reference_numbers
        if self.dates:
            data["dates"] = self.dates
        if self.payer:
            data["payer"] = self.payer.to_dict()
        if self.payee:
            data["payee"] = self.payee.to_dict()
        if self.claims:
            data["claims"] = [claim.to_dict() for claim in self.claims]
        if self.healthcare_transaction:
            data["healthcare_transaction"] = self.healthcare_transaction.to_dict()
        return data

class FinancialInformation(Node):
    def __init__(self, total_paid: int, payment_method: str, payment_date: str):
        self.total_paid = total_paid
        self.payment_method = payment_method
        self.payment_date = payment_date

    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_paid": self.total_paid,
            "payment_method": self.payment_method,
            "payment_date": self.payment_date,
        }

class Payer(Node):
    def __init__(self, name: str):
        self.name = name

    def to_dict(self) -> Dict[str, Any]:
        return {"name": self.name}

class Payee(Node):
    def __init__(self, name: str, npi: str):
        self.name = name
        self.npi = npi

    def to_dict(self) -> Dict[str, Any]:
        return {"name": self.name, "npi": self.npi}

class Claim(Node):
    def __init__(self, claim_id: str, status_code: int, total_charge: float, total_paid: float, patient_responsibility: float, payer_control_number: str):
        self.claim_id = claim_id
        self.status_code = status_code
        self.total_charge = total_charge
        self.total_paid = total_paid
        self.patient_responsibility = patient_responsibility
        self.payer_control_number = payer_control_number
        self.adjustments: List[Adjustment] = []
        self.services: List[Service] = []

    def to_dict(self) -> Dict[str, Any]:
        return {
            "claim_id": self.claim_id,
            "status_code": self.status_code,
            "total_charge": self.total_charge,
            "total_paid": self.total_paid,
            "patient_responsibility": self.patient_responsibility,
            "payer_control_number": self.payer_control_number,
            "adjustments": [adj.to_dict() for adj in self.adjustments],
            "services": [svc.to_dict() for svc in self.services],
        }

class Adjustment(Node):
    def __init__(self, group_code: str, reason_code: str, amount: float, quantity: int):
        self.group_code = group_code
        self.reason_code = reason_code
        self.amount = amount
        self.quantity = quantity

    def to_dict(self) -> Dict[str, Any]:
        return {
            "group_code": self.group_code,
            "reason_code": self.reason_code,
            "amount": self.amount,
            "quantity": self.quantity,
        }

class Service(Node):
    def __init__(self, service_code: str, charge_amount: float, paid_amount: float, revenue_code: str, service_date: str):
        self.service_code = service_code
        self.charge_amount = charge_amount
        self.paid_amount = paid_amount
        self.revenue_code = revenue_code
        self.service_date = service_date

    def to_dict(self) -> Dict[str, Any]:
        return {
            "service_code": self.service_code,
            "charge_amount": self.charge_amount,
            "paid_amount": self.paid_amount,
            "revenue_code": self.revenue_code,
            "service_date": self.service_date,
        }