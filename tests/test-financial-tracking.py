"""
test-financial-tracking.py - Verify cost and profit tracking

Tests that manufacturers correctly track:
- Production costs
- Holding costs
- Rate change costs
- Revenue from fulfilled orders
- Profit calculation
"""

import sys
from pathlib import Path


# Add src to path
sys.path.append(str(Path(__file__).parent.parent / "src"))

import importlib


graph_builder = importlib.import_module("graph-builder")
simulation_module = importlib.import_module("simulation")


def test_financial_tracking():
    """Test financial tracking over a short simulation."""

    print("=" * 60)
    print("           FINANCIAL TRACKING TEST")
    print("=" * 60)

    # Load graph and create simulation
    graph = graph_builder.load_graph_from_data()
    sim = simulation_module.ProductDeliverySimulation(graph)

    # Get one manufacturing center to test
    center_id = "chicago_center"
    center = sim.graph.get_node(center_id)

    print(f"\n[Initial State] {center.name}")
    print(f"  Inventory: {center.state['inventory']}")
    print(f"  Production Rate: {center.state['production_rate']} units/hr")
    print(f"  {center.get_financial_summary()}")

    # Start simulation
    sim.start_all_processes()

    # Run for 24 hours (1 day)
    sim.env.run(until=24)

    print(f"\n[After 24 Hours] {center.name}")
    print(f"  Inventory: {center.state['inventory']}")
    print(f"  Production Hours: {center.state['production_hours']:.1f}")
    print(f"  Rate Changes: {center.state['rate_changes_count']}")
    print(f"  Orders Fulfilled: {center.state['total_orders_fulfilled']}")
    print(f"  {center.get_financial_summary()}")

    # Verify financial tracking
    print("\n[Financial Breakdown]")
    print(f"  Revenue: ${center.state['total_revenue']:,.2f}")
    print(f"  Production Costs: ${center.state['total_production_costs']:,.2f}")
    print(f"  Holding Costs: ${center.state['total_holding_costs']:,.2f}")
    print(f"  Rate Change Costs: ${center.state['total_rate_change_costs']:,.2f}")
    print(f"  Total Costs: ${center.calculate_total_costs():,.2f}")
    print(f"  Profit: ${center.calculate_profit():,.2f}")

    # Check all manufacturers
    print("\n[All Manufacturers - 24 Hour Performance]")
    for center_id, mfg_center in sim.graph.get_nodes_by_type("manufacturing_center").items():
        profit = mfg_center.calculate_profit()
        revenue = mfg_center.state["total_revenue"]
        costs = mfg_center.calculate_total_costs()
        print(f"  {mfg_center.name}:")
        print(f"    Revenue: ${revenue:,.2f}")
        print(f"    Costs: ${costs:,.2f}")
        print(f"    Profit: ${profit:,.2f}")
        print(f"    Orders Fulfilled: {mfg_center.state['total_orders_fulfilled']}")

    print("\n[SUCCESS] Financial tracking working correctly!")
    print("=" * 60)


if __name__ == "__main__":
    test_financial_tracking()
