/**
 * map.js - D3.js Network Map Visualization
 *
 * Renders the product delivery network as a 2D map with:
 * - Nodes (manufacturing centers and distributors)
 * - Edges (connections with animated order flows)
 * - Interactive tooltips
 */

import * as d3 from 'd3';
import * as topojson from 'topojson-client';

export class NetworkMap {
    constructor(containerId, width, height) {
        this.containerId = containerId;
        this.width = width;
        this.height = height;

        // State
        this.nodes = [];
        this.edges = [];
        this.hoveredNode = null;  // Track currently hovered node
        this.selectedNode = null;  // Track clicked/selected node
        this.usStates = null;  // TopoJSON data for US states
        this.isRunning = false;  // Track if simulation is running

        // D3 selections
        this.svg = null;
        this.g = null;
        this.projection = null;
        this.path = null;

        // Initialize
        this.init();
    }

    init() {
        // Create SVG in the visualization container
        this.svg = d3.select(`#${this.containerId}`)
            .append('svg')
            .attr('width', this.width)
            .attr('height', this.height)
            .style('background', '#1a1a2e')
            .style('position', 'absolute')
            .style('top', '0')
            .style('left', '0');

        // Create main group for zoom
        this.g = this.svg.append('g');

        // Setup projection (Albers USA for US map)
        this.projection = d3.geoAlbersUsa()
            .translate([this.width / 2, this.height / 2])
            .scale(1000);

        // Setup path generator
        this.path = d3.geoPath().projection(this.projection);

        // Add zoom behavior
        const zoom = d3.zoom()
            .scaleExtent([0.5, 8])
            .on('zoom', (event) => {
                this.g.attr('transform', event.transform);
            });

        this.svg.call(zoom);

        // Click on background to deselect
        this.svg.on('click', () => this.selectNode(null));

        // Create layer groups (order matters for rendering)
        this.g.append('g').attr('class', 'states');  // States background
        this.g.append('g').attr('class', 'edges');
        this.g.append('g').attr('class', 'nodes');

        // Load US states data
        this.loadUSStates();

        console.log('[D3] Network map initialized');
    }

    /**
     * Load US states TopoJSON data
     */
    async loadUSStates() {
        try {
            // Fetch US states data from public CDN
            const response = await fetch('https://cdn.jsdelivr.net/npm/us-atlas@3/states-10m.json');
            const us = await response.json();

            // Convert TopoJSON to GeoJSON
            this.usStates = topojson.feature(us, us.objects.states);

            // Render states
            this.renderStates();

            console.log('[D3] US states loaded');
        } catch (error) {
            console.error('[D3] Failed to load US states:', error);
        }
    }

    /**
     * Render US state boundaries
     */
    renderStates() {
        if (!this.usStates) return;

        const statesGroup = this.g.select('.states');

        statesGroup
            .selectAll('path')
            .data(this.usStates.features)
            .enter()
            .append('path')
            .attr('d', this.path)
            .attr('fill', 'none')
            .attr('stroke', '#2a3f5f')
            .attr('stroke-width', 1)
            .attr('stroke-opacity', 0.5);
    }

    /**
     * Update visualization with new state
     */
    update(state) {
        this.nodes = state.nodes || [];
        this.edges = state.edges || [];
        this.isRunning = state.running || false;  // Track simulation running state
        this.currentTime = state.time || 0;  // Current simulation time

        this.renderEdges();
        this.renderNodes();

        // Update tooltip if hovering
        if (this.hoveredNode) {
            const updatedNode = this.nodes.find(n => n.id === this.hoveredNode.id);
            if (updatedNode) {
                this.updateTooltip(updatedNode);
            }
        }

        // Update details panel if node is selected
        if (this.selectedNode) {
            const updatedNode = this.nodes.find(n => n.id === this.selectedNode.id);
            if (updatedNode) {
                this.updateDetailsPanel(updatedNode);
            }
        }
    }

    /**
     * Render network edges (connections)
     */
    renderEdges() {
        const edgesGroup = this.g.select('.edges');

        // Bind data
        const edgeLines = edgesGroup
            .selectAll('line')
            .data(this.edges, d => `${d.edge_type}-${d.from}-${d.to}`);

        // Enter + Update
        edgeLines
            .enter()
            .append('line')
            .merge(edgeLines)
            .attr('x1', d => this.getNodeProjection(d.from)[0])
            .attr('y1', d => this.getNodeProjection(d.from)[1])
            .attr('x2', d => this.getNodeProjection(d.to)[0])
            .attr('y2', d => this.getNodeProjection(d.to)[1])
            .attr('stroke', d => {
                // Different colors for different edge types
                if (d.edge_type === 'structural') {
                    return 'rgba(100, 100, 100, 0.2)'; // Gray - network topology
                } else if (d.edge_type === 'order_placement') {
                    return 'rgba(59, 130, 246, 0.7)'; // Blue - pending orders
                } else {
                    return 'rgba(239, 68, 68, 0.7)'; // Red - delivery
                }
            })
            .attr('stroke-width', d => {
                // Structural edges: thin gray lines
                if (d.edge_type === 'structural') {
                    return 1;
                }
                // Thicker lines when orders are active
                if (d.active_orders > 0) {
                    return 2;
                } else {
                    return 1;
                }
            })
            .attr('stroke-opacity', d => {
                // Higher opacity when orders are active
                if (d.active_orders > 0) {
                    return 0.6;
                } else {
                    return 0.2;
                }
            });

        // Exit
        edgeLines.exit().remove();

        // Render animated order flows (only on delivery edges)
        this.renderOrderFlows();
    }

    /**
     * Render animated order flows - synchronized with simulation time
     * Multiple particles: one per active order
     */
    renderOrderFlows() {
        const edgesGroup = this.g.select('.edges');

        // Only show flows on delivery edges with CURRENTLY active orders
        const activeEdges = this.edges.filter(d => d.edge_type === 'delivery' && d.active_orders > 0);

        // Flatten: one particle per delivery (order)
        const deliveryParticles = activeEdges.flatMap(edge =>
            (edge.deliveries || []).map((delivery, index) => ({
                edge: edge,
                delivery: delivery,
                deliveryIndex: index,  // For visual offset
                key: delivery.order_id
            }))
        );

        // Bind data - use order_id as unique key
        const flows = edgesGroup
            .selectAll('circle.flow')
            .data(deliveryParticles, d => d.key);

        // Enter - create new flow particles
        const flowsEnter = flows
            .enter()
            .append('circle')
            .attr('class', 'flow')
            .attr('r', 3)
            .attr('fill', '#f59e0b')
            .attr('opacity', 0.7);

        // Update ALL particles (both new and existing) based on simulation time
        const self = this;
        const allFlows = flowsEnter.merge(flows);

        allFlows.each(function(d) {
            const circle = d3.select(this);

            // Get start and end positions
            const [x1, y1] = self.getNodeProjection(d.edge.from);
            const [x2, y2] = self.getNodeProjection(d.edge.to);

            if (!x1 || !x2) {
                return;
            }

            // Calculate progress based on simulation time for THIS delivery
            const deliveryStartTime = d.delivery.start_time || 0;
            const deliveryDuration = d.delivery.duration || 10;

            // Progress = (current_time - start_time) / duration
            // Clamp to [0, 1] range
            let progress = 0;
            if (deliveryDuration > 0) {
                progress = (self.currentTime - deliveryStartTime) / deliveryDuration;
                progress = Math.max(0, Math.min(1, progress));
            }

            // Calculate base position: interpolate between start and end
            let x = x1 + progress * (x2 - x1);
            let y = y1 + progress * (y2 - y1);

            // Add slight perpendicular offset to prevent perfect overlap
            // Offset based on delivery index (stagger particles)
            const offsetAmount = (d.deliveryIndex % 3) - 1;  // Range: -1 to +1 pixels
            const angle = Math.atan2(y2 - y1, x2 - x1);
            const perpAngle = angle + Math.PI / 2;  // 90 degrees rotation
            x += Math.cos(perpAngle) * offsetAmount;
            y += Math.sin(perpAngle) * offsetAmount;

            // Set position directly (no transition - smooth updates at 10fps)
            circle
                .attr('cx', x)
                .attr('cy', y);
        });

        // Exit - immediately remove when orders are fulfilled
        flows.exit().remove();
    }

    /**
     * Render network nodes
     */
    renderNodes() {
        const nodesGroup = this.g.select('.nodes');

        // Bind data for node groups
        const nodeGroups = nodesGroup
            .selectAll('g.node-group')
            .data(this.nodes, d => d.id);

        // Enter - create groups with shapes
        const groupsEnter = nodeGroups
            .enter()
            .append('g')
            .attr('class', 'node-group');

        // Add circles for all nodes
        groupsEnter
            .append('circle')
            .attr('class', 'node')
            .attr('id', d => d.id.replace(/[^a-zA-Z0-9]/g, '_'));

        // Update positions, sizes, and colors
        const allGroups = groupsEnter.merge(nodeGroups);

        allGroups
            .attr('transform', d => {
                const [x, y] = this.projection([d.location.lon, d.location.lat]);
                return `translate(${x},${y})`;
            })
            .on('mouseenter', (event, d) => this.showTooltip(event, d))
            .on('mouseleave', () => this.hideTooltip())
            .on('click', (event, d) => {
                event.stopPropagation();  // Prevent deselection
                this.selectNode(d);
            });

        // Calculate totals for normalization
        const manufacturingCenters = this.nodes.filter(n => n.type === 'manufacturing_center');
        const distributors = this.nodes.filter(n => n.type === 'distributor');

        const totalProduction = manufacturingCenters.reduce((sum, n) => sum + (n.state.production_rate || 0), 0);
        const totalOrders = distributors.reduce((sum, n) => sum + (n.state.orders_placed || 0), 0);

        allGroups.select('.node')
            .attr('r', d => {
                // Smaller size based on relative contribution
                if (d.type === 'manufacturing_center') {
                    const productionRate = d.state.production_rate || 0;
                    const ratio = totalProduction > 0 ? productionRate / totalProduction : 0.33;
                    return 4 + (ratio * 8); // Scale: 4-12px based on share
                } else {
                    const ordersPlaced = d.state.orders_placed || 0;
                    const ratio = totalOrders > 0 ? ordersPlaced / totalOrders : 0.125;
                    return 3 + (ratio * 6); // Scale: 3-9px based on share
                }
            })
            .attr('fill', d => {
                // Different colors with transparency for node types
                if (d.type === 'manufacturing_center') {
                    return 'rgba(16, 185, 129, 0.7)'; // Green with 70% opacity
                } else {
                    return 'rgba(139, 92, 246, 0.7)'; // Purple with 70% opacity
                }
            })
            .attr('stroke', d => {
                // Highlight selected node
                if (this.selectedNode && d.id === this.selectedNode.id) {
                    return '#fff';
                }
                return 'none';
            })
            .attr('stroke-width', d => {
                if (this.selectedNode && d.id === this.selectedNode.id) {
                    return 3;
                }
                return 0;
            });

        // Exit
        nodeGroups.exit().remove();

        // Add labels
        this.renderLabels();
    }

    /**
     * Render node labels
     */
    renderLabels() {
        const nodesGroup = this.g.select('.nodes');

        const labels = nodesGroup
            .selectAll('text')
            .data(this.nodes, d => d.id);

        labels
            .enter()
            .append('text')
            .attr('text-anchor', 'middle')
            .attr('dy', -15)
            .attr('fill', '#fff')
            .attr('font-size', '10px')
            .merge(labels)
            .attr('x', d => this.projection([d.location.lon, d.location.lat])[0])
            .attr('y', d => this.projection([d.location.lon, d.location.lat])[1])
            .text(d => {
                // Show just the city name
                if (d.type === 'manufacturing_center') {
                    return d.name.split(' ')[0]; // "Chicago" from "Chicago Manufacturing Center"
                } else {
                    // "New York" from "New York Distributor"
                    return d.name.replace(' Distributor', '');
                }
            });

        labels.exit().remove();
    }

    /**
     * Get projected coordinates for a node by ID
     */
    getNodeProjection(nodeId) {
        const node = this.nodes.find(n => n.id === nodeId);
        if (!node) return [0, 0];
        const projected = this.projection([node.location.lon, node.location.lat]);
        // Projection can return null for coordinates outside the projection bounds
        return projected || [0, 0];
    }

    /**
     * Get node element by ID (for edge positioning)
     */
    getNodeElement(nodeId) {
        return this.g.select(`#${nodeId.replace(/[^a-zA-Z0-9]/g, '_')}`).node();
    }

    /**
     * Show tooltip on hover
     */
    showTooltip(event, node) {
        this.hoveredNode = node;

        // Remove existing tooltip
        d3.select('#tooltip').remove();

        // Create tooltip
        const tooltip = d3.select('body')
            .append('div')
            .attr('id', 'tooltip')
            .style('position', 'absolute')
            .style('background', 'rgba(0, 0, 0, 0.9)')
            .style('color', '#fff')
            .style('padding', '10px')
            .style('border-radius', '4px')
            .style('font-size', '12px')
            .style('pointer-events', 'none')
            .style('z-index', '1000');

        this.updateTooltip(node);

        // Position tooltip
        tooltip
            .style('left', (event.pageX + 10) + 'px')
            .style('top', (event.pageY - 10) + 'px');
    }

    /**
     * Update tooltip content with latest node data
     */
    updateTooltip(node) {
        const tooltip = d3.select('#tooltip');
        if (tooltip.empty()) return;

        // Build tooltip content
        let content = `<strong>${node.name}</strong><br>`;
        content += `Type: ${node.type}<br>`;
        content += `Location: ${node.location.city}, ${node.location.state}<br><br>`;

        // Manufacturing center - show Phase 2 financial data
        if (node.type === 'manufacturing_center') {
            if (node.state.inventory !== undefined) {
                content += `Inventory: ${node.state.inventory.toFixed(0)} units<br>`;
            }
            if (node.state.production_rate !== undefined) {
                content += `Production: ${node.state.production_rate}/hr<br>`;
            }
            if (node.state.pending_orders !== undefined) {
                content += `Pending Orders: ${node.state.pending_orders.length}<br>`;
            }

            // Phase 2: Financial metrics
            const revenue = node.state.total_revenue || 0;
            const prodCosts = node.state.total_production_costs || 0;
            const rateCosts = node.state.total_rate_change_costs || 0;
            const totalCosts = prodCosts + rateCosts;
            const profit = revenue - totalCosts;
            const profitMargin = revenue > 0 ? (profit / revenue * 100) : 0;

            content += `<br><strong>💰 Financial:</strong><br>`;
            content += `  Revenue: $${revenue.toFixed(0)}<br>`;
            content += `  Costs: $${totalCosts.toFixed(0)}<br>`;
            content += `  Profit: $${profit.toFixed(0)} (${profitMargin.toFixed(1)}%)<br>`;
        }

        // Distributor - show Phase 3 sourcing data
        if (node.type === 'distributor') {
            if (node.state.orders_placed !== undefined) {
                content += `Orders Placed: ${node.state.orders_placed}<br>`;
            }

            // Phase 3: Sourcing policy
            const sourcingPolicy = node.properties?.sourcing_policy?.type || 'nearest_neighbor';
            content += `<br><strong>🎯 Sourcing:</strong><br>`;
            content += `  Policy: ${sourcingPolicy}<br>`;

            // Show top 2 suppliers
            const relationships = node.state.supplier_relationships || {};
            const sortedSuppliers = Object.entries(relationships)
                .sort((a, b) => b[1].orders_delivered - a[1].orders_delivered)
                .slice(0, 2);

            if (sortedSuppliers.length > 0) {
                content += `  Top Suppliers:<br>`;
                sortedSuppliers.forEach(([supplierId, metrics]) => {
                    const onTimeRate = (metrics.on_time_rate * 100).toFixed(0);
                    const supplierNode = this.nodes.find(n => n.id === supplierId);
                    const supplierName = supplierNode ? supplierNode.location.city : supplierId;
                    content += `    ${supplierName}: ${onTimeRate}% on-time<br>`;
                });
            } else {
                content += `  No history yet<br>`;
            }
        }

        tooltip.html(content);
    }

    /**
     * Hide tooltip
     */
    hideTooltip() {
        this.hoveredNode = null;
        d3.select('#tooltip').remove();
    }

    /**
     * Select/deselect a node
     */
    selectNode(node) {
        this.selectedNode = node;

        // Re-render nodes to update highlighting
        this.renderNodes();

        // Update details panel
        if (node) {
            this.updateDetailsPanel(node);
        } else {
            this.hideDetailsPanel();
        }
    }

    /**
     * Update details panel with node information
     */
    updateDetailsPanel(node) {
        const panel = d3.select('#node-details');
        if (panel.empty()) return;

        // Show panel
        panel.style('display', 'block');

        // Update content
        d3.select('#detail-node-name').text(node.name);
        d3.select('#detail-node-type').text(node.type.replace('_', ' '));
        d3.select('#detail-node-location').text(`${node.location.city}, ${node.location.state}`);

        // Build state list
        let stateHTML = '';

        // Manufacturing center - show Phase 2 financial section first
        if (node.type === 'manufacturing_center') {
            const revenue = node.state.total_revenue || 0;
            const prodCosts = node.state.total_production_costs || 0;
            const rateCosts = node.state.total_rate_change_costs || 0;
            const totalCosts = prodCosts + rateCosts;
            const profit = revenue - totalCosts;
            const profitMargin = revenue > 0 ? (profit / revenue * 100) : 0;

            stateHTML += `<div style="background:#2a4a2a;padding:8px;margin-bottom:8px;border-radius:4px;">`;
            stateHTML += `<strong style="color:#10b981;">💰 Financial</strong><br>`;
            stateHTML += `<div class="detail-item"><span class="detail-label">Revenue:</span> $${revenue.toFixed(0)}</div>`;
            stateHTML += `<div class="detail-item"><span class="detail-label">Costs:</span> $${totalCosts.toFixed(0)}</div>`;
            stateHTML += `<div class="detail-item"><span class="detail-label">Profit:</span> $${profit.toFixed(0)} (${profitMargin.toFixed(1)}%)</div>`;
            stateHTML += `</div>`;
        }

        // Distributor - show Phase 3 sourcing section first
        if (node.type === 'distributor') {
            const sourcingPolicy = node.properties?.sourcing_policy?.type || 'nearest_neighbor';
            const relationships = node.state.supplier_relationships || {};
            const sortedSuppliers = Object.entries(relationships)
                .sort((a, b) => b[1].orders_delivered - a[1].orders_delivered);

            stateHTML += `<div style="background:#2a3a4a;padding:8px;margin-bottom:8px;border-radius:4px;">`;
            stateHTML += `<strong style="color:#8b5cf6;">🎯 Sourcing</strong><br>`;
            stateHTML += `<div class="detail-item"><span class="detail-label">Policy:</span> ${sourcingPolicy}</div>`;

            if (sortedSuppliers.length > 0) {
                stateHTML += `<div style="margin-top:6px;"><span class="detail-label">Suppliers:</span></div>`;
                sortedSuppliers.forEach(([supplierId, metrics]) => {
                    const onTimeRate = (metrics.on_time_rate * 100).toFixed(0);
                    const supplierNode = this.nodes.find(n => n.id === supplierId);
                    const supplierName = supplierNode ? supplierNode.location.city : supplierId;
                    const color = metrics.on_time_rate >= 0.9 ? '#10b981' : (metrics.on_time_rate >= 0.7 ? '#f59e0b' : '#ef4444');
                    stateHTML += `<div class="detail-item" style="padding-left:10px;"><span style="color:${color};">${supplierName}: ${onTimeRate}% (${metrics.orders_delivered} orders)</span></div>`;
                });
            } else {
                stateHTML += `<div class="detail-item" style="font-style:italic;color:#9ca3af;">No supplier history yet</div>`;
            }
            stateHTML += `</div>`;
        }

        // General state information
        for (const [key, value] of Object.entries(node.state)) {
            // Skip Phase 2/3 fields (already shown above) and complex objects
            if (key === 'total_revenue' || key === 'total_production_costs' || key === 'total_rate_change_costs' ||
                key === 'supplier_relationships' || key === 'fulfillment_times' || key === 'orders_in_delivery') {
                continue;
            }

            if (key === 'pending_orders' || key === 'in_delivery') {
                // Show array length
                stateHTML += `<div class="detail-item"><span class="detail-label">${key}:</span> ${value.length}</div>`;
            } else if (typeof value === 'number') {
                // Format numbers
                stateHTML += `<div class="detail-item"><span class="detail-label">${key}:</span> ${value.toFixed(2)}</div>`;
            } else if (typeof value === 'object') {
                // Skip complex objects
                continue;
            } else {
                stateHTML += `<div class="detail-item"><span class="detail-label">${key}:</span> ${value}</div>`;
            }
        }

        d3.select('#detail-node-state').html(stateHTML);
    }

    /**
     * Hide details panel
     */
    hideDetailsPanel() {
        const panel = d3.select('#node-details');
        if (!panel.empty()) {
            panel.style('display', 'none');
        }
    }

    /**
     * Resize the visualization
     */
    resize(width, height) {
        this.width = width;
        this.height = height;

        // Update SVG dimensions
        this.svg
            .attr('width', width)
            .attr('height', height);

        // Update projection
        this.projection
            .translate([width / 2, height / 2]);

        // Re-render states with new projection
        if (this.usStates) {
            this.g.select('.states')
                .selectAll('path')
                .attr('d', this.path);
        }

        // Re-render edges and nodes with new positions
        this.renderEdges();
        this.renderNodes();
    }
}
