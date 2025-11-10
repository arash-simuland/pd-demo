# Step-by-Step Modeling Process

## Philosophy

Build the model incrementally with **visual verification at each step**. Each step produces a working, visualizable artifact before moving to the next. This follows Zurvan's philosophy of understanding the system structure before adding complexity.

## Implementation Approach: SimPy-Based

This demo uses **SimPy** (Simulated Python) as the discrete event simulation engine, following proven patterns from the Simple-Message-Passing examples. Key architectural decisions:

- **ResourceNode class** (SimPy Agent pattern) - Nodes are objects with state and connections
- **Generator functions as actions** - Actions use `yield env.timeout()` for time constraints
- **Simulation class wrapper** - Scenarios encapsulate graph + processes
- **RealtimeEnvironment** - Enables real-time visualization updates
- **Separation of concerns** - Graph structure (Layer 1) + SimPy processes (Layer 2) + Visualization (Layer 3)

See `simpy-patterns-analysis.md` for detailed pattern documentation.

---

## Step 1: Build the Structural Layer (Static Graph)

**Goal**: Create the base graph with all nodes and their static properties. No actions, no simulation - just the "things" and their connections.

### What We Build:
- Manufacturing center nodes (Chicago, Pittsburgh, Nashville)
- Distributor nodes (5-10 distributors at various locations)
- Initial properties (location, capacity, etc.)
- Relationships (distances between nodes)

### Visualization:
- **GIS map** showing all nodes as markers
- Manufacturing centers as blue circles
- Distributors as green triangles
- **Click any node** → popup shows:
  - Node ID
  - Node type
  - Location (lat/lon)
  - Static properties (capacity, etc.)
- Lines showing distances/connections

### Deliverables:
- `graph_builder.py` - Creates the graph structure
- `visualizer.py` - Interactive GIS map with clickable nodes
- `data/nodes.json` - Node definitions
- `data/edges.json` - Relationship definitions

### Verification Checklist:
- [ ] All 3 manufacturing centers appear on map
- [ ] All distributors appear on map
- [ ] Clicking each node shows correct properties
- [ ] Distances/connections are visible
- [ ] No errors in console

**STOP HERE** - Don't proceed until visualization works and you verify the graph structure is correct.

---

## Step 2: Create ResourceNode Class with State

**Goal**: Convert graph from dictionaries to ResourceNode objects (SimPy Agent pattern). Add dynamic state properties while keeping everything static. Still no simulation - just showing what state each node will track.

**Architecture**: Nodes are **autonomous agents** that manage their own actions. Each node knows what actions it can perform and starts them automatically when activated.

### What We Build:
- **`resource_node.py`** - ResourceNode class (autonomous agent pattern):
  ```python
  class ResourceNode:
      def __init__(self, env, node_id, node_type, static_data):
          self.env = env              # SimPy environment (None for now)
          self.node_id = node_id
          self.node_type = node_type
          self.connections = []       # Graph edges
          self.state = {}             # Dynamic state

          # Action management (autonomous agent capabilities)
          self.actions = {}           # Available actions (loaded from properties)
          self.automatic_actions = [] # Actions that auto-start
          self.active_processes = []  # Currently running SimPy processes

      def _register_actions(self):
          """Data-driven: Load actions from properties (no if/else)"""
          action_config = self.properties.get('actions', {})
          module_name = action_config.get('module')
          available_action_names = action_config.get('available', [])
          # Dynamically import action module and register functions

      def _get_automatic_actions(self):
          """Data-driven: Get actions with auto_start=True from properties"""
          action_config = self.properties.get('actions', {})
          available_actions = action_config.get('available', [])
          return [a for a in available_actions if isinstance(a, dict) and a.get('auto_start', False)]

      def start(self):
          """Node starts its own auto-start actions (autonomous agent)"""
          if not self.actions:
              self.actions = self._register_actions()
              self.automatic_actions = self._get_automatic_actions()

          policies_config = self.properties.get('policies', {})

          for action_config in self.automatic_actions:
              action_name = action_config['name']
              function_name = action_config['function']
              policy_ref = action_config['policy_ref']
              resource_spec = action_config.get('resource')
              time = action_config['time']

              action_func = self.actions.get(function_name)
              policy = self._create_policy(policies_config[policy_ref])
              resource = self._resolve_resource(resource_spec)

              process = self.env.process(
                  self._policy_driven_loop(action_func, policy, resource, time)
              )
              self.active_processes.append({'name': action_name, 'process': process})
  ```
- **State initialization** based on node type:
  - Manufacturing centers: `inventory`, `production_rate`, `machine_state`
  - Distributors: `orders_placed`, `orders_fulfilled`
- **Action configuration in JSON** (`data/nodes.json`):
  ```json
  {
    "properties": {
      "capacity": 1000,
      "actions": {
        "module": "manufacturing_actions",
        "available": [
          {
            "name": "continuous_production",
            "function": "produce_batch",
            "auto_start": true,
            "policy_ref": "production_policy",
            "resource": null,
            "time": 1.0
          },
          {
            "name": "process_pending_orders",
            "function": "check_and_fulfill_orders",
            "auto_start": true,
            "policy_ref": "fulfillment_policy",
            "resource": null,
            "time": 0.1
          }
        ]
      },
      "policies": {
        "production_policy": {
          "type": "ContinuousProductionPolicy",
          "interval": 0.0
        },
        "fulfillment_policy": {
          "type": "ContinuousOrderFulfillmentPolicy",
          "interval": 1.0
        }
      }
    }
  }
  ```
- **Update `graph_builder.py`** to create ResourceNode objects instead of dicts

### Visualization Enhancement:
- **Same GIS map** but now clicking a node shows:
  - Static properties (from Step 1)
  - **NEW**: Dynamic state properties from `node.state`
  - Color coding by state (idle = gray, producing = green)
- Add a **state panel** showing summary statistics:
  - Total inventory across all centers
  - Total production rate
  - Number of idle vs. active machines

### Deliverables:
- `resource_node.py` - ResourceNode class (SimPy Agent pattern)
- Updated `graph_builder.py` - Creates ResourceNode objects
- Updated `visualizer.py` - Shows `node.state` in popups
- `data/initial_state.json` - Initial state values (reference)

### Verification Checklist:
- [ ] Clicking manufacturing center shows inventory and production rate
- [ ] State panel shows correct totals
- [ ] Color coding reflects machine states
- [ ] Can manually edit state values and see updates in visualization
- [ ] Node has `actions`, `automatic_actions`, `active_processes` attributes
- [ ] Actions configured in `data/nodes.json`
- [ ] `_register_actions()` dynamically loads actions from module
- [ ] `_get_automatic_actions()` reads automatic actions from config

**STOP HERE** - Verify that state management and action structure work before defining actions.

---

## Step 3: Define Actions as Generator Functions

**Goal**: Define action types as SimPy generator functions (not executed yet). Show what actions are available and their time/resource requirements.

### What We Build:
- **Action generator functions** (SimPy pattern - actions use `yield env.timeout()`):
  ```python
  def continuous_production(manufacturing_center):
      """Atomic action: manufacture products continuously"""
      while True:
          if manufacturing_center.state['production_rate'] > 0:
              yield manufacturing_center.env.timeout(1.0 / manufacturing_center.state['production_rate'])
              manufacturing_center.state['inventory'] += 1
          else:
              yield manufacturing_center.env.timeout(1.0)
  ```
- Action catalog in `actions/` directory:
  - `manufacturing_actions.py` - `continuous_production()`, `change_production_rate()`
  - `order_actions.py` - `generate_orders()`, `route_order()`, `fulfill_order()`
- Each action specifies:
  - Required resources (function parameters)
  - Time constraints (`yield env.timeout()`)
  - State changes (modifies `node.state`)

### Visualization Enhancement:
- **Action catalog panel** showing:
  - List of all available action types
  - For each action: required resources, duration, description
- **Node action menu**: Click a node → see which actions can be performed on it
  - E.g., click manufacturing center → shows "Manufacture", "Change Rate"
  - Actions are grayed out (not executable yet)

### Deliverables:
- `actions/base_action.py` - Base action class
- `actions/manufacturing_actions.py` - Manufacture, ChangeRate actions
- `actions/order_actions.py` - PlaceOrder, RouteOrder, FulfillOrder actions
- Updated `visualizer.py` - Shows action catalog and node menus

### Verification Checklist:
- [ ] Action catalog displays all action types
- [ ] Each action shows correct resource requirements
- [ ] Clicking node shows relevant actions for that node type
- [ ] Action signatures make sense (resources + time)

**STOP HERE** - Verify action definitions are complete before adding execution logic.

---

## Step 4: Create Simulation Class (SimPy Environment)

**Goal**: Wrap graph + actions in a Simulation class (SimPy Pattern 2a). Enable manual process triggering to test individual actions.

### What We Build:
- **`simulation.py`** - Simulation wrapper class:
  ```python
  class ProductDeliverySimulation:
      def __init__(self, graph):
          self.env = simpy.RealtimeEnvironment()
          self.graph = graph
          # Attach env to all nodes
          for node in graph.nodes.values():
              node.env = self.env
  ```
- **Manual process control**: Start/stop individual processes for testing
- **Action logger**: Track all process events
- **SimPy environment** now available to all nodes

### Visualization Enhancement:
- **Enable action buttons**: Click node → click action → see state update
  - E.g., click Chicago center → click "Manufacture 10 units" → inventory increases
  - E.g., click center → click "Set Rate to 100" → production_rate updates
- **Action history panel**: Shows log of all executed actions
  - Timestamp, action type, resources used, state changes
- **Live state updates**: When action executes, map updates in real-time
  - Node colors change
  - State popup values update
  - State panel updates

### Deliverables:
- `action_executor.py` - Executes actions and updates state
- `action_logger.py` - Logs action history
- Updated `visualizer.py` - Interactive action buttons + history panel

### Verification Checklist:
- [ ] Can click "Manufacture" → inventory increases
- [ ] Can click "Change Rate" → production rate updates
- [ ] Action history logs all actions correctly
- [ ] Map updates in real-time when actions execute
- [ ] State panel reflects changes

**STOP HERE** - Verify manual action execution works before adding time/scheduling.

---

## Step 5: Activate Processes and Run Simulation

**Goal**: Start SimPy processes (actions) and run the simulation clock. Real-time visualization of state changes.

**Architecture**: Nodes are autonomous agents that start their own processes. The simulation simply tells each node to activate.

### What We Build:
- **Process activation** - Nodes start their own actions (autonomous agent pattern):
  ```python
  def start_all_processes(self):
      """Nodes are autonomous - just tell them to start"""
      for node in self.graph.nodes.values():
          node.start()  # Each node manages its own actions
  ```

  **How it works**:
  - Each node has `actions` dict (loaded from JSON config)
  - Each node has `automatic_actions` list (actions with `auto_start: true`)
  - Calling `node.start()` activates auto-start actions
  - Node creates policy-driven loops: `self.env.process(self._policy_driven_loop(action, policy, resource, time))`
  - All configuration (action, policy, resource, time) from JSON - zero hardcoded logic

- **Data-driven action configuration** (`data/nodes.json`):
  ```json
  {
    "properties": {
      "actions": {
        "module": "manufacturing_actions",
        "available": [
          {
            "name": "continuous_production",
            "function": "produce_batch",
            "auto_start": true,
            "policy_ref": "production_policy",
            "resource": null,
            "time": 1.0
          },
          {
            "name": "process_pending_orders",
            "function": "check_and_fulfill_orders",
            "auto_start": true,
            "policy_ref": "fulfillment_policy",
            "resource": null,
            "time": 0.1
          }
        ]
      },
      "policies": {
        "production_policy": {
          "type": "ContinuousProductionPolicy",
          "interval": 0.0
        },
        "fulfillment_policy": {
          "type": "ContinuousOrderFulfillmentPolicy",
          "interval": 1.0
        }
      }
    }
  }
  ```
  - `module`: Python module containing action functions
  - `available`: List of action configurations with:
    - `name`: Action identifier
    - `function`: Function to call (e.g., `produce_batch`)
    - `auto_start`: Whether to activate on node initialization
    - `policy_ref`: Reference to policy controlling execution
    - `resource`: Required resource (null, "graph", etc.)
    - `time`: Time parameter for action
  - `policies`: Policy configurations controlling when/how often actions execute

- **SimPy clock**: `env.now` tracks current simulation time
- **Event execution**: SimPy automatically schedules/executes generator yields
- **Time control panel**:
  - Play/Pause simulation
  - Step forward (`env.run(until=env.now + step_size)`)
  - Speed control (via `RealtimeEnvironment` factor)

### Visualization Enhancement:
- **Clock display**: Shows current simulation time
- **Event timeline**: Shows upcoming scheduled events
- **Time controls**: Play/Pause/Step buttons
- **Event execution animation**: When event fires, briefly highlight affected nodes
- **Mode toggle**: Switch between "Manual Mode" (Step 4) and "Simulation Mode" (Step 5)

### Deliverables:
- `simulation_engine.py` - Event loop and clock
- `event_scheduler.py` - Priority queue for events
- Updated `visualizer.py` - Time controls + event timeline

### Verification Checklist:
- [ ] Clock starts at t=0
- [ ] Can schedule events (e.g., "manufacture at t=5")
- [ ] Events execute in correct time order
- [ ] Can pause/resume simulation
- [ ] Can step through events one at a time
- [ ] Event timeline shows upcoming events

**STOP HERE** - Verify time and scheduling work before adding continuous processes.

---

## Step 6: Implement Continuous Production

**Goal**: Add continuous manufacturing process. When production rate > 0, inventory automatically increases over time.

### What We Build:
- **Production process**: When machine has production_rate > 0:
  - Schedule recurring production events
  - Each event adds (production_rate × time_delta) to inventory
- **Rate change delays**: When changing rate, schedule completion event after 2 hours
- **Continuous updates**: Production ticks every hour (or configurable interval)

### Visualization Enhancement:
- **Production animation**: When producing, show particle effects or pulsing
- **Inventory gauge**: Real-time inventory level bar for each center
- **Production rate indicator**: Visual indicator of current production speed
- **Active processes panel**: Shows all ongoing continuous processes

### Deliverables:
- `processes/manufacturing_process.py` - Continuous production logic
- Updated `simulation_engine.py` - Handles continuous processes
- Updated `visualizer.py` - Production animations + gauges

### Verification Checklist:
- [ ] Setting production rate > 0 starts continuous production
- [ ] Inventory increases automatically over time
- [ ] Production rate changes have 2-hour delay
- [ ] Can see production happening in real-time
- [ ] Stopping production (rate = 0) stops inventory growth

**STOP HERE** - Verify continuous production works before adding orders.

---

## Step 7: Add Order Generation and Routing

**Goal**: Distributors start generating orders based on probabilities. Orders are routed to nearest manufacturing center.

### What We Build:
- **Order generation**: Each distributor generates orders based on:
  - Day of week probabilities
  - Order size distribution (mean ± std)
- **Order routing**: New orders automatically routed to nearest center
- **Order queue**: Each center maintains a queue of pending orders

### Visualization Enhancement:
- **Order nodes**: Orders appear as small circles on the map
- **Routing lines**: Animated line from distributor to assigned center when order placed
- **Order queue panel**: For each center, shows pending orders
- **Order flow animation**: Orders move from distributor to center
- **Order statistics**: Total orders, pending, fulfilled

### Deliverables:
- `processes/order_generation.py` - Probabilistic order creation
- `processes/order_routing.py` - Nearest-neighbor routing
- Updated `visualizer.py` - Order animations + queue panel

### Verification Checklist:
- [ ] Orders appear on map when generated
- [ ] Orders route to nearest manufacturing center
- [ ] Order queue shows pending orders correctly
- [ ] Can click order to see details (quantity, arrival time, assigned center)
- [ ] Order generation respects day-of-week probabilities

**STOP HERE** - Verify order generation and routing before adding fulfillment.

---

## Step 8: Add Order Fulfillment ✅ COMPLETE

**Goal**: Centers fulfill orders from inventory. Orders have fulfillment times. Track metrics.

### What We Built:
- **Fulfillment logic**: `process_pending_orders` action - FIFO queue processing when inventory available
- **Fulfillment timing**: Track time from order placement to fulfillment (placement_time → fulfillment_time)
- **Inventory constraint**: Cannot fulfill if insufficient inventory (inventory >= order.quantity check)
- **Metrics tracking**:
  - Average fulfillment time (calculated from fulfillment_times list)
  - Orders fulfilled within 24 hours
  - Orders fulfilled within 48 hours
  - SLA violations (orders exceeding 48 hours)

### Visualization Enhancements:
- **Order status colors**:
  - Green: Fulfilled orders
  - Yellow: Pending orders
  - Red: Violated SLA (>48 hours)
- **Order status display**: Border colors and status text in order queue panel
- **Fulfillment metrics dashboard**: Real-time display of all KPIs
  - Orders fulfilled count
  - Quantity fulfilled
  - Average fulfillment time
  - 24hr/48hr compliance counts
  - SLA violations highlighted in red
- **Inventory alerts**: Red "⚠️ LOW INVENTORY" warning when inventory < 100 units
- **Color-coded inventory**: Red (<100), Yellow (100-300), Green (>300)

### Deliverables:
- `actions/manufacturing_actions.py` - Added `process_pending_orders()` action (line 131-198)
- `resource_node.py` - Added `fulfillment_times` and `sla_violations` to state initialization
- `simulation.py` - Activated `process_pending_orders` for all manufacturing centers
- `dash_components/action_panel.py` - Fulfillment metrics dashboard with KPIs
- `dash_components/sidebar_component.py` - Order status colors and inventory alerts
- Updated `README.md` - Step 8 completion and verification checklist

### Verification Checklist:
- [x] Orders fulfill when inventory available
- [x] Fulfillment time calculated correctly
- [x] Metrics update in real-time
- [x] Low inventory triggers visual alerts
- [x] Cannot fulfill orders when inventory = 0
- [x] FIFO queue processing (oldest order first)
- [x] Order status updated to 'fulfilled' when completed
- [x] Fulfillment messages printed to console
- [x] SLA violations tracked for orders > 48 hours
- [x] Real-time metrics dashboard updates automatically

**✅ STEP 8 COMPLETE** - Ready to proceed to Step 9 (Cost Tracking).

---

## Step 9: Add Cost Tracking

**Goal**: Track holding costs and maintenance costs. Display cost metrics.

### What We Build:
- **Holding cost calculation**: Cost per unit × inventory level × time
- **Maintenance cost calculation**:
  - Fixed cost (when machine running)
  - Variable cost (when changing production rate)
- **Daily cost aggregation**: Total daily costs per center
- **Cost history**: Track costs over time

### Visualization Enhancement:
- **Cost dashboard**:
  - Real-time holding cost
  - Real-time maintenance cost
  - Daily total cost
  - Cost delta vs. baseline
- **Cost graphs**: Line charts showing costs over time
- **Cost breakdown**: Pie chart of holding vs. maintenance
- **Policy comparison**: Cost differences between current and baseline policies

### Deliverables:
- `cost_calculator.py` - Calculate holding and maintenance costs
- Updated `metrics_tracker.py` - Track cost history
- Updated `visualizer.py` - Cost dashboard + graphs

### Verification Checklist:
- [ ] Holding costs increase with inventory
- [ ] Maintenance costs charged when machine active
- [ ] Rate changes incur additional maintenance cost
- [ ] Daily cost totals are correct
- [ ] Cost graphs update in real-time

**STOP HERE** - Verify cost tracking before adding control strategies.

---

## Step 10: Add Control Strategies (Intention Nodes)

**Goal**: Implement baseline control strategies that automatically adjust production rates based on policies.

### What We Build:
- **Policy/Intention nodes**: Special nodes that contain decision logic
- **Control strategies**:
  1. Static policy: Fixed production rate
  2. Linear inventory policy: Adjust based on inventory thresholds
  3. Demand-based policy: Adjust based on recent order patterns
- **Policy activation**: User selects which policy to use per center
- **Policy parameters**: Configurable (e.g., inventory thresholds, target levels)

### Visualization Enhancement:
- **Policy selector**: Dropdown to choose policy for each center
- **Policy state panel**: Shows current policy decisions
  - E.g., "Linear Policy: Inventory = 300 (below target 500) → Increasing rate to 120"
- **Policy graph**: Visualize policy logic (e.g., inventory vs. production rate curve)
- **Policy comparison mode**: Split screen showing multiple policies side-by-side

### Deliverables:
- `policies/base_policy.py` - Base policy class
- `policies/static_policy.py` - Static rate policy
- `policies/linear_inventory_policy.py` - Linear policy
- `policies/demand_based_policy.py` - Demand-based policy
- Updated `visualizer.py` - Policy selector + state panel

### Verification Checklist:
- [ ] Can select policy for each center
- [ ] Static policy maintains constant rate
- [ ] Linear policy adjusts rate based on inventory
- [ ] Demand policy responds to order patterns
- [ ] Policy decisions visible in real-time

**STOP HERE** - Verify policies work before running full scenarios.

---

## Step 11: Scenario Execution and Comparison

**Goal**: Run complete scenarios, compare different policies, analyze results.

### What We Build:
- **Scenario configurations**: Predefined scenarios (baseline, surge, optimization)
- **Scenario runner**: Execute scenario with selected policies
- **Comparison framework**: Run same scenario with different policies
- **Results analysis**: Generate reports comparing performance

### Visualization Enhancement:
- **Scenario selector**: Choose from predefined scenarios
- **Comparison view**: Side-by-side or overlay comparison of policies
- **Results dashboard**:
  - Fulfillment time comparison
  - Cost comparison
  - Inventory level comparison
- **Replay mode**: Replay simulation from saved history
- **Export results**: Save metrics to CSV/JSON

### Deliverables:
- `scenario_runner.py` - Execute scenarios with policies
- `scenario_configs/` - JSON files defining scenarios
- `results_analyzer.py` - Compare and analyze results
- Updated `visualizer.py` - Comparison view + results dashboard

### Verification Checklist:
- [ ] Can load and run predefined scenarios
- [ ] Can compare multiple policies on same scenario
- [ ] Results show clear performance differences
- [ ] Can replay simulations
- [ ] Can export results for further analysis

**STOP HERE** - Verify scenario execution before adding advanced features.

---

## Step 12: Interactive Manipulation (SimCity Mode)

**Goal**: Allow user to interact with running simulation - change rates, inject orders, modify policies on-the-fly.

### What We Build:
- **Live intervention**: Pause simulation and manually:
  - Change production rates
  - Inject custom orders
  - Modify inventory levels
  - Switch policies mid-simulation
- **What-if scenarios**: Fork simulation at any point to explore alternatives
- **Intervention history**: Track all manual interventions

### Visualization Enhancement:
- **Intervention panel**: UI for live manipulation
- **Branch visualization**: Show simulation forks/branches
- **Comparison mode**: Compare intervened vs. non-intervened timelines
- **Intervention markers**: Timeline shows when user intervened

### Deliverables:
- `intervention_manager.py` - Handle live interventions
- `simulation_brancher.py` - Fork simulations
- Updated `visualizer.py` - Intervention panel + branch view

### Verification Checklist:
- [ ] Can pause and change production rates mid-simulation
- [ ] Can inject orders manually
- [ ] Can fork simulation to test alternatives
- [ ] Interventions tracked in history
- [ ] Can compare intervened vs. baseline

---

## Technology Stack

### Core Libraries:
- **Discrete Event Simulation**: SimPy (discrete event simulation engine)
- **Graph structure**: Custom ZurvanGraph + ResourceNode objects
- **Random generation**: NumPy for distributions
- **Time/date**: SimPy's environment clock (`env.now`)

### Visualization:
- **GIS map**: Folium (creates interactive HTML maps)
- **Interactive UI**: Streamlit (real-time updates)
- **Graphs/charts**: Plotly or Matplotlib
- **Real-time updates**: Streamlit + SimPy RealtimeEnvironment

### Data Management:
- **Node state**: In-memory (`node.state` dict)
- **Graph structure**: ResourceNode objects in ZurvanGraph
- **Initial data**: JSON files (`nodes.json`, `edges.json`)
- **Graph database (future)**: Neo4j for scalability

---

## File Structure

```
product-delivery-demo/
├── model-specification.md
├── step-by-step-modeling-process.md (this file)
├── requirements.txt
├── README.md
│
├── src/
│   ├── graph_builder.py          # Step 1
│   ├── state_manager.py          # Step 2
│   ├── action_executor.py        # Step 4
│   ├── action_logger.py          # Step 4
│   ├── simulation_engine.py      # Step 5
│   ├── event_scheduler.py        # Step 5
│   ├── cost_calculator.py        # Step 9
│   ├── metrics_tracker.py        # Step 8, 9
│   ├── intervention_manager.py   # Step 12
│   ├── simulation_brancher.py    # Step 12
│   │
│   ├── actions/
│   │   ├── base_action.py        # Step 3
│   │   ├── manufacturing_actions.py  # Step 3
│   │   └── order_actions.py      # Step 3
│   │
│   ├── processes/
│   │   ├── manufacturing_process.py   # Step 6
wht│   │   ├── order_generation.py        # Step 7
│   │   ├── order_routing.py           # Step 7
│   │   └── order_fulfillment.py       # Step 8
│   │
│   ├── policies/
│   │   ├── base_policy.py             # Step 10
│   │   ├── static_policy.py           # Step 10
│   │   ├── linear_inventory_policy.py # Step 10
│   │   └── demand_based_policy.py     # Step 10
│   │
│   └── visualizer.py             # All steps (evolves)
│
├── data/
│   ├── nodes.json                # Step 1
│   ├── edges.json                # Step 1
│   └── initial_state.json        # Step 2
│
├── scenario_configs/
│   ├── baseline.json             # Step 11
│   ├── demand_surge.json         # Step 11
│   └── optimization.json         # Step 11
│
└── outputs/
    ├── results/                  # Simulation results
    └── logs/                     # Action logs
```

---

## Development Workflow

For each step:

1. **Read the step specification** (above)
2. **Create/modify the files** listed in "Deliverables"
3. **Run the visualizer** to see the new features
4. **Check the verification checklist** - all items must pass
5. **Get approval** before moving to next step
6. **Commit the working code** (optional but recommended)

This ensures we always have a working, visualizable system at each stage.

---

## Next Actionyes
