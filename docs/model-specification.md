# Product Delivery Model Specification

## Overview

A single-echelon supply chain simulation modeling product manufacturing and distribution across multiple manufacturing centers. This model demonstrates Zurvan principles without the formal library implementation.

**Purpose**: Demonstrate Zurvan's graph-based, constraint-layered approach to discrete event simulation before the library exists.

**Scope**: Manufacturing + distribution system with inventory management and cost optimization (NO reinforcement learning - pure simulation).

---

## Domain Description

A supply chain where:
- Manufacturing centers produce products continuously at controllable rates
- Distributors place orders with varying patterns
- Orders are routed to the nearest manufacturing center
- System must balance inventory holding costs vs. production costs
- Goal: Meet order fulfillment targets while minimizing costs

---

## Resources (Nodes)

### Manufacturing Centers
- **Quantity**: 3 centers
- **Locations**: Chicago, Pittsburgh, Nashville
- **Properties**:
  - Current inventory level
  - Current production rate (0-200 units/hour)
  - Machine state
  - Geographic coordinates (for nearest-neighbor routing)

### Distributors
- **Properties**:
  - Location
  - Order probability by day of week
  - Order size distribution
  - Geographic coordinates

### Products
- **Properties**:
  - Quantity
  - Location (which manufacturing center)
  - Status (in production, in inventory, in transit, delivered)

### Manufacturing Machines
- **Properties**:
  - Production rate (current)
  - Target production rate
  - State (idle, producing, adjusting rate)

---

## Actions

### Atomic Actions

1. **Manufacture Product**
   - **Resources**: Manufacturing machine, raw materials
   - **Time**: Continuous process (rate-based)
   - **State Change**: Increase inventory at manufacturing center
   - **Output**: Products added to inventory

2. **Change Production Rate**
   - **Resources**: Manufacturing machine
   - **Time**: 2-hour exponential delay
   - **State Change**: Machine transitions from current rate to target rate
   - **Constraints**: Rate must be between 0-200 units/hour

3. **Place Order**
   - **Resources**: Distributor
   - **Time**: Instantaneous (event-based)
   - **State Change**: Create order entity
   - **Pattern**: Probability-based (varies by day of week)

4. **Route Order**
   - **Resources**: Order, manufacturing center locations
   - **Time**: Instantaneous (decision)
   - **State Change**: Assign order to nearest manufacturing center
   - **Logic**: Nearest-neighbor based on geographic distance

5. **Fulfill Order**
   - **Resources**: Inventory at assigned manufacturing center
   - **Time**: Variable (depends on inventory availability)
   - **State Change**: Decrease inventory, mark order as fulfilled
   - **Constraints**: Must have sufficient inventory

### Composite Actions

1. **Process Order** (combines Route + Fulfill)
   - Route order to nearest center
   - Wait for inventory availability
   - Fulfill order
   - Calculate fulfillment time

2. **Manage Production** (production control strategy)
   - Monitor inventory levels
   - Monitor incoming orders
   - Decide on production rate adjustments
   - Execute rate changes

---

## Time Constraints (Temporal Layer)

### Production Timing
- **Production rate**: 0-200 units/hour (continuous)
- **Rate change delay**: 2-hour exponential delay when adjusting production rate

### Order Timing
- **Order cycle**: 13-week simulation period
- **Order arrival**: Probabilistic based on day of week
- **Fulfillment target**: <24 hours (goal)
- **Fulfillment constraint**: <48 hours (hard limit)

### Simulation Clock
- Discrete event simulation with continuous processes
- Events: order arrivals, production completions, rate changes, fulfillments

---

## Spatial Constraints (Physical Layer)

### Geographic Layout
- Manufacturing centers at specific locations (Chicago, Pittsburgh, Nashville)
- Distributors at various locations
- Distance-based routing (nearest manufacturing center)

### Inventory Capacity
- Physical storage at each manufacturing center
- Inventory levels affect holding costs

---

## Cost Model

### Holding Costs
- **Type**: Proportional to on-hand inventory
- **Calculation**: Cost per unit per time period × inventory level
- **Purpose**: Penalizes excess inventory

### Maintenance Costs
- **Fixed component**: Base machine operating cost
- **Variable component**: Additional cost when changing production rates
- **Purpose**: Penalizes frequent production adjustments

### Total Daily Cost
- Sum of holding costs + maintenance costs across all centers
- **Goal**: Compare policies based on relative cost efficiency

---

## Control Strategies (Intentions)

Since we're not using RL, we'll implement baseline control strategies:

### 1. Static Production Rate
- Set fixed production rate (e.g., 100 units/hour)
- Never adjust
- Simplest baseline

### 2. Linear Inventory Policy
- Adjust production based on current inventory level
- If inventory < threshold: increase production
- If inventory > threshold: decrease production
- Linear relationship

### 3. Demand-Based Heuristic
- Calculate expected daily demand
- Set production rate to match expected demand
- Adjust based on recent order patterns

### 4. Manual Control (for demonstration)
- User specifies production rates
- Demonstrates scenario execution

---

## Zurvan Architecture Mapping

### Structural Layer (Layer 1)
- **Graph nodes**: Manufacturing centers, distributors, machines, inventory
- **Graph edges**:
  - Center-to-distributor (distance/routing)
  - Machine-to-center (ownership)
  - Inventory-to-center (location)
- **State storage**: Graph database (or dictionary for demo)

### Temporal Layer (Layer 2)
- **Event loop**: Discrete event simulation engine
- **Events**: Order arrivals, production ticks, rate changes, fulfillments
- **Resource constraints**: Inventory availability, machine state
- **Time constraints**: Production rates, delays, fulfillment windows

### Physical Layer (Layer 3)
- **Geographic constraints**: Distance-based routing
- **Capacity constraints**: Inventory storage limits
- **Physical resources**: Manufacturing machines, storage facilities

---

## State Management

### Node States (stored in graph database)

**Manufacturing Center Node**:
```python
{
  "id": "chicago_center",
  "type": "manufacturing_center",
  "location": {"lat": 41.8781, "lon": -87.6298},
  "inventory": 500,  # current inventory level
  "production_rate": 100,  # units/hour
  "target_rate": 100,
  "machine_state": "producing"
}
```

**Distributor Node**:
```python
{
  "id": "distributor_1",
  "type": "distributor",
  "location": {"lat": 40.7128, "lon": -74.0060},
  "order_probability": {
    "monday": 0.3,
    "tuesday": 0.4,
    # ... etc
  },
  "order_size_mean": 50,
  "order_size_std": 10
}
```

**Order Node** (created during simulation):
```python
{
  "id": "order_001",
  "type": "order",
  "distributor": "distributor_1",
  "assigned_center": "chicago_center",
  "quantity": 45,
  "arrival_time": 1.5,  # simulation time
  "fulfillment_time": None,
  "status": "pending"
}
```

---

## Scenarios to Demonstrate

### Scenario 1: Baseline Static Production
- All centers produce at fixed rate (100 units/hour)
- Measure fulfillment times and costs
- Shows default behavior

### Scenario 2: Demand Surge
- Introduce spike in orders on specific days
- Compare how different strategies handle surge
- Demonstrates scenario execution

### Scenario 3: Production Rate Optimization
- Test different inventory policies
- Show impact of rate change delays
- Demonstrates intention-based control

### Scenario 4: Interactive Control
- User manually adjusts production rates during simulation
- Shows SimCity-style interaction
- Demonstrates real-time scenario manipulation

---

## Implementation Approach (Manual Zurvan)

### Phase 1: Build the Graph
- Create nodes for centers, distributors, machines
- Define relationships (edges)
- Initialize states

### Phase 2: Implement Actions
- Define action functions (manufacture, change_rate, place_order, etc.)
- Each action takes resources + time as parameters
- Actions update node states in the graph

### Phase 3: Build Event Loop
- Discrete event simulation engine
- Schedule events (order arrivals, production ticks, etc.)
- Process events in time order

### Phase 4: Add Visualization
- Real-time state display
- Show active actions and resource usage
- Display costs and metrics

### Phase 5: Scenario Execution
- Implement control strategies as intention nodes
- Run different scenarios
- Compare results

---

## Success Metrics

### Performance Metrics
- Average order fulfillment time
- Percentage of orders fulfilled within 24 hours
- Percentage of orders exceeding 48 hours (violations)

### Cost Metrics
- Total daily holding cost
- Total daily maintenance cost
- Daily cost delta vs. baseline

### System Metrics
- Average inventory levels per center
- Production rate stability (number of changes)
- Inventory stockouts (unfulfilled orders due to zero inventory)

---

## Implementation Approach: SimPy-Based

This demo uses **SimPy** as the discrete event simulation engine while maintaining Zurvan's architectural principles.

### SimPy Integration

1. **ResourceNode class** - Nodes are autonomous agents (SimPy Agent pattern)
   ```python
   class ResourceNode:
       def __init__(self, env, node_id, node_type, static_data):
           self.env = env               # SimPy environment
           self.connections = []        # Graph edges
           self.state = {}              # Dynamic state

           # Autonomous agent capabilities
           self.actions = {}            # Available actions (loaded from JSON)
           self.automatic_actions = []  # Actions that auto-start
           self.active_processes = []   # Running SimPy processes

       def _register_actions(self):
           """Data-driven: Load actions from properties (no if/else)"""
           action_config = self.properties.get('actions', {})
           module_name = action_config.get('module')
           available_action_names = action_config.get('available', [])
           # Dynamically import and register action functions

       def start(self):
           """Node starts its own auto-start actions"""
           if not self.actions:
               self.actions = self._register_actions()
               self.automatic_actions = self._get_automatic_actions()

           policies_config = self.properties.get('policies', {})

           for action_config in self.automatic_actions:
               # Extract configuration
               action_name = action_config['name']
               function_name = action_config['function']
               policy_ref = action_config['policy_ref']
               resource_spec = action_config.get('resource')
               time = action_config['time']

               # Get action function and create policy
               action_func = self.actions.get(function_name)
               policy = self._create_policy(policies_config[policy_ref])
               resource = self._resolve_resource(resource_spec)

               # Start policy-driven loop
               process = self.env.process(
                   self._policy_driven_loop(action_func, policy, resource, time)
               )
               self.active_processes.append({'name': action_name, 'process': process})
   ```

2. **Actions as generator functions** - Use `yield env.timeout()` for time
   ```python
   def continuous_production(manufacturing_center):
       while True:
           if manufacturing_center.state['production_rate'] > 0:
               yield manufacturing_center.env.timeout(1.0 / rate)
               manufacturing_center.state['inventory'] += 1
   ```

3. **Action configuration in JSON** - Data-driven, no hardcoded logic
   ```json
   {
     "id": "chicago_center",
     "type": "manufacturing_center",
     "properties": {
       "capacity": 1000,
       "initial_inventory": 500,
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
     - `function`: Function name to call
     - `auto_start`: Whether to activate on node initialization
     - `policy_ref`: Reference to policy that controls execution
     - `resource`: Required resource (null, "graph", etc.)
     - `time`: Time parameter for the action
   - `policies`: Policy configurations that control when/how often actions execute

4. **Simulation class wrapper** - Simplified with autonomous agents
   ```python
   class ProductDeliverySimulation:
       def __init__(self, graph):
           self.env = simpy.RealtimeEnvironment()
           self.graph = graph
           # Attach env to all nodes
           for node in graph.nodes.values():
               node.env = self.env

       def start_all_processes(self):
           """Nodes are autonomous - just tell them to start"""
           for node in self.graph.nodes.values():
               node.start()  # Each node manages its own actions
   ```

5. **Real-time visualization** - Streamlit + Folium with live updates
   - Simulation steps forward: `sim.env.run(until=env.now + 0.1)`
   - Map refreshes showing updated node states

### Technology Stack

- **Simulation Engine**: SimPy (discrete event simulation)
- **Graph Structure**: Custom ZurvanGraph + ResourceNode objects
- **Visualization**: Streamlit + Folium (interactive GIS map)
- **Data**: JSON files for initial state, in-memory for simulation
- **Random**: NumPy for distributions

### Zurvan Layer Mapping

- **Layer 1 (Structural)**: ZurvanGraph + ResourceNode objects
- **Layer 2 (Temporal)**: SimPy environment + generator functions
- **Layer 3 (Physical)**: Geographic coordinates + distance calculations

See `simpy-patterns-analysis.md` for detailed pattern documentation.

---

## Implementation Steps

1. ✅ Create graph structure (nodes + edges) - **Step 1 Complete**
2. ✅ Create ResourceNode class (SimPy Agent pattern) - **Step 2 Complete**
3. ✅ Implement actions as generator functions - **Step 3 Complete**
4. ✅ Build Simulation wrapper class - **Step 4 Complete**
5. ✅ Activate processes and run simulation - **Step 5 Complete**
6. ✅ Add continuous production - **Step 6 Complete**
7. ✅ Add order generation and routing - **Step 7 Complete**
8. ✅ Add order fulfillment - **Step 8 Complete**
9. Add cost tracking - **Step 9** ← NEXT
10. Add control strategies (intention nodes) - **Step 10**
11. Run scenarios and compare policies - **Step 11**
12. Add interactive manipulation (SimCity mode) - **Step 12**
