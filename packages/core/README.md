# EDI CLI Core Package

## Overview

The EDI CLI Core package provides a comprehensive framework for parsing, validating, and processing EDI (Electronic Data Interchange) transactions. This package has been refactored to provide a modular, extensible architecture with standardized error handling and plugin support.

## Architecture

### Core Components

#### 1. AST (Abstract Syntax Tree) - `packages/core/base/`
- **`edi_ast.py`**: Unified AST classes for representing EDI documents
- **`parser.py`**: Base parser interface for EDI transactions
- **`enhanced_parser.py`**: Enhanced parser with integrated error handling

#### 2. Error Handling - `packages/core/errors/`
- **`exceptions.py`**: Standardized exception hierarchy for EDI processing
- **`context.py`**: Error context classes for detailed error information
- **`handler.py`**: Error handler implementations (Standard, Silent, FailFast, Filtering)

#### 3. Validation Framework - `packages/core/validation/`
- **`engine.py`**: Core validation engine with rule management
- **`rules.py`**: Base validation rule classes and context
- **`factory.py`**: Factory pattern for validation rule creation
- **`integration.py`**: Integration between validation and plugin systems

#### 4. Plugin Architecture - `packages/core/plugins/`
- **`base_plugin.py`**: Base plugin classes and factory-based plugins
- **`factory.py`**: Factory interfaces for reducing plugin dependencies
- **`plugin_835.py`**: Specialized plugin for 835 transactions

#### 5. Transaction Parsers - `packages/core/transactions/`
- **`t270/`**: 270/271 Eligibility Inquiry/Response parsers
- **`t276/`**: 276/277 Claim Status Request/Response parsers
- **`t835/`**: 835 Healthcare Claim Payment/Advice parsers
- **`t837p/`**: 837P Professional Claim parsers

#### 6. Interfaces - `packages/core/interfaces/`
- **`parser_interface.py`**: Standardized parser interfaces and registry

#### 7. Utilities - `packages/core/utils/`
- **`helpers.py`**: Common utility functions for EDI processing

## Key Features

### 1. Unified AST Design
The AST has been refactored to use a unified `Transaction` class that can handle any transaction type through a generic `transaction_data` field, while maintaining backward compatibility.

```python
from packages.core.base.edi_ast import Transaction

# Generic transaction container
transaction = Transaction(
    transaction_set_code="835",
    control_number="0001",
    transaction_data=transaction_835_data
)
```

### 2. Comprehensive Error Handling
Standardized error handling system with multiple handler types:

```python
from packages.core.errors import (
    StandardErrorHandler, 
    EDIParseError, 
    create_parse_context
)

# Create error handler
handler = StandardErrorHandler(log_errors=True, raise_on_error=False)

# Create error context
context = create_parse_context().operation("parsing").component("Parser835").build()

# Handle errors
try:
    # parsing logic
    pass
except Exception as e:
    error = EDIParseError("Parsing failed", {"line": 1})
    handler.handle_error(error, context)
```

### 3. Enhanced Parser Interface
Parsers can now inherit from `EnhancedParser` for automatic error handling integration:

```python
from packages.core.base.enhanced_parser import EnhancedParser

class MyParser(EnhancedParser):
    def get_transaction_codes(self):
        return ["999"]
    
    def parse(self):
        # Use built-in error handling methods
        segment = self._validate_required_segment("ST", "transaction header")
        value = self._safe_parse_element(segment, 1, "transaction_code", 0)
        return {"transaction_code": value}
```

### 4. Factory-Based Plugin Architecture
Reduced coupling between plugins through factory patterns:

```python
from packages.core.plugins.factory import TransactionParserFactory
from packages.core.plugins.base_plugin import FactoryBasedPlugin

class MyPlugin(FactoryBasedPlugin):
    def __init__(self, parser_factory: TransactionParserFactory):
        super().__init__(parser_factory)
    
    def get_transaction_codes(self):
        return ["999"]
```

### 5. Integrated Validation System
Comprehensive validation with business rules:

```python
from packages.core.validation import ValidationEngine
from packages.core.validation.integration import parse_and_validate

# Parse and validate in one step
result = parse_and_validate(
    segments=edi_segments,
    transaction_code="835",
    validation_rules=["structure", "data", "business"]
)
```

## Usage Examples

### Basic Parsing

```python
from packages.core.transactions.t835.parser import Parser835

segments = [
    ["ISA", "00", "", "00", "", "ZZ", "SENDER", "ZZ", "RECEIVER", "250101", "1200", "U", "00401", "000000001", "0", "P", ">"],
    ["GS", "HP", "SENDER", "RECEIVER", "20250101", "1200", "1", "X", "005010X221A1"],
    ["ST", "835", "0001"],
    ["BPR", "C", "1000.00", "C", "ACH"],
    ["SE", "3", "0001"],
    ["GE", "1", "1"],
    ["IEA", "1", "000000001"]
]

parser = Parser835(segments)
edi_root = parser.parse()
```

### Enhanced Parsing with Error Handling

```python
from packages.core.transactions.t835.parser import Parser835
from packages.core.errors import StandardErrorHandler

# Create parser with custom error handler
handler = StandardErrorHandler(log_errors=True, max_errors=10)
parser = Parser835(segments, handler)

# Parse with comprehensive error reporting
result = parser.parse_with_error_handling()
if result:
    print("Parsing successful")
else:
    errors = parser.get_error_summary()
    print(f"Parsing failed with {errors['total_errors']} errors")
```

### Plugin Usage

```python
from packages.core.plugins.plugin_835 import Plugin835
from packages.core.plugins.factory import GenericTransactionParserFactory

# Create plugin with factory
factory = GenericTransactionParserFactory()
plugin = Plugin835(factory)

# Use plugin for parsing
result = plugin.parse_transaction(segments)
```

### Validation

```python
from packages.core.validation import ValidationEngine
from packages.core.validation.rules_835 import Transaction835StructureRule

# Create validation engine
engine = ValidationEngine()
engine.register_rule(Transaction835StructureRule())

# Validate parsed transaction
validation_result = engine.validate(parsed_transaction)
if validation_result.is_valid:
    print("Validation passed")
else:
    for error in validation_result.errors:
        print(f"Error: {error.message}")
```

## Migration Guide

### From Previous Versions

1. **AST Changes**: The old multiple container fields in Transaction class have been replaced with a single `transaction_data` field. Legacy code continues to work through backward compatibility.

2. **Error Handling**: Replace manual error handling with the standardized error handling system:
   ```python
   # Old
   try:
       # parsing logic
   except Exception as e:
       logger.error(f"Parsing failed: {e}")
   
   # New
   from packages.core.errors import StandardErrorHandler
   handler = StandardErrorHandler()
   # Use enhanced parser or manual error handling
   ```

3. **Plugin Architecture**: Update plugins to use factory pattern for reduced dependencies.

## Testing

The package includes comprehensive tests in `tests/core/`:

```bash
# Run all core tests
python -m pytest tests/core/ -v

# Run specific test modules
python -m pytest tests/core/test_error_handling.py -v
python -m pytest tests/core/test_validation.py -v
python -m pytest tests/core/test_plugins.py -v
```

## Contributing

When adding new features:

1. Follow the established patterns for error handling
2. Use the factory pattern for reducing dependencies
3. Add comprehensive tests for new functionality
4. Update documentation as needed

## Future Enhancements

- Additional transaction type support
- Performance optimizations
- Enhanced validation rules
- Improved error recovery mechanisms
- Plugin hot-loading capabilities