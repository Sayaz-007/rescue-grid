# RescueGrid

RescueGrid is a disaster response and evacuation simulator designed to model urban emergency scenarios. The simulation models a city environment containing dynamic emergencies (e.g., fires, floods, structural collapses), specialized rescue personnel, emergency response vehicles, resource allocation, and evacuation operations.

---

## Prerequisites

To build and run RescueGrid, ensure the following tools are installed:

- **C++ Compiler**: A compiler supporting C++17 or newer:
  - MSVC (Visual Studio 2017 15.7+ or Visual Studio Build Tools)
  - GCC 7.0+
  - Clang 5.0+
- **Build System**:
  - CMake 3.15 or newer
  - Underlying build tool: MSBuild, Ninja, or Make

---

## Domain Architecture & Core Classes

RescueGrid adheres to object-oriented programming principles, strict encapsulation, and clean domain modeling. All class data members are private, with access controlled through const getters, explicit mutators, and input validation:

### 1. `Position`
- **Purpose**: Represents a 2D discrete coordinate `(x, y)` on the simulation grid.
- **Encapsulation**: Coordinates are stored privately (`m_x`, `m_y`) with const accessors (`getX()`, `getY()`) and formatted string rendering (`toString()`).

### 2. `Incident`
- **Purpose**: Models an active urban emergency event.
- **Attributes**:
  - `m_id`: Unique identifier (string, non-empty validation).
  - `m_type`: Categorization via `IncidentType` (`Fire`, `Flood`, `StructuralCollapse`).
  - `m_severity`: Severity rating on a validated scale of 1 (minor) to 5 (catastrophic).
  - `m_position`: Location on the grid represented by a `Position` object.
  - `m_status`: Lifecycle status via `IncidentStatus` (`Reported`, `InProgress`, `Resolved`).
  - `m_assignedResponderId`, `m_assignedVehicleId`: Identifiers of emergency units actively deployed to this incident.
- **Encapsulation**: Strict constructor validation enforces class invariants (throwing `std::invalid_argument` on invalid severity or blank ID). Status and assigned resources are modified via controlled methods (`setStatus()`, `assignResources()`, `releaseResources()`).

### 3. `Responder`
- **Purpose**: Models an individual emergency service personnel member.
- **Attributes**:
  - `m_id`: Unique personnel code (non-empty validation).
  - `m_name`: Full name of the responder (non-empty validation).
  - `m_specialization`: Expertise category via `ResponderSpecialization` (`Firefighter`, `Paramedic`, `RescueSpecialist`).
  - `m_position`: Current grid coordinates (`Position`).
  - `m_isAvailable`: Operational deployment availability flag (`bool`).
- **Encapsulation**: Movement and dispatch are controlled via `setPosition()` and `setAvailability()`. Designed with a virtual destructor for seamless future extension into an abstract hierarchy.

### 4. `RescueVehicle`
- **Purpose**: Models an emergency response vehicle in the fleet.
- **Attributes**:
  - `m_id`: Unique vehicle identifier (non-empty validation).
  - `m_type`: Vehicle classification via `VehicleType` (`FireEngine`, `Ambulance`, `RescueVan`).
  - `m_position`: Current deployment location (`Position`).
  - `m_isAvailable`: Fleet availability status (`bool`).
- **Encapsulation**: State transitions are controlled through dedicated `setPosition()` and `setAvailability()` member functions.

---

## Incident & Resource Management (`RescueManager`)

The `RescueManager` class orchestrates domain collections and coordinates emergency dispatch operations:

- **Collection Design**: Maintains `std::vector<Incident>`, `std::vector<Responder>`, and `std::vector<RescueVehicle>`. Vector storage preserves cache locality and simplifies iteration. Responders and vehicles are referenced by ID within incidents, preventing pointer invalidation issues when vectors grow.
- **Registration & Validation**: Enforces uniqueness across incident, responder, and vehicle identifiers. Duplicate registrations throw `std::invalid_argument`.
- **Search & Retrieval**: Fast pointer-based lookup methods (`findIncident`, `findResponder`, `findVehicle`) provide both const and non-const access without copying entity data.
- **Deterministic Dispatch**:
  1. Verifies that the requested incident exists, is not resolved, and is not already assigned active units.
  2. Selects the first available responder and first available rescue vehicle.
  3. Transitions their availability to unavailable (`false`), moves their positions to the incident location, binds their IDs to the incident, and updates incident status to `InProgress`.
  4. Prevents double-assignment of unavailable resources.
- **Incident Lifecycle Rules**:
  - `Reported -> InProgress`: Permitted *only* through successful resource dispatch via `dispatchResources()`. Direct mutation without dispatch is rejected.
  - `InProgress -> Resolved`: Permitted; automatically returns assigned responder and vehicle to available status and clears the assignment bindings.
  - `Reported -> Resolved`: Permitted for closing incidents directly without dispatch (e.g., false alarms).
  - `InProgress -> Reported`: Prohibited to prevent stranding assigned resources in an unavailable state.
  - `Resolved -> Any`: Prohibited; `Resolved` is a terminal state.
- **Resource Release**: Updating an incident's status to `Resolved` releases only the resources bound to that specific incident, leaving other active deployments unaffected.

---

## Interactive Menu Operations

The application provides a command-line interface featuring 10 operations:

1. **Register an incident**: Captures ID, type (Fire, Flood, StructuralCollapse), severity (1–5), and grid coordinates with full range and type validation.
2. **List all incidents**: Displays all registered incidents with their type, severity, location, status, and assigned units.
3. **Search for an incident by ID**: Queries the manager and formats complete incident details.
4. **Register a responder**: Captures ID, full name, specialization (Firefighter, Paramedic, RescueSpecialist), and station coordinates.
5. **List all responders**: Displays all personnel, specializations, current locations, and operational availability.
6. **Register a rescue vehicle**: Captures ID, vehicular classification (FireEngine, Ambulance, RescueVan), and station coordinates.
7. **List all rescue vehicles**: Displays fleet inventory, vehicle categories, locations, and availability.
8. **Dispatch resources to an incident**: Coordinates available responder and vehicle deployment to a specified incident.
9. **Update an incident's status**: Advances an incident's lifecycle (`Reported`, `InProgress`, `Resolved`) and automatically releases units when resolved.
10. **Exit**: Gracefully shuts down the simulator.

*Robustness*: Non-numeric inputs, empty identifiers, out-of-range choices, and duplicate keys are intercepted and handled with user-friendly messages without terminating the application.

---

## Build Instructions

RescueGrid uses CMake for cross-platform build configuration.

### 1. Configure the Build

Generate build files in a designated `build` directory:

```bash
cmake -B build
```

*Note for Windows users*: If using Ninja:
```bash
cmake -B build -G "Ninja"
```
Or when using the Visual Studio generator (default with Visual Studio / VS Build Tools):
```bash
cmake -B build
```

### 2. Compile the Project and Tests

Compile the main application and test suite:

```bash
cmake --build build --config Release
```

For debug builds:
```bash
cmake --build build --config Debug
```

---

## Run Instructions

### Run the Interactive Application

Execute the compiled application binary:

- **Windows (Visual Studio multi-config)**:
  ```powershell
  .\build\Release\RescueGrid.exe
  ```
- **Windows (Single-config / Ninja / MinGW)**:
  ```powershell
  .\build\RescueGrid.exe
  ```
- **Linux / macOS**:
  ```bash
  ./build/RescueGrid
  ```

### Run the Automated Tests

Run the test suite using CTest:

```bash
ctest --test-dir build -C Release --output-on-failure
```

Or execute the test binary directly:

- **Windows (Visual Studio multi-config)**:
  ```powershell
  .\build\Release\rescuegrid_tests.exe
  ```
- **Windows (Single-config / Ninja / MinGW)**:
  ```powershell
  .\build\rescuegrid_tests.exe
  ```
- **Linux / macOS**:
  ```bash
  ./build/rescuegrid_tests
  ```

---

## Current Project Scope

This project is currently in **Phase 3: Incident and Resource Management**.

The scope of this phase includes:
- Centralized entity management via `RescueManager`.
- Deterministic resource dispatch and automatic resource release on incident resolution.
- Interactive, menu-driven CLI with robust input validation.
- Automated unit test suite (12 test suites) covering core classes, manager operations, dispatch edge cases, lifecycle transition rules, and double-assignment prevention.
- Seamless CTest and CMake integration.

*Excluded from this phase*: Inheritance/polymorphic hierarchies, AI pathfinding, optimization algorithms, constraint satisfaction, graphical user interfaces, databases, and network communication.

---

## Planned Development Stages

1. **Stage 1: Foundation & Build System** *(Completed)*
   - Setup project structure, compiler flags, and CMake configuration.
2. **Stage 2: Core Domain Model & Management** *(Completed)*
   - Core domain classes and encapsulation (`Position`, `Incident`, `Responder`, `RescueVehicle`).
   - Incident & resource management (`RescueManager`), deterministic dispatch, and interactive CLI.
3. **Stage 3: Abstract Hierarchy & Polymorphism** *(Next Stage)*
   - Abstract `Responder` and `Vehicle` base classes with polymorphic behaviors.
   - Spatial city grid container.
4. **Stage 4: Simulation Engine & Event Loop**
   - Discrete time-stepping, hazard propagation, and automated dispatch logic.
5. **Stage 5: Evacuation & Routing Algorithms**
   - Pathfinding, resource allocation, and evacuation optimization strategies.
6. **Stage 6: Verification, Benchmarking & Tooling**
   - Extended scenario suites, performance benchmarks, and reporting.
