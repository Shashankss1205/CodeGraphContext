// Main application logic
class App {
    constructor() {
        this.queryInput = document.getElementById('queryInput');
        this.runBtn = document.getElementById('runQueryBtn');
        this.clearBtn = document.getElementById('clearBtn');

        // Stats
        this.nodeCountEl = document.getElementById('nodeCount');
        this.edgeCountEl = document.getElementById('edgeCount');
        this.queryTimeEl = document.getElementById('queryTime');
        this.totalNodesEl = document.getElementById('totalNodes');

        // Inspector
        this.inspectorPanel = document.getElementById('inspectorPanel');
        this.inspectorTitle = document.getElementById('inspectorTitle');
        this.inspectorContent = document.getElementById('inspectorContent');
        this.closeInspectorBtn = document.getElementById('closeInspectorBtn');

        // Views
        this.viewIcons = document.querySelectorAll('.activity-icon[data-view]');
        this.views = document.querySelectorAll('.panel-view');
        this.actionBtns = document.querySelectorAll('.action-btn');

        this.init();
    }

    init() {
        // Run query on button click
        this.runBtn.addEventListener('click', () => this.runQuery());

        // Run query on Ctrl+Enter
        this.queryInput.addEventListener('keydown', (e) => {
            if (e.ctrlKey && e.key === 'Enter') {
                this.runQuery();
            }
        });

        // Clear button
        this.clearBtn.addEventListener('click', () => {
            if (window.graphViz) window.graphViz.clear();
            this.updateStats(0, 0);
            this.hideInspector();
        });

        // Close inspector
        this.closeInspectorBtn.addEventListener('click', () => this.hideInspector());

        // View Switching
        this.viewIcons.forEach(icon => {
            icon.addEventListener('click', () => {
                // Deactivate all icons
                this.viewIcons.forEach(i => i.classList.remove('active'));
                // Activate clicked
                icon.classList.add('active');

                // Hide all views
                this.views.forEach(v => v.classList.add('hidden'));
                // Show target view
                const viewId = icon.dataset.view;
                document.getElementById(viewId).classList.remove('hidden');
            });
        });

        // Action Buttons
        this.actionBtns.forEach(btn => {
            btn.addEventListener('click', () => {
                const query = btn.dataset.query;
                if (query) {
                    this.queryInput.value = query;
                    this.runQuery();
                }
            });
        });

        // Initial run if query is present
        if (this.queryInput.value.trim()) {
            this.runQuery();
        }

        // Load Initial Stats
        this.loadQuickStats();
    }

    async loadQuickStats() {
        try {
            const response = await fetch('/api/stats');
            const data = await response.json();

            if (data.success && data.total_nodes !== undefined) {
                this.totalNodesEl.textContent = data.total_nodes.toLocaleString();
            } else {
                this.totalNodesEl.textContent = "?";
            }
        } catch (e) {
            console.log("Stats load error", e);
            this.totalNodesEl.textContent = "?";
        }
    }

    async runQuery() {
        const query = this.queryInput.value.trim();
        if (!query) return;

        // Show loading state
        const originalBtnHTML = this.runBtn.innerHTML;
        this.runBtn.innerHTML = '<span class="loading"></span>';
        this.runBtn.disabled = true;

        const startTime = performance.now();

        try {
            const data = await window.queryExecutor.executeQuery(query);

            if (data.success) {
                if (window.graphViz) {
                    window.graphViz.loadGraph(data);
                }
                const duration = Math.round(performance.now() - startTime);
                if (this.queryTimeEl) this.queryTimeEl.textContent = `${duration}ms`;

                // Update total nodes if it was an "All" query
                if (data.count && data.count > 100) {
                    this.loadQuickStats(); // Refresh stats
                }
            } else {
                console.error("Query failed:", data.error);
                alert(`Query failed:\n${data.error}`);
            }
        } catch (err) {
            console.error(err);
        } finally {
            this.runBtn.innerHTML = originalBtnHTML;
            this.runBtn.disabled = false;
        }
    }

    updateStats(nodes, edges) {
        if (this.nodeCountEl) this.nodeCountEl.textContent = `${nodes} Nodes`;
        if (this.edgeCountEl) this.edgeCountEl.textContent = `${edges} Relationships`;
    }

    showNodeDetails(data) {
        if (this.inspectorTitle) {
            this.inspectorTitle.textContent = `Node: ${(data.label || 'Node')}`;
        }
        this.renderProperties(data.properties);
        if (this.inspectorPanel) this.inspectorPanel.classList.add('open');
    }

    showEdgeDetails(data) {
        if (this.inspectorTitle) {
            this.inspectorTitle.textContent = `REL: ${data.type}`;
        }
        this.renderProperties(data.properties);
        if (this.inspectorPanel) this.inspectorPanel.classList.add('open');
    }

    hideInspector() {
        if (this.inspectorPanel) this.inspectorPanel.classList.remove('open');
    }

    renderProperties(props) {
        if (!this.inspectorContent) return;

        if (!props || Object.keys(props).length === 0) {
            this.inspectorContent.innerHTML = '<div style="padding:10px; color:#666; font-style:italic">No properties</div>';
            return;
        }

        let html = '';
        for (const [key, value] of Object.entries(props)) {
            let displayValue = value;
            if (typeof value === 'object') {
                displayValue = JSON.stringify(value);
            }
            displayValue = String(displayValue)
                .replace(/&/g, "&amp;")
                .replace(/</g, "&lt;")
                .replace(/>/g, "&gt;");

            html += `
                <div class="prop-row">
                    <div class="prop-key">${key}</div>
                    <div class="prop-value">${displayValue}</div>
                </div>
            `;
        }
        this.inspectorContent.innerHTML = html;
    }
}

// Global instance
window.app = null;
document.addEventListener('DOMContentLoaded', () => {
    window.app = new App();
});
