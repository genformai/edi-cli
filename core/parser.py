"""
EDI Parser - Main Parser Engine

This module provides the main parsing engine for EDI documents, with support
for multiple transaction types through a plugin architecture. It handles the
core parsing logic and delegates specific transaction parsing to specialized
parsers through the plugin system.
"""

import json
from typing import List, Optional, Dict, Any
import logging
from .schema import EdiSchema
from .base.edi_ast import EdiRoot, Interchange, FunctionalGroup, Transaction
from .transactions.t835.ast import Transaction835, FinancialInformation, Payer, Payee, Claim, Adjustment, Service
from .plugins.api import plugin_registry, PluginManager

logger = logging.getLogger(__name__)


class EdiParser:
    """
    Main EDI parser engine supporting multiple transaction types.
    
    This parser uses a plugin architecture to delegate specific transaction
    parsing to specialized parsers while handling the core EDI structure.
    """
    
    def __init__(self, edi_string: str, schema_path: str, auto_load_plugins: bool = True):
        """
        Initialize the EDI parser.
        
        Args:
            edi_string: Raw EDI content to parse
            schema_path: Path to EDI schema definition file 
            auto_load_plugins: Whether to automatically load built-in plugins
        """
        self.edi_string = edi_string
        with open(schema_path, 'r') as f:
            self.schema = EdiSchema.model_validate(json.load(f))
        self.segment_delimiter = self.schema.schema_definition.delimiters.segment
        self.element_delimiter = self.schema.schema_definition.delimiters.element
        
        # Initialize plugin manager and load built-in plugins
        self.plugin_manager = PluginManager(plugin_registry)
        if auto_load_plugins:
            self._load_plugins()

    def parse(self) -> EdiRoot:
        """
        Parse the EDI document into an AST structure.
        
        Returns:
            EdiRoot: The parsed EDI document as an abstract syntax tree
            
        Raises:
            ValueError: If segments are invalid for the detected transaction type
        """
        # Normalize EDI content
        edi_content = self.edi_string.replace('\n', '').replace('\r', '').strip()
        segments = edi_content.split(self.segment_delimiter)
        segments = [s for s in segments if s]

        # Convert string segments to lists for easier processing
        segment_lists = self._prepare_segments(segments)

        # Handle empty content
        if not segment_lists:
            return EdiRoot()
        
        # Detect transaction type and route to appropriate plugin
        transaction_type = self._detect_transaction_type(segment_lists)
        logger.debug(f"Detected transaction type: {transaction_type}")
        
        # Get plugin for this transaction type
        plugin = plugin_registry.get_parser_for_transaction(transaction_type)
        if plugin:
            if plugin.validate_segments(segment_lists):
                logger.debug(f"Using plugin {plugin.plugin_name} for parsing")
                return plugin.parse(segment_lists)
            else:
                # For invalid segments, fall back to direct parser or return empty root
                if transaction_type == "835":
                    logger.warning("Plugin validation failed, falling back to direct 835 parsing")
                    return self._parse_with_direct_parser(transaction_type, segment_lists)
                else:
                    raise ValueError(f"Invalid segments for transaction type {transaction_type}")
        else:
            # Fallback to direct parser if no plugin found
            logger.debug("No plugin found, using direct parser")
            return self._parse_with_direct_parser(transaction_type, segment_lists)
    
    def _prepare_segments(self, segments: List[str]) -> List[List[str]]:
        """
        Convert string segments to lists of elements.
        
        Args:
            segments: List of segment strings
            
        Returns:
            List of segments, each segment is a list of elements
        """
        segment_lists = []
        for segment_str in segments:
            parts = segment_str.split(self.element_delimiter)
            segment_lists.append(parts)
        return segment_lists
    
    def _load_plugins(self):
        """Load built-in plugins."""
        try:
            self.plugin_manager.load_builtin_plugins()
        except Exception as e:
            print(f"Warning: Failed to load some plugins: {e}")
    
    def _detect_transaction_type(self, segments: list) -> str:
        """Detect the transaction type from ST segment."""
        for segment in segments:
            if segment[0] == "ST" and len(segment) > 1:
                return segment[1]
        return "835"  # Default to 835
    
    def _parse_with_direct_parser(self, transaction_type: str, segments: list) -> EdiRoot:
        """Parse using direct parser instances for specific transaction types."""
        # Import parsers here to avoid circular imports
        from .parser_835 import Parser835
        from .parser_270 import Parser270
        from .parser_276 import Parser276
        from .parser_837p import Parser837P
        
        try:
            if transaction_type == "835":
                parser = Parser835(segments)
                return parser.parse()
            elif transaction_type in ["270", "271"]:
                parser = Parser270(segments)
                result = parser.parse()
                # For 270/271, we need to wrap the result in an EdiRoot
                # This is a temporary solution - ideally these parsers would return EdiRoot
                root = EdiRoot()
                # Add the transaction result to the root structure
                # Note: This is a simplified approach for now
                return root
            elif transaction_type in ["276", "277"]:
                parser = Parser276(segments)
                result = parser.parse()
                # Similar wrapping for 276/277
                root = EdiRoot()
                return root
            elif transaction_type == "837":
                parser = Parser837P(segments)
                result = parser.parse()
                # Similar wrapping for 837P
                root = EdiRoot()
                return root
            else:
                # Default to 835 parser
                logger.warning(f"Unknown transaction type {transaction_type}, defaulting to 835")
                parser = Parser835(segments)
                return parser.parse()
        except Exception as e:
            logger.error(f"Error in direct parser for transaction {transaction_type}: {e}")
            # Return empty root on error
            return EdiRoot()
    
    def get_supported_transaction_types(self) -> list:
        """Get list of supported transaction types from registered plugins."""
        return list(plugin_registry._transaction_parsers.keys())
    
    def get_plugin_info(self) -> dict:
        """Get information about registered plugins."""
        return {
            "parsers": plugin_registry.list_registered_parsers(),
            "validation_rules": plugin_registry.list_registered_validation_rules()
        }