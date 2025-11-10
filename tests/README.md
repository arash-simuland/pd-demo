# Product Delivery Demo - Test Suite

This directory contains test scenarios for validating the product delivery simulation model.

## Overview

The test suite ensures the simulation model works correctly by validating:
- Production output matches expected calculations
- Inventory accounting is accurate
- Order generation follows probabilistic rules
- Order fulfillment operates correctly
- No simulation crashes or errors occur

## Test Files

### test_10hour_scenario.py

**Purpose**: Validates a 10-hour deterministic simulation with known expected outcomes.

**What it tests**:
1. **Production Validation**: Verifies each manufacturing center produces the correct amount based on `rate × time`
2. **Inventory Validation**: Confirms inventory accounting: `Initial + Produced - Fulfilled = Final`
3. **Fulfillment Validation**: Checks orders are fulfilled correctly and metrics are accurate

**Expected Outcomes** (10-hour simulation):

| Center | Production Rate | Expected Production | Initial Inventory |
|--------|----------------|---------------------|-------------------|
| Chicago | 100 units/hr | 1000 units | 500 units |
| Pittsburgh | 50 units/hr | 500 units | 500 units |
| Nashville | 25 units/hr | 250 units | 500 units |
| **Total** | - | **1750 units** | **1500 units** |

**Order Generation**:
- Distributors check every 2 hours (5 checks in 10 hours)
- Orders placed probabilistically based on day-of-week probabilities
- Expected: ~11-12 orders total (Monday probabilities)

**Initial Conditions**:
- Fixed random seed (42) for reproducibility
- Simulation starts at t=0 (Monday)
- All production rates set to design specifications

## Running Tests

### Run all tests:
```bash
py -m pytest tests/
```

### Run specific test:
```bash
py tests/test_10hour_scenario.py
```

### Run with verbose output:
```bash
py tests/test_10hour_scenario.py -v
```

## Test Methodology

### Deterministic Testing
- Uses fixed random seed (`seed=42`) for reproducibility
- Same test run produces identical results every time
- Enables precise validation of expected vs actual outcomes

### Validation Approach
1. **Calculate Expected**: Compute theoretical outcomes based on rates, probabilities, and time
2. **Run Simulation**: Execute simulation with known initial conditions
3. **Compare Results**: Validate actual outcomes match expected (within tolerance)

### Tolerance Levels
- Production: ±1 unit (accounts for floating-point precision)
- Inventory: ±1 unit (same as production)
- All other metrics: Exact match required

## Bugs Found and Fixed

### Bug #1: Swapped Production Rates
**Issue**: Pittsburgh and Nashville had reversed production rates

**Location**: `src/resource_node.py:59-64`

**Symptoms**:
- Pittsburgh produced 250 units (expected 500)
- Nashville produced 500 units (expected 250)

**Fix**: Corrected the initial_rates dictionary:
```python
# BEFORE (WRONG)
initial_rates = {
    'chicago_center': 100,
    'nashville_center': 50,    # Should be 25
    'pittsburgh_center': 25    # Should be 50
}

# AFTER (CORRECT)
initial_rates = {
    'chicago_center': 100,
    'pittsburgh_center': 50,   # Fixed
    'nashville_center': 25     # Fixed
}
```

### Bug #2: Production Timing Issue
**Issue**: Only 9 production cycles occurred instead of 10 in a 10-hour simulation

**Location**: `src/actions/manufacturing_actions.py:28-46` and `test_10hour_scenario.py:146`

**Root Cause**: SimPy `run(until=10)` stops AT t=10, not AFTER processing events at t=10. The production event scheduled for t=10.0 was never executed.

**Physical Correctness**: Production happens at the END of each hour:
- Machine works DURING hour 0→1
- Production completes AT t=1.0
- This pattern continues: work during each hour, produce at end

**Solution**: Run simulation slightly past t=10 to ensure the production event at t=10.0 is processed:

```python
# In test_10hour_scenario.py
def run_simulation(self, duration_hours=10):
    # Run slightly past 10 hours to capture final production at t=10
    self.simulation.env.run(until=duration_hours + 0.01)
```

**Timeline**:
```
t=0.0: Start, begin work
t=1.0: Produce batch #1, begin work
t=2.0: Produce batch #2, begin work
...
t=9.0: Produce batch #9, begin work
t=10.0: Produce batch #10  ← This event is captured by running until=10.01
```

## Test Results

When all tests pass, you should see:
```
============================================================
TEST SUMMARY
============================================================
[PASS] ALL TESTS PASSED
============================================================
```

Exit code: 0 (success)

### Example Output:
```
============================================================
EXPECTED PRODUCTION (10 hours)
============================================================
chicago_center:
  Production: 1000 units
  Inventory range: 500 - 1500 units
pittsburgh_center:
  Production: 500 units
  Inventory range: 500 - 1000 units
nashville_center:
  Production: 250 units
  Inventory range: 500 - 750 units

Total expected production: 1750 units
============================================================

============================================================
VALIDATION RESULTS
============================================================

1. PRODUCTION VALIDATION:
  Chicago Manufacturing Center:
    Expected: 1000 units
    Actual: 1000 units
    Status: [PASS]

  Pittsburgh Manufacturing Center:
    Expected: 500 units
    Actual: 500 units
    Status: [PASS]

  Nashville Manufacturing Center:
    Expected: 250 units
    Actual: 250 units
    Status: [PASS]

  Total Production:
    Expected: 1750 units
    Actual: 1750 units

2. INVENTORY VALIDATION:
  [All centers show correct accounting]

3. FULFILLMENT VALIDATION:
  Orders fulfilled: 10
  Orders pending: 5
```

## Adding New Tests

To add new test scenarios:

1. Create new test file in `tests/` directory
2. Follow the pattern in `test_10hour_scenario.py`:
   - Use fixed random seed for reproducibility
   - Calculate expected outcomes
   - Run simulation
   - Validate results
3. Document expected outcomes and validation criteria
4. Update this README with test description

## Best Practices

1. **Always use fixed random seeds** for deterministic tests
2. **Calculate expected outcomes** before running simulation
3. **Document assumptions** and initial conditions clearly
4. **Use meaningful tolerances** (±1 for floating-point issues)
5. **Validate all state changes** (production, inventory, orders, fulfillment)
6. **Print clear output** showing expected vs actual values
7. **Return proper exit codes** (0 for success, 1 for failure)

## Integration with Development Workflow

These tests should be run:
- Before committing code changes
- After fixing bugs
- When adding new features
- As part of continuous integration (CI)

## Contact and Support

For issues or questions about tests, refer to the main project documentation or open an issue in the repository.
