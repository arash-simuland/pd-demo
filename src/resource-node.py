"""
resource_node.py - Step 2: ResourceNode Class

Zurvan resource node implementation following SimPy Agent pattern.
Each node is an object with state, connections, and (eventually) SimPy processes.
"""


class ResourceNode:
    """
    Zurvan resource node - follows SimPy Agent pattern.

    All nodes are resources. Some nodes have additional capabilities:
    - All have state (inventory, rates, etc.)
    - All have connections (graph edges)
    - All can participate in SimPy processes (env attribute)

    In Zurvan architecture:
    - Layer 1 (Structural): node_id, type, location, connections
    - Layer 2 (Temporal): state changes during simulation via SimPy processes
    - Layer 3 (Physical): location coordinates for spatial constraints
    """

    def __init__(self, env, node_id, node_type, static_data):
        """
        Initialize a resource node.

        Args:
            env: SimPy environment (None for static graph, env object for simulation)
            node_id: Unique identifier for this node
            node_type: Type of node ('manufacturing_center', 'distributor', etc.)
            static_data: Dict containing static properties from JSON (name, location, properties)
        """
        # SimPy integration
        self.env = env

        # Layer 1: Structural properties (static)
        self.node_id = node_id
        self.node_type = node_type
        self.name = static_data.get("name", node_id)
        self.location = static_data.get("location", {})
        self.properties = static_data.get("properties", {})

        # Graph structure
        self.connections = []  # List of connected ResourceNode objects

        # Layer 2: Dynamic state (changes during simulation)
        self.state = self._initialize_state()

        # Actions: What this node can do
        self.actions = {}  # Will be populated when needed
        self.automatic_actions = []  # Actions that auto-start
        self.active_processes = []  # Currently running processes

    def _initialize_state(self):
        """
        Initialize state based on node type.

        State contains dynamic properties that change during simulation.
        Different node types have different state properties.
        """
        if self.node_type == "manufacturing_center":
            # Read initial production rate from properties (data-driven)
            initial_rate = self.properties.get("initial_production_rate", 2.5)
            max_rate = self.properties.get("max_production_rate", 5.0)

            return {
                "inventory": self.properties.get("initial_inventory", 300),
                "production_rate": initial_rate,  # units per hour
                "target_rate": initial_rate,  # target production rate
                "max_production_rate": max_rate,  # maximum capacity (units/hr)
                "machine_state": "producing" if initial_rate > 0 else "idle",
                "last_rate_change_time": 0,
                "total_produced": 0,
                "total_orders_fulfilled": 0,
                "total_quantity_fulfilled": 0,
                "total_orders_missed": 0,
                "total_quantity_missed": 0,
                "pending_orders": [],  # List of Order objects waiting to be fulfilled
                "fulfillment_times": [],  # List of fulfillment times (for avg calculation)
                "sla_violations": 0,  # Count of orders that took > 48 hours
                # Financial tracking (Phase 2: Competitive market)
                "total_revenue": 0.0,  # Total revenue from fulfilled orders ($)
                "total_production_costs": 0.0,  # Cumulative production costs ($)
                "total_holding_costs": 0.0,  # Cumulative inventory holding costs ($)
                "total_rate_change_costs": 0.0,  # Cumulative rate change costs ($)
                "total_cross_fulfillment_costs": 0.0,  # Costs paid to other manufacturers ($)
                "production_hours": 0.0,  # Total hours of production (for cost calculation)
                "rate_changes_count": 0,  # Number of rate changes (for cost calculation)
                "last_cost_update_time": 0,  # Last time holding costs were updated
            }
        if self.node_type == "distributor":
            return {
                "orders_placed": 0,
                "orders_fulfilled": 0,
                "total_order_quantity": 0,
                "total_fulfilled_quantity": 0,
                "last_order_time": 0,
                # Supplier relationship tracking (Phase 3: Competitive market)
                # Maps supplier_id -> performance metrics
                "supplier_relationships": {},
                # Format: {
                #   'chicago_center': {
                #       'orders_placed': 5,
                #       'orders_delivered': 4,
                #       'orders_late': 1,
                #       'total_cost_paid': 125000.0,
                #       'total_wait_time': 120.5,  # hours
                #       'avg_wait_time': 24.1,  # hours
                #       'on_time_rate': 0.80,  # 80%
                #       'last_order_time': 48.0
                #   }
                # }
                # Current orders in delivery (to track performance)
                "orders_in_delivery": [],  # List of Order objects being delivered
            }
        return {}

    def get_state_summary(self):
        """Get a human-readable summary of current state"""
        if self.node_type == "manufacturing_center":
            return (
                f"Inventory: {self.state['inventory']} units, "
                f"Rate: {self.state['production_rate']} units/hr, "
                f"Status: {self.state['machine_state']}"
            )
        if self.node_type == "distributor":
            return (
                f"Orders Placed: {self.state['orders_placed']}, "
                f"Orders Fulfilled: {self.state['orders_fulfilled']}"
            )
        return "No state"

    def get_color(self):
        """
        Get node color based on current state.
        Used for visualization color coding.
        """
        if self.node_type == "manufacturing_center":
            state = self.state.get("machine_state", "idle")
            if state == "idle":
                return "#808080"  # Gray
            if state == "producing":
                return "#00C851"  # Green
            if state == "adjusting":
                return "#FFD700"  # Gold/Yellow
            return "#2E86AB"  # Default blue
        if self.node_type == "distributor":
            return "#00C853"  # Green
        return "#2E86AB"  # Default blue

    def reset_state(self):
        """Reset node state to initial values"""
        self.state = self._initialize_state()

    def _register_actions(self):
        """
        Register actions this node can perform.

        Actions are loaded from properties (data-driven, no if/else!).
        Configuration comes from JSON, not hardcoded in Python.
        """
        action_config = self.properties.get("actions", {})
        module_name = action_config.get("module")
        available_actions = action_config.get("available", [])

        if not module_name or not available_actions:
            return {}

        # Dynamically import the action module (handles kebab-case module names)
        import importlib

        # Map JSON module names to actual kebab-case file names
        module_map = {
            "manufacturing_actions": "manufacturing-actions",
            "order_actions": "order-actions",
        }

        actual_module_name = module_map.get(module_name, module_name)

        try:
            action_module = importlib.import_module(f"actions.{actual_module_name}")
        except ImportError as e:
            print(f"[Warning] Could not import actions.{actual_module_name}: {e}")
            return {}

        # Get action functions from the module
        actions = {}
        for action in available_actions:
            # Support both old format (strings) and new format (dicts)
            if isinstance(action, dict):
                function_name = action["function"]
            else:
                function_name = action  # Old format: just a string

            action_func = getattr(action_module, function_name, None)
            if action_func:
                actions[function_name] = action_func
            else:
                print(f"[Warning] Function '{function_name}' not found in {module_name}")

        return actions

    def _get_automatic_actions(self):
        """
        Get actions that should start automatically at initialization.

        Returns actions where auto_start=True in the action configuration.
        Configuration loaded from properties (data-driven, no if/else!).
        """
        action_config = self.properties.get("actions", {})
        available_actions = action_config.get("available", [])

        # Filter for actions with auto_start=True
        automatic_actions = []
        for action in available_actions:
            # Support both old format (strings) and new format (dicts)
            if isinstance(action, dict) and action.get("auto_start", False):
                automatic_actions.append(action)

        return automatic_actions

    def _policy_driven_loop(self, action_func, policy, resource=None, time=1.0):
        """
        Generic policy-driven loop for actions.

        The policy controls:
        - Whether to continue (should_continue)
        - When to execute next (get_next_interval)
        - How to modify parameters (modify_parameters)

        Args:
            action_func: The one-shot action function to execute
            policy: PolicyNode that controls execution
            resource: Required resource for the action
            time: Time parameter for the action
        """
        # Execute action repeatedly as long as policy says to continue
        while policy.should_continue(self):
            # Execute the action once with four inputs: (owner, resource, policy, time)
            yield from action_func(self, resource, policy, time)

            # Get interval from policy and wait
            # IMPORTANT: Always yield, even if interval=0, to prevent infinite loops
            interval = policy.get_next_interval(self)
            if interval > 0:
                yield self.env.timeout(interval)
            else:
                # Yield control even with 0 interval to allow other processes to run
                yield self.env.timeout(0)

    def _create_policy(self, policy_config):
        """
        Create a policy instance from configuration.

        Args:
            policy_config: Dict with 'type' and optional 'interval'

        Returns:
            PolicyNode instance
        """
        import importlib

        default_policies = importlib.import_module("default-policies")
        ContinuousProductionPolicy = default_policies.ContinuousProductionPolicy
        ContinuousOrderFulfillmentPolicy = default_policies.ContinuousOrderFulfillmentPolicy
        ContinuousOrderGenerationPolicy = default_policies.ContinuousOrderGenerationPolicy
        StaticPolicy = default_policies.StaticPolicy

        policy_type = policy_config.get("type")
        interval = policy_config.get("interval", 0.0)

        # Map policy type to class
        policy_classes = {
            "ContinuousProductionPolicy": ContinuousProductionPolicy,
            "ContinuousOrderFulfillmentPolicy": ContinuousOrderFulfillmentPolicy,
            "ContinuousOrderGenerationPolicy": ContinuousOrderGenerationPolicy,
            "StaticPolicy": StaticPolicy,
        }

        policy_class = policy_classes.get(policy_type)
        if not policy_class:
            raise ValueError(f"Unknown policy type: {policy_type}")

        # Create policy with interval if supported
        if policy_type in ["ContinuousOrderFulfillmentPolicy", "ContinuousOrderGenerationPolicy"]:
            return policy_class(check_interval=interval)
        return policy_class()

    def _resolve_resource(self, resource_spec):
        """
        Resolve a resource specification to an actual resource.

        Args:
            resource_spec: String name or null

        Returns:
            Resource object or None
        """
        if resource_spec is None or resource_spec == "null":
            return None
        if resource_spec == "graph":
            return self._graph_ref
        # Future: resolve other resource types
        return None

    def start(self):
        """
        Start this node's automatic actions with policy-driven loops.

        The node activates its own actions from within - it's an autonomous agent.
        Policies control when and how often actions execute.

        Fully data-driven from JSON configuration - no hardcoded if/elif!
        """
        if not self.actions:
            # Lazy initialization - only register actions when needed
            self.actions = self._register_actions()
            self.automatic_actions = self._get_automatic_actions()

        if self.env is None:
            # Can't start without SimPy environment
            return

        # Guard: Don't start processes if they're already running
        if len(self.active_processes) > 0:
            return  # Already started

        # Get policies configuration
        policies_config = self.properties.get("policies", {})

        # Start each automatic action
        for action_config in self.automatic_actions:
            action_name = action_config["name"]
            function_name = action_config["function"]
            policy_ref = action_config["policy_ref"]
            resource_spec = action_config.get("resource")
            time = action_config["time"]

            # Get action function
            action_func = self.actions.get(function_name)
            if not action_func:
                print(f"[Warning] Function '{function_name}' not found in actions")
                continue

            # Create policy from configuration
            policy_config = policies_config.get(policy_ref)
            if not policy_config:
                print(f"[Warning] Policy '{policy_ref}' not found in policies")
                continue

            policy = self._create_policy(policy_config)

            # Resolve resource
            resource = self._resolve_resource(resource_spec)

            # Start policy-driven loop for this action
            # Calls action with signature: action(owner, resource, policy, time)
            process = self.env.process(
                self._policy_driven_loop(action_func, policy, resource=resource, time=time)
            )

            self.active_processes.append({"name": action_name, "process": process})

    def stop(self):
        """Stop all active processes"""
        for proc_info in self.active_processes:
            try:
                proc_info["process"].interrupt()
            except:
                pass
        self.active_processes = []

    def is_running(self):
        """Check if node has active processes"""
        return len(self.active_processes) > 0

    def update_holding_costs(self):
        """
        Update holding costs based on current inventory and elapsed time.
        Should be called periodically (e.g., daily) by manufacturing centers.

        Uses cost parameters from cost-parameters.json:
        - daily_cost_per_unit: Cost per unit per day for holding inventory
        """
        if self.node_type != "manufacturing_center" or not self.env:
            return

        import json
        from pathlib import Path

        # Load cost parameters
        try:
            cost_params_path = Path(__file__).parent.parent / "data" / "cost-parameters.json"
            with open(cost_params_path) as f:
                cost_params = json.load(f)
            daily_cost_per_unit = cost_params["holding_costs"]["daily_cost_per_unit"]
        except:
            daily_cost_per_unit = 0.34  # Default fallback

        # Calculate time elapsed since last update (in hours)
        current_time = self.env.now
        last_update = self.state["last_cost_update_time"]
        hours_elapsed = current_time - last_update

        if hours_elapsed > 0:
            # Convert hours to days
            days_elapsed = hours_elapsed / 24.0

            # Calculate holding cost: average inventory × days × cost per unit per day
            avg_inventory = self.state["inventory"]  # Simplified: use current inventory
            holding_cost = avg_inventory * days_elapsed * daily_cost_per_unit

            # Update state
            self.state["total_holding_costs"] += holding_cost
            self.state["last_cost_update_time"] = current_time

    def calculate_total_costs(self):
        """
        Calculate total costs for this manufacturing center.

        Returns:
            Total costs ($) including production, holding, rate changes, and cross-fulfillment
        """
        if self.node_type != "manufacturing_center":
            return 0.0

        return (
            self.state.get("total_production_costs", 0.0)
            + self.state.get("total_holding_costs", 0.0)
            + self.state.get("total_rate_change_costs", 0.0)
            + self.state.get("total_cross_fulfillment_costs", 0.0)
        )

    def calculate_profit(self):
        """
        Calculate current profit for this manufacturing center.

        Returns:
            Profit ($) = Revenue - Total Costs
        """
        if self.node_type != "manufacturing_center":
            return 0.0

        revenue = self.state.get("total_revenue", 0.0)
        costs = self.calculate_total_costs()
        return revenue - costs

    def get_financial_summary(self):
        """
        Get a human-readable financial summary.

        Returns:
            String with revenue, costs, and profit
        """
        if self.node_type != "manufacturing_center":
            return "No financial data"

        # Update holding costs to current time
        self.update_holding_costs()

        revenue = self.state.get("total_revenue", 0.0)
        costs = self.calculate_total_costs()
        profit = self.calculate_profit()

        return f"Revenue: ${revenue:,.2f} | Costs: ${costs:,.2f} | Profit: ${profit:,.2f}"

    def record_order_placement(self, supplier_id, order):
        """
        Record that an order was placed to a supplier (Phase 3).

        Updates supplier relationship tracking for distributor nodes.

        Args:
            supplier_id: ID of the manufacturing center receiving the order
            order: Order object that was placed
        """
        if self.node_type != "distributor":
            return

        relationships = self.state["supplier_relationships"]

        # Initialize relationship tracking if first order to this supplier
        if supplier_id not in relationships:
            relationships[supplier_id] = {
                "orders_placed": 0,
                "orders_delivered": 0,
                "orders_late": 0,
                "total_cost_paid": 0.0,
                "total_wait_time": 0.0,
                "avg_wait_time": 0.0,
                "on_time_rate": 1.0,  # Start optimistic
                "last_order_time": 0.0,
            }

        # Update metrics
        rel = relationships[supplier_id]
        rel["orders_placed"] += 1
        rel["last_order_time"] = self.env.now if self.env else 0

        # Add order to tracking list
        self.state["orders_in_delivery"].append(order)

    def record_order_delivery(self, order, late_threshold_hours=48):
        """
        Record that an order was delivered (Phase 3).

        Updates supplier performance metrics based on delivery time.

        Args:
            order: Order object that was delivered
            late_threshold_hours: Hours threshold for considering order "late" (default 48)
        """
        if self.node_type != "distributor":
            return

        supplier_id = order.assigned_center_id
        relationships = self.state["supplier_relationships"]

        if supplier_id not in relationships:
            return  # Shouldn't happen, but be defensive

        rel = relationships[supplier_id]

        # Calculate actual wait time (placement to delivery)
        current_time = self.env.now if self.env else 0
        wait_time = current_time - order.placement_time

        # Update metrics
        rel["orders_delivered"] += 1
        rel["total_wait_time"] += wait_time
        rel["avg_wait_time"] = rel["total_wait_time"] / rel["orders_delivered"]

        # Track late deliveries
        if wait_time > late_threshold_hours:
            rel["orders_late"] += 1

        # Calculate on-time rate
        rel["on_time_rate"] = 1.0 - (rel["orders_late"] / rel["orders_delivered"])

        # Track cost
        if order.total_order_price:
            rel["total_cost_paid"] += order.total_order_price

        # Remove from in-delivery tracking
        if order in self.state["orders_in_delivery"]:
            self.state["orders_in_delivery"].remove(order)

        # Update distributor's overall fulfilled count
        self.state["orders_fulfilled"] += 1
        self.state["total_fulfilled_quantity"] += order.quantity

    def get_supplier_reputation(self, supplier_id):
        """
        Get reputation score for a supplier (Phase 3).

        Calculates a 0-1 reputation score based on past performance.
        Higher score = better supplier.

        Args:
            supplier_id: ID of the manufacturing center

        Returns:
            Reputation score (0-1), or None if no history
        """
        if self.node_type != "distributor":
            return None

        relationships = self.state["supplier_relationships"]

        if supplier_id not in relationships:
            return None  # No history with this supplier

        rel = relationships[supplier_id]

        # Simple reputation: on_time_rate (can be made more sophisticated)
        return rel["on_time_rate"]

    def get_supplier_metrics(self, supplier_id):
        """
        Get detailed performance metrics for a supplier (Phase 3).

        Args:
            supplier_id: ID of the manufacturing center

        Returns:
            Dict of metrics, or None if no history
        """
        if self.node_type != "distributor":
            return None

        relationships = self.state["supplier_relationships"]
        return relationships.get(supplier_id)

    def to_dict(self):
        """
        Export node to dictionary format.
        Useful for JSON serialization and visualization.
        """
        return {
            "node_id": self.node_id,
            "type": self.node_type,
            "name": self.name,
            "location": self.location,
            "properties": self.properties,
            "state": self.state,
            "num_connections": len(self.connections),
        }

    def __str__(self):
        return f"{self.node_type.title()} '{self.name}' ({self.node_id})"

    def __repr__(self):
        return f"ResourceNode(id={self.node_id}, type={self.node_type}, state={self.state})"
