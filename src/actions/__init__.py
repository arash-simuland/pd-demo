"""
actions package - Step 3: Action Definitions

This package contains SimPy generator functions that define all possible actions
in the product delivery model. These actions are NOT executed yet - they are just
definitions of what CAN happen.

Execution will be added in Step 4-5.
"""

import importlib


# Import modules with kebab-case names using importlib
manufacturing_actions = importlib.import_module(".manufacturing-actions", package="actions")
order_actions = importlib.import_module(".order-actions", package="actions")

# Re-export for convenience
MANUFACTURING_ACTIONS = manufacturing_actions.MANUFACTURING_ACTIONS
ORDER_ACTIONS = order_actions.ORDER_ACTIONS
continuous_production = manufacturing_actions.continuous_production
change_production_rate = manufacturing_actions.change_production_rate
fulfill_order = manufacturing_actions.fulfill_order
generate_orders = order_actions.generate_orders
route_order = order_actions.route_order
track_order_fulfillment = order_actions.track_order_fulfillment

__all__ = [
    "MANUFACTURING_ACTIONS",
    "ORDER_ACTIONS",
    "change_production_rate",
    "continuous_production",
    "fulfill_order",
    "generate_orders",
    "route_order",
    "track_order_fulfillment",
]
