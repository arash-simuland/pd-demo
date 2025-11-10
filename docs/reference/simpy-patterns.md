# SimPy Message Passing Patterns - Analysis

This document analyzes several SimPy implementation patterns from the Simple-Message-Passing examples, showing progressive levels of sophistication for agent-based simulation.

---

## Pattern 0a: Simplest Implementation (Functional)

**File**: `sim_0a.py`

### Key Ideas:

1. **Global parameters** - Simple configuration
   ```python
   RATE = 1
   DELAY = 0.1
   ```

2. **RealtimeEnvironment** - Simulation runs in real-time for visualization
   ```python
   env = simpy.RealtimeEnvironment()
   ```

3. **Generator functions as processes** - SimPy uses Python generators
   ```python
   def send_periodic_messages(sender_name, receiver_name):
       counter = 0
       while True:
           yield env.timeout(random.expovariate(RATE))
           print(f"Agent '{sender_name}' sending message: {counter}")
           env.process(receive_message(receiver_name, counter))
           counter += 1
   ```

4. **Process spawning** - New processes created dynamically
   ```python
   env.process(receive_message(receiver_name, counter))
   ```

5. **Time-based delays** - Actions take time
   ```python
   yield env.timeout(DELAY)
   ```

### Zurvan Mapping:
- **Action**: `send_periodic_messages()` - Uses time (exponential rate)
- **Action**: `receive_message()` - Uses time (fixed delay)
- **Temporal constraint**: Random intervals for sending, fixed delay for receiving

---

## Pattern 0b: Adding Metrics (Functional with State Tracking)

**File**: `sim_0b-metrics.py`

### Key Ideas:

1. **Global state tracking** - Metrics accumulated during simulation
   ```python
   total = 0
   num_messages = 0
   ```

2. **State updates in processes** - Modify global state
   ```python
   def receive_message(receiver_name: str, message: int):
       global total, num_messages
       yield env.timeout(DELAY)
       total += message
       num_messages += 1
       print(f"received: {message} ({total} / x{num_messages} = μ {total / num_messages:.2f})")
   ```

3. **Random message generation** - More realistic data
   ```python
   message = random.randint(1, 9)
   ```

4. **Real-time statistics** - Calculate metrics on-the-fly
   ```python
   μ {total / num_messages:.2f}
   ```

### Zurvan Mapping:
- **State management**: Global metrics tracked in "graph database" equivalent
- **Actions update state**: Each receive action modifies accumulated totals
- **Real-time aggregation**: Similar to Zurvan's live state updates

---

## Pattern 1: Agent-Based (Object-Oriented)

**File**: `sim_1.py` + `agent.py`

### Key Ideas:

1. **Agent class** - Encapsulates agent behavior and state
   ```python
   class Agent:
       def __init__(self, env, name=None):
           self.env = env
           self.name = name
           self.connections = []        # Graph edges!
           self.current_message = None  # State property
   ```

2. **Agent connections as graph structure**
   ```python
   self.connections = []  # List of connected agents
   ```

3. **Message passing between agents**
   ```python
   def send_to_connected(self, message, delay=0):
       def send_event():
           yield self.env.timeout(delay)
           for other in self.connections:
               other.receive(message)
       self.env.process(send_event())
   ```

4. **State stored in agents**
   ```python
   def receive(self, message):
       self.current_message = message
   ```

5. **Separation of concerns** - Agent behavior separate from simulation logic
   ```python
   # Agent class in agent.py
   # Simulation logic in sim_1.py
   ```

### Zurvan Mapping:
- **Agent = Resource node** in Zurvan graph
- **`connections[]` = Graph edges** (relationships between nodes)
- **`current_message` = Node state** (stored in graph database)
- **`send_to_connected()` = Action** that uses resources (other agents) and time (delay)
- **`receive()` = State update** modifying node properties

**This pattern closely resembles Zurvan's architecture!**

---

## Pattern 2a: Simulation Class (Encapsulated System)

**File**: `sim_2a.py`

### Key Ideas:

1. **Simulation wrapper class** - Encapsulates entire system
   ```python
   class Simulation:
       def __init__(self, rate=1, delay=0.1):
           self.rate = rate
           self.delay = delay
           self.env = simpy.RealtimeEnvironment()
           self.agent_1 = Agent(self.env, "Abby")
           self.agent_2 = Agent(self.env, "Burt")
           self.agent_1.connections.append(self.agent_2)
           self.env.process(self.send_periodic_messages(self.agent_1))
   ```

2. **Graph construction in init** - Build network structure
   ```python
   self.agent_1.connections.append(self.agent_2)
   ```

3. **Scenario initialization** - Start processes
   ```python
   self.env.process(self.send_periodic_messages(self.agent_1))
   ```

4. **Parameterized configuration** - Easy to create multiple scenarios
   ```python
   sim = Simulation(rate=1, delay=0.1)
   ```

5. **Multiple simulations possible** - Each Simulation instance is independent
   ```python
   # Can create sim1, sim2, sim3 with different parameters
   ```

### Zurvan Mapping:
- **Simulation class = Zurvan scenario**
- **`__init__()` = Graph construction** (Layer 1: Structural)
- **`env.process()` = Scenario activation** (Layer 2: Temporal)
- **Parameters = Scenario configuration**
- **Multiple instances = Different scenarios** running in parallel

**This is exactly Zurvan's scenario design pattern!**

---

## Pattern 2b: Visualization Integration (Pygame)

**File**: `sim_2b-viz.py`

### Key Ideas:

1. **Separate visualizer class** - Decoupled from simulation logic
   ```python
   class PygameVisualizer:
       def __init__(self, simulation):
           self.simulation = simulation
   ```

2. **Dynamic agent positioning** - Calculate layout from graph structure
   ```python
   radius = min(self.WIDTH, self.HEIGHT)/2*0.8
   n_agents = len(self.agents)
   for i, agent in enumerate(self.agents):
       angle = i/n_agents*2*math.pi
       agent.x = math.cos(angle)*radius + self.WIDTH / 2
       agent.y = math.sin(angle)*radius + self.HEIGHT / 2
   ```

3. **Visual state representation** - Agent color based on state
   ```python
   pygame.draw.circle(self.screen, to_color(agent.current_message), (agent.x, agent.y), ...)
   ```

4. **Connection visualization** - Draw graph edges
   ```python
   for agent in self.agents:
       for conn in agent.connections:
           pygame.draw.line(self.screen, ..., (agent.x, agent.y), (conn.x, conn.y), 2)
   ```

5. **Real-time simulation stepping**
   ```python
   def run(self):
       while running:
           self.simulation.env.run(until=self.simulation.env.now+0.1)
           self.draw()
           pygame.display.flip()
           self.clock.tick(30)
   ```

6. **Dynamic attributes** - Add visualization properties without modifying Agent class
   ```python
   agent.x = ...  # Added dynamically
   agent.y = ...  # Not in original Agent class
   ```

### Zurvan Mapping:
- **PygameVisualizer = Zurvan visualizer** (like our Streamlit/Folium app)
- **Dynamic positioning = GIS map layout**
- **Color by state = Node color coding** (idle/producing/adjusting)
- **Connection lines = Graph edge visualization**
- **Real-time stepping = Live simulation updates**
- **Dynamic attributes = Separation of visualization from core model**

---

## Key Patterns Applicable to Zurvan

### 1. **Agent-as-Resource Node**
```python
class Agent:
    def __init__(self, env, name):
        self.env = env           # Simulation environment
        self.name = name         # Node ID
        self.connections = []    # Graph edges
        self.current_message = None  # Node state
```

**Zurvan equivalent**:
```python
class ResourceNode:
    def __init__(self, env, node_id, node_type):
        self.env = env
        self.node_id = node_id
        self.node_type = node_type
        self.connections = []     # Edges to other nodes
        self.state = {}           # State properties (from graph DB)
```

---

### 2. **Actions as Generator Functions**
```python
def send_periodic_messages(agent):
    counter = 0
    while True:
        yield env.timeout(random.expovariate(RATE))  # Time constraint
        agent.send_to_connected(counter, DELAY)      # Use resources
        counter += 1                                 # Update state
```

**Zurvan equivalent**:
```python
def manufacture_product(manufacturing_center, rate):
    """Atomic action: continuous production"""
    while True:
        yield env.timeout(1.0 / rate)  # Time constraint
        manufacturing_center.state['inventory'] += 1  # State update
```

---

### 3. **Message Passing = Resource Usage**
```python
def send_to_connected(self, message, delay=0):
    def send_event():
        yield env.timeout(delay)        # Time to send
        for other in self.connections:  # Resources (other agents)
            other.receive(message)      # State update
    env.process(send_event())
```

**Zurvan equivalent**:
```python
def fulfill_order(order, manufacturing_center, delay=0):
    """Atomic action: fulfill order from inventory"""
    yield env.timeout(delay)
    if manufacturing_center.state['inventory'] >= order.quantity:
        manufacturing_center.state['inventory'] -= order.quantity
        order.state['status'] = 'fulfilled'
        order.state['fulfillment_time'] = env.now
```

---

### 4. **Simulation Class = Scenario**
```python
class Simulation:
    def __init__(self, rate, delay):
        # Layer 1: Build graph structure
        self.env = simpy.RealtimeEnvironment()
        self.agent_1 = Agent(self.env, "Abby")
        self.agent_2 = Agent(self.env, "Burt")
        self.agent_1.connections.append(self.agent_2)

        # Layer 2: Activate processes (temporal layer)
        self.env.process(self.send_periodic_messages(self.agent_1))
```

**Zurvan equivalent**:
```python
class ProductDeliveryScenario:
    def __init__(self, graph, policy):
        # Layer 1: Use existing graph structure
        self.env = simpy.RealtimeEnvironment()
        self.graph = graph
        self.policy = policy

        # Layer 2: Activate processes
        for center_id in graph.get_nodes_by_type('manufacturing_center'):
            center = graph.get_node(center_id)
            self.env.process(self.continuous_production(center))

        for dist_id in graph.get_nodes_by_type('distributor'):
            dist = graph.get_node(dist_id)
            self.env.process(self.generate_orders(dist))
```

---

### 5. **Visualizer = Separate Concern**
```python
class PygameVisualizer:
    def __init__(self, simulation):
        self.simulation = simulation
        # Add visualization attributes dynamically
        for agent in self.agents:
            agent.x = calculate_position()
            agent.y = calculate_position()

    def run(self):
        while running:
            self.simulation.env.run(until=env.now+0.1)  # Step simulation
            self.draw()                                  # Update display
```

**Zurvan equivalent**: Our Streamlit visualizer exactly follows this pattern!

---

## Progressive Complexity Levels

| Level | Pattern | Key Feature | Best For |
|-------|---------|-------------|----------|
| 0a | Functional | Simple, no objects | Prototyping, learning |
| 0b | Functional + Metrics | State tracking | Adding analytics |
| 1 | Agent class | Encapsulation, reusability | Building blocks |
| 2a | Simulation class | Scenario management | Multiple scenarios |
| 2b | + Visualization | Real-time display | Demonstration, debugging |

---

## Recommended Approach for Zurvan Demo

### Use Pattern 2a + 2b hybrid:

1. **Build on existing graph structure** (Step 1 complete)
2. **Add SimPy environment** to nodes
3. **Implement actions as generator functions**
4. **Create Simulation class** for scenarios
5. **Integrate with Streamlit visualizer** (already built)

### Advantages:
- ✅ Clean separation: Graph (Layer 1) + SimPy (Layer 2)
- ✅ Reusable Agent/Node pattern
- ✅ Easy scenario comparison
- ✅ Real-time visualization already working
- ✅ Demonstrates Zurvan concepts clearly

---

## Code Structure Proposal

```
src/
├── graph_builder.py          # Layer 1: Structural (existing)
├── state_manager.py          # State management with SimPy
├── resource_node.py          # Agent-like resource nodes
├── actions/
│   ├── manufacturing_actions.py  # Generator functions for actions
│   └── order_actions.py
├── simulation.py             # Simulation class (Pattern 2a)
└── visualizer.py            # Streamlit + real-time updates (existing)
```

---

## Next Steps for Implementation

1. **Add SimPy to requirements.txt**
2. **Create ResourceNode class** (based on Agent pattern)
3. **Implement actions as generators** (manufacturing, orders, fulfillment)
4. **Build Simulation class** (scenario wrapper)
5. **Integrate with Streamlit** for real-time visualization
6. **Add policy/intention nodes** for control strategies

This approach uses SimPy's proven patterns while demonstrating Zurvan's unique architecture!
