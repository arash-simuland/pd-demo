"""
graph_builder.py - Step 1 & 2: Build the Structural Layer with ResourceNodes

Creates the base graph structure with nodes and edges.
Step 2: Uses ResourceNode objects instead of dictionaries.

Demonstrates Zurvan's Layer 1 (Structural Layer) - the static graph before actions.
"""

import importlib
import json
import math
from pathlib import Path
from typing import Dict, List, Tuple


resource_node = importlib.import_module("resource-node")
ResourceNode = resource_node.ResourceNode


class ZurvanGraph:
    """
    Represents the structural layer of the Zurvan model.

    In Zurvan architecture:
    - Layer 1 (Structural): What things are, where they are, how they're connected
    - This class implements Layer 1 - nodes are ResourceNode objects (Step 2)
    """

    def __init__(self, env=None):
        """
        Initialize graph.

        Args:
            env: SimPy environment (None for static graph, env object for simulation)
        """
        self.env = env
        self.nodes = {}  # node_id -> ResourceNode object
        self.edges = []  # list of edge dicts

    def add_node(self, node_id: str, node_data: dict):
        """
        Add a ResourceNode to the graph.

        Args:
            node_id: Unique node identifier
            node_data: Dict with 'type', 'name', 'location', 'properties'
        """
        node = ResourceNode(
            env=self.env, node_id=node_id, node_type=node_data["type"], static_data=node_data
        )
        # Give node a reference to the graph for actions that need it
        node._graph_ref = self
        self.nodes[node_id] = node

    def add_edge(self, from_id: str, to_id: str, edge_data: dict):
        """
        Add an edge between two nodes and update node connections.

        Args:
            from_id: Source node ID
            to_id: Target node ID
            edge_data: Edge properties (distance, type, etc.)
        """
        edge = {"from": from_id, "to": to_id, **edge_data}
        self.edges.append(edge)

        # Update node connections (graph structure)
        from_node = self.nodes.get(from_id)
        to_node = self.nodes.get(to_id)
        if from_node and to_node and to_node not in from_node.connections:
            from_node.connections.append(to_node)

    def get_node(self, node_id: str) -> ResourceNode:
        """Get ResourceNode by ID"""
        return self.nodes.get(node_id)

    def get_nodes_by_type(self, node_type: str) -> Dict[str, ResourceNode]:
        """Get all ResourceNodes of a specific type"""
        return {
            node_id: node for node_id, node in self.nodes.items() if node.node_type == node_type
        }

    def get_edges_from_node(self, node_id: str) -> List[dict]:
        """Get all edges originating from a node"""
        return [edge for edge in self.edges if edge["from"] == node_id]

    def get_edges_to_node(self, node_id: str) -> List[dict]:
        """Get all edges pointing to a node"""
        return [edge for edge in self.edges if edge["to"] == node_id]

    @staticmethod
    def calculate_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """
        Calculate Euclidean distance between two geographic points.

        For demonstration purposes, we use a simplified calculation.
        In production, you'd use haversine distance for geographic coordinates.

        Returns distance in approximate miles.
        """
        # Rough conversion: 1 degree lat/lon ≈ 69 miles at mid-latitudes
        lat_diff = (lat2 - lat1) * 69
        lon_diff = (lon2 - lon1) * 69 * math.cos(math.radians((lat1 + lat2) / 2))
        distance = math.sqrt(lat_diff**2 + lon_diff**2)
        return distance

    def find_nearest_center(self, distributor_id: str) -> Tuple[str, float]:
        """
        Find the nearest manufacturing center to a distributor.

        Returns (center_id, distance)
        """
        distributor = self.get_node(distributor_id)
        if not distributor:
            raise ValueError(f"Distributor {distributor_id} not found")

        dist_lat = distributor.location["lat"]
        dist_lon = distributor.location["lon"]

        centers = self.get_nodes_by_type("manufacturing_center")

        nearest_center = None
        min_distance = float("inf")

        for center_id, center in centers.items():
            center_lat = center.location["lat"]
            center_lon = center.location["lon"]

            distance = self.calculate_distance(dist_lat, dist_lon, center_lat, center_lon)

            if distance < min_distance:
                min_distance = distance
                nearest_center = center_id

        return nearest_center, min_distance

    def calculate_order_price(self, distributor_id: str, center_id: str, quantity: int) -> dict:
        """
        Calculate total price for an order including delivery costs (Phase 2).

        Args:
            distributor_id: ID of the distributor placing the order
            center_id: ID of the manufacturing center fulfilling the order
            quantity: Number of units ordered

        Returns:
            Dictionary with pricing details:
                - base_unit_price: Base price per unit ($)
                - delivery_cost_total: Total delivery cost ($)
                - delivery_cost_per_unit: Delivery cost per unit ($)
                - total_order_price: Total price including delivery ($)
                - delivery_time_hours: Expected delivery time (hours)
                - distance_miles: Distance between distributor and center (miles)
        """
        # Load cost parameters
        try:
            cost_params_path = Path(__file__).parent.parent / "data" / "cost-parameters.json"
            with open(cost_params_path) as f:
                cost_params = json.load(f)
        except:
            # Default fallback values if file not found
            cost_params = {
                "product": {"base_unit_price": 500.0},
                "delivery": {"cost_per_mile": 0.50, "average_speed_mph": 50.0},
            }

        # Get base prices
        base_unit_price = cost_params["product"]["base_unit_price"]
        cost_per_mile = cost_params["delivery"]["cost_per_mile"]
        speed_mph = cost_params["delivery"]["average_speed_mph"]

        # Calculate distance
        distributor = self.get_node(distributor_id)
        center = self.get_node(center_id)

        dist_lat = distributor.location["lat"]
        dist_lon = distributor.location["lon"]
        center_lat = center.location["lat"]
        center_lon = center.location["lon"]

        distance_miles = self.calculate_distance(dist_lat, dist_lon, center_lat, center_lon)

        # Calculate delivery costs and time
        delivery_cost_total = distance_miles * cost_per_mile
        delivery_cost_per_unit = delivery_cost_total / quantity if quantity > 0 else 0
        delivery_time_hours = distance_miles / speed_mph

        # Calculate total order price
        product_cost = base_unit_price * quantity
        total_order_price = product_cost + delivery_cost_total

        return {
            "base_unit_price": base_unit_price,
            "delivery_cost_total": round(delivery_cost_total, 2),
            "delivery_cost_per_unit": round(delivery_cost_per_unit, 2),
            "total_order_price": round(total_order_price, 2),
            "delivery_time_hours": round(delivery_time_hours, 2),
            "distance_miles": round(distance_miles, 1),
        }

    def to_dict(self) -> dict:
        """Export graph to dictionary format"""
        return {
            "nodes": {node_id: node.to_dict() for node_id, node in self.nodes.items()},
            "edges": self.edges,
        }

    def add_distributor_dynamically(self, city: str, state: str, **overrides) -> ResourceNode:
        """
        Add a new distributor to the graph dynamically (while simulation is running).

        Args:
            city: City name (e.g., "Dallas")
            state: State name or abbreviation (e.g., "TX" or "Texas")
            **overrides: Optional property overrides (order_size_mean, order_probability, etc.)

        Returns:
            The created ResourceNode

        Raises:
            ValueError: If city cannot be geocoded

        Example:
            new_dist = graph.add_distributor_dynamically("Dallas", "TX", order_size_mean=75)
        """
        import importlib

        geocoding_utils = importlib.import_module("geocoding-utils")
        node_templates = importlib.import_module("node-templates")

        # Geocode city
        coords = geocoding_utils.geocode_city(city, state)
        if coords is None:
            raise ValueError(f"Could not geocode city: {city}, {state}")

        lat, lon = coords

        # Generate unique ID
        node_id = f"distributor_{city.lower().replace(' ', '_')}"

        # Check if node already exists
        if node_id in self.nodes:
            raise ValueError(f"Distributor already exists: {node_id}")

        # Create node configuration from template
        properties = node_templates.create_distributor_config(**overrides)

        node_data = {
            "id": node_id,
            "type": "distributor",
            "name": f"{city} Distributor",
            "location": {"lat": lat, "lon": lon, "city": city, "state": state},
            "properties": properties,
        }

        # Add node to graph
        self.add_node(node_id, node_data)
        new_node = self.nodes[node_id]

        # Connect to all manufacturing centers
        centers = self.get_nodes_by_type("manufacturing_center")
        for center_id, center in centers.items():
            distance = self.calculate_distance(
                lat, lon, center.location["lat"], center.location["lon"]
            )

            edge_data = {
                "type": "distributor_to_center",
                "distance_miles": round(distance, 2),
                "routing_cost": round(distance * 0.5, 2),
            }

            self.add_edge(node_id, center_id, edge_data)

        # Start node processes if environment exists
        if self.env is not None:
            initial_count = len(new_node.active_processes)
            new_node.start()
            processes_started = len(new_node.active_processes) - initial_count

            # Print what processes were started
            for proc_info in new_node.active_processes[initial_count:]:
                print(f"[Process] Started {proc_info['name']} for {new_node.name}")

            print(f"[Graph] Started {processes_started} processes for {new_node.name}")

        print(f"[Graph] Created {new_node.name} at ({lat:.4f}, {lon:.4f})")
        print(f"[Graph] Connected to {len(centers)} manufacturing centers")

        return new_node

    def add_manufacturer_dynamically(self, city: str, state: str, **overrides) -> ResourceNode:
        """
        Add a new manufacturing center to the graph dynamically (while simulation is running).

        Args:
            city: City name (e.g., "Atlanta")
            state: State name or abbreviation (e.g., "GA" or "Georgia")
            **overrides: Optional property overrides (capacity, initial_production_rate, etc.)

        Returns:
            The created ResourceNode

        Raises:
            ValueError: If city cannot be geocoded

        Example:
            new_mfg = graph.add_manufacturer_dynamically("Atlanta", "GA", capacity=1500)
        """
        import importlib

        geocoding_utils = importlib.import_module("geocoding-utils")
        node_templates = importlib.import_module("node-templates")

        # Geocode city
        coords = geocoding_utils.geocode_city(city, state)
        if coords is None:
            raise ValueError(f"Could not geocode city: {city}, {state}")

        lat, lon = coords

        # Generate unique ID
        node_id = f"{city.lower().replace(' ', '_')}_center"

        # Check if node already exists
        if node_id in self.nodes:
            raise ValueError(f"Manufacturing center already exists: {node_id}")

        # Create node configuration from template
        properties = node_templates.create_manufacturer_config(**overrides)

        node_data = {
            "id": node_id,
            "type": "manufacturing_center",
            "name": f"{city} Manufacturing Center",
            "location": {"lat": lat, "lon": lon, "city": city, "state": state},
            "properties": properties,
        }

        # Add node to graph
        self.add_node(node_id, node_data)
        new_node = self.nodes[node_id]

        # Connect to all distributors
        distributors = self.get_nodes_by_type("distributor")
        for dist_id, dist in distributors.items():
            distance = self.calculate_distance(lat, lon, dist.location["lat"], dist.location["lon"])

            edge_data = {
                "type": "distributor_to_center",
                "distance_miles": round(distance, 2),
                "routing_cost": round(distance * 0.5, 2),
            }

            self.add_edge(dist_id, node_id, edge_data)

        # Start node processes if environment exists
        if self.env is not None:
            initial_count = len(new_node.active_processes)
            new_node.start()
            processes_started = len(new_node.active_processes) - initial_count

            # Print what processes were started
            for proc_info in new_node.active_processes[initial_count:]:
                print(f"[Process] Started {proc_info['name']} for {new_node.name}")

            print(f"[Graph] Started {processes_started} processes for {new_node.name}")

        print(f"[Graph] Created {new_node.name} at ({lat:.4f}, {lon:.4f})")
        print(f"[Graph] Connected to {len(distributors)} distributors")

        return new_node

    def __repr__(self):
        num_centers = len(self.get_nodes_by_type("manufacturing_center"))
        num_distributors = len(self.get_nodes_by_type("distributor"))
        num_edges = len(self.edges)
        return f"ZurvanGraph(centers={num_centers}, distributors={num_distributors}, edges={num_edges})"


def load_graph_from_data(data_dir: Path = None) -> ZurvanGraph:
    """
    Load graph structure from data files.

    This demonstrates how to build Zurvan's structural layer from data.
    """
    if data_dir is None:
        # Default to data/ directory relative to this file
        data_dir = Path(__file__).parent.parent / "data"

    # Load nodes
    nodes_file = data_dir / "nodes.json"
    with open(nodes_file) as f:
        nodes_data = json.load(f)

    # Load edge definitions
    edges_file = data_dir / "edges.json"
    with open(edges_file) as f:
        edges_config = json.load(f)

    # Create graph
    graph = ZurvanGraph()

    # Add manufacturing centers
    for center in nodes_data["manufacturing_centers"]:
        graph.add_node(center["id"], center)

    # Add distributors
    for distributor in nodes_data["distributors"]:
        graph.add_node(distributor["id"], distributor)

    # Create edges: each distributor connects to all manufacturing centers
    # (weighted by distance for routing decisions)
    distributors = graph.get_nodes_by_type("distributor")
    centers = graph.get_nodes_by_type("manufacturing_center")

    for dist_id, dist_node in distributors.items():
        for center_id, center_node in centers.items():
            # Calculate distance
            dist_loc = dist_node.location
            center_loc = center_node.location

            distance = ZurvanGraph.calculate_distance(
                dist_loc["lat"], dist_loc["lon"], center_loc["lat"], center_loc["lon"]
            )

            # Create edge
            edge_data = {
                "type": "distributor_to_center",
                "distance_miles": round(distance, 2),
                "routing_cost": round(distance * 0.5, 2),  # $0.50 per mile
            }

            graph.add_edge(dist_id, center_id, edge_data)

    print(f"[OK] Loaded {graph}")
    print(f"  - Manufacturing Centers: {list(centers.keys())}")
    print(f"  - Distributors: {list(distributors.keys())}")
    print(f"  - Edges created: {len(graph.edges)}")

    return graph


def print_graph_summary(graph: ZurvanGraph):
    """Print a summary of the graph structure"""
    print("\n" + "=" * 60)
    print("ZURVAN STRUCTURAL LAYER (Layer 1)")
    print("=" * 60)

    # Manufacturing Centers
    print("\nMANUFACTURING CENTERS:")
    centers = graph.get_nodes_by_type("manufacturing_center")
    for center_id, center in centers.items():
        loc = center.location
        cap = center.properties["capacity"]
        print(f"  • {center.name}")
        print(f"    Location: {loc['city']}, {loc['state']} ({loc['lat']:.4f}, {loc['lon']:.4f})")
        print(f"    Capacity: {cap} units")
        print(f"    State: {center.get_state_summary()}")

    # Distributors
    print("\nDISTRIBUTORS:")
    distributors = graph.get_nodes_by_type("distributor")
    for dist_id, dist in distributors.items():
        loc = dist.location
        nearest_center, distance = graph.find_nearest_center(dist_id)
        nearest_name = graph.get_node(nearest_center).name
        print(f"  • {dist.name}")
        print(f"    Location: {loc['city']}, {loc['state']}")
        print(f"    Nearest Center: {nearest_name} ({distance:.1f} miles)")
        print(f"    State: {dist.get_state_summary()}")

    # Connections
    print("\nCONNECTIONS:")
    print(f"  Total edges: {len(graph.edges)}")
    print(
        f"  Average distance: {sum(e['distance_miles'] for e in graph.edges) / len(graph.edges):.1f} miles"
    )

    print("\n" + "=" * 60)


if __name__ == "__main__":
    # Load and display the graph
    graph = load_graph_from_data()
    print_graph_summary(graph)

    # Example: Find nearest center for each distributor
    print("\nROUTING ANALYSIS:")
    distributors = graph.get_nodes_by_type("distributor")
    for dist_id, dist in distributors.items():
        nearest_center, distance = graph.find_nearest_center(dist_id)
        dist_name = dist.name
        center_name = graph.get_node(nearest_center).name
        print(f"  {dist_name} -> {center_name} ({distance:.1f} mi)")
