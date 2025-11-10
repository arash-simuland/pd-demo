"""
api.py - FastAPI Backend for Zurvan Visualization

Replaces Dash with a modern FastAPI + WebSocket architecture.
Keeps all SimPy simulation logic unchanged.
"""

import asyncio
import importlib
import sys
from pathlib import Path

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

# Import LangChain agent
from langchain_agent import initialize_agent, process_message
from pydantic import BaseModel


# Add src to path
sys.path.append(str(Path(__file__).parent.parent / "src"))

# Import simulation modules
graph_builder = importlib.import_module("graph-builder")
simulation_module = importlib.import_module("simulation")

load_graph_from_data = graph_builder.load_graph_from_data
ProductDeliverySimulation = simulation_module.ProductDeliverySimulation

# =============================================================================
# GLOBAL STATE
# =============================================================================

# Load graph and create simulation
graph = load_graph_from_data()
simulation = ProductDeliverySimulation(graph)

print(f"[FastAPI] Loaded graph with {len(graph.nodes)} nodes")
print(f"[FastAPI] Simulation initialized at t={simulation.env.now}")

# Initialize LangChain agent with graph and simulation
initialize_agent(graph, simulation)
print("[FastAPI] LangChain agent initialized")

# Simulation state
sim_state = {"running": False, "speed": 1.0, "processes_started": False}

# =============================================================================
# FASTAPI APP
# =============================================================================

app = FastAPI(title="Zurvan Product Delivery API")

# CORS middleware for development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# =============================================================================
# REST API ENDPOINTS
# =============================================================================


@app.get("/api/status")
async def get_status():
    """Get current simulation status"""
    return {
        "running": sim_state["running"],
        "speed": sim_state["speed"],
        "time": simulation.env.now,
        "processes_started": sim_state["processes_started"],
    }


@app.post("/api/control/play")
async def play():
    """Start simulation"""
    # Start processes on first play
    if not sim_state["processes_started"]:
        simulation.start_all_processes()
        sim_state["processes_started"] = True
        print("[API] Processes started")

    sim_state["running"] = True
    print("[API] Simulation playing")
    return {"status": "playing"}


@app.post("/api/control/pause")
async def pause():
    """Pause simulation"""
    sim_state["running"] = False
    print("[API] Simulation paused")
    return {"status": "paused"}


@app.post("/api/control/reset")
async def reset():
    """Reset simulation"""
    simulation.reset()

    # Reset Order class ID counter
    from order import Order

    Order._next_id = 1

    sim_state["running"] = False
    sim_state["processes_started"] = False
    print("[API] Simulation reset")
    return {"status": "reset", "time": 0}


@app.post("/api/control/speed")
async def set_speed(speed: float):
    """Set simulation speed"""
    sim_state["speed"] = max(0.1, min(10.0, speed))
    print(f"[API] Speed set to {sim_state['speed']}x")
    return {"speed": sim_state["speed"]}


# =============================================================================
# CHAT ENDPOINT (LangChain + Ollama Integration)
# =============================================================================


class ChatRequest(BaseModel):
    message: str


@app.post("/api/chat")
async def chat(request: ChatRequest):
    """
    Chat endpoint that uses LangChain with Ollama Mistral for natural language control.

    Uses tool calling for proper action execution and verification.
    """
    user_message = request.message
    print(f"[Chat] Received: {user_message}")

    try:
        # Process message using LangChain agent
        result = process_message(user_message)

        if result["success"]:
            return {
                "response": result["response"],
                "action_executed": None,  # Tools handle execution confirmation
            }
        return {"response": result["response"], "action_executed": None}

    except Exception as e:
        print(f"[Chat] Error: {e}")
        return {"response": f"Error processing your message: {e!s}", "action_executed": None}


# =============================================================================
# WEBSOCKET ENDPOINT
# =============================================================================


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint for real-time simulation state updates.

    Sends simulation state to client every 100ms (10 fps).
    """
    await websocket.accept()
    print("[WebSocket] Client connected")

    try:
        while True:
            # Run simulation if playing
            if sim_state["running"]:
                # Time-step mode: advance by 0.1 * speed simulation hours
                speed = sim_state["speed"]
                time_step = 0.1 * speed

                prev_time = simulation.env.now
                simulation.run_step(time_step)

                if simulation.env.now > prev_time:
                    print(
                        f"[Animation] Time: {prev_time:.2f} -> {simulation.env.now:.2f} hrs (+{time_step:.2f}hrs @ {speed}x speed)"
                    )

            # Prepare state for transmission
            state = get_simulation_state()

            # Send to client
            await websocket.send_json(state)

            # Update rate: 10 fps (100ms interval)
            await asyncio.sleep(0.1)

    except WebSocketDisconnect:
        print("[WebSocket] Client disconnected")
    except Exception as e:
        print(f"[WebSocket] Error: {e}")


def get_simulation_state():
    """
    Get current simulation state in JSON-serializable format.
    """
    # Get nodes
    nodes = []
    for node_id, node in graph.nodes.items():
        # Serialize state (convert Order objects to dicts)
        serialized_state = {}
        for key, value in node.state.items():
            # Check if this is a list of Order objects
            if key in ["pending_orders", "in_delivery", "orders_in_delivery"]:
                # Convert Order objects to dictionaries
                serialized_state[key] = [order.to_dict() for order in value]
            elif isinstance(value, list) and len(value) > 0 and hasattr(value[0], "to_dict"):
                # Handle any other list of objects with to_dict method
                serialized_state[key] = [item.to_dict() for item in value]
            else:
                serialized_state[key] = value

        node_data = {
            "id": node_id,
            "type": node.node_type,
            "name": node.name,
            "location": node.location,
            "properties": node.properties,  # Include properties for sourcing policy, etc.
            "state": serialized_state,
            "color": node.get_color(),
        }
        nodes.append(node_data)

    # Get edges - show structural topology + order placement + delivery routes
    edges = []

    # 0. Structural edges (gray background showing network topology)
    # Add ALL graph edges as base layer
    for graph_edge in graph.edges:
        if graph_edge["type"] == "distributor_to_center":
            edge_data = {
                "from": graph_edge["from"],
                "to": graph_edge["to"],
                "distance": graph_edge.get("distance_miles", 0),
                "edge_type": "structural",  # Base topology edge
            }
            edges.append(edge_data)

    # 1. Order placement edges (distributor → manufacturer) - flash when recently placed
    centers = graph.get_nodes_by_type("manufacturing_center")
    current_time = simulation.env.now

    for center_id, center in centers.items():
        pending_orders = center.state.get("pending_orders", [])

        # Group by distributor - only show orders placed in last 0.1 simulation hours
        distributor_recent = {}
        for order in pending_orders:
            time_since_placement = current_time - order.placement_time
            if time_since_placement <= 0.1:  # Only orders placed in last 0.1 hours (brief flash)
                dist_id = order.distributor_id
                if dist_id not in distributor_recent:
                    distributor_recent[dist_id] = []
                distributor_recent[dist_id].append(order)

        # Create edge for each distributor with recently placed orders
        for dist_id, orders in distributor_recent.items():
            # Find the edge with distance info
            distance = 0
            for edge in graph.edges:
                if edge["from"] == dist_id and edge["to"] == center_id:
                    distance = edge.get("distance_miles", 0)
                    break

            edge_data = {
                "from": dist_id,
                "to": center_id,
                "distance": distance,
                "edge_type": "order_placement",  # Recently placed orders (flash)
                "active_orders": len(orders),
            }
            edges.append(edge_data)

    # 2. Delivery edges (manufacturer → distributor) - with animated particles
    centers = graph.get_nodes_by_type("manufacturing_center")
    for center_id, center in centers.items():
        in_delivery = center.state.get("in_delivery", [])

        # Group by distributor
        distributor_orders = {}
        for order in in_delivery:
            dist_id = order.distributor_id
            if dist_id not in distributor_orders:
                distributor_orders[dist_id] = []
            distributor_orders[dist_id].append(order)

        # Create edge for each distributor with active deliveries
        for dist_id, orders in distributor_orders.items():
            # Send individual timing for each order so frontend can render multiple particles
            first_order = orders[0] if orders else None

            edge_data = {
                "from": center_id,
                "to": dist_id,
                "distance": first_order.routing_distance if first_order else 0,
                "edge_type": "delivery",  # Delivery edge with animation
                "active_orders": len(orders),
                # Array of individual order timings for multiple particles
                "deliveries": [
                    {
                        "order_id": order.id,
                        "start_time": order.delivery_start_time,
                        "duration": order.delivery_duration,
                        "arrival_time": order.delivery_arrival_time,
                    }
                    for order in orders
                ],
            }
            edges.append(edge_data)

    # Calculate statistics
    centers = graph.get_nodes_by_type("manufacturing_center")
    distributors = graph.get_nodes_by_type("distributor")

    total_inventory = sum(c.state.get("inventory", 0) for c in centers.values())
    total_orders_placed = sum(d.state.get("orders_placed", 0) for d in distributors.values())
    total_fulfilled = sum(c.state.get("total_orders_fulfilled", 0) for c in centers.values())
    total_pending = sum(len(c.state.get("pending_orders", [])) for c in centers.values())

    return {
        "time": simulation.env.now,
        "running": sim_state["running"],
        "speed": sim_state["speed"],
        "nodes": nodes,
        "edges": edges,
        "stats": {
            "total_inventory": total_inventory,
            "orders_placed": total_orders_placed,
            "orders_fulfilled": total_fulfilled,
            "pending_orders": total_pending,
        },
    }


# =============================================================================
# MAIN
# =============================================================================

if __name__ == "__main__":
    import uvicorn

    print("\n" + "=" * 60)
    print("Zurvan Product Delivery - FastAPI Backend")
    print("=" * 60)
    print(f"Nodes loaded: {len(graph.nodes)}")
    print(f"Manufacturing centers: {len(graph.get_nodes_by_type('manufacturing_center'))}")
    print(f"Distributors: {len(graph.get_nodes_by_type('distributor'))}")
    print("\nStarting FastAPI server...")
    print("API: http://127.0.0.1:8000")
    print("WebSocket: ws://127.0.0.1:8000/ws")
    print("=" * 60 + "\n")

    uvicorn.run(app, host="127.0.0.1", port=8000)
