"""
Generic EDI AST Definitions - Unified Transaction Design

This module defines a simplified, unified Abstract Syntax Tree for EDI documents.
The new design uses a single transaction_data field instead of multiple type-specific
containers, making it more extensible and maintainable.

Key changes:
- Removed healthcare_transaction, financial_transaction, logistics_transaction fields
- Added single transaction_data field to hold any transaction-specific AST
- Maintains backward compatibility for 835 transactions through special handling
- Supports arbitrary transaction types without code changes to the base Transaction class
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
    def __init__(self, transaction_set_code: str, control_number: str, transaction_data: Any = None):
        self.header = {
            "transaction_set_code": transaction_set_code,
            "control_number": control_number,
        }
        # Single unified container for transaction-specific data
        self.transaction_data: Optional[Any] = transaction_data

    def to_dict(self) -> Dict[str, Any]:
        data = {"header": self.header}
        
        if self.transaction_data:
            # Handle backward compatibility for different transaction types
            transaction_dict = self.transaction_data.to_dict()
            
            # For 835 transactions, maintain backward compatibility by flattening
            if hasattr(self.transaction_data, '__class__') and self.transaction_data.__class__.__name__ == 'Transaction835':
                # Remove nested header to avoid duplication
                if "header" in transaction_dict:
                    del transaction_dict["header"]
                data.update(transaction_dict)
            else:
                # For other transaction types, store under transaction_data key
                data["transaction_data"] = transaction_dict
            
        return data