# Zurvan Product Delivery Demo

A step-by-step demonstration of Zurvan modeling principles using a product delivery supply chain model with **SimPy** discrete event simulation.

> **Note:** This is a **standalone demo**, separate from the main Zurvan framework. It uses SimPy for discrete event simulation with a modern web stack (FastAPI + Vite + D3.js).

## Getting the Right Version

The product-delivery-demo was added to the repository on **November 7, 2025**. To access it:

```bash
# If you're on an older commit, switch to a version that includes the demo:
git checkout 0e7316d  # Or any commit from Nov 7, 2025 onwards

# Or create a branch from that commit:
git checkout -b my-demo-branch 0e7316d
```

## Current Status: Foundation Complete - Building Agentic UX ✅

**Completed Foundation (Phases 1-3)**:
- ✅ **SimPy discrete event simulation** - Order lifecycle, production, delivery
- ✅ **Financial tracking** - Revenue, costs, profit margins for manufacturers
- ✅ **Sourcing intelligence** - Distributor policies and supplier reputation tracking
- ✅ **Real-time visualization** - D3.js map with synchronized delivery animations
- ✅ **Interactive UI** - Node details, resizable panels, simulation controls

**Agentic UX** (Natural Language Control) - ✅ **Phases A, B, & C Complete!**
- ✅ **Phase A**: Chat interface + LLM integration (Ollama Mistral + LangChain)
- ✅ **Phase B**: Production control commands (increase, shutdown, resume, status)
- ✅ **Phase C**: Dynamic node creation ("Add distributor in Dallas, TX")
- 🎯 **Phase D**: Advanced agentic features (scenario analysis, optimization)

**Modern Web Stack**
- **FastAPI Backend** - REST API + WebSocket for real-time streaming (10 fps)
- **D3.js Frontend** - Geographic visualization with interactive features
- **Vite Dev Server** - Fast hot-reload development experience
- **Order Delivery Phase** - Full lifecycle tracking (pending → in_delivery → delivered)
- **Dual-Edge Visualization** - Blue for order placement signals, red for delivery routes
- **Animated Delivery Particles** - Orange particles travel along delivery routes with pause/resume
- **Interactive Node Details** - Click any node to see real-time financial & sourcing metrics
- **Container-Ready** - Backend and frontend can deploy as separate containers

**Order Lifecycle Features:**
- **Order placement** - Distributors place orders to nearest manufacturing center
- **Delivery simulation** - Products travel by truck at 50 mph based on real distance
- **Travel time calculation** - distance (miles) / 50 mph = delivery duration (hours)
- **Delivery tracking** - Orders move from pending → in_delivery → delivered
- **Visual feedback** - Blue flash for order placement, red edges with orange particles for delivery

## Implementation Approach

This demo uses **SimPy** (Simulated Python) as the discrete event simulation engine while maintaining Zurvan's three-layer architecture:

- **ResourceNode class** - Nodes as objects (SimPy Agent pattern)
- **Generator functions** - Actions with time constraints (`yield env.timeout()`)
- **Simulation wrapper** - Scenarios encapsulate graph + SimPy environment
- **Real-time visualization** - FastAPI + WebSocket + D3.js with geographic projection

See `docs/reference/simpy-patterns.md` for detailed SimPy pattern documentation.

## Quick Start

### Prerequisites

- Python 3.10+ (with `pip`)
- Node.js 16+ (with `npm`)

### Installation

```bash
# Install Python dependencies (backend)
pip install -r requirements.txt
# OR on Windows if 'python' is not found:
py -m pip install -r requirements.txt

# Install frontend dependencies
cd frontend
npm install
cd ..
```

### Run the Visualization

**Method 1: Using Background Processes (Windows)**

```powershell
# Navigate to the product-delivery-demo directory
cd arash/product-delivery-demo

# Start backend in background
Start-Process -NoNewWindow -FilePath "py" -ArgumentList "backend\api.py"

# Start frontend in background
cd frontend
Start-Process -NoNewWindow cmd -ArgumentList "/c", "npm run dev"
```

**Method 2: Using Two Terminals (Cross-Platform)**

**Terminal 1 - Backend (FastAPI + WebSocket):**
```bash
cd arash/product-delivery-demo/backend
python api.py
# OR on Windows:
py api.py
```

You should see:
```
[OK] Loaded ZurvanGraph(centers=3, distributors=8, edges=24)
[FastAPI] Loaded graph with 11 nodes
Starting FastAPI server...
API: http://127.0.0.1:8000
```

**Terminal 2 - Frontend (Vite + D3.js):**
```bash
cd arash/product-delivery-demo/frontend
npm run dev
```

You should see:
```
VITE v5.4.20  ready in 546 ms
➜  Local:   http://localhost:3000/
```

**Open browser to:** http://localhost:3000

### Verification

To verify both servers are running, check the ports:

**Windows (PowerShell):**
```powershell
netstat -ano | findstr ":8000"   # Backend should be LISTENING
netstat -ano | findstr ":3000"   # Frontend should be LISTENING
```

**Linux/Mac:**
```bash
lsof -i :8000   # Backend
lsof -i :3000   # Frontend
```

### Troubleshooting

**Backend won't start:**
- Check if Python dependencies are installed: `py -c "import simpy, fastapi, uvicorn"`
- If port 8000 is in use, kill the process:
  ```powershell
  # Windows: Find and kill process on port 8000
  netstat -ano | findstr ":8000"
  taskkill /PID <process_id> /F
  ```

**Frontend won't start:**
- Make sure you're in the `frontend/` directory
- Check if `node_modules` exists (run `npm install` if not)
- Try clearing npm cache: `npm cache clean --force`
- Check Vite config for port conflicts

**Browser shows blank page:**
- Open browser console (F12) and check for errors
- Verify backend is running and accessible at http://127.0.0.1:8000
- Try hard refresh (Ctrl+F5)
- Check that WebSocket connection is established

**Frontend is on different port:**
- Vite's default port is 3000, but it may use 3001, 3002, etc. if 3000 is occupied
- Check the terminal output for the actual port number
- Vite will auto-increment the port if there's a conflict

### Features

The visualization shows:
- 🏭 **Manufacturing centers** - Circular nodes (gray=idle, green=producing)
  - Size based on inventory level
  - Click to see detailed state + **financial metrics** (revenue, costs, profit margin)
- 🏪 **Distributors** - Circular nodes (smaller, green)
  - Click to see order stats + **sourcing policy & supplier reputation tracking**
- 🔵 **Order placement signals** - Blue edges flash briefly (0.1 hrs) when order placed
- 🔴 **Delivery routes** - Red edges with **multiple animated orange particles** showing product delivery
  - **One particle per active order** - Accurately visualizes high-volume routes (20-30 simultaneous deliveries)
  - Particles travel at realistic speed (50 mph truck delivery, e.g., Nashville→Phoenix: ~29 hours)
  - Individual progress tracking for each order
  - Pause/resume preserves all particle positions
- 📊 **Live metrics** - Total inventory, orders placed/fulfilled, pending orders
- 🎮 **Simulation controls** - Play, pause, reset, speed control
- 📋 **Node details panel** - Click any node to see real-time state variables
  - **Manufacturers**: Revenue, costs, profit margins in real-time
  - **Distributors**: Sourcing policy, supplier relationships, on-time rates

**Interactive Features:**
- 💬 **AI Chat Interface** - Natural language control with local LLM (Ollama Mistral)
  - **Production control**: "Increase Chicago production to 25 units per hour"
  - **Status queries**: "Show Pittsburgh status"
  - **Node creation**: "Add a distributor in Dallas, Texas"
  - **Node creation**: "Add manufacturing center in Atlanta, Georgia"
  - **Batch operations**: "Resume all production"
- **Click nodes** to inspect detailed state (inventory, production rate, orders, etc.)
- **Pan and zoom** the map using mouse
- **Pause/Resume** animation - particles freeze and resume from exact position
- **Speed control** - Adjust simulation speed (0.1x to 10x)
- **Real-time updates** - All metrics update automatically at 10 fps

### Test the Graph Builder

```bash
# From the product-delivery-demo directory
python src/graph-builder.py
```

This will print a summary of the graph structure.

## Project Structure

```
product-delivery-demo/
├── README.md                    # This file
├── requirements.txt             # Python dependencies
│
├── backend/                     # FastAPI backend
│   └── api.py                  # REST API + WebSocket server
│
├── frontend/                    # Vite + D3.js frontend
│   ├── index.html              # Main HTML with sidebar and controls
│   ├── package.json            # Node dependencies
│   ├── vite.config.js          # Vite configuration
│   └── src/
│       ├── main.js             # App initialization and WebSocket
│       ├── controls.js         # Simulation controls (play/pause/speed)
│       └── d3/
│           └── map.js          # D3.js geographic visualization
│
├── data/
│   ├── nodes.json              # Node definitions (centers, distributors)
│   └── edges.json              # Edge type definitions
│
├── docs/                        # Documentation
│   ├── model-specification.md
│   ├── step-by-step-process.md
│   ├── animation-guide.md
│   └── reference/
│       ├── simpy-concepts.md
│       └── simpy-patterns.md
│
└── src/                         # Simulation core (SimPy)
    ├── resource-node.py         # ResourceNode class
    ├── graph-builder.py         # Graph structure with ResourceNodes
    ├── simulation.py            # Simulation wrapper class
    ├── order.py                 # Order class with delivery tracking
    ├── policy-node.py           # Policy base class
    ├── default-policies.py      # Policy implementations
    ├── node-templates.py        # Default configs for dynamic nodes
    └── actions/                 # Action definitions (SimPy generators)
        ├── __init__.py
        ├── manufacturing-actions.py  # Production, fulfillment, delivery
        └── order-actions.py     # Order generation and routing
```

## Zurvan Architecture (Implemented)

### Layer 1: Structural Layer ✅ (Steps 1-2)
- **Autonomous Agent Pattern** - Nodes are self-managing agents
- **ResourceNode objects** - Not dicts, full object-oriented design
- **Data-driven action configuration** - Actions defined in `data/nodes.json`, not hardcoded
- **Action management attributes**:
  - `actions`: Dictionary of available action functions (loaded from JSON config)
  - `automatic_actions`: List of action configs with `auto_start: true`
  - `active_processes`: Currently running SimPy processes
  - Policy-driven execution: Actions controlled by PolicyNode objects
- **Dynamic state management** - `inventory`, `production_rate`, `machine_state`
- **Graph structure** - Distance-based connections between nodes
- **Color coding** - Visual state representation
- **Ready for SimPy** - Nodes have `env` attribute for simulation

### Layer 2: Temporal Layer 🔄 (Steps 3-8)
- ✅ **Step 3 Complete**: Action definitions as SimPy generator functions
  - continuous_production, change_production_rate, fulfill_order
  - generate_orders, route_order, track_order_fulfillment, process_pending_orders
  - Action metadata for visualization
- ✅ **Step 4 Complete**: Simulation class with manual action execution
  - ProductDeliverySimulation wrapper class
  - ActionLog for execution tracking
  - Manual execution methods with interactive UI
  - Real-time state updates and simulation time
- ✅ **Step 5-6 Complete**: Activate processes and continuous production
  - **Autonomous agent activation** - Nodes start their own processes via `node.start()`
  - **Policy-driven execution** - Policies control when/how often actions execute
  - **Data-driven process activation** - All configuration (action, policy, resource, time) from JSON
  - **Simplified simulation control** - Just call `start_all_processes()`, nodes self-manage
  - Play/Pause/Step controls for simulation playback
  - Continuous production processes activated automatically
  - Real-time inventory updates based on production rates
  - Speed control and status display
- ✅ **Step 7 Complete**: Order generation and routing
  - Order class with routing and tracking
  - Distributors generate orders probabilistically
  - Nearest-center routing algorithm
  - Order queue visualization and statistics
  - Event-driven time advancement (SimPy clock jumps to events)
  - Reset button to restart simulation from initial state
  - Configurable playback speed (events per second)
  - Improved production batching (1-hour intervals)
- ✅ **Step 8 Complete**: Order fulfillment and inventory management
  - Automatic FIFO order fulfillment process
  - Inventory constraints prevent over-fulfillment
  - Fulfillment time tracking and SLA monitoring
  - Comprehensive fulfillment metrics dashboard
  - Visual inventory alerts and order status colors
  - Real-time metrics: avg fulfillment time, 24hr/48hr compliance, violations

### Layer 3: Physical Layer (Partially Implemented)
- Geographic constraints (distance-based routing) ✅ (Step 7)
- Inventory capacity limits ✅ (Step 8)
- Order fulfillment with resource constraints ✅ (Step 8)

## Agentic UX Implementation

**Natural language control of simulation through chat interface:**

### Phase A: Chat Interface & LLM Integration ✅ **COMPLETE**

**Implemented Features:**
- ✅ **Chat UI**: Chat panel in sidebar with message history
- ✅ **LLM Backend**: Ollama Mistral (7B) with LangChain tools
- ✅ **Fast JSON Command Parsing**: 1-3 second response time
- ✅ **Proper Agentic Workflow**: Schedules SimPy actions (doesn't hack state)
- ✅ **Tool Verification**: Built-in validation and error handling

**Working Commands:**
```
# Production Control
"Increase Chicago production to 25 units per hour"
"Shutdown Nashville production"
"Resume all production"

# Status Queries
"Show Pittsburgh status"
"Show simulation stats"

# Dynamic Node Creation (Phase C)
"Add a distributor in Dallas, Texas"
"Add manufacturing center in Atlanta, Georgia"
```

**Technical Architecture:**
- Structured JSON extraction (not complex ReAct agent)
- LangChain tools with direct invocation
- Proper SimPy integration (schedules processes)
- ~100% command execution success rate

### Phase B: Production Control Commands ✅ **COMPLETE**

**All production control commands working:**
- ✅ **"Shutdown Chicago production"** → Set production rate to 0
- ✅ **"Increase Nashville production to 15 units/hour"** → Adjust production rate
- ✅ **"Resume all production"** → Restore default rates
- ✅ **Real-time feedback**: Chat confirms actions and shows results
- ✅ **State queries**: "Show [center] status" with live metrics

### Phase C: Dynamic Node Creation ✅ **COMPLETE**

**Implemented Features:**
- ✅ **Node templates**: Default configurations for new distributors and manufacturers (`src/node-templates.py`)
- ✅ **Geocoding**: Converts city/state names to coordinates (50+ US cities)
- ✅ **Dynamic graph updates**: New nodes connect automatically with distance-based edges
- ✅ **SimPy integration**: New nodes start processes while simulation is running
  - **Idempotent process activation**: Guards prevent duplicate processes
  - **Environment propagation**: `graph.env` enables dynamic nodes to access SimPy environment
  - **Automatic process startup**: New nodes activate their actions immediately
- ✅ **LangChain tools**: Natural language commands for node creation
- ✅ **Multiple-particle visualization**: Each active order gets its own animated particle

**Working Commands:**
```
"Add a distributor in Dallas, Texas"
"Add manufacturing center in Atlanta, Georgia"
"Add distributor in Phoenix, Arizona"  # Long-distance route shows multiple simultaneous deliveries
```

**Technical Features:**
- Automatic edge calculation to all relevant nodes
- Process activation for new nodes (production, order generation)
- Real-time map updates (new nodes appear immediately)
- Fallback geocoding database (no API required)
- Validation and error handling for invalid locations
- Realistic day-of-week order probability patterns (30-50% weekdays, 10-20% weekends)

### Phase D: Advanced Agentic Features
- **Scenario queries**: "What if we add 2 more distributors in the Southeast?"
- **Performance analysis**: "Show me which manufacturer is most profitable"
- **Optimization suggestions**: "How can we reduce costs by 10%?"
- **Natural language exports**: "Export last 24 hours of data to CSV"

---

## Future Enhancements (Deferred)

**Note**: The following phases are planned for future development after agentic UX is complete.

**Phase 4**: Cross-fulfillment cooperation (manufacturers help each other fulfill orders)
**Phase 5**: Manufacturer objective functions (profit-maximization, revenue-maximization, market-share strategies)
**Phases 6-9**: Advanced policies, network coordination, analytics

See `docs/business-case.md` for complete market simulation roadmap (deferred features).

## Step 8 Verification Checklist

- [x] process_pending_orders action created (FIFO fulfillment)
- [x] Order fulfillment process activated in simulation
- [x] Fulfillment only occurs when inventory >= order quantity
- [x] Fulfillment time tracked (placement_time → fulfillment_time)
- [x] fulfillment_times list maintained in center state
- [x] SLA violations tracked (orders > 48 hours)
- [x] Order status updated to 'fulfilled' when completed
- [x] Average fulfillment time displayed in dashboard
- [x] 24hr/48hr compliance metrics shown
- [x] Order status colors (green/yellow/red) in UI
- [x] Inventory alerts (<100 units = red warning)
- [x] Real-time metrics update automatically
- [x] Fulfillment messages printed to console

Ready to proceed to Step 9!
