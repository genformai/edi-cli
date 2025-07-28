# EDI Core Library

The shared core library providing EDI parsing, validation, and analysis capabilities used by all EDI CLI applications.

## Features

- **Transaction Parsers** - Support for X12 835, 837P, 270/271, 276/277 transaction sets
- **Validation Engine** - YAML-based rule system with HIPAA compliance  
- **Plugin Architecture** - Extensible system for custom transaction types
- **AST Generation** - Rich abstract syntax trees for parsed EDI data
- **Performance Optimized** - Fast parsing with minimal memory usage

## Usage

### Basic Parsing

```python
from core.transactions.t835.parser import Parser835

# Parse EDI content
with open('sample-835.edi', 'r') as f:
    content = f.read()

parser = Parser835()
result = parser.parse(content)

# Access parsed data
transaction = result.interchanges[0].functional_groups[0].transactions[0]
payment_data = transaction.transaction_data

print(f"Payer: {payment_data.payer.name}")
print(f"Total Paid: ${payment_data.financial_information.total_paid}")
```

### Installation

```bash
# Install in development mode
cd core
pip install -e .
```

See individual application READMEs for integration examples.