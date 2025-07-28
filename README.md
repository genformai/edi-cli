# EDI CLI - Postman for EDI

A comprehensive, open-source toolkit for parsing, validating, and analyzing Electronic Data Interchange (EDI) files. Built with a modern, developer-friendly approach that treats EDI as code.

**🎯 Our Vision:** Build the "Postman for EDI" - the most comprehensive, developer-friendly EDI platform that makes reading, validating, and debugging EDI files trivial.

📖 **[Read "Why Open Source EDI?" →](why-open-source-edi.md)**

## 🚀 Applications

### **🖥️ Desktop App** - Visual EDI Analysis
```bash
cd apps/desktop
npm install && npm run dev
```
- **Dual-pane interface** with raw EDI text + hierarchical tree view
- **Advanced syntax highlighting** with Monaco Editor
- **Validation error panel** with clickable navigation
- **File management** with drag & drop and session persistence

### **⚡ CLI Tool** - Terminal Powerhouse  
```bash
cd apps/cli
pip install -e . && edi convert sample-835.edi --to json
```
- **Convert** EDI files to JSON/CSV formats
- **Validate** with comprehensive YAML-based rules
- **Inspect** EDI structure and segments
- **Plugin system** for custom transaction types

### **🌐 API Service** - REST Integration
```bash
cd apps/api
pip install -r requirements.txt && python main.py
```
- **RESTful API** for EDI operations
- **Asynchronous processing** for large files
- **WebSocket support** for real-time updates
- **Docker containerization** ready

## 📦 Monorepo Structure

```
edi-cli/
├── apps/                     # All Applications
│   ├── cli/                  # Terminal CLI application
│   ├── desktop/              # Electron desktop app
│   └── api/                  # REST API service
├── core/                     # Shared Core Library
│   ├── parsers/              # Transaction parsers (835, 837P, 270/271, etc.)
│   ├── validation/           # Validation engines and rules
│   ├── plugins/              # Plugin system
│   └── utils/                # Shared utilities
├── shared/                   # Cross-Application Resources
│   ├── validation-rules/     # YAML validation rules
│   ├── schemas/              # JSON schemas  
│   ├── test-data/            # Sample EDI files
│   └── tests/                # Shared tests
└── tools/                    # Development & Build Tools
```

## 🏥 Supported Transaction Sets

### ✅ **Production Ready (v0.3.0)**
- **835** - Healthcare Claim Payment/Advice (ERA)
- **837P** - Professional Healthcare Claims  
- **270/271** - Eligibility Inquiry/Response
- **276/277** - Claim Status Inquiry/Response

### 🚧 **In Development (v0.4.0)**
- **850** - Purchase Order
- **810** - Invoice

### 🔮 **Planned**
- **837I** - Institutional Claims
- **837D** - Dental Claims
- **278** - Healthcare Services Review
- **856** - Advance Shipping Notice

## 🛠️ Quick Start

### **Option 1: Desktop App (Recommended)**
```bash
# Install and run desktop app
cd apps/desktop
npm install
npm run dev
```

### **Option 2: CLI Tool**
```bash
# Install CLI
cd apps/cli  
pip install -e .

# Convert EDI to JSON
edi convert sample-835.edi --to json --schema 835

# Validate with comprehensive rules  
edi validate sample-835.edi --rule-set comprehensive --verbose
```

### **Option 3: API Service**
```bash
# Start API server
cd apps/api
pip install -r requirements.txt
python main.py

# Use API
curl -X POST http://localhost:8000/parse \
  -F "file=@sample-835.edi" \
  -F "schema=835"
```

## 🔧 Development

### **Install All Dependencies**
```bash
npm run install:all
```

### **Run Applications**
```bash
# Desktop app
npm run dev:desktop

# CLI tool  
npm run dev:cli

# API service
npm run dev:api
```

### **Build All**
```bash
npm run build:all
```

### **Test All**
```bash
npm run test:all
```

## 🎯 Key Features

### **Advanced Validation**
- **YAML DSL** for custom validation rules
- **HIPAA compliance** with 39+ built-in rules  
- **Partner overrides** for trading partner specific requirements
- **Business rule engine** with mathematical calculations

### **Developer Experience**
- **Plugin architecture** for custom transaction types
- **JSON/CSV export** for data analysis
- **Rich error reporting** with field-level diagnostics
- **Performance optimized** (1-5ms execution time)

### **Cross-Platform**
- **Desktop app** for Windows, macOS, Linux
- **CLI tool** for automation and scripting
- **API service** for integration workflows
- **Docker support** for containerized deployments

## 📊 Roadmap

**Phase 1: CLI Foundation (✅ Completed)** → **Phase 2: Desktop App (🚀 v0.4)** → **Phase 3: Enterprise Platform**

### **v0.4 - "Postman for EDI" Desktop App** *(Q1 2025)*
- ✅ Cross-platform Electron application
- ✅ Dual-pane EDI analysis interface
- 🚧 X12 850/810 parser integration
- 🚧 Partner override configuration system
- 🚧 File diff viewer for document comparison

### **v0.5 - Enterprise Features** *(Q2 2025)*
- Multi-file batch processing
- Advanced search and filtering
- Custom validation rule editor
- SFTP/AS2 protocol support

[See full roadmap →](docs/roadmap.md)

## 🤝 Contributing

We welcome contributions! This project supports multiple ways to contribute:

- **Core Library** - Python parsers and validation engines
- **Desktop App** - Electron/JavaScript UI development  
- **CLI Tool** - Python command-line features
- **API Service** - FastAPI/Python web service
- **Documentation** - Guides, examples, tutorials

See our [Contributing Guide](CONTRIBUTING.md) for details.

## 📄 License

MIT License - see [LICENSE](LICENSE) for details.

## 🌟 Why Open Source EDI?

The EDI industry has been dominated by expensive, proprietary solutions for decades. We believe in:

- **Developer-first tools** that treat EDI as code
- **Modern architectures** over legacy monoliths  
- **Community-driven innovation** over vendor lock-in
- **Transparent, extensible solutions** for everyone

[Read our full vision →](why-open-source-edi.md)

---

**Building the future of EDI, one transaction at a time.** 🚀

[![GitHub Stars](https://img.shields.io/github/stars/your-org/edi-cli?style=social)](https://github.com/your-org/edi-cli)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.8+-blue.svg)](https://python.org)
[![Node.js](https://img.shields.io/badge/node.js-18+-green.svg)](https://nodejs.org)