"""
EDI 835 (Healthcare Claim Payment/Advice) Parser - Refactored Version

This module provides a complete refactored parser with:
- Segment dispatcher architecture
- ParseState management
- Enhanced error handling
- Comprehensive segment support
- Proper data validation and balancing
"""

from typing import List, Optional, Dict, Callable, Any, Tuple
from enum import Enum
from dataclasses import dataclass
import logging
from ...base.parser import BaseParser
from ...base.enhanced_parser import EnhancedParser
from ...errors import ErrorHandler, EDISegmentError, create_parse_context
from ...base.edi_ast import EdiRoot, Interchange, FunctionalGroup, Transaction
from .ast import (
    Transaction835,
    FinancialInformation,
    Payer,
    Payee,
    Claim,
    Adjustment,
    Service,
)

logger = logging.getLogger(__name__)


# Constants and Enums
class EntityCode(Enum):
    """Entity identifier codes for N1 segments."""
    PAYER = "PR"
    PAYEE = "PE"
    PATIENT = "QC"
    PROVIDER = "82"
    BILLING_PROVIDER = "85"


class DTMQualifier(Enum):
    """Date/time qualifiers for DTM segments."""
    PRODUCTION_DATE = "405"
    SERVICE_DATE = "472"
    CLAIM_RECEIVED_DATE = "050"
    CHECK_DATE = "009"
    COVERAGE_EXPIRATION = "036"


class CASGroupCode(Enum):
    """Claim Adjustment Group Codes."""
    CONTRACTUAL = "CO"
    CORRECTION_REVERSAL = "CR"
    OTHER_ADJUSTMENTS = "OA"
    PATIENT_RESPONSIBILITY = "PR"
    PAYER_INITIATED = "PI"


class BPRPaymentMethod(Enum):
    """BPR Payment Method codes."""
    ACH = "ACH"
    CHECK = "CHK"
    WIRE = "FWT"
    NON_PAYMENT = "NON"


class RefQualifier(Enum):
    """Reference identifier qualifiers."""
    TAX_ID = "TJ"
    NPI = "HPI"
    PROVIDER_CONTROL = "1K"
    ORIGINAL_REF = "F8"


@dataclass
class ParseState:
    """Holds the current parsing state."""
    root: EdiRoot
    current_interchange: Optional[Interchange] = None
    current_functional_group: Optional[FunctionalGroup] = None
    current_transaction: Optional[Transaction] = None
    current_transaction_835: Optional[Transaction835] = None
    current_claim: Optional[Claim] = None
    segment_count: int = 0
    errors: List[EDISegmentError] = None
    
    # Dynamic delimiters
    element_separator: str = "*"
    component_separator: str = ":"
    segment_terminator: str = "~"
    
    def __post_init__(self):
        if self.errors is None:
            self.errors = []


class ParserUtilities:
    """Utility methods for parsing operations."""
    
    @staticmethod
    def parse_composite(composite_value: str, separator: str = ":") -> Dict[str, str]:
        """Parse composite field like HC:99213:25 into components."""
        if not composite_value:
            return {}
        
        parts = composite_value.split(separator)
        result = {"raw": composite_value}
        
        if len(parts) >= 1:
            result["coding_system"] = parts[0]
        if len(parts) >= 2:
            result["procedure_code"] = parts[1]
        if len(parts) >= 3:
            result["modifier1"] = parts[2]
        if len(parts) >= 4:
            result["modifier2"] = parts[3]
        if len(parts) >= 5:
            result["modifier3"] = parts[4]
        if len(parts) >= 6:
            result["modifier4"] = parts[5]
            
        return result
    
    @staticmethod
    def parse_dtm(date_qualifier: str, date_value: str) -> Dict[str, str]:
        """Parse DTM segment into semantic date information."""
        try:
            qualifier_enum = DTMQualifier(date_qualifier)
            date_type_map = {
                DTMQualifier.PRODUCTION_DATE: "production_date",
                DTMQualifier.SERVICE_DATE: "service_date",
                DTMQualifier.CLAIM_RECEIVED_DATE: "claim_received_date",
                DTMQualifier.CHECK_DATE: "check_date",
                DTMQualifier.COVERAGE_EXPIRATION: "coverage_expiration_date"
            }
            date_type = date_type_map.get(qualifier_enum, "other")
        except ValueError:
            date_type = "other"
        
        return {
            "qualifier": date_qualifier,
            "type": date_type,
            "date": date_value
        }
    
    @staticmethod
    def parse_cas_triplets(segment: List[str], start_index: int = 2) -> List[Dict[str, Any]]:
        """Parse CAS segment triplets (reason_code, amount, quantity)."""
        triplets = []
        index = start_index
        
        while index < len(segment) and index + 1 < len(segment):  # Need at least reason + amount
            reason_code = segment[index] if index < len(segment) else None
            amount_str = segment[index + 1] if index + 1 < len(segment) else None
            quantity_str = segment[index + 2] if index + 2 < len(segment) else None
            
            if not reason_code or not amount_str:
                break
                
            try:
                amount = float(amount_str)
                quantity = float(quantity_str) if quantity_str and quantity_str.strip() else None
                
                triplets.append({
                    "reason_code": reason_code,
                    "amount": amount,
                    "quantity": quantity
                })
                
                index += 3  # Move to next triplet
            except ValueError:
                break
        
        return triplets


class Parser835Refactored(BaseParser):
    """Refactored parser for EDI 835 Healthcare Claim Payment/Advice transactions."""

    def __init__(self, segments: List[List[str]] = None):
        """Initialize the parser with optional segments."""
        super().__init__(segments or [])
        self.error_handler = ErrorHandler()
        self.utilities = ParserUtilities()
        
        # Segment dispatcher map
        self.segment_handlers: Dict[str, Callable] = {
            "ISA": self._handle_isa,
            "IEA": self._handle_iea,
            "GS": self._handle_gs,
            "GE": self._handle_ge,
            "ST": self._handle_st,
            "SE": self._handle_se,
            "BPR": self._handle_bpr,
            "TRN": self._handle_trn,
            "DTM": self._handle_dtm,
            "N1": self._handle_n1,
            "NM1": self._handle_nm1,
            "PER": self._handle_per,
            "REF": self._handle_ref,
            "CLP": self._handle_clp,
            "CAS": self._handle_cas,
            "SVC": self._handle_svc,
            "SVD": self._handle_svd,
            "PLB": self._handle_plb,
            "LX": self._handle_lx,
        }

    def get_transaction_codes(self) -> List[str]:
        """Get the transaction codes this parser supports."""
        return ["835"]

    def parse(self, edi_content: str = None) -> EdiRoot:
        """
        Parse the 835 transaction from EDI segments or content.

        Args:
            edi_content: Raw EDI content string (if not using segments from constructor)

        Returns:
            EdiRoot: Parsed EDI document with 835 transaction

        Raises:
            ValueError: If unable to parse the transaction
        """
        try:
            logger.debug("Parsing 835 healthcare claim payment/advice transaction")
            
            # Handle case where edi_content is provided
            if edi_content:
                segments = self._parse_edi_content(edi_content)
            else:
                segments = self.segments
            
            # Initialize parse state
            state = ParseState(root=EdiRoot())
            
            # Extract delimiters from ISA segment if available
            if segments and segments[0] and segments[0][0] == "ISA":
                self._extract_delimiters(segments[0], state)
            
            # Process each segment
            for segment_index, segment in enumerate(segments):
                if not segment:
                    continue
                
                state.segment_count += 1
                segment_id = segment[0]
                
                try:
                    # Use dispatcher to handle segment
                    handler = self.segment_handlers.get(segment_id)
                    if handler:
                        handler(segment, state, segment_index)
                    else:
                        logger.debug(f"No handler for segment {segment_id}, skipping")
                        
                except Exception as e:
                    # Create error context and continue parsing
                    context = create_parse_context(
                        segment_index=segment_index,
                        control_number=getattr(state.current_transaction, 'header', {}).get('control_number'),
                        segment_id=segment_id
                    )
                    error = EDISegmentError(f"Error processing {segment_id} segment: {e}", context)
                    state.errors.append(error)
                    self.error_handler.add_error(error)
            
            # Perform final validation
            self._perform_balancing_checks(state)
            
            logger.debug(f"Parsed 835 transaction with {len(state.current_transaction_835.claims) if state.current_transaction_835 else 0} claims")
            return state.root
            
        except Exception as e:
            logger.error(f"Error parsing 835 transaction: {e}")
            raise ValueError(f"Failed to parse 835 transaction: {e}")

    def _extract_delimiters(self, isa_segment: List[str], state: ParseState):
        """Extract delimiters from ISA segment."""
        if len(isa_segment) >= 17:
            # ISA segment uses fixed positions for delimiters
            # Element separator is position 3 (after ISA)
            # Component separator is position 16 
            # Segment terminator follows the segment
            state.element_separator = "*"  # Standard
            if len(isa_segment[16]) > 0:
                state.component_separator = isa_segment[16][0]
            state.segment_terminator = "~"  # Standard

    def _parse_edi_content(self, edi_content: str) -> List[List[str]]:
        """Parse EDI content string into segments with dynamic delimiter detection."""
        if not edi_content:
            return []
        
        # Extract segment terminator (usually ~)
        segment_terminator = "~"
        if len(edi_content) > 100:  # Look for terminator in ISA segment
            isa_end = edi_content.find("GS")
            if isa_end > 0:
                potential_terminator = edi_content[isa_end - 1]
                if potential_terminator in ["~", "|", "!"]:
                    segment_terminator = potential_terminator
        
        # Split by segment terminator
        raw_segments = edi_content.split(segment_terminator)
        segments = []
        
        # Extract element separator from ISA segment
        element_separator = "*"
        if raw_segments and raw_segments[0].startswith("ISA"):
            # Element separator is typically the 4th character in ISA
            if len(raw_segments[0]) > 3:
                element_separator = raw_segments[0][3]
        
        for raw_segment in raw_segments:
            raw_segment = raw_segment.strip()
            if raw_segment:
                # Split by element separator
                elements = raw_segment.split(element_separator)
                segments.append(elements)
        
        return segments

    # Segment Handlers
    def _handle_isa(self, segment: List[str], state: ParseState, segment_index: int):
        """Handle ISA (Interchange Control Header) segment."""
        state.current_interchange = Interchange(
            sender_id=self._get_element(segment, 6),
            receiver_id=self._get_element(segment, 8),
            date=self._format_date_yymmdd(self._get_element(segment, 9)),
            time=self._format_time(self._get_element(segment, 10)),
            control_number=self._get_element(segment, 13),
        )
        state.root.interchanges.append(state.current_interchange)

    def _handle_iea(self, segment: List[str], state: ParseState, segment_index: int):
        """Handle IEA (Interchange Control Trailer) segment."""
        if state.current_interchange:
            expected_control = state.current_interchange.header["control_number"]
            actual_control = self._get_element(segment, 2)
            
            if expected_control != actual_control:
                error = EDISegmentError(
                    f"IEA control number mismatch: expected {expected_control}, got {actual_control}",
                    create_parse_context(segment_index, actual_control, "IEA")
                )
                state.errors.append(error)

    def _handle_gs(self, segment: List[str], state: ParseState, segment_index: int):
        """Handle GS (Functional Group Header) segment."""
        if state.current_interchange:
            state.current_functional_group = FunctionalGroup(
                functional_group_code=self._get_element(segment, 1),
                sender_id=self._get_element(segment, 2),
                receiver_id=self._get_element(segment, 3),
                date=self._format_date_ccyymmdd(self._get_element(segment, 4)),
                time=self._format_time(self._get_element(segment, 5)),
                control_number=self._get_element(segment, 6),
            )
            state.current_interchange.functional_groups.append(state.current_functional_group)

    def _handle_ge(self, segment: List[str], state: ParseState, segment_index: int):
        """Handle GE (Functional Group Trailer) segment."""
        if state.current_functional_group:
            expected_control = state.current_functional_group.header["control_number"]
            actual_control = self._get_element(segment, 2)
            
            if expected_control != actual_control:
                error = EDISegmentError(
                    f"GE control number mismatch: expected {expected_control}, got {actual_control}",
                    create_parse_context(segment_index, actual_control, "GE")
                )
                state.errors.append(error)

    def _handle_st(self, segment: List[str], state: ParseState, segment_index: int):
        """Handle ST (Transaction Set Header) segment."""
        if state.current_functional_group:
            state.current_transaction_835 = Transaction835(
                header={
                    "transaction_set_identifier": self._get_element(segment, 1),
                    "transaction_set_control_number": self._get_element(segment, 2),
                }
            )
            
            state.current_transaction = Transaction(
                transaction_set_code=self._get_element(segment, 1),
                control_number=self._get_element(segment, 2),
                transaction_data=state.current_transaction_835
            )
            state.current_functional_group.transactions.append(state.current_transaction)

    def _handle_se(self, segment: List[str], state: ParseState, segment_index: int):
        """Handle SE (Transaction Set Trailer) segment."""
        if state.current_transaction:
            expected_control = state.current_transaction.header["control_number"]
            actual_control = self._get_element(segment, 2)
            expected_count = int(self._get_element(segment, 1))
            
            # Control number validation
            if expected_control != actual_control:
                error = EDISegmentError(
                    f"SE control number mismatch: expected {expected_control}, got {actual_control}",
                    create_parse_context(segment_index, actual_control, "SE")
                )
                state.errors.append(error)
            
            # Segment count validation (would need transaction-level segment counting)
            # This is a simplified check - full implementation would track segments per transaction
            if hasattr(state.current_transaction_835, 'segment_count_mismatch'):
                if expected_count != getattr(state.current_transaction_835, 'actual_segment_count', expected_count):
                    state.current_transaction_835.segment_count_mismatch = True

    def _handle_bpr(self, segment: List[str], state: ParseState, segment_index: int):
        """Handle BPR (Beginning Segment for Payment Order/Remittance Advice) segment."""
        if state.current_transaction_835:
            total_paid = self._safe_float(self._get_element(segment, 2))
            payment_method = self._get_element(segment, 4)
            payment_date_raw = self._get_element(segment, 11)
            payment_date = self._format_date_ccyymmdd(payment_date_raw)
            
            state.current_transaction_835.financial_information = FinancialInformation(
                total_paid=total_paid,
                payment_method=payment_method,
                payment_date=payment_date
            )

    def _handle_trn(self, segment: List[str], state: ParseState, segment_index: int):
        """Handle TRN (Trace) segment."""
        if state.current_transaction_835:
            reference_value = self._get_element(segment, 2)
            if reference_value:
                state.current_transaction_835.reference_numbers.append({
                    "type": "trace_number",
                    "value": reference_value
                })

    def _handle_dtm(self, segment: List[str], state: ParseState, segment_index: int):
        """Handle DTM (Date/Time Reference) segment."""
        date_qualifier = self._get_element(segment, 1)
        date_value = self._get_element(segment, 2)
        
        if not date_value:
            return
            
        parsed_dtm = self.utilities.parse_dtm(date_qualifier, date_value)
        formatted_date = self._format_date_ccyymmdd(date_value)
        parsed_dtm["date"] = formatted_date
        
        if state.current_claim and state.current_claim.services and parsed_dtm["type"] == "service_date":
            # Service-level date
            state.current_claim.services[-1].service_date = formatted_date
        elif state.current_transaction_835:
            # Transaction-level date
            state.current_transaction_835.dates.append(parsed_dtm)

    def _handle_n1(self, segment: List[str], state: ParseState, segment_index: int):
        """Handle N1 (Name) segment."""
        if state.current_transaction_835:
            entity_code = self._get_element(segment, 1)
            name = self._get_element(segment, 2)
            
            try:
                entity_enum = EntityCode(entity_code)
                if entity_enum == EntityCode.PAYER:
                    state.current_transaction_835.payer = Payer(name=name)
                elif entity_enum == EntityCode.PAYEE:
                    state.current_transaction_835.payee = Payee(name=name, npi="", tax_id="")
            except ValueError:
                logger.debug(f"Unknown entity code: {entity_code}")

    def _handle_nm1(self, segment: List[str], state: ParseState, segment_index: int):
        """Handle NM1 (Individual or Organizational Name) segment."""
        if state.current_claim:
            entity_type = self._get_element(segment, 1)
            entity_code = self._get_element(segment, 2)
            last_name = self._get_element(segment, 3)
            first_name = self._get_element(segment, 4)
            middle_name = self._get_element(segment, 5)
            
            # Store patient/subscriber information
            if entity_type == "QC":  # Patient
                full_name = " ".join(filter(None, [first_name, middle_name, last_name]))
                if not hasattr(state.current_claim, 'patient_info'):
                    state.current_claim.patient_info = {}
                state.current_claim.patient_info['name'] = full_name

    def _handle_per(self, segment: List[str], state: ParseState, segment_index: int):
        """Handle PER (Administrative Communications Contact) segment."""
        if state.current_transaction_835:
            contact_function = self._get_element(segment, 1)
            contact_name = self._get_element(segment, 2)
            
            if not hasattr(state.current_transaction_835, 'contacts'):
                state.current_transaction_835.contacts = []
                
            state.current_transaction_835.contacts.append({
                "function": contact_function,
                "name": contact_name
            })

    def _handle_ref(self, segment: List[str], state: ParseState, segment_index: int):
        """Handle REF (Reference Information) segment."""
        reference_qualifier = self._get_element(segment, 1)
        reference_value = self._get_element(segment, 2)
        
        if not reference_value:
            return
            
        try:
            ref_enum = RefQualifier(reference_qualifier)
            
            if ref_enum == RefQualifier.TAX_ID and state.current_transaction_835 and state.current_transaction_835.payee:
                # Fix: REF*TJ is Tax ID, not NPI
                state.current_transaction_835.payee.tax_id = reference_value
            elif ref_enum == RefQualifier.NPI and state.current_transaction_835 and state.current_transaction_835.payee:
                state.current_transaction_835.payee.npi = reference_value
            elif state.current_transaction_835:
                # Generic reference
                state.current_transaction_835.reference_numbers.append({
                    "type": reference_qualifier,
                    "value": reference_value
                })
        except ValueError:
            # Unknown qualifier, store as generic reference
            if state.current_transaction_835:
                state.current_transaction_835.reference_numbers.append({
                    "type": reference_qualifier,
                    "value": reference_value
                })

    def _handle_clp(self, segment: List[str], state: ParseState, segment_index: int):
        """Handle CLP (Claim Payment Information) segment."""
        if state.current_transaction_835:
            state.current_claim = Claim(
                claim_id=self._get_element(segment, 1),
                status_code=self._get_element(segment, 2),
                total_charge=self._safe_float(self._get_element(segment, 3)),
                total_paid=self._safe_float(self._get_element(segment, 4)),
                patient_responsibility=self._safe_float(self._get_element(segment, 5)),
                payer_control_number=self._get_element(segment, 7),
            )
            state.current_transaction_835.claims.append(state.current_claim)

    def _handle_cas(self, segment: List[str], state: ParseState, segment_index: int):
        """Handle CAS (Claim Adjustment) segment with multiple triplets."""
        if not state.current_claim:
            return
            
        group_code = self._get_element(segment, 1)
        
        # Parse all triplets in the segment
        triplets = self.utilities.parse_cas_triplets(segment, start_index=2)
        
        for triplet in triplets:
            if triplet["reason_code"]:
                adjustment = Adjustment(
                    group_code=group_code,
                    reason_code=triplet["reason_code"],
                    amount=triplet["amount"],
                    quantity=triplet["quantity"],  # Can be None now
                )
                state.current_claim.adjustments.append(adjustment)

    def _handle_svc(self, segment: List[str], state: ParseState, segment_index: int):
        """Handle SVC (Service Payment Information) segment with composite parsing."""
        if not state.current_claim:
            return
            
        service_code_raw = self._get_element(segment, 1)
        charge_amount = self._safe_float(self._get_element(segment, 2))
        paid_amount = self._safe_float(self._get_element(segment, 3))
        
        # Parse composite service code
        service_code_parts = self.utilities.parse_composite(service_code_raw, state.component_separator)
        
        service = Service(
            service_code=service_code_raw,
            charge_amount=charge_amount,
            paid_amount=paid_amount,
            revenue_code="",
            service_date="",
        )
        
        # Add parsed components as attributes
        if "procedure_code" in service_code_parts:
            service.procedure_code = service_code_parts["procedure_code"]
        if "modifier1" in service_code_parts:
            service.modifier1 = service_code_parts["modifier1"]
        if "modifier2" in service_code_parts:
            service.modifier2 = service_code_parts["modifier2"]
            
        state.current_claim.services.append(service)

    def _handle_svd(self, segment: List[str], state: ParseState, segment_index: int):
        """Handle SVD (Service Line Adjudication Information) segment."""
        if state.current_claim and state.current_claim.services:
            # SVD provides additional adjudication info for the last service
            service = state.current_claim.services[-1]
            adjudicated_amount = self._safe_float(self._get_element(segment, 2))
            
            # Add adjudication information
            if not hasattr(service, 'adjudication_info'):
                service.adjudication_info = {}
            service.adjudication_info['adjudicated_amount'] = adjudicated_amount

    def _handle_plb(self, segment: List[str], state: ParseState, segment_index: int):
        """Handle PLB (Provider Level Adjustments) segment."""
        if not state.current_transaction_835:
            return
            
        provider_id = self._get_element(segment, 1)
        fiscal_period_date = self._get_element(segment, 2)
        
        # Initialize PLB list if not exists
        if not hasattr(state.current_transaction_835, 'plb'):
            state.current_transaction_835.plb = []
        
        # Parse adjustment pairs (reason code, reference, amount)
        index = 3
        while index + 2 < len(segment):
            reason_code = self._get_element(segment, index)
            reference = self._get_element(segment, index + 1)
            amount_str = self._get_element(segment, index + 2)
            
            if reason_code and amount_str:
                try:
                    amount = float(amount_str)
                    plb_adjustment = {
                        "provider_npi": provider_id,
                        "fiscal_period_date": fiscal_period_date,
                        "reason": reason_code,
                        "reference": reference,
                        "amount": amount
                    }
                    state.current_transaction_835.plb.append(plb_adjustment)
                except ValueError:
                    pass
            
            index += 3

    def _handle_lx(self, segment: List[str], state: ParseState, segment_index: int):
        """Handle LX (Header Number) segment."""
        if state.current_claim:
            line_number = self._get_element(segment, 1)
            if not hasattr(state.current_claim, 'line_numbers'):
                state.current_claim.line_numbers = []
            state.current_claim.line_numbers.append(line_number)

    def _perform_balancing_checks(self, state: ParseState):
        """Perform financial balancing and validation checks."""
        if not state.current_transaction_835:
            return
            
        financial_info = state.current_transaction_835.financial_information
        if not financial_info:
            return
            
        # Calculate total claim payments
        total_claim_payments = sum(
            claim.total_paid for claim in state.current_transaction_835.claims
            if claim.total_paid is not None
        )
        
        # Calculate total PLB adjustments
        total_plb_adjustments = 0
        if hasattr(state.current_transaction_835, 'plb') and state.current_transaction_835.plb:
            total_plb_adjustments = sum(
                plb["amount"] for plb in state.current_transaction_835.plb
                if plb["amount"] is not None
            )
        
        # Check balance
        bpr_total = financial_info.total_paid or 0
        calculated_total = total_claim_payments + total_plb_adjustments
        balance_delta = bpr_total - calculated_total
        
        # Set balance flags
        state.current_transaction_835.out_of_balance = abs(balance_delta) > 0.01
        state.current_transaction_835.balance_delta = balance_delta
        
        if state.current_transaction_835.out_of_balance:
            logger.warning(f"Transaction out of balance: BPR={bpr_total}, Claims+PLB={calculated_total}, Delta={balance_delta}")