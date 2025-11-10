"""
policy_node.py - PolicyNode Base Class

Policy nodes are special resource nodes that contain decision logic.
They control how and when actions are executed.

In Zurvan architecture:
- Actions define WHAT happens (the logic)
- Policies define WHEN and HOW OFTEN actions execute (the control)
- Resources define WHAT is needed (the constraints)
"""


class PolicyNode:
    """
    Base class for policy nodes.

    Policy nodes are decision-making nodes that control action execution.
    They determine:
    - Whether an action should execute (guard condition)
    - When to execute next (interval/timing)
    - How to modify action parameters (adaptive behavior)

    In Zurvan terms, policies are "intention nodes" that give actions purpose.
    """

    def __init__(self, policy_id, policy_type="base"):
        """
        Initialize a policy node.

        Args:
            policy_id: Unique identifier for this policy
            policy_type: Type of policy (for categorization)
        """
        self.policy_id = policy_id
        self.policy_type = policy_type

    def should_continue(self, node, **context):
        """
        Decide if action should continue executing.

        Args:
            node: The ResourceNode executing the action
            **context: Additional context for decision (state, history, etc.)

        Returns:
            bool: True if action should execute again, False to stop
        """
        # Default: always continue (override in subclasses)
        return True

    def get_next_interval(self, node, **context):
        """
        Decide how long to wait before next execution.

        Args:
            node: The ResourceNode executing the action
            **context: Additional context for decision

        Returns:
            float: Time (hours) to wait before next execution
        """
        # Default: 1 hour interval (override in subclasses)
        return 1.0

    def modify_parameters(self, node, default_params, **context):
        """
        Modify action parameters before execution.

        Allows policy to adaptively adjust action behavior based on
        current state, history, or other factors.

        Args:
            node: The ResourceNode executing the action
            default_params: Default parameters for the action
            **context: Additional context for decision

        Returns:
            dict: Modified parameters for action execution
        """
        # Default: use default parameters unchanged (override in subclasses)
        return default_params

    def __str__(self):
        return f"Policy '{self.policy_id}' ({self.policy_type})"

    def __repr__(self):
        return f"PolicyNode(id={self.policy_id}, type={self.policy_type})"
