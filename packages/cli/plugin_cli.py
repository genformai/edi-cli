#!/usr/bin/env python3
"""
Plugin CLI for EDI-CLI Plugin Management

This module provides command-line tools for managing EDI transaction parser plugins,
including listing, loading, and creating custom plugins.
"""

import sys
import os
import json
from pathlib import Path
from typing import Dict, Any, Optional, List

# Add parent directory to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from core.plugins.api import PluginManager, plugin_registry
from core.plugins.base_plugin import SimpleParserPlugin, PluginMetadata, PluginLoader


def list_plugins_command():
    """List all registered plugins."""
    print("🔌 EDI Plugin Registry\n")
    
    # Load built-in plugins first
    manager = PluginManager()
    manager.load_builtin_plugins()
    
    # List transaction parsers
    parsers = plugin_registry.list_registered_parsers()
    if parsers:
        print("📊 Transaction Parser Plugins:")
        for name, info in parsers.items():
            print(f"  • {name} v{info['version']}")
            print(f"    Transaction Codes: {', '.join(info['transaction_codes'])}")
            if info['schema_path']:
                print(f"    Schema: {info['schema_path']}")
            print()
    else:
        print("❌ No transaction parser plugins registered")
    
    # List validation rules  
    validation_rules = plugin_registry.list_registered_validation_rules()
    if validation_rules:
        print("🔍 Validation Rule Plugins:")
        for transaction_code, rules in validation_rules.items():
            print(f"  • {transaction_code}: {', '.join(rules)}")
    else:
        print("❌ No validation rule plugins registered")


def load_plugin_command(plugin_path: str, class_name: str):
    """Load a custom plugin from file."""
    try:
        if not os.path.exists(plugin_path):
            print(f"❌ Plugin file not found: {plugin_path}")
            return 1
        
        # Add plugin directory to Python path
        plugin_dir = os.path.dirname(os.path.abspath(plugin_path))
        if plugin_dir not in sys.path:
            sys.path.insert(0, plugin_dir)
        
        # Extract module name from file
        module_name = os.path.splitext(os.path.basename(plugin_path))[0]
        
        manager = PluginManager()
        manager.load_plugin_from_module(module_name, class_name)
        
        print(f"✅ Successfully loaded plugin {class_name} from {plugin_path}")
        return 0
        
    except Exception as e:
        print(f"❌ Failed to load plugin: {e}")
        return 1


def discover_plugins_command(plugin_directory: str):
    """Discover and load all plugins in a directory."""
    try:
        manager = PluginManager()
        manager.discover_plugins(plugin_directory)
        return 0
        
    except Exception as e:
        print(f"❌ Failed to discover plugins: {e}")
        return 1


def create_plugin_template_command(plugin_name: str, transaction_codes: List[str], output_path: str):
    """Create a template plugin file."""
    try:
        template_content = f'''"""
Custom EDI Transaction Parser Plugin: {plugin_name}

This is a template plugin for parsing EDI transactions {', '.join(transaction_codes)}.
Customize the parsing logic in the parse_transaction method.
"""

from typing import List, Dict, Any, Type
import sys
import os

# Add packages to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from core.plugins.base_plugin import SimpleParserPlugin
from core.base.parser import BaseParser
from core.base.edi_ast import EdiRoot, Interchange, FunctionalGroup, Transaction, Node
from dataclasses import dataclass


@dataclass
class {plugin_name}Transaction(Node):
    """AST node for {plugin_name} transaction data."""
    header: Dict[str, str]
    # Add your custom fields here
    custom_field: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        return {{
            "header": self.header,
            "custom_field": self.custom_field
        }}


class {plugin_name}Parser(BaseParser):
    """Parser for {plugin_name} transactions."""
    
    def get_transaction_codes(self) -> List[str]:
        return {transaction_codes}
    
    def parse(self) -> EdiRoot:
        """Parse the transaction and return EdiRoot structure."""
        # Extract transaction type from ST segment
        st_segment = self._find_segment("ST")
        transaction_code = st_segment[1] if st_segment and len(st_segment) > 1 else ""
        
        # Parse your transaction data
        transaction_data = self._parse_transaction(transaction_code)
        
        # Wrap in EdiRoot structure
        return self._wrap_in_edi_structure(transaction_data)
    
    def _parse_transaction(self, transaction_code: str) -> {plugin_name}Transaction:
        """Parse transaction-specific data."""
        # Parse header
        header = {{}}
        st_segment = self._find_segment("ST")
        if st_segment:
            header["transaction_set_identifier"] = st_segment[1] if len(st_segment) > 1 else ""
            header["transaction_set_control_number"] = st_segment[2] if len(st_segment) > 2 else ""
        
        # Create transaction object
        transaction = {plugin_name}Transaction(header=header)
        
        # TODO: Add your custom parsing logic here
        # Example: Parse specific segments for your transaction type
        # custom_segments = self._find_all_segments("YOUR_SEGMENT_ID")
        # transaction.custom_field = self._process_custom_segments(custom_segments)
        
        return transaction
    
    def _wrap_in_edi_structure(self, transaction_data) -> EdiRoot:
        """Wrap parsed data in EDI envelope structure."""
        root = EdiRoot()
        
        # Create basic envelope structure
        isa_segment = self._find_segment("ISA")
        gs_segment = self._find_segment("GS") 
        st_segment = self._find_segment("ST")
        
        # Create interchange
        if isa_segment:
            interchange = Interchange(
                sender_id=isa_segment[6] if len(isa_segment) > 6 else "",
                receiver_id=isa_segment[8] if len(isa_segment) > 8 else "",
                date=isa_segment[9] if len(isa_segment) > 9 else "",
                time=isa_segment[10] if len(isa_segment) > 10 else "",
                control_number=isa_segment[13] if len(isa_segment) > 13 else ""
            )
        else:
            interchange = Interchange("", "", "", "", "")
        
        # Create functional group
        if gs_segment:
            functional_group = FunctionalGroup(
                functional_group_code=gs_segment[1] if len(gs_segment) > 1 else "",
                sender_id=gs_segment[2] if len(gs_segment) > 2 else "",
                receiver_id=gs_segment[3] if len(gs_segment) > 3 else "",
                date=gs_segment[4] if len(gs_segment) > 4 else "",
                time=gs_segment[5] if len(gs_segment) > 5 else "",
                control_number=gs_segment[6] if len(gs_segment) > 6 else ""
            )
        else:
            functional_group = FunctionalGroup("", "", "", "", "", "")
        
        # Create transaction wrapper
        if st_segment:
            transaction = Transaction(
                transaction_set_code=st_segment[1] if len(st_segment) > 1 else "",
                control_number=st_segment[2] if len(st_segment) > 2 else "",
                transaction_data=transaction_data
            )
        else:
            transaction = Transaction("", "", transaction_data)
        
        # Assemble structure
        functional_group.transactions.append(transaction)
        interchange.functional_groups.append(functional_group)
        root.interchanges.append(interchange)
        
        return root


class {plugin_name}Plugin(SimpleParserPlugin):
    """Plugin wrapper for {plugin_name} parser."""
    
    def __init__(self):
        super().__init__(
            parser_class={plugin_name}Parser,
            transaction_class={plugin_name}Transaction,
            transaction_codes={transaction_codes},
            plugin_name="{plugin_name}",
            plugin_version="1.0.0"
        )


# Export the plugin class for automatic discovery
__all__ = ['{plugin_name}Plugin']
'''

        with open(output_path, 'w') as f:
            f.write(template_content)
        
        print(f"✅ Created plugin template: {output_path}")
        print(f"📝 Edit the file to customize parsing logic for {', '.join(transaction_codes)} transactions")
        print(f"🔌 Load with: edi plugin load {output_path} {plugin_name}Plugin")
        return 0
        
    except Exception as e:
        print(f"❌ Failed to create plugin template: {e}")
        return 1


def validate_plugin_command(plugin_path: str, class_name: str):
    """Validate a plugin without loading it into the registry."""
    try:
        # Basic file validation
        if not os.path.exists(plugin_path):
            print(f"❌ Plugin file not found: {plugin_path}")
            return 1
        
        # Add plugin directory to Python path temporarily
        plugin_dir = os.path.dirname(os.path.abspath(plugin_path))
        if plugin_dir not in sys.path:
            sys.path.insert(0, plugin_dir)
        
        # Try to import and validate
        module_name = os.path.splitext(os.path.basename(plugin_path))[0]
        
        import importlib
        module = importlib.import_module(module_name)
        plugin_class = getattr(module, class_name)
        plugin_instance = plugin_class()
        
        # Validate plugin interface
        from core.plugins.api import TransactionParserPlugin, ValidationRulePlugin
        
        if isinstance(plugin_instance, TransactionParserPlugin):
            print("✅ Valid TransactionParserPlugin")
            print(f"   Plugin Name: {plugin_instance.plugin_name}")
            print(f"   Version: {plugin_instance.plugin_version}")
            print(f"   Transaction Codes: {', '.join(plugin_instance.transaction_codes)}")
            
            # Test basic functionality
            try:
                transaction_class = plugin_instance.get_transaction_class()
                print(f"   Transaction Class: {transaction_class.__name__}")
            except Exception as e:
                print(f"⚠️  Warning: Could not get transaction class: {e}")
            
        elif isinstance(plugin_instance, ValidationRulePlugin):
            print("✅ Valid ValidationRulePlugin")
            print(f"   Rule Name: {plugin_instance.rule_name}")
            print(f"   Supported Transactions: {', '.join(plugin_instance.supported_transactions)}")
        else:
            print("❌ Plugin must implement TransactionParserPlugin or ValidationRulePlugin")
            return 1
        
        print("✅ Plugin validation successful")
        return 0
        
    except Exception as e:
        print(f"❌ Plugin validation failed: {e}")
        return 1


def main():
    """Main plugin CLI entry point."""
    if len(sys.argv) < 2:
        print("EDI Plugin Manager")
        print("")
        print("Usage:")
        print("  edi plugin list                                    - List all plugins")
        print("  edi plugin load <path> <class>                     - Load plugin from file")
        print("  edi plugin discover <directory>                    - Discover plugins in directory")
        print("  edi plugin create <name> <codes> <output>          - Create plugin template")
        print("  edi plugin validate <path> <class>                 - Validate plugin file")
        print("")
        print("Examples:")
        print("  edi plugin list")
        print("  edi plugin load ./my_plugin.py MyPlugin")
        print("  edi plugin create MyCustom850Plugin 850 ./custom_850_plugin.py")
        print("  edi plugin validate ./my_plugin.py MyPlugin")
        return 1
    
    command = sys.argv[1].lower()
    
    if command == "list":
        return list_plugins_command()
    
    elif command == "load":
        if len(sys.argv) < 4:
            print("❌ Usage: edi plugin load <path> <class>")
            return 1
        return load_plugin_command(sys.argv[2], sys.argv[3])
    
    elif command == "discover":
        if len(sys.argv) < 3:
            print("❌ Usage: edi plugin discover <directory>")
            return 1
        return discover_plugins_command(sys.argv[2])
    
    elif command == "create":
        if len(sys.argv) < 5:
            print("❌ Usage: edi plugin create <name> <transaction_codes> <output_path>")
            print("   Example: edi plugin create MyCustom850Plugin 850,855 ./my_plugin.py")
            return 1
        
        plugin_name = sys.argv[2]
        transaction_codes = sys.argv[3].split(',')
        output_path = sys.argv[4]
        
        return create_plugin_template_command(plugin_name, transaction_codes, output_path)
    
    elif command == "validate":
        if len(sys.argv) < 4:
            print("❌ Usage: edi plugin validate <path> <class>")
            return 1
        return validate_plugin_command(sys.argv[2], sys.argv[3])
    
    else:
        print(f"❌ Unknown command: {command}")
        print("Available commands: list, load, discover, create, validate")
        return 1


if __name__ == "__main__":
    sys.exit(main())