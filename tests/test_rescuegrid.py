"""
Comprehensive unit test suite for RescueGrid (Python AI Course Edition).
Directly mirrors and verifies the 13 C++ unit test suites and all domain invariants.
"""

import os
import sys
import unittest

# Ensure the root project directory is on the module search path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from models.position import Position
from models.incident import Incident, IncidentType, IncidentStatus
from models.responder import Responder, ResponderSpecialization
from models.rescue_vehicle import RescueVehicle, VehicleType
from core.rescue_manager import (
    RescueManager,
    RescueGridError,
    DuplicateEntityError,
    EntityNotFoundError,
    ResourceUnavailableError,
    InvalidStatusTransitionError,
)


class TestPositionCoordinates(unittest.TestCase):
    """Test Suite 1: Position coordinate initialization and string representations."""

    def test_default_position(self) -> None:
        pos = Position()
        self.assertEqual(pos.get_x(), 0, "Default Position X coordinate")
        self.assertEqual(pos.get_y(), 0, "Default Position Y coordinate")
        self.assertEqual(pos.x, 0)
        self.assertEqual(pos.y, 0)
        self.assertEqual(pos.to_string(), "(0, 0)", "Default Position toString format")
        self.assertEqual(str(pos), "(0, 0)")

    def test_custom_position(self) -> None:
        pos = Position(15, -42)
        self.assertEqual(pos.get_x(), 15, "Custom Position X coordinate")
        self.assertEqual(pos.get_y(), -42, "Custom Position Y coordinate")
        self.assertEqual(pos.x, 15)
        self.assertEqual(pos.y, -42)
        self.assertEqual(pos.to_string(), "(15, -42)", "Custom Position toString format")
        self.assertEqual(str(pos), "(15, -42)")

    def test_position_type_validation(self) -> None:
        with self.assertRaises(TypeError):
            Position("10", 20)  # type: ignore
        with self.assertRaises(TypeError):
            Position(10, 20.5)  # type: ignore
        with self.assertRaises(TypeError):
            Position(True, 20)  # type: ignore


class TestIncidentConstructionAndValidation(unittest.TestCase):
    """Test Suite 2: Incident construction, attributes, and boundary validation."""

    def test_valid_incident_construction(self) -> None:
        loc = Position(5, 10)
        inc = Incident("INC-101", IncidentType.FIRE, 4, loc)
        self.assertEqual(inc.get_id(), "INC-101", "Incident ID match")
        self.assertEqual(inc.id, "INC-101")
        self.assertEqual(inc.get_severity(), 4, "Incident severity match")
        self.assertEqual(inc.severity, 4)
        self.assertEqual(inc.get_type_string(), "Fire", "Incident type string")
        self.assertEqual(inc.get_status(), IncidentStatus.REPORTED, "Default incident status")
        self.assertEqual(inc.get_position().get_x(), 5, "Incident position X")
        self.assertEqual(inc.get_position().get_y(), 10, "Incident position Y")
        self.assertFalse(inc.has_assigned_resources())

    def test_severity_boundaries(self) -> None:
        loc = Position(5, 10)
        inc_min = Incident("INC-MIN", IncidentType.FLOOD, 1, loc)
        self.assertEqual(inc_min.get_severity(), 1, "Incident min severity 1")

        inc_max = Incident("INC-MAX", IncidentType.STRUCTURAL_COLLAPSE, 5, loc)
        self.assertEqual(inc_max.get_severity(), 5, "Incident max severity 5")

        with self.assertRaises(ValueError, msg="Severity 0 should throw ValueError"):
            Incident("INC-ERR", IncidentType.FIRE, 0, loc)

        with self.assertRaises(ValueError, msg="Severity 6 should throw ValueError"):
            Incident("INC-ERR", IncidentType.FIRE, 6, loc)

    def test_empty_id_validation(self) -> None:
        loc = Position(5, 10)
        with self.assertRaises(ValueError, msg="Empty Incident ID should throw ValueError"):
            Incident("", IncidentType.FIRE, 3, loc)
        with self.assertRaises(ValueError, msg="Whitespace Incident ID should throw ValueError"):
            Incident("   ", IncidentType.FIRE, 3, loc)


class TestIncidentStatusUpdates(unittest.TestCase):
    """Test Suite 3: Incident status modification and status string conversions."""

    def test_incident_status_transitions(self) -> None:
        loc = Position(2, 8)
        inc = Incident("INC-202", IncidentType.FLOOD, 2, loc)

        self.assertEqual(inc.get_status(), IncidentStatus.REPORTED, "Initial status Reported")
        self.assertEqual(inc.get_status_string(), "Reported", "Initial status string Reported")

        inc.set_status(IncidentStatus.IN_PROGRESS)
        self.assertEqual(inc.get_status(), IncidentStatus.IN_PROGRESS, "Updated status InProgress")
        self.assertEqual(inc.get_status_string(), "InProgress", "Updated status string InProgress")

        inc.set_status(IncidentStatus.RESOLVED)
        self.assertEqual(inc.get_status(), IncidentStatus.RESOLVED, "Updated status Resolved")
        self.assertEqual(inc.get_status_string(), "Resolved", "Updated status string Resolved")


class TestResponderConstructionAndUpdates(unittest.TestCase):
    """Test Suite 4: Responder construction, movement, and availability updates."""

    def test_responder_lifecycle(self) -> None:
        home_base = Position(0, 0)
        resp = Responder("RES-01", "Marcus Vance", ResponderSpecialization.FIREFIGHTER, home_base)

        self.assertEqual(resp.get_id(), "RES-01", "Responder ID match")
        self.assertEqual(resp.get_name(), "Marcus Vance", "Responder name match")
        self.assertEqual(resp.get_specialization_string(), "Firefighter", "Specialization string match")
        self.assertTrue(resp.is_available(), "Responder default availability should be true")
        self.assertEqual(resp.get_position().get_x(), 0, "Initial position X")
        self.assertEqual(resp.get_position().get_y(), 0, "Initial position Y")

        # Position update via Position object
        dispatch_target = Position(12, 34)
        resp.set_position(dispatch_target)
        self.assertEqual(resp.get_position().get_x(), 12, "Updated position X")
        self.assertEqual(resp.get_position().get_y(), 34, "Updated position Y")

        # Overloaded position update: set_position(int, int)
        resp.set_position(56, 78)
        self.assertEqual(resp.get_position().get_x(), 56, "Overloaded position X")
        self.assertEqual(resp.get_position().get_y(), 78, "Overloaded position Y")
        self.assertEqual(resp.get_position(), Position(56, 78), "Overloaded position matches Position(56, 78)")

        # Availability update
        resp.set_availability(False)
        self.assertFalse(resp.is_available(), "Updated availability should be false")

        resp.set_availability(True)
        self.assertTrue(resp.is_available(), "Updated availability should be true")

    def test_responder_validation(self) -> None:
        home_base = Position(0, 0)
        with self.assertRaises(ValueError, msg="Empty Responder name should throw ValueError"):
            Responder("RES-ERR", "", ResponderSpecialization.PARAMEDIC, home_base)

        with self.assertRaises(ValueError, msg="Empty Responder ID should throw ValueError"):
            Responder("", "Valid Name", ResponderSpecialization.PARAMEDIC, home_base)


class TestRescueVehicleConstructionAndUpdates(unittest.TestCase):
    """Test Suite 5: RescueVehicle construction, location updates, and availability."""

    def test_vehicle_lifecycle(self) -> None:
        station = Position(4, 4)
        vehicle = RescueVehicle("VEH-10", VehicleType.AMBULANCE, station)

        self.assertEqual(vehicle.get_id(), "VEH-10", "Vehicle ID match")
        self.assertEqual(vehicle.get_type_string(), "Ambulance", "Vehicle type string match")
        self.assertTrue(vehicle.is_available(), "Vehicle default availability should be true")
        self.assertEqual(vehicle.get_position().get_x(), 4, "Initial vehicle position X")
        self.assertEqual(vehicle.get_position().get_y(), 4, "Initial vehicle position Y")

        # Position update via Position object
        scene = Position(20, 30)
        vehicle.set_position(scene)
        self.assertEqual(vehicle.get_position().get_x(), 20, "Updated vehicle position X")
        self.assertEqual(vehicle.get_position().get_y(), 30, "Updated vehicle position Y")

        # Overloaded position update: set_position(int, int)
        vehicle.set_position(77, 88)
        self.assertEqual(vehicle.get_position().get_x(), 77, "Overloaded vehicle position X")
        self.assertEqual(vehicle.get_position().get_y(), 88, "Overloaded vehicle position Y")
        self.assertEqual(vehicle.get_position(), Position(77, 88), "Overloaded vehicle position matches Position(77, 88)")

        # Availability update
        vehicle.set_availability(False)
        self.assertFalse(vehicle.is_available(), "Updated vehicle availability should be false")

    def test_vehicle_validation(self) -> None:
        station = Position(4, 4)
        with self.assertRaises(ValueError, msg="Empty Vehicle ID should throw ValueError"):
            RescueVehicle("", VehicleType.RESCUE_VAN, station)


class TestManagerRegistrationAndListing(unittest.TestCase):
    """Test Suite 6: Manager entity registration and listing counts."""

    def test_registration_and_counts(self) -> None:
        manager = RescueManager()
        self.assertEqual(manager.get_incident_count(), 0, "Initial incident count should be 0")
        self.assertEqual(manager.get_responder_count(), 0, "Initial responder count should be 0")
        self.assertEqual(manager.get_vehicle_count(), 0, "Initial vehicle count should be 0")

        # Register incidents
        manager.register_incident(Incident("INC-1", IncidentType.FIRE, 3, Position(10, 10)))
        manager.register_incident(Incident("INC-2", IncidentType.FLOOD, 5, Position(20, 20)))
        self.assertEqual(manager.get_incident_count(), 2, "Incident count after registration")
        self.assertEqual(manager.get_incidents()[0].get_id(), "INC-1", "First incident ID")
        self.assertEqual(manager.get_incidents()[1].get_id(), "INC-2", "Second incident ID")

        # Register responders
        manager.register_responder(Responder("R-1", "Alice", ResponderSpecialization.FIREFIGHTER, Position(0, 0)))
        manager.register_responder(Responder("R-2", "Bob", ResponderSpecialization.PARAMEDIC, Position(0, 0)))
        self.assertEqual(manager.get_responder_count(), 2, "Responder count after registration")
        self.assertEqual(manager.get_available_responder_count(), 2, "Available responder count")

        # Register vehicles
        manager.register_vehicle(RescueVehicle("V-1", VehicleType.FIRE_ENGINE, Position(0, 0)))
        manager.register_vehicle(RescueVehicle("V-2", VehicleType.AMBULANCE, Position(0, 0)))
        self.assertEqual(manager.get_vehicle_count(), 2, "Vehicle count after registration")
        self.assertEqual(manager.get_available_vehicle_count(), 2, "Available vehicle count")


class TestManagerSearchAndDuplicateHandling(unittest.TestCase):
    """Test Suite 7: Entity lookup and duplicate identifier rejection."""

    def test_search_and_duplicates(self) -> None:
        manager = RescueManager()
        manager.register_incident(Incident("INC-A", IncidentType.FIRE, 2, Position(5, 5)))
        manager.register_responder(Responder("R-A", "Carlos", ResponderSpecialization.RESCUE_SPECIALIST, Position(0, 0)))
        manager.register_vehicle(RescueVehicle("V-A", VehicleType.RESCUE_VAN, Position(0, 0)))

        # Existing searches
        found_inc = manager.find_incident("INC-A")
        self.assertIsNotNone(found_inc, "Incident INC-A should be found")
        self.assertEqual(found_inc.get_id(), "INC-A", "Found incident ID matches")
        self.assertEqual(found_inc.get_severity(), 2, "Found incident severity matches")

        self.assertTrue(manager.has_incident("INC-A"), "has_incident returns true for INC-A")
        self.assertTrue(manager.has_responder("R-A"), "has_responder returns true for R-A")
        self.assertTrue(manager.has_vehicle("V-A"), "has_vehicle returns true for V-A")

        # Missing searches
        self.assertIsNone(manager.find_incident("NON-EXISTENT"), "Missing incident returns None")
        self.assertIsNone(manager.find_responder("NON-EXISTENT"), "Missing responder returns None")
        self.assertIsNone(manager.find_vehicle("NON-EXISTENT"), "Missing vehicle returns None")
        self.assertFalse(manager.has_incident("NON-EXISTENT"), "has_incident returns false for missing ID")

        # Duplicate registrations
        with self.assertRaises(ValueError, msg="Duplicate incident registration should throw ValueError"):
            manager.register_incident(Incident("INC-A", IncidentType.FLOOD, 1, Position(1, 1)))

        with self.assertRaises(ValueError, msg="Duplicate responder registration should throw ValueError"):
            manager.register_responder(Responder("R-A", "Duplicate Name", ResponderSpecialization.PARAMEDIC, Position(0, 0)))

        with self.assertRaises(ValueError, msg="Duplicate vehicle registration should throw ValueError"):
            manager.register_vehicle(RescueVehicle("V-A", VehicleType.FIRE_ENGINE, Position(0, 0)))


class TestDispatchResourcesSuccess(unittest.TestCase):
    """Test Suite 8: Successful dispatch coordination and state updates."""

    def test_successful_dispatch(self) -> None:
        manager = RescueManager()
        manager.register_incident(Incident("INC-DISP", IncidentType.FIRE, 4, Position(50, 75)))
        manager.register_responder(Responder("R-DISP", "Elena", ResponderSpecialization.FIREFIGHTER, Position(0, 0)))
        manager.register_vehicle(RescueVehicle("V-DISP", VehicleType.FIRE_ENGINE, Position(0, 0)))

        self.assertEqual(manager.get_available_responder_count(), 1, "Initially 1 available responder")
        self.assertEqual(manager.get_available_vehicle_count(), 1, "Initially 1 available vehicle")

        # Execute dispatch
        result = manager.dispatch_resources("INC-DISP")
        self.assertTrue(result, "Dispatch should return true on success")

        # Verify incident state
        inc = manager.find_incident("INC-DISP")
        self.assertIsNotNone(inc, "Incident must exist")
        self.assertEqual(inc.get_status(), IncidentStatus.IN_PROGRESS, "Incident status should be InProgress")
        self.assertTrue(inc.has_assigned_resources(), "Incident should have assigned resources")
        self.assertEqual(inc.get_assigned_responder_id(), "R-DISP", "Assigned responder ID match")
        self.assertEqual(inc.get_assigned_vehicle_id(), "V-DISP", "Assigned vehicle ID match")

        # Verify responder state
        resp = manager.find_responder("R-DISP")
        self.assertIsNotNone(resp, "Responder must exist")
        self.assertFalse(resp.is_available(), "Responder should now be unavailable")
        self.assertEqual(resp.get_position().get_x(), 50, "Responder moved to incident X")
        self.assertEqual(resp.get_position().get_y(), 75, "Responder moved to incident Y")

        # Verify vehicle state
        veh = manager.find_vehicle("V-DISP")
        self.assertIsNotNone(veh, "Vehicle must exist")
        self.assertFalse(veh.is_available(), "Vehicle should now be unavailable")
        self.assertEqual(veh.get_position().get_x(), 50, "Vehicle moved to incident X")
        self.assertEqual(veh.get_position().get_y(), 75, "Vehicle moved to incident Y")

        self.assertEqual(manager.get_available_responder_count(), 0, "0 available responders remaining")
        self.assertEqual(manager.get_available_vehicle_count(), 0, "0 available vehicles remaining")


class TestDispatchResourcesUnavailableAndRejection(unittest.TestCase):
    """Test Suite 9: Dispatch failure handling for unavailable resources and invalid states."""

    def test_dispatch_rejections(self) -> None:
        manager = RescueManager()

        # 1. Dispatching to non-existent incident
        with self.assertRaises(ValueError, msg="Dispatch to missing incident should throw ValueError"):
            manager.dispatch_resources("MISSING-INC")

        # 2. Incident exists, but no responders or vehicles registered
        manager.register_incident(Incident("INC-NO-RES", IncidentType.FLOOD, 3, Position(10, 10)))
        with self.assertRaises(RuntimeError, msg="Dispatch with no responders should throw RuntimeError"):
            manager.dispatch_resources("INC-NO-RES")

        # 3. Responder registered, but no vehicles registered
        manager.register_responder(Responder("R-1", "Dan", ResponderSpecialization.PARAMEDIC, Position(0, 0)))
        with self.assertRaises(RuntimeError, msg="Dispatch with no vehicles should throw RuntimeError"):
            manager.dispatch_resources("INC-NO-RES")

        # 4. Vehicle registered -> now dispatch can succeed
        manager.register_vehicle(RescueVehicle("V-1", VehicleType.AMBULANCE, Position(0, 0)))
        self.assertTrue(manager.dispatch_resources("INC-NO-RES"))

        # 5. Attempting to dispatch again to an incident already InProgress
        with self.assertRaises(RuntimeError, msg="Dispatch to already InProgress incident should throw RuntimeError"):
            manager.dispatch_resources("INC-NO-RES")

        # 6. Attempting to dispatch to a Resolved incident
        manager.register_incident(Incident("INC-RESOLVED", IncidentType.FIRE, 1, Position(2, 2), IncidentStatus.RESOLVED))
        with self.assertRaises(RuntimeError, msg="Dispatch to already Resolved incident should throw RuntimeError"):
            manager.dispatch_resources("INC-RESOLVED")


class TestPreventDoubleAssignment(unittest.TestCase):
    """Test Suite 10: Prevention of allocating unavailable resources to multiple incidents."""

    def test_double_assignment_prevention(self) -> None:
        manager = RescueManager()
        manager.register_incident(Incident("INC-1", IncidentType.FIRE, 2, Position(10, 10)))
        manager.register_incident(Incident("INC-2", IncidentType.FLOOD, 4, Position(20, 20)))

        # Register only ONE responder and ONE vehicle
        manager.register_responder(Responder("R-SOLE", "Solo Responder", ResponderSpecialization.RESCUE_SPECIALIST, Position(0, 0)))
        manager.register_vehicle(RescueVehicle("V-SOLE", VehicleType.RESCUE_VAN, Position(0, 0)))

        # Dispatch INC-1
        manager.dispatch_resources("INC-1")

        # Attempt to dispatch INC-2: must fail because all resources are busy
        with self.assertRaises(RuntimeError, msg="Dispatching INC-2 with busy resources should throw RuntimeError"):
            manager.dispatch_resources("INC-2")

        # Verify INC-2 was NOT modified
        inc2 = manager.find_incident("INC-2")
        self.assertIsNotNone(inc2)
        self.assertEqual(inc2.get_status(), IncidentStatus.REPORTED, "INC-2 must remain Reported")
        self.assertFalse(inc2.has_assigned_resources(), "INC-2 must not have resources assigned")


class TestStatusUpdateAndResourceRelease(unittest.TestCase):
    """Test Suite 11: Resolution of incidents and automatic return of resources to available pool."""

    def test_status_update_and_resource_release(self) -> None:
        manager = RescueManager()
        manager.register_incident(Incident("INC-X", IncidentType.FIRE, 3, Position(30, 30)))
        manager.register_incident(Incident("INC-Y", IncidentType.FLOOD, 2, Position(40, 40)))

        manager.register_responder(Responder("R-SHARED", "Shared Responder", ResponderSpecialization.FIREFIGHTER, Position(0, 0)))
        manager.register_vehicle(RescueVehicle("V-SHARED", VehicleType.FIRE_ENGINE, Position(0, 0)))

        # Dispatch INC-X
        manager.dispatch_resources("INC-X")
        self.assertEqual(manager.get_available_responder_count(), 0, "No available responders while INC-X in progress")

        # Resolve INC-X
        manager.update_incident_status("INC-X", IncidentStatus.RESOLVED)

        # Verify INC-X resolved and resources freed
        inc_x = manager.find_incident("INC-X")
        self.assertIsNotNone(inc_x)
        self.assertEqual(inc_x.get_status(), IncidentStatus.RESOLVED, "INC-X is Resolved")
        self.assertFalse(inc_x.has_assigned_resources(), "INC-X released resource bindings")

        resp = manager.find_responder("R-SHARED")
        self.assertIsNotNone(resp)
        self.assertTrue(resp.is_available(), "Responder is available again after INC-X resolution")

        veh = manager.find_vehicle("V-SHARED")
        self.assertIsNotNone(veh)
        self.assertTrue(veh.is_available(), "Vehicle is available again after INC-X resolution")

        self.assertEqual(manager.get_available_responder_count(), 1, "1 available responder after release")
        self.assertEqual(manager.get_available_vehicle_count(), 1, "1 available vehicle after release")

        # Now INC-Y can be dispatched successfully using the released resources!
        y_result = manager.dispatch_resources("INC-Y")
        self.assertTrue(y_result, "INC-Y dispatch succeeds using freed resources")

        inc_y = manager.find_incident("INC-Y")
        self.assertIsNotNone(inc_y)
        self.assertEqual(inc_y.get_status(), IncidentStatus.IN_PROGRESS, "INC-Y is now InProgress")
        self.assertEqual(inc_y.get_assigned_responder_id(), "R-SHARED", "INC-Y assigned to R-SHARED")

        # Non-existent incident status update throws ValueError
        with self.assertRaises(ValueError, msg="Updating non-existent incident should throw ValueError"):
            manager.update_incident_status("MISSING", IncidentStatus.RESOLVED)


class TestIncidentLifecycleAndInvalidTransitions(unittest.TestCase):
    """Test Suite 12: Incident lifecycle state machine validation and strict transitions."""

    def test_lifecycle_rules(self) -> None:
        manager = RescueManager()

        # 1. Attempting to mark an incident InProgress without a successful dispatch
        manager.register_incident(Incident("INC-L1", IncidentType.FIRE, 2, Position(10, 10)))
        with self.assertRaises(RuntimeError, msg="Direct Reported -> InProgress transition without dispatch must throw"):
            manager.update_incident_status("INC-L1", IncidentStatus.IN_PROGRESS)

        inc_l1 = manager.find_incident("INC-L1")
        self.assertIsNotNone(inc_l1)
        self.assertEqual(inc_l1.get_status(), IncidentStatus.REPORTED, "Incident must remain Reported after rejected transition")
        self.assertFalse(inc_l1.has_assigned_resources(), "Incident must have no assigned resources")

        # 2. Dispatch resources to make INC-L1 active (InProgress)
        manager.register_responder(Responder("R-L1", "Responder 1", ResponderSpecialization.FIREFIGHTER, Position(0, 0)))
        manager.register_vehicle(RescueVehicle("V-L1", VehicleType.FIRE_ENGINE, Position(0, 0)))
        manager.dispatch_resources("INC-L1")

        self.assertEqual(inc_l1.get_status(), IncidentStatus.IN_PROGRESS, "INC-L1 is now InProgress")
        self.assertTrue(inc_l1.has_assigned_resources(), "INC-L1 now has assigned resources")
        resp_l1 = manager.find_responder("R-L1")
        veh_l1 = manager.find_vehicle("V-L1")
        self.assertIsNotNone(resp_l1)
        self.assertIsNotNone(veh_l1)
        self.assertFalse(resp_l1.is_available(), "R-L1 is unavailable during active dispatch")
        self.assertFalse(veh_l1.is_available(), "V-L1 is unavailable during active dispatch")

        # 3. Attempting to move an active incident with assigned resources back to Reported
        with self.assertRaises(RuntimeError, msg="Active incident cannot be reverted from InProgress to Reported"):
            manager.update_incident_status("INC-L1", IncidentStatus.REPORTED)

        # Confirm rejected transition leaves resource assignments and availability unchanged
        self.assertEqual(inc_l1.get_status(), IncidentStatus.IN_PROGRESS, "INC-L1 must remain InProgress")
        self.assertTrue(inc_l1.has_assigned_resources(), "INC-L1 must still retain assigned resources")
        self.assertEqual(inc_l1.get_assigned_responder_id(), "R-L1", "Assigned responder must still be R-L1")
        self.assertEqual(inc_l1.get_assigned_vehicle_id(), "V-L1", "Assigned vehicle must still be V-L1")
        self.assertFalse(resp_l1.is_available(), "R-L1 must remain unavailable after rejected transition")
        self.assertFalse(veh_l1.is_available(), "V-L1 must remain unavailable after rejected transition")

        # 4. Valid resolution releases assigned resources
        manager.update_incident_status("INC-L1", IncidentStatus.RESOLVED)
        self.assertEqual(inc_l1.get_status(), IncidentStatus.RESOLVED, "INC-L1 is now Resolved")
        self.assertFalse(inc_l1.has_assigned_resources(), "INC-L1 resources must be cleared")
        self.assertTrue(resp_l1.is_available(), "R-L1 must be released to available")
        self.assertTrue(veh_l1.is_available(), "V-L1 must be released to available")

        # 5. Attempting to reopen a Resolved incident
        with self.assertRaises(RuntimeError, msg="Resolved incident cannot be reopened to Reported"):
            manager.update_incident_status("INC-L1", IncidentStatus.REPORTED)
        with self.assertRaises(RuntimeError, msg="Resolved incident cannot be reopened to InProgress"):
            manager.update_incident_status("INC-L1", IncidentStatus.IN_PROGRESS)
        with self.assertRaises(RuntimeError, msg="Resolved incident cannot transition to Resolved again"):
            manager.update_incident_status("INC-L1", IncidentStatus.RESOLVED)
        with self.assertRaises(RuntimeError, msg="Resolved incident cannot receive dispatch"):
            manager.dispatch_resources("INC-L1")
        self.assertEqual(inc_l1.get_status(), IncidentStatus.RESOLVED, "INC-L1 remains Resolved")

        # 6. Direct Reported -> Resolved transition without dispatch (e.g. false alarm)
        manager.register_incident(Incident("INC-L2", IncidentType.FLOOD, 1, Position(20, 20)))
        manager.update_incident_status("INC-L2", IncidentStatus.RESOLVED)
        inc_l2 = manager.find_incident("INC-L2")
        self.assertIsNotNone(inc_l2)
        self.assertEqual(inc_l2.get_status(), IncidentStatus.RESOLVED, "Reported incident directly resolved")
        self.assertFalse(inc_l2.has_assigned_resources(), "Directly resolved incident has no assigned resources")
        with self.assertRaises(RuntimeError, msg="Directly resolved incident cannot be reopened"):
            manager.update_incident_status("INC-L2", IncidentStatus.REPORTED)

        # 7. Resolving one incident must NOT release resources belonging to another incident
        iso_manager = RescueManager()
        iso_manager.register_incident(Incident("INC-ISO1", IncidentType.FIRE, 3, Position(30, 30)))
        iso_manager.register_incident(Incident("INC-ISO2", IncidentType.FLOOD, 4, Position(40, 40)))
        iso_manager.register_responder(Responder("R-ISO1", "Resp ISO 1", ResponderSpecialization.FIREFIGHTER, Position(0, 0)))
        iso_manager.register_responder(Responder("R-ISO2", "Resp ISO 2", ResponderSpecialization.PARAMEDIC, Position(0, 0)))
        iso_manager.register_vehicle(RescueVehicle("V-ISO1", VehicleType.FIRE_ENGINE, Position(0, 0)))
        iso_manager.register_vehicle(RescueVehicle("V-ISO2", VehicleType.AMBULANCE, Position(0, 0)))

        iso_manager.dispatch_resources("INC-ISO1")
        iso_manager.dispatch_resources("INC-ISO2")

        # Both incidents are active
        inc_iso1 = iso_manager.find_incident("INC-ISO1")
        inc_iso2 = iso_manager.find_incident("INC-ISO2")
        resp_iso1 = iso_manager.find_responder("R-ISO1")
        resp_iso2 = iso_manager.find_responder("R-ISO2")
        veh_iso1 = iso_manager.find_vehicle("V-ISO1")
        veh_iso2 = iso_manager.find_vehicle("V-ISO2")

        self.assertFalse(resp_iso1.is_available(), "R-ISO1 busy with INC-ISO1")
        self.assertFalse(resp_iso2.is_available(), "R-ISO2 busy with INC-ISO2")

        # Resolve INC-ISO1 only
        iso_manager.update_incident_status("INC-ISO1", IncidentStatus.RESOLVED)

        # Verify INC-ISO1 freed its resources
        self.assertEqual(inc_iso1.get_status(), IncidentStatus.RESOLVED, "INC-ISO1 is resolved")
        self.assertTrue(resp_iso1.is_available(), "R-ISO1 is now available")
        self.assertTrue(veh_iso1.is_available(), "V-ISO1 is now available")

        # Verify INC-ISO2 resources are UNTOUCHED
        self.assertEqual(inc_iso2.get_status(), IncidentStatus.IN_PROGRESS, "INC-ISO2 remains InProgress")
        self.assertTrue(inc_iso2.has_assigned_resources(), "INC-ISO2 retains assigned resources")
        self.assertEqual(inc_iso2.get_assigned_responder_id(), "R-ISO2", "INC-ISO2 still assigned to R-ISO2")
        self.assertEqual(inc_iso2.get_assigned_vehicle_id(), "V-ISO2", "INC-ISO2 still assigned to V-ISO2")
        self.assertFalse(resp_iso2.is_available(), "R-ISO2 remains unavailable")
        self.assertFalse(veh_iso2.is_available(), "V-ISO2 remains unavailable")


class TestPositionOperatorsAndOverloading(unittest.TestCase):
    """Test Suite 13: Coordinate comparisons, string rendering, and method overloading."""

    def test_position_overloading_and_operators(self) -> None:
        p_default = Position()
        self.assertEqual(p_default.get_x(), 0, "Default Position constructor X is 0")
        self.assertEqual(p_default.get_y(), 0, "Default Position constructor Y is 0")
        self.assertEqual(p_default.to_string(), "(0, 0)", "Default Position toString format")

        p_param = Position(15, 20)
        self.assertEqual(p_param.get_x(), 15, "Parameterized Position constructor X")
        self.assertEqual(p_param.get_y(), 20, "Parameterized Position constructor Y")
        self.assertEqual(p_param.to_string(), "(15, 20)", "Parameterized Position toString format")

        p_negative = Position(-8, -42)
        self.assertEqual(p_negative.get_x(), -8, "Negative Position constructor X")
        self.assertEqual(p_negative.get_y(), -42, "Negative Position constructor Y")

        # Requirement 1: pos1 == pos2 returns true when coordinates are identical
        p1 = Position(10, 20)
        p2 = Position(10, 20)
        self.assertTrue(p1 == p2, "Identical positions must compare equal with operator==")
        self.assertTrue(p_default == Position(0, 0), "Default position equals Position(0, 0)")

        # Requirement 2: pos1 != pos2 returns true when x differs, y differs, or both differ
        p_diff_x = Position(11, 20)
        p_diff_y = Position(10, 21)
        p_diff_both = Position(99, 88)

        self.assertTrue(p1 != p_diff_x, "operator!= returns true when X differs")
        self.assertTrue(p1 != p_diff_y, "operator!= returns true when Y differs")
        self.assertTrue(p1 != p_diff_both, "operator!= returns true when both X and Y differ")

        self.assertFalse(p1 == p_diff_x, "operator== returns false when X differs")
        self.assertFalse(p1 == p_diff_y, "operator== returns false when Y differs")
        self.assertFalse(p1 == p_diff_both, "operator== returns false when both X and Y differ")

        # Requirement 3: operator!= is the logical inverse of operator==
        self.assertEqual(p1 == p2, not (p1 != p2), "operator!= must be logical inverse of operator==")
        self.assertEqual(p1 == p_diff_x, not (p1 != p_diff_x))
        self.assertEqual(p1 == p_diff_y, not (p1 != p_diff_y))
        self.assertEqual(p1 == p_diff_both, not (p1 != p_diff_both))

        # Requirement 4 & 5: String formatting and chaining
        self.assertEqual(f"At {p_param} confirmed", "At (15, 20) confirmed")
        self.assertEqual(str(Position(33, -99)), Position(33, -99).to_string())

        # Flexible argument form: Responder.set_position(int, int) matches set_position(Position)
        base_pos = Position(0, 0)
        resp1 = Responder("R-OV1", "Alice", ResponderSpecialization.FIREFIGHTER, base_pos)
        resp2 = Responder("R-OV2", "Bob", ResponderSpecialization.FIREFIGHTER, base_pos)

        resp1.set_position(Position(25, 35))
        resp2.set_position(25, 35)
        self.assertEqual(resp2.get_position(), resp1.get_position(), "Responder set_position(int, int) matches set_position(Position)")
        self.assertEqual(resp2.get_position().get_x(), 25, "Responder X after set_position(int, int)")
        self.assertEqual(resp2.get_position().get_y(), 35, "Responder Y after set_position(int, int)")

        # Flexible argument form: RescueVehicle.set_position(int, int) matches set_position(Position)
        veh1 = RescueVehicle("V-OV1", VehicleType.FIRE_ENGINE, base_pos)
        veh2 = RescueVehicle("V-OV2", VehicleType.FIRE_ENGINE, base_pos)

        veh1.set_position(Position(45, 55))
        veh2.set_position(45, 55)
        self.assertEqual(veh2.get_position(), veh1.get_position(), "RescueVehicle set_position(int, int) matches set_position(Position)")
        self.assertEqual(veh2.get_position().get_x(), 45, "RescueVehicle X after set_position(int, int)")
        self.assertEqual(veh2.get_position().get_y(), 55, "RescueVehicle Y after set_position(int, int)")


class TestCollectionProtectionAndInvariants(unittest.TestCase):
    """Test Suite 14: Collection encapsulation, status synchronization, and error consistency."""

    def test_internal_collections_protection(self) -> None:
        """Verify that mutating returned lists does not compromise RescueManager internal collections."""
        manager = RescueManager()
        manager.register_incident(Incident("INC-P1", IncidentType.FIRE, 3, Position(10, 10)))
        manager.register_responder(Responder("R-P1", "Officer Test", ResponderSpecialization.FIREFIGHTER, Position(0, 0)))
        manager.register_vehicle(RescueVehicle("V-P1", VehicleType.FIRE_ENGINE, Position(0, 0)))

        # Retrieve collections
        incidents = manager.get_incidents()
        responders = manager.get_responders()
        vehicles = manager.get_vehicles()

        # Attempt to mutate returned lists
        incidents.clear()
        responders.append(Responder("R-ROGUE", "Rogue", ResponderSpecialization.PARAMEDIC, Position(1, 1)))
        vehicles.pop()

        # Verify manager's internal state is completely unaffected
        self.assertEqual(manager.get_incident_count(), 1, "Incident count must remain 1 after external clear()")
        self.assertEqual(manager.get_responder_count(), 1, "Responder count must remain 1 after external append()")
        self.assertEqual(manager.get_vehicle_count(), 1, "Vehicle count must remain 1 after external pop()")
        self.assertTrue(manager.has_incident("INC-P1"), "Original incident must remain registered")
        self.assertFalse(manager.has_responder("R-ROGUE"), "Appended rogue responder must not exist in manager")
        self.assertTrue(manager.has_vehicle("V-P1"), "Popped vehicle must still exist in manager")

    def test_direct_status_change_via_incident_delegation(self) -> None:
        """Verify that calling set_status() directly on a managed incident routes through manager and releases resources."""
        manager = RescueManager()
        manager.register_incident(Incident("INC-DEL", IncidentType.FIRE, 4, Position(15, 25)))
        manager.register_responder(Responder("R-DEL", "Alex", ResponderSpecialization.FIREFIGHTER, Position(0, 0)))
        manager.register_vehicle(RescueVehicle("V-DEL", VehicleType.FIRE_ENGINE, Position(0, 0)))

        manager.dispatch_resources("INC-DEL")
        inc = manager.find_incident("INC-DEL")
        resp = manager.find_responder("R-DEL")
        veh = manager.find_vehicle("V-DEL")

        self.assertIsNotNone(inc)
        self.assertIsNotNone(resp)
        self.assertIsNotNone(veh)
        self.assertFalse(resp.is_available())
        self.assertFalse(veh.is_available())
        self.assertTrue(inc.has_assigned_resources())

        # Directly invoke set_status on the incident
        inc.set_status(IncidentStatus.RESOLVED)

        # Invariant verification: resources must have been released back to available pool
        self.assertEqual(inc.get_status(), IncidentStatus.RESOLVED)
        self.assertFalse(inc.has_assigned_resources(), "Incident bindings must be cleared upon resolution")
        self.assertTrue(resp.is_available(), "Assigned responder must be returned to available")
        self.assertTrue(veh.is_available(), "Assigned vehicle must be returned to available")
        self.assertEqual(manager.get_available_responder_count(), 1)
        self.assertEqual(manager.get_available_vehicle_count(), 1)

    def test_direct_status_change_invalid_transitions(self) -> None:
        """Verify that invalid status transitions via direct set_status() are rejected."""
        manager = RescueManager()
        manager.register_incident(Incident("INC-INV", IncidentType.FLOOD, 2, Position(5, 5)))
        inc = manager.find_incident("INC-INV")
        self.assertIsNotNone(inc)

        # 1. Reported -> InProgress directly without dispatch
        with self.assertRaises(InvalidStatusTransitionError):
            inc.set_status(IncidentStatus.IN_PROGRESS)

        # 2. Directly resolve it (valid false alarm)
        inc.set_status(IncidentStatus.RESOLVED)
        self.assertEqual(inc.get_status(), IncidentStatus.RESOLVED)

        # 3. Attempt to transition from Resolved (terminal state)
        with self.assertRaises(InvalidStatusTransitionError):
            inc.set_status(IncidentStatus.REPORTED)
        with self.assertRaises(InvalidStatusTransitionError):
            inc.set_status(IncidentStatus.IN_PROGRESS)
        with self.assertRaises(InvalidStatusTransitionError):
            inc.set_status(IncidentStatus.RESOLVED)

        # 4. Standalone incident terminal state enforcement
        standalone = Incident("INC-ST", IncidentType.FIRE, 1, Position(0, 0), IncidentStatus.RESOLVED)
        with self.assertRaises(InvalidStatusTransitionError):
            standalone.set_status(IncidentStatus.REPORTED)

    def test_resource_consistency_after_failed_dispatch(self) -> None:
        """Verify resource availability is not corrupted when a dispatch operation fails halfway."""
        manager = RescueManager()
        manager.register_incident(Incident("INC-FAIL", IncidentType.FLOOD, 3, Position(20, 30)))
        # Register a responder, but NO vehicles
        manager.register_responder(Responder("R-LONE", "Lone Ranger", ResponderSpecialization.PARAMEDIC, Position(0, 0)))

        self.assertEqual(manager.get_available_responder_count(), 1)

        # Dispatch must fail due to missing vehicle
        with self.assertRaises(ResourceUnavailableError):
            manager.dispatch_resources("INC-FAIL")

        # Invariant check: responder must remain available, incident must remain Reported without resources
        resp = manager.find_responder("R-LONE")
        inc = manager.find_incident("INC-FAIL")
        self.assertIsNotNone(resp)
        self.assertIsNotNone(inc)
        self.assertTrue(resp.is_available(), "Responder must remain available after failed dispatch")
        self.assertEqual(resp.get_position(), Position(0, 0), "Responder position must not change on failed dispatch")
        self.assertEqual(inc.get_status(), IncidentStatus.REPORTED, "Incident must remain Reported")
        self.assertFalse(inc.has_assigned_resources(), "Incident must not hold resources")
        self.assertEqual(manager.get_available_responder_count(), 1)

    def test_invalid_registration_object_types(self) -> None:
        """Verify manager rejects registrations of incorrect object types."""
        manager = RescueManager()

        with self.assertRaises(TypeError):
            manager.register_incident("not an incident")  # type: ignore
        with self.assertRaises(TypeError):
            manager.register_responder(12345)  # type: ignore
        with self.assertRaises(TypeError):
            manager.register_vehicle(None)  # type: ignore


if __name__ == "__main__":
    unittest.main()
