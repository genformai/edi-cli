/**
 * Monaco Editor Integration for EDI Files
 * Handles syntax highlighting, formatting, and editor features
 */

class EDIEditor {
    constructor() {
        this.editor = null;
        this.syntaxHighlightEnabled = true;
        this.currentContent = '';
        
        this.init();
    }

    init() {
        // Load Monaco Editor
        require.config({ paths: { vs: '../node_modules/monaco-editor/min/vs' } });
        
        require(['vs/editor/editor.main'], () => {
            this.setupEditor();
        });
    }

    setupEditor() {
        // Define EDI language
        monaco.languages.register({ id: 'edi' });

        // Define EDI tokens
        monaco.languages.setMonarchTokensProvider('edi', {
            tokenizer: {
                root: [
                    // ISA segment (Interchange Control Header)
                    [/^ISA\*/, 'isa-segment'],
                    // IEA segment (Interchange Control Trailer)
                    [/^IEA\*/, 'iea-segment'],
                    // GS segment (Functional Group Header)
                    [/^GS\*/, 'gs-segment'],
                    // GE segment (Functional Group Trailer)
                    [/^GE\*/, 'ge-segment'],
                    // ST segment (Transaction Set Header)
                    [/^ST\*/, 'st-segment'],
                    // SE segment (Transaction Set Trailer)
                    [/^SE\*/, 'se-segment'],
                    
                    // Common healthcare segments
                    [/^BPR\*/, 'financial-segment'],
                    [/^CLP\*/, 'claim-segment'],
                    [/^SVC\*/, 'service-segment'],
                    [/^CAS\*/, 'adjustment-segment'],
                    [/^PLB\*/, 'adjustment-segment'],
                    
                    // Common purchase order segments
                    [/^BEG\*/, 'header-segment'],
                    [/^PO1\*/, 'line-item-segment'],
                    [/^PID\*/, 'description-segment'],
                    
                    // Common segments
                    [/^N1\*/, 'name-segment'],
                    [/^N3\*/, 'address-segment'],
                    [/^N4\*/, 'city-segment'],
                    [/^REF\*/, 'reference-segment'],
                    [/^DTM\*/, 'date-segment'],
                    [/^PER\*/, 'contact-segment'],
                    
                    // Element separator
                    [/\*/, 'element-separator'],
                    // Segment terminator
                    [/~/, 'segment-terminator'],
                    // Sub-element separator
                    [/:/, 'sub-element-separator'],
                    
                    // Numbers
                    [/\d+(\.\d+)?/, 'number'],
                    // Dates (YYYYMMDD, YYMMDD)
                    [/\d{6,8}/, 'date'],
                    // Times (HHMM, HHMMSS)
                    [/\d{4,6}/, 'time'],
                    
                    // Default text
                    [/[^*~:]+/, 'text']
                ]
            }
        });

        // Define EDI theme
        monaco.editor.defineTheme('edi-theme', {
            base: 'vs',
            inherit: true,
            rules: [
                { token: 'isa-segment', foreground: '0066cc', fontStyle: 'bold' },
                { token: 'iea-segment', foreground: '0066cc', fontStyle: 'bold' },
                { token: 'gs-segment', foreground: '009900', fontStyle: 'bold' },
                { token: 'ge-segment', foreground: '009900', fontStyle: 'bold' },
                { token: 'st-segment', foreground: 'cc6600', fontStyle: 'bold' },
                { token: 'se-segment', foreground: 'cc6600', fontStyle: 'bold' },
                
                { token: 'financial-segment', foreground: 'cc0066' },
                { token: 'claim-segment', foreground: '6600cc' },
                { token: 'service-segment', foreground: '0099cc' },
                { token: 'adjustment-segment', foreground: 'cc3300' },
                { token: 'header-segment', foreground: '006600' },
                { token: 'line-item-segment', foreground: '666600' },
                { token: 'description-segment', foreground: '336699' },
                
                { token: 'name-segment', foreground: '009999' },
                { token: 'address-segment', foreground: '009999' },
                { token: 'city-segment', foreground: '009999' },
                { token: 'reference-segment', foreground: '999900' },
                { token: 'date-segment', foreground: '990099' },
                { token: 'contact-segment', foreground: '990099' },
                
                { token: 'element-separator', foreground: 'ff6600', fontStyle: 'bold' },
                { token: 'segment-terminator', foreground: 'ff0000', fontStyle: 'bold' },
                { token: 'sub-element-separator', foreground: 'ff9900' },
                
                { token: 'number', foreground: '0066ff' },
                { token: 'date', foreground: '9900cc' },
                { token: 'time', foreground: 'cc9900' },
                { token: 'text', foreground: '333333' }
            ],
            colors: {
                'editor.background': '#ffffff',
                'editor.foreground': '#333333',
                'editor.lineHighlightBackground': '#f8f9fa',
                'editor.selectionBackground': '#e3f2fd'
            }
        });

        // Define dark theme
        monaco.editor.defineTheme('edi-dark-theme', {
            base: 'vs-dark',
            inherit: true,
            rules: [
                { token: 'isa-segment', foreground: '569cd6', fontStyle: 'bold' },
                { token: 'iea-segment', foreground: '569cd6', fontStyle: 'bold' },
                { token: 'gs-segment', foreground: '4ec9b0', fontStyle: 'bold' },
                { token: 'ge-segment', foreground: '4ec9b0', fontStyle: 'bold' },
                { token: 'st-segment', foreground: 'dcdcaa', fontStyle: 'bold' },
                { token: 'se-segment', foreground: 'dcdcaa', fontStyle: 'bold' },
                
                { token: 'financial-segment', foreground: 'c586c0' },
                { token: 'claim-segment', foreground: '9cdcfe' },
                { token: 'service-segment', foreground: '4fc1ff' },
                { token: 'adjustment-segment', foreground: 'f44747' },
                { token: 'header-segment', foreground: '6a9955' },
                { token: 'line-item-segment', foreground: 'b5cea8' },
                { token: 'description-segment', foreground: '9cdcfe' },
                
                { token: 'element-separator', foreground: 'ff8c00', fontStyle: 'bold' },
                { token: 'segment-terminator', foreground: 'ff6b6b', fontStyle: 'bold' },
                { token: 'sub-element-separator', foreground: 'ffcc02' },
                
                { token: 'number', foreground: 'b5cea8' },
                { token: 'date', foreground: 'c586c0' },
                { token: 'time', foreground: 'dcdcaa' },
                { token: 'text', foreground: 'd4d4d4' }
            ]
        });

        // Create the editor
        this.editor = monaco.editor.create(document.getElementById('raw-editor'), {
            value: '',
            language: 'edi',
            theme: 'edi-theme',
            fontSize: 13,
            fontFamily: 'Monaco, Menlo, "Ubuntu Mono", Consolas, monospace',
            lineNumbers: 'on',
            minimap: { enabled: true },
            wordWrap: 'off',
            scrollBeyondLastLine: false,
            automaticLayout: true,
            folding: true,
            renderWhitespace: 'boundary',
            rulers: [80, 120],
            contextmenu: true,
            mouseWheelZoom: true,
            
            // EDI-specific settings
            renderLineHighlight: 'all',
            selectOnLineNumbers: true,
            scrollbar: {
                vertical: 'visible',
                horizontal: 'visible',
                useShadows: false,
                verticalHasArrows: true,
                horizontalHasArrows: true
            }
        });

        // Set up event listeners
        this.setupEventListeners();
        
        // Expose globally
        window.ediEditor = this;
    }

    setupEventListeners() {
        // Content change detection
        this.editor.onDidChangeModelContent(() => {
            this.currentContent = this.editor.getValue();
            if (window.ediApp) {
                window.ediApp.isDirty = true;
            }
            this.updateLineColumn();
        });

        // Cursor position change
        this.editor.onDidChangeCursorPosition(() => {
            this.updateLineColumn();
        });

        // Right-click context menu
        this.editor.onContextMenu((e) => {
            // Custom context menu for EDI-specific actions
            this.showEDIContextMenu(e);
        });

        // Double-click on segments
        this.editor.onMouseDown((e) => {
            if (e.detail === 2) { // Double-click
                this.handleSegmentDoubleClick(e);
            }
        });

        // Theme change detection
        window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', (e) => {
            this.updateTheme();
        });
    }

    loadContent(content) {
        this.currentContent = content;
        this.editor.setValue(content);
        this.formatContent();
        this.updateLineColumn();
        
        // Hide empty state
        const emptyState = document.querySelector('#raw-editor .empty-state');
        if (emptyState) {
            emptyState.style.display = 'none';
        }
    }

    getContent() {
        return this.editor.getValue();
    }

    format() {
        const content = this.editor.getValue();
        const formatted = this.formatEDIContent(content);
        this.editor.setValue(formatted);
        this.editor.getAction('editor.action.formatDocument').run();
    }

    formatEDIContent(content) {
        // Basic EDI formatting
        let formatted = content
            .replace(/~/g, '~\n')  // Add line breaks after segment terminators
            .replace(/\n\n+/g, '\n')  // Remove multiple line breaks
            .trim();
        
        // Ensure each segment starts on a new line
        const segments = formatted.split('\n');
        const formattedSegments = segments.map(segment => {
            return segment.trim();
        }).filter(segment => segment.length > 0);
        
        return formattedSegments.join('\n') + '\n';
    }

    toggleSyntaxHighlight() {
        this.syntaxHighlightEnabled = !this.syntaxHighlightEnabled;
        
        if (this.syntaxHighlightEnabled) {
            monaco.editor.setModelLanguage(this.editor.getModel(), 'edi');
            document.getElementById('syntax-highlight-btn').textContent = 'Syntax';
        } else {
            monaco.editor.setModelLanguage(this.editor.getModel(), 'plaintext');
            document.getElementById('syntax-highlight-btn').textContent = 'Plain';
        }
    }

    updateTheme() {
        const isDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
        const theme = isDark ? 'edi-dark-theme' : 'edi-theme';
        monaco.editor.setTheme(theme);
    }

    updateLineColumn() {
        const position = this.editor.getPosition();
        const lineCol = document.getElementById('line-col');
        if (lineCol && position) {
            lineCol.textContent = `Ln ${position.lineNumber}, Col ${position.column}`;
        }
    }

    highlightSegment(segmentPath) {
        // Highlight a specific segment based on validation error path
        // Format: interchange[0].functional_group[0].transaction[0].BEG[1]
        
        try {
            const content = this.editor.getValue();
            const lines = content.split('\n');
            
            // Simple segment highlighting - find segment by ID
            const segmentMatch = segmentPath.match(/\.([A-Z0-9]+)\[(\d+)\]/);
            if (segmentMatch) {
                const segmentId = segmentMatch[1];
                const segmentIndex = parseInt(segmentMatch[2]);
                
                let currentIndex = 0;
                for (let i = 0; i < lines.length; i++) {
                    const line = lines[i].trim();
                    if (line.startsWith(segmentId + '*')) {
                        if (currentIndex === segmentIndex) {
                            // Highlight this line
                            this.editor.setSelection(new monaco.Range(i + 1, 1, i + 1, line.length + 1));
                            this.editor.revealLineInCenter(i + 1);
                            
                            // Add decoration
                            this.editor.deltaDecorations([], [{
                                range: new monaco.Range(i + 1, 1, i + 1, line.length + 1),
                                options: {
                                    className: 'validation-error-highlight',
                                    isWholeLine: true
                                }
                            }]);
                            break;
                        }
                        currentIndex++;
                    }
                }
            }
        } catch (error) {
            console.error('Error highlighting segment:', error);
        }
    }

    clearHighlights() {
        this.editor.deltaDecorations(['validation-error-highlight'], []);
    }

    showEDIContextMenu(event) {
        // Get word under cursor
        const position = this.editor.getPositionAt(event.target.position);
        const word = this.editor.getModel().getWordAtPosition(position);
        
        // Check if it's a segment ID
        if (word && /^[A-Z]{2,3}$/.test(word.word)) {
            // Show EDI-specific context menu
            const menu = document.getElementById('context-menu');
            menu.style.display = 'block';
            menu.style.left = event.event.browserEvent.pageX + 'px';
            menu.style.top = event.event.browserEvent.pageY + 'px';
            
            // Update context menu items
            document.getElementById('ctx-goto-segment').textContent = `Go to ${word.word} definition`;
            document.getElementById('ctx-validate-segment').textContent = `Validate ${word.word} segment`;
        }
    }

    handleSegmentDoubleClick(event) {
        const position = this.editor.getPositionAt(event.target.position);
        const line = this.editor.getModel().getLineContent(position.lineNumber);
        
        // Parse segment
        const segments = line.split('*');
        if (segments.length > 0) {
            const segmentId = segments[0];
            
            // Show segment information
            this.showSegmentInfo(segmentId, segments);
        }
    }

    showSegmentInfo(segmentId, elements) {
        // Create a simple popup with segment information
        const info = this.getSegmentDefinition(segmentId);
        
        const popup = document.createElement('div');
        popup.className = 'segment-popup';
        popup.innerHTML = `
            <div class="segment-popup-header">
                <strong>${segmentId}</strong> - ${info.name}
                <button class="segment-popup-close">×</button>
            </div>
            <div class="segment-popup-content">
                <p>${info.description}</p>
                <table class="segment-elements">
                    <thead>
                        <tr><th>Pos</th><th>Element</th><th>Value</th></tr>
                    </thead>
                    <tbody>
                        ${elements.slice(1).map((value, index) => `
                            <tr>
                                <td>${String(index + 1).padStart(2, '0')}</td>
                                <td>${info.elements[index] || 'Unknown'}</td>
                                <td>${value || '(empty)'}</td>
                            </tr>
                        `).join('')}
                    </tbody>
                </table>
            </div>
        `;
        
        document.body.appendChild(popup);
        
        // Position popup
        const rect = this.editor.getDomNode().getBoundingClientRect();
        popup.style.position = 'fixed';
        popup.style.left = rect.left + 20 + 'px';
        popup.style.top = rect.top + 20 + 'px';
        
        // Close button
        popup.querySelector('.segment-popup-close').addEventListener('click', () => {
            document.body.removeChild(popup);
        });
        
        // Auto-close after 10 seconds
        setTimeout(() => {
            if (document.body.contains(popup)) {
                document.body.removeChild(popup);
            }
        }, 10000);
    }

    getSegmentDefinition(segmentId) {
        // Basic segment definitions
        const definitions = {
            'ISA': {
                name: 'Interchange Control Header',
                description: 'Start of an EDI interchange',
                elements: ['Authorization Info Qualifier', 'Authorization Information', 'Security Info Qualifier', 'Security Information', 'Interchange ID Qualifier', 'Interchange Sender ID', 'Interchange ID Qualifier', 'Interchange Receiver ID', 'Interchange Date', 'Interchange Time', 'Interchange Control Standards Identifier', 'Interchange Control Version Number', 'Interchange Control Number', 'Acknowledgment Requested', 'Usage Indicator', 'Component Element Separator']
            },
            'GS': {
                name: 'Functional Group Header',
                description: 'Start of a functional group',
                elements: ['Functional Identifier Code', 'Application Sender Code', 'Application Receiver Code', 'Date', 'Time', 'Group Control Number', 'Responsible Agency Code', 'Version/Release/Industry ID Code']
            },
            'ST': {
                name: 'Transaction Set Header',
                description: 'Start of a transaction set',
                elements: ['Transaction Set Identifier Code', 'Transaction Set Control Number']
            },
            'BEG': {
                name: 'Beginning Segment for Purchase Order',
                description: 'Beginning segment for purchase order transaction',
                elements: ['Transaction Set Purpose Code', 'Purchase Order Type Code', 'Purchase Order Number', 'Release Number', 'Date', 'Contract Number']
            },
            'PO1': {
                name: 'Baseline Item Data',
                description: 'Line item information',
                elements: ['Assigned Identification', 'Quantity Ordered', 'Unit or Basis for Measurement Code', 'Unit Price', 'Basis of Unit Price Code', 'Product/Service ID Qualifier', 'Product/Service ID']
            },
            'N1': {
                name: 'Name',
                description: 'Party identification',
                elements: ['Entity Identifier Code', 'Name', 'Identification Code Qualifier', 'Identification Code']
            }
        };
        
        return definitions[segmentId] || {
            name: 'Unknown Segment',
            description: 'Segment definition not available',
            elements: []
        };
    }

    addValidationDecorations(validationResults) {
        const decorations = [];
        
        if (validationResults && validationResults.errors) {
            validationResults.errors.forEach(error => {
                if (error.segment_id && error.element_position) {
                    // Find the line with this segment
                    const content = this.editor.getValue();
                    const lines = content.split('\n');
                    
                    for (let i = 0; i < lines.length; i++) {
                        const line = lines[i].trim();
                        if (line.startsWith(error.segment_id + '*')) {
                            decorations.push({
                                range: new monaco.Range(i + 1, 1, i + 1, line.length + 1),
                                options: {
                                    className: 'validation-error-line',
                                    hoverMessage: { value: error.message },
                                    glyphMarginClassName: 'validation-error-glyph'
                                }
                            });
                            break;
                        }
                    }
                }
            });
        }
        
        this.editor.deltaDecorations([], decorations);
    }

    clearValidationDecorations() {
        this.editor.deltaDecorations(['validation-error-line', 'validation-error-glyph'], []);
    }
}

// Add CSS for segment popup and validation decorations
const style = document.createElement('style');
style.textContent = `
    .segment-popup {
        background: white;
        border: 1px solid #ddd;
        border-radius: 8px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        z-index: 1000;
        max-width: 500px;
        font-size: 13px;
    }
    
    .segment-popup-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 12px 16px;
        background-color: #f8f9fa;
        border-bottom: 1px solid #e1e5e9;
        border-radius: 8px 8px 0 0;
        font-weight: 600;
    }
    
    .segment-popup-close {
        background: none;
        border: none;
        font-size: 18px;
        cursor: pointer;
        color: #666;
    }
    
    .segment-popup-content {
        padding: 16px;
    }
    
    .segment-elements {
        width: 100%;
        border-collapse: collapse;
        margin-top: 12px;
        font-size: 12px;
    }
    
    .segment-elements th,
    .segment-elements td {
        text-align: left;
        padding: 6px 8px;
        border-bottom: 1px solid #eee;
    }
    
    .segment-elements th {
        background-color: #f8f9fa;
        font-weight: 600;
    }
    
    .validation-error-highlight {
        background-color: rgba(255, 0, 0, 0.1) !important;
    }
    
    .validation-error-line {
        background-color: rgba(255, 0, 0, 0.05) !important;
        border-left: 3px solid #dc3545 !important;
    }
    
    .validation-error-glyph {
        background-color: #dc3545;
        width: 16px !important;
        height: 16px !important;
        border-radius: 50%;
    }
    
    .validation-error-glyph::after {
        content: "!";
        color: white;
        font-weight: bold;
        font-size: 12px;
        position: absolute;
        top: 1px;
        left: 5px;
    }
`;
document.head.appendChild(style);

// Initialize the editor when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    // Wait a bit for other scripts to load
    setTimeout(() => {
        new EDIEditor();
    }, 100);
});