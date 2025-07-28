/**
 * Main Application Controller
 * Handles overall app state and coordination between modules
 */

class EDIApp {
    constructor() {
        this.currentFile = null;
        this.currentContent = '';
        this.parsedData = null;
        this.validationResults = null;
        this.isDirty = false;
        
        this.init();
    }

    init() {
        this.setupEventListeners();
        this.setupSplitter();
        this.setupIPC();
        this.updateUI();
    }

    setupEventListeners() {
        // File operations
        document.getElementById('open-file-btn').addEventListener('click', () => this.openFile());
        document.getElementById('empty-open-btn').addEventListener('click', () => this.openFile());
        
        // Processing operations
        document.getElementById('validate-btn').addEventListener('click', () => this.validateFile());
        document.getElementById('parse-btn').addEventListener('click', () => this.parseFile());
        
        // Panel controls
        document.getElementById('format-btn').addEventListener('click', () => this.formatContent());
        document.getElementById('syntax-highlight-btn').addEventListener('click', () => this.toggleSyntaxHighlight());
        document.getElementById('expand-all-btn').addEventListener('click', () => this.expandAllTreeNodes());
        document.getElementById('collapse-all-btn').addEventListener('click', () => this.collapseAllTreeNodes());
        
        // Validation panel controls
        document.getElementById('clear-errors-btn').addEventListener('click', () => this.clearValidationResults());
        document.getElementById('export-errors-btn').addEventListener('click', () => this.exportValidationResults());
        document.getElementById('toggle-errors-btn').addEventListener('click', () => this.toggleValidationPanel());
        
        // Context menu
        document.addEventListener('contextmenu', (e) => this.showContextMenu(e));
        document.addEventListener('click', () => this.hideContextMenu());
        
        // Keyboard shortcuts
        document.addEventListener('keydown', (e) => this.handleKeyboardShortcuts(e));
        
        // Window events
        window.addEventListener('beforeunload', (e) => this.handleBeforeUnload(e));
    }

    setupSplitter() {
        // Create horizontal splitter between left and right panels
        Split(['.left-panel', '.right-panel'], {
            sizes: [50, 50],
            minSize: [300, 250],
            gutterSize: 4,
            cursor: 'col-resize'
        });
    }

    setupIPC() {
        const { ipcRenderer } = require('electron');
        
        // File operations from menu
        ipcRenderer.on('file-opened', (event, fileData) => {
            this.loadFile(fileData);
        });
        
        ipcRenderer.on('menu-save', () => {
            this.saveFile();
        });
        
        ipcRenderer.on('save-file-as', (event, filePath) => {
            this.saveFileAs(filePath);
        });
        
        // View operations from menu
        ipcRenderer.on('menu-toggle-view', () => {
            this.toggleView();
        });
        
        ipcRenderer.on('menu-toggle-errors', () => {
            this.toggleValidationPanel();
        });
        
        // Processing operations from menu
        ipcRenderer.on('menu-validate', () => {
            this.validateFile();
        });
        
        ipcRenderer.on('menu-parse', () => {
            this.parseFile();
        });
        
        ipcRenderer.on('menu-export-json', () => {
            this.exportAsJSON();
        });
        
        ipcRenderer.on('menu-settings', () => {
            this.showSettings();
        });
    }

    async openFile() {
        const { dialog } = require('electron').remote || require('@electron/remote');
        
        const result = await dialog.showOpenDialog({
            properties: ['openFile'],
            filters: [
                { name: 'EDI Files', extensions: ['edi', 'x12', 'txt'] },
                { name: 'All Files', extensions: ['*'] }
            ]
        });

        if (!result.canceled && result.filePaths.length > 0) {
            const filePath = result.filePaths[0];
            const { ipcRenderer } = require('electron');
            
            const fileResult = await ipcRenderer.invoke('read-file', filePath);
            if (fileResult.success) {
                this.loadFile({
                    path: filePath,
                    content: fileResult.content,
                    name: require('path').basename(filePath)
                });
            } else {
                this.showError('Failed to open file', fileResult.error);
            }
        }
    }

    loadFile(fileData) {
        this.currentFile = fileData;
        this.currentContent = fileData.content;
        this.isDirty = false;
        
        // Update UI
        document.getElementById('current-file-name').textContent = fileData.name;
        document.getElementById('file-status').textContent = `Loaded: ${fileData.name}`;
        
        // Load content into editor
        if (window.ediEditor) {
            window.ediEditor.loadContent(fileData.content);
        }
        
        // Enable controls
        this.enableFileControls();
        
        // Auto-parse if file is small enough
        if (fileData.content.length < 100000) { // 100KB limit for auto-parse
            setTimeout(() => this.parseFile(), 100);
        }
        
        this.updateUI();
    }

    async saveFile() {
        if (!this.currentFile) {
            await this.saveFileAs();
            return;
        }
        
        const content = window.ediEditor ? window.ediEditor.getContent() : this.currentContent;
        const { ipcRenderer } = require('electron');
        
        const result = await ipcRenderer.invoke('write-file', this.currentFile.path, content);
        if (result.success) {
            this.isDirty = false;
            document.getElementById('file-status').textContent = 'Saved';
            setTimeout(() => {
                document.getElementById('file-status').textContent = 'Ready';
            }, 2000);
        } else {
            this.showError('Failed to save file', result.error);
        }
    }

    async saveFileAs(filePath = null) {
        if (!filePath) {
            const { dialog } = require('electron').remote || require('@electron/remote');
            
            const result = await dialog.showSaveDialog({
                filters: [
                    { name: 'EDI Files', extensions: ['edi'] },
                    { name: 'All Files', extensions: ['*'] }
                ]
            });
            
            if (result.canceled) return;
            filePath = result.filePath;
        }
        
        const content = window.ediEditor ? window.ediEditor.getContent() : this.currentContent;
        const { ipcRenderer } = require('electron');
        
        const result = await ipcRenderer.invoke('write-file', filePath, content);
        if (result.success) {
            this.currentFile = {
                ...this.currentFile,
                path: filePath,
                name: require('path').basename(filePath)
            };
            this.isDirty = false;
            document.getElementById('current-file-name').textContent = this.currentFile.name;
            document.getElementById('file-status').textContent = 'Saved';
        } else {
            this.showError('Failed to save file', result.error);
        }
    }

    async parseFile() {
        if (!this.currentContent) {
            this.showError('No file loaded', 'Please open an EDI file first');
            return;
        }
        
        this.showLoading('Parsing EDI file...');
        
        try {
            // Simulate parsing with the existing Python CLI
            // In a real implementation, this would call the Python parser
            const result = await this.callParser(this.currentContent);
            this.parsedData = result;
            
            // Update tree view
            if (window.treeView) {
                window.treeView.loadData(result);
            }
            
            document.getElementById('file-status').textContent = 'Parsed successfully';
            this.enableTreeControls();
            
        } catch (error) {
            this.showError('Parsing failed', error.message);
        } finally {
            this.hideLoading();
        }
    }

    async validateFile() {
        if (!this.currentContent) {
            this.showError('No file loaded', 'Please open an EDI file first');
            return;
        }
        
        this.showLoading('Validating EDI file...');
        
        try {
            // Simulate validation with the existing Python CLI
            const result = await this.callValidator(this.currentContent);
            this.validationResults = result;
            
            // Update validation panel
            if (window.validation) {
                window.validation.loadResults(result);
            }
            
            document.getElementById('file-status').textContent = 
                `Validation complete: ${result.error_count} errors, ${result.warning_count} warnings`;
            
            this.enableValidationControls();
            
        } catch (error) {
            this.showError('Validation failed', error.message);
        } finally {
            this.hideLoading();
        }
    }

    async callParser(content) {
        // Placeholder for calling the Python parser
        // This would typically use child_process to call the CLI
        return new Promise((resolve) => {
            setTimeout(() => {
                resolve({
                    interchanges: [{
                        header: {
                            sender_id: 'SENDER',
                            receiver_id: 'RECEIVER',
                            date: '20241128',
                            time: '1200',
                            control_number: '000000001'
                        },
                        functional_groups: [{
                            functional_group_code: 'HP',
                            transactions: [{
                                transaction_set_code: '835',
                                transaction_data: {
                                    // Mock parsed data
                                    payer: { name: 'Sample Payer' },
                                    claims: []
                                }
                            }]
                        }]
                    }]
                });
            }, 1000);
        });
    }

    async callValidator(content) {
        // Placeholder for calling the Python validator
        return new Promise((resolve) => {
            setTimeout(() => {
                resolve({
                    is_valid: false,
                    error_count: 2,
                    warning_count: 1,
                    errors: [
                        {
                            rule_name: 'required_field',
                            severity: 'error',
                            message: 'BEG03 (Purchase Order Date) is missing and required',
                            code: 'BEG03_MISSING',
                            path: 'interchange[0].functional_group[0].transaction[0].BEG[1]',
                            segment_id: 'BEG',
                            element_position: 3
                        },
                        {
                            rule_name: 'field_length',
                            severity: 'error',
                            message: 'PO101 (Line Number) exceeds maximum length of 6 characters',
                            code: 'PO101_LENGTH',
                            path: 'interchange[0].functional_group[0].transaction[0].PO1[1]',
                            segment_id: 'PO1',
                            element_position: 1
                        }
                    ],
                    warnings: [
                        {
                            rule_name: 'optional_field',
                            severity: 'warning',
                            message: 'N1 segment recommended for trading partner identification',
                            code: 'N1_RECOMMENDED',
                            path: 'interchange[0].functional_group[0].transaction[0]'
                        }
                    ]
                });
            }, 800);
        });
    }

    formatContent() {
        if (window.ediEditor) {
            window.ediEditor.format();
        }
    }

    toggleSyntaxHighlight() {
        if (window.ediEditor) {
            window.ediEditor.toggleSyntaxHighlight();
        }
    }

    expandAllTreeNodes() {
        if (window.treeView) {
            window.treeView.expandAll();
        }
    }

    collapseAllTreeNodes() {
        if (window.treeView) {
            window.treeView.collapseAll();
        }
    }

    clearValidationResults() {
        this.validationResults = null;
        if (window.validation) {
            window.validation.clear();
        }
        this.updateErrorCounts(0, 0);
    }

    async exportValidationResults() {
        if (!this.validationResults) return;
        
        const { dialog } = require('electron').remote || require('@electron/remote');
        
        const result = await dialog.showSaveDialog({
            filters: [
                { name: 'JSON Files', extensions: ['json'] },
                { name: 'All Files', extensions: ['*'] }
            ]
        });
        
        if (!result.canceled) {
            const { ipcRenderer } = require('electron');
            const content = JSON.stringify(this.validationResults, null, 2);
            
            const writeResult = await ipcRenderer.invoke('write-file', result.filePath, content);
            if (writeResult.success) {
                document.getElementById('file-status').textContent = 'Validation results exported';
            } else {
                this.showError('Export failed', writeResult.error);
            }
        }
    }

    async exportAsJSON() {
        if (!this.parsedData) {
            this.showError('No parsed data', 'Please parse the file first');
            return;
        }
        
        const { dialog } = require('electron').remote || require('@electron/remote');
        
        const result = await dialog.showSaveDialog({
            filters: [
                { name: 'JSON Files', extensions: ['json'] },
                { name: 'All Files', extensions: ['*'] }
            ]
        });
        
        if (!result.canceled) {
            const { ipcRenderer } = require('electron');
            const content = JSON.stringify(this.parsedData, null, 2);
            
            const writeResult = await ipcRenderer.invoke('write-file', result.filePath, content);
            if (writeResult.success) {
                document.getElementById('file-status').textContent = 'JSON exported';
            } else {
                this.showError('Export failed', writeResult.error);
            }
        }
    }

    toggleValidationPanel() {
        const panel = document.getElementById('validation-panel');
        const btn = document.getElementById('toggle-errors-btn');
        
        if (panel.classList.contains('hidden')) {
            panel.classList.remove('hidden');
            btn.textContent = 'Hide';
        } else {
            panel.classList.add('hidden');
            btn.textContent = 'Show';
        }
    }

    toggleView() {
        // Toggle between raw and tree view prominence
        const leftPanel = document.querySelector('.left-panel');
        const rightPanel = document.querySelector('.right-panel');
        
        if (leftPanel.style.flex === '2') {
            leftPanel.style.flex = '1';
            rightPanel.style.flex = '2';
        } else {
            leftPanel.style.flex = '2';
            rightPanel.style.flex = '1';
        }
    }

    showContextMenu(event) {
        event.preventDefault();
        const menu = document.getElementById('context-menu');
        menu.style.display = 'block';
        menu.style.left = event.pageX + 'px';
        menu.style.top = event.pageY + 'px';
    }

    hideContextMenu() {
        document.getElementById('context-menu').style.display = 'none';
    }

    handleKeyboardShortcuts(event) {
        const isCtrlOrCmd = event.ctrlKey || event.metaKey;
        
        if (isCtrlOrCmd) {
            switch (event.key) {
                case 'o':
                    event.preventDefault();
                    this.openFile();
                    break;
                case 's':
                    event.preventDefault();
                    if (event.shiftKey) {
                        this.saveFileAs();
                    } else {
                        this.saveFile();
                    }
                    break;
                case 't':
                    event.preventDefault();
                    this.toggleView();
                    break;
                case 'e':
                    event.preventDefault();
                    this.toggleValidationPanel();
                    break;
            }
        }
    }

    handleBeforeUnload(event) {
        if (this.isDirty) {
            event.preventDefault();
            event.returnValue = '';
        }
    }

    enableFileControls() {
        document.getElementById('validate-btn').disabled = false;
        document.getElementById('parse-btn').disabled = false;
        document.getElementById('format-btn').disabled = false;
    }

    enableTreeControls() {
        document.getElementById('expand-all-btn').disabled = false;
        document.getElementById('collapse-all-btn').disabled = false;
    }

    enableValidationControls() {
        document.getElementById('export-errors-btn').disabled = false;
    }

    updateErrorCounts(errors, warnings) {
        document.getElementById('error-count').textContent = `${errors} error${errors !== 1 ? 's' : ''}`;
        document.getElementById('warning-count').textContent = `${warnings} warning${warnings !== 1 ? 's' : ''}`;
    }

    showLoading(message) {
        const overlay = document.getElementById('loading-overlay');
        overlay.querySelector('p').textContent = message;
        overlay.style.display = 'flex';
    }

    hideLoading() {
        document.getElementById('loading-overlay').style.display = 'none';
    }

    showError(title, message) {
        const { dialog } = require('electron').remote || require('@electron/remote');
        dialog.showErrorBox(title, message);
    }

    showSettings() {
        // Placeholder for settings dialog
        alert('Settings dialog - coming soon!');
    }

    updateUI() {
        // Update various UI elements based on current state
        const hasFile = !!this.currentFile;
        const hasParsedData = !!this.parsedData;
        const hasValidationResults = !!this.validationResults;
        
        // Update empty states
        const rawEditor = document.getElementById('raw-editor');
        const treeView = document.getElementById('tree-view');
        const validationResults = document.getElementById('validation-results');
        
        if (hasFile) {
            rawEditor.querySelector('.empty-state').style.display = 'none';
        }
        
        if (hasParsedData) {
            treeView.querySelector('.empty-state').style.display = 'none';
        }
        
        if (hasValidationResults) {
            validationResults.querySelector('.empty-state').style.display = 'none';
            this.updateErrorCounts(
                this.validationResults.error_count,
                this.validationResults.warning_count
            );
        }
    }
}

// Initialize the application when the DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.ediApp = new EDIApp();
});