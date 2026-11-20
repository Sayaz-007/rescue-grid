"""
Menu workflows and input validation for the RescueGrid interactive CLI.
"""

import sys
from typing import Optional
from models.position import Position
from models.incident import Incident, IncidentType, IncidentStatus
from models.responder import Responder, ResponderSpecialization
from models.rescue_vehicle import RescueVehicle, VehicleType
from core.rescue_manager import RescueManager


def read_line() -> Optional[str]:
    """Read a single line from standard input, stripping whitespace.

    Returns:
        The stripped string, or None if EOF or interrupt is encountered.
    """
    try:
        line = input()
        return line.strip()
    except (EOFError, KeyboardInterrupt):
        return None


def read_non_empty_string(prompt: str) -> Optional[str]:
    """Repeatedly prompt until a non-blank string is entered.

    Args:
        prompt: Display prompt.

    Returns:
        Non-empty stripped string, or None on EOF.
    """
    while True:
        try:
            val = input(prompt).strip()
            if val:
                return val
            print("  [!] Input cannot be blank. Please try again.")
        except (EOFError, KeyboardInterrupt):
            return None


def read_int(
    prompt: str,
    min_val: Optional[int] = None,
    max_val: Optional[int] = None,
) -> Optional[int]:
    """Repeatedly prompt until a valid integer within [min_val, max_val] is entered.

    Args:
        prompt: Display prompt.
        min_val: Minimum acceptable integer (inclusive, optional).
        max_val: Maximum acceptable integer (inclusive, optional).

    Returns:
        Validated integer, or None on EOF.
    """
    while True:
        try:
            line = input(prompt).strip()
            if not line:
                print("  [!] Input cannot be empty. Please enter a valid number.")
                continue

            parsed = int(line)
            if min_val is not None and parsed < min_val:
                print(f"  [!] Value must be between {min_val} and {max_val}. Please try again.")
                continue
            if max_val is not None and parsed > max_val:
                print(f"  [!] Value must be between {min_val} and {max_val}. Please try again.")
                continue

            return parsed
        except ValueError:
            print("  [!] Invalid numeric format. Please enter an integer.")
        except (EOFError, KeyboardInterrupt):
            return None


def handle_register_incident(manager: RescueManager) -> None:
    """Handle CLI option 1: Register an incident."""
    print("\n--- Register New Incident ---")
    incident_id = read_non_empty_string("Enter Incident ID (e.g., INC-101): ")
    if incident_id is None:
        return

    if manager.has_incident(incident_id):
        print(f"  [!] An incident with ID '{incident_id}' already exists.")
        return

    print("Select Incident Type:")
    print("  1. Fire")
    print("  2. Flood")
    print("  3. Structural Collapse")
    type_choice = read_int("Enter choice (1-3): ", 1, 3)
    if type_choice is None:
        return

    incident_type = IncidentType.FIRE
    if type_choice == 2:
        incident_type = IncidentType.FLOOD
    elif type_choice == 3:
        incident_type = IncidentType.STRUCTURAL_COLLAPSE

    severity = read_int("Enter Severity rating (1 to 5): ", 1, 5)
    if severity is None:
        return

    x = read_int("Enter Grid Coordinate X: ")
    if x is None:
        return
    y = read_int("Enter Grid Coordinate Y: ")
    if y is None:
        return

    try:
        incident = Incident(incident_id, incident_type, severity, Position(x, y))
        manager.register_incident(incident)
        print(f"  [+] Incident registered successfully: {incident.to_string()}")
    except Exception as ex:
        print(f"  [!] Error registering incident: {ex}")


def handle_list_incidents(manager: RescueManager) -> None:
    """Handle CLI option 2: List all incidents."""
    count = manager.get_incident_count()
    print(f"\n--- Registered Incidents ({count}) ---")
    incidents = manager.get_incidents()
    if not incidents:
        print("  No incidents currently registered.")
        return

    for i, inc in enumerate(incidents, start=1):
        print(f"  {i}. {inc.to_string()}")


def handle_search_incident(manager: RescueManager) -> None:
    """Handle CLI option 3: Search for an incident by ID."""
    print("\n--- Search Incident by ID ---")
    incident_id = read_non_empty_string("Enter Incident ID to search: ")
    if incident_id is None:
        return

    incident = manager.find_incident(incident_id)
    if incident is not None:
        print(f"  [+] Found: {incident.to_string()}")
        print(f"      Grid Location: {incident.get_position().to_string()}")
    else:
        print(f"  [-] No incident found with ID '{incident_id}'.")


def handle_register_responder(manager: RescueManager) -> None:
    """Handle CLI option 4: Register a responder."""
    print("\n--- Register New Responder ---")
    responder_id = read_non_empty_string("Enter Responder ID (e.g., RES-01): ")
    if responder_id is None:
        return

    if manager.has_responder(responder_id):
        print(f"  [!] A responder with ID '{responder_id}' already exists.")
        return

    name = read_non_empty_string("Enter Responder Full Name: ")
    if name is None:
        return

    print("Select Specialization:")
    print("  1. Firefighter")
    print("  2. Paramedic")
    print("  3. Rescue Specialist")
    spec_choice = read_int("Enter choice (1-3): ", 1, 3)
    if spec_choice is None:
        return

    spec = ResponderSpecialization.FIREFIGHTER
    if spec_choice == 2:
        spec = ResponderSpecialization.PARAMEDIC
    elif spec_choice == 3:
        spec = ResponderSpecialization.RESCUE_SPECIALIST

    x = read_int("Enter Initial Station Coordinate X: ")
    if x is None:
        return
    y = read_int("Enter Initial Station Coordinate Y: ")
    if y is None:
        return

    try:
        responder = Responder(responder_id, name, spec, Position(x, y))
        manager.register_responder(responder)
        print(f"  [+] Responder registered successfully: {responder.to_string()}")
    except Exception as ex:
        print(f"  [!] Error registering responder: {ex}")


def handle_list_responders(manager: RescueManager) -> None:
    """Handle CLI option 5: List all responders."""
    total = manager.get_responder_count()
    available = manager.get_available_responder_count()
    print(f"\n--- Registered Responders ({total} total, {available} available) ---")
    responders = manager.get_responders()
    if not responders:
        print("  No responders currently registered.")
        return

    for i, resp in enumerate(responders, start=1):
        print(f"  {i}. {resp.to_string()}")


def handle_register_vehicle(manager: RescueManager) -> None:
    """Handle CLI option 6: Register a rescue vehicle."""
    print("\n--- Register New Rescue Vehicle ---")
    vehicle_id = read_non_empty_string("Enter Vehicle ID (e.g., VEH-01): ")
    if vehicle_id is None:
        return

    if manager.has_vehicle(vehicle_id):
        print(f"  [!] A vehicle with ID '{vehicle_id}' already exists.")
        return

    print("Select Vehicle Type:")
    print("  1. Fire Engine")
    print("  2. Ambulance")
    print("  3. Rescue Van")
    type_choice = read_int("Enter choice (1-3): ", 1, 3)
    if type_choice is None:
        return

    vehicle_type = VehicleType.FIRE_ENGINE
    if type_choice == 2:
        vehicle_type = VehicleType.AMBULANCE
    elif type_choice == 3:
        vehicle_type = VehicleType.RESCUE_VAN

    x = read_int("Enter Initial Station Coordinate X: ")
    if x is None:
        return
    y = read_int("Enter Initial Station Coordinate Y: ")
    if y is None:
        return

    try:
        vehicle = RescueVehicle(vehicle_id, vehicle_type, Position(x, y))
        manager.register_vehicle(vehicle)
        print(f"  [+] Rescue vehicle registered successfully: {vehicle.to_string()}")
    except Exception as ex:
        print(f"  [!] Error registering vehicle: {ex}")


def handle_list_vehicles(manager: RescueManager) -> None:
    """Handle CLI option 7: List all rescue vehicles."""
    total = manager.get_vehicle_count()
    available = manager.get_available_vehicle_count()
    print(f"\n--- Registered Vehicles ({total} total, {available} available) ---")
    vehicles = manager.get_vehicles()
    if not vehicles:
        print("  No vehicles currently registered.")
        return

    for i, veh in enumerate(vehicles, start=1):
        print(f"  {i}. {veh.to_string()}")


def handle_dispatch(manager: RescueManager) -> None:
    """Handle CLI option 8: Dispatch resources to an incident."""
    print("\n--- Dispatch Resources to Incident ---")
    incident_id = read_non_empty_string("Enter Incident ID to receive dispatch: ")
    if incident_id is None:
        return

    try:
        manager.dispatch_resources(incident_id)
        inc = manager.find_incident(incident_id)
        print("  [+] Dispatch successful!")
        if inc is not None:
            print(f"      {inc.to_string()}")
            print(f"      Dispatched to scene at: {inc.get_position().to_string()}")
    except Exception as ex:
        print(f"  [-] Dispatch rejected: {ex}")


def handle_update_incident_status(manager: RescueManager) -> None:
    """Handle CLI option 9: Update an incident's status."""
    print("\n--- Update Incident Status ---")
    incident_id = read_non_empty_string("Enter Incident ID: ")
    if incident_id is None:
        return

    inc = manager.find_incident(incident_id)
    if inc is None:
        print(f"  [-] Incident '{incident_id}' does not exist.")
        return

    print(f"Current Incident State: {inc.to_string()}")
    print("Select New Status:")
    print("  1. Reported")
    print("  2. InProgress")
    print("  3. Resolved")
    status_choice = read_int("Enter choice (1-3): ", 1, 3)
    if status_choice is None:
        return

    new_status = IncidentStatus.REPORTED
    if status_choice == 2:
        new_status = IncidentStatus.IN_PROGRESS
    elif status_choice == 3:
        new_status = IncidentStatus.RESOLVED

    try:
        manager.update_incident_status(incident_id, new_status)
        print("  [+] Incident status updated successfully.")
        print(f"      {inc.to_string()}")
        if new_status in (IncidentStatus.RESOLVED, IncidentStatus.Resolved):
            print("      Note: Assigned resources have been released back to the available pool.")
    except Exception as ex:
        print(f"  [!] Failed to update status: {ex}")


def set_initial_data(manager: RescueManager) -> None:
    """Preload standard demonstration data into RescueManager."""
    # Initial sample incidents
    manager.register_incident(
        Incident("INC-101", IncidentType.FIRE, 4, Position(15, 25))
    )
    manager.register_incident(
        Incident("INC-102", IncidentType.FLOOD, 2, Position(40, 60))
    )

    # Initial sample responders
    manager.register_responder(
        Responder("RES-01", "Capt. Aamir", ResponderSpecialization.FIREFIGHTER, Position(0, 0))
    )
    manager.register_responder(
        Responder("RES-02", "Lt. Madhuchan", ResponderSpecialization.PARAMEDIC, Position(0, 0))
    )

    # Initial sample vehicles
    manager.register_vehicle(
        RescueVehicle("VEH-01", VehicleType.FIRE_ENGINE, Position(0, 0))
    )
    manager.register_vehicle(
        RescueVehicle("VEH-02", VehicleType.AMBULANCE, Position(0, 0))
    )


# C++ compatibility aliases
handleRegisterIncident = handle_register_incident
handleListIncidents = handle_list_incidents
handleSearchIncident = handle_search_incident
handleRegisterResponder = handle_register_responder
handleListResponders = handle_list_responders
handleRegisterVehicle = handle_register_vehicle
handleListVehicles = handle_list_vehicles
handleDispatch = handle_dispatch
handleUpdateIncidentStatus = handle_update_incident_status
setInitialData = set_initial_data
