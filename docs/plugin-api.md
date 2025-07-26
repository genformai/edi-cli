# Plugin API

This document describes the plugin API for `edi-cli`, which allows you to extend its functionality with new transaction sets and custom logic.

## Creating a Plugin

To create a plugin, you will need to create a new Python package that includes a `setup.py` file. The package should contain a module that defines a `register` function. This function will be called by `edi-cli` to register your plugin.

### Example

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
