"""
EDI 276/277 (Claim Status Inquiry/Response) Parser

This module provides parsing capabilities for EDI 276/277 Claim Status Inquiry
and Response transactions, building the AST structures defined in ast_276.py.
"""

from typing import Dict, List, Any, Optional
import logging
from .ast_276 import (
    Transaction276, Transaction277, InformationSourceInfo276, InformationReceiverInfo276,
    ProviderInfo276, SubscriberInfo276, PatientInfo276, ClaimStatusInquiry,
    ClaimStatusInfo, ServiceLineStatusInfo, StatusMessage
)

logger = logging.getLogger(__name__)


class Parser276:
    """Parser for EDI 276/277 Claim Status Inquiry/Response transactions."""
    
    def __init__(self, segments: List[List[str]]):
        """
        Initialize the 276/277 parser.
        
        Args:
            segments: List of EDI segments, each segment is a list of elements
        """
        self.segments = segments
        self.current_index = 0
        self.transaction_type = None
        
    def parse(self):
        """
        Parse the 276/277 transaction from EDI segments.
        
        Returns:
            Transaction276 or Transaction277: Parsed transaction object
        """
        # Determine transaction type from ST segment
        st_segment = self._find_segment("ST")
        if st_segment and len(st_segment) > 1:
            self.transaction_type = st_segment[1]
        
        if self.transaction_type == "276":
            return self._parse_276()
        elif self.transaction_type == "277":
            return self._parse_277()
        else:
            # Default to 276 if unknown
            return self._parse_276()
    
    def _parse_276(self) -> Transaction276:
        """Parse 276 Claim Status Inquiry transaction."""
        transaction = Transaction276(header={})
        
        # Parse header information
        self._parse_header(transaction)
        
        # Parse hierarchical loops
        self._parse_hierarchical_loops_276(transaction)
        
        return transaction
    
    def _parse_277(self) -> Transaction277:
        """Parse 277 Claim Status Response transaction."""
        transaction = Transaction277(header={})
        
        # Parse header information
        self._parse_header(transaction)
        
        # Parse hierarchical loops
        self._parse_hierarchical_loops_277(transaction)
        
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
    
    def _parse_hierarchical_loops_276(self, transaction: Transaction276):
        """Parse hierarchical loops for 276 inquiry."""
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
            elif hierarchical_level_code == "19":  # Provider of Service
                self._parse_provider(hl_segment, transaction)
            elif hierarchical_level_code == "22":  # Subscriber
                self._parse_subscriber_276(hl_segment, transaction)
            elif hierarchical_level_code == "23":  # Patient (if different from subscriber)
                self._parse_patient_276(hl_segment, transaction)
    
    def _parse_hierarchical_loops_277(self, transaction: Transaction277):
        """Parse hierarchical loops for 277 response."""
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
            elif hierarchical_level_code == "19":  # Provider of Service
                self._parse_provider(hl_segment, transaction)
            elif hierarchical_level_code == "22":  # Subscriber
                self._parse_subscriber_277(hl_segment, transaction)
            elif hierarchical_level_code == "23":  # Patient (if different from subscriber)
                self._parse_patient_277(hl_segment, transaction)
    
    def _parse_information_source(self, hl_segment: List[str], transaction):
        """Parse information source (payer) information."""
        nm1_segment = self._find_next_segment("NM1", after_segment=hl_segment)
        if not nm1_segment or nm1_segment[1] != "PR":  # PR = Payer
            return
        
        info_source = InformationSourceInfo276(
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
        
        info_receiver = InformationReceiverInfo276(
            name=nm1_segment[3] if len(nm1_segment) > 3 else "",
            entity_identifier_code=nm1_segment[1] if len(nm1_segment) > 1 else "1P",
            id_code_qualifier=nm1_segment[8] if len(nm1_segment) > 8 else "XX",
            npi=nm1_segment[9] if len(nm1_segment) > 9 else ""
        )
        
        transaction.information_receiver = info_receiver
    
    def _parse_provider(self, hl_segment: List[str], transaction):
        """Parse provider information."""
        nm1_segment = self._find_next_segment("NM1", after_segment=hl_segment)
        if not nm1_segment or nm1_segment[1] != "85":  # 85 = Billing Provider
            return
        
        provider = ProviderInfo276(
            name=nm1_segment[3] if len(nm1_segment) > 3 else "",
            entity_identifier_code=nm1_segment[1] if len(nm1_segment) > 1 else "85",
            id_code_qualifier=nm1_segment[8] if len(nm1_segment) > 8 else "XX",
            npi=nm1_segment[9] if len(nm1_segment) > 9 else ""
        )
        
        transaction.provider = provider
    
    def _parse_subscriber_276(self, hl_segment: List[str], transaction: Transaction276):
        """Parse subscriber information for 276 inquiry."""
        nm1_segment = self._find_next_segment("NM1", after_segment=hl_segment)
        if not nm1_segment or nm1_segment[1] != "IL":  # IL = Insured/Subscriber
            return
        
        subscriber = SubscriberInfo276(
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
        
        # Parse claim inquiries for this subscriber
        self._parse_claim_inquiries(hl_segment, transaction)
    
    def _parse_subscriber_277(self, hl_segment: List[str], transaction: Transaction277):
        """Parse subscriber information for 277 response."""
        nm1_segment = self._find_next_segment("NM1", after_segment=hl_segment)
        if not nm1_segment or nm1_segment[1] != "IL":  # IL = Insured/Subscriber
            return
        
        subscriber = SubscriberInfo276(
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
        
        # Parse claim status information
        self._parse_claim_status_info(hl_segment, transaction)
        
        # Parse service line status
        self._parse_service_line_status(hl_segment, transaction)
        
        # Parse messages
        self._parse_messages(hl_segment, transaction)
    
    def _parse_patient_276(self, hl_segment: List[str], transaction: Transaction276):
        """Parse patient information for 276 inquiry."""
        nm1_segment = self._find_next_segment("NM1", after_segment=hl_segment)
        if not nm1_segment or nm1_segment[1] != "QC":  # QC = Patient
            return
        
        patient = PatientInfo276(
            first_name=nm1_segment[4] if len(nm1_segment) > 4 else "",
            last_name=nm1_segment[3] if len(nm1_segment) > 3 else "",
            middle_name=nm1_segment[5] if len(nm1_segment) > 5 else None,
            name_suffix=nm1_segment[7] if len(nm1_segment) > 7 else None
        )
        
        # Look for demographic information
        dmg_segment = self._find_next_segment("DMG", after_segment=nm1_segment)
        if dmg_segment:
            patient.date_of_birth = dmg_segment[2] if len(dmg_segment) > 2 else None
            patient.gender = dmg_segment[3] if len(dmg_segment) > 3 else None
        
        transaction.patient = patient
        
        # Parse claim inquiries for this patient
        self._parse_claim_inquiries(hl_segment, transaction)
    
    def _parse_patient_277(self, hl_segment: List[str], transaction: Transaction277):
        """Parse patient information for 277 response."""
        nm1_segment = self._find_next_segment("NM1", after_segment=hl_segment)
        if not nm1_segment or nm1_segment[1] != "QC":  # QC = Patient
            return
        
        patient = PatientInfo276(
            first_name=nm1_segment[4] if len(nm1_segment) > 4 else "",
            last_name=nm1_segment[3] if len(nm1_segment) > 3 else "",
            middle_name=nm1_segment[5] if len(nm1_segment) > 5 else None,
            name_suffix=nm1_segment[7] if len(nm1_segment) > 7 else None
        )
        
        # Look for demographic information
        dmg_segment = self._find_next_segment("DMG", after_segment=nm1_segment)
        if dmg_segment:
            patient.date_of_birth = dmg_segment[2] if len(dmg_segment) > 2 else None
            patient.gender = dmg_segment[3] if len(dmg_segment) > 3 else None
        
        transaction.patient = patient
        
        # Parse claim status information
        self._parse_claim_status_info(hl_segment, transaction)
        
        # Parse service line status  
        self._parse_service_line_status(hl_segment, transaction)
        
        # Parse messages
        self._parse_messages(hl_segment, transaction)
    
    def _parse_claim_inquiries(self, hl_segment: List[str], transaction: Transaction276):
        """Parse claim inquiry information for 276."""
        # Look for TRN segments (trace number) and associated claim data
        trn_segments = self._find_all_segments_after("TRN", hl_segment)
        
        for trn_segment in trn_segments:
            if len(trn_segment) < 3:
                continue
            
            # TRN segment contains claim control number
            claim_control_number = trn_segment[2] if len(trn_segment) > 2 else ""
            
            inquiry = ClaimStatusInquiry(claim_control_number=claim_control_number)
            
            # Look for associated AMT segment (claim amount)
            amt_segment = self._find_next_segment("AMT", after_segment=trn_segment)
            if amt_segment and len(amt_segment) > 2:
                try:
                    inquiry.total_claim_charge = float(amt_segment[2])
                except ValueError:
                    pass
            
            # Look for DTP segments (dates)
            dtp_segments = self._find_all_segments_after("DTP", trn_segment)
            for dtp_segment in dtp_segments:
                if len(dtp_segment) > 3:
                    qualifier = dtp_segment[1]
                    date_value = dtp_segment[3]
                    
                    if qualifier == "472":  # Service Date
                        inquiry.date_of_service_from = date_value
                        inquiry.date_of_service_to = date_value
                    elif qualifier == "434":  # Service Date From
                        inquiry.date_of_service_from = date_value
                    elif qualifier == "435":  # Service Date To
                        inquiry.date_of_service_to = date_value
            
            transaction.claim_inquiries.append(inquiry)
    
    def _parse_claim_status_info(self, hl_segment: List[str], transaction: Transaction277):
        """Parse claim status information (STC segments) for 277."""
        stc_segments = self._find_all_segments_after("STC", hl_segment)
        
        for stc_segment in stc_segments:
            if len(stc_segment) < 4:
                continue
            
            status_info = ClaimStatusInfo(
                entity_identifier_code=stc_segment[1],
                status_code=stc_segment[2],
                status_category_code=stc_segment[3],
                date_time_period=stc_segment[4] if len(stc_segment) > 4 else None,
                action_code=stc_segment[5] if len(stc_segment) > 5 else None
            )
            
            # Parse monetary amount if present
            if len(stc_segment) > 6 and stc_segment[6]:
                try:
                    status_info.monetary_amount = float(stc_segment[6])
                except ValueError:
                    pass
            
            transaction.claim_status_info.append(status_info)
    
    def _parse_service_line_status(self, hl_segment: List[str], transaction: Transaction277):
        """Parse service line status information for 277."""
        # Service line status typically follows SVC segments in claim responses
        svc_segments = self._find_all_segments_after("SVC", hl_segment)
        
        for i, svc_segment in enumerate(svc_segments):
            if len(svc_segment) < 2:
                continue
            
            # Look for associated STC segment for this service line
            stc_segment = None
            # Find the next STC segment after this SVC segment
            try:
                start_index = self.segments.index(svc_segment) + 1
                for j in range(start_index, len(self.segments)):
                    segment = self.segments[j]
                    if segment and segment[0] == "STC":
                        stc_segment = segment
                        break
                    elif segment and segment[0] in ["SVC", "HL"]:
                        # Stop if we hit another service or hierarchical level
                        break
            except ValueError:
                continue
            
            if stc_segment and len(stc_segment) >= 4:
                service_status = ServiceLineStatusInfo(
                    line_item_control_number=str(i + 1),  # Use index as line number
                    status_code=stc_segment[2],
                    status_category_code=stc_segment[3],
                    entity_identifier_code=stc_segment[1] if len(stc_segment) > 1 else "1"
                )
                
                # Parse monetary amount if present in SVC segment
                if len(svc_segment) > 2:
                    try:
                        service_status.monetary_amount = float(svc_segment[2])
                    except ValueError:
                        pass
                
                # Parse date/time if present in STC segment
                if len(stc_segment) > 4 and stc_segment[4]:
                    service_status.date_time_period = stc_segment[4]
                
                transaction.service_line_status.append(service_status)
    
    def _parse_messages(self, hl_segment: List[str], transaction: Transaction277):
        """Parse message information (MSG segments) for 277."""
        msg_segments = self._find_all_segments_after("MSG", hl_segment)
        
        for msg_segment in msg_segments:
            if len(msg_segment) < 2:
                continue
            
            message = StatusMessage(message_text=msg_segment[1])
            transaction.messages.append(message)
    
    def _find_segment(self, segment_id: str) -> Optional[List[str]]:
        """Find the first segment with the given ID."""
        for segment in self.segments:
            if segment and segment[0] == segment_id:
                return segment
        return None
    
    def _find_all_segments(self, segment_id: str) -> List[List[str]]:
        """Find all segments with the given ID."""
        return [segment for segment in self.segments if segment and segment[0] == segment_id]
    
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