# C++ to Python Functionality Mapping

This document provides a detailed mapping between the original C++ RescueGrid implementation and the Python implementation created for the *Artificial Intelligence with Python* course.

## 1. Domain Entities & Models

| C++ Element (`rescuegrid` namespace) | Python Element (`models` package) | Notes & Design Equivalencies |
| :--- | :--- | :--- |
| `Position` class (`include/rescuegrid/Position.h`) | `Position` class (`models/position.py`) | Encapsulates discrete `(x, y)` coordinates. Type checked (rejects floats, booleans, strings). |
| `Position::Position()` | `Position(x=0, y=0)` | Default parameter values provide identical default `(0, 0)` initialization. |
| `Position::Position(int, int)` | `Position(x, y)` | Parameterized constructor with integer validation. |
| `Position::operator==`, `operator!=` | `Position.__eq__`, `__ne__` | Standard Python operator overloads returning booleans. |
| `Position::toString()` | `Position.to_string()`, `Position.toString` | String formatting producing `"(x, y)"`. |
| `friend operator<<(ostream&, Position)` | `Position.__str__`, `Position.__repr__` | String interpolation and stream-like representation (`str(pos)`). |
| `Position::getX()`, `getY()` | `@property x, y`, `get_x()`, `get_y()`, `getX()`, `getY()` | Idiomatic properties with C++ compatibility method aliases. |
| `IncidentType` enum class | `IncidentType(str, Enum)` | `FIRE`, `FLOOD`, `STRUCTURAL_COLLAPSE` with string values and aliases. |
| `IncidentStatus` enum class | `IncidentStatus(str, Enum)` | `REPORTED`, `IN_PROGRESS`, `RESOLVED` with string values and aliases. |
| `Incident` class (`include/rescuegrid/Incident.h`) | `Incident` class (`models/incident.py`) | Validates non-empty ID and severity rating (1 to 5). |
| `Incident::assignResources(respId, vehId)` | `Incident.assign_resources(resp_id, veh_id)` | Binds responder and vehicle identifiers to the incident. |
| `Incident::releaseResources()` | `Incident.release_resources()` | Clears assigned IDs. |
| `Incident::hasAssignedResources()` | `Incident.has_assigned_resources()` | Returns boolean checking if both resources are bound. |
| `ResponderSpecialization` enum class | `ResponderSpecialization(str, Enum)` | `FIREFIGHTER`, `PARAMEDIC`, `RESCUE_SPECIALIST`. |
| `Responder` class (`include/rescuegrid/Responder.h`) | `Responder` class (`models/responder.py`) | Encapsulates ID, name, specialization, position, availability. |
| `Responder::setPosition(Position)` & `(int, int)` | `Responder.set_position(new_pos, y=None)` | Flexible argument forms: accepts either a Position instance or discrete (x, y) coordinates. |
| `VehicleType` enum class | `VehicleType(str, Enum)` | `FIRE_ENGINE`, `AMBULANCE`, `RESCUE_VAN`. |
| `RescueVehicle` class (`include/rescuegrid/RescueVehicle.h`) | `RescueVehicle` class (`models/rescue_vehicle.py`) | Encapsulates ID, type, position, availability. |
| `RescueVehicle::setPosition(Position)` & `(int, int)` | `RescueVehicle.set_position(new_pos, y=None)` | Flexible argument forms: accepts either a Position instance or discrete (x, y) coordinates. |

---

## 2. Central Management Logic (`RescueManager`)

| C++ Feature (`RescueManager.cpp`) | Python Feature (`core/rescue_manager.py`) | Behavioral Fidelity |
| :--- | :--- | :--- |
| `std::vector<Incident> m_incidents` | `self._incidents: list[Incident]` | In-memory dynamic list preserving registration order. |
| `std::vector<Responder> m_responders` | `self._responders: list[Responder]` | In-memory list of responders. |
| `std::vector<RescueVehicle> m_vehicles` | `self._vehicles: list[RescueVehicle]` | In-memory fleet inventory. |
| `registerIncident`, `registerResponder`, `registerVehicle` | `register_incident`, `register_responder`, `register_vehicle` | Enforces unique IDs. Rejects duplicates with `DuplicateEntityError` (inherits `ValueError`). |
| `hasIncident`, `hasResponder`, `hasVehicle` | `has_incident`, `has_responder`, `has_vehicle` | Boolean existence checks. |
| `findIncident`, `findResponder`, `findVehicle` | `find_incident`, `find_responder`, `find_vehicle` | Pointer/reference lookup returning entity or `None`. |
| `dispatchResources(id)` | `dispatch_resources(id)` | Selects first available responder and vehicle, marks them busy, updates locations to incident, binds IDs, transitions incident status to `InProgress`. |
| `updateIncidentStatus(id, newStatus)` | `update_incident_status(id, new_status)` | Enforces strict status transition state machine. Automatically frees bound resources upon `Resolved`. |
| Cross-incident resource isolation | Cross-incident resource isolation | Resolving one incident releases only its bound resources; other active incidents remain undisturbed. |

---

## 3. Exceptions & Error Handling

| C++ Exception | Python Exception | Usage in Simulation |
| :--- | :--- | :--- |
| `std::invalid_argument` | `ValueError` / `DuplicateEntityError` / `EntityNotFoundError` | Empty IDs, invalid severity ranges (< 1 or > 5), duplicate ID registrations, missing entity lookups during dispatch/status updates. |
| `std::logic_error` | `RuntimeError` / `InvalidStatusTransitionError` | Attempting dispatch to resolved/active incident, invalid status transitions (e.g. Reported -> InProgress without dispatch, InProgress -> Reported, reopening Resolved incidents). |
| `std::runtime_error` | `RuntimeError` / `ResourceUnavailableError` | Attempting dispatch when no responder or rescue vehicle is available in fleet. |

---

## 4. User Interface & Menu Operations

| C++ Operation (`src/menu.cpp`, `src/main.cpp`) | Python Operation (`menu.py`, `main.py`) | Notes |
| :--- | :--- | :--- |
| Option 1: Register incident | `handle_register_incident(manager)` | Prompts for ID, type (1-3), severity (1-5), X, Y. |
| Option 2: List incidents | `handle_list_incidents(manager)` | Displays all registered incidents with formatted details. |
| Option 3: Search incident by ID | `handle_search_incident(manager)` | Searches manager and prints full record and coordinates. |
| Option 4: Register responder | `handle_register_responder(manager)` | Prompts for ID, name, specialization (1-3), station X, Y. |
| Option 5: List responders | `handle_list_responders(manager)` | Displays total and available counts, plus formatted responder list. |
| Option 6: Register vehicle | `handle_register_vehicle(manager)` | Prompts for ID, vehicle type (1-3), station X, Y. |
| Option 7: List vehicles | `handle_list_vehicles(manager)` | Displays total and available fleet counts, plus vehicle list. |
| Option 8: Dispatch resources | `handle_dispatch(manager)` | Dispatches first available units to specified incident. |
| Option 9: Update incident status | `handle_update_incident_status(manager)` | Advances status and releases resources upon resolution. |
| Option 10: Exit | Graceful exit (`running = False`) | Terminates application with closing message. |
| Demonstration Data | `set_initial_data(manager)` | Preloads `INC-101`, `INC-102`, `RES-01`, `RES-02`, `VEH-01`, `VEH-02`. |
