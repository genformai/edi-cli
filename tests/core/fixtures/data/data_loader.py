"""
Data loader for YAML-based test data sources.
"""

import yaml
import random
from pathlib import Path
from typing import Dict, List, Any, Optional
from decimal import Decimal

from ..base.data_types import Address, EntityInfo
from ..base.generators import DataGenerator


class DataLoader:
    """Loads and manages YAML-based test data."""
    
    def __init__(self):
        self.data_dir = Path(__file__).parent
        self._payers: Optional[List[Dict]] = None
        self._providers: Optional[List[Dict]] = None
        self._procedure_codes: Optional[List[Dict]] = None
        self._diagnosis_codes: Optional[List[Dict]] = None
    
    def _load_yaml(self, filename: str) -> Dict[str, Any]:
        """Load a YAML file from the data directory."""
        file_path = self.data_dir / filename
        with open(file_path, 'r', encoding='utf-8') as file:
            return yaml.safe_load(file)
    
    @property
    def payers(self) -> List[Dict]:
        """Get all payer data."""
        if self._payers is None:
            data = self._load_yaml('payers.yaml')
            self._payers = data['payers']
        return self._payers
    
    @property
    def providers(self) -> List[Dict]:
        """Get all provider data."""
        if self._providers is None:
            data = self._load_yaml('providers.yaml')
            self._providers = data['providers']
        return self._providers
    
    @property
    def procedure_codes(self) -> List[Dict]:
        """Get all procedure code data."""
        if self._procedure_codes is None:
            data = self._load_yaml('procedure_codes.yaml')
            self._procedure_codes = data['procedure_codes']
        return self._procedure_codes
    
    @property
    def diagnosis_codes(self) -> List[Dict]:
        """Get all diagnosis code data."""
        if self._diagnosis_codes is None:
            data = self._load_yaml('diagnosis_codes.yaml')
            self._diagnosis_codes = data['diagnosis_codes']
        return self._diagnosis_codes
    
    def get_random_payer(self, payer_type: str = None) -> Dict:
        """
        Get a random payer, optionally filtered by type.
        
        Args:
            payer_type: Optional filter ('insurance', 'government', 'hmo')
        """
        payers = self.payers
        if payer_type:
            payers = [p for p in payers if p.get('type') == payer_type]
        
        if not payers:
            raise ValueError(f"No payers found for type: {payer_type}")
        
        return random.choice(payers)
    
    def get_random_provider(self, provider_type: str = None, specialty: str = None) -> Dict:
        """
        Get a random provider, optionally filtered by type or specialty.
        
        Args:
            provider_type: Optional filter ('individual', 'facility')
            specialty: Optional specialty code filter
        """
        providers = self.providers
        
        if provider_type:
            providers = [p for p in providers if p.get('type') == provider_type]
        
        if specialty:
            providers = [p for p in providers if p.get('specialty') == specialty]
        
        if not providers:
            # Fallback to all providers if filters are too restrictive
            providers = self.providers
        
        return random.choice(providers)
    
    def get_random_procedure_codes(self, category: str = None, count: int = 1) -> List[Dict]:
        """
        Get random procedure codes, optionally filtered by category.
        
        Args:
            category: Optional category filter ('office_visit', 'laboratory', etc.)
            count: Number of codes to return
        """
        codes = self.procedure_codes
        
        if category:
            codes = [c for c in codes if c.get('category') == category]
        
        if not codes:
            codes = self.procedure_codes  # Fallback
        
        return random.sample(codes, min(count, len(codes)))
    
    def get_random_diagnosis_codes(self, category: str = None, severity: str = None, count: int = 1) -> List[Dict]:
        """
        Get random diagnosis codes, optionally filtered by category or severity.
        
        Args:
            category: Optional category filter ('cardiovascular', 'respiratory', etc.)
            severity: Optional severity filter ('acute', 'chronic', 'symptom', etc.)
            count: Number of codes to return
        """
        codes = self.diagnosis_codes
        
        if category:
            codes = [c for c in codes if c.get('category') == category]
        
        if severity:
            codes = [c for c in codes if c.get('severity') == severity]
        
        if not codes:
            codes = self.diagnosis_codes  # Fallback
        
        return random.sample(codes, min(count, len(codes)))
    
    def create_payer_entity(self, payer_data: Dict = None) -> EntityInfo:
        """Create an EntityInfo object from payer data."""
        if payer_data is None:
            payer_data = self.get_random_payer()
        
        address = None
        if 'address' in payer_data:
            addr_data = payer_data['address']
            address = Address(
                line1=addr_data['line1'],
                line2=addr_data.get('line2'),
                city=addr_data['city'],
                state=addr_data['state'],
                zip_code=addr_data['zip']
            )
        
        return EntityInfo(
            name=payer_data['name'],
            entity_type="2",  # Organization
            id_qualifier="PI",  # Payer Identification
            id_value=payer_data['id'],
            address=address
        )
    
    def create_provider_entity(self, provider_data: Dict = None) -> EntityInfo:
        """Create an EntityInfo object from provider data."""
        if provider_data is None:
            provider_data = self.get_random_provider()
        
        address = None
        if 'address' in provider_data:
            addr_data = provider_data['address']
            address = Address(
                line1=addr_data['line1'],
                line2=addr_data.get('line2'),
                city=addr_data['city'],
                state=addr_data['state'],
                zip_code=addr_data['zip']
            )
        
        # Determine entity type based on provider type
        entity_type = "1" if provider_data.get('type') == 'individual' else "2"
        
        return EntityInfo(
            name=provider_data['name'],
            entity_type=entity_type,
            id_qualifier="XX",  # NPI
            id_value=provider_data['npi'],
            address=address
        )
    
    def get_procedure_with_charge(self, procedure_code: str = None) -> tuple[str, Decimal]:
        """
        Get a procedure code with its typical charge.
        
        Returns:
            Tuple of (procedure_code, typical_charge)
        """
        if procedure_code:
            # Find specific procedure
            for proc in self.procedure_codes:
                if proc['code'] == procedure_code:
                    return proc['code'], Decimal(str(proc['typical_charge']))
        
        # Get random procedure
        proc = random.choice(self.procedure_codes)
        return proc['code'], Decimal(str(proc['typical_charge']))
    
    def get_related_diagnosis_and_procedure(self, category: str = None) -> tuple[str, str, Decimal]:
        """
        Get related diagnosis and procedure codes with charge.
        
        Returns:
            Tuple of (diagnosis_code, procedure_code, charge)
        """
        # Common relationships between diagnoses and procedures
        relationships = {
            'cardiovascular': ['office_visit', 'procedure'],
            'respiratory': ['office_visit', 'radiology'],
            'gastrointestinal': ['office_visit', 'procedure'],
            'musculoskeletal': ['office_visit', 'radiology'],
            'endocrine': ['office_visit', 'laboratory'],
            'general': ['office_visit', 'laboratory']
        }
        
        if category and category in relationships:
            diag_codes = self.get_random_diagnosis_codes(category=category, count=1)
            proc_categories = relationships[category]
            proc_codes = self.get_random_procedure_codes(category=random.choice(proc_categories), count=1)
        else:
            diag_codes = self.get_random_diagnosis_codes(count=1)
            proc_codes = self.get_random_procedure_codes(count=1)
        
        diagnosis = diag_codes[0]['code']
        procedure = proc_codes[0]['code']
        charge = Decimal(str(proc_codes[0]['typical_charge']))
        
        return diagnosis, procedure, charge
    
    def get_office_visit_scenario(self) -> Dict[str, Any]:
        """Get a complete office visit scenario with related codes."""
        # Get a primary diagnosis
        diagnosis = self.get_random_diagnosis_codes(severity='chronic', count=1)[0]
        
        # Get appropriate office visit code
        office_visit = self.get_random_procedure_codes(category='office_visit', count=1)[0]
        
        # Possibly add lab work
        add_lab = random.choice([True, False])
        lab_service = None
        if add_lab:
            lab_service = self.get_random_procedure_codes(category='laboratory', count=1)[0]
        
        return {
            'diagnosis': diagnosis,
            'office_visit': office_visit,
            'lab_service': lab_service,
            'total_charge': Decimal(str(office_visit['typical_charge'])) + 
                           (Decimal(str(lab_service['typical_charge'])) if lab_service else Decimal('0'))
        }


# Global instance for easy access
data_loader = DataLoader()