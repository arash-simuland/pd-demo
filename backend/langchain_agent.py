"""
langchain_agent.py - LangChain Agent for Simulation Control

Uses LangChain with Ollama for sophisticated natural language control
with proper tool calling and verification.
"""

import importlib
import json
import re
import sys
from pathlib import Path
from typing import Any, Dict

from langchain.tools import tool
from langchain_community.chat_models import ChatOllama


# Add src to path for action imports
sys.path.append(str(Path(__file__).parent.parent / "src"))

# Global reference to graph and simulation (set by API)
_graph = None
_simulation = None


def initialize_agent(graph, simulation):
    """Initialize the LangChain agent with graph and simulation references"""
    global _graph, _simulation
    _graph = graph
    _simulation = simulation


# =============================================================================
# SIMULATION TOOLS
# =============================================================================


@tool
def set_production_rate(input_str: str) -> str:
    """Set production rate for a manufacturing center. Input format: 'center_name, rate' or 'center_name rate' (e.g. 'chicago 20' or 'chicago, 20')"""
    if not _graph or not _simulation:
        return "Error: Agent not initialized"

    # Parse input - handle various formats
    import re

    # Remove quotes and extra spaces
    input_str = input_str.replace("'", "").replace('"', "").strip()

    # Try to extract center name and rate
    parts = re.split(r"[,\s]+", input_str)
    if len(parts) < 2:
        return f"Error: Invalid input '{input_str}'. Expected format: 'center_name rate' (e.g., 'chicago 20')"

    center_name = parts[0].lower().strip()
    try:
        rate = int(parts[1])
    except (ValueError, IndexError):
        return f"Error: Could not parse rate from '{input_str}'"

    # Dynamically find center by name (supports both original and dynamically added centers)
    centers = _graph.get_nodes_by_type("manufacturing_center")
    center_id = None

    for cid, node in centers.items():
        # Match by city name (e.g., "Chicago Manufacturing Center" matches "chicago")
        city_name = node.location.get("city", "").lower()
        if city_name == center_name:
            center_id = cid
            break

    if not center_id:
        available = [node.location.get("city", "").lower() for node in centers.values()]
        return f"Error: Unknown center '{center_name}'. Available: {', '.join(available)}"

    node = _graph.nodes.get(center_id)
    if not node:
        return f"Error: Center {center_id} not found in graph"

    # Import the action
    try:
        # Import using path manipulation for kebab-case module name
        actions_path = Path(__file__).parent.parent / "src" / "actions"
        sys.path.insert(0, str(actions_path))
        manufacturing_actions = importlib.import_module("manufacturing-actions")
        sys.path.pop(0)
        change_production_rate = manufacturing_actions.change_production_rate
    except Exception as e:
        return f"Error importing action: {e}"

    # Schedule the rate change action (SimPy process)
    try:
        old_rate = node.state.get("production_rate", 0)
        process = _simulation.env.process(change_production_rate(node, rate))

        # Immediate state update for UI feedback
        node.state["target_rate"] = rate
        node.state["machine_state"] = "adjusting"

        return f"✓ Scheduled rate change for {node.name} from {old_rate} to {rate} units/hr (will complete in 2 simulation hours)"
    except Exception as e:
        return f"Error scheduling rate change: {e}"


@tool
def show_center_status(center_name: str) -> str:
    """Show current status of a manufacturing center. Input: center name (chicago, pittsburgh, or nashville)"""
    if not _graph:
        return "Error: Agent not initialized"

    # Clean input
    center_name = center_name.replace("'", "").replace('"', "").strip().lower()

    # Dynamically find center by name (supports both original and dynamically added centers)
    centers = _graph.get_nodes_by_type("manufacturing_center")
    center_id = None

    for cid, node in centers.items():
        # Match by city name (e.g., "Chicago Manufacturing Center" matches "chicago")
        city_name = node.location.get("city", "").lower()
        if city_name == center_name:
            center_id = cid
            break

    if not center_id:
        available = [node.location.get("city", "").lower() for node in centers.values()]
        return f"Error: Unknown center '{center_name}'. Available: {', '.join(available)}"

    node = _graph.nodes.get(center_id)
    if not node:
        return "Error: Center not found"

    # Format status
    state = node.state
    status_lines = [
        f"📊 **{node.name}** Status:",
        f"• Production Rate: {state.get('production_rate', 0)} units/hr",
        f"• Inventory: {state.get('inventory', 0)} units",
        f"• Machine State: {state.get('machine_state', 'unknown')}",
        f"• Total Produced: {state.get('total_produced', 0)} units",
        f"• Pending Orders: {len(state.get('pending_orders', []))}",
        f"• Orders Fulfilled: {state.get('total_orders_fulfilled', 0)}",
    ]

    # Add financial metrics if available
    revenue = state.get("total_revenue", 0)
    costs = state.get("total_production_costs", 0)
    if revenue > 0 or costs > 0:
        profit = revenue - costs
        margin = (profit / revenue * 100) if revenue > 0 else 0
        status_lines.extend(
            [
                f"• Revenue: ${revenue:,.2f}",
                f"• Costs: ${costs:,.2f}",
                f"• Profit: ${profit:,.2f} ({margin:.1f}% margin)",
            ]
        )

    return "\n".join(status_lines)


@tool
def resume_all_production() -> str:
    """
    Resume production at all manufacturing centers to default rate (10 units/hr).

    Returns:
        Status message for all centers
    """
    if not _graph or not _simulation:
        return "Error: Agent not initialized"

    centers = _graph.get_nodes_by_type("manufacturing_center")
    results = []

    # Import the action
    try:
        # Import using path manipulation for kebab-case module name
        actions_path = Path(__file__).parent.parent / "src" / "actions"
        sys.path.insert(0, str(actions_path))
        manufacturing_actions = importlib.import_module("manufacturing-actions")
        sys.path.pop(0)
        change_production_rate = manufacturing_actions.change_production_rate
    except Exception as e:
        return f"Error importing action: {e}"

    for center_id, center in centers.items():
        try:
            old_rate = center.state.get("production_rate", 0)
            process = _simulation.env.process(change_production_rate(center, 10))

            # Immediate state update
            center.state["target_rate"] = 10
            center.state["machine_state"] = "adjusting"

            results.append(f"✓ {center.name}: {old_rate} → 10 units/hr")
        except Exception as e:
            results.append(f"✗ {center.name}: Error - {e}")

    return "Resumed production for all centers:\n" + "\n".join(results)


@tool
def get_simulation_stats() -> str:
    """
    Get overall simulation statistics.

    Returns:
        Formatted statistics for the entire simulation
    """
    if not _graph or not _simulation:
        return "Error: Agent not initialized"

    centers = _graph.get_nodes_by_type("manufacturing_center")
    distributors = _graph.get_nodes_by_type("distributor")

    total_inventory = sum(c.state.get("inventory", 0) for c in centers.values())
    total_produced = sum(c.state.get("total_produced", 0) for c in centers.values())
    total_orders_placed = sum(d.state.get("orders_placed", 0) for d in distributors.values())
    total_fulfilled = sum(c.state.get("total_orders_fulfilled", 0) for c in centers.values())
    total_pending = sum(len(c.state.get("pending_orders", [])) for c in centers.values())

    # Financial totals
    total_revenue = sum(c.state.get("total_revenue", 0) for c in centers.values())
    total_costs = sum(c.state.get("total_production_costs", 0) for c in centers.values())
    total_profit = total_revenue - total_costs

    stats = [
        f"📈 **Simulation Statistics** (t={_simulation.env.now:.2f} hrs)",
        "",
        "**Production:**",
        f"• Total Inventory: {total_inventory} units",
        f"• Total Produced: {total_produced} units",
        "",
        "**Orders:**",
        f"• Orders Placed: {total_orders_placed}",
        f"• Orders Fulfilled: {total_fulfilled}",
        f"• Pending Orders: {total_pending}",
        "",
        "**Financials:**",
        f"• Total Revenue: ${total_revenue:,.2f}",
        f"• Total Costs: ${total_costs:,.2f}",
        f"• Total Profit: ${total_profit:,.2f}",
    ]

    return "\n".join(stats)


@tool
def add_distributor(input_str: str) -> str:
    """Add a new distributor to the simulation. Input format: 'city, state' or 'city state' (e.g., 'Dallas, TX' or 'Dallas TX')"""
    if not _graph or not _simulation:
        return "Error: Agent not initialized"

    # Parse input
    input_str = input_str.replace("'", "").replace('"', "").strip()

    # Try to split by comma first, then by space
    if "," in input_str:
        parts = [p.strip() for p in input_str.split(",")]
    else:
        parts = input_str.split()

    if len(parts) < 2:
        return f"Error: Invalid input '{input_str}'. Expected format: 'city, state' (e.g., 'Dallas, TX')"

    city = parts[0].strip()
    state = parts[1].strip()

    try:
        # Add distributor dynamically
        new_node = _graph.add_distributor_dynamically(city, state)

        # Count connected centers
        centers = _graph.get_nodes_by_type("manufacturing_center")

        result = [
            f"✓ Created {new_node.name}",
            f"• Location: {city}, {state}",
            f"• Coordinates: ({new_node.location['lat']:.4f}, {new_node.location['lon']:.4f})",
            f"• Connected to {len(centers)} manufacturing centers",
            "• Order generation: Active",
            "",
            "The new distributor is now visible on the map and generating orders.",
        ]

        return "\n".join(result)

    except ValueError as e:
        return f"Error: {e!s}"
    except Exception as e:
        return f"Error creating distributor: {e!s}"


@tool
def add_manufacturer(input_str: str) -> str:
    """Add a new manufacturing center to the simulation. Input format: 'city, state' or 'city state' (e.g., 'Atlanta, GA' or 'Atlanta GA')"""
    if not _graph or not _simulation:
        return "Error: Agent not initialized"

    # Parse input
    input_str = input_str.replace("'", "").replace('"', "").strip()

    # Try to split by comma first, then by space
    if "," in input_str:
        parts = [p.strip() for p in input_str.split(",")]
    else:
        parts = input_str.split()

    if len(parts) < 2:
        return f"Error: Invalid input '{input_str}'. Expected format: 'city, state' (e.g., 'Atlanta, GA')"

    city = parts[0].strip()
    state = parts[1].strip()

    try:
        # Add manufacturer dynamically
        new_node = _graph.add_manufacturer_dynamically(city, state)

        # Count connected distributors
        distributors = _graph.get_nodes_by_type("distributor")

        result = [
            f"✓ Created {new_node.name}",
            f"• Location: {city}, {state}",
            f"• Coordinates: ({new_node.location['lat']:.4f}, {new_node.location['lon']:.4f})",
            f"• Capacity: {new_node.properties['capacity']} units",
            f"• Production Rate: {new_node.properties['initial_production_rate']} units/hr",
            f"• Initial Inventory: {new_node.state['inventory']} units",
            f"• Connected to {len(distributors)} distributors",
            "",
            "The new manufacturing center is now operational on the map.",
        ]

        return "\n".join(result)

    except ValueError as e:
        return f"Error: {e!s}"
    except Exception as e:
        return f"Error creating manufacturer: {e!s}"


# =============================================================================
# SIMPLIFIED JSON-BASED COMMAND EXTRACTION
# =============================================================================

# Map tools for easy access
TOOL_MAP = {
    "set_production_rate": set_production_rate,
    "show_center_status": show_center_status,
    "resume_all_production": resume_all_production,
    "get_simulation_stats": get_simulation_stats,
    "add_distributor": add_distributor,
    "add_manufacturer": add_manufacturer,
}


def extract_command_with_llm(user_message: str) -> Dict[str, Any]:
    """
    Use Ollama to extract structured command from natural language.

    Returns JSON like:
    {"action": "set_production_rate", "args": "chicago 20", "response_text": "Setting Chicago to 20..."}
    or
    {"action": null, "response_text": "conversational response"}
    """
    llm = ChatOllama(
        model="mistral:latest",
        temperature=0.3,
        num_predict=200,
        format="json",  # Request JSON output
    )

    system_prompt = """You are a command parser for a manufacturing simulation. Extract the user's intent and return ONLY valid JSON.

Available commands:
- set_production_rate: Change production rate (e.g., "increase chicago to 20" → {"action": "set_production_rate", "args": "chicago 20"})
- show_center_status: Show center status (e.g., "show chicago status" → {"action": "show_center_status", "args": "chicago"})
- resume_all_production: Resume all centers (e.g., "resume all" → {"action": "resume_all_production", "args": ""})
- get_simulation_stats: Get overall stats (e.g., "show stats" → {"action": "get_simulation_stats", "args": ""})
- add_distributor: Add a new distributor (e.g., "add distributor in Dallas TX" → {"action": "add_distributor", "args": "Dallas TX"})
- add_manufacturer: Add a new manufacturing center (e.g., "add manufacturer in Atlanta GA" → {"action": "add_manufacturer", "args": "Atlanta GA"})

If no command detected, return: {"action": null, "args": "", "response": "conversational response"}

Return ONLY JSON, no other text."""

    try:
        prompt = f"{system_prompt}\n\nUser message: {user_message}\n\nJSON:"
        result = llm.invoke(prompt)

        # Extract JSON from response
        response_text = result.content if hasattr(result, "content") else str(result)

        # Try to parse JSON
        # Sometimes LLM adds extra text, so extract JSON block
        json_match = re.search(r"\{[^{}]*\}", response_text, re.DOTALL)
        if json_match:
            command_json = json.loads(json_match.group())
            return command_json
        # No JSON found, treat as conversational
        return {"action": None, "args": "", "response": response_text}

    except Exception as e:
        print(f"[LLM] Error extracting command: {e}")
        return {
            "action": None,
            "args": "",
            "response": "I couldn't understand that command. Try 'increase chicago production to 20' or 'show chicago status'.",
        }


# =============================================================================
# MAIN INTERFACE
# =============================================================================


def process_message(message: str) -> Dict[str, Any]:
    """
    Process a user message using simplified JSON command extraction.

    Args:
        message: User's natural language input

    Returns:
        Dictionary with response and metadata
    """
    try:
        # Extract command using LLM
        command = extract_command_with_llm(message)

        action_name = command.get("action")
        args = command.get("args", "")

        # If no action, return conversational response
        if not action_name or action_name == "null":
            return {
                "response": command.get(
                    "response",
                    "I'm here to help control the simulation. Try 'increase chicago production to 20' or 'show status'.",
                ),
                "success": True,
            }

        # Get the tool function
        tool_func = TOOL_MAP.get(action_name)
        if not tool_func:
            return {"response": f"Unknown command: {action_name}", "success": False}

        # Call the tool
        try:
            if args:
                result = tool_func.invoke(args)
            else:
                result = tool_func.invoke("")

            return {"response": result, "success": True, "action_executed": action_name}
        except Exception as e:
            return {"response": f"Error executing {action_name}: {e!s}", "success": False}

    except Exception as e:
        print(f"[Agent] Error: {e}")
        return {"response": f"Error processing message: {e!s}", "success": False, "error": str(e)}
