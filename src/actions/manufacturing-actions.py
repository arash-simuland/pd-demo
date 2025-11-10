"""
manufacturing_actions.py - Step 3: Manufacturing Action Generators

SimPy generator functions for manufacturing center actions.
These are NOT executed yet - just definitions of what CAN happen.
"""


def produce_batch(owner, resource, policy, time):
    """
    One-shot action: Produce one batch of units.

    This action executes once - produces units based on current production rate
    over the specified time. Policy controls if/when to repeat.

    Args:
        owner: ResourceNode executing the action (the manufacturing center)
        resource: Required resources (machine, materials, etc.) - for future use
        policy: PolicyNode that controls when/how often to execute
        time: Time (hours) for this production cycle

    Yields:
        SimPy timeout event for time

    State changes:
        - Increments 'inventory' when producing
        - Increments 'total_produced'
        - Updates 'machine_state' based on production_rate
        - Increments 'total_production_costs' (Phase 2)
        - Updates 'production_hours' (Phase 2)
    """
    import json
    from pathlib import Path

    current_rate = owner.state.get("production_rate", 0)

    # Load cost parameters
    try:
        cost_params_path = Path(__file__).parent.parent.parent / "data" / "cost-parameters.json"
        with open(cost_params_path) as f:
            cost_params = json.load(f)

        # Get tiered cost structure
        cost_tiers = cost_params["production_costs"]["cost_per_unit_by_rate"]["tiers"]

        # Find applicable cost tier based on current production rate
        cost_per_unit = 10.0  # Default fallback
        for tier in cost_tiers:
            if tier["rate_min"] <= current_rate < tier["rate_max"]:
                cost_per_unit = tier["cost_per_unit"]
                break
    except:
        cost_per_unit = 10.0  # Default fallback

    if current_rate > 0:
        # Machine is producing
        owner.state["machine_state"] = "producing"

        # Work for time (machine operates during this time)
        yield owner.env.timeout(time)

        # Production completes at END of cycle
        units_produced = current_rate * time
        owner.state["inventory"] += units_produced
        owner.state["total_produced"] += units_produced

        # Track production costs (Phase 2: Competitive market)
        # Use tiered cost per unit based on production rate
        production_cost = units_produced * cost_per_unit
        owner.state["total_production_costs"] += production_cost
        owner.state["production_hours"] += time

    else:
        # Machine is idle
        owner.state["machine_state"] = "idle"
        yield owner.env.timeout(time)


def change_production_rate(manufacturing_center, new_rate, adjustment_time=2.0):
    """
    Composite action: Change production rate with adjustment delay.

    Changing production rate takes time (default 2 hours) because the machine
    needs to ramp up/down. During this time, machine_state = 'adjusting'.

    Args:
        manufacturing_center: ResourceNode with manufacturing center state
        new_rate: Target production rate (units per hour)
        adjustment_time: Time (hours) to complete rate change (default 2.0)

    Yields:
        SimPy timeout event for adjustment_time

    State changes:
        - Sets 'machine_state' to 'adjusting' during transition
        - Updates 'target_rate' immediately
        - Updates 'production_rate' after adjustment_time
        - Records 'last_rate_change_time'
        - Increments 'total_rate_change_costs' (Phase 2)
        - Increments 'rate_changes_count' (Phase 2)
    """
    import json
    from pathlib import Path

    # Load cost parameters
    try:
        cost_params_path = Path(__file__).parent.parent.parent / "data" / "cost-parameters.json"
        with open(cost_params_path) as f:
            cost_params = json.load(f)
        rate_change_cost = cost_params["rate_change_costs"]["cost_per_change"]
    except:
        rate_change_cost = 400.0  # Default fallback

    # Set target rate immediately
    manufacturing_center.state["target_rate"] = new_rate
    manufacturing_center.state["machine_state"] = "adjusting"

    # Wait for adjustment time (machine ramping up/down)
    yield manufacturing_center.env.timeout(adjustment_time)

    # Complete rate change
    manufacturing_center.state["production_rate"] = new_rate
    manufacturing_center.state["last_rate_change_time"] = manufacturing_center.env.now

    # Track rate change costs (Phase 2: Competitive market)
    manufacturing_center.state["total_rate_change_costs"] += rate_change_cost
    manufacturing_center.state["rate_changes_count"] += 1

    # Update machine state based on new rate
    if new_rate > 0:
        manufacturing_center.state["machine_state"] = "producing"
    else:
        manufacturing_center.state["machine_state"] = "idle"


def fulfill_order(manufacturing_center, order_quantity, fulfillment_time=0.1):
    """
    Atomic action: Fulfill an order from inventory.

    Checks if sufficient inventory is available, then deducts from inventory
    and ships the order. Takes a small amount of time (default 0.1 hours = 6 minutes).

    Args:
        manufacturing_center: ResourceNode with manufacturing center state
        order_quantity: Number of units to fulfill
        fulfillment_time: Time (hours) to process fulfillment (default 0.1)

    Yields:
        SimPy timeout event for fulfillment_time

    Returns:
        True if order fulfilled, False if insufficient inventory

    State changes:
        - Decrements 'inventory' by order_quantity (if successful)
        - Increments 'total_orders_fulfilled'
    """
    current_inventory = manufacturing_center.state.get("inventory", 0)

    # Check if sufficient inventory
    if current_inventory >= order_quantity:
        # Wait for fulfillment processing time
        yield manufacturing_center.env.timeout(fulfillment_time)

        # Deduct from inventory
        manufacturing_center.state["inventory"] -= order_quantity
        manufacturing_center.state["total_orders_fulfilled"] += 1
        manufacturing_center.state["total_quantity_fulfilled"] += order_quantity

        return True
    else:
        # Insufficient inventory - order is missed entirely
        manufacturing_center.state["total_orders_missed"] += 1
        manufacturing_center.state["total_quantity_missed"] += order_quantity
        return False


def process_deliveries(owner, resource, policy, time):
    """
    One-shot action: Check in-delivery orders and mark as delivered when they arrive.

    Checks orders currently in transit and marks them as 'delivered' when their
    delivery_arrival_time is reached. Policy controls if/when to check again.

    Args:
        owner: ResourceNode executing the action (the manufacturing center)
        resource: Required resources (ZurvanGraph to access distributor nodes)
        policy: PolicyNode that controls when/how often to execute
        time: Time (hours) to process each delivery completion

    Yields:
        SimPy timeout events for time

    State changes:
        - Removes delivered orders from 'in_delivery'
        - Updates order status to 'delivered'
        - Increments delivery metrics
        - Records delivery with distributor for reputation tracking (Phase 3)
    """
    in_delivery = owner.state.get("in_delivery", [])

    # Check orders that have arrived
    orders_to_deliver = []
    for order in in_delivery:
        if owner.env.now >= order.delivery_arrival_time:
            orders_to_deliver.append(order)

    # IMPORTANT: Always yield at least once, even if no work to do
    if not orders_to_deliver:
        yield owner.env.timeout(0)
        return

    # Process arrived orders
    for order in orders_to_deliver:
        yield owner.env.timeout(time)

        # Update order status
        order.status = "delivered"

        # Remove from in_delivery
        in_delivery.remove(order)

        # Update metrics
        if "total_orders_delivered" not in owner.state:
            owner.state["total_orders_delivered"] = 0
        owner.state["total_orders_delivered"] += 1

        # Record delivery with distributor for reputation tracking (Phase 3)
        if resource:  # resource is the graph
            distributor = resource.get_node(order.distributor_id)
            if distributor:
                distributor.record_order_delivery(order)

        total_time = owner.env.now - order.placement_time
        print(
            f"[Delivery] {owner.name}: {order.id} delivered to {order.distributor_id} (total time={total_time:.1f}hrs)"
        )


def check_and_fulfill_orders(owner, resource, policy, time):
    """
    One-shot action: Check pending orders and fulfill what we can.

    Checks the pending order queue once and fulfills as many orders as possible
    with current inventory (FIFO). Policy controls if/when to check again.

    Args:
        owner: ResourceNode executing the action (the manufacturing center)
        resource: Required resources (inventory, shipping) - for future use
        policy: PolicyNode that controls when/how often to execute
        time: Time (hours) to process each fulfillment

    Yields:
        SimPy timeout events for time

    State changes:
        - Moves fulfilled orders from 'pending_orders' to 'in_delivery'
        - Updates order status to 'in_delivery'
        - Decrements 'inventory'
        - Increments fulfillment metrics
        - Increments 'total_revenue' (Phase 2)
    """
    pending_orders = owner.state.get("pending_orders", [])

    # Initialize in_delivery list if not exists
    if "in_delivery" not in owner.state:
        owner.state["in_delivery"] = []

    # IMPORTANT: Always yield at least once, even if no work to do
    if not pending_orders:
        yield owner.env.timeout(0)
        return

    # Process orders while we have inventory
    while pending_orders:
        oldest_order = pending_orders[0]  # FIFO - oldest first
        current_inventory = owner.state.get("inventory", 0)

        # Check if we can fulfill this order
        if current_inventory >= oldest_order.quantity:
            # Fulfill the order
            yield owner.env.timeout(time)

            # Deduct from inventory
            owner.state["inventory"] -= oldest_order.quantity

            # Update order status to in_delivery
            oldest_order.status = "in_delivery"
            oldest_order.fulfillment_time = owner.env.now
            oldest_order.delivery_start_time = owner.env.now

            # Calculate delivery duration based on distance
            # Assume truck speed of 50 mph
            distance_miles = oldest_order.routing_distance or 0
            delivery_duration = distance_miles / 50.0  # hours
            oldest_order.delivery_duration = delivery_duration
            oldest_order.delivery_arrival_time = owner.env.now + delivery_duration

            # Calculate fulfillment duration (time in queue)
            wait_time = oldest_order.fulfillment_time - oldest_order.placement_time

            # Update metrics
            owner.state["total_orders_fulfilled"] += 1
            owner.state["total_quantity_fulfilled"] += oldest_order.quantity

            # Track revenue (Phase 2: Competitive market)
            order_revenue = oldest_order.total_order_price or 0
            owner.state["total_revenue"] += order_revenue

            # Track fulfillment times for metrics
            if "fulfillment_times" not in owner.state:
                owner.state["fulfillment_times"] = []
            owner.state["fulfillment_times"].append(wait_time)

            # Check if violated SLA (48 hours)
            if wait_time > 48:
                if "sla_violations" not in owner.state:
                    owner.state["sla_violations"] = 0
                owner.state["sla_violations"] += 1

            # Move from pending to in_delivery
            pending_orders.pop(0)
            owner.state["in_delivery"].append(oldest_order)

            print(
                f"[Fulfill] {owner.name}: {oldest_order.id} shipped to {oldest_order.distributor_id} ({oldest_order.quantity} units, revenue=${order_revenue:,.2f}, ETA={delivery_duration:.1f}hrs)"
            )
        else:
            # Not enough inventory - stop processing
            break


# Backwards compatibility aliases
# These allow old code/configs to still work
continuous_production = produce_batch  # Alias for backwards compatibility
process_pending_orders = check_and_fulfill_orders  # Alias for backwards compatibility


# Action metadata for visualization
MANUFACTURING_ACTIONS = {
    "continuous_production": {
        "name": "Continuous Production",
        "description": "Produce items continuously based on production rate",
        "type": "continuous",
        "parameters": [],
        "duration": "Variable (based on production_rate)",
        "state_changes": ["inventory", "total_produced", "machine_state"],
    },
    "change_production_rate": {
        "name": "Change Production Rate",
        "description": "Adjust production rate with 2-hour ramp time",
        "type": "atomic",
        "parameters": ["new_rate"],
        "duration": "2 hours (default)",
        "state_changes": ["production_rate", "target_rate", "machine_state"],
    },
    "fulfill_order": {
        "name": "Fulfill Order",
        "description": "Ship order from inventory (if available)",
        "type": "atomic",
        "parameters": ["order_quantity"],
        "duration": "0.1 hours (6 minutes)",
        "state_changes": ["inventory", "total_orders_fulfilled"],
    },
    "process_pending_orders": {
        "name": "Process Pending Orders",
        "description": "Continuously fulfill pending orders (FIFO) when inventory available",
        "type": "continuous",
        "parameters": [],
        "duration": "Every 1 hour",
        "state_changes": [
            "pending_orders",
            "inventory",
            "total_orders_fulfilled",
            "fulfillment_times",
        ],
    },
}
