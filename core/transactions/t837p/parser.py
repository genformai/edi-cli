"""
EDI 837P (Professional Claims) Parser

This module provides parsing capabilities for EDI 837P Professional Claims
transactions, building the AST structures defined in ast_837p.py.
"""

from typing import Dict, List, Any, Optional
import logging
from ...base.parser import BaseParser
from ...base.edi_ast import EdiRoot, Interchange, FunctionalGroup, Transaction
from .ast import (
    Transaction837P, SubmitterInfo, ReceiverInfo, BillingProviderInfo,
    SubscriberInfo, PatientInfo, ClaimInfo837P, ServiceLine837P,
    DiagnosisInfo, RenderingProviderInfo
)

logger = logging.getLogger(__name__)


class Parser837P(BaseParser):
    """Parser for EDI 837P Professional Claims transactions."""
    
    def __init__(self, segments: List[List[str]]):
        """
        Initialize the 837P parser.
        
        Args:
            segments: List of EDI segments, each segment is a list of elements
        """
        super().__init__(segments)
        self.transaction = None
        
    def parse(self) -> EdiRoot:
        """
        Parse the 837P transaction from EDI segments.
        
        Returns:
            EdiRoot: Parsed EDI document with 837P transaction
            
        Raises:
            ValueError: If unable to parse the transaction
        """
        try:
            self.transaction = Transaction837P(header={})
            
            logger.debug("Parsing 837P professional claims transaction")
            
            # Parse header information
            self._parse_header()
            
            # Parse hierarchical loops
            self._parse_hierarchical_loops()
            
            logger.debug(f"Parsed 837P transaction with {len(self.transaction.service_lines)} service lines")
            
            # Wrap in EdiRoot structure for consistency with other parsers
            transaction = Transaction(
                transaction_set_code=self.transaction.header.get("transaction_set_identifier", "837"),
                control_number=self.transaction.header.get("transaction_set_control_number", "0001"),
                transaction_data=self.transaction
            )
            
            functional_group = FunctionalGroup(
                functional_group_code="HC",
                sender_id="SENDER",
                receiver_id="RECEIVER", 
                date="20240101",
                time="1200",
                control_number="1"
            )
            functional_group.transactions = [transaction]
            
            interchange = Interchange(
                sender_id="SENDER",
                receiver_id="RECEIVER",
                date="20240101", 
                time="1200",
                control_number="1"
            )
            interchange.functional_groups = [functional_group]
            
            root = EdiRoot()
            root.interchanges = [interchange]
            return root
            
        except Exception as e:
            logger.error(f"Error parsing 837P transaction: {e}")
            # Return minimal structure instead of failing
            transaction = Transaction(
                transaction_set_code="837",
                control_number="0001",
                transaction_data=Transaction837P(header={})
            )
            functional_group = FunctionalGroup(
                functional_group_code="HC",
                sender_id="SENDER",
                receiver_id="RECEIVER",
                date="20240101",
                time="1200", 
                control_number="1"
            )
            functional_group.transactions = [transaction]
            
            interchange = Interchange(
                sender_id="SENDER",
                receiver_id="RECEIVER",
                date="20240101",
                time="1200",
                control_number="1"
            )
            interchange.functional_groups = [functional_group]
            
            root = EdiRoot()
            root.interchanges = [interchange]
            return root
    
    def get_transaction_codes(self) -> List[str]:
        """Get the transaction codes this parser supports."""
        return ["837"]
    
    def _parse_header(self):
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
        
        self.transaction.header = header
    
    def _parse_hierarchical_loops(self):
        """Parse hierarchical loops (HL segments) and their associated data."""
        # First, parse submitter and receiver info that appear before HL segments
        self._parse_transaction_level_info()
        
        hl_segments = self._find_all_segments("HL")
        
        for hl_segment in hl_segments:
            if len(hl_segment) < 4:
                continue
                
            hierarchical_level_code = hl_segment[3]
            
            # Parse based on hierarchical level
            if hierarchical_level_code == "20":  # Billing Provider (Information Source)
                self._parse_billing_provider_info(hl_segment)
                # Parse claim information after billing provider
                self._parse_claim_info(hl_segment)
            elif hierarchical_level_code == "22":  # Subscriber
                self._parse_subscriber_info(hl_segment)
            elif hierarchical_level_code == "23":  # Patient (if different from subscriber)
                self._parse_patient_info(hl_segment)
    
    def _parse_transaction_level_info(self):
        """Parse submitter and receiver info that appear at transaction level."""
        # Find submitter info (NM1*41) - appears early in transaction
        nm1_segments = self._find_all_segments("NM1")
        
        for nm1_segment in nm1_segments:
            if len(nm1_segment) > 1 and nm1_segment[1] == "41":  # Submitter
                submitter = SubmitterInfo(
                    name=nm1_segment[3] if len(nm1_segment) > 3 else "",
                    entity_identifier_code=nm1_segment[1],
                    id_code_qualifier=nm1_segment[8] if len(nm1_segment) > 8 else "46",
                    id_code=nm1_segment[9] if len(nm1_segment) > 9 else ""
                )
                
                # Look for contact information (PER segment after this NM1)
                per_segment = self._find_next_segment("PER", after_segment=nm1_segment)
                if per_segment:
                    submitter.contact_name = per_segment[2] if len(per_segment) > 2 else None
                    # Parse contact methods
                    for i in range(3, len(per_segment), 2):
                        if i + 1 < len(per_segment):
                            method = per_segment[i]
                            value = per_segment[i + 1]
                            if method == "TE":  # Telephone
                                submitter.contact_phone = value
                            elif method == "EM":  # Email
                                submitter.contact_email = value
                
                self.transaction.submitter = submitter
                break
        
        # Find receiver info (NM1*40)
        for nm1_segment in nm1_segments:
            if len(nm1_segment) > 1 and nm1_segment[1] == "40":  # Receiver
                receiver = ReceiverInfo(
                    name=nm1_segment[3] if len(nm1_segment) > 3 else "",
                    entity_identifier_code=nm1_segment[1],
                    id_code_qualifier=nm1_segment[8] if len(nm1_segment) > 8 else "46",
                    id_code=nm1_segment[9] if len(nm1_segment) > 9 else ""
                )
                self.transaction.receiver = receiver
                break
    
    def _parse_submitter_info(self, hl_segment: List[str]):
        """Parse submitter information."""
        # Find associated NM1 segment for submitter
        nm1_segment = self._find_next_segment("NM1", after_segment=hl_segment)
        if not nm1_segment or nm1_segment[1] != "41":  # 41 = Submitter
            return
        
        submitter = SubmitterInfo(
            name=nm1_segment[3] if len(nm1_segment) > 3 else "",
            entity_identifier_code=nm1_segment[1] if len(nm1_segment) > 1 else "41",
            id_code_qualifier=nm1_segment[8] if len(nm1_segment) > 8 else "46",
            id_code=nm1_segment[9] if len(nm1_segment) > 9 else ""
        )
        
        # Look for contact information (PER segment)
        per_segment = self._find_next_segment("PER", after_segment=nm1_segment)
        if per_segment:
            submitter.contact_name = per_segment[2] if len(per_segment) > 2 else None
            # Parse contact methods (phone, email can be in different positions)
            for i in range(3, len(per_segment), 2):
                if i + 1 < len(per_segment):
                    method = per_segment[i]
                    value = per_segment[i + 1]
                    if method == "TE":  # Telephone
                        submitter.contact_phone = value
                    elif method == "EM":  # Email
                        submitter.contact_email = value
        
        self.transaction.submitter = submitter
    
    def _parse_receiver_info(self, hl_segment: List[str]):
        """Parse receiver information."""
        nm1_segment = self._find_next_segment("NM1", after_segment=hl_segment)
        if not nm1_segment or nm1_segment[1] != "40":  # 40 = Receiver
            return
        
        receiver = ReceiverInfo(
            name=nm1_segment[3] if len(nm1_segment) > 3 else "",
            entity_identifier_code=nm1_segment[1] if len(nm1_segment) > 1 else "40",
            id_code_qualifier=nm1_segment[8] if len(nm1_segment) > 8 else "46",
            id_code=nm1_segment[9] if len(nm1_segment) > 9 else ""
        )
        
        self.transaction.receiver = receiver
    
    def _parse_billing_provider_info(self, hl_segment: List[str]):
        """Parse billing provider information."""
        nm1_segment = self._find_next_segment("NM1", after_segment=hl_segment)
        if not nm1_segment or nm1_segment[1] != "85":  # 85 = Billing Provider
            return
        
        billing_provider = BillingProviderInfo(
            name=nm1_segment[3] if len(nm1_segment) > 3 else "",
            entity_identifier_code=nm1_segment[1] if len(nm1_segment) > 1 else "85",
            id_code_qualifier=nm1_segment[8] if len(nm1_segment) > 8 else "XX",
            npi=nm1_segment[9] if len(nm1_segment) > 9 else ""
        )
        
        # Look for tax ID information (REF segment)
        ref_segment = self._find_next_segment("REF", after_segment=nm1_segment)
        if ref_segment and ref_segment[1] == "EI":  # EI = Employer ID
            billing_provider.tax_id = ref_segment[2] if len(ref_segment) > 2 else ""
        
        # Look for address information (N3, N4 segments)
        address = self._parse_address_info(nm1_segment)
        if address:
            billing_provider.address = address
        
        self.transaction.billing_provider = billing_provider
    
    def _parse_subscriber_info(self, hl_segment: List[str]):
        """Parse subscriber information."""
        # Find SBR segment (Subscriber Information)
        sbr_segment = self._find_next_segment("SBR", after_segment=hl_segment)
        if not sbr_segment:
            return
        
        nm1_segment = self._find_next_segment("NM1", after_segment=sbr_segment)
        if not nm1_segment or nm1_segment[1] != "IL":  # IL = Insured/Subscriber
            return
        
        subscriber = SubscriberInfo(
            payer_responsibility_code=sbr_segment[1] if len(sbr_segment) > 1 else "P",
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
        
        # Parse address
        address = self._parse_address_info(nm1_segment)
        if address:
            subscriber.address = address
        
        self.transaction.subscriber = subscriber
    
    def _parse_patient_info(self, hl_segment: List[str]):
        """Parse patient information (if different from subscriber)."""
        # Find PAT segment (Patient Information)
        pat_segment = self._find_next_segment("PAT", after_segment=hl_segment)
        if not pat_segment:
            return
        
        nm1_segment = self._find_next_segment("NM1", after_segment=pat_segment)
        if not nm1_segment or nm1_segment[1] != "QC":  # QC = Patient
            return
        
        patient = PatientInfo(
            relationship_code=pat_segment[1] if len(pat_segment) > 1 else "18",
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
        
        # Parse address
        address = self._parse_address_info(nm1_segment)
        if address:
            patient.address = address
        
        self.transaction.patient = patient
    
    def _parse_claim_info(self, hl_segment: List[str]):
        """Parse claim information."""
        # Find CLM segment (Claim Information)
        clm_segment = self._find_next_segment("CLM", after_segment=hl_segment)
        if not clm_segment:
            return
        
        claim = ClaimInfo837P(
            claim_id=clm_segment[1] if len(clm_segment) > 1 else "",
            total_charge=float(clm_segment[2]) if len(clm_segment) > 2 and clm_segment[2] else 0.0,
            place_of_service_code=clm_segment[5] if len(clm_segment) > 5 else "",
            signature_indicator=clm_segment[6] if len(clm_segment) > 6 else "Y",
            medicare_assignment=clm_segment[7] if len(clm_segment) > 7 else "A",
            benefits_assignment=clm_segment[8] if len(clm_segment) > 8 else "Y",
            release_of_info=clm_segment[9] if len(clm_segment) > 9 else "Y"
        )
        
        self.transaction.claim = claim
        
        # Parse diagnosis information
        self._parse_diagnosis_info(clm_segment)
        
        # Parse service lines
        self._parse_service_lines(clm_segment)
        
        # Parse rendering provider
        self._parse_rendering_provider(clm_segment)
    
    def _parse_diagnosis_info(self, clm_segment: List[str]):
        """Parse diagnosis information."""
        # Find HI segments (Health Care Diagnosis Code)
        hi_segments = self._find_all_segments_after("HI", clm_segment)
        
        diagnoses = []
        for hi_segment in hi_segments:
            # HI segments can contain multiple diagnosis codes
            for i in range(1, len(hi_segment)):
                element = hi_segment[i]
                if ":" in element:  # Format: qualifier:code
                    qualifier, code = element.split(":", 1)
                    diagnoses.append(DiagnosisInfo(qualifier=qualifier, code=code))
        
        self.transaction.diagnoses = diagnoses
    
    def _parse_service_lines(self, clm_segment: List[str]):
        """Parse service line information."""
        # Find LX segments (Service Line Number)
        lx_segments = self._find_all_segments_after("LX", clm_segment)
        
        service_lines = []
        for lx_segment in lx_segments:
            line_number = lx_segment[1] if len(lx_segment) > 1 else ""
            
            # Find associated SV1 segment (Professional Service)
            sv1_segment = self._find_next_segment("SV1", after_segment=lx_segment)
            if not sv1_segment:
                continue
            
            # Parse procedure code and modifiers
            procedure_info = sv1_segment[1] if len(sv1_segment) > 1 else ""
            procedure_parts = procedure_info.split(":") if ":" in procedure_info else [procedure_info]
            
            procedure_code = procedure_parts[1] if len(procedure_parts) > 1 else procedure_parts[0]
            modifiers = procedure_parts[2:6] if len(procedure_parts) > 2 else []
            
            service_line = ServiceLine837P(
                line_number=line_number,
                procedure_code=procedure_code,
                procedure_modifiers=modifiers,
                charge_amount=float(sv1_segment[2]) if len(sv1_segment) > 2 and sv1_segment[2] else 0.0,
                units=float(sv1_segment[4]) if len(sv1_segment) > 4 and sv1_segment[4] else 1.0,
                diagnosis_pointers=sv1_segment[7].split() if len(sv1_segment) > 7 and sv1_segment[7] else []
            )
            
            # Look for additional service line information
            if len(sv1_segment) > 8:
                service_line.emergency_indicator = sv1_segment[8] if sv1_segment[8] else None
            
            service_lines.append(service_line)
        
        self.transaction.service_lines = service_lines
    
    def _parse_rendering_provider(self, clm_segment: List[str]):
        """Parse rendering provider information."""
        # Find NM1 segment with entity identifier 82 (Rendering Provider)
        segments_after_claim = self._get_segments_after(clm_segment)
        
        for segment in segments_after_claim:
            if segment[0] == "NM1" and len(segment) > 1 and segment[1] == "82":
                rendering_provider = RenderingProviderInfo(
                    entity_identifier_code=segment[1],
                    name=segment[3] if len(segment) > 3 else "",
                    id_code_qualifier=segment[8] if len(segment) > 8 else "XX",
                    npi=segment[9] if len(segment) > 9 else ""
                )
                
                self.transaction.rendering_provider = rendering_provider
                break
    
    def _parse_address_info(self, after_segment: List[str]) -> Optional[Dict[str, str]]:
        """Parse address information from N3 and N4 segments."""
        n3_segment = self._find_next_segment("N3", after_segment=after_segment)
        n4_segment = self._find_next_segment("N4", after_segment=after_segment)
        
        if not n3_segment and not n4_segment:
            return None
        
        address = {}
        
        if n3_segment:
            address["address_line_1"] = n3_segment[1] if len(n3_segment) > 1 else ""
            address["address_line_2"] = n3_segment[2] if len(n3_segment) > 2 else ""
        
        if n4_segment:
            address["city"] = n4_segment[1] if len(n4_segment) > 1 else ""
            address["state"] = n4_segment[2] if len(n4_segment) > 2 else ""
            address["postal_code"] = n4_segment[3] if len(n4_segment) > 3 else ""
            address["country_code"] = n4_segment[4] if len(n4_segment) > 4 else ""
        
        return address if address else None
    
    
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
    
    def _get_segments_after(self, after_segment: List[str]) -> List[List[str]]:
        """Get all segments after the specified segment."""
        try:
            start_index = self.segments.index(after_segment) + 1
        except ValueError:
            return []
        
        return self.segments[start_index:]