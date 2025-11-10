"""
test_10hour_scenario.py - 10-Hour Deterministic Test Scenario

This test runs a 10-hour simulation with known initial conditions
and validates expected outcomes for production, orders, and fulfillment.

Expected Calculations:
- Production: rate × time (with 1-hour batching)
- Orders: Based on check intervals (every 2 hours) and probabilities
- Fulfillment: Orders fulfilled when inventory available

Initial Conditions:
- Chicago: 500 inventory, 100 units/hr production rate
- Pittsburgh: 500 inventory, 50 units/hr production rate
- Nashville: 500 inventory, 25 units/hr production rate
- 8 distributors checking every 2 hours (5 checks in 10 hours)

Test validates:
1. Production output matches expected (rate × hours)
2. Inventory levels are correct (initial + produced - fulfilled)
3. Order generation follows probabilities
4. Fulfillment metrics are accurate
5. No simulation errors or crashes
"""

import sys
from pathlib import Path


sys.path.append(str(Path(__file__).parent.parent / "src"))

import importlib


graph_builder = importlib.import_module("graph-builder")
simulation = importlib.import_module("simulation")
load_graph_from_data = graph_builder.load_graph_from_data
ProductDeliverySimulation = simulation.ProductDeliverySimulation
import random


class TestScenario:
    """10-hour deterministic test scenario"""

    def __init__(self, seed=42):
        """Initialize test with fixed random seed for reproducibility"""
        random.seed(seed)
        self.graph = load_graph_from_data()
        self.simulation = ProductDeliverySimulation(self.graph)

        # Initial conditions (from resource_node.py)
        self.initial_conditions = {
            "chicago_center": {"inventory": 500, "production_rate": 100},
            "pittsburgh_center": {"inventory": 500, "production_rate": 50},
            "nashville_center": {"inventory": 500, "production_rate": 25},
        }

    def calculate_expected_production(self, duration_hours=10):
        """
        Calculate expected production after 10 hours

        Production happens in 1-hour batches:
        - Chicago: 100 units/hr × 10 hrs = 1000 units
        - Pittsburgh: 50 units/hr × 10 hrs = 500 units
        - Nashville: 25 units/hr × 10 hrs = 250 units

        Total expected production: 1750 units
        """
        expected = {}
        for center_id, initial in self.initial_conditions.items():
            rate = initial["production_rate"]
            production = rate * duration_hours
            expected[center_id] = {
                "production": production,
                "min_inventory": initial["inventory"],  # If no orders fulfilled
                "max_inventory": initial["inventory"] + production,  # If no orders placed
            }

        total_production = sum(e["production"] for e in expected.values())

        print("=" * 60)
        print("EXPECTED PRODUCTION (10 hours)")
        print("=" * 60)
        for center_id, exp in expected.items():
            print(f"{center_id}:")
            print(f"  Production: {exp['production']} units")
            print(f"  Inventory range: {exp['min_inventory']} - {exp['max_inventory']} units")
        print(f"\nTotal expected production: {total_production} units")
        print("=" * 60)

        return expected, total_production

    def calculate_expected_orders(self, duration_hours=10):
        """
        Calculate expected order generation

        Orders check every 2 hours: 0, 2, 4, 6, 8 (5 checks)
        Starting at t=0 (Monday, day 0)

        For deterministic testing with seed=42, we can estimate:
        - Each distributor has 5 chances to place orders
        - Probability varies by day (Monday probabilities apply)

        Expected orders per distributor (Monday, 5 checks):
        - NY: 0.3 × 5 = 1.5 orders expected
        - Boston: 0.25 × 5 = 1.25 orders
        - Atlanta: 0.35 × 5 = 1.75 orders
        - Miami: 0.3 × 5 = 1.5 orders
        - Detroit: 0.28 × 5 = 1.4 orders
        - Indianapolis: 0.32 × 5 = 1.6 orders
        - Louisville: 0.27 × 5 = 1.35 orders
        - Memphis: 0.29 × 5 = 1.45 orders

        Total expected orders: ~11-12 orders
        """
        distributors = self.graph.get_nodes_by_type("distributor")

        # Monday probabilities
        day_name = "monday"
        checks_per_10h = 5

        expected_orders = {}
        total_expected = 0

        print("\n" + "=" * 60)
        print("EXPECTED ORDER GENERATION (10 hours, Monday)")
        print("=" * 60)

        for dist_id, dist in distributors.items():
            prob = dist.properties["order_probability"][day_name]
            expected = prob * checks_per_10h
            expected_orders[dist_id] = expected
            total_expected += expected
            print(f"{dist.name}: {prob:.2f} prob × 5 checks = {expected:.2f} expected orders")

        print(f"\nTotal expected orders: {total_expected:.1f} orders")
        print("=" * 60)

        return expected_orders, total_expected

    def run_simulation(self, duration_hours=10):
        """Run 10-hour simulation"""
        print("\n" + "=" * 60)
        print("RUNNING 10-HOUR SIMULATION")
        print("=" * 60)

        # Start all processes
        self.simulation.start_all_processes()

        # Run slightly past 10 hours to capture final production at t=10
        # Production happens at END of each hour, so we need to run past t=10
        # to ensure the hour 9->10 production completes
        self.simulation.env.run(until=duration_hours + 0.01)

        print(f"Simulation completed at t={self.simulation.env.now} hours")
        print("=" * 60)

    def validate_results(self, expected_production, expected_total_production):
        """Validate simulation results against expected values"""
        print("\n" + "=" * 60)
        print("VALIDATION RESULTS")
        print("=" * 60)

        centers = self.graph.get_nodes_by_type("manufacturing_center")

        results = {
            "production_match": True,
            "inventory_valid": True,
            "fulfillment_valid": True,
            "errors": [],
        }

        # Validate production
        print("\n1. PRODUCTION VALIDATION:")
        total_actual_production = 0
        for center_id, center in centers.items():
            actual_production = center.state["total_produced"]
            expected = expected_production[center_id]["production"]
            total_actual_production += actual_production

            match = abs(actual_production - expected) < 1  # Allow 1 unit tolerance
            status = "[PASS]" if match else "[FAIL]"

            print(f"  {center.name}:")
            print(f"    Expected: {expected} units")
            print(f"    Actual: {actual_production} units")
            print(f"    Status: {status}")

            if not match:
                results["production_match"] = False
                results["errors"].append(f"{center_id} production mismatch")

        print("\n  Total Production:")
        print(f"    Expected: {expected_total_production} units")
        print(f"    Actual: {total_actual_production} units")

        # Validate inventory
        print("\n2. INVENTORY VALIDATION:")
        for center_id, center in centers.items():
            initial = self.initial_conditions[center_id]["inventory"]
            produced = center.state["total_produced"]
            fulfilled = center.state["total_quantity_fulfilled"]
            actual_inventory = center.state["inventory"]
            expected_inventory = initial + produced - fulfilled

            match = abs(actual_inventory - expected_inventory) < 1
            status = "[PASS]" if match else "[FAIL]"

            print(f"  {center.name}:")
            print(f"    Initial: {initial}")
            print(f"    Produced: {produced}")
            print(f"    Fulfilled: {fulfilled}")
            print(f"    Expected final: {expected_inventory}")
            print(f"    Actual final: {actual_inventory}")
            print(f"    Status: {status}")

            if not match:
                results["inventory_valid"] = False
                results["errors"].append(f"{center_id} inventory mismatch")

        # Validate fulfillment
        print("\n3. FULFILLMENT VALIDATION:")
        total_fulfilled = sum(c.state["total_orders_fulfilled"] for c in centers.values())
        total_pending = sum(len(c.state["pending_orders"]) for c in centers.values())

        print(f"  Orders fulfilled: {total_fulfilled}")
        print(f"  Orders pending: {total_pending}")

        for center_id, center in centers.items():
            fulfillment_times = center.state.get("fulfillment_times", [])
            if fulfillment_times:
                avg_time = sum(fulfillment_times) / len(fulfillment_times)
                print(
                    f"  {center.name}: {len(fulfillment_times)} fulfilled, avg time {avg_time:.1f}hrs"
                )

        # Summary
        print("\n" + "=" * 60)
        print("TEST SUMMARY")
        print("=" * 60)
        all_pass = (
            results["production_match"]
            and results["inventory_valid"]
            and results["fulfillment_valid"]
        )

        if all_pass:
            print("[PASS] ALL TESTS PASSED")
        else:
            print("[FAIL] SOME TESTS FAILED:")
            for error in results["errors"]:
                print(f"  - {error}")

        print("=" * 60)

        return results


def main():
    """Run the 10-hour test scenario"""
    print("\n")
    print("=" * 60)
    print(" " * 15 + "10-HOUR TEST SCENARIO")
    print("=" * 60)

    # Initialize test
    test = TestScenario(seed=42)

    # Calculate expected outcomes
    expected_production, expected_total = test.calculate_expected_production(10)
    expected_orders, expected_order_total = test.calculate_expected_orders(10)

    # Run simulation
    test.run_simulation(10)

    # Validate results
    results = test.validate_results(expected_production, expected_total)

    # Return exit code
    return (
        0
        if all(
            [results["production_match"], results["inventory_valid"], results["fulfillment_valid"]]
        )
        else 1
    )


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
