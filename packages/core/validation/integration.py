"""
Integration layer between validation system and plugin architecture.

This module provides seamless integration of the validation framework
with the existing plugin system.
"""

from typing import Dict, List, Any, Optional
import logging

from .engine import ValidationEngine, ValidationResult
from .factory import create_validation_engine
from .rules_835 import Transaction835StructureRule, Transaction835DataValidationRule, Transaction835BusinessRule
from ..plugins.api import PluginManager, plugin_registry
from ..base.edi_ast import EdiRoot

logger = logging.getLogger(__name__)


class ValidationIntegrationManager:
    """Manages integration between validation system and plugin architecture."""
    
    def __init__(self, plugin_manager: Optional[PluginManager] = None):
        self.plugin_manager = plugin_manager or PluginManager()
        self.validation_engine = self._create_default_validation_engine()
        self._validation_enabled = True
    
    def _create_default_validation_engine(self) -> ValidationEngine:
        """Create validation engine with default rules."""
        builder = create_validation_engine()
        
        # Add built-in 835 validation rules
        builder.add_rule(Transaction835StructureRule())
        builder.add_rule(Transaction835DataValidationRule())
        builder.add_rule(Transaction835BusinessRule())
        
        logger.info("Created validation engine with built-in rules")
        return builder.build()
    
    def enable_validation(self):
        """Enable validation."""
        self._validation_enabled = True
        logger.info("Validation enabled")
    
    def disable_validation(self):
        """Disable validation."""
        self._validation_enabled = False
        logger.info("Validation disabled")
    
    def is_validation_enabled(self) -> bool:
        """Check if validation is enabled."""
        return self._validation_enabled
    
    def parse_and_validate(self, segments: List[List[str]], 
                          validation_context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Parse EDI segments and validate the result.
        
        Args:
            segments: EDI segments to parse
            validation_context: Optional validation context
            
        Returns:
            Dictionary containing parsing and validation results
        """
        result = {
            'parse_success': False,
            'edi_root': None,
            'parse_error': None,
            'validation_enabled': self._validation_enabled,
            'validation_result': None
        }
        
        # Step 1: Parse the segments
        try:
            edi_root = self._parse_segments(segments)
            result['parse_success'] = True
            result['edi_root'] = edi_root
            logger.debug("Successfully parsed EDI segments")
            
        except Exception as e:
            result['parse_error'] = str(e)
            logger.error(f"Failed to parse EDI segments: {e}")
            return result
        
        # Step 2: Validate if enabled
        if self._validation_enabled:
            try:
                validation_result = self.validation_engine.validate(edi_root, validation_context)
                result['validation_result'] = validation_result
                logger.debug(f"Validation completed: {validation_result.error_count} errors, "
                           f"{validation_result.warning_count} warnings")
                
            except Exception as e:
                logger.error(f"Validation failed: {e}")
                # Create error validation result
                from .engine import ValidationResult, ValidationError, ValidationSeverity
                error_result = ValidationResult(is_valid=False)
                error_result.add_error(ValidationError(
                    rule_name="system",
                    severity=ValidationSeverity.ERROR,
                    message=f"Validation system error: {str(e)}",
                    code="VALIDATION_SYSTEM_ERROR"
                ))
                result['validation_result'] = error_result
        
        return result
    
    def _parse_segments(self, segments: List[List[str]]) -> EdiRoot:
        """Parse EDI segments using appropriate plugin."""
        if not segments:
            raise ValueError("No segments provided for parsing")
        
        # Determine transaction type
        transaction_code = self._extract_transaction_code(segments)
        if not transaction_code:
            raise ValueError("Unable to determine transaction code from segments")
        
        # Get appropriate parser plugin
        parser_plugin = self.plugin_manager.registry.get_parser_for_transaction(transaction_code)
        if not parser_plugin:
            raise ValueError(f"No parser plugin available for transaction code: {transaction_code}")
        
        # Parse using the plugin
        return parser_plugin.parse(segments)
    
    def _extract_transaction_code(self, segments: List[List[str]]) -> Optional[str]:
        """Extract transaction code from segments."""
        for segment in segments:
            if segment and len(segment) >= 2 and segment[0] == "ST":
                return segment[1]
        return None
    
    def validate_document(self, edi_root: EdiRoot, 
                         validation_context: Optional[Dict[str, Any]] = None) -> ValidationResult:
        """
        Validate an already parsed EDI document.
        
        Args:
            edi_root: Parsed EDI document
            validation_context: Optional validation context
            
        Returns:
            ValidationResult with validation findings
        """
        if not self._validation_enabled:
            # Return empty successful result
            from .engine import ValidationResult
            return ValidationResult(is_valid=True)
        
        return self.validation_engine.validate(edi_root, validation_context)
    
    def add_validation_rule(self, rule):
        """Add a custom validation rule."""
        self.validation_engine.register_rule_plugin(rule)
        logger.info(f"Added validation rule: {rule.rule_name}")
    
    def add_global_validation_rule(self, rule):
        """Add a global validation rule."""
        self.validation_engine.register_global_rule(rule)
        logger.info(f"Added global validation rule: {rule.rule_name}")
    
    def enable_rule(self, rule_name: str):
        """Enable a specific validation rule."""
        self.validation_engine.enable_rule(rule_name)
        logger.info(f"Enabled validation rule: {rule_name}")
    
    def disable_rule(self, rule_name: str):
        """Disable a specific validation rule."""
        self.validation_engine.disable_rule(rule_name)
        logger.info(f"Disabled validation rule: {rule_name}")
    
    def get_validation_summary(self) -> Dict[str, Any]:
        """Get summary of validation configuration."""
        return {
            'validation_enabled': self._validation_enabled,
            'validation_engine_summary': self.validation_engine.get_rule_summary(),
            'available_parsers': list(self.plugin_manager.registry.list_registered_parsers().keys())
        }


# Global integration manager instance
validation_manager = ValidationIntegrationManager()


def setup_validation_integration(plugin_manager: Optional[PluginManager] = None) -> ValidationIntegrationManager:
    """
    Setup validation integration with plugin system.
    
    Args:
        plugin_manager: Optional plugin manager instance
        
    Returns:
        Configured ValidationIntegrationManager
    """
    global validation_manager
    
    if plugin_manager:
        validation_manager = ValidationIntegrationManager(plugin_manager)
    else:
        # Load built-in plugins
        validation_manager.plugin_manager.load_builtin_plugins()
    
    logger.info("Validation integration setup completed")
    return validation_manager


def parse_and_validate(segments: List[List[str]], 
                      validation_context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Convenience function to parse and validate EDI segments.
    
    Args:
        segments: EDI segments to parse
        validation_context: Optional validation context
        
    Returns:
        Dictionary containing parsing and validation results
    """
    return validation_manager.parse_and_validate(segments, validation_context)


def validate_document(edi_root: EdiRoot, 
                     validation_context: Optional[Dict[str, Any]] = None) -> ValidationResult:
    """
    Convenience function to validate an EDI document.
    
    Args:
        edi_root: Parsed EDI document
        validation_context: Optional validation context
        
    Returns:
        ValidationResult with validation findings
    """
    return validation_manager.validate_document(edi_root, validation_context)