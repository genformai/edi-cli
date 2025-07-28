/**
 * Validation Results Component
 * Displays validation errors, warnings, and info messages
 */

class ValidationPanel {
    constructor() {
        this.container = document.getElementById('validation-results');
        this.results = null;
        this.filteredResults = null;
        this.currentFilter = 'all'; // all, errors, warnings, info
        
        this.init();
    }

    init() {
        this.setupEventListeners();
        
        // Expose globally
        window.validation = this;
    }

    setupEventListeners() {
        // Panel controls
        document.getElementById('clear-errors-btn').addEventListener('click', () => {
            this.clear();
        });
        
        document.getElementById('export-errors-btn').addEventListener('click', () => {
            this.exportResults();
        });
        
        document.getElementById('toggle-errors-btn').addEventListener('click', () => {
            this.togglePanel();
        });
        
        // Container clicks for error navigation
        this.container.addEventListener('click', (event) => {
            this.handleErrorClick(event);
        });
        
        // Add filter buttons
        this.addFilterControls();
    }

    addFilterControls() {
        const header = document.querySelector('#validation-panel .panel-header');
        const filterContainer = document.createElement('div');
        filterContainer.className = 'validation-filters';
        filterContainer.innerHTML = `
            <button class="filter-btn active" data-filter="all">All</button>
            <button class="filter-btn" data-filter="errors">Errors</button>
            <button class="filter-btn" data-filter="warnings">Warnings</button>
            <button class="filter-btn" data-filter="info">Info</button>
        `;
        
        // Insert before controls
        const controls = header.querySelector('.panel-controls');
        header.insertBefore(filterContainer, controls);
        
        // Add filter event listeners
        filterContainer.addEventListener('click', (event) => {
            if (event.target.classList.contains('filter-btn')) {
                this.setFilter(event.target.dataset.filter);
                
                // Update active state
                filterContainer.querySelectorAll('.filter-btn').forEach(btn => {
                    btn.classList.remove('active');
                });
                event.target.classList.add('active');
            }
        });
    }

    loadResults(validationResults) {
        this.results = validationResults;
        this.filteredResults = this.applyFilter(validationResults);
        this.render();
        
        // Hide empty state
        const emptyState = this.container.querySelector('.empty-state');
        if (emptyState) {
            emptyState.style.display = 'none';
        }
        
        // Enable export button
        document.getElementById('export-errors-btn').disabled = false;
        
        // Update error counts in header
        this.updateErrorCounts();
        
        // Show panel if it's hidden and there are errors
        if (validationResults.error_count > 0) {
            this.showPanel();
        }
        
        // Add validation decorations to editor
        if (window.ediEditor) {
            window.ediEditor.addValidationDecorations(validationResults);
        }
    }

    render() {
        if (!this.filteredResults || this.filteredResults.total_issues === 0) {
            this.showEmptyState();
            return;
        }

        let html = '';
        
        // Render errors
        if (this.filteredResults.errors && this.filteredResults.errors.length > 0) {
            this.filteredResults.errors.forEach(error => {
                html += this.createValidationItem(error, 'error');
            });
        }
        
        // Render warnings
        if (this.filteredResults.warnings && this.filteredResults.warnings.length > 0) {
            this.filteredResults.warnings.forEach(warning => {
                html += this.createValidationItem(warning, 'warning');
            });
        }
        
        // Render info messages
        if (this.filteredResults.info && this.filteredResults.info.length > 0) {
            this.filteredResults.info.forEach(info => {
                html += this.createValidationItem(info, 'info');
            });
        }
        
        this.container.innerHTML = html;
    }

    createValidationItem(item, severity) {
        const icon = this.getSeverityIcon(severity);
        const code = item.code ? `<span class="validation-code">${item.code}</span>` : '';
        
        return `
            <div class="validation-item ${severity}" 
                 data-path="${item.path || ''}" 
                 data-segment="${item.segment_id || ''}"
                 data-element="${item.element_position || ''}">
                <div class="validation-icon">${icon}</div>
                <div class="validation-content">
                    <div class="validation-message">
                        ${this.escapeHTML(item.message)}
                        ${code}
                    </div>
                    ${item.path ? `<div class="validation-path">${this.formatPath(item.path)}</div>` : ''}
                    ${item.rule_name ? `<div class="validation-rule">Rule: ${item.rule_name}</div>` : ''}
                </div>
                <div class="validation-actions">
                    <button class="btn btn-sm goto-btn" title="Go to location">📍</button>
                    ${item.segment_id ? `<button class="btn btn-sm info-btn" title="Segment info">ℹ️</button>` : ''}
                </div>
            </div>
        `;
    }

    getSeverityIcon(severity) {
        const icons = {
            error: '❌',
            warning: '⚠️',
            info: 'ℹ️'
        };
        return icons[severity] || '●';
    }

    formatPath(path) {
        // Format path to be more readable
        return path
            .replace(/interchange\[(\d+)\]/g, 'Interchange $1')
            .replace(/functional_group\[(\d+)\]/g, 'Group $1')
            .replace(/transaction\[(\d+)\]/g, 'Transaction $1')
            .replace(/\./g, ' → ');
    }

    escapeHTML(str) {
        const div = document.createElement('div');
        div.textContent = str;
        return div.innerHTML;
    }

    handleErrorClick(event) {
        const validationItem = event.target.closest('.validation-item');
        if (!validationItem) return;
        
        const button = event.target.closest('.btn');
        if (button) {
            event.stopPropagation();
            
            if (button.classList.contains('goto-btn')) {
                this.goToLocation(validationItem);
            } else if (button.classList.contains('info-btn')) {
                this.showSegmentInfo(validationItem);
            }
            return;
        }
        
        // Click on item itself - go to location
        this.goToLocation(validationItem);
    }

    goToLocation(validationItem) {
        const path = validationItem.dataset.path;
        const segment = validationItem.dataset.segment;
        const element = validationItem.dataset.element;
        
        // Highlight in editor
        if (window.ediEditor && path) {
            window.ediEditor.highlightSegment(path);
        }
        
        // Select in tree view
        if (window.treeView && path) {
            window.treeView.expandToPath(path);
        }
        
        // Update status
        document.getElementById('file-status').textContent = 
            `Navigated to: ${segment || 'location'}${element ? ` element ${element}` : ''}`;
        
        // Highlight the clicked validation item
        this.container.querySelectorAll('.validation-item.selected').forEach(item => {
            item.classList.remove('selected');
        });
        validationItem.classList.add('selected');
    }

    showSegmentInfo(validationItem) {
        const segment = validationItem.dataset.segment;
        const element = validationItem.dataset.element;
        
        if (segment && window.ediEditor) {
            // Trigger segment info popup in editor
            window.ediEditor.showSegmentInfo(segment, []);
        }
    }

    setFilter(filter) {
        this.currentFilter = filter;
        if (this.results) {
            this.filteredResults = this.applyFilter(this.results);
            this.render();
        }
    }

    applyFilter(results) {
        if (!results) return null;
        
        const filtered = {
            is_valid: results.is_valid,
            errors: [],
            warnings: [],
            info: [],
            error_count: 0,
            warning_count: 0,
            info_count: 0,
            total_issues: 0
        };
        
        switch (this.currentFilter) {
            case 'errors':
                filtered.errors = results.errors || [];
                filtered.error_count = filtered.errors.length;
                break;
            case 'warnings':
                filtered.warnings = results.warnings || [];
                filtered.warning_count = filtered.warnings.length;
                break;
            case 'info':
                filtered.info = results.info || [];
                filtered.info_count = filtered.info.length;
                break;
            default: // 'all'
                filtered.errors = results.errors || [];
                filtered.warnings = results.warnings || [];
                filtered.info = results.info || [];
                filtered.error_count = filtered.errors.length;
                filtered.warning_count = filtered.warnings.length;
                filtered.info_count = filtered.info.length;
        }
        
        filtered.total_issues = filtered.error_count + filtered.warning_count + filtered.info_count;
        
        return filtered;
    }

    updateErrorCounts() {
        if (!this.results) return;
        
        const errorCount = document.getElementById('error-count');
        const warningCount = document.getElementById('warning-count');
        
        if (errorCount) {
            errorCount.textContent = `${this.results.error_count} error${this.results.error_count !== 1 ? 's' : ''}`;
        }
        
        if (warningCount) {
            warningCount.textContent = `${this.results.warning_count} warning${this.results.warning_count !== 1 ? 's' : ''}`;
        }
        
        // Update filter button badges
        const filterButtons = document.querySelectorAll('.validation-filters .filter-btn');
        filterButtons.forEach(btn => {
            const filter = btn.dataset.filter;
            let count = 0;
            
            switch (filter) {
                case 'errors':
                    count = this.results.error_count;
                    break;
                case 'warnings':
                    count = this.results.warning_count;
                    break;
                case 'info':
                    count = this.results.info_count;
                    break;
                case 'all':
                    count = this.results.total_issues;
                    break;
            }
            
            // Update button text with count
            const baseText = btn.textContent.replace(/ \(\d+\)/, '');
            btn.textContent = count > 0 ? `${baseText} (${count})` : baseText;
        });
    }

    clear() {
        this.results = null;
        this.filteredResults = null;
        this.showEmptyState();
        
        // Clear editor decorations
        if (window.ediEditor) {
            window.ediEditor.clearValidationDecorations();
        }
        
        // Reset error counts
        document.getElementById('error-count').textContent = '0 errors';
        document.getElementById('warning-count').textContent = '0 warnings';
        
        // Disable export button
        document.getElementById('export-errors-btn').disabled = true;
        
        // Reset filter buttons
        document.querySelectorAll('.validation-filters .filter-btn').forEach(btn => {
            const baseText = btn.textContent.replace(/ \(\d+\)/, '');
            btn.textContent = baseText;
        });
    }

    async exportResults() {
        if (!this.results) return;
        
        const { dialog } = require('electron').remote || require('@electron/remote');
        
        const result = await dialog.showSaveDialog({
            filters: [
                { name: 'JSON Files', extensions: ['json'] },
                { name: 'CSV Files', extensions: ['csv'] },
                { name: 'Text Files', extensions: ['txt'] }
            ],
            defaultPath: 'validation-results.json'
        });
        
        if (!result.canceled) {
            const { ipcRenderer } = require('electron');
            let content;
            
            const ext = require('path').extname(result.filePath).toLowerCase();
            
            switch (ext) {
                case '.csv':
                    content = this.exportAsCSV();
                    break;
                case '.txt':
                    content = this.exportAsText();
                    break;
                default:
                    content = JSON.stringify(this.results, null, 2);
            }
            
            const writeResult = await ipcRenderer.invoke('write-file', result.filePath, content);
            if (writeResult.success) {
                document.getElementById('file-status').textContent = 'Validation results exported';
            } else {
                console.error('Export failed:', writeResult.error);
            }
        }
    }

    exportAsCSV() {
        const lines = ['Severity,Message,Code,Path,Segment,Element,Rule'];
        
        const addItems = (items, severity) => {
            items.forEach(item => {
                const line = [
                    severity,
                    `"${item.message.replace(/"/g, '""')}"`,
                    item.code || '',
                    item.path || '',
                    item.segment_id || '',
                    item.element_position || '',
                    item.rule_name || ''
                ].join(',');
                lines.push(line);
            });
        };
        
        if (this.results.errors) addItems(this.results.errors, 'Error');
        if (this.results.warnings) addItems(this.results.warnings, 'Warning');
        if (this.results.info) addItems(this.results.info, 'Info');
        
        return lines.join('\n');
    }

    exportAsText() {
        const lines = [];
        lines.push('EDI Validation Results');
        lines.push('='.repeat(50));
        lines.push(`Total Issues: ${this.results.total_issues}`);
        lines.push(`Errors: ${this.results.error_count}`);
        lines.push(`Warnings: ${this.results.warning_count}`);
        lines.push(`Info: ${this.results.info_count}`);
        lines.push('');
        
        const addItems = (items, title) => {
            if (items && items.length > 0) {
                lines.push(title);
                lines.push('-'.repeat(title.length));
                
                items.forEach((item, index) => {
                    lines.push(`${index + 1}. ${item.message}`);
                    if (item.code) lines.push(`   Code: ${item.code}`);
                    if (item.path) lines.push(`   Path: ${item.path}`);
                    if (item.rule_name) lines.push(`   Rule: ${item.rule_name}`);
                    lines.push('');
                });
            }
        };
        
        addItems(this.results.errors, 'ERRORS');
        addItems(this.results.warnings, 'WARNINGS');
        addItems(this.results.info, 'INFO');
        
        return lines.join('\n');
    }

    togglePanel() {
        const panel = document.getElementById('validation-panel');
        const btn = document.getElementById('toggle-errors-btn');
        
        if (panel.classList.contains('hidden')) {
            this.showPanel();
        } else {
            this.hidePanel();
        }
    }

    showPanel() {
        const panel = document.getElementById('validation-panel');
        const btn = document.getElementById('toggle-errors-btn');
        
        panel.classList.remove('hidden');
        btn.textContent = 'Hide';
    }

    hidePanel() {
        const panel = document.getElementById('validation-panel');
        const btn = document.getElementById('toggle-errors-btn');
        
        panel.classList.add('hidden');
        btn.textContent = 'Show';
    }

    showEmptyState() {
        this.container.innerHTML = `
            <div class="empty-state">
                <div class="empty-icon">✅</div>
                <h3>No Validation Results</h3>
                <p>Run validation to see errors and warnings</p>
            </div>
        `;
    }

    // Public API methods
    highlightError(errorIndex, severity = 'error') {
        const items = this.container.querySelectorAll(`.validation-item.${severity}`);
        if (items[errorIndex]) {
            this.goToLocation(items[errorIndex]);
        }
    }

    getErrorSummary() {
        if (!this.results) return null;
        
        return {
            total: this.results.total_issues,
            errors: this.results.error_count,
            warnings: this.results.warning_count,
            info: this.results.info_count,
            isValid: this.results.is_valid
        };
    }
}

// Add CSS for validation filters and enhanced styling
const validationStyle = document.createElement('style');
validationStyle.textContent = `
    .validation-filters {
        display: flex;
        gap: 4px;
        margin-right: 12px;
    }

    .filter-btn {
        padding: 4px 8px;
        font-size: 11px;
        background-color: #f8f9fa;
        border: 1px solid #dee2e6;
        border-radius: 4px;
        cursor: pointer;
        transition: all 0.2s ease;
    }

    .filter-btn:hover {
        background-color: #e9ecef;
    }

    .filter-btn.active {
        background-color: #007bff;
        color: white;
        border-color: #007bff;
    }

    .validation-item {
        display: flex;
        align-items: flex-start;
        padding: 12px;
        margin: 6px 0;
        border-radius: 6px;
        border-left: 4px solid;
        cursor: pointer;
        transition: all 0.2s ease;
        position: relative;
    }

    .validation-item:hover {
        background-color: rgba(0,0,0,0.02);
        transform: translateX(2px);
    }

    .validation-item.selected {
        background-color: rgba(0,123,255,0.1);
        border-color: #007bff;
    }

    .validation-item.error {
        border-left-color: #dc3545;
        background-color: #fff5f5;
    }

    .validation-item.warning {
        border-left-color: #ffc107;
        background-color: #fffbf0;
    }

    .validation-item.info {
        border-left-color: #17a2b8;
        background-color: #f0f8ff;
    }

    .validation-icon {
        margin-right: 12px;
        margin-top: 2px;
        font-size: 14px;
    }

    .validation-content {
        flex: 1;
        min-width: 0;
    }

    .validation-message {
        font-weight: 500;
        margin-bottom: 4px;
        line-height: 1.4;
    }

    .validation-path {
        font-size: 12px;
        color: #666;
        font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
        margin-bottom: 2px;
    }

    .validation-rule {
        font-size: 11px;
        color: #888;
        font-style: italic;
    }

    .validation-code {
        font-size: 11px;
        color: #888;
        background-color: #f1f3f4;
        padding: 2px 6px;
        border-radius: 3px;
        margin-left: 8px;
        font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
    }

    .validation-actions {
        display: flex;
        gap: 4px;
        opacity: 0;
        transition: opacity 0.2s ease;
    }

    .validation-item:hover .validation-actions {
        opacity: 1;
    }

    .validation-actions .btn {
        padding: 4px 6px;
        font-size: 10px;
        background-color: transparent;
        border: 1px solid #ddd;
        border-radius: 3px;
        cursor: pointer;
    }

    .validation-actions .btn:hover {
        background-color: #f8f9fa;
    }

    @media (prefers-color-scheme: dark) {
        .filter-btn {
            background-color: #2d2d30;
            border-color: #3c3c3c;
            color: #cccccc;
        }
        
        .filter-btn:hover {
            background-color: #3c3c3c;
        }
        
        .filter-btn.active {
            background-color: #0e639c;
            border-color: #0e639c;
        }
        
        .validation-item.error {
            background-color: #2d1b1b;
        }
        
        .validation-item.warning {
            background-color: #2d2a1b;
        }
        
        .validation-item.info {
            background-color: #1b2a2d;
        }
        
        .validation-path {
            color: #999;
        }
        
        .validation-rule {
            color: #777;
        }
        
        .validation-code {
            background-color: #3c3c3c;
            color: #cccccc;
        }
    }
`;
document.head.appendChild(validationStyle);

// Initialize the validation panel when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    new ValidationPanel();
});