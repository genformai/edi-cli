"""
Generic EDI AST Definitions

This module defines the generic Abstract Syntax Tree nodes for EDI documents,
independent of specific transaction types.
"""

from typing import List, Dict, Any, Optional


class Node:
    """Base class for all AST nodes."""
    def to_dict(self) -> Dict[str, Any]:
        raise NotImplementedError


class EdiRoot(Node):
    """Root node representing the complete EDI document."""
    def __init__(self):
        self.interchanges: List[Interchange] = []

    def to_dict(self) -> Dict[str, Any]:
        return {"interchanges": [interchange.to_dict() for interchange in self.interchanges]}


class Interchange(Node):
    """EDI Interchange (ISA/IEA envelope)."""
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
    """EDI Functional Group (GS/GE envelope)."""
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
    """Generic EDI Transaction (ST/SE envelope)."""
    def __init__(self, transaction_set_code: str, control_number: str):
        self.header = {
            "transaction_set_code": transaction_set_code,
            "control_number": control_number,
        }
        # Generic container for specific transaction data
        self.healthcare_transaction: Optional[Any] = None  # For 837P, 270/271, 276/277
        self.financial_transaction: Optional[Any] = None   # For 835 ERA
        self.logistics_transaction: Optional[Any] = None   # For future 850, 856, etc.

    def to_dict(self) -> Dict[str, Any]:
        data = {"header": self.header}
        
        if self.healthcare_transaction:
            data["healthcare_transaction"] = self.healthcare_transaction.to_dict()
        if self.financial_transaction:
            # For backward compatibility, flatten 835 fields directly into transaction
            financial_data = self.financial_transaction.to_dict()
            # Remove the nested header since it's redundant
            if "header" in financial_data:
                del financial_data["header"]
            data.update(financial_data)
        if self.logistics_transaction:
            data["logistics_transaction"] = self.logistics_transaction.to_dict()
            
        return data