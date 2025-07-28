/**
 * File Manager Component
 * Handles file operations, recent files, and session persistence
 */

class FileManager {
    constructor() {
        this.recentFiles = [];
        this.currentFile = null;
        this.maxRecentFiles = 10;
        this.storageKey = 'edi-cli-desktop-recent-files';
        this.sessionKey = 'edi-cli-desktop-session';
        
        this.init();
    }

    init() {
        this.loadRecentFiles();
        this.loadSession();
        this.setupEventListeners();
        
        // Expose globally
        window.fileManager = this;
    }

    setupEventListeners() {
        // File drag and drop
        this.setupDragAndDrop();
        
        // Auto-save session on changes
        window.addEventListener('beforeunload', () => {
            this.saveSession();
        });
        
        // Periodic session save
        setInterval(() => {
            this.saveSession();
        }, 30000); // Every 30 seconds
    }

    setupDragAndDrop() {
        const dropZone = document.body;
        
        // Prevent default drag behaviors
        ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
            dropZone.addEventListener(eventName, this.preventDefaults, false);
        });
        
        // Highlight drop zone
        ['dragenter', 'dragover'].forEach(eventName => {
            dropZone.addEventListener(eventName, this.highlight, false);
        });
        
        ['dragleave', 'drop'].forEach(eventName => {
            dropZone.addEventListener(eventName, this.unhighlight, false);
        });
        
        // Handle dropped files
        dropZone.addEventListener('drop', (e) => {
            this.handleDrop(e);
        }, false);
    }

    preventDefaults(e) {
        e.preventDefault();
        e.stopPropagation();
    }

    highlight(e) {
        document.body.classList.add('drag-highlight');
    }

    unhighlight(e) {
        document.body.classList.remove('drag-highlight');
    }

    handleDrop(e) {
        const dt = e.dataTransfer;
        const files = dt.files;
        
        if (files.length > 0) {
            const file = files[0];
            
            // Check if it's an EDI file
            if (this.isEDIFile(file)) {
                this.loadDroppedFile(file);
            } else {
                this.showError('Invalid file type', 'Please drop an EDI file (.edi, .x12, .txt)');
            }
        }
    }

    isEDIFile(file) {
        const validExtensions = ['.edi', '.x12', '.txt'];
        const extension = file.name.toLowerCase().substring(file.name.lastIndexOf('.'));
        return validExtensions.includes(extension);
    }

    async loadDroppedFile(file) {
        try {
            const content = await this.readFileContent(file);
            const fileData = {
                path: file.path || file.name,
                content: content,
                name: file.name
            };
            
            this.openFile(fileData);
        } catch (error) {
            this.showError('Error reading file', error.message);
        }
    }

    readFileContent(file) {
        return new Promise((resolve, reject) => {
            const reader = new FileReader();
            reader.onload = (e) => resolve(e.target.result);
            reader.onerror = (e) => reject(new Error('Failed to read file'));
            reader.readAsText(file);
        });
    }

    openFile(fileData) {
        this.currentFile = fileData;
        
        // Add to recent files
        this.addToRecentFiles(fileData);
        
        // Notify main app
        if (window.ediApp) {
            window.ediApp.loadFile(fileData);
        }
        
        // Update UI
        this.updateFileUI(fileData);
        
        // Save session
        this.saveSession();
    }

    addToRecentFiles(fileData) {
        // Remove if already exists
        this.recentFiles = this.recentFiles.filter(file => file.path !== fileData.path);
        
        // Add to beginning
        this.recentFiles.unshift({
            path: fileData.path,
            name: fileData.name,
            lastOpened: new Date().toISOString()
        });
        
        // Keep only max files
        this.recentFiles = this.recentFiles.slice(0, this.maxRecentFiles);
        
        // Save to storage
        this.saveRecentFiles();
        
        // Update recent files menu
        this.updateRecentFilesMenu();
    }

    updateFileUI(fileData) {
        // Update title bar
        document.title = `EDI CLI Desktop - ${fileData.name}`;
        
        // Update file name display
        const fileNameElement = document.getElementById('current-file-name');
        if (fileNameElement) {
            fileNameElement.textContent = fileData.name;
            fileNameElement.title = fileData.path;
        }
        
        // Update status
        document.getElementById('file-status').textContent = `Loaded: ${fileData.name}`;
    }

    updateRecentFilesMenu() {
        // This would typically update the application menu
        // For now, we'll create a recent files dropdown
        this.createRecentFilesDropdown();
    }

    createRecentFilesDropdown() {
        // Remove existing dropdown
        const existing = document.getElementById('recent-files-dropdown');
        if (existing) {
            existing.remove();
        }
        
        if (this.recentFiles.length === 0) return;
        
        // Create dropdown
        const dropdown = document.createElement('div');
        dropdown.id = 'recent-files-dropdown';
        dropdown.className = 'recent-files-dropdown';
        dropdown.innerHTML = `
            <button class="recent-files-btn">Recent Files ▼</button>
            <div class="recent-files-menu" style="display: none;">
                ${this.recentFiles.map(file => `
                    <div class="recent-file-item" data-path="${file.path}">
                        <div class="recent-file-name">${file.name}</div>
                        <div class="recent-file-path">${file.path}</div>
                        <div class="recent-file-date">${this.formatDate(file.lastOpened)}</div>
                    </div>
                `).join('')}
                <div class="recent-files-separator"></div>
                <div class="recent-file-item clear-recent" data-action="clear">
                    <div class="recent-file-name">Clear Recent Files</div>
                </div>
            </div>
        `;
        
        // Add to header
        const headerLeft = document.querySelector('.header-left');
        headerLeft.appendChild(dropdown);
        
        // Add event listeners
        const btn = dropdown.querySelector('.recent-files-btn');
        const menu = dropdown.querySelector('.recent-files-menu');
        
        btn.addEventListener('click', () => {
            menu.style.display = menu.style.display === 'none' ? 'block' : 'none';
        });
        
        menu.addEventListener('click', (e) => {
            const item = e.target.closest('.recent-file-item');
            if (!item) return;
            
            if (item.dataset.action === 'clear') {
                this.clearRecentFiles();
            } else {
                const path = item.dataset.path;
                this.openRecentFile(path);
            }
            
            menu.style.display = 'none';
        });
        
        // Close menu when clicking elsewhere
        document.addEventListener('click', (e) => {
            if (!dropdown.contains(e.target)) {
                menu.style.display = 'none';
            }
        });
    }

    async openRecentFile(filePath) {
        const { ipcRenderer } = require('electron');
        
        const result = await ipcRenderer.invoke('read-file', filePath);
        if (result.success) {
            const fileData = {
                path: filePath,
                content: result.content,
                name: require('path').basename(filePath)
            };
            this.openFile(fileData);
        } else {
            this.showError('Failed to open recent file', result.error);
            // Remove from recent files if it doesn't exist
            this.removeFromRecentFiles(filePath);
        }
    }

    removeFromRecentFiles(filePath) {
        this.recentFiles = this.recentFiles.filter(file => file.path !== filePath);
        this.saveRecentFiles();
        this.updateRecentFilesMenu();
    }

    clearRecentFiles() {
        this.recentFiles = [];
        this.saveRecentFiles();
        this.updateRecentFilesMenu();
        
        // Remove dropdown
        const dropdown = document.getElementById('recent-files-dropdown');
        if (dropdown) {
            dropdown.remove();
        }
    }

    formatDate(dateString) {
        const date = new Date(dateString);
        const now = new Date();
        const diffMs = now - date;
        const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));
        
        if (diffDays === 0) {
            return 'Today';
        } else if (diffDays === 1) {
            return 'Yesterday';
        } else if (diffDays < 7) {
            return `${diffDays} days ago`;
        } else {
            return date.toLocaleDateString();
        }
    }

    saveRecentFiles() {
        try {
            localStorage.setItem(this.storageKey, JSON.stringify(this.recentFiles));
        } catch (error) {
            console.warn('Failed to save recent files:', error);
        }
    }

    loadRecentFiles() {
        try {
            const stored = localStorage.getItem(this.storageKey);
            if (stored) {
                this.recentFiles = JSON.parse(stored);
                this.updateRecentFilesMenu();
            }
        } catch (error) {
            console.warn('Failed to load recent files:', error);
            this.recentFiles = [];
        }
    }

    saveSession() {
        try {
            const session = {
                currentFile: this.currentFile,
                timestamp: new Date().toISOString(),
                editorState: null,
                treeViewState: null,
                validationState: null
            };
            
            // Get state from other components
            if (window.ediEditor) {
                session.editorState = {
                    content: window.ediEditor.getContent(),
                    syntaxHighlight: window.ediEditor.syntaxHighlightEnabled
                };
            }
            
            if (window.treeView) {
                session.treeViewState = {
                    expandedNodes: Array.from(window.treeView.expandedNodes),
                    selectedNode: window.treeView.selectedNode
                };
            }
            
            if (window.validation) {
                session.validationState = {
                    currentFilter: window.validation.currentFilter,
                    results: window.validation.results
                };
            }
            
            localStorage.setItem(this.sessionKey, JSON.stringify(session));
        } catch (error) {
            console.warn('Failed to save session:', error);
        }
    }

    loadSession() {
        try {
            const stored = localStorage.getItem(this.sessionKey);
            if (!stored) return;
            
            const session = JSON.parse(stored);
            
            // Check if session is recent (within 24 hours)
            const sessionTime = new Date(session.timestamp);
            const now = new Date();
            const diffHours = (now - sessionTime) / (1000 * 60 * 60);
            
            if (diffHours > 24) {
                // Session too old, clear it
                localStorage.removeItem(this.sessionKey);
                return;
            }
            
            // Restore file if it exists
            if (session.currentFile) {
                this.restoreFile(session.currentFile, session);
            }
        } catch (error) {
            console.warn('Failed to load session:', error);
        }
    }

    async restoreFile(fileData, session) {
        try {
            // Try to read the file again to make sure it still exists
            const { ipcRenderer } = require('electron');
            const result = await ipcRenderer.invoke('read-file', fileData.path);
            
            if (result.success) {
                // File exists, restore it
                fileData.content = result.content;
                this.openFile(fileData);
                
                // Restore component states after a short delay
                setTimeout(() => {
                    this.restoreComponentStates(session);
                }, 500);
                
                // Show restoration notification
                document.getElementById('file-status').textContent = `Restored session: ${fileData.name}`;
            } else {
                // File no longer exists, remove from recent files
                this.removeFromRecentFiles(fileData.path);
            }
        } catch (error) {
            console.warn('Failed to restore file:', error);
        }
    }

    restoreComponentStates(session) {
        // Restore tree view state
        if (session.treeViewState && window.treeView) {
            if (session.treeViewState.expandedNodes) {
                window.treeView.expandedNodes = new Set(session.treeViewState.expandedNodes);
            }
            if (session.treeViewState.selectedNode) {
                window.treeView.selectNode(session.treeViewState.selectedNode);
            }
        }
        
        // Restore validation state
        if (session.validationState && window.validation) {
            if (session.validationState.currentFilter) {
                window.validation.setFilter(session.validationState.currentFilter);
            }
            if (session.validationState.results) {
                window.validation.loadResults(session.validationState.results);
            }
        }
        
        // Restore editor state
        if (session.editorState && window.ediEditor) {
            if (session.editorState.syntaxHighlight !== undefined) {
                window.ediEditor.syntaxHighlightEnabled = session.editorState.syntaxHighlight;
            }
        }
    }

    showError(title, message) {
        const { dialog } = require('electron').remote || require('@electron/remote');
        dialog.showErrorBox(title, message);
    }

    // Public API methods
    getCurrentFile() {
        return this.currentFile;
    }

    getRecentFiles() {
        return [...this.recentFiles];
    }

    clearSession() {
        localStorage.removeItem(this.sessionKey);
    }

    exportRecentFiles() {
        return {
            recentFiles: this.recentFiles,
            exportDate: new Date().toISOString()
        };
    }

    importRecentFiles(data) {
        if (data.recentFiles && Array.isArray(data.recentFiles)) {
            this.recentFiles = data.recentFiles.slice(0, this.maxRecentFiles);
            this.saveRecentFiles();
            this.updateRecentFilesMenu();
        }
    }
}

// Add CSS for recent files dropdown and drag/drop
const fileManagerStyle = document.createElement('style');
fileManagerStyle.textContent = `
    .drag-highlight {
        background-color: rgba(0, 123, 255, 0.1);
        outline: 2px dashed #007bff;
        outline-offset: -2px;
    }

    .recent-files-dropdown {
        position: relative;
        margin-left: 16px;
    }

    .recent-files-btn {
        background: rgba(255,255,255,0.2);
        border: 1px solid rgba(255,255,255,0.3);
        color: white;
        padding: 6px 12px;
        border-radius: 4px;
        cursor: pointer;
        font-size: 12px;
        transition: background-color 0.2s ease;
    }

    .recent-files-btn:hover {
        background: rgba(255,255,255,0.3);
    }

    .recent-files-menu {
        position: absolute;
        top: 100%;
        left: 0;
        background: white;
        border: 1px solid #ddd;
        border-radius: 6px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        z-index: 1000;
        min-width: 300px;
        max-height: 400px;
        overflow-y: auto;
        margin-top: 4px;
    }

    .recent-file-item {
        padding: 12px 16px;
        cursor: pointer;
        border-bottom: 1px solid #f1f3f4;
        transition: background-color 0.2s ease;
    }

    .recent-file-item:hover {
        background-color: #f8f9fa;
    }

    .recent-file-item:last-child {
        border-bottom: none;
    }

    .recent-file-item.clear-recent {
        color: #dc3545;
        font-weight: 500;
        text-align: center;
    }

    .recent-file-name {
        font-weight: 500;
        margin-bottom: 4px;
        color: #333;
    }

    .recent-file-path {
        font-size: 11px;
        color: #666;
        font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
        margin-bottom: 2px;
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
    }

    .recent-file-date {
        font-size: 10px;
        color: #888;
    }

    .recent-files-separator {
        height: 1px;
        background-color: #e1e5e9;
        margin: 8px 0;
    }

    @media (prefers-color-scheme: dark) {
        .recent-files-menu {
            background: #252526;
            border-color: #3c3c3c;
        }
        
        .recent-file-item {
            border-bottom-color: #3c3c3c;
        }
        
        .recent-file-item:hover {
            background-color: #2a2d2e;
        }
        
        .recent-file-name {
            color: #cccccc;
        }
        
        .recent-file-path {
            color: #999;
        }
        
        .recent-file-date {
            color: #777;
        }
        
        .recent-files-separator {
            background-color: #3c3c3c;
        }
    }

    /* File drop zone styling */
    body.drag-highlight::before {
        content: "Drop EDI file here to open";
        position: fixed;
        top: 50%;
        left: 50%;
        transform: translate(-50%, -50%);
        background: rgba(0, 123, 255, 0.9);
        color: white;
        padding: 20px 40px;
        border-radius: 8px;
        font-size: 18px;
        font-weight: 500;
        z-index: 10000;
        pointer-events: none;
    }
`;
document.head.appendChild(fileManagerStyle);

// Initialize the file manager when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    new FileManager();
});