import json
from .schema import EdiSchema
from .ast import (
    EdiRoot,
    Interchange,
    FunctionalGroup,
    Transaction,
    FinancialInformation,
    Payer,
    Payee,
    Claim,
    Adjustment,
    Service,
)

def _format_yymmdd(date: str) -> str:
    """Formats YYMMDD to YYYY-MM-DD."""
    if len(date) == 6:
        return f"20{date[0:2]}-{date[2:4]}-{date[4:6]}"
    return date

def _format_ccyymmdd(date: str) -> str:
    """Formats CCYYMMDD to YYYY-MM-DD."""
    if len(date) == 8:
        return f"{date[0:4]}-{date[4:6]}-{date[6:8]}"
    return date

def _format_time(time: str) -> str:
    """Formats HHMM to HH:MM."""
    if len(time) == 4:
        return f"{time[0:2]}:{time[2:4]}"
    return time

class EdiParser:
    def __init__(self, edi_string: str, schema_path: str):
        self.edi_string = edi_string
        with open(schema_path, 'r') as f:
            self.schema = EdiSchema.model_validate(json.load(f))
        self.segment_delimiter = self.schema.schema_definition.delimiters.segment
        self.element_delimiter = self.schema.schema_definition.delimiters.element

    def parse(self) -> EdiRoot:
        root = EdiRoot()
        edi_content = self.edi_string.replace('\n', '').replace('\r', '').strip()
        segments = edi_content.split(self.segment_delimiter)
        segments = [s for s in segments if s]

        interchange: Interchange = None
        functional_group: FunctionalGroup = None
        transaction: Transaction = None
        claim: Claim = None

        for segment_str in segments:
            parts = segment_str.split(self.element_delimiter)
            segment_id = parts[0]
            elements = parts[1:]

            if segment_id == "ISA":
                interchange = Interchange(
                    sender_id=elements[5].strip(),
                    receiver_id=elements[7].strip(),
                    date=_format_yymmdd(elements[8]),
                    time=_format_time(elements[9]),
                    control_number=elements[12],
                )
                root.interchanges.append(interchange)
            elif segment_id == "GS":
                functional_group = FunctionalGroup(
                    functional_group_code=elements[0],
                    sender_id=elements[1],
                    receiver_id=elements[2],
                    date=_format_ccyymmdd(elements[3]),
                    time=_format_time(elements[4]),
                    control_number=elements[5],
                )
                if interchange:
                    interchange.functional_groups.append(functional_group)
            elif segment_id == "ST":
                transaction = Transaction(
                    transaction_set_code=elements[0],
                    control_number=elements[1],
                )
                if functional_group:
                    functional_group.transactions.append(transaction)
            elif segment_id == "BPR":
                if transaction:
                    transaction.financial_information = FinancialInformation(
                        total_paid=int(float(elements[1])),
                        payment_method=elements[3],
                        payment_date=_format_ccyymmdd(elements[4]),
                    )
            elif segment_id == "TRN":
                if transaction:
                    transaction.reference_numbers.append(
                        {"type": "trace_number", "value": elements[1]}
                    )
            elif segment_id == "DTM":
                if transaction:
                    if len(elements) > 1:
                        if elements[0] == "405":
                            transaction.dates.append(
                                {"type": "production_date", "date": _format_ccyymmdd(elements[1])}
                            )
                        elif elements[0] == "484" and claim:
                            claim.services[-1].service_date = _format_ccyymmdd(elements[1])

            elif segment_id == "N1":
                if transaction:
                    if elements[0] == "PR":
                        transaction.payer = Payer(name=elements[1])
                    elif elements[0] == "PE":
                        transaction.payee = Payee(name=elements[1], npi=elements[3])
            elif segment_id == "CLP":
                if transaction:
                    claim = Claim(
                        claim_id=elements[0],
                        status_code=int(elements[1]),
                        total_charge=float(elements[2]),
                        total_paid=float(elements[3]),
                        patient_responsibility=float(elements[4]),
                        payer_control_number=elements[6],
                    )
                    transaction.claims.append(claim)
            elif segment_id == "CAS":
                if claim:
                    adjustment = Adjustment(
                        group_code=elements[0],
                        reason_code=elements[1],
                        amount=float(elements[2]),
                        quantity=int(elements[3]),
                    )
                    claim.adjustments.append(adjustment)
            elif segment_id == "SVC":
                if claim:
                    service = Service(
                        service_code=elements[0],
                        charge_amount=float(elements[1]),
                        paid_amount=float(elements[2]),
                        revenue_code=elements[3],
                        service_date="",
                    )
                    claim.services.append(service)

        return root