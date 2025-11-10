"""
order.py - Order class for tracking customer orders

Orders are created by distributors and routed to manufacturing centers.
They wait in a queue until fulfilled.
"""


class Order:
    """
    Represents a customer order in the system.

    Orders flow through the system:
    1. Created by distributor (with quantity and time)
    2. Routed to nearest manufacturing center
    3. Added to center's pending queue
    4. Fulfilled when inventory available (Step 8)
    """

    # Class-level counter for unique IDs
    _next_id = 1

    def __init__(self, distributor_id, quantity, placement_time):
        """
        Create a new order.

        Args:
            distributor_id: ID of distributor placing the order
            quantity: Number of units requested
            placement_time: Simulation time when order was placed
        """
        self.id = f"ORD-{Order._next_id:05d}"
        Order._next_id += 1

        self.distributor_id = distributor_id
        self.quantity = quantity
        self.placement_time = placement_time

        # Routing information (set when routed)
        self.assigned_center_id = None
        self.routing_distance = None

        # Pricing information (set when routed - Phase 2)
        self.base_unit_price = None  # Base price per unit ($)
        self.delivery_cost_total = None  # Total delivery cost for order ($)
        self.total_order_price = None  # Total price including delivery ($)
        self.delivery_time_hours = None  # Expected delivery time (hours)

        # Fulfillment information (set when fulfilled in Step 8)
        self.status = "pending"  # 'pending', 'in_delivery', 'delivered', 'missed'
        self.fulfillment_time = None

        # Delivery information (set when shipped)
        self.delivery_start_time = None
        self.delivery_arrival_time = None
        self.delivery_duration = None

    def route_to_center(self, center_id, distance, pricing_info=None):
        """
        Assign this order to a manufacturing center with pricing.

        Args:
            center_id: ID of the manufacturing center
            distance: Distance from distributor to center (miles)
            pricing_info: Dict with pricing details (optional, Phase 2)
                - base_unit_price: Base price per unit
                - delivery_cost_total: Total delivery cost
                - total_order_price: Total price including delivery
                - delivery_time_hours: Expected delivery time
        """
        self.assigned_center_id = center_id
        self.routing_distance = distance

        # Set pricing information if provided (Phase 2)
        if pricing_info:
            self.base_unit_price = pricing_info.get("base_unit_price")
            self.delivery_cost_total = pricing_info.get("delivery_cost_total")
            self.total_order_price = pricing_info.get("total_order_price")
            self.delivery_time_hours = pricing_info.get("delivery_time_hours")

    def get_wait_time(self, current_time):
        """
        Calculate how long this order has been waiting.

        Args:
            current_time: Current simulation time

        Returns:
            Wait time in hours
        """
        return current_time - self.placement_time

    def to_dict(self):
        """Convert order to dictionary for serialization"""
        return {
            "id": self.id,
            "distributor_id": self.distributor_id,
            "quantity": self.quantity,
            "placement_time": self.placement_time,
            "assigned_center_id": self.assigned_center_id,
            "routing_distance": self.routing_distance,
            "base_unit_price": self.base_unit_price,
            "delivery_cost_total": self.delivery_cost_total,
            "total_order_price": self.total_order_price,
            "delivery_time_hours": self.delivery_time_hours,
            "status": self.status,
            "fulfillment_time": self.fulfillment_time,
            "delivery_start_time": self.delivery_start_time,
            "delivery_arrival_time": self.delivery_arrival_time,
            "delivery_duration": self.delivery_duration,
        }

    def __repr__(self):
        return f"Order({self.id}, qty={self.quantity}, from={self.distributor_id}, to={self.assigned_center_id}, status={self.status})"
