"""
default_policies.py - Default Policy Implementations

Default policies that replicate the current hardcoded behavior.
These ensure backwards compatibility while transitioning to policy-driven architecture.
"""

import importlib


policy_node = importlib.import_module("policy-node")
PolicyNode = policy_node.PolicyNode


class ContinuousProductionPolicy(PolicyNode):
    """
    Policy for continuous production.

    Decides:
    - Continue while production_rate > 0 OR machine is idle
    - Interval: production_time (no additional wait)
    - Parameters: production_time based on current settings
    """

    def __init__(self, policy_id="continuous_production_policy"):
        super().__init__(policy_id, policy_type="production")

    def should_continue(self, node, **context):
        """Always continue - production is ongoing"""
        return True

    def get_next_interval(self, node, **context):
        """No additional interval - production happens continuously"""
        return 0.0  # No wait between production cycles

    def modify_parameters(self, node, default_params, **context):
        """Use default production time"""
        return default_params


class ContinuousOrderFulfillmentPolicy(PolicyNode):
    """
    Policy for continuous order fulfillment.

    Decides:
    - Always continue checking for pending orders
    - Interval: 1 hour between checks
    - Parameters: fulfillment_time per order
    """

    def __init__(self, policy_id="continuous_fulfillment_policy", check_interval=1.0):
        super().__init__(policy_id, policy_type="fulfillment")
        self.check_interval = check_interval

    def should_continue(self, node, **context):
        """Always continue - keep checking for orders"""
        return True

    def get_next_interval(self, node, **context):
        """Check every hour"""
        return self.check_interval

    def modify_parameters(self, node, default_params, **context):
        """Use default fulfillment time"""
        return default_params


class ContinuousOrderGenerationPolicy(PolicyNode):
    """
    Policy for continuous order generation.

    Decides:
    - Always continue generating orders
    - Interval: 2 hours between generation checks
    - Parameters: order_generation_time
    """

    def __init__(self, policy_id="continuous_generation_policy", check_interval=2.0):
        super().__init__(policy_id, policy_type="order_generation")
        self.check_interval = check_interval

    def should_continue(self, node, **context):
        """Always continue - keep generating orders"""
        return True

    def get_next_interval(self, node, **context):
        """Check every 2 hours (for demo speed)"""
        return self.check_interval

    def modify_parameters(self, node, default_params, **context):
        """Use default order generation time"""
        return default_params


class StaticPolicy(PolicyNode):
    """
    Simple static policy for one-shot actions.

    Executes action once and stops (no repetition).
    """

    def __init__(self, policy_id="static_policy"):
        super().__init__(policy_id, policy_type="static")

    def should_continue(self, node, **context):
        """Execute once only"""
        return False

    def get_next_interval(self, node, **context):
        """No interval - single execution"""
        return 0.0

    def modify_parameters(self, node, default_params, **context):
        """Use parameters as-is"""
        return default_params
