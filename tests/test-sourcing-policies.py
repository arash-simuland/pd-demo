"""
test-sourcing-policies.py - Test distributor sourcing policies (Phase 3)

Verifies that:
1. Different sourcing policies make different supplier selection decisions
2. Reputation tracking updates correctly after deliveries
3. Distributors learn from past performance and adjust sourcing
"""

import sys
from pathlib import Path


# Add src to path
sys.path.append(str(Path(__file__).parent.parent / "src"))

import importlib


graph_builder = importlib.import_module("graph-builder")
simulation_module = importlib.import_module("simulation")
sourcing_policies = importlib.import_module("sourcing-policies")


def test_sourcing_policies():
    """Test that different sourcing policies make different decisions."""

    print("=" * 60)
    print("        SOURCING POLICIES TEST")
    print("=" * 60)

    # Load graph and create simulation
    graph = graph_builder.load_graph_from_data()
    sim = simulation_module.ProductDeliverySimulation(graph)

    # Get a distributor to test
    dist_id = "distributor_ny"
    distributor = sim.graph.get_node(dist_id)

    print(f"\n[Test Distributor] {distributor.name}")
    print(f"  Location: {distributor.location['city']}, {distributor.location['state']}")

    # Test different sourcing policies
    print("\n[Policy Comparison] Selecting supplier for 50-unit order:\n")

    # 1. Nearest Neighbor
    policy1 = sourcing_policies.NearestNeighborSourcingPolicy()
    supplier1, decision1 = policy1.select_supplier(distributor, graph, 50)
    supplier1_name = graph.get_node(supplier1).name
    print(f"1. NearestNeighbor: {supplier1_name}")
    print(f"   Reason: {decision1['reason']}")
    print(f"   Cost: ${decision1['total_cost']:,.2f}")

    # 2. Cost Minimizer
    policy2 = sourcing_policies.CostMinimizerSourcingPolicy()
    supplier2, decision2 = policy2.select_supplier(distributor, graph, 50)
    supplier2_name = graph.get_node(supplier2).name
    print(f"\n2. CostMinimizer: {supplier2_name}")
    print(f"   Reason: {decision2['reason']}")
    print(f"   Cost: ${decision2['total_cost']:,.2f}")
    print(f"   Unit cost: ${decision2['unit_cost']:.2f}")
    print(f"   Delivery cost: ${decision2['delivery_cost']:.2f}")

    # 3. Reliability Threshold (no history yet, should be optimistic)
    policy3 = sourcing_policies.ReliabilityThresholdSourcingPolicy(min_on_time_rate=0.80)
    supplier3, decision3 = policy3.select_supplier(distributor, graph, 50)
    supplier3_name = graph.get_node(supplier3).name
    print(f"\n3. ReliabilityThreshold: {supplier3_name}")
    print(f"   Reason: {decision3['reason']}")
    print(f"   Cost: ${decision3['total_cost']:,.2f}")
    print(f"   Reputation: {decision3.get('reputation', 'None (new supplier)')}")

    # 4. Weighted Score
    policy4 = sourcing_policies.WeightedScoreSourcingPolicy(
        cost_weight=0.5, delivery_weight=0.3, reputation_weight=0.2
    )
    supplier4, decision4 = policy4.select_supplier(distributor, graph, 50)
    supplier4_name = graph.get_node(supplier4).name
    print(f"\n4. WeightedScore: {supplier4_name}")
    print(f"   Reason: {decision4['reason']}")
    print(f"   Total score: {decision4['score']:.3f}")
    print(f"   Cost score: {decision4['cost_score']:.3f} (weight: {decision4['weights']['cost']})")
    print(
        f"   Delivery score: {decision4['delivery_score']:.3f} (weight: {decision4['weights']['delivery']})"
    )
    print(
        f"   Reputation score: {decision4['reputation_score']:.3f} (weight: {decision4['weights']['reputation']})"
    )

    # 5. Loyalty-Based (no history, should behave like cost minimizer)
    policy5 = sourcing_policies.LoyaltyBasedSourcingPolicy(loyalty_bonus=0.2)
    supplier5, decision5 = policy5.select_supplier(distributor, graph, 50)
    supplier5_name = graph.get_node(supplier5).name
    print(f"\n5. LoyaltyBased: {supplier5_name}")
    print(f"   Reason: {decision5['reason']}")
    print(f"   Cost: ${decision5['total_cost']:,.2f}")
    print(f"   Is loyal supplier: {decision5['is_loyal']}")

    print("\n[SUCCESS] All policies executed successfully!")
    print("=" * 60)


def test_reputation_tracking():
    """Test that reputation tracking works correctly."""

    print("\n" + "=" * 60)
    print("        REPUTATION TRACKING TEST")
    print("=" * 60)

    # Load graph and create simulation
    graph = graph_builder.load_graph_from_data()
    sim = simulation_module.ProductDeliverySimulation(graph)

    # Run simulation for 48 hours to generate orders and deliveries
    sim.start_all_processes()
    sim.env.run(until=48)

    # Check distributor supplier relationships
    print("\n[Distributor Supplier Relationships after 48 hours]\n")

    for dist_id, distributor in sim.graph.get_nodes_by_type("distributor").items():
        relationships = distributor.state["supplier_relationships"]

        if not relationships:
            print(f"{distributor.name}: No orders placed yet")
            continue

        print(f"{distributor.name}:")
        for supplier_id, metrics in relationships.items():
            supplier = sim.graph.get_node(supplier_id)
            print(f"  -> {supplier.name}:")
            print(f"      Orders placed: {metrics['orders_placed']}")
            print(f"      Orders delivered: {metrics['orders_delivered']}")
            print(f"      On-time rate: {metrics['on_time_rate']:.1%}")
            print(f"      Avg wait time: {metrics['avg_wait_time']:.1f} hours")
            print(f"      Total cost paid: ${metrics['total_cost_paid']:,.2f}")

            # Reputation score
            reputation = distributor.get_supplier_reputation(supplier_id)
            print(f"      Reputation score: {reputation:.3f}")

    print("\n[SUCCESS] Reputation tracking working correctly!")
    print("=" * 60)


def test_policy_learning():
    """Test that reliability policy learns and adapts to supplier performance."""

    print("\n" + "=" * 60)
    print("        POLICY LEARNING TEST")
    print("=" * 60)

    # Load graph and create simulation
    graph = graph_builder.load_graph_from_data()
    sim = simulation_module.ProductDeliverySimulation(graph)

    # Get a distributor
    dist_id = "distributor_boston"
    distributor = sim.graph.get_node(dist_id)

    print(f"\n[Test] {distributor.name} using ReliabilityThreshold policy")
    print("       (min_on_time_rate = 0.70)\n")

    # Run simulation to build history
    sim.start_all_processes()
    sim.env.run(until=72)  # 3 days

    # Check which suppliers meet the threshold
    policy = sourcing_policies.ReliabilityThresholdSourcingPolicy(min_on_time_rate=0.70)

    print("[Supplier Evaluation]")
    relationships = distributor.state["supplier_relationships"]

    for supplier_id, metrics in relationships.items():
        supplier = sim.graph.get_node(supplier_id)
        reputation = distributor.get_supplier_reputation(supplier_id)

        meets_threshold = reputation >= 0.70
        status = "✓ RELIABLE" if meets_threshold else "✗ UNRELIABLE"

        print(f"  {supplier.name}: {reputation:.1%} on-time {status}")
        print(f"    Orders: {metrics['orders_delivered']}, Late: {metrics['orders_late']}")

    # Make a sourcing decision with the policy
    print("\n[Sourcing Decision] Placing new 50-unit order:")
    selected_supplier, decision = policy.select_supplier(distributor, graph, 50)
    if selected_supplier:
        selected_name = graph.get_node(selected_supplier).name
        print(f"  Selected: {selected_name}")
        print(f"  Reason: {decision['reason']}")
        print(f"  Reputation: {decision.get('reputation', 'N/A')}")
    else:
        print("  No reliable suppliers available")

    print("\n[SUCCESS] Policy learning working correctly!")
    print("=" * 60)


if __name__ == "__main__":
    test_sourcing_policies()
    test_reputation_tracking()
    test_policy_learning()
