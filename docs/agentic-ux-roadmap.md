# Agentic UX Roadmap

## Vision

Enable natural language control of the supply chain simulation through conversational AI. Users can manage the simulation, add nodes, adjust parameters, and query insights using plain English instead of manual controls.

---

## Phase A: Chat Interface & LLM Integration

### Frontend: Chat UI Component

**Location**: `frontend/src/components/chat-panel.js`

**Features**:
- Chat input field with send button
- Message history (user messages + AI responses)
- Typing indicators
- Auto-scroll to latest message
- Collapsible panel (can minimize to save screen space)

**UI Placement**:
- Bottom panel (dockable)
- Resize handle for height adjustment
- Can be toggled with button in control ribbon

**Styling**:
- Dark theme to match existing UI
- User messages: Right-aligned, blue background
- AI responses: Left-aligned, gray background
- Code/data blocks: Monospace font with syntax highlighting

### Backend: LLM Integration

**Location**: `backend/llm_agent.py`

**LLM Options**:
1. **Anthropic Claude** (Preferred)
   - Claude 3.5 Sonnet via API
   - Function calling for structured commands
   - Context window: 200K tokens

2. **OpenAI GPT-4** (Alternative)
   - GPT-4 Turbo via API
   - Function calling support
   - Context window: 128K tokens

3. **Local LLM** (Offline option)
   - Ollama with Llama 3 or Mistral
   - No API costs, runs locally
   - Smaller context window

**System Prompt**:
```
You are an AI assistant controlling a supply chain simulation. You have access to:

CURRENT STATE:
- Manufacturing centers: Chicago (IL), Pittsburgh (PA), Nashville (TN)
- Distributors: 8 locations across Eastern US
- Production rates, inventory levels, orders in flight

AVAILABLE COMMANDS:
1. Production control: shutdown, start, adjust rate
2. Node creation: add distributors, add manufacturers
3. Query state: show metrics, list nodes, show node details
4. Scenario analysis: what-if questions, optimization

Parse user requests and call appropriate functions.
Confirm actions before executing.
Provide clear feedback on results.
```

**API Endpoints**:
```python
POST /api/chat/message
{
  "message": "Shutdown Chicago production",
  "session_id": "uuid"
}

Response:
{
  "response": "Shutting down Chicago Manufacturing Center...",
  "action": {
    "type": "production_control",
    "target": "chicago_center",
    "command": "shutdown"
  },
  "confirmation_required": true
}

POST /api/chat/confirm
{
  "action_id": "uuid",
  "confirmed": true
}
```

---

## Phase B: Production Control Commands

### Command Types

#### 1. Shutdown Production
**User input**:
- "Shutdown Chicago production"
- "Stop Nashville manufacturing"
- "Turn off Pittsburgh"

**Action**:
```python
def shutdown_production(center_id: str):
    center = graph.get_node(center_id)
    center.state['production_rate'] = 0.0
    center.state['machine_state'] = 'shutdown'
    log_action(f"Production shutdown at {center.name}")
```

**Response**:
> ✅ Chicago Manufacturing Center production has been shut down. Current inventory: 287 units. Production rate: 0.0 units/hour.

#### 2. Increase/Decrease Production
**User input**:
- "Increase Nashville production to 15 units/hour"
- "Set Chicago production rate to 20"
- "Double Pittsburgh production"

**Action**:
```python
def set_production_rate(center_id: str, rate: float):
    center = graph.get_node(center_id)
    max_rate = center.properties['max_production_rate']

    if rate > max_rate:
        return f"Cannot set rate to {rate}. Maximum capacity is {max_rate} units/hour."

    center.state['production_rate'] = rate
    center.state['machine_state'] = 'producing'
    log_action(f"Production rate at {center.name} set to {rate} units/hour")
```

**Response**:
> ✅ Nashville Manufacturing Center production increased to 15.0 units/hour (was 10.0). Estimated daily output: 360 units.

#### 3. Resume Production
**User input**:
- "Resume all production"
- "Start Chicago back up"
- "Restore default production rates"

**Action**:
```python
def resume_production(center_id: str = None):
    if center_id:
        centers = [graph.get_node(center_id)]
    else:
        centers = graph.get_nodes_by_type('manufacturing_center').values()

    for center in centers:
        default_rate = center.properties['initial_production_rate']
        center.state['production_rate'] = default_rate
        center.state['machine_state'] = 'producing'
```

**Response**:
> ✅ Resumed production at all manufacturing centers:
> - Chicago: 10.0 units/hour
> - Pittsburgh: 14.0 units/hour
> - Nashville: 20.0 units/hour

### Real-Time Feedback

**Visual Updates**:
- Map nodes change color when production rate changes
- Node size adjusts with production rate
- Console shows action logs
- Sidebar metrics update immediately

**Chat Confirmations**:
- Show "Processing..." while executing
- Confirm action completed with metrics
- Show warnings if action conflicts with current state

---

## Phase C: Dynamic Node Creation

### Add Distributor

**User input**:
- "Add a distributor in Dallas, Texas"
- "Create new distributor in Miami with 60 unit average order size"
- "Add DC in Atlanta, Georgia"

**Action**:
```python
def add_distributor(city: str, state: str, params: dict = None):
    # Geocode city to get coordinates
    lat, lon = geocode(f"{city}, {state}")

    # Generate unique ID
    node_id = f"distributor_{city.lower()}"

    # Create node with default or custom parameters
    node_data = {
        "id": node_id,
        "type": "distributor",
        "name": f"{city} Distributor",
        "location": {"lat": lat, "lon": lon, "city": city, "state": state},
        "properties": {
            "order_probability": params.get("order_probability", DEFAULT_PROB),
            "order_size_mean": params.get("order_size_mean", 50),
            "order_size_std": params.get("order_size_std", 10),
            "actions": DEFAULT_DISTRIBUTOR_ACTIONS,
            "policies": DEFAULT_DISTRIBUTOR_POLICIES
        }
    }

    # Add to graph
    new_node = ResourceNode(env=simulation.env, **node_data)
    graph.add_node(node_id, new_node)

    # Connect to nearest manufacturing centers (calculate distances)
    add_edges_to_nearest_centers(new_node)

    # Start node processes
    new_node.start()

    return new_node
```

**Response**:
> ✅ Created Dallas Distributor at 32.78°N, 96.80°W
>
> **Properties**:
> - Average order size: 50 units
> - Order probability: 35% (weekdays)
> - Nearest manufacturer: Nashville (641 miles)
>
> **Status**: Active and generating orders
>
> The new distributor is now visible on the map.

### Add Manufacturing Center

**User input**:
- "Add manufacturing center in Atlanta with 500 capacity"
- "Create new factory in Columbus, Ohio"
- "Add manufacturer in Louisville, Kentucky producing 10 units/hour"

**Action**:
```python
def add_manufacturing_center(city: str, state: str, params: dict = None):
    lat, lon = geocode(f"{city}, {state}")
    node_id = f"{city.lower()}_center"

    node_data = {
        "id": node_id,
        "type": "manufacturing_center",
        "name": f"{city} Manufacturing Center",
        "location": {"lat": lat, "lon": lon, "city": city, "state": state},
        "properties": {
            "capacity": params.get("capacity", 1000),
            "initial_inventory": params.get("initial_inventory", 300),
            "initial_production_rate": params.get("production_rate", 10.0),
            "max_production_rate": params.get("max_rate", 20.0),
            "actions": DEFAULT_MANUFACTURER_ACTIONS,
            "policies": DEFAULT_MANUFACTURER_POLICIES
        }
    }

    new_node = ResourceNode(env=simulation.env, **node_data)
    graph.add_node(node_id, new_node)

    # Connect to all distributors (calculate distances)
    add_edges_to_all_distributors(new_node)

    # Start processes
    new_node.start()

    return new_node
```

**Response**:
> ✅ Created Atlanta Manufacturing Center at 33.75°N, 84.39°W
>
> **Capacity**: 1000 units
> **Production rate**: 10.0 units/hour (max 20.0)
> **Initial inventory**: 300 units
>
> **Connected to**:
> - Atlanta Distributor (0 miles)
> - Miami Distributor (662 miles)
> - Memphis Distributor (383 miles)
> - [+ 5 more]
>
> The new manufacturing center is now operational.

### Automatic Integration

**Graph updates**:
1. Calculate distances to existing nodes
2. Create edges with distance metadata
3. Add node to simulation graph
4. Initialize state variables
5. Start automatic processes (production, order processing)

**Visual updates**:
- New node appears on map immediately
- Edges shown to connected nodes
- Real-time state updates via WebSocket

---

## Phase D: Advanced Agentic Features

### 1. Scenario Analysis

**User input**:
- "What if we add 2 more distributors in the Southeast?"
- "How would costs change if we shutdown Chicago?"
- "Simulate adding Atlanta manufacturing for 24 hours"

**Action**:
```python
def run_scenario(description: str, duration_hours: float = 24):
    # Create simulation snapshot
    snapshot = simulation.save_state()

    # Parse scenario from description
    actions = llm_parse_scenario(description)

    # Apply scenario changes
    for action in actions:
        execute_action(action)

    # Run simulation
    results = simulation.run_for(duration_hours)

    # Compare metrics
    comparison = {
        "baseline": snapshot.metrics,
        "scenario": results.metrics,
        "delta": calculate_delta(snapshot.metrics, results.metrics)
    }

    # Restore original state
    simulation.restore_state(snapshot)

    return comparison
```

**Response**:
> 📊 **Scenario Results** (24-hour simulation)
>
> **Changes**: Added 2 distributors (Atlanta, Dallas)
>
> **Impact**:
> - Total orders: +28% (112 → 143 orders)
> - Total revenue: +$67,500 (+32%)
> - Avg fulfillment time: +2.3 hours (capacity strain)
> - Inventory turnover: +15%
>
> **Recommendation**: Additional distributors would benefit from 4th manufacturing center to maintain service levels.

### 2. Performance Analysis

**User input**:
- "Show me which manufacturer is most profitable"
- "Which distributor places the most orders?"
- "Compare production efficiency across all centers"

**Action**:
```python
def analyze_performance(metric: str, entity_type: str):
    nodes = graph.get_nodes_by_type(entity_type)

    results = []
    for node_id, node in nodes.items():
        value = calculate_metric(node, metric)
        results.append({
            "name": node.name,
            "value": value,
            "state": node.state
        })

    results.sort(key=lambda x: x['value'], reverse=True)
    return results
```

**Response**:
> 📈 **Manufacturer Profitability** (Last 24 hours)
>
> 1. **Nashville Manufacturing** - $42,850 profit
>    - Revenue: $187,500
>    - Costs: $144,650 (production, holding, delivery)
>    - Margin: 22.8%
>
> 2. **Pittsburgh Manufacturing** - $38,200 profit
>    - Revenue: $156,000
>    - Costs: $117,800
>    - Margin: 24.5%
>
> 3. **Chicago Manufacturing** - $31,100 profit
>    - Revenue: $143,500
>    - Costs: $112,400
>    - Margin: 21.7%
>
> **Insight**: Pittsburgh has highest margin but Nashville leads in total profit due to higher volume.

### 3. Optimization Suggestions

**User input**:
- "How can we reduce costs by 10%?"
- "Suggest ways to improve service levels"
- "Optimize production rates for maximum profit"

**Action**:
```python
def optimize_for(objective: str):
    # Run optimization algorithm
    current_state = simulation.get_state()

    if objective == "cost_reduction":
        suggestions = [
            {
                "action": "Reduce Chicago production to 8 units/hour",
                "impact": "Save $1,200/day in production costs",
                "risk": "Possible stockouts during peak demand"
            },
            {
                "action": "Consolidate low-volume distributors",
                "impact": "Save $800/day in delivery costs",
                "risk": "Longer delivery times to some regions"
            }
        ]

    return suggestions
```

**Response**:
> 💡 **Cost Reduction Recommendations**
>
> To achieve 10% cost reduction ($450/day):
>
> **Option 1**: Adjust production rates
> - Chicago: 10 → 8 units/hour (-$280/day)
> - Nashville: 20 → 18 units/hour (-$240/day)
> - **Total savings**: $520/day (11.6% reduction)
> - **Risk**: Medium - May cause stockouts during Friday peaks
>
> **Option 2**: Optimize inventory targets
> - Reduce target inventory from 400 to 300 units per center
> - **Savings**: $102/day in holding costs
> - **Plus**: Reduce production by 1 unit/hour system-wide (+$360/day)
> - **Total savings**: $462/day (10.3% reduction)
> - **Risk**: Low - Still maintains 2-day buffer
>
> **Recommendation**: Option 2 provides target savings with lower risk.

### 4. Natural Language Data Export

**User input**:
- "Export last 24 hours of data to CSV"
- "Generate a report of Nashville performance"
- "Download order history for Chicago"

**Action**:
```python
def export_data(query: str):
    # Parse export request
    time_range = llm_extract_time_range(query)
    entity = llm_extract_entity(query)
    format = llm_extract_format(query)

    # Query data
    data = simulation.get_historical_data(
        entity=entity,
        start_time=time_range.start,
        end_time=time_range.end
    )

    # Format and save
    filepath = f"exports/{entity}_{timestamp}.{format}"
    save_data(data, filepath, format)

    return filepath
```

**Response**:
> 📥 **Export Complete**
>
> **File**: `nashville_performance_2025-10-12.csv`
> **Records**: 1,440 (24 hours × 60 minutes)
> **Size**: 87 KB
>
> **Columns**:
> - timestamp, inventory, production_rate, orders_pending
> - orders_fulfilled, revenue, costs, profit_margin
>
> [Download File] button appears in chat

---

## Implementation Priority

### Phase A (Week 1-2): Foundation
- [ ] Chat UI component
- [ ] WebSocket chat endpoint
- [ ] LLM API integration
- [ ] Basic command parsing

### Phase B (Week 3): Production Control
- [ ] Shutdown command
- [ ] Rate adjustment command
- [ ] Resume command
- [ ] Real-time feedback

### Phase C (Week 4-5): Dynamic Nodes
- [ ] Add distributor command
- [ ] Add manufacturer command
- [ ] Geocoding integration
- [ ] Automatic graph updates

### Phase D (Week 6+): Advanced Features
- [ ] Scenario analysis
- [ ] Performance queries
- [ ] Optimization suggestions
- [ ] Data export

---

## Technical Requirements

### Frontend Dependencies
```json
{
  "dependencies": {
    "d3": "^7.8.5",
    "marked": "^4.0.0",  // Markdown rendering for responses
    "highlight.js": "^11.0.0"  // Code syntax highlighting
  }
}
```

### Backend Dependencies
```python
# requirements.txt additions
anthropic>=0.18.0  # Claude API
openai>=1.12.0     # GPT-4 API (alternative)
geopy>=2.3.0       # Geocoding for new nodes
python-dotenv>=1.0.0  # API key management
```

### Environment Variables
```bash
# .env
ANTHROPIC_API_KEY=sk-ant-...
OPENAI_API_KEY=sk-...
LLM_PROVIDER=anthropic  # or openai
```

---

## Success Metrics

**User Experience**:
- Command success rate > 95%
- Average response time < 2 seconds
- User satisfaction score > 4.5/5

**Functionality**:
- 100% coverage of production control commands
- Node creation success rate > 99%
- Scenario analysis accuracy > 90%

**Performance**:
- Chat latency < 1s (excluding LLM API)
- No impact on simulation performance
- WebSocket message rate: 10 fps maintained

---

## Future Enhancements

**Voice Control**:
- Add speech-to-text input
- Text-to-speech responses
- Hands-free operation

**Multi-User**:
- Shared simulation sessions
- Chat history per user
- Role-based access control

**Advanced AI**:
- Proactive suggestions ("Chicago inventory is low")
- Anomaly detection
- Predictive maintenance alerts

**Integration**:
- Connect to real ERP systems
- Import actual demand data
- Export to BI tools
