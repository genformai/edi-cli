"""
EDI 270/271 (Eligibility Inquiry/Response) Parser

This module provides parsing capabilities for EDI 270/271 Eligibility Inquiry
and Response transactions, building the AST structures defined in ast.py.
"""

from typing import Dict, List, Any, Optional
import logging
from ...base.parser import BaseParser
from .ast import (
    Transaction270, Transaction271, InformationSourceInfo, InformationReceiverInfo,
    SubscriberEligibilityInfo, DependentEligibilityInfo, EligibilityInquiry,
    EligibilityBenefit, EligibilityMessage
)

logger = logging.getLogger(__name__)


class Parser270(BaseParser):
    """Parser for EDI 270/271 Eligibility Inquiry/Response transactions."""
    
    def __init__(self, segments: List[List[str]]):
        """
        Initialize the 270/271 parser.
        
        Args:
            segments: List of EDI segments, each segment is a list of elements
        """
        self.segments = segments
        self.current_index = 0
        self.transaction_type = None
        
    def parse(self):
        """
        Parse the 270/271 transaction from EDI segments.
        
        Returns:
            Transaction270 or Transaction271: Parsed transaction object
            
        Raises:
            ValueError: If unable to parse the transaction
        """
        try:
            # Determine transaction type from ST segment
            st_segment = self._find_segment("ST")
            if st_segment and len(st_segment) > 1:
                self.transaction_type = st_segment[1]
            
            logger.debug(f"Parsing {self.transaction_type or 'unknown'} transaction")
            
            if self.transaction_type == "270":
                return self._parse_270()
            elif self.transaction_type == "271":
                return self._parse_271()
            else:
                # Default to 270 if unknown
                logger.warning(f"Unknown transaction type {self.transaction_type}, defaulting to 270")
                return self._parse_270()
        except Exception as e:
            logger.error(f"Error parsing 270/271 transaction: {e}")
            # Return minimal transaction instead of failing
            return Transaction270(header={})
    
    def get_transaction_codes(self) -> List[str]:
        """Get the transaction codes this parser supports."""
        return ["270", "271"]
    
    def _parse_270(self) -> Transaction270:
        """
        Parse 270 Eligibility Inquiry transaction.
        
        Returns:
            Transaction270: Parsed eligibility inquiry transaction
        """
        transaction = Transaction270(header={})
        
        # Parse header information
        self._parse_header(transaction)
        
        # Parse hierarchical loops
        self._parse_hierarchical_loops_270(transaction)
        
        logger.debug(f"Parsed 270 transaction with {len(transaction.eligibility_inquiries)} inquiries")
        return transaction
    
    def _parse_271(self) -> Transaction271:
        """
        Parse 271 Eligibility Response transaction.
        
        Returns:
            Transaction271: Parsed eligibility response transaction
        """
        transaction = Transaction271(header={})
        
        # Parse header information
        self._parse_header(transaction)
        
        # Parse hierarchical loops  
        self._parse_hierarchical_loops_271(transaction)
        
        logger.debug(f"Parsed 271 transaction with {len(transaction.eligibility_benefits)} benefits")
        return transaction
    
    def _parse_header(self, transaction):
        """Parse transaction header information."""
        header = {}
        
        # Find ST segment (Transaction Set Header)
        st_segment = self._find_segment("ST")
        if st_segment:
            header["transaction_set_identifier"] = st_segment[1] if len(st_segment) > 1 else ""
            header["transaction_set_control_number"] = st_segment[2] if len(st_segment) > 2 else ""
        
        # Find BHT segment (Beginning of Hierarchical Transaction)
        bht_segment = self._find_segment("BHT")
        if bht_segment:
            header["hierarchical_structure_code"] = bht_segment[1] if len(bht_segment) > 1 else ""
            header["transaction_set_purpose_code"] = bht_segment[2] if len(bht_segment) > 2 else ""
            header["reference_identification"] = bht_segment[3] if len(bht_segment) > 3 else ""
            header["date"] = bht_segment[4] if len(bht_segment) > 4 else ""
            header["time"] = bht_segment[5] if len(bht_segment) > 5 else ""
            header["transaction_type_code"] = bht_segment[6] if len(bht_segment) > 6 else ""
        
        transaction.header = header
    
    def _parse_hierarchical_loops_270(self, transaction: Transaction270):
        """Parse hierarchical loops for 270 inquiry."""
        hl_segments = self._find_all_segments("HL")
        
        for hl_segment in hl_segments:
            if len(hl_segment) < 4:
                continue
                
            hierarchical_level_code = hl_segment[3]
            
            # Parse based on hierarchical level
            if hierarchical_level_code == "20":  # Information Source (Payer)
                self._parse_information_source(hl_segment, transaction)
            elif hierarchical_level_code == "21":  # Information Receiver (Provider)
                self._parse_information_receiver(hl_segment, transaction)
            elif hierarchical_level_code == "22":  # Subscriber
                self._parse_subscriber_270(hl_segment, transaction)
            elif hierarchical_level_code == "23":  # Dependent
                self._parse_dependent_270(hl_segment, transaction)
    
    def _parse_hierarchical_loops_271(self, transaction: Transaction271):
        """Parse hierarchical loops for 271 response."""
        hl_segments = self._find_all_segments("HL")
        
        for hl_segment in hl_segments:
            if len(hl_segment) < 4:
                continue
                
            hierarchical_level_code = hl_segment[3]
            
            # Parse based on hierarchical level
            if hierarchical_level_code == "20":  # Information Source (Payer)
                self._parse_information_source(hl_segment, transaction)
            elif hierarchical_level_code == "21":  # Information Receiver (Provider)
                self._parse_information_receiver(hl_segment, transaction)
            elif hierarchical_level_code == "22":  # Subscriber
                self._parse_subscriber_271(hl_segment, transaction)
            elif hierarchical_level_code == "23":  # Dependent
                self._parse_dependent_271(hl_segment, transaction)
    
    def _parse_information_source(self, hl_segment: List[str], transaction):
        """Parse information source (payer) information."""
        nm1_segment = self._find_next_segment("NM1", after_segment=hl_segment)
        if not nm1_segment or nm1_segment[1] != "PR":  # PR = Payer
            return
        
        info_source = InformationSourceInfo(
            name=nm1_segment[3] if len(nm1_segment) > 3 else "",
            entity_identifier_code=nm1_segment[1] if len(nm1_segment) > 1 else "PR",
            id_code_qualifier=nm1_segment[8] if len(nm1_segment) > 8 else "PI",
            id_code=nm1_segment[9] if len(nm1_segment) > 9 else ""
        )
        
        transaction.information_source = info_source
    
    def _parse_information_receiver(self, hl_segment: List[str], transaction):
        """Parse information receiver (provider) information."""
        nm1_segment = self._find_next_segment("NM1", after_segment=hl_segment)
        if not nm1_segment or nm1_segment[1] != "1P":  # 1P = Provider
            return
        
        info_receiver = InformationReceiverInfo(
            name=nm1_segment[3] if len(nm1_segment) > 3 else "",
            entity_identifier_code=nm1_segment[1] if len(nm1_segment) > 1 else "1P",
            id_code_qualifier=nm1_segment[8] if len(nm1_segment) > 8 else "XX",
            npi=nm1_segment[9] if len(nm1_segment) > 9 else ""
        )
        
        transaction.information_receiver = info_receiver
    
    def _parse_subscriber_270(self, hl_segment: List[str], transaction: Transaction270):
        """Parse subscriber information for 270 inquiry."""
        nm1_segment = self._find_next_segment("NM1", after_segment=hl_segment)
        if not nm1_segment or nm1_segment[1] != "IL":  # IL = Insured/Subscriber
            return
        
        subscriber = SubscriberEligibilityInfo(
            member_id=nm1_segment[9] if len(nm1_segment) > 9 else "",
            first_name=nm1_segment[4] if len(nm1_segment) > 4 else "",
            last_name=nm1_segment[3] if len(nm1_segment) > 3 else "",
            middle_name=nm1_segment[5] if len(nm1_segment) > 5 else None,
            name_suffix=nm1_segment[7] if len(nm1_segment) > 7 else None,
            id_code_qualifier=nm1_segment[8] if len(nm1_segment) > 8 else "MI"
        )
        
        # Look for demographic information (DMG segment)
        dmg_segment = self._find_next_segment("DMG", after_segment=nm1_segment)
        if dmg_segment:
            subscriber.date_of_birth = dmg_segment[2] if len(dmg_segment) > 2 else None
            subscriber.gender = dmg_segment[3] if len(dmg_segment) > 3 else None
        
        transaction.subscriber = subscriber
        
        # Parse eligibility inquiries for this subscriber
        self._parse_eligibility_inquiries(hl_segment, transaction)
    
    def _parse_subscriber_271(self, hl_segment: List[str], transaction: Transaction271):
        """Parse subscriber information for 271 response."""
        nm1_segment = self._find_next_segment("NM1", after_segment=hl_segment)
        if not nm1_segment or nm1_segment[1] != "IL":  # IL = Insured/Subscriber
            return
        
        subscriber = SubscriberEligibilityInfo(
            member_id=nm1_segment[9] if len(nm1_segment) > 9 else "",
            first_name=nm1_segment[4] if len(nm1_segment) > 4 else "",
            last_name=nm1_segment[3] if len(nm1_segment) > 3 else "",
            middle_name=nm1_segment[5] if len(nm1_segment) > 5 else None,
            name_suffix=nm1_segment[7] if len(nm1_segment) > 7 else None,
            id_code_qualifier=nm1_segment[8] if len(nm1_segment) > 8 else "MI"
        )
        
        # Look for demographic information
        dmg_segment = self._find_next_segment("DMG", after_segment=nm1_segment)
        if dmg_segment:
            subscriber.date_of_birth = dmg_segment[2] if len(dmg_segment) > 2 else None
            subscriber.gender = dmg_segment[3] if len(dmg_segment) > 3 else None
        
        transaction.subscriber = subscriber
        
        # Parse eligibility benefits for this subscriber
        self._parse_eligibility_benefits(hl_segment, transaction)
        
        # Parse messages
        self._parse_messages(hl_segment, transaction)
    
    def _parse_dependent_270(self, hl_segment: List[str], transaction: Transaction270):
        """Parse dependent information for 270 inquiry."""
        nm1_segment = self._find_next_segment("NM1", after_segment=hl_segment)
        if not nm1_segment or nm1_segment[1] != "03":  # 03 = Dependent
            return
        
        dependent = DependentEligibilityInfo(
            first_name=nm1_segment[4] if len(nm1_segment) > 4 else "",
            last_name=nm1_segment[3] if len(nm1_segment) > 3 else "",
            middle_name=nm1_segment[5] if len(nm1_segment) > 5 else None,
            name_suffix=nm1_segment[7] if len(nm1_segment) > 7 else None
        )
        
        # Look for demographic information
        dmg_segment = self._find_next_segment("DMG", after_segment=nm1_segment)
        if dmg_segment:
            dependent.date_of_birth = dmg_segment[2] if len(dmg_segment) > 2 else None
            dependent.gender = dmg_segment[3] if len(dmg_segment) > 3 else None
        
        transaction.dependent = dependent
        
        # Parse eligibility inquiries for this dependent
        self._parse_eligibility_inquiries(hl_segment, transaction)
    
    def _parse_dependent_271(self, hl_segment: List[str], transaction: Transaction271):
        """Parse dependent information for 271 response."""
        nm1_segment = self._find_next_segment("NM1", after_segment=hl_segment)
        if not nm1_segment or nm1_segment[1] != "03":  # 03 = Dependent
            return
        
        dependent = DependentEligibilityInfo(
            first_name=nm1_segment[4] if len(nm1_segment) > 4 else "",
            last_name=nm1_segment[3] if len(nm1_segment) > 3 else "",
            middle_name=nm1_segment[5] if len(nm1_segment) > 5 else None,
            name_suffix=nm1_segment[7] if len(nm1_segment) > 7 else None
        )
        
        # Look for demographic information
        dmg_segment = self._find_next_segment("DMG", after_segment=nm1_segment)
        if dmg_segment:
            dependent.date_of_birth = dmg_segment[2] if len(dmg_segment) > 2 else None
            dependent.gender = dmg_segment[3] if len(dmg_segment) > 3 else None
        
        transaction.dependent = dependent
        
        # Parse eligibility benefits for this dependent
        self._parse_eligibility_benefits(hl_segment, transaction)
        
        # Parse messages
        self._parse_messages(hl_segment, transaction)
    
    def _parse_eligibility_inquiries(self, hl_segment: List[str], transaction: Transaction270):
        """Parse eligibility inquiry information (EQ segments)."""
        eq_segments = self._find_all_segments_after("EQ", hl_segment)
        
        for eq_segment in eq_segments:
            if len(eq_segment) < 2:
                continue
            
            inquiry = EligibilityInquiry(
                service_type_code=eq_segment[1],
                coverage_level_code=eq_segment[2] if len(eq_segment) > 2 else None,
                insurance_type_code=eq_segment[3] if len(eq_segment) > 3 else None
            )
            
            transaction.eligibility_inquiries.append(inquiry)
    
    def _parse_eligibility_benefits(self, hl_segment: List[str], transaction: Transaction271):
        """Parse eligibility benefit information (EB segments)."""
        eb_segments = self._find_all_segments_after("EB", hl_segment)
        
        for eb_segment in eb_segments:
            if len(eb_segment) < 4:
                continue
            
            benefit = EligibilityBenefit(
                eligibility_code=eb_segment[1],
                coverage_level_code=eb_segment[2] if len(eb_segment) > 2 else "",
                service_type_code=eb_segment[3] if len(eb_segment) > 3 else "",
                insurance_type_code=eb_segment[4] if len(eb_segment) > 4 else None,
                plan_coverage_description=eb_segment[5] if len(eb_segment) > 5 else None,
                time_period_qualifier=eb_segment[6] if len(eb_segment) > 6 else None
            )
            
            # Parse monetary amount if present
            if len(eb_segment) > 7 and eb_segment[7]:
                try:
                    benefit.monetary_amount = float(eb_segment[7])
                except ValueError:
                    pass
            
            # Parse percentage if present
            if len(eb_segment) > 8 and eb_segment[8]:
                try:
                    benefit.percentage = float(eb_segment[8])
                except ValueError:
                    pass
            
            # Parse quantity qualifier and quantity
            if len(eb_segment) > 9 and eb_segment[9]:
                benefit.quantity_qualifier = eb_segment[9]
            if len(eb_segment) > 10 and eb_segment[10]:
                try:
                    benefit.quantity = float(eb_segment[10])
                except ValueError:
                    pass
            
            # Parse authorization required and in-plan network indicators
            if len(eb_segment) > 11 and eb_segment[11]:
                benefit.authorization_required = eb_segment[11]
            if len(eb_segment) > 12 and eb_segment[12]:
                benefit.in_plan_network = eb_segment[12]
            
            transaction.eligibility_benefits.append(benefit)
    
    def _parse_messages(self, hl_segment: List[str], transaction: Transaction271):
        """Parse message information (MSG segments)."""
        msg_segments = self._find_all_segments_after("MSG", hl_segment)
        
        for msg_segment in msg_segments:
            if len(msg_segment) < 2:
                continue
            
            message = EligibilityMessage(
                message_text=msg_segment[1]
            )
            
            transaction.messages.append(message)
    
    
    def _find_next_segment(self, segment_id: str, after_segment: List[str]) -> Optional[List[str]]:
        """Find the next segment with the given ID after the specified segment."""
        try:
            start_index = self.segments.index(after_segment) + 1
        except ValueError:
            return None
        
        for i in range(start_index, len(self.segments)):
            segment = self.segments[i]
            if segment and segment[0] == segment_id:
                return segment
        
        return None
    
    def _find_all_segments_after(self, segment_id: str, after_segment: List[str]) -> List[List[str]]:
        """Find all segments with the given ID after the specified segment."""
        try:
            start_index = self.segments.index(after_segment) + 1
        except ValueError:
            return []
        
        result = []
        for i in range(start_index, len(self.segments)):
            segment = self.segments[i]
            if segment and segment[0] == segment_id:
                result.append(segment)
        
        return result