"""
Improved Base Plugin Architecture

This module provides base plugin classes that use factory patterns
to reduce direct dependencies on core implementations.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, Type
from .api import TransactionParserPlugin
from .factory import TransactionParserFactory, ASTNodeFactory, plugin_context
from ..base.edi_ast import EdiRoot


class FactoryBasedPlugin(TransactionParserPlugin):
    """Base plugin class using factory pattern for reduced coupling."""
    
    def __init__(self, 
                 transaction_codes: List[str],
                 plugin_name: str,
                 plugin_version: str = "1.0.0",
                 schema_path: Optional[str] = None):
        self._transaction_codes = transaction_codes
        self._plugin_name = plugin_name
        self._plugin_version = plugin_version
        self._schema_path = schema_path
        self._parser_factory: Optional[TransactionParserFactory] = None
        self._ast_factory: Optional[ASTNodeFactory] = None
    
    @property
    def transaction_codes(self) -> List[str]:
        """Return transaction codes this plugin handles."""
        return self._transaction_codes.copy()
    
    @property
    def plugin_name(self) -> str:
        """Return plugin name."""
        return self._plugin_name
    
    @property
    def plugin_version(self) -> str:
        """Return plugin version."""
        return self._plugin_version
    
    def get_schema_path(self) -> Optional[str]:
        """Return schema path."""
        return self._schema_path
    
    @abstractmethod
    def setup_factories(self) -> tuple[TransactionParserFactory, ASTNodeFactory]:
        """Setup and return the parser and AST factories for this plugin."""
        pass
    
    def _ensure_factories(self):
        """Ensure factories are initialized."""
        if self._parser_factory is None or self._ast_factory is None:
            self._parser_factory, self._ast_factory = self.setup_factories()
    
    def get_transaction_class(self) -> Type:
        """Return the transaction-specific AST class."""
        self._ensure_factories()
        return self._ast_factory.get_transaction_class()
    
    def parse(self, segments: List[List[str]]) -> EdiRoot:
        """Parse EDI segments using factory-created parser."""
        self._ensure_factories()
        
        # Create parser using factory
        parser = self._parser_factory.create_parser(segments)
        
        # Parse using the factory-created parser
        return parser.parse()
    
    def validate_segments(self, segments: List[List[str]]) -> bool:
        """Validate segments using factory-created parser."""
        self._ensure_factories()
        
        # Create parser for validation
        parser = self._parser_factory.create_parser(segments)
        
        # Use parser's validation if available
        if hasattr(parser, 'validate_segments'):
            return parser.validate_segments(segments)
        
        return True


class SimpleParserPlugin(FactoryBasedPlugin):
    """Simple plugin implementation for straightforward parser integration."""
    
    def __init__(self,
                 parser_class: Type,
                 transaction_class: Type,
                 transaction_codes: List[str],
                 plugin_name: str,
                 plugin_version: str = "1.0.0",
                 schema_path: Optional[str] = None):
        super().__init__(transaction_codes, plugin_name, plugin_version, schema_path)
        self.parser_class = parser_class
        self.transaction_class = transaction_class
    
    def setup_factories(self) -> tuple[TransactionParserFactory, ASTNodeFactory]:
        """Setup factories using provided classes."""
        from .factory import GenericTransactionParserFactory, GenericASTNodeFactory
        
        parser_factory = GenericTransactionParserFactory(
            self.parser_class, 
            self.transaction_codes
        )
        
        ast_factory = GenericASTNodeFactory(self.transaction_class)
        
        return parser_factory, ast_factory


class ConfigurablePlugin(FactoryBasedPlugin):
    """Plugin with configurable behavior through dependency injection."""
    
    def __init__(self,
                 config: Dict[str, Any],
                 factory_provider: callable):
        """
        Create plugin from configuration.
        
        Args:
            config: Plugin configuration dictionary
            factory_provider: Function that returns (parser_factory, ast_factory) tuple
        """
        super().__init__(
            transaction_codes=config.get('transaction_codes', []),
            plugin_name=config.get('plugin_name', 'Unknown'),
            plugin_version=config.get('plugin_version', '1.0.0'),
            schema_path=config.get('schema_path')
        )
        self.config = config
        self.factory_provider = factory_provider
    
    def setup_factories(self) -> tuple[TransactionParserFactory, ASTNodeFactory]:
        """Setup factories using injected provider."""
        return self.factory_provider(self.config)


class PluginMetadata:
    """Metadata container for plugin information."""
    
    def __init__(self,
                 name: str,
                 version: str,
                 description: str,
                 author: str,
                 transaction_codes: List[str],
                 dependencies: List[str] = None,
                 schema_path: Optional[str] = None):
        self.name = name
        self.version = version
        self.description = description
        self.author = author
        self.transaction_codes = transaction_codes
        self.dependencies = dependencies or []
        self.schema_path = schema_path
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert metadata to dictionary."""
        return {
            'name': self.name,
            'version': self.version,
            'description': self.description,
            'author': self.author,
            'transaction_codes': self.transaction_codes,
            'dependencies': self.dependencies,
            'schema_path': self.schema_path
        }


class PluginLoader:
    """Utility for loading plugins with dependency management."""
    
    def __init__(self, plugin_context=None):
        self.context = plugin_context or plugin_context
        self.loaded_plugins: Dict[str, TransactionParserPlugin] = {}
        self.failed_plugins: Dict[str, str] = {}  # name -> error message
    
    def load_plugin_from_metadata(self, metadata: PluginMetadata, factory_provider: callable) -> bool:
        """Load a plugin from metadata and factory provider."""
        try:
            # Check dependencies
            for dep in metadata.dependencies:
                if dep not in self.loaded_plugins:
                    raise ValueError(f"Missing dependency: {dep}")
            
            # Create plugin configuration
            config = metadata.to_dict()
            
            # Create plugin
            plugin = ConfigurablePlugin(config, factory_provider)
            
            # Validate plugin works
            if not plugin.transaction_codes:
                raise ValueError("Plugin must specify transaction codes")
            
            self.loaded_plugins[metadata.name] = plugin
            return True
            
        except Exception as e:
            self.failed_plugins[metadata.name] = str(e)
            return False
    
    def get_load_summary(self) -> Dict[str, Any]:
        """Get summary of plugin loading results."""
        return {
            'loaded': list(self.loaded_plugins.keys()),
            'failed': self.failed_plugins,
            'total_attempted': len(self.loaded_plugins) + len(self.failed_plugins),
            'success_rate': len(self.loaded_plugins) / max(1, len(self.loaded_plugins) + len(self.failed_plugins))
        }