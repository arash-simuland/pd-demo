"""
order_actions.py - Step 3: Order Action Generators

SimPy generator functions for order-related actions.
These define how orders are generated, routed, and tracked.
"""

import random
import sys
from pathlib import Path


# Add src to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from order import Order


def check_and_generate_order(owner, resource, policy, time):
    """
    One-shot action: Check if an order should be generated and create it.

    Checks once if an order should be placed (based on day-of-week probability),
    and if yes, generates and routes the order using sourcing policy. Policy controls if/when to check again.

    Args:
        owner: ResourceNode executing the action (the distributor)
        resource: Required resource (ZurvanGraph to find suppliers)
        policy: PolicyNode that controls when/how often to execute
        time: Time (hours) to create/place an order

    Yields:
        SimPy timeout event for time

    State changes:
        - Increments 'orders_placed' (if order generated)
        - Increments 'total_order_quantity' (if order generated)
        - Records 'last_order_time' (if order generated)
        - Updates 'supplier_relationships' (Phase 3: tracks supplier performance)
    """
    # Determine day of week (0-6, where 0 = Monday)
    current_time = owner.env.now
    day_of_week = int(current_time / 24) % 7

    # Get order probability for this day
    order_probabilities = owner.properties.get("order_probability", {})
    day_names = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
    prob = order_probabilities.get(day_names[day_of_week], 0.5)

    # Decide if order is placed this check
    if random.random() < prob:
        # Time to generate the order
        yield owner.env.timeout(time)

        # Generate order size from normal distribution
        mean_size = owner.properties.get("order_size_mean", 50)
        std_size = owner.properties.get("order_size_std", 10)
        order_size = max(1, int(random.gauss(mean_size, std_size)))

        # Create order object
        order = Order(
            distributor_id=owner.node_id, quantity=order_size, placement_time=owner.env.now
        )

        # Select supplier using sourcing policy (Phase 3)
        # Get sourcing policy from distributor properties, or use nearest-neighbor as default
        import importlib

        sourcing_policies = importlib.import_module("sourcing-policies")

        sourcing_policy_config = owner.properties.get(
            "sourcing_policy", {"type": "nearest_neighbor"}
        )
        policy_type = sourcing_policy_config.get("type", "nearest_neighbor")
        policy_params = sourcing_policy_config.get("params", {})

        sourcing_policy = sourcing_policies.create_sourcing_policy(policy_type, **policy_params)

        # Use policy to select supplier (resource is the graph)
        selected_center_id, decision_info = sourcing_policy.select_supplier(
            owner, resource, order_size
        )

        if not selected_center_id:
            # No supplier available - shouldn't happen, but be defensive
            yield owner.env.timeout(time)
            return

        selected_center = resource.get_node(selected_center_id)

        # Calculate order pricing (Phase 2)
        pricing_info = resource.calculate_order_price(owner.node_id, selected_center_id, order_size)

        # Route order with pricing information
        distance = pricing_info["distance_miles"]
        order.route_to_center(selected_center_id, distance, pricing_info)

        # Record order placement for reputation tracking (Phase 3)
        owner.record_order_placement(selected_center_id, order)

        # Add order to center's pending queue
        selected_center.state["pending_orders"].append(order)

        # Update distributor state
        owner.state["orders_placed"] += 1
        owner.state["total_order_quantity"] += order_size
        owner.state["last_order_time"] = owner.env.now

        # Print order details with sourcing decision
        print(f"[Order] {order.id}: {owner.name} -> {selected_center.name}")
        print(f"  Quantity: {order_size} units | Distance: {distance:.1f} mi")
        print(
            f"  Price: ${pricing_info['total_order_price']:,.2f} (${pricing_info['base_unit_price']:.2f}/unit + ${pricing_info['delivery_cost_total']:.2f} delivery)"
        )
        print(f"  Est. delivery time: {pricing_info['delivery_time_hours']:.1f} hours")
        print(f"  Sourcing: {decision_info['policy']} - {decision_info['reason']}")
    else:
        # No order this time - just a quick check
        yield owner.env.timeout(time)


def route_order(distributor, graph, routing_time=0.01):
    """
    One-shot action: Route an order to nearest manufacturing center.

    Finds the nearest manufacturing center to the distributor based on
    geographic distance and creates a routing decision.

    Args:
        distributor: ResourceNode with distributor state
        graph: ZurvanGraph to find nearest center
        routing_time: Time (hours) for routing calculation (default 0.01)

    Yields:
        SimPy timeout event for routing_time

    Returns:
        Tuple of (center_id, distance) for the nearest center
    """
    # Routing calculation takes routing_time
    yield distributor.env.timeout(routing_time)

    # Find nearest center
    nearest_center, distance = graph.find_nearest_center(distributor.node_id)

    return nearest_center, distance


def track_order_fulfillment(distributor, order_id, fulfillment_time, tracking_time=0.001):
    """
    One-shot action: Track when an order is fulfilled.

    Updates distributor state when an order they placed is fulfilled
    by a manufacturing center.

    Args:
        distributor: ResourceNode with distributor state
        order_id: Identifier for the fulfilled order
        fulfillment_time: Time when order was fulfilled
        tracking_time: Time (hours) for state update (default 0.001)

    Yields:
        SimPy timeout event for tracking_time

    State changes:
        - Increments 'orders_fulfilled'
        - Increments 'total_fulfilled_quantity'
    """
    # State update takes tracking_time
    yield distributor.env.timeout(tracking_time)

    # Update fulfillment metrics
    distributor.state["orders_fulfilled"] += 1
    # Note: total_fulfilled_quantity would need order quantity passed in
    # Will implement fully in Step 8


# Backwards compatibility alias
# This allows old code/configs to still work
generate_orders = check_and_generate_order  # Alias for backwards compatibility


# Action metadata for visualization
ORDER_ACTIONS = {
    "generate_orders": {
        "name": "Generate Orders",
        "description": "Generate orders based on day-of-week probabilities",
        "type": "continuous",
        "parameters": ["graph"],
        "duration": "Every 24 hours",
        "state_changes": ["orders_placed", "total_order_quantity", "last_order_time"],
    },
    "route_order": {
        "name": "Route Order",
        "description": "Find nearest manufacturing center for order",
        "type": "atomic",
        "parameters": ["graph"],
        "duration": "0.01 hours (instant)",
        "state_changes": [],
    },
    "track_order_fulfillment": {
        "name": "Track Order Fulfillment",
        "description": "Update distributor state when order fulfilled",
        "type": "atomic",
        "parameters": ["order_id", "fulfillment_time"],
        "duration": "0.001 hours (instant)",
        "state_changes": ["orders_fulfilled", "total_fulfilled_quantity"],
    },
}
