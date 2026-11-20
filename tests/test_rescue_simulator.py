"""
Comprehensive Unit Test Suite for RescueGrid Simulator Integration (Phase 9.3).

Verifies:
1. Simulator initialization, input validation, and planner configuration.
2. Incident management, registration, and severity-based prioritization.
3. Multi-Agent CSP resource allocation without vehicle teleportation.
4. Discrete cell-by-cell vehicle locomotion and physical movement cost calculation.
5. Physical safety invariants (blocked-cell and unknown-cell avoidance).
6. Sensor-based environmental discovery and dynamic route replanning.
7. Unreachable destinations and graceful failure reporting.
8. On-scene emergency operations, incident resolution, and fleet resource release.
9. Multi-incident simulation event loop coordination and resource reuse.
10. Structured event logging API (creation, filtering, step tracking).
11. State visualization integration and headless rendering.
"""

import os
import sys
import unittest
import warnings
from typing import Any, List

# Suppress headless animation deletion warnings
warnings.filterwarnings("ignore", category=UserWarning, module="matplotlib.animation")

# Ensure non-interactive headless backend for Matplotlib
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from models.position import Position
from models.incident import Incident, IncidentType, IncidentStatus
from models.responder import Responder, ResponderSpecialization
from models.rescue_vehicle import RescueVehicle, VehicleType
from core.rescue_manager import RescueManager
from environment.cell import Cell, TerrainType
from environment.grid import Grid
from environment.actual_grid import ActualGrid
from environment.knowledge_grid import KnowledgeGrid
from algorithms.csp import CSPSolver
from algorithms.astar import astar
from algorithms.ucs import ucs
from algorithms.bfs import bfs
from algorithms.dfs import dfs
from simulation.sensor import Sensor
from simulation.rescue_simulator import (
    RescueSimulator,
    SimulationEvent,
    MissionResult,
    SimulationReport,
)


class TestSimulatorInitializationAndConfiguration(unittest.TestCase):
    """Test Suite 1: Simulator setup, input validation, and planner configuration."""

    def setUp(self) -> None:
        self.actual = ActualGrid(rows=6, cols=8)
        self.knowledge = KnowledgeGrid(rows=6, cols=8)

    def test_default_initialization(self) -> None:
        """Simulator initializes with valid defaults, default sensor, and A* planner."""
        sim = RescueSimulator(self.actual, self.knowledge)
        self.assertIs(sim.actual_grid, self.actual)
        self.assertIs(sim.knowledge_grid, self.knowledge)
        self.assertEqual(sim.sensor.radius, 2)
        self.assertIsNotNone(sim.manager)
        self.assertEqual(sim.current_step, 0)

    def test_type_validation_on_grids(self) -> None:
        """Invalid grid instances raise TypeError."""
        with self.assertRaises(TypeError):
            RescueSimulator("not_a_grid", self.knowledge)
        with self.assertRaises(TypeError):
            RescueSimulator(self.actual, "not_a_knowledge_grid")

    def test_dimension_mismatch_validation(self) -> None:
        """Mismatched actual and knowledge grid dimensions raise ValueError."""
        mismatched_knowledge = KnowledgeGrid(rows=10, cols=8)
        with self.assertRaises(ValueError):
            RescueSimulator(self.actual, mismatched_knowledge)

    def test_string_planner_aliases(self) -> None:
        """Simulator configures supported pathfinding planners via string names."""
        sim = RescueSimulator(self.actual, self.knowledge)
        for name in ["astar", "ucs", "bfs", "dfs", "hill_climbing"]:
            sim.set_planner(name)
            self.assertIsNotNone(sim.planner_name)

    def test_unknown_planner_rejected(self) -> None:
        """Unknown planner string raises ValueError."""
        sim = RescueSimulator(self.actual, self.knowledge)
        with self.assertRaises(ValueError):
            sim.set_planner("quantum_teleportation")

    def test_invalid_planner_type_rejected(self) -> None:
        """Non-string non-callable planner raises TypeError."""
        sim = RescueSimulator(self.actual, self.knowledge)
        with self.assertRaises(TypeError):
            sim.set_planner(12345)


class TestIncidentManagementAndPrioritization(unittest.TestCase):
    """Test Suite 2: Incident registration, priority ordering, and validation."""

    def setUp(self) -> None:
        self.actual = ActualGrid(rows=6, cols=8)
        self.knowledge = KnowledgeGrid(rows=6, cols=8)
        self.sim = RescueSimulator(self.actual, self.knowledge)

    def test_register_incident(self) -> None:
        """Registering an incident logs an INCIDENT_CREATED event and stores in manager."""
        inc = Incident("INC-01", IncidentType.FIRE, severity=4, position=Position(3, 3))
        self.sim.register_incident(inc)
        self.assertTrue(self.sim.manager.has_incident("INC-01"))

        events = self.sim.get_events_by_type("INCIDENT_CREATED")
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0].incident_id, "INC-01")

    def test_invalid_incident_type_rejected(self) -> None:
        """Non-Incident registration raises TypeError."""
        with self.assertRaises(TypeError):
            self.sim.register_incident("not_an_incident")

    def test_severity_based_prioritization(self) -> None:
        """Incidents are prioritized in descending order of severity (5 down to 1)."""
        inc1 = Incident("INC-LOW", IncidentType.MEDICAL, severity=1, position=Position(1, 1))
        inc2 = Incident("INC-CRIT", IncidentType.FIRE, severity=5, position=Position(2, 2))
        inc3 = Incident("INC-MED", IncidentType.FLOOD, severity=3, position=Position(3, 3))

        self.sim.register_incident(inc1)
        self.sim.register_incident(inc2)
        self.sim.register_incident(inc3)

        prioritized = self.sim.prioritize_incidents()
        self.assertEqual(len(prioritized), 3)
        self.assertEqual(prioritized[0].get_id(), "INC-CRIT")
        self.assertEqual(prioritized[1].get_id(), "INC-MED")
        self.assertEqual(prioritized[2].get_id(), "INC-LOW")

    def test_deterministic_tie_breaking(self) -> None:
        """Incidents with equal severity break ties deterministically by ID."""
        inc_b = Incident("INC-B", IncidentType.FIRE, severity=4, position=Position(1, 1))
        inc_a = Incident("INC-A", IncidentType.FIRE, severity=4, position=Position(2, 2))

        self.sim.register_incident(inc_b)
        self.sim.register_incident(inc_a)

        prioritized = self.sim.prioritize_incidents()
        self.assertEqual(prioritized[0].get_id(), "INC-A")
        self.assertEqual(prioritized[1].get_id(), "INC-B")


class TestCSPResourceAllocation(unittest.TestCase):
    """Test Suite 3: CSP fleet assignment, matching, and no-teleportation invariant."""

    def setUp(self) -> None:
        self.actual = ActualGrid(rows=6, cols=8)
        self.knowledge = KnowledgeGrid(rows=6, cols=8)
        self.sim = RescueSimulator(self.actual, self.knowledge)
        self.depot = Position(0, 0)

    def test_specialization_and_vehicle_matching(self) -> None:
        """CSP matches Firefighter+FireEngine to Fire and Paramedic+Ambulance to Medical."""
        self.sim.register_responder(Responder("R-FIRE", "Bob", ResponderSpecialization.FIREFIGHTER, self.depot))
        self.sim.register_responder(Responder("R-MED", "Alice", ResponderSpecialization.PARAMEDIC, self.depot))
        self.sim.register_vehicle(RescueVehicle("V-ENG", VehicleType.FIRE_ENGINE, self.depot))
        self.sim.register_vehicle(RescueVehicle("V-AMB", VehicleType.AMBULANCE, self.depot))

        inc_fire = Incident("INC-1", IncidentType.FIRE, severity=5, position=Position(4, 4))
        inc_med = Incident("INC-2", IncidentType.MEDICAL, severity=3, position=Position(5, 5))
        self.sim.register_incident(inc_fire)
        self.sim.register_incident(inc_med)

        csp_res = self.sim.allocate_resources_csp(allow_partial=False)
        self.assertTrue(csp_res.is_complete)
        self.assertEqual(csp_res.assignments["INC-1"][0].get_id(), "R-FIRE")
        self.assertEqual(csp_res.assignments["INC-1"][1].get_id(), "V-ENG")
        self.assertEqual(csp_res.assignments["INC-2"][0].get_id(), "R-MED")
        self.assertEqual(csp_res.assignments["INC-2"][1].get_id(), "V-AMB")

    def test_no_teleportation_invariant(self) -> None:
        """CSP allocation updates availability and status but preserves vehicle coordinates."""
        veh = RescueVehicle("V-ENG", VehicleType.FIRE_ENGINE, self.depot)
        resp = Responder("R-FIRE", "Bob", ResponderSpecialization.FIREFIGHTER, self.depot)
        inc = Incident("INC-1", IncidentType.FIRE, severity=5, position=Position(5, 4))

        self.sim.register_vehicle(veh)
        self.sim.register_responder(resp)
        self.sim.register_incident(inc)

        self.sim.allocate_resources_csp()
        # Coordinates must remain at depot (0, 0)
        self.assertEqual(veh.get_position(), self.depot)
        self.assertEqual(resp.get_position(), self.depot)
        # Availability and status must reflect dispatch
        self.assertFalse(veh.is_available())
        self.assertFalse(resp.is_available())
        self.assertEqual(inc.get_status(), IncidentStatus.IN_PROGRESS)

    def test_insufficient_resources_atomic_failure(self) -> None:
        """When resources are insufficient and allow_partial=False, state remains unchanged."""
        veh = RescueVehicle("V-ENG", VehicleType.FIRE_ENGINE, self.depot)
        resp = Responder("R-FIRE", "Bob", ResponderSpecialization.FIREFIGHTER, self.depot)
        # Two simultaneous fires, but only one fire engine
        inc1 = Incident("INC-1", IncidentType.FIRE, severity=5, position=Position(3, 3))
        inc2 = Incident("INC-2", IncidentType.FIRE, severity=4, position=Position(4, 4))

        self.sim.register_vehicle(veh)
        self.sim.register_responder(resp)
        self.sim.register_incident(inc1)
        self.sim.register_incident(inc2)

        csp_res = self.sim.allocate_resources_csp(allow_partial=False)
        self.assertFalse(csp_res.is_complete)
        self.assertTrue(veh.is_available())
        self.assertTrue(resp.is_available())
        self.assertEqual(inc1.get_status(), IncidentStatus.REPORTED)
        self.assertEqual(inc2.get_status(), IncidentStatus.REPORTED)

    def test_insufficient_resources_partial_allocation(self) -> None:
        """When allow_partial=True, the highest priority incident receives available resources."""
        veh = RescueVehicle("V-ENG", VehicleType.FIRE_ENGINE, self.depot)
        resp = Responder("R-FIRE", "Bob", ResponderSpecialization.FIREFIGHTER, self.depot)
        inc_low = Incident("INC-LOW", IncidentType.FIRE, severity=2, position=Position(3, 3))
        inc_high = Incident("INC-HIGH", IncidentType.FIRE, severity=5, position=Position(4, 4))

        self.sim.register_vehicle(veh)
        self.sim.register_responder(resp)
        self.sim.register_incident(inc_low)
        self.sim.register_incident(inc_high)

        csp_res = self.sim.allocate_resources_csp(allow_partial=True)
        self.assertEqual(csp_res.assigned_count, 1)
        self.assertIn("INC-HIGH", csp_res.assignments)
        self.assertNotIn("INC-LOW", csp_res.assignments)


class TestDiscreteVehicleLocomotionAndMovementCosts(unittest.TestCase):
    """Test Suite 4: Step-by-step movement, path execution, and weighted cost calculation."""

    def setUp(self) -> None:
        # 8 cols x 4 rows
        self.actual = ActualGrid(rows=4, cols=8, default_terrain=TerrainType.NORMAL)
        # Highway bypass on row 1 (cost 1.0)
        for x in range(8):
            self.actual.add_road(Position(x, 1))

        self.knowledge = KnowledgeGrid(rows=4, cols=8, default_terrain=TerrainType.NORMAL)
        for x in range(8):
            self.knowledge.add_road(Position(x, 1))

        self.sim = RescueSimulator(self.actual, self.knowledge, planner_func="astar")
        self.depot = Position(0, 1)

    def test_cell_by_cell_locomotion(self) -> None:
        """Vehicle moves strictly one adjacent grid cell per simulation step."""
        veh = RescueVehicle("V1", VehicleType.FIRE_ENGINE, self.depot)
        resp = Responder("R1", "Firefighter", ResponderSpecialization.FIREFIGHTER, self.depot)
        inc = Incident("INC-1", IncidentType.FIRE, severity=5, position=Position(4, 1))

        self.sim.register_vehicle(veh)
        self.sim.register_responder(resp)
        self.sim.register_incident(inc)

        self.sim.allocate_resources_csp()
        mission = self.sim.execute_mission(inc, service_duration=0)

        self.assertTrue(mission.success)
        self.assertEqual(mission.steps_taken, 4)
        # Check every consecutive pair in traversed_path has Manhattan distance == 1
        path = mission.traversed_path
        self.assertEqual(len(path), 5)
        for i in range(len(path) - 1):
            dist = abs(path[i].x - path[i+1].x) + abs(path[i].y - path[i+1].y)
            self.assertEqual(dist, 1, f"Step from {path[i]} to {path[i+1]} is not cardinal adjacency.")

    def test_movement_cost_incurred(self) -> None:
        """Physical movement cost reflects actual terrain entering costs."""
        # 4 steps on ROAD (cost 1.0 each) = 4.0
        veh = RescueVehicle("V1", VehicleType.FIRE_ENGINE, self.depot)
        resp = Responder("R1", "Firefighter", ResponderSpecialization.FIREFIGHTER, self.depot)
        inc = Incident("INC-1", IncidentType.FIRE, severity=5, position=Position(4, 1))

        self.sim.register_vehicle(veh)
        self.sim.register_responder(resp)
        self.sim.register_incident(inc)
        self.sim.allocate_resources_csp()

        mission = self.sim.execute_mission(inc, service_duration=0)
        self.assertEqual(mission.cost_incurred, 4.0)


class TestHazardDiscoveryAndDynamicReplanning(unittest.TestCase):
    """Test Suite 5: Sensory hazard discovery, obstacle avoidance, and dynamic replanning."""

    def setUp(self) -> None:
        cols, rows = 10, 4
        self.actual = ActualGrid(rows=rows, cols=cols, default_terrain=TerrainType.NORMAL)
        for x in range(cols):
            self.actual.add_road(Position(x, 1))

        # Hidden rubble hazard on ActualGrid at (3, 1)
        self.actual.add_collapsed_building(Position(3, 1))

        # KnowledgeGrid believes the highway at (3, 1) is open
        self.knowledge = KnowledgeGrid(rows=rows, cols=cols, default_terrain=TerrainType.NORMAL)
        for x in range(cols):
            self.knowledge.add_road(Position(x, 1))

        self.sim = RescueSimulator(self.actual, self.knowledge, sensor=Sensor(radius=2), planner_func="astar")
        self.depot = Position(0, 1)

    def test_vehicle_stops_before_blocked_cell_and_replans(self) -> None:
        """Vehicle never enters physically blocked cell; discovers hazard, replans, and succeeds."""
        veh = RescueVehicle("V1", VehicleType.FIRE_ENGINE, self.depot)
        resp = Responder("R1", "Firefighter", ResponderSpecialization.FIREFIGHTER, self.depot)
        inc = Incident("INC-1", IncidentType.FIRE, severity=5, position=Position(6, 1))

        self.sim.register_vehicle(veh)
        self.sim.register_responder(resp)
        self.sim.register_incident(inc)
        self.sim.allocate_resources_csp()

        mission = self.sim.execute_mission(inc, service_duration=0)
        self.assertTrue(mission.success)
        self.assertGreaterEqual(mission.replanning_count, 1)
        self.assertIn(Position(3, 1), mission.hazards_discovered)

        # Invariant: Vehicle must NEVER have traversed (3, 1)
        self.assertNotIn(Position(3, 1), mission.traversed_path)

        # Verify HAZARD_DISCOVERED and ROUTE_REPLANNED events were recorded
        hazard_events = self.sim.get_events_by_type("HAZARD_DISCOVERED")
        replan_events = self.sim.get_events_by_type("ROUTE_REPLANNED")
        self.assertGreaterEqual(len(hazard_events), 1)
        self.assertGreaterEqual(len(replan_events), 1)

    def test_unreachable_destination_reported_as_failure(self) -> None:
        """When destination is walled off, mission reports failure cleanly without crashing."""
        # Enclose incident with rubble
        goal = Position(8, 1)
        self.actual.add_collapsed_building(Position(7, 1))
        self.actual.add_collapsed_building(Position(8, 0))
        self.actual.add_collapsed_building(Position(8, 2))
        self.actual.add_collapsed_building(Position(9, 1))

        veh = RescueVehicle("V1", VehicleType.FIRE_ENGINE, self.depot)
        resp = Responder("R1", "Firefighter", ResponderSpecialization.FIREFIGHTER, self.depot)
        inc = Incident("INC-TRAPPED", IncidentType.FIRE, severity=5, position=goal)

        self.sim.register_vehicle(veh)
        self.sim.register_responder(resp)
        self.sim.register_incident(inc)
        self.sim.allocate_resources_csp()

        mission = self.sim.execute_mission(inc, service_duration=0)
        self.assertFalse(mission.success)
        self.assertIsNotNone(mission.failure_reason)

    def test_blocked_starting_cell_failure(self) -> None:
        """Vehicle positioned on an impassable obstacle reports failure immediately."""
        self.actual.add_collapsed_building(self.depot)
        veh = RescueVehicle("V1", VehicleType.FIRE_ENGINE, self.depot)
        resp = Responder("R1", "Firefighter", ResponderSpecialization.FIREFIGHTER, self.depot)
        inc = Incident("INC-1", IncidentType.FIRE, severity=5, position=Position(4, 1))

        self.sim.register_vehicle(veh)
        self.sim.register_responder(resp)
        self.sim.register_incident(inc)
        self.sim.allocate_resources_csp()

        mission = self.sim.execute_mission(inc)
        self.assertFalse(mission.success)
        self.assertIn("blocked", mission.failure_reason.lower())

    def test_start_equals_goal_immediate_resolution(self) -> None:
        """Vehicle already at incident location executes service and resolves without movement."""
        veh = RescueVehicle("V1", VehicleType.FIRE_ENGINE, self.depot)
        resp = Responder("R1", "Firefighter", ResponderSpecialization.FIREFIGHTER, self.depot)
        inc = Incident("INC-DEPOT", IncidentType.FIRE, severity=5, position=self.depot)

        self.sim.register_vehicle(veh)
        self.sim.register_responder(resp)
        self.sim.register_incident(inc)
        self.sim.allocate_resources_csp()

        mission = self.sim.execute_mission(inc, service_duration=2)
        self.assertTrue(mission.success)
        self.assertEqual(mission.steps_taken, 0)
        self.assertEqual(inc.get_status(), IncidentStatus.RESOLVED)

    def test_actual_grid_immutability(self) -> None:
        """ActualGrid terrain classifications and costs remain 100% unaltered after missions."""
        def snapshot():
            return [(c, r, self.actual.get_cell_by_rc(r, c).terrain, self.actual.get_cell_by_rc(r, c).movement_cost)
                    for r in range(self.actual.rows) for c in range(self.actual.cols)]

        before = snapshot()
        veh = RescueVehicle("V1", VehicleType.FIRE_ENGINE, self.depot)
        resp = Responder("R1", "Firefighter", ResponderSpecialization.FIREFIGHTER, self.depot)
        inc = Incident("INC-1", IncidentType.FIRE, severity=5, position=Position(6, 1))

        self.sim.register_vehicle(veh)
        self.sim.register_responder(resp)
        self.sim.register_incident(inc)
        self.sim.allocate_resources_csp()
        self.sim.execute_mission(inc, service_duration=0)

        after = snapshot()
        self.assertEqual(before, after)


class TestIncidentResolutionAndResourceRelease(unittest.TestCase):
    """Test Suite 6: Service duration, incident resolution, and fleet release."""

    def setUp(self) -> None:
        self.actual = ActualGrid(rows=4, cols=6, default_terrain=TerrainType.NORMAL)
        self.knowledge = KnowledgeGrid(rows=4, cols=6, default_terrain=TerrainType.NORMAL)
        self.sim = RescueSimulator(self.actual, self.knowledge)
        self.depot = Position(0, 0)

    def test_on_scene_service_and_incident_resolution(self) -> None:
        """Arriving at scene executes service duration and marks incident RESOLVED."""
        veh = RescueVehicle("V1", VehicleType.FIRE_ENGINE, self.depot)
        resp = Responder("R1", "Firefighter", ResponderSpecialization.FIREFIGHTER, self.depot)
        inc = Incident("INC-1", IncidentType.FIRE, severity=5, position=Position(2, 0))

        self.sim.register_vehicle(veh)
        self.sim.register_responder(resp)
        self.sim.register_incident(inc)
        self.sim.allocate_resources_csp()

        start_step = self.sim.current_step
        mission = self.sim.execute_mission(inc, service_duration=3)

        self.assertTrue(mission.success)
        self.assertEqual(inc.get_status(), IncidentStatus.RESOLVED)
        # Step counter advanced: 2 movement steps + 3 service steps = 5
        self.assertEqual(self.sim.current_step - start_step, 5)

        # Resources must be released and available again
        self.assertTrue(veh.is_available())
        self.assertTrue(resp.is_available())
        self.assertFalse(inc.has_assigned_resources())

    def test_released_resources_reassigned_to_subsequent_incident(self) -> None:
        """Resources released from incident 1 are immediately eligible for incident 2."""
        veh = RescueVehicle("V1", VehicleType.FIRE_ENGINE, self.depot)
        resp = Responder("R1", "Firefighter", ResponderSpecialization.FIREFIGHTER, self.depot)
        inc1 = Incident("INC-1", IncidentType.FIRE, severity=5, position=Position(2, 0))
        inc2 = Incident("INC-2", IncidentType.FIRE, severity=4, position=Position(4, 0))

        self.sim.register_vehicle(veh)
        self.sim.register_responder(resp)
        self.sim.register_incident(inc1)
        self.sim.register_incident(inc2)

        report = self.sim.run_simulation(service_duration=1)
        self.assertEqual(report.resolved_incidents, 2)
        self.assertEqual(report.total_incidents, 2)
        self.assertEqual(inc1.get_status(), IncidentStatus.RESOLVED)
        self.assertEqual(inc2.get_status(), IncidentStatus.RESOLVED)


class TestEventLoggingAPI(unittest.TestCase):
    """Test Suite 7: Event creation, structured query methods, and logging integrity."""

    def setUp(self) -> None:
        self.actual = ActualGrid(rows=4, cols=6)
        self.knowledge = KnowledgeGrid(rows=4, cols=6)
        self.sim = RescueSimulator(self.actual, self.knowledge)

    def test_event_logging_and_filtering(self) -> None:
        """Events are logged with sequential steps and can be queried by category or incident."""
        self.sim.log_event("CUSTOM_EVENT", "First action", incident_id="INC-1")
        self.sim.log_event("ANOTHER_EVENT", "Second action", incident_id="INC-2")
        self.sim.log_event("CUSTOM_EVENT", "Third action", incident_id="INC-1")

        all_events = self.sim.get_event_log()
        self.assertEqual(len(all_events), 3)

        custom = self.sim.get_events_by_type("CUSTOM_EVENT")
        self.assertEqual(len(custom), 2)

        inc1_events = self.sim.get_events_for_incident("INC-1")
        self.assertEqual(len(inc1_events), 2)

    def test_clear_event_log(self) -> None:
        """clear_event_log empties the event list and resets clock."""
        self.sim.log_event("TEST", "Note")
        self.sim.clear_event_log()
        self.assertEqual(len(self.sim.get_event_log()), 0)
        self.assertEqual(self.sim.current_step, 0)


class TestVisualizationStateRendering(unittest.TestCase):
    """Test Suite 8: State rendering integration with GridVisualizer in headless mode."""

    def setUp(self) -> None:
        self.actual = ActualGrid(rows=5, cols=8, default_terrain=TerrainType.NORMAL)
        self.knowledge = KnowledgeGrid(rows=5, cols=8, default_terrain=TerrainType.NORMAL)
        self.sim = RescueSimulator(self.actual, self.knowledge)
        self.depot = Position(0, 0)

        self.sim.register_vehicle(RescueVehicle("V1", VehicleType.AMBULANCE, self.depot))
        self.sim.register_responder(Responder("R1", "Paramedic", ResponderSpecialization.PARAMEDIC, self.depot))
        self.sim.register_incident(Incident("INC-1", IncidentType.MEDICAL, severity=4, position=Position(5, 3)))

    def tearDown(self) -> None:
        plt.close("all")

    def test_render_simulation_state(self) -> None:
        """render_simulation_state overlays incidents and vehicles without errors."""
        fig, ax = self.sim.render_simulation_state(title="Test State")
        self.assertIsNotNone(fig)
        self.assertIsNotNone(ax)

    def test_render_simulation_state_saves_file(self) -> None:
        """render_simulation_state writes valid image to disk when save_path is provided."""
        tmp_path = "/tmp/test_rescue_state.png"
        if os.path.exists(tmp_path):
            os.remove(tmp_path)

        fig, _ = self.sim.render_simulation_state(save_path=tmp_path)
        self.assertTrue(os.path.exists(tmp_path))
        self.assertGreater(os.path.getsize(tmp_path), 0)
        os.remove(tmp_path)


class TestMissionFailureAndResourceReleaseLifecycle(unittest.TestCase):
    """Test Suite 9: Failure lifecycle, atomic resource release, and state transitions."""

    def setUp(self) -> None:
        self.actual = ActualGrid(rows=6, cols=8, default_terrain=TerrainType.NORMAL)
        self.knowledge = KnowledgeGrid(rows=6, cols=8, default_terrain=TerrainType.NORMAL)
        self.sim = RescueSimulator(self.actual, self.knowledge)
        self.depot = Position(0, 0)

    def test_no_initial_route_releases_both_resources(self) -> None:
        """When no initial route exists on KnowledgeGrid, both resources are released and incident marked FAILED."""
        goal = Position(5, 3)
        for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            wall_pos = Position(goal.x + dx, goal.y + dy)
            self.knowledge.add_collapsed_building(wall_pos)
            self.actual.add_collapsed_building(wall_pos)

        veh = RescueVehicle("V1", VehicleType.FIRE_ENGINE, self.depot)
        resp = Responder("R1", "Firefighter", ResponderSpecialization.FIREFIGHTER, self.depot)
        inc = Incident("INC-NOWHERE", IncidentType.FIRE, severity=5, position=goal)

        self.sim.register_vehicle(veh)
        self.sim.register_responder(resp)
        self.sim.register_incident(inc)
        self.sim.allocate_resources_csp()

        self.assertFalse(veh.is_available())
        self.assertFalse(resp.is_available())
        self.assertTrue(inc.has_assigned_resources())

        mission = self.sim.execute_mission(inc)

        self.assertFalse(mission.success)
        self.assertTrue(veh.is_available())
        self.assertTrue(resp.is_available())
        self.assertFalse(inc.has_assigned_resources())
        self.assertEqual(inc.get_status(), IncidentStatus.FAILED)
        self.assertIsNotNone(inc.get_failure_reason())
        self.assertIn("initial", inc.get_failure_reason().lower())

        failed_events = self.sim.get_events_by_type("MISSION_FAILED")
        released_events = self.sim.get_events_by_type("RESOURCES_RELEASED")
        self.assertGreaterEqual(len(failed_events), 1)
        self.assertGreaterEqual(len(released_events), 1)

    def test_blocked_starting_position_releases_both_resources(self) -> None:
        """When vehicle start position is blocked, both resources are released immediately."""
        self.actual.add_collapsed_building(self.depot)
        veh = RescueVehicle("V1", VehicleType.FIRE_ENGINE, self.depot)
        resp = Responder("R1", "Firefighter", ResponderSpecialization.FIREFIGHTER, self.depot)
        inc = Incident("INC-BLOCKED-START", IncidentType.FIRE, severity=5, position=Position(4, 2))

        self.sim.register_vehicle(veh)
        self.sim.register_responder(resp)
        self.sim.register_incident(inc)
        self.sim.allocate_resources_csp()

        mission = self.sim.execute_mission(inc)

        self.assertFalse(mission.success)
        self.assertTrue(veh.is_available())
        self.assertTrue(resp.is_available())
        self.assertFalse(inc.has_assigned_resources())
        self.assertEqual(inc.get_status(), IncidentStatus.FAILED)
        self.assertIn("starting position is blocked", inc.get_failure_reason().lower())

        failed_events = self.sim.get_events_by_type("MISSION_FAILED")
        released_events = self.sim.get_events_by_type("RESOURCES_RELEASED")
        self.assertGreaterEqual(len(failed_events), 1)
        self.assertGreaterEqual(len(released_events), 1)

    def test_failed_dynamic_replanning_releases_both_resources(self) -> None:
        """When a discovered hazard completely blocks all routes, dynamic replanning failure releases resources."""
        # Unrevealed wall across column 3 in ActualGrid
        for r in range(6):
            self.actual.add_collapsed_building(Position(3, r))

        veh = RescueVehicle("V1", VehicleType.FIRE_ENGINE, self.depot)
        resp = Responder("R1", "Firefighter", ResponderSpecialization.FIREFIGHTER, self.depot)
        inc = Incident("INC-BEHIND-WALL", IncidentType.FIRE, severity=5, position=Position(5, 0))

        self.sim.register_vehicle(veh)
        self.sim.register_responder(resp)
        self.sim.register_incident(inc)
        self.sim.allocate_resources_csp()

        mission = self.sim.execute_mission(inc)

        self.assertFalse(mission.success)
        self.assertTrue(veh.is_available())
        self.assertTrue(resp.is_available())
        self.assertFalse(inc.has_assigned_resources())
        self.assertEqual(inc.get_status(), IncidentStatus.FAILED)
        self.assertIsNotNone(inc.get_failure_reason())

        failed_events = self.sim.get_events_by_type("MISSION_FAILED")
        released_events = self.sim.get_events_by_type("RESOURCES_RELEASED")
        self.assertGreaterEqual(len(failed_events), 1)
        self.assertGreaterEqual(len(released_events), 1)

    def test_maximum_step_failure_releases_both_resources(self) -> None:
        """When step limit is exceeded, mission fails and both resources are released."""
        veh = RescueVehicle("V1", VehicleType.FIRE_ENGINE, self.depot)
        resp = Responder("R1", "Firefighter", ResponderSpecialization.FIREFIGHTER, self.depot)
        inc = Incident("INC-FAR", IncidentType.FIRE, severity=5, position=Position(5, 5))

        self.sim.register_vehicle(veh)
        self.sim.register_responder(resp)
        self.sim.register_incident(inc)
        self.sim.allocate_resources_csp()

        mission = self.sim.execute_mission(inc, max_steps=2)

        self.assertFalse(mission.success)
        self.assertTrue(veh.is_available())
        self.assertTrue(resp.is_available())
        self.assertFalse(inc.has_assigned_resources())
        self.assertEqual(inc.get_status(), IncidentStatus.FAILED)
        self.assertIn("maximum", inc.get_failure_reason().lower())

        failed_events = self.sim.get_events_by_type("MISSION_FAILED")
        released_events = self.sim.get_events_by_type("RESOURCES_RELEASED")
        self.assertGreaterEqual(len(failed_events), 1)
        self.assertGreaterEqual(len(released_events), 1)

    def test_failed_incidents_not_repeatedly_dispatched(self) -> None:
        """Failed incidents transition to FAILED and are excluded from subsequent simulation dispatch iterations."""
        self.actual.add_collapsed_building(self.depot)
        veh = RescueVehicle("V1", VehicleType.FIRE_ENGINE, self.depot)
        resp = Responder("R1", "Firefighter", ResponderSpecialization.FIREFIGHTER, self.depot)
        inc = Incident("INC-FAIL", IncidentType.FIRE, severity=5, position=Position(4, 2))

        self.sim.register_vehicle(veh)
        self.sim.register_responder(resp)
        self.sim.register_incident(inc)

        report = self.sim.run_simulation()

        self.assertEqual(inc.get_status(), IncidentStatus.FAILED)
        self.assertEqual(report.failed_incidents, 1)
        self.assertEqual(report.resolved_incidents, 0)
        alloc_events = [
            e for e in self.sim.get_event_log()
            if e.event_type == "RESOURCES_ALLOCATED" and e.incident_id == "INC-FAIL"
        ]
        self.assertEqual(len(alloc_events), 1)

    def test_other_pending_incidents_can_use_released_resources(self) -> None:
        """When an incident mission fails, released vehicle and responder service other pending incidents."""
        for r in range(6):
            self.actual.add_collapsed_building(Position(3, r))

        veh = RescueVehicle("V1", VehicleType.FIRE_ENGINE, self.depot)
        resp = Responder("R1", "Firefighter", ResponderSpecialization.FIREFIGHTER, self.depot)

        inc1 = Incident("INC-BLOCKED", IncidentType.FIRE, severity=5, position=Position(5, 0))
        inc2 = Incident("INC-ACCESSIBLE", IncidentType.FIRE, severity=3, position=Position(2, 0))

        self.sim.register_vehicle(veh)
        self.sim.register_responder(resp)
        self.sim.register_incident(inc1)
        self.sim.register_incident(inc2)

        report = self.sim.run_simulation(service_duration=1)

        self.assertEqual(inc1.get_status(), IncidentStatus.FAILED)
        self.assertEqual(inc2.get_status(), IncidentStatus.RESOLVED)
        self.assertEqual(report.failed_incidents, 1)
        self.assertEqual(report.resolved_incidents, 1)
        self.assertEqual(report.total_incidents, 2)
        self.assertTrue(veh.is_available())
        self.assertTrue(resp.is_available())

    def test_failed_incidents_not_counted_as_resolved(self) -> None:
        """Failed incidents are counted under failed_incidents, never under resolved_incidents."""
        self.actual.add_collapsed_building(self.depot)
        veh = RescueVehicle("V1", VehicleType.FIRE_ENGINE, self.depot)
        resp = Responder("R1", "Firefighter", ResponderSpecialization.FIREFIGHTER, self.depot)
        inc = Incident("INC-FAIL-COUNT", IncidentType.FIRE, severity=5, position=Position(4, 2))

        self.sim.register_vehicle(veh)
        self.sim.register_responder(resp)
        self.sim.register_incident(inc)

        report = self.sim.run_simulation()

        self.assertEqual(report.resolved_incidents, 0)
        self.assertEqual(report.failed_incidents, 1)
        self.assertEqual(report.unallocated_incidents, 0)
        self.assertFalse(report.is_fully_resolved)

    def test_successful_mission_behaviour_remains_unchanged(self) -> None:
        """Successful missions continue to resolve incidents and release resources normally."""
        veh = RescueVehicle("V1", VehicleType.FIRE_ENGINE, self.depot)
        resp = Responder("R1", "Firefighter", ResponderSpecialization.FIREFIGHTER, self.depot)
        inc = Incident("INC-SUCCESS", IncidentType.FIRE, severity=5, position=Position(2, 1))

        self.sim.register_vehicle(veh)
        self.sim.register_responder(resp)
        self.sim.register_incident(inc)
        self.sim.allocate_resources_csp()

        mission = self.sim.execute_mission(inc, service_duration=1)

        self.assertTrue(mission.success)
        self.assertEqual(inc.get_status(), IncidentStatus.RESOLVED)
        self.assertTrue(veh.is_available())
        self.assertTrue(resp.is_available())
        self.assertFalse(inc.has_assigned_resources())

        resolved_events = self.sim.get_events_by_type("INCIDENT_RESOLVED")
        released_events = self.sim.get_events_by_type("RESOURCES_RELEASED")
        self.assertGreaterEqual(len(resolved_events), 1)
        self.assertGreaterEqual(len(released_events), 1)


if __name__ == "__main__":
    unittest.main()
