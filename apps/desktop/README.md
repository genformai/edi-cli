# EDI CLI Desktop

**Postman for EDI** - A cross-platform desktop application for parsing, validating, and analyzing EDI files.

## Features

### ✅ Current Features (v0.4.0)

- **Cross-platform Electron app** for Windows, macOS, and Linux
- **Dual-pane interface** with raw EDI text editor and hierarchical tree view
- **Advanced EDI syntax highlighting** with Monaco Editor
- **File management** with drag & drop, recent files, and session persistence
- **Validation error panel** with clickable errors and navigation
- **Export capabilities** for JSON, CSV, and text formats
- **Professional UI** with dark/light theme support

### 🚧 Planned Features

- **X12 850/810 parser integration** with existing CLI parsers
- **Partner override rules** with JSON configuration
- **File diff viewer** for comparing EDI documents
- **Advanced validation** with partner-specific rules
- **Performance optimization** for large files

## Quick Start

### Development

1. **Install dependencies:**
   ```bash
   cd desktop
   npm install
   ```

2. **Run in development mode:**
   ```bash
   npm run dev
   ```

3. **Build for production:**
   ```bash
   npm run build
   ```

### Usage

1. **Open EDI files:**
   - Use File → Open EDI File
   - Drag and drop .edi, .x12, or .txt files
   - Access recent files from the header dropdown

2. **Parse and validate:**
   - Click "Parse" to generate hierarchical structure
   - Click "Validate" to check for errors and warnings
   - Navigate between errors using the validation panel

3. **Explore structure:**
   - Expand/collapse tree nodes to explore EDI hierarchy
   - Click on tree nodes to highlight corresponding segments
   - Use context menus for additional actions

4. **Export data:**
   - Export parsed data as JSON
   - Export validation results as JSON, CSV, or text
   - Save modified EDI files

## Architecture

### Core Components

- **Main Process** (`src/main.js`) - Electron main process with file operations
- **Renderer Process** (`src/renderer/`) - UI components and business logic
  - **App Controller** (`js/app.js`) - Main application state and coordination
  - **Editor** (`js/editor.js`) - Monaco editor with EDI syntax highlighting
  - **Tree View** (`js/tree-view.js`) - Hierarchical structure display
  - **Validation Panel** (`js/validation.js`) - Error/warning display and navigation
  - **File Manager** (`js/file-manager.js`) - File operations and session management

### Integration Points

The desktop app integrates with the existing EDI CLI parsing engine:

- **Parser Integration** - Calls Python CLI parsers via child processes
- **Validation Engine** - Uses existing YAML-based validation rules
- **Schema Support** - Leverages existing X12 schema definitions
- **Plugin System** - Compatible with existing parser plugins

## Development

### Prerequisites

- Node.js 18+ 
- npm or yarn
- Python 3.8+ (for CLI integration)
- Git

### Project Structure

```
desktop/
├── src/
│   ├── main.js              # Electron main process
│   └── renderer/
│       ├── index.html       # Main UI
│       ├── styles.css       # Global styles
│       └── js/
│           ├── app.js       # Main controller
│           ├── editor.js    # Monaco editor integration
│           ├── tree-view.js # Structure tree component
│           ├── validation.js # Validation panel
│           └── file-manager.js # File operations
├── assets/                  # Icons and resources
├── package.json            # Dependencies and scripts
└── README.md               # This file
```

### Building

```bash
# Development build
npm run dev

# Production build (all platforms)
npm run build

# Platform-specific builds
npm run build -- --mac
npm run build -- --win
npm run build -- --linux
```

### Testing

```bash
# Run tests
npm test

# Run with coverage
npm run test:coverage
```

## Configuration

### Application Settings

Settings are stored in:
- **Windows**: `%APPDATA%/edi-cli-desktop/`
- **macOS**: `~/Library/Application Support/edi-cli-desktop/`
- **Linux**: `~/.config/edi-cli-desktop/`

### File Associations

The app supports opening:
- `.edi` files (EDI documents)
- `.x12` files (X12 transactions)
- `.txt` files (Plain text EDI)

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

See the main project [CONTRIBUTING.md](../CONTRIBUTING.md) for detailed guidelines.

## License

MIT License - see [LICENSE](../LICENSE) for details.

## Roadmap

### v0.4.1 - Enhanced Validation
- Integrate X12 850/810 parsers
- Partner override configuration UI
- Enhanced error messages with suggestions

### v0.4.2 - File Comparison
- Side-by-side diff viewer
- Change detection algorithms
- Structured diff reports

### v0.4.3 - Performance & Polish
- Large file optimization
- Memory usage improvements
- UI/UX enhancements

### v0.5.0 - Enterprise Features
- Multi-file batch processing
- Advanced search and filtering
- Custom validation rule editor

---

**EDI CLI Desktop** is part of the larger [edi-cli project](https://github.com/your-org/edi-cli) - building the "Postman for EDI" toolkit.