"""
Rescue simulation and dynamic replanning engine for RescueGrid (Phase 9.3).

Coordinates:
1. Disaster environment (ActualGrid vs. KnowledgeGrid).
2. Incident management (creation, registration, prioritization, resolution).
3. Responder and vehicle availability and specialization matching.
4. CSP-based multi-agent resource allocation.
5. Pathfinding using configurable algorithms (A*, UCS, BFS, DFS, Hill Climbing).
6. Discrete vehicle locomotion (moving strictly one grid cell per step without teleportation).
7. Proximity sensor-based environmental discovery.
8. Dynamic replanning upon obstacle detection.
9. Incident resolution with configurable service duration.
10. Atomic resource release and lifecycle synchronization.
"""

import time
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Set, Tuple, Union

from models.position import Position
from models.incident import Incident, IncidentStatus, IncidentType
from models.responder import Responder, ResponderSpecialization
from models.rescue_vehicle import RescueVehicle, VehicleType
from core.rescue_manager import RescueManager
from environment.cell import Cell, TerrainType
from environment.grid import Grid
from environment.actual_grid import ActualGrid
from environment.knowledge_grid import KnowledgeGrid
from algorithms.search_result import SearchResult
from algorithms.astar import astar
from algorithms.ucs import ucs
from algorithms.bfs import bfs
from algorithms.dfs import dfs
from algorithms.hill_climbing import hill_climbing
from algorithms.csp import CSPSolver, CSPResult
from simulation.sensor import Sensor


# Standard planner mapping for configurable pathfinding
DEFAULT_PLANNERS: Dict[str, Callable[[Grid, Position, Position], SearchResult]] = {
    "astar": astar,
    "a*": astar,
    "ucs": ucs,
    "uniform_cost": ucs,
    "bfs": bfs,
    "breadth_first": bfs,
    "dfs": dfs,
    "depth_first": dfs,
    "hill_climbing": hill_climbing,
    "hc": hill_climbing,
}


@dataclass
class SimulationEvent:
    """Structured record of a single simulation lifecycle event.

    Attributes:
        step: Simulation tick index at which the event occurred.
        event_type: Category identifier ('INCIDENT_CREATED', 'INCIDENT_PRIORITIZED',
                    'RESOURCES_ALLOCATED', 'ROUTE_CALCULATED', 'VEHICLE_MOVEMENT',
                    'HAZARD_DISCOVERED', 'ROUTE_REPLANNED', 'VEHICLE_ARRIVED',
                    'RESCUE_IN_PROGRESS', 'INCIDENT_RESOLVED', 'RESOURCES_RELEASED',
                    'MISSION_FAILED', 'SIMULATION_START', 'SIMULATION_COMPLETE').
        description: Informative human-readable event description.
        incident_id: Identifier of the associated incident, if applicable.
        vehicle_id: Identifier of the involved rescue vehicle, if applicable.
        responder_id: Identifier of the assigned responder, if applicable.
        position: Grid coordinates associated with the event, if applicable.
        timestamp: System wall-clock time (seconds) of the event.
    """
    step: int
    event_type: str
    description: str
    incident_id: Optional[str] = None
    vehicle_id: Optional[str] = None
    responder_id: Optional[str] = None
    position: Optional[Position] = None
    timestamp: float = field(default_factory=time.time)

    def to_string(self) -> str:
        pos_str = f" @ ({self.position.x}, {self.position.y})" if self.position is not None else ""
        return f"[Step {self.step:03d}] {self.event_type:<22} | {self.description}{pos_str}"

    def __repr__(self) -> str:
        return f"SimulationEvent(step={self.step}, type='{self.event_type}', desc='{self.description}')"


@dataclass
class MissionResult:
    """Outcome of an individual vehicle dispatch mission to an incident.

    Attributes:
        incident_id: Identifier of the target incident.
        vehicle_id: Identifier of the dispatched vehicle.
        responder_id: Identifier of the assigned responder.
        success: Whether the mission reached the incident and resolved it.
        steps_taken: Number of movement/service steps executed.
        cost_incurred: Cumulative physical movement cost on ActualGrid.
        replanning_count: Number of dynamic route replans triggered.
        hazards_discovered: List of hazard positions discovered during mission.
        traversed_path: Sequence of coordinates traversed by the vehicle.
        failure_reason: Explanation if mission was unsuccessful.
        execution_time_ms: Wall-clock execution time for this mission.
    """
    incident_id: str
    vehicle_id: str
    responder_id: str
    success: bool
    steps_taken: int
    cost_incurred: float
    replanning_count: int
    hazards_discovered: List[Position] = field(default_factory=list)
    traversed_path: List[Position] = field(default_factory=list)
    failure_reason: Optional[str] = None
    execution_time_ms: float = 0.0

    def summary(self) -> str:
        status_str = "RESOLVED" if self.success else f"FAILED ({self.failure_reason or 'Blocked'})"
        return (
            f"Mission [{self.incident_id}] -> {status_str} | "
            f"Vehicle: {self.vehicle_id} | Responder: {self.responder_id} | "
            f"Steps: {self.steps_taken} | Cost: {self.cost_incurred:.1f} | "
            f"Replans: {self.replanning_count}"
        )


class SimulationReport:
    """Comprehensive summary of a multi-incident disaster response simulation."""

    def __init__(
        self,
        total_incidents: int,
        resolved_incidents: int,
        failed_incidents: int,
        unallocated_incidents: int,
        total_steps: int,
        total_movement_cost: float,
        total_replans: int,
        mission_results: List[MissionResult],
        event_log: List[SimulationEvent],
        execution_time_ms: float = 0.0,
    ) -> None:
        self.total_incidents: int = total_incidents
        self.resolved_incidents: int = resolved_incidents
        self.failed_incidents: int = failed_incidents
        self.unallocated_incidents: int = unallocated_incidents
        self.total_steps: int = total_steps
        self.total_movement_cost: float = total_movement_cost
        self.total_replans: int = total_replans
        self.mission_results: List[MissionResult] = list(mission_results)
        self.event_log: List[SimulationEvent] = list(event_log)
        self.execution_time_ms: float = execution_time_ms

    @property
    def is_fully_resolved(self) -> bool:
        return self.total_incidents > 0 and self.resolved_incidents == self.total_incidents

    def summary(self) -> str:
        pct = (self.resolved_incidents / max(1, self.total_incidents)) * 100.0
        lines = [
            "=" * 72,
            "     RESCUEGRID DISASTER RESPONSE SIMULATION REPORT (PHASE 9.3)     ",
            "=" * 72,
            f"Total Incidents Tracked   : {self.total_incidents}",
            f"Successfully Resolved     : {self.resolved_incidents} ({pct:.1f}%)",
            f"Failed / Unreachable      : {self.failed_incidents}",
            f"Unallocated (No Fleet)    : {self.unallocated_incidents}",
            f"Total Simulation Steps    : {self.total_steps}",
            f"Total Physical Move Cost  : {self.total_movement_cost:.2f}",
            f"Total Route Replans       : {self.total_replans}",
            f"Total Logged Events       : {len(self.event_log)}",
            f"Execution Wall Time       : {self.execution_time_ms:.2f} ms",
            "-" * 72,
            "Mission Details:",
        ]
        for m in self.mission_results:
            lines.append(f"  • {m.summary()}")
        lines.append("=" * 72)
        return "\n".join(lines)


@dataclass
class SimulationStepRecord:
    """Detailed telemetry record for an individual simulation step.

    Attributes:
        step_number: Sequential step index (0 = initialization, 1..N = moves/replanning).
        vehicle_position: Position of the rescue vehicle at this step.
        action: High-level action identifier ('INITIALIZE', 'MOVE', 'REPLAN', 'ARRIVED', 'BLOCKED').
        cost_incurred: Physical movement cost incurred during this step (0.0 for setup/replan).
        newly_revealed: List of grid positions discovered by sensors during this step.
        planned_route: Currently planned route from vehicle_position to destination.
        notes: Descriptive human-readable explanation of the step events.
        grid_snapshot: ASCII representation of the KnowledgeGrid at this moment in time.
        revealed_positions: Set of all positions revealed up to this step.
    """
    step_number: int
    vehicle_position: Position
    action: str
    cost_incurred: float
    newly_revealed: List[Position] = field(default_factory=list)
    planned_route: List[Position] = field(default_factory=list)
    notes: str = ""
    grid_snapshot: Optional[str] = None
    revealed_positions: Set[Position] = field(default_factory=set)


class SimulationResult:
    """Comprehensive summary of a single-vehicle partially observable simulation execution."""

    def __init__(
        self,
        destination_reached: bool,
        total_steps: int,
        actual_cost: float,
        replanning_count: int,
        cells_revealed: int,
        cells_unknown: int,
        search_executions: int,
        total_nodes_explored: int,
        traversed_path: List[Position],
        step_history: List[SimulationStepRecord],
        failure_reason: Optional[str] = None,
        execution_time_ms: float = 0.0,
    ) -> None:
        self.destination_reached: bool = destination_reached
        self.total_steps: int = total_steps
        self.actual_cost: float = actual_cost
        self.replanning_count: int = replanning_count
        self.cells_revealed: int = cells_revealed
        self.cells_unknown: int = cells_unknown
        self.search_executions: int = search_executions
        self.total_nodes_explored: int = total_nodes_explored
        self.traversed_path: List[Position] = list(traversed_path)
        self.step_history: List[SimulationStepRecord] = list(step_history)
        self.failure_reason: Optional[str] = failure_reason
        self.execution_time_ms: float = execution_time_ms

    def summary(self) -> str:
        """Render a formatted human-readable summary of simulation outcomes."""
        status_str = "YES" if self.destination_reached else f"NO ({self.failure_reason or 'Failed'})"
        path_str = " -> ".join(f"({p.x}, {p.y})" for p in self.traversed_path)
        if len(self.traversed_path) > 8:
            first_few = " -> ".join(f"({p.x}, {p.y})" for p in self.traversed_path[:4])
            last_few = " -> ".join(f"({p.x}, {p.y})" for p in self.traversed_path[-3:])
            path_str = f"{first_few} -> ... -> {last_few} ({len(self.traversed_path)} waypoints)"

        lines = [
            "=" * 64,
            "         RESCUEGRID SIMULATION SUMMARY (PHASE 6)         ",
            "=" * 64,
            f"Destination Reached     : {status_str}",
            f"Total Movement Steps    : {self.total_steps}",
            f"Actual Movement Cost    : {self.actual_cost:.2f} (ground truth)",
            f"Replanning Operations   : {self.replanning_count}",
            f"Cells Revealed          : {self.cells_revealed}",
            f"Cells Remaining Unknown : {self.cells_unknown}",
            f"Search Executions       : {self.search_executions}",
            f"Total Nodes Explored    : {self.total_nodes_explored}",
            f"Execution Wall Time     : {self.execution_time_ms:.2f} ms",
            f"Traversed Route         : {path_str}",
            "=" * 64,
        ]
        return "\n".join(lines)

    def __repr__(self) -> str:
        return (
            f"SimulationResult(destination_reached={self.destination_reached}, "
            f"total_steps={self.total_steps}, actual_cost={self.actual_cost}, "
            f"replanning_count={self.replanning_count}, cells_revealed={self.cells_revealed})"
        )


class RescueSimulator:
    """Coordinates disaster simulation, CSP allocation, pathfinding, and locomotion.

    Strict Architectural Separation:
    - Queries the ActualGrid strictly to reveal nearby sensor data and validate physical movement.
    - Supplies strictly the KnowledgeGrid to path-planning algorithms (BFS, DFS, UCS, A*, Hill Climbing).
    - Prevents the planner from inspecting hidden or unknown environmental information.
    - Uses CSP solver strictly for combinatorial resource assignment, never for pathfinding.
    """

    def __init__(
        self,
        actual_grid: ActualGrid,
        knowledge_grid: KnowledgeGrid,
        sensor: Optional[Sensor] = None,
        planner_func: Optional[Union[str, Callable[[Grid, Position, Position], SearchResult]]] = None,
        manager: Optional[RescueManager] = None,
    ) -> None:
        """Initialize a RescueSimulator instance.

        Args:
            actual_grid: Complete physical ground truth Grid.
            knowledge_grid: Agent's internal knowledge state Grid.
            sensor: Proximity sensor instance (defaults to radius 2).
            planner_func: Search function signature (grid, start, goal) -> SearchResult,
                or a registered planner string ('astar', 'ucs', 'bfs', 'dfs', 'hill_climbing').
                Defaults to A* Search (astar).
            manager: Central disaster response manager entity. Defaults to a new RescueManager.

        Raises:
            TypeError: If actual_grid is not Grid or knowledge_grid is not KnowledgeGrid.
            ValueError: If grid dimensions do not match.
        """
        if not isinstance(actual_grid, Grid):
            raise TypeError(f"actual_grid must be a Grid instance, got {type(actual_grid).__name__}.")
        if not isinstance(knowledge_grid, KnowledgeGrid):
            raise TypeError(f"knowledge_grid must be a KnowledgeGrid instance, got {type(knowledge_grid).__name__}.")

        if actual_grid.rows != knowledge_grid.rows or actual_grid.cols != knowledge_grid.cols:
            raise ValueError(
                f"Grid dimension mismatch: actual_grid is {actual_grid.cols}x{actual_grid.rows}, "
                f"knowledge_grid is {knowledge_grid.cols}x{knowledge_grid.rows}."
            )

        self._actual_grid: ActualGrid = actual_grid
        self._knowledge_grid: KnowledgeGrid = knowledge_grid
        self._sensor: Sensor = sensor if sensor is not None else Sensor(radius=2)
        self._manager: RescueManager = manager if manager is not None else RescueManager()
        self._event_log: List[SimulationEvent] = []
        self._current_step: int = 0

        self._planner_func: Callable[[Grid, Position, Position], SearchResult] = astar
        self._planner_name: str = "A* Search"
        self.set_planner(planner_func if planner_func is not None else astar)

    @property
    def actual_grid(self) -> ActualGrid:
        """Return the physical ground truth environment."""
        return self._actual_grid

    @property
    def knowledge_grid(self) -> KnowledgeGrid:
        """Return the agent's knowledge grid."""
        return self._knowledge_grid

    @property
    def sensor(self) -> Sensor:
        """Return the onboard sensor instance."""
        return self._sensor

    @property
    def manager(self) -> RescueManager:
        """Return the associated disaster coordination manager."""
        return self._manager

    @property
    def planner_name(self) -> str:
        """Return the display name of the active route planner."""
        return self._planner_name

    @property
    def current_step(self) -> int:
        """Return the current simulation clock step."""
        return self._current_step

    def set_manager(self, manager: RescueManager) -> None:
        """Assign an external RescueManager instance."""
        if not isinstance(manager, RescueManager):
            raise TypeError(f"Expected RescueManager, got {type(manager).__name__}.")
        self._manager = manager

    def set_planner(
        self,
        planner: Union[str, Callable[[Grid, Position, Position], SearchResult]],
    ) -> None:
        """Configure the active route planning algorithm.

        Args:
            planner: Registered string identifier ('astar', 'ucs', 'bfs', 'dfs', 'hill_climbing')
                     or a callable search function matching (grid, start, goal) -> SearchResult.

        Raises:
            ValueError: If string planner name is not recognized.
            TypeError: If planner is neither a string nor a callable.
        """
        if isinstance(planner, str):
            key = planner.lower().strip()
            if key not in DEFAULT_PLANNERS:
                valid = ", ".join(sorted(DEFAULT_PLANNERS.keys()))
                raise ValueError(f"Unknown planner '{planner}'. Supported planners: {valid}")
            self._planner_func = DEFAULT_PLANNERS[key]
            self._planner_name = planner.upper() if len(planner) <= 4 else planner.replace("_", " ").title()
        elif callable(planner):
            self._planner_func = planner
            self._planner_name = getattr(planner, "__name__", "custom_planner")
        else:
            raise TypeError(f"planner must be a string name or callable, got {type(planner).__name__}.")

    # =========================================================================
    # Event Logging API
    # =========================================================================

    def log_event(
        self,
        event_type: str,
        description: str,
        incident_id: Optional[str] = None,
        vehicle_id: Optional[str] = None,
        responder_id: Optional[str] = None,
        position: Optional[Position] = None,
    ) -> SimulationEvent:
        """Record a structured simulation lifecycle event."""
        event = SimulationEvent(
            step=self._current_step,
            event_type=event_type,
            description=description,
            incident_id=incident_id,
            vehicle_id=vehicle_id,
            responder_id=responder_id,
            position=position,
            timestamp=time.time(),
        )
        self._event_log.append(event)
        return event

    def get_event_log(self) -> List[SimulationEvent]:
        """Return a copy of the simulation event log."""
        return list(self._event_log)

    def get_events_by_type(self, event_type: str) -> List[SimulationEvent]:
        """Return all logged events matching a specified event category."""
        return [e for e in self._event_log if e.event_type == event_type]

    def get_events_for_incident(self, incident_id: str) -> List[SimulationEvent]:
        """Return all logged events associated with a specific incident ID."""
        return [e for e in self._event_log if e.incident_id == incident_id]

    def clear_event_log(self) -> None:
        """Reset the simulation event log and step counter."""
        self._event_log.clear()
        self._current_step = 0

    # =========================================================================
    # Incident & Entity Management
    # =========================================================================

    def register_incident(self, incident: Incident) -> None:
        """Register an emergency incident into the simulation."""
        if not isinstance(incident, Incident):
            raise TypeError(f"Expected Incident instance, got {type(incident).__name__}.")
        self._manager.register_incident(incident)
        self.log_event(
            event_type="INCIDENT_CREATED",
            description=(
                f"Registered incident <{incident.get_id()}>: {incident.get_type().value} "
                f"(Severity {incident.get_severity()}) at {incident.get_position()}"
            ),
            incident_id=incident.get_id(),
            position=incident.get_position(),
        )

    def register_responder(self, responder: Responder) -> None:
        """Register an emergency responder into the simulation fleet."""
        if not isinstance(responder, Responder):
            raise TypeError(f"Expected Responder instance, got {type(responder).__name__}.")
        self._manager.register_responder(responder)

    def register_vehicle(self, vehicle: RescueVehicle) -> None:
        """Register a rescue vehicle into the simulation fleet."""
        if not isinstance(vehicle, RescueVehicle):
            raise TypeError(f"Expected RescueVehicle instance, got {type(vehicle).__name__}.")
        self._manager.register_vehicle(vehicle)

    def prioritize_incidents(
        self,
        incidents: Optional[List[Incident]] = None,
    ) -> List[Incident]:
        """Order emergency incidents by descending severity rating.

        Higher-severity incidents (e.g. 5) receive precedence over lower-severity (e.g. 1).
        Ties are broken deterministically by incident ID.

        Args:
            incidents: Optional subset of incidents to prioritize. Defaults to all
                registered incidents currently in REPORTED status.

        Returns:
            List of Incident objects ordered by descending priority.
        """
        if incidents is not None:
            if not isinstance(incidents, (list, tuple)):
                raise TypeError("incidents must be a list or sequence.")
            target_list = list(incidents)
        else:
            target_list = [
                inc for inc in self._manager.get_incidents()
                if inc.get_status() in (IncidentStatus.REPORTED, IncidentStatus.Reported)
            ]

        # Severity descending: -severity, then incident_id
        sorted_incidents = sorted(
            target_list,
            key=lambda inc: (-inc.get_severity(), inc.get_id()),
        )

        for rank, inc in enumerate(sorted_incidents, 1):
            self.log_event(
                event_type="INCIDENT_PRIORITIZED",
                description=(
                    f"Prioritized incident <{inc.get_id()}> (Rank {rank}, "
                    f"Severity {inc.get_severity()}, Type {inc.get_type().value})"
                ),
                incident_id=inc.get_id(),
                position=inc.get_position(),
            )

        return sorted_incidents

    # =========================================================================
    # CSP Resource Allocation (Without Teleportation)
    # =========================================================================

    def allocate_resources_csp(
        self,
        incidents: Optional[List[Incident]] = None,
        allow_partial: bool = True,
        solver: Optional[CSPSolver] = None,
    ) -> CSPResult:
        """Allocate response fleet to prioritized incidents using CSP without teleportation.

        Matches personnel specialization and vehicle capabilities.
        Preserves physical vehicle coordinates: vehicles stay at their current locations
        and will navigate cell-by-cell in the simulation loop.

        Args:
            incidents: Optional list of incidents. Defaults to all unassigned REPORTED incidents.
            allow_partial: Whether to commit partial allocations when full fleet is unavailable.
            solver: Optional custom CSPSolver.

        Returns:
            CSPResult containing allocation outcomes and assignment mappings.
        """
        prioritized = self.prioritize_incidents(incidents)
        avail_resp = [r for r in self._manager.get_responders() if r.is_available()]
        avail_veh = [v for v in self._manager.get_vehicles() if v.is_available()]

        active_solver = solver if solver is not None else CSPSolver()
        csp_res: CSPResult = active_solver.solve(
            prioritized,
            avail_resp,
            avail_veh,
            allow_partial=allow_partial,
        )

        if csp_res.is_complete or (allow_partial and csp_res.assigned_count > 0):
            for inc_id, (resp, veh) in csp_res.assignments.items():
                m_inc = self._manager.find_incident(inc_id)
                m_resp = self._manager.find_responder(resp.get_id())
                m_veh = self._manager.find_vehicle(veh.get_id())

                if m_inc and m_resp and m_veh:
                    # Mark assigned resources unavailable
                    m_resp.set_availability(False)
                    m_veh.set_availability(False)
                    # Bind IDs and advance incident status
                    m_inc.assign_resources(m_resp.get_id(), m_veh.get_id())
                    m_inc._set_status_direct(IncidentStatus.IN_PROGRESS)

                    # Preserve vehicle current position (NO teleportation)
                    self.log_event(
                        event_type="RESOURCES_ALLOCATED",
                        description=(
                            f"Assigned responder <{m_resp.get_id()}> ({m_resp.get_specialization().value}) "
                            f"and vehicle <{m_veh.get_id()}> ({m_veh.get_type().value}) to incident <{inc_id}>"
                        ),
                        incident_id=inc_id,
                        responder_id=m_resp.get_id(),
                        vehicle_id=m_veh.get_id(),
                        position=m_veh.get_position(),
                    )
        else:
            self.log_event(
                event_type="RESOURCES_UNAVAILABLE",
                description=f"CSP allocation failed to assign fleet (Status: {csp_res.status}).",
            )

        return csp_res

    def _handle_mission_failure(
        self,
        incident: Incident,
        vehicle: RescueVehicle,
        responder: Responder,
        reason: str,
    ) -> None:
        """Handle atomic resource release and incident status transition on mission failure."""
        if hasattr(incident, "set_failure_reason"):
            incident.set_failure_reason(reason)

        if self._manager.has_incident(incident.get_id()):
            self._manager.update_incident_status(incident.get_id(), IncidentStatus.FAILED)
        else:
            responder.set_availability(True)
            vehicle.set_availability(True)
            incident.release_resources()
            incident._set_status_direct(IncidentStatus.FAILED)

        self.log_event(
            event_type="MISSION_FAILED",
            description=f"Mission to incident <{incident.get_id()}> failed: {reason}",
            incident_id=incident.get_id(),
            vehicle_id=vehicle.get_id(),
            responder_id=responder.get_id(),
            position=vehicle.get_position(),
        )
        self.log_event(
            event_type="RESOURCES_RELEASED",
            description=(
                f"Released responder <{responder.get_id()}> and vehicle <{vehicle.get_id()}> "
                f"following mission failure."
            ),
            incident_id=incident.get_id(),
            responder_id=responder.get_id(),
            vehicle_id=vehicle.get_id(),
        )

    # =========================================================================
    # Mission Dispatch & Discrete Vehicle Locomotion
    # =========================================================================

    def execute_mission(
        self,
        incident: Incident,
        vehicle: Optional[RescueVehicle] = None,
        responder: Optional[Responder] = None,
        service_duration: int = 1,
        max_steps: int = 1000,
    ) -> MissionResult:
        """Dispatch assigned vehicle and responder to incident, navigate safely, resolve, and release.

        Vehicles move strictly one grid cell per simulation step.
        Discovers environmental hazards using the proximity sensor.
        Dynamically replans routes when newly discovered obstacles block the path.
        Simulates on-scene emergency service before marking the incident RESOLVED.
        Releases assigned resources back to the available fleet upon completion.

        Args:
            incident: Target incident entity.
            vehicle: Optional vehicle instance (inferred from incident if omitted).
            responder: Optional responder instance (inferred from incident if omitted).
            service_duration: Number of simulation steps to spend resolving emergency at scene.
            max_steps: Maximum movement step limit to safeguard against infinite loops.

        Returns:
            MissionResult with detailed metrics and path history.
        """
        start_time = time.perf_counter()

        # Resolve assigned vehicle and responder
        active_veh = vehicle
        if active_veh is None and incident.has_assigned_resources():
            active_veh = self._manager.find_vehicle(incident.get_assigned_vehicle_id())

        active_resp = responder
        if active_resp is None and incident.has_assigned_resources():
            active_resp = self._manager.find_responder(incident.get_assigned_responder_id())

        if active_veh is None or active_resp is None:
            raise ValueError(
                f"Incident <{incident.get_id()}> does not have an assigned vehicle and responder."
            )

        start_pos = active_veh.get_position()
        goal_pos = incident.get_position()

        # Handle starting cell validity
        if not self._actual_grid.is_inside(start_pos):
            raise IndexError(f"Vehicle start position {start_pos} is outside grid boundaries.")
        if not self._actual_grid.is_inside(goal_pos):
            raise IndexError(f"Incident goal position {goal_pos} is outside grid boundaries.")

        if not self._actual_grid.is_walkable(start_pos):
            end_time = time.perf_counter()
            reason = "Vehicle starting position is blocked in the physical environment."
            self._handle_mission_failure(incident, active_veh, active_resp, reason)
            return MissionResult(
                incident_id=incident.get_id(),
                vehicle_id=active_veh.get_id(),
                responder_id=active_resp.get_id(),
                success=False,
                steps_taken=0,
                cost_incurred=0.0,
                replanning_count=0,
                traversed_path=[start_pos],
                failure_reason=reason,
                execution_time_ms=(end_time - start_time) * 1000.0,
            )

        # Initial sensor scan at start position
        self._sensor.sense(start_pos, self._actual_grid, self._knowledge_grid)

        # Handle trivial case: vehicle already at incident location
        if start_pos == goal_pos:
            self.log_event(
                event_type="VEHICLE_ARRIVED",
                description=f"Vehicle <{active_veh.get_id()}> already at incident <{incident.get_id()}> location.",
                incident_id=incident.get_id(),
                vehicle_id=active_veh.get_id(),
                position=start_pos,
            )
            # Service duration
            for s in range(service_duration):
                self._current_step += 1
                self.log_event(
                    event_type="RESCUE_IN_PROGRESS",
                    description=(
                        f"Performing emergency service at incident <{incident.get_id()}> "
                        f"(Service tick {s+1}/{service_duration})"
                    ),
                    incident_id=incident.get_id(),
                    position=start_pos,
                )
            # Incident resolution & resource release
            self._manager.update_incident_status(incident.get_id(), IncidentStatus.RESOLVED)
            self.log_event(
                event_type="INCIDENT_RESOLVED",
                description=f"Incident <{incident.get_id()}> successfully resolved.",
                incident_id=incident.get_id(),
                position=start_pos,
            )
            self.log_event(
                event_type="RESOURCES_RELEASED",
                description=(
                    f"Released responder <{active_resp.get_id()}> and vehicle <{active_veh.get_id()}> "
                    f"back to available fleet."
                ),
                incident_id=incident.get_id(),
                responder_id=active_resp.get_id(),
                vehicle_id=active_veh.get_id(),
            )
            end_time = time.perf_counter()
            return MissionResult(
                incident_id=incident.get_id(),
                vehicle_id=active_veh.get_id(),
                responder_id=active_resp.get_id(),
                success=True,
                steps_taken=0,
                cost_incurred=0.0,
                replanning_count=0,
                traversed_path=[start_pos],
                execution_time_ms=(end_time - start_time) * 1000.0,
            )

        # Initial route planning on KnowledgeGrid
        search_res = self._planner_func(self._knowledge_grid, start_pos, goal_pos)
        if not search_res.found:
            end_time = time.perf_counter()
            reason = "No initial path to destination found on Knowledge Grid."
            self._handle_mission_failure(incident, active_veh, active_resp, reason)
            return MissionResult(
                incident_id=incident.get_id(),
                vehicle_id=active_veh.get_id(),
                responder_id=active_resp.get_id(),
                success=False,
                steps_taken=0,
                cost_incurred=0.0,
                replanning_count=0,
                traversed_path=[start_pos],
                failure_reason=reason,
                execution_time_ms=(end_time - start_time) * 1000.0,
            )

        self.log_event(
            event_type="ROUTE_CALCULATED",
            description=(
                f"Planned route for vehicle <{active_veh.get_id()}> to incident <{incident.get_id()}>: "
                f"{len(search_res.path)-1} steps, estimated cost {search_res.total_cost}."
            ),
            incident_id=incident.get_id(),
            vehicle_id=active_veh.get_id(),
            position=start_pos,
        )

        current_pos = start_pos
        current_route = list(search_res.path)
        traversed_path: List[Position] = [current_pos]
        hazards_discovered: List[Position] = []
        steps_taken = 0
        cost_incurred = 0.0
        replanning_count = 0
        mission_success = False
        failure_reason: Optional[str] = None

        # Step-by-step physical movement loop (1 cell per simulation step)
        while current_pos != goal_pos:
            if steps_taken >= max_steps:
                failure_reason = f"Exceeded maximum simulation limit of {max_steps} steps."
                break

            if len(current_route) < 2:
                # Replan from current coordinates
                replanning_count += 1
                search_res = self._planner_func(self._knowledge_grid, current_pos, goal_pos)
                if not search_res.found:
                    failure_reason = f"No route to incident <{incident.get_id()}> from current position {current_pos}."
                    break
                current_route = list(search_res.path)

            next_pos = current_route[1]

            # Physical Reality Safety Invariant: Vehicle must NEVER enter a cell that is physically blocked
            if not self._actual_grid.is_walkable(next_pos):
                # Discover hazard immediately before entry
                self._knowledge_grid.reveal_cell(next_pos, self._actual_grid)
                hazards_discovered.append(next_pos)
                replanning_count += 1

                self.log_event(
                    event_type="HAZARD_DISCOVERED",
                    description=(
                        f"Physical hazard discovered ahead at {next_pos} "
                        f"({self._actual_grid.get_cell(next_pos).terrain.value}). Vehicle stopped safely."
                    ),
                    incident_id=incident.get_id(),
                    vehicle_id=active_veh.get_id(),
                    position=next_pos,
                )

                # Replan from current position
                search_res = self._planner_func(self._knowledge_grid, current_pos, goal_pos)
                if not search_res.found:
                    failure_reason = f"Hazard at {next_pos} blocked route and no alternative exists."
                    self.log_event(
                        event_type="MISSION_FAILED",
                        description=failure_reason,
                        incident_id=incident.get_id(),
                        vehicle_id=active_veh.get_id(),
                        position=current_pos,
                    )
                    break

                current_route = list(search_res.path)
                self.log_event(
                    event_type="ROUTE_REPLANNED",
                    description=(
                        f"Dynamic route replanned around {next_pos}: "
                        f"{len(current_route)-1} steps remaining."
                    ),
                    incident_id=incident.get_id(),
                    vehicle_id=active_veh.get_id(),
                    position=current_pos,
                )
                continue

            # Safe physical movement: advance vehicle exactly 1 grid cell
            current_pos = next_pos
            active_veh.set_position(current_pos)
            active_resp.set_position(current_pos)
            traversed_path.append(current_pos)
            steps_taken += 1
            self._current_step += 1

            # Incur physical movement cost on ActualGrid
            step_cost = self._actual_grid.get_cell(current_pos).movement_cost
            cost_incurred += step_cost
            current_route = current_route[1:]

            self.log_event(
                event_type="VEHICLE_MOVEMENT",
                description=(
                    f"Vehicle <{active_veh.get_id()}> advanced to {current_pos}. "
                    f"Cost incurred: {step_cost:.1f}."
                ),
                incident_id=incident.get_id(),
                vehicle_id=active_veh.get_id(),
                position=current_pos,
            )

            # Proximity sensor scan around new position
            newly_revealed = self._sensor.sense(current_pos, self._actual_grid, self._knowledge_grid)

            # Check if destination reached
            if current_pos == goal_pos:
                mission_success = True
                self.log_event(
                    event_type="VEHICLE_ARRIVED",
                    description=f"Vehicle <{active_veh.get_id()}> arrived at incident <{incident.get_id()}> at {current_pos}.",
                    incident_id=incident.get_id(),
                    vehicle_id=active_veh.get_id(),
                    position=current_pos,
                )
                break

            # Check if newly revealed information invalidates any cell in the remaining route
            invalidated_cells = [
                p for p in current_route if not self._knowledge_grid.is_walkable(p)
            ]
            if invalidated_cells:
                for inv_p in invalidated_cells:
                    if inv_p not in hazards_discovered:
                        hazards_discovered.append(inv_p)
                replanning_count += 1
                self.log_event(
                    event_type="HAZARD_DISCOVERED",
                    description="Sensor scan detected hazard intersecting currently planned route.",
                    incident_id=incident.get_id(),
                    vehicle_id=active_veh.get_id(),
                    position=current_pos,
                )

                search_res = self._planner_func(self._knowledge_grid, current_pos, goal_pos)
                if not search_res.found:
                    failure_reason = "Newly discovered hazard blocks route to incident and no detour exists."
                    self.log_event(
                        event_type="MISSION_FAILED",
                        description=failure_reason,
                        incident_id=incident.get_id(),
                        vehicle_id=active_veh.get_id(),
                        position=current_pos,
                    )
                    break

                current_route = list(search_res.path)
                self.log_event(
                    event_type="ROUTE_REPLANNED",
                    description=(
                        f"Dynamic route replanned after sensor detection: "
                        f"{len(current_route)-1} steps remaining."
                    ),
                    incident_id=incident.get_id(),
                    vehicle_id=active_veh.get_id(),
                    position=current_pos,
                )

        # On-Scene Incident Resolution & Resource Release
        if mission_success:
            for s in range(service_duration):
                self._current_step += 1
                self.log_event(
                    event_type="RESCUE_IN_PROGRESS",
                    description=(
                        f"Performing emergency service at incident <{incident.get_id()}> "
                        f"(Service tick {s+1}/{service_duration})"
                    ),
                    incident_id=incident.get_id(),
                    position=current_pos,
                )

            # Atomic incident resolution and fleet release via RescueManager
            self._manager.update_incident_status(incident.get_id(), IncidentStatus.RESOLVED)
            self.log_event(
                event_type="INCIDENT_RESOLVED",
                description=f"Incident <{incident.get_id()}> marked RESOLVED.",
                incident_id=incident.get_id(),
                position=current_pos,
            )
            self.log_event(
                event_type="RESOURCES_RELEASED",
                description=(
                    f"Released responder <{active_resp.get_id()}> and vehicle <{active_veh.get_id()}> "
                    f"back to available fleet."
                ),
                incident_id=incident.get_id(),
                responder_id=active_resp.get_id(),
                vehicle_id=active_veh.get_id(),
            )
        else:
            self._handle_mission_failure(
                incident, active_veh, active_resp, failure_reason or "Mission failed."
            )

        end_time = time.perf_counter()
        return MissionResult(
            incident_id=incident.get_id(),
            vehicle_id=active_veh.get_id(),
            responder_id=active_resp.get_id(),
            success=mission_success,
            steps_taken=steps_taken,
            cost_incurred=cost_incurred,
            replanning_count=replanning_count,
            hazards_discovered=hazards_discovered,
            traversed_path=traversed_path,
            failure_reason=failure_reason,
            execution_time_ms=(end_time - start_time) * 1000.0,
        )

    # =========================================================================
    # Multi-Incident Coordinated Simulation Loop
    # =========================================================================

    def run_simulation(
        self,
        max_steps_per_mission: int = 1000,
        service_duration: int = 1,
        allow_partial: bool = True,
    ) -> SimulationReport:
        """Coordinate multi-incident disaster simulation event loop.

        Workflow:
        1. Identifies unserviced REPORTED incidents.
        2. Orders incidents by descending severity rating.
        3. Solves multi-agent resource allocation using CSP without teleportation.
        4. Dispatches assigned vehicles cell-by-cell in priority order.
        5. Dynamically replans upon physical obstacle or sensor discovery.
        6. Resolves emergencies on-scene and releases fleet resources.
        7. Re-allocates newly freed resources to remaining queued incidents.
        8. Terminates cleanly and compiles comprehensive simulation metrics.

        Args:
            max_steps_per_mission: Step ceiling per mission.
            service_duration: On-scene service ticks.
            allow_partial: Allow partial allocation if fleet is constrained.

        Returns:
            SimulationReport with full mission telemetry, metrics, and event log.
        """
        start_time = time.perf_counter()
        self.log_event("SIMULATION_START", "Commenced multi-incident disaster response simulation.")

        mission_results: List[MissionResult] = []
        total_steps = 0
        total_cost = 0.0
        total_replans = 0

        while True:
            # Check for reported incidents requiring response
            pending_incidents = [
                inc for inc in self._manager.get_incidents()
                if inc.get_status() in (IncidentStatus.REPORTED, IncidentStatus.Reported)
                and not inc.has_assigned_resources()
            ]
            if not pending_incidents:
                break

            # Check for available response resources
            avail_resp = [r for r in self._manager.get_responders() if r.is_available()]
            avail_veh = [v for v in self._manager.get_vehicles() if v.is_available()]
            if not avail_resp or not avail_veh:
                break

            # CSP multi-agent allocation
            csp_res = self.allocate_resources_csp(pending_incidents, allow_partial=allow_partial)
            if csp_res.assigned_count == 0:
                # No compatible resource pair available for remaining reported incidents
                break

            # Fetch assigned incidents ordered by severity
            assigned_incidents = [
                self._manager.find_incident(inc_id)
                for inc_id in csp_res.assignments
            ]
            assigned_incidents = [inc for inc in assigned_incidents if inc is not None]
            assigned_incidents = sorted(
                assigned_incidents,
                key=lambda inc: (-inc.get_severity(), inc.get_id()),
            )

            # Execute missions for currently allocated batch
            for inc in assigned_incidents:
                veh = self._manager.find_vehicle(inc.get_assigned_vehicle_id())
                resp = self._manager.find_responder(inc.get_assigned_responder_id())

                mission_res = self.execute_mission(
                    incident=inc,
                    vehicle=veh,
                    responder=resp,
                    service_duration=service_duration,
                    max_steps=max_steps_per_mission,
                )
                mission_results.append(mission_res)
                total_steps += mission_res.steps_taken
                total_cost += mission_res.cost_incurred
                total_replans += mission_res.replanning_count

        end_time = time.perf_counter()
        self.log_event("SIMULATION_COMPLETE", "Completed multi-incident disaster response simulation.")

        all_incidents = self._manager.get_incidents()
        resolved_count = sum(
            1 for inc in all_incidents
            if inc.get_status() in (IncidentStatus.RESOLVED, IncidentStatus.Resolved)
        )
        failed_count = sum(
            1 for inc in all_incidents
            if inc.get_status() in (IncidentStatus.FAILED, IncidentStatus.Failed)
        )
        if failed_count == 0 and any(not m.success for m in mission_results):
            failed_count = sum(1 for m in mission_results if not m.success)
        unallocated_count = sum(
            1 for inc in all_incidents
            if inc.get_status() in (IncidentStatus.REPORTED, IncidentStatus.Reported)
        )

        return SimulationReport(
            total_incidents=len(all_incidents),
            resolved_incidents=resolved_count,
            failed_incidents=failed_count,
            unallocated_incidents=unallocated_count,
            total_steps=total_steps,
            total_movement_cost=total_cost,
            total_replans=total_replans,
            mission_results=mission_results,
            event_log=self.get_event_log(),
            execution_time_ms=(end_time - start_time) * 1000.0,
        )

    # =========================================================================
    # Phase 6 Single-Vehicle Locomotion (Preserved for Backwards Compatibility)
    # =========================================================================

    def run(
        self,
        start: Position,
        goal: Position,
        max_steps: int = 1000,
    ) -> SimulationResult:
        """Execute step-by-step vehicle locomotion and dynamic replanning (Phase 6 API).

        Preserves 100% backwards compatibility with Phase 6 test suites and demonstrations.
        """
        start_time = time.perf_counter()

        if not isinstance(start, Position):
            raise TypeError(f"start must be a Position, got {type(start).__name__}.")
        if not isinstance(goal, Position):
            raise TypeError(f"goal must be a Position, got {type(goal).__name__}.")

        if not self._actual_grid.is_inside(start):
            raise IndexError(f"Start position {start} is outside grid boundaries.")
        if not self._actual_grid.is_inside(goal):
            raise IndexError(f"Goal position {goal} is outside grid boundaries.")

        # Physical reality check: starting depot must be physically traversable
        if not self._actual_grid.is_walkable(start):
            end_time = time.perf_counter()
            return SimulationResult(
                destination_reached=False,
                total_steps=0,
                actual_cost=0.0,
                replanning_count=0,
                cells_revealed=self._knowledge_grid.revealed_count,
                cells_unknown=self._knowledge_grid.unknown_count,
                search_executions=0,
                total_nodes_explored=0,
                traversed_path=[start],
                step_history=[],
                failure_reason="Starting position is blocked in the physical environment.",
                execution_time_ms=(end_time - start_time) * 1000.0,
            )

        # Metrics tracking
        total_steps = 0
        actual_cost = 0.0
        replanning_count = 0
        search_executions = 0
        total_nodes_explored = 0
        traversed_path: List[Position] = [start]
        history: List[SimulationStepRecord] = []
        destination_reached = False
        failure_reason: Optional[str] = None

        current_pos = start

        # Step 1: Initial sensor scan at starting position
        initial_revealed = self._sensor.sense(current_pos, self._actual_grid, self._knowledge_grid)
        history.append(
            SimulationStepRecord(
                step_number=0,
                vehicle_position=current_pos,
                action="INITIALIZE",
                cost_incurred=0.0,
                newly_revealed=initial_revealed,
                planned_route=[],
                notes="Initialized simulation. Performed initial sensor scan around start position.",
                grid_snapshot=self._knowledge_grid.to_string(),
                revealed_positions=self._knowledge_grid.get_revealed_positions(),
            )
        )

        # Handle trivial case: start equals goal
        if current_pos == goal:
            end_time = time.perf_counter()
            history[0].action = "ARRIVED"
            history[0].notes = "Start position is identical to destination. Mission complete."
            return SimulationResult(
                destination_reached=True,
                total_steps=0,
                actual_cost=0.0,
                replanning_count=0,
                cells_revealed=self._knowledge_grid.revealed_count,
                cells_unknown=self._knowledge_grid.unknown_count,
                search_executions=0,
                total_nodes_explored=0,
                traversed_path=[start],
                step_history=history,
                failure_reason=None,
                execution_time_ms=(end_time - start_time) * 1000.0,
            )

        # Step 2: Plan initial route on Knowledge Grid
        search_res = self._planner_func(self._knowledge_grid, current_pos, goal)
        search_executions += 1
        total_nodes_explored += search_res.nodes_explored

        if not search_res.found:
            end_time = time.perf_counter()
            return SimulationResult(
                destination_reached=False,
                total_steps=0,
                actual_cost=0.0,
                replanning_count=0,
                cells_revealed=self._knowledge_grid.revealed_count,
                cells_unknown=self._knowledge_grid.unknown_count,
                search_executions=search_executions,
                total_nodes_explored=total_nodes_explored,
                traversed_path=[current_pos],
                step_history=history,
                failure_reason="No initial path to destination found on Knowledge Grid.",
                execution_time_ms=(end_time - start_time) * 1000.0,
            )

        current_route = list(search_res.path)
        history[0].planned_route = list(current_route)

        # Step-by-step movement and replanning loop
        while current_pos != goal:
            if total_steps >= max_steps:
                failure_reason = f"Exceeded maximum simulation limit of {max_steps} steps."
                break

            if len(current_route) < 2:
                # Need to replan
                replanning_count += 1
                search_res = self._planner_func(self._knowledge_grid, current_pos, goal)
                search_executions += 1
                total_nodes_explored += search_res.nodes_explored
                if not search_res.found:
                    failure_reason = "No route to destination from current position."
                    break
                current_route = list(search_res.path)

            next_pos = current_route[1]

            # Physical Safety Invariant: Vehicle must NEVER enter a cell that is actually blocked
            if not self._actual_grid.is_walkable(next_pos):
                # Discover hazard immediately before entry
                self._knowledge_grid.reveal_cell(next_pos, self._actual_grid)
                replanning_count += 1
                search_res = self._planner_func(self._knowledge_grid, current_pos, goal)
                search_executions += 1
                total_nodes_explored += search_res.nodes_explored

                if not search_res.found:
                    history.append(
                        SimulationStepRecord(
                            step_number=total_steps + 1,
                            vehicle_position=current_pos,
                            action="BLOCKED",
                            cost_incurred=0.0,
                            newly_revealed=[next_pos],
                            planned_route=[],
                            notes=f"Physical path blocked at {next_pos}. Replanning failed to find an alternative.",
                            grid_snapshot=self._knowledge_grid.to_string(),
                            revealed_positions=self._knowledge_grid.get_revealed_positions(),
                        )
                    )
                    failure_reason = f"Next cell {next_pos} is blocked and no alternative route exists."
                    break

                current_route = list(search_res.path)
                history.append(
                    SimulationStepRecord(
                        step_number=total_steps,
                        vehicle_position=current_pos,
                        action="REPLAN",
                        cost_incurred=0.0,
                        newly_revealed=[next_pos],
                        planned_route=list(current_route),
                        notes=f"Hazard discovered ahead at {next_pos}. Stopped vehicle and replanned new route.",
                        grid_snapshot=self._knowledge_grid.to_string(),
                        revealed_positions=self._knowledge_grid.get_revealed_positions(),
                    )
                )
                continue

            # Move vehicle 1 step to next_pos
            current_pos = next_pos
            traversed_path.append(current_pos)
            total_steps += 1

            # Incur physical movement cost on ActualGrid
            step_cost = self._actual_grid.get_cell(current_pos).movement_cost
            actual_cost += step_cost

            # Advance planned route
            current_route = current_route[1:]

            # Scan surrounding environment with sensor
            newly_revealed = self._sensor.sense(current_pos, self._actual_grid, self._knowledge_grid)

            # Check if destination reached
            if current_pos == goal:
                destination_reached = True
                history.append(
                    SimulationStepRecord(
                        step_number=total_steps,
                        vehicle_position=current_pos,
                        action="ARRIVED",
                        cost_incurred=step_cost,
                        newly_revealed=newly_revealed,
                        planned_route=[current_pos],
                        notes=f"Arrived at destination {goal} safely.",
                        grid_snapshot=self._knowledge_grid.to_string(),
                        revealed_positions=self._knowledge_grid.get_revealed_positions(),
                    )
                )
                break

            # Requirement 9: Check whether newly discovered information affects the remaining route
            route_invalidated = False
            for route_pos in current_route:
                if not self._knowledge_grid.is_walkable(route_pos):
                    route_invalidated = True
                    break

            if route_invalidated:
                replanning_count += 1
                search_res = self._planner_func(self._knowledge_grid, current_pos, goal)
                search_executions += 1
                total_nodes_explored += search_res.nodes_explored

                if not search_res.found:
                    history.append(
                        SimulationStepRecord(
                            step_number=total_steps,
                            vehicle_position=current_pos,
                            action="BLOCKED",
                            cost_incurred=step_cost,
                            newly_revealed=newly_revealed,
                            planned_route=[],
                            notes="Discovered hazard along planned route. Replanning failed to find an alternative.",
                            grid_snapshot=self._knowledge_grid.to_string(),
                            revealed_positions=self._knowledge_grid.get_revealed_positions(),
                        )
                    )
                    failure_reason = "Discovered hazard along planned route and no alternative route exists."
                    break

                current_route = list(search_res.path)
                history.append(
                    SimulationStepRecord(
                        step_number=total_steps,
                        vehicle_position=current_pos,
                        action="REPLAN",
                        cost_incurred=step_cost,
                        newly_revealed=newly_revealed,
                        planned_route=list(current_route),
                        notes=f"Discovered hazard along planned route. Successfully replanned route: {len(current_route)-1} steps remaining.",
                        grid_snapshot=self._knowledge_grid.to_string(),
                        revealed_positions=self._knowledge_grid.get_revealed_positions(),
                    )
                )
            else:
                history.append(
                    SimulationStepRecord(
                        step_number=total_steps,
                        vehicle_position=current_pos,
                        action="MOVE",
                        cost_incurred=step_cost,
                        newly_revealed=newly_revealed,
                        planned_route=list(current_route),
                        notes=f"Moved to {current_pos}. Planned route remains clear and valid.",
                        grid_snapshot=self._knowledge_grid.to_string(),
                        revealed_positions=self._knowledge_grid.get_revealed_positions(),
                    )
                )

        end_time = time.perf_counter()
        return SimulationResult(
            destination_reached=destination_reached,
            total_steps=total_steps,
            actual_cost=actual_cost,
            replanning_count=replanning_count,
            cells_revealed=self._knowledge_grid.revealed_count,
            cells_unknown=self._knowledge_grid.unknown_count,
            search_executions=search_executions,
            total_nodes_explored=total_nodes_explored,
            traversed_path=traversed_path,
            step_history=history,
            failure_reason=failure_reason,
            execution_time_ms=(end_time - start_time) * 1000.0,
        )

    # =========================================================================
    # Visualization Integration (Phase 9.3)
    # =========================================================================

    def render_simulation_state(
        self,
        ax: Optional[Any] = None,
        show_incidents: bool = True,
        show_vehicles: bool = True,
        show_routes: bool = True,
        active_routes: Optional[List[List[Position]]] = None,
        title: Optional[str] = None,
        save_path: Optional[str] = None,
    ) -> Tuple[Any, Any]:
        """Render the current simulation state using GridVisualizer."""
        from visualization.grid_visualizer import GridVisualizer
        viz = GridVisualizer()
        fig, ax = viz.render_grid(
            self._knowledge_grid,
            ax=ax,
            title=title or "RescueGrid Disaster Simulation State",
            show_legend=True,
        )

        # Overlay active incidents
        if show_incidents:
            for inc in self._manager.get_incidents():
                pos = inc.get_position()
                status = inc.get_status()
                if status in (IncidentStatus.RESOLVED, IncidentStatus.Resolved):
                    color = "#4CAF50"
                    marker = "*"
                elif status in (IncidentStatus.FAILED, IncidentStatus.Failed):
                    color = "#757575"
                    marker = "X"
                else:
                    color = "#E91E63"
                    marker = "P"
                ax.scatter(
                    pos.x, pos.y, s=180, c=color, marker=marker,
                    edgecolors="#212121", linewidths=1.5, zorder=6,
                )
                ax.text(
                    pos.x, pos.y + 0.35, f"{inc.get_id()} ({inc.get_severity()})",
                    fontsize=8, fontweight="bold", ha="center", va="top",
                    bbox=dict(boxstyle="round,pad=0.2", facecolor="white", alpha=0.8, edgecolor="gray"),
                    zorder=7,
                )

        # Overlay vehicles
        if show_vehicles:
            for veh in self._manager.get_vehicles():
                pos = veh.get_position()
                ax.scatter(
                    pos.x, pos.y, s=140, c="#FF9800", marker="s",
                    edgecolors="#212121", linewidths=1.5, zorder=6,
                )
                ax.text(
                    pos.x, pos.y - 0.35, veh.get_id(),
                    fontsize=8, fontweight="bold", ha="center", va="bottom",
                    bbox=dict(boxstyle="round,pad=0.2", facecolor="#FFF3E0", alpha=0.8, edgecolor="orange"),
                    zorder=7,
                )

        # Overlay routes
        if show_routes and active_routes:
            for route in active_routes:
                if len(route) >= 2:
                    xs = [p.x for p in route]
                    ys = [p.y for p in route]
                    ax.plot(xs, ys, color="#FFD600", linewidth=3.0, zorder=5)

        if save_path:
            import os
            os.makedirs(os.path.dirname(os.path.abspath(save_path)), exist_ok=True)
            fig.savefig(save_path, bbox_inches="tight", dpi=150)

        return fig, ax
