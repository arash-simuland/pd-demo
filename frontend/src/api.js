/**
 * api.js - WebSocket Client for Real-time Simulation Updates
 *
 * Connects to FastAPI backend and receives simulation state updates.
 */

export class SimulationAPI {
    constructor(onStateUpdate, onConnectionChange) {
        this.ws = null;
        this.onStateUpdate = onStateUpdate;
        this.onConnectionChange = onConnectionChange;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 10;
    }

    connect() {
        console.log('[API] Connecting to WebSocket...');

        // Connect to WebSocket (proxied through Vite during dev)
        this.ws = new WebSocket('ws://localhost:8000/ws');

        this.ws.onopen = () => {
            console.log('[API] WebSocket connected');
            this.reconnectAttempts = 0;
            this.onConnectionChange(true);
        };

        this.ws.onmessage = (event) => {
            try {
                const state = JSON.parse(event.data);
                this.onStateUpdate(state);
            } catch (error) {
                console.error('[API] Error parsing state:', error);
            }
        };

        this.ws.onerror = (error) => {
            console.error('[API] WebSocket error:', error);
        };

        this.ws.onclose = () => {
            console.log('[API] WebSocket disconnected');
            this.onConnectionChange(false);

            // Attempt to reconnect
            if (this.reconnectAttempts < this.maxReconnectAttempts) {
                this.reconnectAttempts++;
                console.log(`[API] Reconnecting (attempt ${this.reconnectAttempts})...`);
                setTimeout(() => this.connect(), 2000);
            } else {
                console.error('[API] Max reconnect attempts reached');
            }
        };
    }

    disconnect() {
        if (this.ws) {
            this.ws.close();
            this.ws = null;
        }
    }

    // Control methods
    async play() {
        await fetch('http://localhost:8000/api/control/play', { method: 'POST' });
    }

    async pause() {
        await fetch('http://localhost:8000/api/control/pause', { method: 'POST' });
    }

    async reset() {
        await fetch('http://localhost:8000/api/control/reset', { method: 'POST' });
    }

    async setSpeed(speed) {
        await fetch(`http://localhost:8000/api/control/speed?speed=${speed}`, {
            method: 'POST'
        });
    }
}
