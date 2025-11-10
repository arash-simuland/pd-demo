# 🎬 Zurvan Animation Guide - D3.js Visualization

## How to Watch the Simulation Come Alive!

### 1. Start the Backend and Frontend

**Terminal 1 - Backend:**
```bash
cd backend
python api.py
```

**Terminal 2 - Frontend:**
```bash
cd frontend
npm run dev
```

### 2. Open the Visualization

**URL**: http://localhost:5173

The Vite dev server will automatically open your browser, or navigate to the URL manually.

### 3. What You'll See

#### Top Section: Header
- **"🎬 Zurvan Product Delivery - Live Simulation"**
- Subtitle: "D3.js + Three.js Visualization"

#### Middle Section: Geographic Map (D3.js)
- **Manufacturing Centers** (large circles):
  - ⚪ **Gray** = Idle (not producing)
  - 🟢 **Green** = Actively producing
  - **Size** = Current inventory level (bigger = more inventory)
  - **Click** to see detailed state in sidebar

- **Distributors** (smaller circles):
  - 🟢 **Green** = Active (placing orders)
  - **Click** to see order generation stats

- **Connection Lines**:
  - 🔵 **Blue flash** = Order placement signal (brief 0.1 hour flash)
  - 🔴 **Red lines** = Active delivery routes with animated particles
  - 🟠 **Orange particles** = Products in transit (move at 50 mph truck speed)

#### Right Section: Sidebar
- **Node Details Panel** (when node selected):
  - Node name, type, location
  - Current state variables (inventory, production_rate, orders, etc.)
  - Real-time updates
- **Statistics Cards**:
  - Total Inventory
  - Orders Placed
  - Orders Fulfilled
  - Pending Orders

#### Bottom Section: Simulation Controls
- **▶ Play** - Start simulation
- **⏸ Pause** - Pause simulation (particles freeze in place)
- **🔄 Reset** - Reset to initial state
- **Speed Slider** - Adjust simulation speed (0.1x to 10x)
- **Time Display** - Current simulation time in hours

### 4. How to Start the Animation

**Step-by-step:**

1. Look for the control bar at the top
2. Click the **"▶ Play"** button (green)
3. Watch the time display start advancing

### 5. What Happens When You Click Play?

The simulation starts executing automatically! Watch for:

#### Immediately:
- **Time display** starts counting up (0.00 hrs → 0.10 hrs → ...)
- **Manufacturing centers** begin producing inventory
- **Circles grow** as inventory increases
- **Circle colors** change (gray → green when producing)

#### After ~2 Hours (simulation time):
- **Distributors** start placing orders
- **Blue flashes** appear briefly showing order placement signals
- **Order queues** build up (check "Pending Orders" stat)

#### After ~3-5 Hours:
- **Order fulfillment** begins
- **Red lines appear** with animated orange particles
- **Particles travel** from manufacturing centers to distributors
- Watch particles move across the map at realistic speed!
- **Inventory decreases** as orders are fulfilled (circles shrink)
- **"Orders Fulfilled"** count increases

#### Continuously:
- **All metrics update** in real-time (10 fps)
- **Node states** update if a node is selected
- **Particles animate** smoothly along delivery routes

### 6. Visual Indicators of Animation

You'll know the animation is working when you see:

1. **Time advancing**:
   - "X.XX hrs" in the control bar increases
   - Console shows: `[Animation] Time: 0.00 → 0.10 hrs`

2. **Console logs** (backend terminal):
   - `[Order] order-001: Boston → Chicago (50 units, distance=120.5 miles)`
   - `[Fulfill] Chicago Center: order-001 shipped to Boston (ETA=2.4hrs)`
   - `[Delivery] Chicago Center: order-001 delivered to Boston (total time=3.5hrs)`

3. **Map changes**:
   - Circle sizes change dynamically (inventory levels)
   - Colors shift (idle → producing)
   - Blue flashes when orders placed
   - Red lines appear with moving particles

4. **Sidebar updates**:
   - Statistics cards update continuously
   - Selected node details refresh in real-time

### 7. Interactive Features

#### Click Nodes to Inspect
- **Click any node** (manufacturing center or distributor)
- **Details panel appears** at top of sidebar
- See **real-time state**:
  - Inventory level
  - Production rate
  - Machine state
  - Pending orders count
  - In-delivery orders count
  - All state variables
- **Click background** to deselect
- **White border** shows selected node

#### Pause and Resume Animation
- **Click ⏸ Pause** to freeze simulation
- Particles stop moving at exact position
- Time stops advancing
- **Click ▶ Play** to resume
- Particles continue from where they stopped
- Remaining travel distance calculated automatically

#### Speed Control
- **Drag the slider** to adjust speed
- Range: 0.1x (slow motion) to 10x (fast forward)
- Default: 1.0x (1 simulation hour per 10 real seconds)
- Try **5.0x** for quick testing
- Try **0.5x** for detailed observation

#### Pan and Zoom
- **Mouse wheel**: Zoom in/out
- **Click and drag**: Pan the map
- Geographic projection (Albers USA) preserves real distances

### 8. Understanding the Delivery Animation

**Order Lifecycle:**

1. **Order Placed** (distributor → manufacturer):
   - Blue edge flashes briefly (0.1 simulation hours)
   - Order appears in pending queue

2. **Order Fulfilled** (manufacturer processes):
   - Inventory check
   - If sufficient inventory, order moves to "in_delivery"
   - Red edge appears with orange particle

3. **Delivery in Transit** (manufacturer → distributor):
   - Orange particle travels along red edge
   - Speed: 50 mph (based on real distance)
   - Duration: distance (miles) / 50 mph = hours
   - Particle position updates smoothly

4. **Delivery Complete**:
   - Particle reaches destination
   - Order status changes to "delivered"
   - Red edge disappears
   - Console shows delivery confirmation

**Why Two Edge Types?**
- **Blue (order placement)**: Information flow - distributor sends order request
- **Red (delivery)**: Physical flow - truck delivers products

### 9. Animation Controls

**Speed Control:**
- **0.1x** - Slow motion (watch every detail)
- **1.0x** - Default (realistic pace)
- **5.0x** - Fast testing (see trends quickly)
- **10.0x** - Maximum speed

**Other Buttons:**
- **⏸ Pause**: Freeze everything, state preserved
- **▶ Play**: Resume from exact position
- **🔄 Reset**: Clear all state, return to t=0

### 10. Troubleshooting

**"I don't see any changes!"**
- Make sure you clicked **▶ Play**
- Check time display - is it advancing?
- Look at backend terminal for console logs
- Try increasing speed to 5.0x to see faster changes

**"No particles moving"**
- Wait ~2-5 simulation hours for orders to start
- Check "Pending Orders" count - should increase first
- Check backend logs for order placement messages
- Orders need to be fulfilled before delivery starts

**"Particles disappear when I pause"**
- Should not happen - particles should freeze in place
- If this happens, it's a bug - please report

**"Node details not showing"**
- Make sure you're clicking directly on a node circle
- White border should appear on selected node
- Click background to deselect first, then try again

**"Connection status shows Connecting..."**
- Check backend is running on port 8000
- Check frontend WebSocket connection
- Look for WebSocket errors in browser console (F12)

### 11. Best Viewing Experience

**Recommended sequence:**

1. **Start**: Click Play and watch time advance
2. **0-2 hours**: Watch inventory grow (circles getting bigger)
3. **2-5 hours**: First orders appear (blue flashes, pending queue builds)
4. **5-10 hours**: Deliveries start (red lines, moving particles)
5. **10-20 hours**: System reaches steady state

**Dramatic moments to watch:**
- **Blue flash** = New order placed
- **Red line appears** = Delivery starts
- **Particle journey** = Watch product travel from factory to distributor
- **Particle arrival** = Delivery complete

**Tips:**
- **Click nodes** while simulation runs to watch state variables change
- **Try different speeds** to find what's comfortable
- **Pause** to inspect current state in detail
- **Reset and replay** to see consistent behavior

### 12. Understanding the Console Output

Backend terminal shows detailed logs:

```
[FastAPI] Loaded graph with 11 nodes
[FastAPI] Simulation initialized at t=0

[API] Processes started
[API] Simulation playing

[Animation] Time: 0.00 -> 0.10 hrs (+0.10hrs @ 1.0x speed)
[Animation] Time: 0.10 -> 0.20 hrs (+0.10hrs @ 1.0x speed)

[Order] order-001: Boston Distributor → Chicago Manufacturing Center (45 units, 165.2 miles)

[Fulfill] Chicago Manufacturing Center: order-001 shipped to Boston Distributor (45 units, ETA=3.3hrs)

[Delivery] Chicago Manufacturing Center: order-001 delivered to distributor_boston (total time=4.5hrs)
```

This shows:
- Graph loaded successfully
- Processes starting on play
- Time advancing in 0.1-hour steps
- Orders being placed with routing
- Orders being fulfilled and shipped
- Deliveries completing

## Summary

**To see animation:**
1. Start backend (`cd backend && python api.py`)
2. Start frontend (`cd frontend && npm run dev`)
3. Open http://localhost:5173
4. Click **▶ Play**
5. Watch time advance, circles grow, particles move

**The animation is working when:**
- Time display is advancing
- Console shows time logs
- Circle sizes change
- Blue flashes appear
- Orange particles move along red lines
- Statistics update continuously

**Interactive features:**
- Click nodes for detailed inspection
- Pause/resume preserves exact position
- Speed control adjusts playback rate
- Pan/zoom for better viewing

Enjoy watching your digital twin come alive! 🎬
