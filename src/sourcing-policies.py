"""
sourcing-policies.py - Distributor Sourcing Policies (Phase 3)

Policy classes that determine how distributors select suppliers.
Each policy implements select_supplier() to choose from available manufacturers.

Competitive market simulation: Distributors are independent businesses making
autonomous sourcing decisions based on cost, reliability, and past experience.
"""


class BaseSourcingPolicy:
    """
    Base class for distributor sourcing policies.

    All sourcing policies must implement select_supplier().
    """

    def __init__(self, **params):
        """
        Initialize policy with parameters.

        Args:
            **params: Policy-specific parameters
        """
        self.params = params

    def select_supplier(self, distributor, graph, order_quantity):
        """
        Select which manufacturer should fulfill an order.

        Args:
            distributor: ResourceNode (distributor making the decision)
            graph: ZurvanGraph (access to all manufacturers and routing info)
            order_quantity: Number of units being ordered

        Returns:
            Tuple of (supplier_id, decision_info_dict) or (None, None) if no supplier
        """
        raise NotImplementedError("Subclasses must implement select_supplier()")


class NearestNeighborSourcingPolicy(BaseSourcingPolicy):
    """
    Baseline policy: Always select nearest manufacturing center.

    This is the current behavior - no intelligence, just proximity.
    Useful as a baseline for comparison.
    """

    def select_supplier(self, distributor, graph, order_quantity):
        """Select nearest manufacturer (baseline behavior)."""
        nearest_center_id, distance = graph.find_nearest_center(distributor.node_id)

        if not nearest_center_id:
            return None, None

        # Calculate pricing for decision logging
        pricing = graph.calculate_order_price(
            distributor.node_id, nearest_center_id, order_quantity
        )

        decision_info = {
            "policy": "NearestNeighbor",
            "reason": f"Closest supplier ({distance:.1f} mi)",
            "distance": distance,
            "total_cost": pricing["total_order_price"],
        }

        return nearest_center_id, decision_info


class CostMinimizerSourcingPolicy(BaseSourcingPolicy):
    """
    Pure cost minimization: Select supplier with lowest total cost.

    Evaluates all manufacturers and picks the one with lowest price
    (base unit price + delivery cost). Ignores reliability/reputation.

    Good for price-sensitive distributors, but may lead to poor service
    if cheapest supplier is unreliable.
    """

    def select_supplier(self, distributor, graph, order_quantity):
        """Select manufacturer with lowest total order cost."""
        manufacturers = graph.get_nodes_by_type("manufacturing_center")

        if not manufacturers:
            return None, None

        best_supplier = None
        min_cost = float("inf")
        best_pricing = None
        best_distance = None

        # Evaluate each manufacturer
        for center_id, center in manufacturers.items():
            # Calculate cost for this supplier
            pricing = graph.calculate_order_price(distributor.node_id, center_id, order_quantity)
            total_cost = pricing["total_order_price"]

            if total_cost < min_cost:
                min_cost = total_cost
                best_supplier = center_id
                best_pricing = pricing
                best_distance = pricing["distance_miles"]

        decision_info = {
            "policy": "CostMinimizer",
            "reason": f"Lowest cost (${min_cost:,.2f})",
            "distance": best_distance,
            "total_cost": min_cost,
            "unit_cost": best_pricing["base_unit_price"],
            "delivery_cost": best_pricing["delivery_cost_total"],
        }

        return best_supplier, decision_info


class ReliabilityThresholdSourcingPolicy(BaseSourcingPolicy):
    """
    Reliability-first: Only use suppliers meeting minimum on-time threshold.

    Filters manufacturers by on-time delivery rate, then picks nearest
    from the reliable subset. If no history exists with a supplier,
    gives them a chance (optimistic initial trust).

    Parameters:
        min_on_time_rate: Minimum acceptable on-time rate (default 0.80 = 80%)
    """

    def __init__(self, min_on_time_rate=0.80, **params):
        super().__init__(**params)
        self.min_on_time_rate = min_on_time_rate

    def select_supplier(self, distributor, graph, order_quantity):
        """Select nearest manufacturer meeting reliability threshold."""
        manufacturers = graph.get_nodes_by_type("manufacturing_center")

        if not manufacturers:
            return None, None

        # Filter to reliable suppliers
        reliable_suppliers = []

        for center_id, center in manufacturers.items():
            reputation = distributor.get_supplier_reputation(center_id)

            # If no history, give them a chance (optimistic)
            if reputation is None or reputation >= self.min_on_time_rate:
                dist_lat = distributor.location["lat"]
                dist_lon = distributor.location["lon"]
                center_lat = center.location["lat"]
                center_lon = center.location["lon"]
                distance = graph.calculate_distance(dist_lat, dist_lon, center_lat, center_lon)

                reliable_suppliers.append((center_id, distance, reputation))

        if not reliable_suppliers:
            # No reliable suppliers available - fall back to nearest
            nearest_center_id, distance = graph.find_nearest_center(distributor.node_id)
            pricing = graph.calculate_order_price(
                distributor.node_id, nearest_center_id, order_quantity
            )

            decision_info = {
                "policy": "ReliabilityThreshold",
                "reason": "No reliable suppliers, fallback to nearest",
                "distance": distance,
                "total_cost": pricing["total_order_price"],
                "threshold": self.min_on_time_rate,
            }
            return nearest_center_id, decision_info

        # Pick nearest from reliable set
        best_supplier = min(reliable_suppliers, key=lambda x: x[1])
        supplier_id, distance, reputation = best_supplier

        pricing = graph.calculate_order_price(distributor.node_id, supplier_id, order_quantity)

        # Format reputation for display
        rep_display = f"{reputation:.1%}" if reputation is not None else "No history"

        decision_info = {
            "policy": "ReliabilityThreshold",
            "reason": f"Reliable supplier (on-time: {rep_display}, threshold: {self.min_on_time_rate:.1%})",
            "distance": distance,
            "total_cost": pricing["total_order_price"],
            "reputation": reputation,
            "threshold": self.min_on_time_rate,
        }

        return supplier_id, decision_info


class WeightedScoreSourcingPolicy(BaseSourcingPolicy):
    """
    Balanced decision: Weight cost, delivery time, and reputation.

    Calculates weighted score for each supplier:
    score = w_cost × (1 - normalized_cost) +
            w_delivery × (1 - normalized_delivery_time) +
            w_reputation × reputation

    Higher score = better supplier. All factors normalized to 0-1 range.

    Parameters:
        cost_weight: Weight for cost factor (default 0.4)
        delivery_weight: Weight for delivery time factor (default 0.3)
        reputation_weight: Weight for reputation factor (default 0.3)
        default_reputation: Reputation for suppliers with no history (default 0.5)
    """

    def __init__(
        self,
        cost_weight=0.4,
        delivery_weight=0.3,
        reputation_weight=0.3,
        default_reputation=0.5,
        **params,
    ):
        super().__init__(**params)
        self.cost_weight = cost_weight
        self.delivery_weight = delivery_weight
        self.reputation_weight = reputation_weight
        self.default_reputation = default_reputation

        # Ensure weights sum to 1.0
        total_weight = cost_weight + delivery_weight + reputation_weight
        if abs(total_weight - 1.0) > 0.01:
            # Normalize weights
            self.cost_weight /= total_weight
            self.delivery_weight /= total_weight
            self.reputation_weight /= total_weight

    def select_supplier(self, distributor, graph, order_quantity):
        """Select manufacturer with best weighted score."""
        manufacturers = graph.get_nodes_by_type("manufacturing_center")

        if not manufacturers:
            return None, None

        # Collect data for all suppliers
        supplier_data = []

        for center_id, center in manufacturers.items():
            pricing = graph.calculate_order_price(distributor.node_id, center_id, order_quantity)
            reputation = distributor.get_supplier_reputation(center_id)

            if reputation is None:
                reputation = self.default_reputation

            supplier_data.append(
                {
                    "id": center_id,
                    "cost": pricing["total_order_price"],
                    "delivery_time": pricing["delivery_time_hours"],
                    "reputation": reputation,
                    "pricing": pricing,
                }
            )

        if not supplier_data:
            return None, None

        # Normalize factors to 0-1 range
        min_cost = min(s["cost"] for s in supplier_data)
        max_cost = max(s["cost"] for s in supplier_data)
        cost_range = max_cost - min_cost if max_cost > min_cost else 1.0

        min_delivery = min(s["delivery_time"] for s in supplier_data)
        max_delivery = max(s["delivery_time"] for s in supplier_data)
        delivery_range = max_delivery - min_delivery if max_delivery > min_delivery else 1.0

        # Calculate weighted scores
        best_supplier = None
        best_score = -float("inf")
        best_data = None

        for supplier in supplier_data:
            # Normalize (0 = worst, 1 = best)
            cost_score = 1.0 - ((supplier["cost"] - min_cost) / cost_range)
            delivery_score = 1.0 - ((supplier["delivery_time"] - min_delivery) / delivery_range)
            reputation_score = supplier["reputation"]

            # Weighted sum
            total_score = (
                self.cost_weight * cost_score
                + self.delivery_weight * delivery_score
                + self.reputation_weight * reputation_score
            )

            supplier["score"] = total_score
            supplier["cost_score"] = cost_score
            supplier["delivery_score"] = delivery_score
            supplier["reputation_score"] = reputation_score

            if total_score > best_score:
                best_score = total_score
                best_supplier = supplier["id"]
                best_data = supplier

        decision_info = {
            "policy": "WeightedScore",
            "reason": f"Best weighted score ({best_score:.3f})",
            "distance": best_data["pricing"]["distance_miles"],
            "total_cost": best_data["cost"],
            "delivery_time": best_data["delivery_time"],
            "reputation": best_data["reputation"],
            "score": best_score,
            "cost_score": best_data["cost_score"],
            "delivery_score": best_data["delivery_score"],
            "reputation_score": best_data["reputation_score"],
            "weights": {
                "cost": self.cost_weight,
                "delivery": self.delivery_weight,
                "reputation": self.reputation_weight,
            },
        }

        return best_supplier, decision_info


class LoyaltyBasedSourcingPolicy(BaseSourcingPolicy):
    """
    Loyalty-based: Prefer suppliers with established relationships.

    Gives preference to manufacturers the distributor has successfully
    worked with before. Helps build long-term partnerships but may
    miss better deals from new suppliers.

    Parameters:
        loyalty_bonus: Score bonus for suppliers with history (default 0.2)
        min_orders_for_loyalty: Minimum orders to qualify as "established" (default 3)
    """

    def __init__(self, loyalty_bonus=0.2, min_orders_for_loyalty=3, **params):
        super().__init__(**params)
        self.loyalty_bonus = loyalty_bonus
        self.min_orders_for_loyalty = min_orders_for_loyalty

    def select_supplier(self, distributor, graph, order_quantity):
        """Select manufacturer with loyalty consideration."""
        manufacturers = graph.get_nodes_by_type("manufacturing_center")

        if not manufacturers:
            return None, None

        # Score each supplier: cost + loyalty
        best_supplier = None
        best_score = float("inf")  # Lower score = better (cost-based)
        best_pricing = None
        best_distance = None
        best_is_loyal = False

        for center_id, center in manufacturers.items():
            pricing = graph.calculate_order_price(distributor.node_id, center_id, order_quantity)
            cost = pricing["total_order_price"]

            # Check if this is a loyal supplier
            metrics = distributor.get_supplier_metrics(center_id)
            is_loyal = False
            if metrics and metrics["orders_delivered"] >= self.min_orders_for_loyalty:
                is_loyal = True
                # Apply loyalty discount to effective cost
                cost = cost * (1 - self.loyalty_bonus)

            if cost < best_score:
                best_score = cost
                best_supplier = center_id
                best_pricing = pricing
                best_distance = pricing["distance_miles"]
                best_is_loyal = is_loyal

        decision_info = {
            "policy": "LoyaltyBased",
            "reason": f"{'Loyal supplier' if best_is_loyal else 'New supplier'} (effective cost: ${best_score:,.2f})",
            "distance": best_distance,
            "total_cost": best_pricing["total_order_price"],
            "effective_cost": best_score,
            "is_loyal": best_is_loyal,
            "loyalty_bonus": self.loyalty_bonus if best_is_loyal else 0,
        }

        return best_supplier, decision_info


# Policy registry for easy lookup
SOURCING_POLICIES = {
    "nearest_neighbor": NearestNeighborSourcingPolicy,
    "cost_minimizer": CostMinimizerSourcingPolicy,
    "reliability_threshold": ReliabilityThresholdSourcingPolicy,
    "weighted_score": WeightedScoreSourcingPolicy,
    "loyalty_based": LoyaltyBasedSourcingPolicy,
}


def create_sourcing_policy(policy_type, **params):
    """
    Factory function to create sourcing policy instances.

    Args:
        policy_type: String identifier for policy type
        **params: Policy-specific parameters

    Returns:
        SourcingPolicy instance
    """
    if policy_type not in SOURCING_POLICIES:
        raise ValueError(
            f"Unknown sourcing policy: {policy_type}. Available: {list(SOURCING_POLICIES.keys())}"
        )

    policy_class = SOURCING_POLICIES[policy_type]
    return policy_class(**params)
