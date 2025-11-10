"""
simulation.py - Step 4: Simulation Wrapper Class

Wraps the graph + SimPy environment to enable action execution.
This follows SimPy Pattern 2a: Simulation class encapsulating environment.

Step 4: Manual action execution (click buttons to trigger actions)
Step 5: Automatic process activation (continuous processes run automatically)
"""

from datetime import datetime
from typing import Any, Dict, List

import simpy


class ActionLog:
    """
    Tracks executed actions for visualization and debugging.

    Each log entry records what action was executed, when, on which resources,
    and what state changes occurred.
    """

    def __init__(self):
        self.entries = []

    def log_action(
        self,
        sim_time: float,
        action_name: str,
        node_id: str,
        parameters: Dict[str, Any],
        result: Any = None,
    ):
        """
        Log an executed action.

        Args:
            sim_time: Simulation time when action executed
            action_name: Name of the action (e.g., 'change_production_rate')
            node_id: ID of the node the action was performed on
            parameters: Dictionary of parameters passed to action
            result: Return value from action (if any)
        """
        entry = {
            "sim_time": sim_time,
            "real_time": datetime.now().strftime("%H:%M:%S"),
            "action_name": action_name,
            "node_id": node_id,
            "parameters": parameters,
            "result": result,
        }
        self.entries.append(entry)

    def get_recent(self, n: int = 10) -> List[Dict[str, Any]]:
        """Get n most recent log entries"""
        return self.entries[-n:]

    def get_all(self) -> List[Dict[str, Any]]:
        """Get all log entries"""
        return self.entries

    def clear(self):
        """Clear all log entries"""
        self.entries = []


class ProductDeliverySimulation:
    """
    Simulation wrapper for product delivery model.

    Encapsulates:
    - SimPy environment (discrete event simulation engine)
    - Graph of nodes (resource network)
    - Action log (history of executed actions)
    - Manual action execution methods (Step 4)
    - Automatic process activation (Step 5 - not yet implemented)

    In Zurvan terms, this is a "Scenario" - a specific configuration of
    the model with an environment and initial conditions.
    """

    def __init__(self, graph, realtime_factor: float = 0.1):
        """
        Initialize simulation.

        Args:
            graph: ZurvanGraph with ResourceNode objects
            realtime_factor: Speed of simulation relative to real time
                (e.g., 0.1 = 10x slower than real time for visualization)
        """
        # Create SimPy environment
        # For Step 4-5, we use RealtimeEnvironment for visualization
        # (actions execute at human-observable speeds)
        self.env = simpy.Environment()  # Standard environment for now
        # Note: Will switch to RealtimeEnvironment in Step 5 for continuous processes

        self.graph = graph
        self.action_log = ActionLog()
        self.active_processes = []  # List of running SimPy processes

        # Attach environment to graph AND all nodes
        self.graph.env = self.env  # Critical: allows dynamic node creation to work
        for node in self.graph.nodes.values():
            node.env = self.env

        print(f"[Simulation] Created with {len(self.graph.nodes)} nodes")
        print(f"[Simulation] Environment time: {self.env.now}")

    # -------------------------------------------------------------------------
    # Step 4: Manual Action Execution
    # These methods allow triggering actions manually (one at a time)
    # -------------------------------------------------------------------------

    def execute_change_production_rate(
        self, center_id: str, new_rate: float, adjustment_time: float = 2.0
    ):
        """
        Manually execute: Change production rate for a manufacturing center.

        This is a manual trigger for testing. In Step 5, this will be called
        automatically by policies/controllers.

        Args:
            center_id: ID of manufacturing center
            new_rate: Target production rate (units/hour)
            adjustment_time: Time to complete rate change (default 2 hours)

        Returns:
            True if action completed successfully
        """
        from actions import change_production_rate

        center = self.graph.get_node(center_id)
        if not center:
            print(f"[Error] Node {center_id} not found")
            return False

        print(f"[Action] Changing rate for {center.name} to {new_rate} units/hr")

        # Create and run the process
        process = self.env.process(change_production_rate(center, new_rate, adjustment_time))

        # Run simulation until process completes
        self.env.run(until=process)

        # Log the action
        self.action_log.log_action(
            sim_time=self.env.now,
            action_name="change_production_rate",
            node_id=center_id,
            parameters={"new_rate": new_rate, "adjustment_time": adjustment_time},
            result="completed",
        )

        print(f"[Simulation] Time advanced to {self.env.now}")
        print(f"[State] {center.name} rate now: {center.state['production_rate']} units/hr")

        return True

    def execute_fulfill_order(
        self, center_id: str, order_quantity: int, fulfillment_time: float = 0.1
    ):
        """
        Manually execute: Fulfill an order from manufacturing center inventory.

        Args:
            center_id: ID of manufacturing center
            order_quantity: Number of units to fulfill
            fulfillment_time: Time to process fulfillment (default 0.1 hours)

        Returns:
            True if order fulfilled, False if insufficient inventory
        """
        from actions import fulfill_order

        center = self.graph.get_node(center_id)
        if not center:
            print(f"[Error] Node {center_id} not found")
            return False

        print(f"[Action] Fulfilling order of {order_quantity} units from {center.name}")
        print(f"[State] Current inventory: {center.state['inventory']} units")

        # Create and run the process
        process = self.env.process(fulfill_order(center, order_quantity, fulfillment_time))

        # Run simulation until process completes
        self.env.run(until=process)

        # Get result from process
        result = process.value

        # Log the action
        self.action_log.log_action(
            sim_time=self.env.now,
            action_name="fulfill_order",
            node_id=center_id,
            parameters={"order_quantity": order_quantity, "fulfillment_time": fulfillment_time},
            result="fulfilled" if result else "insufficient_inventory",
        )

        print(f"[Simulation] Time advanced to {self.env.now}")
        if result:
            print(
                f"[Result] Order fulfilled! Remaining inventory: {center.state['inventory']} units"
            )
        else:
            print("[Result] Order could not be fulfilled (insufficient inventory)")

        return result

    def produce_units(self, center_id: str, num_units: int = 1):
        """
        Manually produce units (simplified for Step 4 testing).

        This is a simplified version for manual testing. The full
        continuous_production process will run automatically in Step 5.

        Args:
            center_id: ID of manufacturing center
            num_units: Number of units to produce
        """
        center = self.graph.get_node(center_id)
        if not center:
            print(f"[Error] Node {center_id} not found")
            return False

        print(f"[Action] Manually producing {num_units} units at {center.name}")

        # Directly update state (no time passage for manual production)
        center.state["inventory"] += num_units
        center.state["total_produced"] += num_units

        # Log the action
        self.action_log.log_action(
            sim_time=self.env.now,
            action_name="produce_units",
            node_id=center_id,
            parameters={"num_units": num_units},
            result="completed",
        )

        print(f"[State] {center.name} inventory now: {center.state['inventory']} units")

        return True

    # -------------------------------------------------------------------------
    # Step 5: Automatic Process Activation
    # -------------------------------------------------------------------------

    def start_all_processes(self):
        """
        Start all automatic processes.

        Nodes are now autonomous agents that start their own actions.
        The simulation environment simply tells each node to start.

        Each node:
        - Knows what actions it can perform (registered in node.actions)
        - Knows which actions auto-start (node.automatic_actions)
        - Starts its own processes from within (node.start())
        """
        # Tell each node to start its automatic actions
        process_count = 0
        for node in self.graph.nodes.values():
            initial_count = len(node.active_processes)
            node.start()
            processes_started = len(node.active_processes) - initial_count

            # Print what each node started
            for proc_info in node.active_processes[initial_count:]:
                print(f"[Process] Started {proc_info['name']} for {node.name}")
                process_count += 1

        print(f"[Simulation] {process_count} processes activated")

    def run_step(self, time_step: float = 0.1):
        """
        Run simulation forward - either to next event or by time step.

        This is called repeatedly by the Dash interval callback when
        simulation is in "play" mode.

        Args:
            time_step: Maximum simulation time to advance (default 0.1 hours = 6 minutes)
                      If None, runs to next event
        """
        try:
            if time_step is None:
                # Event-driven: run to next event (no time limit)
                # SimPy will process the next event and stop
                self.env.step()
            else:
                # Time-driven: run until env.now + time_step
                # SimPy will process all events up to that time
                self.env.run(until=self.env.now + time_step)
        except StopIteration:
            # Simulation has no more events
            print("[Simulation] No more events to process")
        except Exception as e:
            print(f"[Simulation] ERROR in run_step: {type(e).__name__}: {e}")
            import traceback

            traceback.print_exc()

    def run_to_next_event(self):
        """
        Run simulation to the next event (event-driven mode).

        This processes exactly one event and stops, allowing the clock
        to jump directly from event to event.
        """
        try:
            self.env.step()
        except (StopIteration, Exception):
            # No more events or empty schedule - this is OK
            # EmptySchedule happens when processes haven't started yet
            pass

    def is_running(self) -> bool:
        """Check if any processes are active"""
        return len(self.active_processes) > 0

    # -------------------------------------------------------------------------
    # Utility Methods
    # -------------------------------------------------------------------------

    def get_state_snapshot(self) -> Dict[str, Any]:
        """Get current state of all nodes"""
        return {node_id: node.to_dict() for node_id, node in self.graph.nodes.items()}

    def reset(self):
        """Reset simulation to initial state"""
        # Stop all running processes first
        for node in self.graph.nodes.values():
            node.stop()  # Stop and clear all active processes
        
        # Recreate environment
        self.env = simpy.Environment()

        # Attach environment to graph (for dynamic node creation)
        self.graph.env = self.env

        # Reset all node states to initial values
        for node in self.graph.nodes.values():
            node.env = self.env
            node.reset_state()  # Reset to initial state
            # Ensure active_processes is cleared (stop() should do this, but be explicit)
            node.active_processes = []

        # Clear logs
        self.action_log.clear()
        self.active_processes = []

        print("[Simulation] Reset to time 0")
