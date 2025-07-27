"""
Tests for the improved plugin architecture.

These tests verify that the new factory-based plugin system works correctly
and reduces coupling between plugins and core implementations.
"""

import pytest
from packages.core.plugins.api import PluginManager, PluginRegistry
from packages.core.plugins.implementations.plugin_835 import Plugin835
from packages.core.plugins.factory import GenericTransactionParserFactory, GenericASTNodeFactory
from packages.core.base.edi_ast import EdiRoot


class TestPluginArchitecture:
    """Test cases for the new plugin architecture."""

    def test_plugin_instantiation(self):
        """Test that plugins can be instantiated without errors."""
        plugin = Plugin835()
        
        assert plugin.plugin_name == "EDI-835-Parser"
        assert plugin.plugin_version == "1.0.0"
        assert plugin.transaction_codes == ["835"]
        assert plugin.get_schema_path() == "schemas/835.json"

    def test_factory_setup(self):
        """Test that plugin factories are set up correctly."""
        plugin = Plugin835()
        
        parser_factory, ast_factory = plugin.setup_factories()
        
        assert isinstance(parser_factory, GenericTransactionParserFactory)
        assert isinstance(ast_factory, GenericASTNodeFactory)
        assert parser_factory.get_supported_codes() == ["835"]

    def test_plugin_registry(self):
        """Test plugin registration and retrieval."""
        registry = PluginRegistry()
        plugin = Plugin835()
        
        # Register plugin
        registry.register_transaction_parser(plugin)
        
        # Verify registration
        assert "835" in registry._transaction_parsers
        assert registry.get_parser_for_transaction("835") == plugin
        assert registry.get_parser_for_transaction("270") is None

    def test_plugin_manager_builtin_loading(self):
        """Test that plugin manager can load all built-in plugins."""
        manager = PluginManager()
        manager.load_builtin_plugins()
        
        # Verify all expected plugins are loaded
        parsers = manager.registry.list_registered_parsers()
        expected_plugins = ["EDI-835-Parser", "EDI-837P-Parser", "EDI-270-271-Parser", "EDI-276-277-Parser"]
        
        for plugin_name in expected_plugins:
            assert plugin_name in parsers

    def test_plugin_parsing_integration(self):
        """Test that plugins can parse EDI segments correctly."""
        plugin = Plugin835()
        
        # Minimal 835 segments
        segments = [
            ["ISA", "00", "", "00", "", "ZZ", "SENDER", "ZZ", "RECEIVER", "241226", "1430", "U", "00501", "000000001", "0", "P", ">"],
            ["GS", "HP", "SENDER", "RECEIVER", "20241226", "1430", "000000001", "X", "005010X221A1"],
            ["ST", "835", "0001"],
            ["BPR", "I", "1000.00", "C", "ACH", "", "", "", "", "", "", "20241226"],
            ["TRN", "1", "TRACE123", "1"],
            ["SE", "5", "0001"],
            ["GE", "1", "000000001"],
            ["IEA", "1", "000000001"]
        ]
        
        result = plugin.parse(segments)
        
        # Verify parsing results
        assert isinstance(result, EdiRoot)
        assert len(result.interchanges) == 1
        
        interchange = result.interchanges[0]
        assert interchange.header["sender_id"] == "SENDER"
        assert interchange.header["receiver_id"] == "RECEIVER"
        
        assert len(interchange.functional_groups) == 1
        functional_group = interchange.functional_groups[0]
        
        assert len(functional_group.transactions) == 1
        transaction = functional_group.transactions[0]
        assert transaction.header["transaction_set_code"] == "835"
        
        # Verify transaction data is present and correct type
        assert transaction.transaction_data is not None
        assert hasattr(transaction.transaction_data, 'financial_information')

    def test_plugin_validation(self):
        """Test plugin segment validation."""
        plugin = Plugin835()
        
        # Valid segments
        valid_segments = [
            ["ISA", "00", "", "00", "", "ZZ", "SENDER", "ZZ", "RECEIVER", "241226", "1430", "U", "00501", "000000001", "0", "P", ">"],
            ["ST", "835", "0001"],
            ["BPR", "I", "1000.00", "C", "ACH", "", "", "", "", "", "", "20241226"],
        ]
        
        # Invalid segments (empty)
        invalid_segments = []
        
        assert plugin.validate_segments(valid_segments) == True
        assert plugin.validate_segments(invalid_segments) == False  # Empty segments are invalid

    def test_factory_isolation(self):
        """Test that factories provide proper isolation."""
        plugin = Plugin835()
        
        # Get factories
        parser_factory1, ast_factory1 = plugin.setup_factories()
        parser_factory2, ast_factory2 = plugin.setup_factories()
        
        # Should be different instances (not singleton)
        assert parser_factory1 is not parser_factory2
        assert ast_factory1 is not ast_factory2
        
        # But should have same configuration
        assert parser_factory1.get_supported_codes() == parser_factory2.get_supported_codes()
        assert ast_factory1.get_transaction_class() == ast_factory2.get_transaction_class()

    def test_plugin_transaction_class_access(self):
        """Test that plugin provides correct transaction class."""
        plugin = Plugin835()
        
        transaction_class = plugin.get_transaction_class()
        
        # Should be Transaction835
        assert transaction_class.__name__ == "Transaction835"
        
        # Should be able to instantiate
        instance = transaction_class(header={"test": "value"})
        assert hasattr(instance, 'header')
        assert instance.header["test"] == "value"

    def test_multiple_transaction_codes(self):
        """Test plugins that handle multiple transaction codes."""
        from packages.core.plugins.implementations.plugin_270_271 import Plugin270271
        
        plugin = Plugin270271()
        
        assert set(plugin.transaction_codes) == {"270", "271"}
        assert plugin.plugin_name == "EDI-270-271-Parser"

    def test_plugin_error_handling(self):
        """Test plugin error handling for invalid data."""
        plugin = Plugin835()
        
        # Malformed segments should not crash the plugin
        malformed_segments = [
            ["ISA"],  # Incomplete segment
            ["INVALID"],  # Unknown segment type
        ]
        
        # Should handle gracefully
        result = plugin.parse(malformed_segments)
        assert isinstance(result, EdiRoot)

    def test_plugin_manager_transaction_lookup(self):
        """Test that plugin manager correctly routes transaction codes to plugins."""
        manager = PluginManager()
        manager.load_builtin_plugins()
        
        # Test each transaction code maps to correct plugin
        test_cases = [
            ("835", "EDI-835-Parser"),
            ("837", "EDI-837P-Parser"),
            ("270", "EDI-270-271-Parser"),
            ("271", "EDI-270-271-Parser"),
            ("276", "EDI-276-277-Parser"),
            ("277", "EDI-276-277-Parser"),
        ]
        
        for transaction_code, expected_plugin in test_cases:
            plugin = manager.registry.get_parser_for_transaction(transaction_code)
            assert plugin is not None, f"No plugin found for {transaction_code}"
            assert plugin.plugin_name == expected_plugin, f"Wrong plugin for {transaction_code}"
        
        # Test unknown transaction code
        unknown_plugin = manager.registry.get_parser_for_transaction("999")
        assert unknown_plugin is None