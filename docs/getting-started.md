# Getting Started

This guide will walk you through the process of installing and using `edi-cli`.

## Installation

To install `edi-cli`, you will need Python 3.11+ and `pip`. You can install `edi-cli` from PyPI:

```bash
_pip install edi-cli_
```

## Basic Usage

Once installed, you can use the `edi` command-line interface to interact with your EDI files. Here are some common commands:

*   **Convert an EDI file to JSON:**

    ```bash
    edi convert <input_file> --to json --out <output_file>
    ```

*   **Validate an EDI file against a schema:**

    ```bash
    edi validate <input_file> --schema <schema_name>
    ```

For more detailed information on the available commands and options, please refer to the [CLI documentation](cli.md).
