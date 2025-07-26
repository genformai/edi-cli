"""
Plugin API Architecture for EDI Transaction Sets

This module defines the plugin interface and registry system for extending
the EDI parser with custom transaction sets.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, Type, Protocol
from .ast import EdiRoot, Transaction


class TransactionParserPlugin(ABC):
    """Abstract base class for transaction parser plugins."""
    
    @property
    @abstractmethod
    def transaction_codes(self) -> List[str]:
        """Return list of transaction codes this plugin handles."""
        pass
    
    @property
    @abstractmethod
    def plugin_name(self) -> str:
        """Return the name of this plugin."""
        pass
    
    @property 
    @abstractmethod
    def plugin_version(self) -> str:
        """Return the version of this plugin."""
        pass
    
    @abstractmethod
    def parse(self, segments: List[List[str]]) -> EdiRoot:
        """Parse EDI segments into an AST structure."""
        pass
    
    @abstractmethod
    def get_transaction_class(self) -> Type:
        """Return the transaction-specific AST class."""
        pass
    
    def validate_segments(self, segments: List[List[str]]) -> bool:
        """Optional: Validate segments before parsing. Default implementation returns True."""
        return True
    
    def get_schema_path(self) -> Optional[str]:
        """Optional: Return path to JSON schema for this transaction type."""
        return None


class ValidationRulePlugin(ABC):
    """Abstract base class for validation rule plugins."""
    
    @property
    @abstractmethod
    def rule_name(self) -> str:
        """Return the name of this validation rule."""
        pass
    
    @property
    @abstractmethod
    def supported_transactions(self) -> List[str]:
        """Return list of transaction codes this rule applies to."""
        pass
    
    @abstractmethod
    def validate(self, edi_root: EdiRoot, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Validate the EDI document and return list of validation errors."""
        pass


class PluginRegistry:
    """Registry for managing transaction parser and validation plugins."""
    
    def __init__(self):
        self._transaction_parsers: Dict[str, TransactionParserPlugin] = {}
        self._validation_rules: Dict[str, List[ValidationRulePlugin]] = {}
        self._plugins_by_name: Dict[str, TransactionParserPlugin] = {}
    
    def register_transaction_parser(self, plugin: TransactionParserPlugin):
        """Register a transaction parser plugin."""
        for transaction_code in plugin.transaction_codes:
            if transaction_code in self._transaction_parsers:
                raise ValueError(f"Transaction code {transaction_code} is already registered")
            self._transaction_parsers[transaction_code] = plugin
        
        self._plugins_by_name[plugin.plugin_name] = plugin
        print(f"Registered transaction parser plugin: {plugin.plugin_name} v{plugin.plugin_version}")
    
    def register_validation_rule(self, plugin: ValidationRulePlugin):
        """Register a validation rule plugin."""
        for transaction_code in plugin.supported_transactions:
            if transaction_code not in self._validation_rules:
                self._validation_rules[transaction_code] = []
            self._validation_rules[transaction_code].append(plugin)
        
        print(f"Registered validation rule plugin: {plugin.rule_name}")
    
    def get_parser_for_transaction(self, transaction_code: str) -> Optional[TransactionParserPlugin]:
        """Get the parser plugin for a specific transaction code."""
        return self._transaction_parsers.get(transaction_code)
    
    def get_validation_rules_for_transaction(self, transaction_code: str) -> List[ValidationRulePlugin]:
        """Get all validation rules for a specific transaction code."""
        return self._validation_rules.get(transaction_code, [])
    
    def list_registered_parsers(self) -> Dict[str, Dict[str, Any]]:
        """List all registered parser plugins with their metadata."""
        result = {}
        for plugin in self._plugins_by_name.values():
            result[plugin.plugin_name] = {
                "version": plugin.plugin_version,
                "transaction_codes": plugin.transaction_codes,
                "schema_path": plugin.get_schema_path()
            }
        return result
    
    def list_registered_validation_rules(self) -> Dict[str, List[str]]:
        """List all registered validation rules by transaction code."""
        result = {}
        for transaction_code, rules in self._validation_rules.items():
            result[transaction_code] = [rule.rule_name for rule in rules]
        return result
    
    def unregister_parser(self, plugin_name: str):
        """Unregister a parser plugin by name."""
        if plugin_name not in self._plugins_by_name:
            raise ValueError(f"Plugin {plugin_name} is not registered")
        
        plugin = self._plugins_by_name[plugin_name]
        for transaction_code in plugin.transaction_codes:
            if transaction_code in self._transaction_parsers:
                del self._transaction_parsers[transaction_code]
        
        del self._plugins_by_name[plugin_name]
        print(f"Unregistered transaction parser plugin: {plugin_name}")


# Global plugin registry instance
plugin_registry = PluginRegistry()


class PluginManager:
    """Manager for loading and configuring plugins."""
    
    def __init__(self, registry: PluginRegistry = None):
        self.registry = registry or plugin_registry
    
    def load_builtin_plugins(self):
        """Load all built-in transaction parser plugins."""
        from .plugins.plugin_835 import Plugin835
        from .plugins.plugin_837p import Plugin837P
        from .plugins.plugin_270_271 import Plugin270271
        from .plugins.plugin_276_277 import Plugin276277
        
        # Register built-in parsers
        self.registry.register_transaction_parser(Plugin835())
        self.registry.register_transaction_parser(Plugin837P())
        self.registry.register_transaction_parser(Plugin270271())
        self.registry.register_transaction_parser(Plugin276277())
        
        print("Loaded all built-in transaction parser plugins")
    
    def load_plugin_from_module(self, module_path: str, class_name: str):
        """Dynamically load a plugin from a module path."""
        import importlib
        
        try:
            module = importlib.import_module(module_path)
            plugin_class = getattr(module, class_name)
            plugin_instance = plugin_class()
            
            if isinstance(plugin_instance, TransactionParserPlugin):
                self.registry.register_transaction_parser(plugin_instance)
            elif isinstance(plugin_instance, ValidationRulePlugin):
                self.registry.register_validation_rule(plugin_instance)
            else:
                raise ValueError(f"Plugin {class_name} must implement TransactionParserPlugin or ValidationRulePlugin")
        
        except Exception as e:
            print(f"Failed to load plugin {class_name} from {module_path}: {e}")
            raise
    
    def discover_plugins(self, plugin_directory: str):
        """Discover and load plugins from a directory."""
        import os
        import importlib.util
        
        if not os.path.exists(plugin_directory):
            print(f"Plugin directory {plugin_directory} does not exist")
            return
        
        for filename in os.listdir(plugin_directory):
            if filename.endswith('.py') and not filename.startswith('__'):
                module_path = os.path.join(plugin_directory, filename)
                module_name = filename[:-3]  # Remove .py extension
                
                try:
                    spec = importlib.util.spec_from_file_location(module_name, module_path)
                    module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(module)
                    
                    # Look for plugin classes in the module
                    for attr_name in dir(module):
                        attr = getattr(module, attr_name)
                        if (isinstance(attr, type) and 
                            (issubclass(attr, TransactionParserPlugin) or issubclass(attr, ValidationRulePlugin)) and
                            attr not in [TransactionParserPlugin, ValidationRulePlugin]):
                            
                            plugin_instance = attr()
                            if isinstance(plugin_instance, TransactionParserPlugin):
                                self.registry.register_transaction_parser(plugin_instance)
                            elif isinstance(plugin_instance, ValidationRulePlugin):
                                self.registry.register_validation_rule(plugin_instance)
                
                except Exception as e:
                    print(f"Failed to load plugin from {filename}: {e}")
        
        print(f"Plugin discovery completed in {plugin_directory}")