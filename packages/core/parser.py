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
from .parser_837p import Parser837P
from .ast_837p import Transaction837P
from .parser_270 import Parser270
from .ast_270 import Transaction270, Transaction271

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

        # Convert string segments to lists for easier processing
        segment_lists = []
        for segment_str in segments:
            parts = segment_str.split(self.element_delimiter)
            segment_lists.append(parts)

        # Detect transaction type and route to appropriate parser
        transaction_type = self._detect_transaction_type(segment_lists)
        
        if transaction_type == "837":
            return self._parse_837p(segment_lists)
        elif transaction_type == "270" or transaction_type == "271":
            return self._parse_270_271(segment_lists)
        else:
            # Default to 835 parsing
            return self._parse_835(segment_lists)
    
    def _detect_transaction_type(self, segments: list) -> str:
        """Detect the transaction type from ST segment."""
        for segment in segments:
            if segment[0] == "ST" and len(segment) > 1:
                transaction_code = segment[1]
                if transaction_code == "837":
                    return "837"
                elif transaction_code == "835":
                    return "835"
                elif transaction_code == "270":
                    return "270"
                elif transaction_code == "271":
                    return "271"
        return "835"  # Default to 835
    
    def _parse_837p(self, segments: list) -> EdiRoot:
        """Parse 837P Professional Claims transaction."""
        root = EdiRoot()
        
        # Create a basic interchange structure
        interchange = Interchange(
            sender_id="",
            receiver_id="", 
            date="",
            time="",
            control_number=""
        )
        
        # Parse ISA segment for interchange info
        isa_segment = next((s for s in segments if s[0] == "ISA"), None)
        if isa_segment and len(isa_segment) > 12:
            interchange.sender_id = isa_segment[6].strip()
            interchange.receiver_id = isa_segment[8].strip()
            interchange.date = _format_yymmdd(isa_segment[9])
            interchange.time = _format_time(isa_segment[10])
            interchange.control_number = isa_segment[13]
        
        # Create functional group
        functional_group = FunctionalGroup(
            functional_group_code="",
            sender_id="",
            receiver_id="",
            date="",
            time="",
            control_number=""
        )
        
        # Parse GS segment for functional group info
        gs_segment = next((s for s in segments if s[0] == "GS"), None)
        if gs_segment and len(gs_segment) > 5:
            functional_group.functional_group_code = gs_segment[1]
            functional_group.sender_id = gs_segment[2]
            functional_group.receiver_id = gs_segment[3]
            functional_group.date = _format_ccyymmdd(gs_segment[4])
            functional_group.time = _format_time(gs_segment[5])
            functional_group.control_number = gs_segment[6]
        
        # Parse 837P specific content
        parser_837p = Parser837P(segments)
        transaction_837p = parser_837p.parse()
        
        # Create a generic transaction wrapper for the 837P data
        transaction = Transaction(
            transaction_set_code="837",
            control_number=transaction_837p.header.get("transaction_set_control_number", "")
        )
        
        # Store the 837P transaction in the generic transaction
        transaction.healthcare_transaction = transaction_837p
        
        functional_group.transactions.append(transaction)
        interchange.functional_groups.append(functional_group)
        root.interchanges.append(interchange)
        
        return root
    
    def _parse_270_271(self, segments: list) -> EdiRoot:
        """Parse 270/271 Eligibility Inquiry/Response transaction."""
        root = EdiRoot()
        
        # Create a basic interchange structure
        interchange = Interchange(
            sender_id="",
            receiver_id="", 
            date="",
            time="",
            control_number=""
        )
        
        # Parse ISA segment for interchange info
        isa_segment = next((s for s in segments if s[0] == "ISA"), None)
        if isa_segment and len(isa_segment) > 12:
            interchange.sender_id = isa_segment[6].strip()
            interchange.receiver_id = isa_segment[8].strip()
            interchange.date = _format_yymmdd(isa_segment[9])
            interchange.time = _format_time(isa_segment[10])
            interchange.control_number = isa_segment[13]
        
        # Create functional group
        functional_group = FunctionalGroup(
            functional_group_code="",
            sender_id="",
            receiver_id="",
            date="",
            time="",
            control_number=""
        )
        
        # Parse GS segment for functional group info
        gs_segment = next((s for s in segments if s[0] == "GS"), None)
        if gs_segment and len(gs_segment) > 5:
            functional_group.functional_group_code = gs_segment[1]
            functional_group.sender_id = gs_segment[2]
            functional_group.receiver_id = gs_segment[3]
            functional_group.date = _format_ccyymmdd(gs_segment[4])
            functional_group.time = _format_time(gs_segment[5])
            functional_group.control_number = gs_segment[6]
        
        # Parse 270/271 specific content
        parser_270 = Parser270(segments)
        healthcare_transaction = parser_270.parse()
        
        # Determine transaction set code
        transaction_code = "270"
        st_segment = next((s for s in segments if s[0] == "ST"), None)
        if st_segment and len(st_segment) > 1:
            transaction_code = st_segment[1]
        
        # Create a generic transaction wrapper for the 270/271 data
        transaction = Transaction(
            transaction_set_code=transaction_code,
            control_number=healthcare_transaction.header.get("transaction_set_control_number", "")
        )
        
        # Store the 270/271 transaction in the generic transaction
        transaction.healthcare_transaction = healthcare_transaction
        
        functional_group.transactions.append(transaction)
        interchange.functional_groups.append(functional_group)
        root.interchanges.append(interchange)
        
        return root
    
    def _parse_835(self, segments: list) -> EdiRoot:
        """Parse 835 ERA transaction (original logic)."""
        root = EdiRoot()

        interchange: Interchange = None
        functional_group: FunctionalGroup = None
        transaction: Transaction = None
        claim: Claim = None

        for segment in segments:
            segment_id = segment[0]
            elements = segment[1:]

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