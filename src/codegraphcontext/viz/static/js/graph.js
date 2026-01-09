// Graph visualization using Cytoscape.js
class GraphVisualizer {
    constructor(containerId) {
        this.container = document.getElementById(containerId);
        this.cy = null;
        this.init();
    }

    init() {
        // Neo4j Color Palette
        const nodeColors = {
            'Function': '#33C6FF',  // Light Blue
            'Class': '#F1C40F',     // Gold
            'File': '#2ECC71',      // Green
            'Module': '#E74C3C',    // Red
            'Repository': '#E67E22', // Orange
            'default': '#7b2890ff'    // Purple
        };

        this.cy = cytoscape({
            container: this.container,

            style: [
                {
                    selector: 'node',
                    style: {
                        'background-color': function (ele) {
                            const type = ele.data('type');
                            return nodeColors[type] || nodeColors.default;
                        },
                        'label': function (ele) {
                            // strictly fit inside the circle like Neo4j
                            let label = ele.data('label') || '';
                            if (label.length > 8) {
                                return label.substring(0, 7) + '..';
                            }
                            return label;
                        },
                        'color': '#1D2125', // Dark text on bright circles (Neo4j style)
                        'text-valign': 'center',
                        'text-halign': 'center',
                        'font-size': '12px',
                        'font-weight': 'bold',
                        'font-family': 'sans-serif',

                        // PERFECT CIRCLES
                        'width': 60,
                        'height': 60,

                        'border-width': 2,
                        'border-color': '#fff',
                        'border-opacity': 0.8,
                        'overlay-padding': '4px',
                        'z-index': 10
                    }
                },
                {
                    selector: 'node:selected',
                    style: {
                        'border-width': 4,
                        'border-color': '#fff',
                        'border-opacity': 1,
                        'background-blacken': -0.1
                    }
                },
                {
                    selector: 'edge',
                    style: {
                        'width': 1,
                        'line-color': '#A5ABB6',
                        'target-arrow-color': '#A5ABB6',
                        'target-arrow-shape': 'triangle',
                        'curve-style': 'bezier',
                        'arrow-scale': 1.0,
                        'label': '', // Clean edges by default
                        'z-index': 1
                    }
                },
                {
                    selector: 'edge:selected',
                    style: {
                        'line-color': '#008CC1',
                        'target-arrow-color': '#008CC1',
                        'width': 3,
                        'label': 'data(type)',
                        'font-size': '10px',
                        'color': '#fff',
                        'text-background-color': '#1D2125',
                        'text-background-opacity': 1,
                        'text-background-padding': '2px',
                        'z-index': 20
                    }
                },
                {
                    selector: '.highlighted',
                    style: {
                        'border-width': 4,
                        'border-color': '#33C6FF',
                        'transition-duration': '0.3s'
                    }
                },
                {
                    selector: '.faded',
                    style: {
                        'opacity': 0.1,
                        'text-opacity': 0
                    }
                }
            ],

            layout: {
                name: 'cose',
                animate: false
            },

            wheelSensitivity: 0.2,
            minZoom: 0.1,
            maxZoom: 3
        });

        this.setupEvents();
    }

    setupEvents() {
        // Node click - show details
        this.cy.on('tap', 'node', (evt) => {
            window.app.showNodeDetails(evt.target.data());
        });

        // Edge click - show details
        this.cy.on('tap', 'edge', (evt) => {
            window.app.showEdgeDetails(evt.target.data());
        });

        // Double click - expand neighbors
        this.cy.on('dbltap', 'node', (evt) => {
            this.highlightNeighborhood(evt.target);
        });

        // Background click - hide inspector & reset highlight
        this.cy.on('tap', (evt) => {
            if (evt.target === this.cy) {
                window.app.hideInspector();
                this.resetHighlight();
            }
        });
    }

    highlightNeighborhood(node) {
        this.resetHighlight();

        const neighborhood = node.neighborhood().add(node);

        this.cy.elements().addClass('faded');
        neighborhood.removeClass('faded').addClass('highlighted');

        // Fit to highlighted elements
        this.cy.fit(neighborhood, 50);
    }

    resetHighlight() {
        this.cy.elements().removeClass('faded').removeClass('highlighted');
    }

    loadGraph(data) {
        // Clear existing graph
        this.cy.elements().remove();

        // Add nodes
        data.nodes.forEach(node => {
            this.cy.add({
                group: 'nodes',
                data: node
            });
        });

        // Add edges
        data.edges.forEach(edge => {
            this.cy.add({
                group: 'edges',
                data: edge
            });
        });

        // IMPROVED LAYOUT - Prevent Overlap
        const layout = this.cy.layout({
            name: 'cose',
            animate: true,
            animationDuration: 1500,
            animationEasing: 'ease-out',

            // Strong collision prevention
            nodeRepulsion: 100000,        // Increased from 8000 - stronger push
            nodeOverlap: 150,              // Minimum spacing between nodes
            idealEdgeLength: 400,         // Increased from 100 - longer edges
            edgeElasticity: 30,

            // Reduced gravity to allow spreading
            gravity: 1,                  // Reduced from 20

            // Layout quality
            numIter: 3000,                // More iterations for better layout
            initialTemp: 500,
            coolingFactor: 0.95,
            minTemp: 1.0,

            // Start configuration
            randomize: true,              // Random initial positions
            fit: true,
            padding: 150                   // More padding around edges
        });

        layout.run();

        // Update stats
        window.app.updateStats(data.nodes.length, data.edges.length);
    }

    clear() {
        this.cy.elements().remove();
        this.resetHighlight();
    }

    fitToView() {
        this.cy.fit(null, 50);
    }

    exportPNG() {
        const png = this.cy.png({
            full: true,
            scale: 2,
            bg: '#1a1a1a'
        });

        const link = document.createElement('a');
        link.download = 'codegraph.png';
        link.href = png;
        link.click();
    }
}

// Initialize graph when DOM is ready
window.graphViz = null;
document.addEventListener('DOMContentLoaded', () => {
    window.graphViz = new GraphVisualizer('cy');
});
