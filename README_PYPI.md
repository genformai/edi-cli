# edi-cli

A modern, developer-friendly CLI tool for parsing and testing EDI (Electronic Data Interchange) files.

## 🚧 Early Release Notice

This is an early release to reserve the `edi-cli` namespace on PyPI. The current version provides basic CLI infrastructure and will be expanded with full EDI parsing capabilities in upcoming releases.

## Installation

```bash
pip install edi-cli
```

## Usage

After installation, you can run:

```bash
edi-cli
```

This will display the current status and version information.

### Available Commands

- `edi-cli` - Show status and version
- `edi-cli version` - Display version information  
- `edi-cli status` - Show installation status
- `edi-cli --help` - Display help information

## Coming Soon

- 📄 Full EDI file parsing (X12, HIPAA)
- ✅ Validation against EDI standards
- 🔄 Format conversion (EDI ↔ JSON ↔ CSV)
- 🔍 EDI file inspection and analysis
- 📊 Detailed validation reports
- 🎯 Support for common transaction sets (835, 837, 270, 271, 276, 277)

## Development

This tool is being actively developed. Follow the project for updates:

- **Repository**: https://github.com/edi-cli/edi-cli
- **Issues**: https://github.com/edi-cli/edi-cli/issues

## Requirements

- Python 3.7 or higher
- typer (automatically installed)

## License

MIT License - see LICENSE file for details.

## Support

For questions, bug reports, or feature requests, please visit our GitHub repository.