# EDI-CLI Plugin API Documentation

The EDI-CLI plugin system allows developers to easily extend the toolkit with support for custom EDI transaction sets without modifying the core codebase.

## Quick Start

### 1. Create a Plugin Template

```bash
edi plugin create MyCustom850Plugin 850 ./my_850_plugin.py
```

This generates a complete plugin template with:
- Parser class with EDI segment processing
- AST (Abstract Syntax Tree) data structures  
- Plugin wrapper for registration
- Full CLI integration

### 2. Customize the Plugin

Edit the generated file to implement your transaction-specific logic:

```python
def _parse_transaction(self, transaction_code: str) -> MyCustom850Transaction:
    """Parse transaction-specific data."""
    # Add your custom parsing logic here
    # Example: Parse BEG segment for purchase orders
    beg_segment = self._find_segment("BEG")
    # Process other segments specific to your transaction
```

### 3. Load and Use the Plugin

```bash
# Validate the plugin
edi plugin validate ./my_850_plugin.py MyCustom850Plugin

# Load the plugin
edi plugin load ./my_850_plugin.py MyCustom850Plugin  

# Use it to parse EDI files
edi convert sample-850.edi --schema 850 --to json
```

## Plugin Architecture

### Core Components

1. **Transaction Parser Plugin** - Handles EDI parsing for specific transaction codes
2. **AST Classes** - Define data structures for parsed EDI data
3. **Plugin Registry** - Manages plugin discovery and loading
4. **CLI Integration** - Automatic CLI command support

### Plugin Base Classes

#### `SimpleParserPlugin`
The easiest way to create a plugin:

```python
from core.plugins.base_plugin import SimpleParserPlugin

class MyPlugin(SimpleParserPlugin):
    def __init__(self):
        super().__init__(
            parser_class=MyParser,
            transaction_class=MyTransaction,
            transaction_codes=["850", "855"],
            plugin_name="My-EDI-Plugin",
            plugin_version="1.0.0"
        )
```

#### `FactoryBasedPlugin`
For advanced customization with factory patterns:

```python
from core.plugins.base_plugin import FactoryBasedPlugin

class AdvancedPlugin(FactoryBasedPlugin):
    def setup_factories(self):
        # Return custom parser and AST factories
        return parser_factory, ast_factory
```

## Parser Implementation

### Base Parser Methods

Your parser class must inherit from `BaseParser` and implement:

```python
from core.base.parser import BaseParser
from core.base.edi_ast import EdiRoot

class MyParser(BaseParser):
    def get_transaction_codes(self) -> List[str]:
        return ["850"]  # Transaction codes this parser handles
    
    def parse(self) -> EdiRoot:
        # Parse and return wrapped transaction data
        transaction_data = self._parse_my_transaction()
        return self._wrap_in_edi_structure(transaction_data)
```

### Utility Methods Available

The `BaseParser` provides helpful segment processing methods:

```python
# Find segments
segment = self._find_segment("BEG")           # First BEG segment
segments = self._find_all_segments("PO1")     # All PO1 segments

# Segment navigation  
next_seg = self._find_next_segment("PID", after_segment=po1_segment)
```

## AST Data Structures

### Transaction Class

Define your transaction's data structure:

```python
from dataclasses import dataclass
from core.base.edi_ast import Node

@dataclass
class MyTransaction(Node):
    header: Dict[str, str]
    purchase_order: PurchaseOrderInfo = None
    line_items: List[LineItem] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "header": self.header,
            "purchase_order": self.purchase_order.to_dict() if self.purchase_order else None,
            "line_items": [item.to_dict() for item in self.line_items or []]
        }
```

### Data Classes

Create classes for complex data structures:

```python
@dataclass
class LineItem(Node):
    line_number: str = ""
    quantity: float = 0.0
    unit_price: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "line_number": self.line_number,
            "quantity": self.quantity,
            "unit_price": self.unit_price,
            "total": self.quantity * self.unit_price
        }
```

## CLI Integration

Plugins automatically integrate with CLI commands:

### Convert Command
```bash
edi convert input.edi --schema 850 --to json
```

### Validation
```bash
edi validate input.edi --schema 850 --rule-set basic
```

### Schema Detection
The CLI automatically detects transaction codes from:
1. Schema parameter (`--schema 850`)
2. ST segment in EDI file
3. Plugin registration

## Plugin Management Commands

### List Plugins
```bash
edi plugin list
```

### Load Plugin
```bash
edi plugin load /path/to/plugin.py PluginClass
```

### Discover Plugins
```bash
edi plugin discover /path/to/plugin/directory
```

### Validate Plugin
```bash
edi plugin validate /path/to/plugin.py PluginClass
```

### Create Template
```bash
edi plugin create PluginName transaction_codes output_file.py
```

## Advanced Features

### Validation Rules

Create custom validation plugins:

```python
from core.plugins.api import ValidationRulePlugin

class MyValidationRule(ValidationRulePlugin):
    @property
    def rule_name(self) -> str:
        return "my-custom-rule"
    
    @property 
    def supported_transactions(self) -> List[str]:
        return ["850"]
    
    def validate(self, edi_root: EdiRoot, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        # Return list of validation errors
        return []
```

### Plugin Discovery

Auto-discover plugins in directories:

```python
from core.plugins.api import PluginManager

manager = PluginManager()
manager.discover_plugins('/path/to/plugins')
```

## Example: Complete 850 Plugin

See `examples/plugins/sample_850_plugin.py` for a complete working example that demonstrates:

- Purchase order header parsing
- Line item processing  
- Buyer/seller information extraction
- Product descriptions
- CLI integration
- JSON output formatting

## Best Practices

1. **Follow Naming Conventions**
   - Plugin class: `MyTransactionPlugin`
   - Parser class: `MyTransactionParser`  
   - Transaction class: `MyTransaction`

2. **Error Handling**
   - Use try/catch for segment parsing
   - Provide meaningful error messages
   - Return partial data on non-fatal errors

3. **Performance**
   - Cache segment lookups when possible
   - Use generators for large datasets
   - Minimize memory usage

4. **Testing**
   - Create sample EDI files
   - Test edge cases and malformed data
   - Validate against reference implementations

5. **Documentation**
   - Document custom fields and segments
   - Provide usage examples
   - Include transaction specifications

```python
# my_plugin.py

def register():
    # Register your custom transaction sets here
    pass
```

## Adding a New Transaction Set

To add a new transaction set, you will need to create a new mapping specification as described in the [Mapping Spec](mapping-spec.md) documentation. You can then register the new transaction set in your plugin's `register` function.

### Example

```python
# my_plugin.py

from edi_cli.core import register_transaction_set

def register():
    register_transaction_set("my_transaction_set", "/path/to/my/schema.json")
```
