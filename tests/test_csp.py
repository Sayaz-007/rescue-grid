"""
Comprehensive unit test suite for Multi-Agent Resource Allocation using CSP in RescueGrid (Phase 8).

Verifies:
- CSP problem formulation and constraint satisfaction
- Hard constraints (availability, specialization, vehicle compatibility, resource uniqueness)
- MRV variable selection, Degree heuristic tie-breaking, LCV value ordering
- Forward checking domain wipeout detection and recursive backtracking
- Allocation metrics and status contracts (COMPLETE, PARTIAL, FAILED)
- Atomic RescueManager integration and non-regression of manual dispatch
"""

import os
import sys
import unittest

# Ensure root workspace directory is on module search path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from models.position import Position
from models.incident import Incident, IncidentType, IncidentStatus
from models.responder import Responder, ResponderSpecialization
from models.rescue_vehicle import RescueVehicle, VehicleType
from core.rescue_manager import RescueManager
from models.exceptions import EntityNotFoundError
from algorithms.csp_result import CSPResult
from algorithms.csp import (
    CSPSolver,
    allocate_resources_csp,
    DEFAULT_RESPONDER_COMPATIBILITY,
    DEFAULT_VEHICLE_COMPATIBILITY,
)


class TestCSPBasics(unittest.TestCase):
    """Test Suite 1: Fundamental CSP solver behavior, trivial inputs, and solvability."""

    def setUp(self) -> None:
        self.solver = CSPSolver()
        self.base_pos = Position(0, 0)

    def test_empty_incident_input(self) -> None:
        """Empty incident list returns complete allocation with zero assignments."""
        res = self.solver.solve([], [], [])
        self.assertTrue(res.is_complete)
        self.assertEqual(res.status, "COMPLETE")
        self.assertEqual(res.assigned_count, 0)
        self.assertEqual(res.target_incident_count, 0)
        self.assertEqual(res.assignments, {})
        self.assertEqual(res.unassigned_incident_ids, [])

    def test_single_incident_success(self) -> None:
        """Single incident is successfully matched with compatible resources."""
        inc = Incident("INC-1", IncidentType.FIRE, 3, Position(1, 1))
        resp = Responder("R-1", "Alice", ResponderSpecialization.FIREFIGHTER, self.base_pos)
        veh = RescueVehicle("V-1", VehicleType.FIRE_ENGINE, self.base_pos)

        res = self.solver.solve([inc], [resp], [veh])
        self.assertTrue(res.is_complete)
        self.assertEqual(res.status, "COMPLETE")
        self.assertEqual(res.assigned_count, 1)
        self.assertTrue(res.has_assignment("INC-1"))

        assigned_resp, assigned_veh = res.get_assignment("INC-1")  # type: ignore
        self.assertEqual(assigned_resp.id, "R-1")
        self.assertEqual(assigned_veh.id, "V-1")

    def test_multiple_incidents_success(self) -> None:
        """Multiple distinct incidents receive compatible, disjoint resources."""
        incidents = [
            Incident("INC-FIRE", IncidentType.FIRE, 4, Position(2, 2)),
            Incident("INC-COLLAPSE", IncidentType.STRUCTURAL_COLLAPSE, 5, Position(4, 4)),
            Incident("INC-MED", IncidentType.MEDICAL, 3, Position(6, 6)),
        ]
        responders = [
            Responder("R-FF", "Firefighter One", ResponderSpecialization.FIREFIGHTER, self.base_pos),
            Responder("R-RS", "Rescue Spec One", ResponderSpecialization.RESCUE_SPECIALIST, self.base_pos),
            Responder("R-MED", "Paramedic One", ResponderSpecialization.PARAMEDIC, self.base_pos),
        ]
        vehicles = [
            RescueVehicle("V-FE", VehicleType.FIRE_ENGINE, self.base_pos),
            RescueVehicle("V-RV", VehicleType.RESCUE_VAN, self.base_pos),
            RescueVehicle("V-AMB", VehicleType.AMBULANCE, self.base_pos),
        ]

        res = self.solver.solve(incidents, responders, vehicles)
        self.assertTrue(res.is_complete)
        self.assertEqual(res.status, "COMPLETE")
        self.assertEqual(res.assigned_count, 3)

        # Verify correct pairings
        self.assertEqual(res.get_assigned_responder("INC-FIRE").id, "R-FF")  # type: ignore
        self.assertEqual(res.get_assigned_vehicle("INC-FIRE").id, "V-FE")    # type: ignore
        self.assertEqual(res.get_assigned_responder("INC-COLLAPSE").id, "R-RS")  # type: ignore
        self.assertEqual(res.get_assigned_vehicle("INC-COLLAPSE").id, "V-RV")    # type: ignore
        self.assertEqual(res.get_assigned_responder("INC-MED").id, "R-MED")  # type: ignore
        self.assertEqual(res.get_assigned_vehicle("INC-MED").id, "V-AMB")    # type: ignore

    def test_impossible_allocation_detected(self) -> None:
        """When insufficient compatible resources exist, solver reports FAILED."""
        # Two fire incidents, but only one fire engine exists
        incidents = [
            Incident("INC-F1", IncidentType.FIRE, 3, Position(1, 1)),
            Incident("INC-F2", IncidentType.FIRE, 4, Position(2, 2)),
        ]
        responders = [
            Responder("R-1", "Firefighter 1", ResponderSpecialization.FIREFIGHTER, self.base_pos),
            Responder("R-2", "Firefighter 2", ResponderSpecialization.FIREFIGHTER, self.base_pos),
        ]
        vehicles = [
            RescueVehicle("V-1", VehicleType.FIRE_ENGINE, self.base_pos),  # only 1 engine!
            RescueVehicle("V-2", VehicleType.AMBULANCE, self.base_pos),     # incompatible
        ]

        res = self.solver.solve(incidents, responders, vehicles)
        self.assertFalse(res.is_complete)
        self.assertEqual(res.status, "FAILED")
        self.assertEqual(res.assigned_count, 0)
        self.assertEqual(len(res.unassigned_incident_ids), 2)
        self.assertIn("INC-F1", res.unassigned_incident_ids)
        self.assertIn("INC-F2", res.unassigned_incident_ids)

    def test_invalid_input_types_raise_type_error(self) -> None:
        """Reject non-collection or wrong-typed arguments with TypeError."""
        with self.assertRaises(TypeError):
            self.solver.solve("bad", [], [])  # type: ignore
        with self.assertRaises(TypeError):
            self.solver.solve([], "bad", [])  # type: ignore
        with self.assertRaises(TypeError):
            self.solver.solve([], [], "bad")  # type: ignore
        with self.assertRaises(TypeError):
            self.solver.solve([123], [], [])  # type: ignore


class TestCSPConstraints(unittest.TestCase):
    """Test Suite 2: Verification of hard constraints."""

    def setUp(self) -> None:
        self.solver = CSPSolver()
        self.base_pos = Position(0, 0)

    def test_unavailable_responders_excluded(self) -> None:
        """Responders marked is_available=False must never be assigned."""
        inc = Incident("INC-1", IncidentType.FIRE, 3, Position(1, 1))
        busy_resp = Responder("R-BUSY", "Busy Firefighter", ResponderSpecialization.FIREFIGHTER, self.base_pos, is_available=False)
        veh = RescueVehicle("V-1", VehicleType.FIRE_ENGINE, self.base_pos)

        res = self.solver.solve([inc], [busy_resp], [veh])
        self.assertFalse(res.is_complete)
        self.assertEqual(res.status, "FAILED")

    def test_unavailable_vehicles_excluded(self) -> None:
        """Vehicles marked is_available=False must never be assigned."""
        inc = Incident("INC-1", IncidentType.FIRE, 3, Position(1, 1))
        resp = Responder("R-1", "Firefighter", ResponderSpecialization.FIREFIGHTER, self.base_pos)
        busy_veh = RescueVehicle("V-BUSY", VehicleType.FIRE_ENGINE, self.base_pos, is_available=False)

        res = self.solver.solve([inc], [resp], [busy_veh])
        self.assertFalse(res.is_complete)
        self.assertEqual(res.status, "FAILED")

    def test_responder_specialization_enforced(self) -> None:
        """Fire incident must reject Paramedics; Medical incident must reject Firefighters."""
        fire_inc = Incident("INC-FIRE", IncidentType.FIRE, 3, Position(1, 1))
        paramedic = Responder("R-MED", "Paramedic", ResponderSpecialization.PARAMEDIC, self.base_pos)
        engine = RescueVehicle("V-FE", VehicleType.FIRE_ENGINE, self.base_pos)

        res = self.solver.solve([fire_inc], [paramedic], [engine])
        self.assertFalse(res.is_complete)
        self.assertEqual(res.status, "FAILED")

    def test_vehicle_compatibility_enforced(self) -> None:
        """Collapse incident must reject Ambulance when RescueVan is required."""
        collapse_inc = Incident("INC-COL", IncidentType.STRUCTURAL_COLLAPSE, 4, Position(1, 1))
        specialist = Responder("R-SPEC", "Rescue Specialist", ResponderSpecialization.RESCUE_SPECIALIST, self.base_pos)
        ambulance = RescueVehicle("V-AMB", VehicleType.AMBULANCE, self.base_pos)

        res = self.solver.solve([collapse_inc], [specialist], [ambulance])
        self.assertFalse(res.is_complete)
        self.assertEqual(res.status, "FAILED")

    def test_custom_incident_explicit_requirements(self) -> None:
        """Explicit required_specialization and required_vehicle_type override incident type defaults."""
        flood_medical = Incident(
            "INC-MED-FLOOD",
            IncidentType.FLOOD,
            4,
            Position(1, 1),
            required_specialization=ResponderSpecialization.PARAMEDIC,
            required_vehicle_type=VehicleType.AMBULANCE,
        )
        self.assertEqual(flood_medical.required_specialization, ResponderSpecialization.PARAMEDIC)
        self.assertEqual(flood_medical.required_vehicle_type, VehicleType.AMBULANCE)

        ff = Responder("R-FF", "Firefighter", ResponderSpecialization.FIREFIGHTER, self.base_pos)
        engine = RescueVehicle("V-FE", VehicleType.FIRE_ENGINE, self.base_pos)
        paramedic = Responder("R-MED", "Paramedic", ResponderSpecialization.PARAMEDIC, self.base_pos)
        ambulance = RescueVehicle("V-AMB", VehicleType.AMBULANCE, self.base_pos)

        # Standard flood responders should be rejected because of explicit override
        res_fail = self.solver.solve([flood_medical], [ff], [engine])
        self.assertFalse(res_fail.is_complete)

        # Explicitly required resources should succeed
        res_ok = self.solver.solve([flood_medical], [paramedic], [ambulance])
        self.assertTrue(res_ok.is_complete)
        self.assertEqual(res_ok.get_assigned_responder("INC-MED-FLOOD").id, "R-MED")  # type: ignore

    def test_no_double_assignment_of_responder(self) -> None:
        """A single responder cannot be assigned to two simultaneous incidents."""
        inc1 = Incident("INC-1", IncidentType.FIRE, 3, Position(1, 1))
        inc2 = Incident("INC-2", IncidentType.FIRE, 4, Position(2, 2))
        solo_resp = Responder("R-SOLO", "Solo Firefighter", ResponderSpecialization.FIREFIGHTER, self.base_pos)
        veh1 = RescueVehicle("V-1", VehicleType.FIRE_ENGINE, self.base_pos)
        veh2 = RescueVehicle("V-2", VehicleType.FIRE_ENGINE, self.base_pos)

        res = self.solver.solve([inc1, inc2], [solo_resp], [veh1, veh2])
        self.assertFalse(res.is_complete)
        self.assertEqual(res.status, "FAILED")

    def test_no_double_assignment_of_vehicle(self) -> None:
        """A single vehicle cannot be assigned to two simultaneous incidents."""
        inc1 = Incident("INC-1", IncidentType.FIRE, 3, Position(1, 1))
        inc2 = Incident("INC-2", IncidentType.FIRE, 4, Position(2, 2))
        resp1 = Responder("R-1", "Firefighter 1", ResponderSpecialization.FIREFIGHTER, self.base_pos)
        resp2 = Responder("R-2", "Firefighter 2", ResponderSpecialization.FIREFIGHTER, self.base_pos)
        solo_veh = RescueVehicle("V-SOLO", VehicleType.FIRE_ENGINE, self.base_pos)

        res = self.solver.solve([inc1, inc2], [resp1, resp2], [solo_veh])
        self.assertFalse(res.is_complete)
        self.assertEqual(res.status, "FAILED")

    def test_resolved_incidents_excluded(self) -> None:
        """Resolved incidents are filtered out and receive no allocations."""
        resolved_inc = Incident("INC-DONE", IncidentType.FIRE, 1, Position(1, 1), status=IncidentStatus.RESOLVED)
        active_inc = Incident("INC-ACT", IncidentType.FIRE, 3, Position(2, 2))
        resp = Responder("R-1", "Firefighter", ResponderSpecialization.FIREFIGHTER, self.base_pos)
        veh = RescueVehicle("V-1", VehicleType.FIRE_ENGINE, self.base_pos)

        res = self.solver.solve([resolved_inc, active_inc], [resp], [veh])
        self.assertTrue(res.is_complete)
        self.assertEqual(res.assigned_count, 1)
        self.assertFalse(res.has_assignment("INC-DONE"))
        self.assertTrue(res.has_assignment("INC-ACT"))

    def test_incidents_with_active_resources_excluded(self) -> None:
        """Incidents that already have assigned resources are excluded from new allocation."""
        busy_inc = Incident("INC-BUSY", IncidentType.FIRE, 2, Position(1, 1))
        busy_inc.assign_resources("R-OLD", "V-OLD")
        active_inc = Incident("INC-NEW", IncidentType.FIRE, 4, Position(2, 2))

        resp = Responder("R-NEW", "Firefighter", ResponderSpecialization.FIREFIGHTER, self.base_pos)
        veh = RescueVehicle("V-NEW", VehicleType.FIRE_ENGINE, self.base_pos)

        res = self.solver.solve([busy_inc, active_inc], [resp], [veh])
        self.assertTrue(res.is_complete)
        self.assertEqual(res.assigned_count, 1)
        self.assertFalse(res.has_assignment("INC-BUSY"))
        self.assertTrue(res.has_assignment("INC-NEW"))


class TestCSPSearchStrategies(unittest.TestCase):
    """Test Suite 3: Verification of MRV, Degree Heuristic, LCV, Forward Checking, and Backtracking."""

    def setUp(self) -> None:
        self.base_pos = Position(0, 0)

    def test_mrv_selects_most_constrained_variable(self) -> None:
        """MRV prioritizes the incident with the smallest remaining candidate domain."""
        inc_tight = Incident("INC-TIGHT", IncidentType.STRUCTURAL_COLLAPSE, 4, Position(1, 1))
        inc_broad = Incident("INC-BROAD", IncidentType.FIRE, 3, Position(2, 2))

        responders = [
            Responder("R-RS", "Rescue Spec", ResponderSpecialization.RESCUE_SPECIALIST, self.base_pos),
            Responder("R-FF1", "Firefighter 1", ResponderSpecialization.FIREFIGHTER, self.base_pos),
            Responder("R-FF2", "Firefighter 2", ResponderSpecialization.FIREFIGHTER, self.base_pos),
        ]
        vehicles = [
            RescueVehicle("V-RV", VehicleType.RESCUE_VAN, self.base_pos),
            RescueVehicle("V-FE1", VehicleType.FIRE_ENGINE, self.base_pos),
            RescueVehicle("V-FE2", VehicleType.FIRE_ENGINE, self.base_pos),
        ]

        solver = CSPSolver(enable_mrv=True)
        domains = solver.build_initial_domains([inc_broad, inc_tight], responders, vehicles)

        self.assertEqual(len(domains["INC-TIGHT"]), 1)
        self.assertEqual(len(domains["INC-BROAD"]), 4)

        selected = solver._select_variable([inc_broad, inc_tight], domains)
        self.assertEqual(selected.id, "INC-TIGHT")

    def test_degree_heuristic_breaks_mrv_ties(self) -> None:
        """When domain sizes are tied, Degree Heuristic selects variable with highest contention."""
        inc_a = Incident("INC-A", IncidentType.FIRE, 3, Position(1, 1))
        inc_b = Incident("INC-B", IncidentType.MEDICAL, 3, Position(2, 2))
        inc_c = Incident("INC-C", IncidentType.FIRE, 3, Position(3, 3))

        shared_resp = Responder("R-SHARED", "Shared FF", ResponderSpecialization.FIREFIGHTER, self.base_pos)
        solo_paramedic = Responder("R-MED", "Solo Med", ResponderSpecialization.PARAMEDIC, self.base_pos)
        engine1 = RescueVehicle("V-FE1", VehicleType.FIRE_ENGINE, self.base_pos)
        ambulance = RescueVehicle("V-AMB", VehicleType.AMBULANCE, self.base_pos)

        solver = CSPSolver(enable_mrv=True, enable_degree=True)
        domains = {
            "INC-A": [(shared_resp, engine1)],
            "INC-B": [(solo_paramedic, ambulance)],
            "INC-C": [(shared_resp, engine1)],
        }

        selected = solver._select_variable([inc_b, inc_a], domains)
        self.assertEqual(selected.id, "INC-A")

    def test_lcv_orders_candidates_least_constraining_first(self) -> None:
        """LCV heuristic orders candidate pairs that rule out the fewest choices first."""
        inc_target = Incident("INC-TGT", IncidentType.FLOOD, 3, Position(1, 1))
        inc_other = Incident("INC-OTHER", IncidentType.FIRE, 3, Position(2, 2))

        ff = Responder("R-FF", "Firefighter", ResponderSpecialization.FIREFIGHTER, self.base_pos)
        spec = Responder("R-SPEC", "Rescue Spec", ResponderSpecialization.RESCUE_SPECIALIST, self.base_pos)
        engine = RescueVehicle("V-FE", VehicleType.FIRE_ENGINE, self.base_pos)
        van = RescueVehicle("V-VAN", VehicleType.RESCUE_VAN, self.base_pos)

        solver = CSPSolver(enable_lcv=True)
        domains = {
            "INC-TGT": [(spec, van), (ff, engine)],
            "INC-OTHER": [(ff, engine)],  # INC-OTHER specifically needs (ff, engine)
        }

        # (ff, engine) rules out 1 option for INC-OTHER.
        # (spec, van) rules out 0 options for INC-OTHER.
        # Therefore, LCV MUST place (spec, van) first!
        ordered = solver._order_domain_values(
            inc_target, domains["INC-TGT"], [inc_target, inc_other], domains
        )
        self.assertEqual(ordered[0][0].id, "R-SPEC")
        self.assertEqual(ordered[0][1].id, "V-VAN")

    def test_forward_checking_detects_empty_domain(self) -> None:
        """Forward checking prunes conflicting options and flags domain wipeout."""
        inc1 = Incident("INC-1", IncidentType.FIRE, 3, Position(1, 1))
        inc2 = Incident("INC-2", IncidentType.FIRE, 4, Position(2, 2))

        resp = Responder("R-1", "Only FF", ResponderSpecialization.FIREFIGHTER, self.base_pos)
        veh = RescueVehicle("V-1", VehicleType.FIRE_ENGINE, self.base_pos)

        solver = CSPSolver(enable_forward_checking=True)
        domains = {
            "INC-1": [(resp, veh)],
            "INC-2": [(resp, veh)],
        }

        is_viable, pruned = solver._forward_check(inc1, (resp, veh), [inc1, inc2], domains)
        self.assertFalse(is_viable)
        self.assertEqual(pruned, {})

    def test_backtracking_recovers_from_conflict(self) -> None:
        """Solver successfully backtracks when a greedy decision leads to a dead end."""
        inc_flood = Incident("INC-A-FLOOD", IncidentType.FLOOD, 3, Position(1, 1))
        inc_collapse = Incident("INC-B-COLLAPSE", IncidentType.STRUCTURAL_COLLAPSE, 4, Position(2, 2))

        spec = Responder("R-1-SPEC", "Rescue Spec", ResponderSpecialization.RESCUE_SPECIALIST, self.base_pos)
        ff = Responder("R-2-FF", "Firefighter", ResponderSpecialization.FIREFIGHTER, self.base_pos)

        van = RescueVehicle("V-1-VAN", VehicleType.RESCUE_VAN, self.base_pos)
        engine = RescueVehicle("V-2-FE", VehicleType.FIRE_ENGINE, self.base_pos)

        # Force solver to evaluate without MRV so it considers INC-A-FLOOD first
        solver = CSPSolver(enable_mrv=False, enable_lcv=False, enable_forward_checking=True)
        res = solver.solve([inc_flood, inc_collapse], [spec, ff], [van, engine])

        self.assertTrue(res.is_complete)
        self.assertEqual(res.status, "COMPLETE")
        self.assertGreater(res.backtracks, 0)

        # Verify final assignment is non-conflicting and satisfies both
        self.assertEqual(res.get_assigned_responder("INC-B-COLLAPSE").id, "R-1-SPEC")  # type: ignore
        self.assertEqual(res.get_assigned_vehicle("INC-B-COLLAPSE").id, "V-1-VAN")      # type: ignore
        self.assertEqual(res.get_assigned_responder("INC-A-FLOOD").id, "R-2-FF")        # type: ignore
        self.assertEqual(res.get_assigned_vehicle("INC-A-FLOOD").id, "V-2-FE")          # type: ignore

    def test_deterministic_reproducibility(self) -> None:
        """Repeated runs of the CSP solver yield identical assignments and metrics."""
        incidents = [
            Incident("INC-1", IncidentType.FIRE, 3, Position(1, 1)),
            Incident("INC-2", IncidentType.FLOOD, 4, Position(2, 2)),
            Incident("INC-3", IncidentType.MEDICAL, 2, Position(3, 3)),
        ]
        responders = [
            Responder("R-FF", "Firefighter", ResponderSpecialization.FIREFIGHTER, self.base_pos),
            Responder("R-RS", "Rescue Spec", ResponderSpecialization.RESCUE_SPECIALIST, self.base_pos),
            Responder("R-MED", "Paramedic", ResponderSpecialization.PARAMEDIC, self.base_pos),
        ]
        vehicles = [
            RescueVehicle("V-FE", VehicleType.FIRE_ENGINE, self.base_pos),
            RescueVehicle("V-VAN", VehicleType.RESCUE_VAN, self.base_pos),
            RescueVehicle("V-AMB", VehicleType.AMBULANCE, self.base_pos),
        ]

        solver = CSPSolver()
        res1 = solver.solve(incidents, responders, vehicles)
        res2 = solver.solve(incidents, responders, vehicles)

        self.assertEqual(res1.status, res2.status)
        self.assertEqual(res1.is_complete, res2.is_complete)
        self.assertEqual(res1.nodes_explored, res2.nodes_explored)
        self.assertEqual(res1.backtracks, res2.backtracks)
        for inc_id in ["INC-1", "INC-2", "INC-3"]:
            self.assertEqual(res1.get_assigned_responder(inc_id).id, res2.get_assigned_responder(inc_id).id)  # type: ignore
            self.assertEqual(res1.get_assigned_vehicle(inc_id).id, res2.get_assigned_vehicle(inc_id).id)      # type: ignore


class TestCSPResultAndPartialAllocation(unittest.TestCase):
    """Test Suite 4: Result model contracts, metrics, and partial allocation mode."""

    def setUp(self) -> None:
        self.base_pos = Position(0, 0)

    def test_partial_allocation_mode(self) -> None:
        """When allow_partial=True, solver returns maximum partial allocation instead of empty."""
        # 3 incidents, but only resources for 2
        incidents = [
            Incident("INC-1", IncidentType.FIRE, 3, Position(1, 1)),
            Incident("INC-2", IncidentType.FIRE, 4, Position(2, 2)),
            Incident("INC-3", IncidentType.FIRE, 5, Position(3, 3)),
        ]
        responders = [
            Responder("R-1", "FF 1", ResponderSpecialization.FIREFIGHTER, self.base_pos),
            Responder("R-2", "FF 2", ResponderSpecialization.FIREFIGHTER, self.base_pos),
        ]
        vehicles = [
            RescueVehicle("V-1", VehicleType.FIRE_ENGINE, self.base_pos),
            RescueVehicle("V-2", VehicleType.FIRE_ENGINE, self.base_pos),
        ]

        solver = CSPSolver()
        res = solver.solve(incidents, responders, vehicles, allow_partial=True)

        self.assertFalse(res.is_complete)
        self.assertEqual(res.status, "PARTIAL")
        self.assertEqual(res.assigned_count, 2)
        self.assertEqual(res.unassigned_count, 1)
        self.assertEqual(len(res.unassigned_incident_ids), 1)

    def test_result_dictionary_and_string_representation(self) -> None:
        """Verify to_dict() and to_string() exports."""
        inc = Incident("INC-1", IncidentType.FIRE, 3, Position(1, 1))
        resp = Responder("R-1", "Marcus Vance", ResponderSpecialization.FIREFIGHTER, self.base_pos)
        veh = RescueVehicle("V-1", VehicleType.FIRE_ENGINE, self.base_pos)

        res = allocate_resources_csp([inc], [resp], [veh])
        d = res.to_dict()
        s = res.to_string()

        self.assertEqual(d["status"], "COMPLETE")
        self.assertTrue(d["is_complete"])
        self.assertEqual(d["assigned_count"], 1)
        self.assertIn("INC-1", d["assignments"])
        self.assertIn("Marcus Vance", s)
        self.assertIn("FIREENGINE", s.upper())


class TestRescueManagerCSPIntegration(unittest.TestCase):
    """Test Suite 5: Integration with RescueManager and atomicity."""

    def setUp(self) -> None:
        self.manager = RescueManager()
        self.base_pos = Position(0, 0)

    def test_successful_manager_allocation_commits_atomically(self) -> None:
        """Successful CSP allocation updates manager resources and statuses atomically."""
        inc1 = Incident("INC-101", IncidentType.FIRE, 4, Position(5, 5))
        inc2 = Incident("INC-102", IncidentType.STRUCTURAL_COLLAPSE, 5, Position(10, 10))

        resp1 = Responder("R-1", "Alice", ResponderSpecialization.FIREFIGHTER, self.base_pos)
        resp2 = Responder("R-2", "Bob", ResponderSpecialization.RESCUE_SPECIALIST, self.base_pos)

        veh1 = RescueVehicle("V-1", VehicleType.FIRE_ENGINE, self.base_pos)
        veh2 = RescueVehicle("V-2", VehicleType.RESCUE_VAN, self.base_pos)

        self.manager.register_incident(inc1)
        self.manager.register_incident(inc2)
        self.manager.register_responder(resp1)
        self.manager.register_responder(resp2)
        self.manager.register_vehicle(veh1)
        self.manager.register_vehicle(veh2)

        res = self.manager.allocate_resources_csp()
        self.assertTrue(res.is_complete)
        self.assertEqual(res.status, "COMPLETE")

        # Verify incidents transitioned to InProgress with bindings
        self.assertEqual(inc1.status, IncidentStatus.IN_PROGRESS)
        self.assertEqual(inc2.status, IncidentStatus.IN_PROGRESS)
        self.assertTrue(inc1.has_assigned_resources())
        self.assertTrue(inc2.has_assigned_resources())

        # Verify resources marked unavailable and relocated
        self.assertFalse(resp1.is_available())
        self.assertFalse(resp2.is_available())
        self.assertFalse(veh1.is_available())
        self.assertFalse(veh2.is_available())
        self.assertEqual(resp1.position, inc1.position)
        self.assertEqual(veh1.position, inc1.position)
        self.assertEqual(resp2.position, inc2.position)
        self.assertEqual(veh2.position, inc2.position)

        # Available counts updated
        self.assertEqual(self.manager.get_available_responder_count(), 0)
        self.assertEqual(self.manager.get_available_vehicle_count(), 0)

    def test_failed_manager_allocation_leaves_state_unchanged(self) -> None:
        """Infeasible CSP allocation commits zero changes, preserving initial state."""
        inc1 = Incident("INC-F1", IncidentType.FIRE, 3, Position(5, 5))
        inc2 = Incident("INC-F2", IncidentType.FIRE, 4, Position(6, 6))

        resp = Responder("R-1", "Solo FF", ResponderSpecialization.FIREFIGHTER, self.base_pos)
        veh = RescueVehicle("V-1", VehicleType.FIRE_ENGINE, self.base_pos)

        self.manager.register_incident(inc1)
        self.manager.register_incident(inc2)
        self.manager.register_responder(resp)
        self.manager.register_vehicle(veh)

        res = self.manager.allocate_resources_csp()
        self.assertFalse(res.is_complete)
        self.assertEqual(res.status, "FAILED")

        # All incidents remain in Reported status with no resources
        self.assertEqual(inc1.status, IncidentStatus.REPORTED)
        self.assertEqual(inc2.status, IncidentStatus.REPORTED)
        self.assertFalse(inc1.has_assigned_resources())
        self.assertFalse(inc2.has_assigned_resources())

        # All resources remain available at base position
        self.assertTrue(resp.is_available())
        self.assertTrue(veh.is_available())
        self.assertEqual(resp.position, self.base_pos)
        self.assertEqual(veh.position, self.base_pos)

    def test_manager_rejects_unregistered_incident(self) -> None:
        """Manager raises EntityNotFoundError if an incident is not registered."""
        unregistered = Incident("INC-GHOST", IncidentType.FIRE, 3, Position(1, 1))
        with self.assertRaises(EntityNotFoundError):
            self.manager.allocate_resources_csp(incidents=[unregistered])

    def test_existing_manual_dispatch_remains_functional(self) -> None:
        """Existing manual dispatch_resources() method functions with zero regressions."""
        inc = Incident("INC-MANUAL", IncidentType.FIRE, 3, Position(2, 3))
        resp = Responder("R-M", "Manual FF", ResponderSpecialization.FIREFIGHTER, self.base_pos)
        veh = RescueVehicle("V-M", VehicleType.FIRE_ENGINE, self.base_pos)

        self.manager.register_incident(inc)
        self.manager.register_responder(resp)
        self.manager.register_vehicle(veh)

        success = self.manager.dispatch_resources("INC-MANUAL")
        self.assertTrue(success)
        self.assertEqual(inc.status, IncidentStatus.IN_PROGRESS)
        self.assertEqual(inc.assigned_responder_id, "R-M")
        self.assertEqual(inc.assigned_vehicle_id, "V-M")
        self.assertFalse(resp.is_available())
        self.assertFalse(veh.is_available())


if __name__ == "__main__":
    unittest.main()
