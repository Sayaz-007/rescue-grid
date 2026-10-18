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

## Core Domain Classes (Phase 2)

RescueGrid employs clean object-oriented design and encapsulation principles. All data members are private, with controlled access through const getters, explicit mutators, and input validation:

### 1. `Position`
- **Purpose**: Represents a 2D discrete coordinate `(x, y)` on the simulation grid.
- **Encapsulation**: Coordinates are held privately (`m_x`, `m_y`) with const accessors (`getX()`, `getY()`) and formatted string rendering (`toString()`).

### 2. `Incident`
- **Purpose**: Models an active urban emergency event.
- **Attributes**:
  - `m_id`: Unique identifier (string, non-empty validation).
  - `m_type`: Categorization via `IncidentType` (`Fire`, `Flood`, `StructuralCollapse`).
  - `m_severity`: Severity rating on a validated scale of 1 (minor) to 5 (catastrophic).
  - `m_position`: Location on the grid represented by a `Position` object.
  - `m_status`: Lifecycle status via `IncidentStatus` (`Reported`, `InProgress`, `Resolved`).
- **Encapsulation**: Invariants are strictly checked in the constructor (throwing `std::invalid_argument` on invalid severity or empty ID). Status updates occur via a controlled `setStatus` method.

### 3. `Responder`
- **Purpose**: Models an individual emergency service personnel member.
- **Attributes**:
  - `m_id`: Unique personnel code (non-empty validation).
  - `m_name`: Full name of the responder (non-empty validation).
  - `m_specialization`: Expertise category via `ResponderSpecialization` (`Firefighter`, `Paramedic`, `RescueSpecialist`).
  - `m_position`: Current grid coordinates (`Position`).
  - `m_isAvailable`: Operational deployment flag (`bool`).
- **Encapsulation**: Movement and dispatch are controlled via `setPosition()` and `setAvailability()`. Designed with a virtual destructor for seamless extension into an abstract hierarchy in future phases.

### 4. `RescueVehicle`
- **Purpose**: Models an emergency response vehicle in the fleet.
- **Attributes**:
  - `m_id`: Unique vehicle identifier (non-empty validation).
  - `m_type`: Vehicle classification via `VehicleType` (`FireEngine`, `Ambulance`, `RescueVan`).
  - `m_position`: Current deployment location (`Position`).
  - `m_isAvailable`: Fleet availability status (`bool`).
- **Encapsulation**: State transitions are controlled through dedicated `setPosition()` and `setAvailability()` member functions.

---

## Build Instructions

RescueGrid uses CMake for cross-platform build configuration.

### 1. Configure the Build

Generate build files in a designated `build` directory:

```bash
cmake -B build
```

*Note for Windows users*: If using Ninja or a specific generator:
```bash
cmake -B build -G "Ninja"
```
Or when using the Visual Studio generator (default on systems with Visual Studio / VS Build Tools):
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

### Run the Main Demonstration

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

This project is currently in **Phase 2: Core Classes and Encapsulation**.

The scope of this phase includes:
- Implementation of the four core domain classes (`Position`, `Incident`, `Responder`, `RescueVehicle`).
- Strict encapsulation with private data members, const-correct getters, and controlled mutators.
- Input validation with standard C++ exception handling (`std::invalid_argument`).
- Modular CMake build target architecture (`rescuegrid_core` static library, `RescueGrid` executable, `rescuegrid_tests` test runner).
- Automated unit testing integrated with CTest.

*Excluded from this phase*: AI pathfinding, optimization algorithms, constraint satisfaction, graphical user interfaces, databases, and network communication.

---

## Planned Development Stages

1. **Stage 1: Foundation & Build System** *(Completed)*
   - Setup project structure, compiler flags, and CMake configuration.
2. **Stage 2: Core Domain Model & OOP Architecture** *(In Progress)*
   - Core domain classes and encapsulation (`Position`, `Incident`, `Responder`, `RescueVehicle`).
   - *Next*: Abstract hierarchy, grid spatial container, and polymorphism.
3. **Stage 3: Simulation Engine & Event Loop**
   - Discrete time-stepping, hazard propagation, and dispatch logic.
4. **Stage 4: Evacuation & Routing Algorithms**
   - Pathfinding, resource allocation, and evacuation optimization strategies.
5. **Stage 5: Verification, Benchmarking & Tooling**
   - Extended scenario suites, performance benchmarks, and reporting.
