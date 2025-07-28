/**
 * Tree View Component for EDI Structure
 * Displays parsed EDI data in a hierarchical tree format
 */

class TreeView {
    constructor() {
        this.container = document.getElementById('tree-view');
        this.data = null;
        this.expandedNodes = new Set();
        this.selectedNode = null;
        
        this.init();
    }

    init() {
        this.setupEventListeners();
        
        // Expose globally
        window.treeView = this;
    }

    setupEventListeners() {
        // Expand/collapse all buttons
        document.getElementById('expand-all-btn').addEventListener('click', () => {
            this.expandAll();
        });
        
        document.getElementById('collapse-all-btn').addEventListener('click', () => {
            this.collapseAll();
        });
        
        // Tree container clicks for node selection
        this.container.addEventListener('click', (event) => {
            this.handleNodeClick(event);
        });
        
        // Double-click to expand/collapse
        this.container.addEventListener('dblclick', (event) => {
            this.handleNodeDoubleClick(event);
        });
        
        // Right-click context menu
        this.container.addEventListener('contextmenu', (event) => {
            this.handleNodeContextMenu(event);
        });
    }

    loadData(parsedData) {
        this.data = parsedData;
        this.render();
        
        // Hide empty state
        const emptyState = this.container.querySelector('.empty-state');
        if (emptyState) {
            emptyState.style.display = 'none';
        }
        
        // Enable tree controls
        document.getElementById('expand-all-btn').disabled = false;
        document.getElementById('collapse-all-btn').disabled = false;
    }

    render() {
        if (!this.data) {
            this.showEmptyState();
            return;
        }

        const treeHTML = this.buildTreeHTML(this.data, 'root');
        this.container.innerHTML = treeHTML;
        
        // Apply expand/collapse states
        this.applyExpandStates();
    }

    buildTreeHTML(data, path = '') {
        if (!data) return '';

        let html = '';

        if (Array.isArray(data)) {
            data.forEach((item, index) => {
                const itemPath = `${path}[${index}]`;
                html += this.createArrayItemNode(item, index, itemPath);
            });
        } else if (typeof data === 'object') {
            Object.entries(data).forEach(([key, value]) => {
                const itemPath = path ? `${path}.${key}` : key;
                html += this.createObjectPropertyNode(key, value, itemPath);
            });
        } else {
            html += this.createValueNode(data, path);
        }

        return html;
    }

    createArrayItemNode(item, index, path) {
        const hasChildren = this.hasChildren(item);
        const isExpanded = this.expandedNodes.has(path);
        const displayValue = this.getDisplayValue(item);
        
        return `
            <div class="tree-node" data-path="${path}">
                <div class="tree-node-content" data-path="${path}">
                    <span class="tree-node-icon">
                        ${hasChildren ? (isExpanded ? '▼' : '▶') : '●'}
                    </span>
                    <span class="tree-node-label">[${index}]</span>
                    <span class="tree-node-value">${displayValue}</span>
                </div>
                ${hasChildren && isExpanded ? `
                    <div class="tree-children">
                        ${this.buildTreeHTML(item, path)}
                    </div>
                ` : ''}
            </div>
        `;
    }

    createObjectPropertyNode(key, value, path) {
        const hasChildren = this.hasChildren(value);
        const isExpanded = this.expandedNodes.has(path);
        const displayValue = this.getDisplayValue(value);
        const nodeType = this.getNodeType(key, value);
        
        return `
            <div class="tree-node ${nodeType}" data-path="${path}">
                <div class="tree-node-content" data-path="${path}">
                    <span class="tree-node-icon">
                        ${hasChildren ? (isExpanded ? '▼' : '▶') : this.getNodeIcon(key, value)}
                    </span>
                    <span class="tree-node-label">${this.formatLabel(key)}</span>
                    <span class="tree-node-value">${displayValue}</span>
                </div>
                ${hasChildren && isExpanded ? `
                    <div class="tree-children">
                        ${this.buildTreeHTML(value, path)}
                    </div>
                ` : ''}
            </div>
        `;
    }

    createValueNode(value, path) {
        return `
            <div class="tree-node tree-value" data-path="${path}">
                <div class="tree-node-content" data-path="${path}">
                    <span class="tree-node-icon">●</span>
                    <span class="tree-node-label">value</span>
                    <span class="tree-node-value">${this.escapeHTML(String(value))}</span>
                </div>
            </div>
        `;
    }

    hasChildren(value) {
        if (Array.isArray(value)) {
            return value.length > 0;
        }
        if (typeof value === 'object' && value !== null) {
            return Object.keys(value).length > 0;
        }
        return false;
    }

    getDisplayValue(value) {
        if (Array.isArray(value)) {
            return `Array[${value.length}]`;
        }
        if (typeof value === 'object' && value !== null) {
            const keys = Object.keys(value);
            if (keys.length === 0) return '{}';
            if (keys.length === 1) return `{${keys[0]}}`;
            return `{${keys.length} properties}`;
        }
        if (typeof value === 'string') {
            if (value.length > 50) {
                return `"${this.escapeHTML(value.substring(0, 47))}..."`;
            }
            return `"${this.escapeHTML(value)}"`;
        }
        return this.escapeHTML(String(value));
    }

    getNodeType(key, value) {
        // Classify nodes based on EDI structure
        if (key === 'interchanges') return 'interchange-container';
        if (key === 'functional_groups') return 'functional-group-container';
        if (key === 'transactions') return 'transaction-container';
        if (key === 'claims') return 'claims-container';
        if (key === 'line_items') return 'line-items-container';
        
        if (key === 'header') return 'header-node';
        if (key === 'payer' || key === 'payee') return 'entity-node';
        if (key === 'claim' || key.startsWith('claim_')) return 'claim-node';
        if (key === 'service' || key.startsWith('service_')) return 'service-node';
        if (key.includes('financial') || key.includes('amount')) return 'financial-node';
        if (key.includes('date') || key.includes('time')) return 'date-node';
        if (key.includes('code') || key.includes('id')) return 'code-node';
        
        return 'default-node';
    }

    getNodeIcon(key, value) {
        const type = this.getNodeType(key, value);
        
        const icons = {
            'interchange-container': '🔄',
            'functional-group-container': '📦',
            'transaction-container': '📄',
            'claims-container': '🏥',
            'line-items-container': '📋',
            'header-node': '📋',
            'entity-node': '🏢',
            'claim-node': '💊',
            'service-node': '🔧',
            'financial-node': '💰',
            'date-node': '📅',
            'code-node': '🏷️',
            'default-node': '●'
        };
        
        return icons[type] || '●';
    }

    formatLabel(key) {
        // Convert snake_case to Title Case
        return key
            .split('_')
            .map(word => word.charAt(0).toUpperCase() + word.slice(1))
            .join(' ');
    }

    escapeHTML(str) {
        const div = document.createElement('div');
        div.textContent = str;
        return div.innerHTML;
    }

    handleNodeClick(event) {
        const nodeContent = event.target.closest('.tree-node-content');
        if (!nodeContent) return;
        
        const path = nodeContent.dataset.path;
        
        // Clear previous selection
        this.container.querySelectorAll('.tree-node-content.selected').forEach(node => {
            node.classList.remove('selected');
        });
        
        // Select clicked node
        nodeContent.classList.add('selected');
        this.selectedNode = path;
        
        // Notify other components
        this.notifyNodeSelection(path);
    }

    handleNodeDoubleClick(event) {
        const nodeContent = event.target.closest('.tree-node-content');
        if (!nodeContent) return;
        
        const path = nodeContent.dataset.path;
        this.toggleNode(path);
    }

    handleNodeContextMenu(event) {
        event.preventDefault();
        
        const nodeContent = event.target.closest('.tree-node-content');
        if (!nodeContent) return;
        
        const path = nodeContent.dataset.path;
        this.showNodeContextMenu(event, path);
    }

    toggleNode(path) {
        if (this.expandedNodes.has(path)) {
            this.expandedNodes.delete(path);
        } else {
            this.expandedNodes.add(path);
        }
        this.render();
    }

    expandAll() {
        this.expandedNodes.clear();
        this.addAllPaths(this.data, 'root');
        this.render();
    }

    collapseAll() {
        this.expandedNodes.clear();
        this.render();
    }

    addAllPaths(data, path = '') {
        if (Array.isArray(data)) {
            data.forEach((item, index) => {
                const itemPath = `${path}[${index}]`;
                this.expandedNodes.add(itemPath);
                if (this.hasChildren(item)) {
                    this.addAllPaths(item, itemPath);
                }
            });
        } else if (typeof data === 'object' && data !== null) {
            Object.entries(data).forEach(([key, value]) => {
                const itemPath = path ? `${path}.${key}` : key;
                this.expandedNodes.add(itemPath);
                if (this.hasChildren(value)) {
                    this.addAllPaths(value, itemPath);
                }
            });
        }
    }

    applyExpandStates() {
        // This is handled in the render method by checking expandedNodes
    }

    notifyNodeSelection(path) {
        // Notify editor to highlight corresponding segment
        if (window.ediEditor && path) {
            // Extract segment information from path
            const segmentMatch = path.match(/\.(transaction_data)\.(.+)/);
            if (segmentMatch) {
                window.ediEditor.highlightSegment(path);
            }
        }
        
        // Update status bar
        document.getElementById('file-status').textContent = `Selected: ${path}`;
    }

    showNodeContextMenu(event, path) {
        // Create context menu for tree nodes
        const menu = document.createElement('div');
        menu.className = 'tree-context-menu';
        menu.innerHTML = `
            <ul>
                <li data-action="copy-path">Copy Path</li>
                <li data-action="copy-value">Copy Value</li>
                <li class="separator"></li>
                <li data-action="expand-branch">Expand Branch</li>
                <li data-action="collapse-branch">Collapse Branch</li>
                <li class="separator"></li>
                <li data-action="goto-segment">Go to Segment</li>
                <li data-action="validate-node">Validate Node</li>
            </ul>
        `;
        
        menu.style.position = 'fixed';
        menu.style.left = event.pageX + 'px';
        menu.style.top = event.pageY + 'px';
        menu.style.zIndex = '2000';
        
        document.body.appendChild(menu);
        
        // Handle menu item clicks
        menu.addEventListener('click', (e) => {
            const action = e.target.dataset.action;
            if (action) {
                this.handleContextMenuAction(action, path);
            }
            document.body.removeChild(menu);
        });
        
        // Close menu when clicking elsewhere
        setTimeout(() => {
            document.addEventListener('click', function closeMenu() {
                if (document.body.contains(menu)) {
                    document.body.removeChild(menu);
                }
                document.removeEventListener('click', closeMenu);
            });
        }, 100);
    }

    handleContextMenuAction(action, path) {
        switch (action) {
            case 'copy-path':
                this.copyToClipboard(path);
                break;
            case 'copy-value':
                const value = this.getValueAtPath(path);
                this.copyToClipboard(JSON.stringify(value, null, 2));
                break;
            case 'expand-branch':
                this.expandBranch(path);
                break;
            case 'collapse-branch':
                this.collapseBranch(path);
                break;
            case 'goto-segment':
                if (window.ediEditor) {
                    window.ediEditor.highlightSegment(path);
                }
                break;
            case 'validate-node':
                this.validateNode(path);
                break;
        }
    }

    copyToClipboard(text) {
        navigator.clipboard.writeText(text).then(() => {
            document.getElementById('file-status').textContent = 'Copied to clipboard';
            setTimeout(() => {
                document.getElementById('file-status').textContent = 'Ready';
            }, 2000);
        });
    }

    getValueAtPath(path) {
        const parts = path.split(/[.\[\]]/).filter(Boolean);
        let current = this.data;
        
        for (const part of parts) {
            if (current === null || current === undefined) {
                return null;
            }
            
            if (Array.isArray(current) && /^\d+$/.test(part)) {
                current = current[parseInt(part)];
            } else if (typeof current === 'object') {
                current = current[part];
            } else {
                return null;
            }
        }
        
        return current;
    }

    expandBranch(path) {
        this.expandedNodes.add(path);
        const value = this.getValueAtPath(path);
        if (value) {
            this.addAllPaths(value, path);
        }
        this.render();
    }

    collapseBranch(path) {
        // Remove this path and all sub-paths
        const pathsToRemove = Array.from(this.expandedNodes).filter(p => 
            p === path || p.startsWith(path + '.') || p.startsWith(path + '[')
        );
        
        pathsToRemove.forEach(p => this.expandedNodes.delete(p));
        this.render();
    }

    validateNode(path) {
        // Trigger validation for specific node
        if (window.ediApp) {
            window.ediApp.validateFile();
        }
    }

    showEmptyState() {
        this.container.innerHTML = `
            <div class="empty-state">
                <div class="empty-icon">🌳</div>
                <h3>No Structure Available</h3>
                <p>Parse an EDI file to see its hierarchical structure</p>
            </div>
        `;
    }

    // Public API methods
    selectNode(path) {
        this.selectedNode = path;
        
        // Clear previous selection
        this.container.querySelectorAll('.tree-node-content.selected').forEach(node => {
            node.classList.remove('selected');
        });
        
        // Select new node
        const nodeContent = this.container.querySelector(`[data-path="${path}"]`);
        if (nodeContent) {
            nodeContent.classList.add('selected');
            nodeContent.scrollIntoView({ behavior: 'smooth', block: 'center' });
        }
    }

    expandToPath(path) {
        // Expand all parent nodes to make path visible
        const parts = path.split(/[.\[\]]/).filter(Boolean);
        let currentPath = '';
        
        for (let i = 0; i < parts.length; i++) {
            if (i === 0) {
                currentPath = parts[i];
            } else if (/^\d+$/.test(parts[i])) {
                currentPath += `[${parts[i]}]`;
            } else {
                currentPath += `.${parts[i]}`;
            }
            
            this.expandedNodes.add(currentPath);
        }
        
        this.render();
        this.selectNode(path);
    }

    filter(searchTerm) {
        // Simple filtering - hide nodes that don't match
        if (!searchTerm) {
            this.container.querySelectorAll('.tree-node').forEach(node => {
                node.style.display = '';
            });
            return;
        }
        
        const term = searchTerm.toLowerCase();
        this.container.querySelectorAll('.tree-node').forEach(node => {
            const label = node.querySelector('.tree-node-label').textContent.toLowerCase();
            const value = node.querySelector('.tree-node-value').textContent.toLowerCase();
            
            if (label.includes(term) || value.includes(term)) {
                node.style.display = '';
                // Show parent nodes
                let parent = node.parentElement;
                while (parent && parent.classList.contains('tree-children')) {
                    parent.style.display = '';
                    parent = parent.parentElement?.parentElement;
                }
            } else {
                node.style.display = 'none';
            }
        });
    }
}

// Add CSS for tree context menu
const treeStyle = document.createElement('style');
treeStyle.textContent = `
    .tree-context-menu {
        background-color: white;
        border: 1px solid #ddd;
        border-radius: 6px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        min-width: 150px;
    }

    .tree-context-menu ul {
        list-style: none;
        margin: 0;
        padding: 4px 0;
    }

    .tree-context-menu li {
        padding: 8px 16px;
        cursor: pointer;
        font-size: 13px;
        color: #333;
    }

    .tree-context-menu li:hover {
        background-color: #f8f9fa;
    }

    .tree-context-menu li.separator {
        height: 1px;
        background-color: #e1e5e9;
        margin: 4px 0;
        padding: 0;
        cursor: default;
    }

    .tree-context-menu li.separator:hover {
        background-color: #e1e5e9;
    }

    /* Enhanced tree node styles */
    .tree-node.interchange-container > .tree-node-content {
        background-color: #e3f2fd;
        border-left: 3px solid #2196f3;
    }

    .tree-node.functional-group-container > .tree-node-content {
        background-color: #f3e5f5;
        border-left: 3px solid #9c27b0;
    }

    .tree-node.transaction-container > .tree-node-content {
        background-color: #e8f5e8;
        border-left: 3px solid #4caf50;
    }

    .tree-node.claims-container > .tree-node-content {
        background-color: #fff3e0;
        border-left: 3px solid #ff9800;
    }

    .tree-node.financial-node > .tree-node-content {
        color: #2e7d32;
        font-weight: 500;
    }

    .tree-node.date-node > .tree-node-content {
        color: #7b1fa2;
    }

    .tree-node.code-node > .tree-node-content {
        color: #1976d2;
        font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
    }

    @media (prefers-color-scheme: dark) {
        .tree-context-menu {
            background-color: #252526;
            border-color: #3c3c3c;
        }
        
        .tree-context-menu li {
            color: #cccccc;
        }
        
        .tree-context-menu li:hover {
            background-color: #2a2d2e;
        }
        
        .tree-node.interchange-container > .tree-node-content {
            background-color: #1e3a8a;
        }
        
        .tree-node.functional-group-container > .tree-node-content {
            background-color: #581c87;
        }
        
        .tree-node.transaction-container > .tree-node-content {
            background-color: #166534;
        }
        
        .tree-node.claims-container > .tree-node-content {
            background-color: #9a3412;
        }
    }
`;
document.head.appendChild(treeStyle);

// Initialize the tree view when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    new TreeView();
});