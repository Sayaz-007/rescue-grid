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

### 2. Compile the Project

Compile the target executable using CMake's build command:

```bash
cmake --build build --config Release
```

For debug builds:
```bash
cmake --build build --config Debug
```

---

## Run Instructions

Execute the compiled application binary:

- **Windows (Visual Studio multi-config generator)**:
  ```powershell
  .\build\Release\RescueGrid.exe
  ```
- **Windows (Single-config generators like Ninja / MinGW)**:
  ```powershell
  .\build\RescueGrid.exe
  ```
- **Linux / macOS**:
  ```bash
  ./build/RescueGrid
  ```

### Expected Output

```text
====================================================
                    RescueGrid                      
====================================================
Description : Disaster response and evacuation simulator
Phase       : Phase 1 - Foundation
Status      : Application initialized successfully.
====================================================
```

---

## Current Project Scope

This project is currently in **Phase 1: Project Foundation**.

The scope of this phase is restricted to establishing a clean, maintainable project architecture:
- Modern CMake build system configuration.
- Separation of concerns between source files (`src/`) and public headers (`include/rescuegrid/`).
- Standardized directory layout for future tests and documentation.
- Minimal entry point confirming build and environment health.

*Excluded from this phase*: AI pathfinding, optimization algorithms, constraint satisfaction, graphical user interfaces, databases, and network communication.

---

## Planned Development Stages

1. **Stage 1: Foundation & Build System** *(Current)*
   - Setup project structure, compiler flags, and CMake configuration.
2. **Stage 2: Core Domain Model & OOP Architecture**
   - Object-oriented hierarchy for grid cells, emergencies, responders, and vehicles.
3. **Stage 3: Simulation Engine & Event Loop**
   - Discrete time-stepping, hazard propagation, and dispatch logic.
4. **Stage 4: Evacuation & Routing Algorithms**
   - Pathfinding, resource allocation, and evacuation optimization strategies.
5. **Stage 5: Verification, Benchmarking & Tooling**
   - Automated unit tests, performance benchmarks, and scenario reporting.
