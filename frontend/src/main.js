/**
 * main.js - Entry Point for Zurvan Visualization
 *
 * Initializes WebSocket connection, sets up controls, and coordinates
 * D3.js and Three.js rendering (to be implemented in Phase 2 & 3).
 */

import { SimulationAPI } from './api.js';
import { NetworkMap } from './d3/map.js';

// =============================================================================
// STATE
// =============================================================================

let currentState = null;
let networkMap = null;

// =============================================================================
// INITIALIZATION
// =============================================================================

document.addEventListener('DOMContentLoaded', () => {
    console.log('[Main] Initializing Zurvan visualization...');

    // Initialize D3 Network Map
    const vizContainer = document.getElementById('visualization');
    const width = vizContainer.clientWidth;
    const height = vizContainer.clientHeight;
    networkMap = new NetworkMap('visualization', width, height);

    // Initialize API connection
    const api = new SimulationAPI(onStateUpdate, onConnectionChange);
    api.connect();

    // Setup control event listeners
    setupControls(api);

    // Setup sidebar resize
    setupSidebarResize();

    // Setup window resize handler
    setupWindowResize();

    console.log('[Main] Initialization complete');
});

// =============================================================================
// API CALLBACKS
// =============================================================================

function onStateUpdate(state) {
    currentState = state;

    // Update time display
    const timeDisplay = document.getElementById('time-display');
    timeDisplay.textContent = `${state.time.toFixed(2)} hrs`;

    // Update statistics
    if (state.stats) {
        document.getElementById('stat-inventory').textContent = state.stats.total_inventory;
        document.getElementById('stat-orders').textContent = state.stats.orders_placed;
        document.getElementById('stat-fulfilled').textContent = state.stats.orders_fulfilled;
        document.getElementById('stat-pending').textContent = state.stats.pending_orders;
    }

    // Update D3.js visualization
    if (networkMap) {
        networkMap.update(state);
    }

    // TODO Phase 3: Update Three.js scene
    // updateThreeJS(state);
}

function onConnectionChange(connected) {
    const statusElement = document.getElementById('connection-status');

    if (connected) {
        statusElement.textContent = 'Connected';
        statusElement.classList.add('connected');
    } else {
        statusElement.textContent = 'Disconnected';
        statusElement.classList.remove('connected');
    }
}

// =============================================================================
// CONTROLS
// =============================================================================

function setupControls(api) {
    // Play button
    document.getElementById('btn-play').addEventListener('click', () => {
        console.log('[Controls] Play clicked');
        api.play();
    });

    // Pause button
    document.getElementById('btn-pause').addEventListener('click', () => {
        console.log('[Controls] Pause clicked');
        api.pause();
    });

    // Reset button
    document.getElementById('btn-reset').addEventListener('click', () => {
        console.log('[Controls] Reset clicked');
        api.reset();
    });

    // Speed slider
    const speedSlider = document.getElementById('speed-slider');
    const speedValue = document.getElementById('speed-value');

    speedSlider.addEventListener('input', (e) => {
        const speed = parseFloat(e.target.value);
        speedValue.textContent = `${speed.toFixed(1)}x`;
        api.setSpeed(speed);
    });
}

// =============================================================================
// SIDEBAR RESIZE
// =============================================================================

function setupSidebarResize() {
    const resizeHandle = document.getElementById('resize-handle');
    const sidebar = document.getElementById('sidebar');
    const mainContainer = document.getElementById('main-container');

    let isResizing = false;

    resizeHandle.addEventListener('mousedown', (e) => {
        isResizing = true;
        document.body.style.cursor = 'ew-resize';
        document.body.style.userSelect = 'none';
    });

    document.addEventListener('mousemove', (e) => {
        if (!isResizing) return;

        // Calculate new width (distance from right edge of window)
        const newWidth = window.innerWidth - e.clientX;

        // Constrain between 200px and 600px
        const constrainedWidth = Math.max(200, Math.min(600, newWidth));

        sidebar.style.width = `${constrainedWidth}px`;

        // Trigger D3 map resize if needed
        if (networkMap) {
            const vizContainer = document.getElementById('visualization');
            networkMap.resize(vizContainer.clientWidth, vizContainer.clientHeight);
        }
    });

    document.addEventListener('mouseup', () => {
        if (isResizing) {
            isResizing = false;
            document.body.style.cursor = '';
            document.body.style.userSelect = '';
        }
    });
}

// =============================================================================
// WINDOW RESIZE HANDLER
// =============================================================================

function setupWindowResize() {
    let resizeTimeout;
    
    window.addEventListener('resize', () => {
        // Debounce resize events
        clearTimeout(resizeTimeout);
        resizeTimeout = setTimeout(() => {
            if (networkMap) {
                const vizContainer = document.getElementById('visualization');
                const width = vizContainer.clientWidth;
                const height = vizContainer.clientHeight;
                networkMap.resize(width, height);
            }
        }, 100);
    });
}

// =============================================================================
// PHASE 2: D3.js VISUALIZATION (TO BE IMPLEMENTED)
// =============================================================================

// TODO: Implement D3.js network graph
// - US map with nodes
// - Order flow lines
// - Interactive tooltips

// =============================================================================
// PHASE 3: THREE.JS VISUALIZATION (TO BE IMPLEMENTED)
// =============================================================================

// TODO: Implement Three.js 3D scene
// - 3D spatial layout
// - Animated order flows
// - Camera controls
