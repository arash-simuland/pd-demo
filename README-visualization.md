# Zurvan Visualization - D3.js + Three.js

This is the new web-native visualization stack for the Zurvan product delivery demo, replacing the Python-based Dash/Plotly implementation.

## Architecture

```
Frontend (Browser)           Backend (Python)
├─ D3.js (2D viz)      ←→   ├─ FastAPI (REST + WebSocket)
├─ Three.js (3D scene)      ├─ SimPy Simulation
└─ HTML/CSS/JS              └─ ZurvanGraph
```

## Quick Start

### 1. Install Backend Dependencies

```bash
cd arash/product-delivery-demo
pip install -r requirements.txt

# On Windows if 'python' is not found:
py -m pip install -r requirements.txt
```

### 2. Install Frontend Dependencies

```bash
cd frontend
npm install
cd ..
```

### 3. Start Backend Server

**Windows (PowerShell) - Background:**
```powershell
Start-Process -NoNewWindow -FilePath "py" -ArgumentList "backend\api.py"
```

**Cross-Platform - Foreground:**
```bash
cd backend
python api.py
# OR on Windows:
py api.py
```

Expected output:
```
[OK] Loaded ZurvanGraph(centers=3, distributors=8, edges=24)
[FastAPI] Loaded graph with 11 nodes
Starting FastAPI server...
API: http://127.0.0.1:8000
```

### 4. Start Frontend Dev Server

**Windows (PowerShell) - Background:**
```powershell
cd frontend
Start-Process -NoNewWindow cmd -ArgumentList "/c", "npm run dev"
```

**Cross-Platform - Foreground:**
```bash
cd frontend
npm run dev
```

Expected output:
```
VITE v5.4.20  ready in 546 ms
➜  Local:   http://localhost:3000/
```

### 5. Open Browser

Navigate to: **http://localhost:3000**

### Verification

Check that both servers are running:
```powershell
# Windows
netstat -ano | findstr ":8000"  # Backend
netstat -ano | findstr ":3000"  # Frontend
```

## Phase 1 Status (Complete ✅)

- [x] FastAPI backend with WebSocket
- [x] Frontend structure with Vite
- [x] WebSocket real-time connection
- [x] Control buttons (Play/Pause/Reset/Speed)
- [x] Basic statistics display

## Phase 2: D3.js 2D Visualization (Next)

**Features to Implement:**
- US map with node positions
- Network graph with animated edges
- Order flow visualization
- Time series charts
- Interactive tooltips

**Files to Create:**
- `frontend/src/d3/map.js` - 2D network map
- `frontend/src/d3/charts.js` - Time series charts
- `frontend/src/d3/controls.js` - Interactive controls

## Phase 3: Three.js 3D Scene (After Phase 2)

**Features to Implement:**
- 3D spatial layout
- Manufacturing centers as 3D buildings
- Animated order flows (Bézier curves)
- Camera orbit controls
- Inventory visualization (growing/shrinking)

**Files to Create:**
- `frontend/src/three/scene.js` - Main 3D scene
- `frontend/src/three/nodes.js` - 3D objects
- `frontend/src/three/flows.js` - Animated paths

## Phase 4: Combined D3 + Three (Future)

- Overlay 2D HUD on 3D scene
- Coordinate projection (3D → 2D)
- Seamless view transitions

## Development Notes

### WebSocket Message Format

The backend sends JSON state updates every 100ms:

```json
{
  "time": 123.45,
  "running": true,
  "speed": 1.0,
  "nodes": [
    {
      "id": "chicago_center",
      "type": "manufacturing_center",
      "name": "Chicago Manufacturing Center",
      "location": {"lat": 41.8781, "lon": -87.6298},
      "state": {"inventory": 500, "production_rate": 100},
      "color": "#00C851"
    }
  ],
  "edges": [
    {
      "from": "distributor_ny",
      "to": "chicago_center",
      "distance": 790,
      "active_orders": 2
    }
  ],
  "stats": {
    "total_inventory": 1500,
    "orders_placed": 45,
    "orders_fulfilled": 38,
    "pending_orders": 7
  }
}
```

### Technology Stack

**Frontend:**
- Vite - Fast build tool
- D3.js ^7.9.0 - 2D data visualization
- Three.js ^0.160.1 - 3D graphics
- topojson-client - US map data

**Backend:**
- FastAPI - Modern Python web framework
- Uvicorn - ASGI server
- WebSockets - Real-time communication
- SimPy - Discrete event simulation (unchanged)

### Directory Structure

```
frontend/
├── index.html              # Main HTML
├── package.json            # npm dependencies
├── vite.config.js          # Build config
└── src/
    ├── main.js             # Entry point ✅
    ├── api.js              # WebSocket client ✅
    ├── d3/                 # D3.js modules (Phase 2)
    │   ├── map.js
    │   ├── charts.js
    │   └── controls.js
    ├── three/              # Three.js modules (Phase 3)
    │   ├── scene.js
    │   ├── nodes.js
    │   └── flows.js
    └── hybrid/             # Combined view (Phase 4)
        ├── renderer.js
        └── hud.js

backend/
├── api.py                  # FastAPI server ✅
├── requirements.txt        # Python dependencies ✅
└── [uses ../src/ for simulation code]
```

## Why This Migration?

1. **Better Performance**: Native WebGL vs Plotly overhead
2. **3D Visualization**: Support for Layer 3 (Physical/Spatial)
3. **Full Control**: Custom animations and effects
4. **Web-Native**: Runs anywhere, easy to embed
5. **Future-Proof**: Path to NVIDIA Omniverse integration

## Next Steps

See migration plan in `docs/` for detailed implementation roadmap.
