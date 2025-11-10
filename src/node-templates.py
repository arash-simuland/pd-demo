"""
node-templates.py - Default configurations for dynamically created nodes

Provides template configurations for creating new nodes during runtime.
These templates ensure new nodes have proper actions and policies configured.
"""

# Default configuration for distributor nodes
DEFAULT_DISTRIBUTOR_CONFIG = {
    "order_probability": {
        "monday": 0.3,
        "tuesday": 0.4,
        "wednesday": 0.35,
        "thursday": 0.4,
        "friday": 0.5,
        "saturday": 0.2,
        "sunday": 0.1,
    },
    "order_size_mean": 50,
    "order_size_std": 10,
    "actions": {
        "module": "order_actions",
        "available": [
            {
                "name": "generate_orders",
                "function": "check_and_generate_order",
                "auto_start": True,
                "policy_ref": "order_policy",
                "resource": "graph",
                "time": 1.0,
            }
        ],
    },
    "policies": {"order_policy": {"type": "ContinuousOrderGenerationPolicy", "interval": 0.0}},
}

# Default configuration for manufacturing center nodes
DEFAULT_MANUFACTURER_CONFIG = {
    "capacity": 1000,
    "initial_inventory": 300,
    "initial_production_rate": 10.0,
    "max_production_rate": 20.0,
    "machine_type": "Standard Production Line",
    "actions": {
        "module": "manufacturing_actions",
        "available": [
            {
                "name": "continuous_production",
                "function": "produce_batch",
                "auto_start": True,
                "policy_ref": "production_policy",
                "resource": None,
                "time": 1.0,
            },
            {
                "name": "process_pending_orders",
                "function": "check_and_fulfill_orders",
                "auto_start": True,
                "policy_ref": "fulfillment_policy",
                "resource": None,
                "time": 0.1,
            },
            {
                "name": "process_deliveries",
                "function": "process_deliveries",
                "auto_start": True,
                "policy_ref": "delivery_policy",
                "resource": "graph",
                "time": 0.1,
            },
        ],
    },
    "policies": {
        "production_policy": {"type": "ContinuousProductionPolicy", "interval": 0.0},
        "fulfillment_policy": {"type": "ContinuousOrderFulfillmentPolicy", "interval": 0.0},
        "delivery_policy": {"type": "ContinuousOrderFulfillmentPolicy", "interval": 0.0},
    },
}


def create_distributor_config(**overrides):
    """
    Create a distributor configuration with optional overrides.

    Args:
        **overrides: Key-value pairs to override default values

    Returns:
        Dict with distributor configuration

    Example:
        config = create_distributor_config(order_size_mean=75, order_probability=0.45)
    """
    import copy

    config = copy.deepcopy(DEFAULT_DISTRIBUTOR_CONFIG)

    # Apply overrides to top-level properties
    for key, value in overrides.items():
        if key in config:
            config[key] = value

    return config


def create_manufacturer_config(**overrides):
    """
    Create a manufacturer configuration with optional overrides.

    Args:
        **overrides: Key-value pairs to override default values

    Returns:
        Dict with manufacturer configuration

    Example:
        config = create_manufacturer_config(capacity=1500, initial_production_rate=15.0)
    """
    import copy

    config = copy.deepcopy(DEFAULT_MANUFACTURER_CONFIG)

    # Apply overrides to top-level properties
    for key, value in overrides.items():
        if key in config:
            config[key] = value

    return config
