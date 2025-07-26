# edi-cli

A modern, open-source EDI toolkit.

**edi-cli** is a developer-first toolkit for parsing, validating, and transforming Electronic Data Interchange (EDI) files. It provides a fast, well-tested core library and a user-friendly command-line interface (CLI) to streamline working with complex EDI formats.

## Why Open Core?

We believe that core EDI parsing and validation should be a commodity. By open-sourcing the core, we aim to foster a community of contributors and build a robust foundation for a wide range of EDI applications. Our open-core model allows us to offer a free, powerful toolkit for developers while providing a clear path to commercial, enterprise-grade features like a hosted API, SFTP watchers, and advanced auditing capabilities.

## Quickstart (10 minutes)

1.  **Install `edi-cli`:**

    ```bash
    pip install edi-cli
    ```

2.  **Convert an EDI file to JSON:**

    ```bash
    edi convert examples/datasets/sample-835.edi --to json --out output.json
    ```

3.  **Validate an EDI file:**

    ```bash
    edi validate examples/datasets/sample-835.edi --schema x12-835-5010 --rules hipaa/basic.yml
    ```

## Roadmap

*   **v0.1:** 835 parse → JSON/CSV, CLI, tests, docs.
*   **v0.2:** 835 validation DSL.
*   **v0.3:** 837P support, plugin API.
*   **v0.4:** FastAPI service, Docker, auth stub.
*   **v0.5:** SFTP watcher prototype (enterprise path).

## Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for more information.

## License

The core `edi-cli` library and CLI are licensed under the [MIT License](LICENSE). Future enterprise modules will be licensed under a commercial license.
