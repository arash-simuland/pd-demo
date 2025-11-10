# Realistic Cost Model for Product Delivery Demo

## Product Type: Industrial Equipment Components

Based on the simulation parameters, this models **industrial equipment components** (motors, pumps, control units) used in manufacturing.

**Why this makes sense:**
- Order sizes: 40-60 units (typical B2B order quantities)
- Regional distribution: Industrial distributors serving manufacturing hubs
- Production capacity: 200 units/hour suggests automated assembly lines
- 48-hour SLA: Standard for industrial just-in-time delivery

---

## Demand Analysis

### Expected Daily Demand
- **8 distributors** with average order probability ~35%/day
- **Average order size**: ~50 units
- **Expected daily orders**: 8 × 0.35 = 2.8 orders/day
- **Expected daily demand**: 2.8 × 50 = **~140 units/day**

### Production Capacity
- **3 manufacturing centers**
- **Max production rate**: 5.0 units/hour per center
- **Typical sustainable rate**: 2.5 units/hour per center
- **Daily capacity at max rate**: 3 centers × 5 units/hr × 24 hrs = **360 units/day**
- **Daily capacity at typical rate**: 3 centers × 2.5 units/hr × 24 hrs = **180 units/day**

**Key insight**: Production capacity is constrained at 2.5× demand (at max rate) or 1.3× demand (at typical rate). The challenge is **dynamic capacity allocation** - which centers should run at what rates to balance costs, inventory, and service levels across the network.

---

## Cost Structure

### 1. Holding Costs (Inventory Carrying Costs)

**Unit value**: $500/component (industrial motor/pump)

**Annual holding cost rate**: 25% (industry standard includes):
- Warehouse space: 6%
- Insurance: 2%
- Obsolescence risk: 5%
- Damaged/spoilage: 2%
- Tied-up capital (opportunity cost): 10%

**Daily holding cost per unit**: $500 × 25% ÷ 365 days = **$0.34/unit/day**

**Typical inventory levels**:
- Starting inventory: 500 units/center × 3 = 1,500 units
- Daily holding cost at start: 1,500 × $0.34 = **$510/day**

### 2. Production Costs (Machine Operating Costs)

**Fixed operating cost** (when machine is running):
- Labor: $25/hour (operator)
- Energy: $15/hour (automated line power)
- Consumables: $10/hour (lubricants, tooling wear)
- **Total**: **$50/hour per center**

**Daily fixed cost** (continuous operation):
- 3 centers × $50/hr × 24 hrs = **$3,600/day**

### 3. Rate Change Costs (Setup/Changeover Costs)

**Cost per rate change**:
- Labor (2 hours × 2 technicians × $40/hr): $160
- Quality inspection: $80
- Recalibration: $60
- Production loss during transition: $100
- **Total**: **$400 per rate change**

**Typical scenario**:
- Aggressive policy: 3 rate changes/day → $1,200/day
- Stable policy: 1 rate change/week → $57/day

---

## Economic Scenarios

### Scenario A: Max Production (High Inventory)

**Policy**: Run all 3 centers at max rate (5 units/hour) continuously
- **Production**: 360 units/day
- **Demand**: ~140 units/day
- **Inventory accumulation**: +220 units/day

**Daily costs**:
- Holding cost (assuming avg 1,500 units): 1,500 × $0.34 = $510/day
- Production cost: $3,600/day
- Rate changes: $0/day (no changes)
- **Total**: **$4,110/day**

**Problem**: Inventory grows continuously → storage costs increase over time

### Scenario B: Just-in-Time Production (Minimal Inventory)

**Policy**: Match production to demand (~2 units/hour per center)
- **Production**: ~144 units/day (3 centers × 2 units/hr × 24 hrs)
- **Demand**: ~140 units/day
- **Inventory**: Stays near 300 units/center (900 total)

**Daily costs**:
- Holding cost: 900 × $0.34 = $306/day
- Production cost: $3,600/day (machines still manned, just slower)
- Rate changes: $400/day (frequent adjustments to match demand)
- **Total**: **$4,306/day**

**Problem**: Frequent rate changes, risk of stockouts during demand surges

### Scenario C: Buffer Inventory Strategy (Balanced)

**Policy**: Maintain 400-500 units/center (2-3 day buffer), adjust production smoothly
- **Production**: Adjust slowly to maintain buffer (avg ~2.5 units/hour per center)
- **Demand**: ~140 units/day
- **Inventory**: Maintains 1,350 units average (450 per center)

**Daily costs**:
- Holding cost: 1,350 × $0.34 = $459/day
- Production cost: $3,600/day
- Rate changes: $114/day (2 changes/week)
- **Total**: **$4,173/day**

**Benefits**: Good responsiveness, fewer rate changes, stable costs, sustainable inventory levels

---

## Cost Comparison Summary

| Policy | Holding | Production | Rate Changes | **Total/Day** | Trade-offs |
|--------|---------|------------|--------------|---------------|------------|
| **Max Production** | $510+ | $3,600 | $0 | **$4,110+** | Inventory grows continuously |
| **Just-in-Time** | $306 | $3,600 | $400 | **$4,306** | Stockout risk, high variability |
| **Buffer Strategy** | $459 | $3,600 | $114 | **$4,173** | **Best balance** |

**Key finding**: Optimal buffer strategy is 3.2% more costly than max production initially, but avoids unbounded inventory growth. JIT is 3.2% more expensive than buffer strategy due to frequent rate changes.

---

## Implementation Parameters

### Configuration Values (for `data/cost-parameters.json`)

```json
{
  "holding_cost": {
    "unit_value": 500.0,
    "annual_holding_rate": 0.25,
    "daily_cost_per_unit": 0.34
  },
  "production_cost": {
    "hourly_operating_cost": 50.0,
    "daily_fixed_cost": 3600.0
  },
  "rate_change_cost": {
    "per_change": 400.0,
    "time_hours": 2.0
  },
  "product_info": {
    "type": "Industrial Equipment Component",
    "description": "Motors, pumps, control units for manufacturing",
    "typical_order_size": 50,
    "expected_daily_demand": 140
  }
}
```

---

## Visualization Metrics

### Real-time Cost Dashboard
- **Current inventory value**: `inventory × $500`
- **Daily holding cost**: `inventory × $0.34`
- **Daily production cost**: `$3,600` (constant)
- **Rate change cost**: `num_changes × $400`
- **Total daily cost**: Sum of above

### Policy Comparison View
- **Baseline cost**: $4,173/day (buffer strategy)
- **Current cost**: Real-time calculation
- **Cost delta**: `current - baseline`
- **Cost delta %**: `(current - baseline) / baseline × 100%`
- **Color coding**:
  - Green: < -5% (better than baseline)
  - Yellow: ±5% (comparable)
  - Red: > +5% (worse than baseline)

### Cost History Graph
- Line chart showing daily costs over simulation time
- Separate lines for: holding, production, rate changes, total
- Shaded regions showing optimal range

---

## Success Criteria

### Cost Efficiency Goals
- **Primary**: Total daily cost within 10% of optimal (~$4,173/day)
- **Secondary**: Minimize cost variance (stable costs preferred)
- **Tertiary**: Balance cost efficiency with service quality (fulfillment times)

### Trade-off Analysis
Good policies must balance:
1. **Low holding costs** → Keep inventory low
2. **Low rate change costs** → Avoid frequent adjustments
3. **Good service** → Meet 48-hour SLA (Step 8 metrics)

**This demonstrates Zurvan's multi-objective optimization capabilities.**
