# Getting Started

This guide will walk you through the process of installing and using `edi-cli`.

## Installation

To install `edi-cli`, you will need Python 3.11+ and `pip`. You can install `edi-cli` from PyPI:

```bash
pip install edi-cli
```

## Basic Usage

Once installed, you can use the `edi` command-line interface to interact with your EDI files. Here are the most common commands:

### Converting Files

*   **Convert an EDI file to JSON:**

    ```bash
    edi convert sample.edi --to json --out output.json
    ```

*   **Convert an EDI file to CSV:**

    ```bash
    edi convert sample.edi --to csv --out claims.csv
    ```

### Validation and Analysis

*   **Validate an EDI file:**

    ```bash
    edi validate sample.edi --schema x12-835-5010
    ```

*   **Inspect file structure:**

    ```bash
    edi inspect sample.edi
    ```

*   **Extract specific segments:**

    ```bash
    edi inspect sample.edi --segments CLP,SVC
    ```

*   **Compare two EDI files:**

    ```bash
    edi diff file1.edi file2.edi
    ```

## Next Steps

For detailed information on all available commands and options, please refer to the [CLI documentation](cli.md).

You can also explore the example EDI files included in the `examples/datasets/` directory to get started with real data.
