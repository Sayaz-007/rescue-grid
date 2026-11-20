"""
RescueGrid — Complete Disaster Response Simulation Demonstration (Phase 9.3).

Demonstrates the integrated multi-incident emergency response lifecycle:
1. Heterogeneous disaster environment (ActualGrid vs. KnowledgeGrid).
2. Incident registration and priority ordering by severity rating.
3. Constraint Satisfaction Problem (CSP) fleet resource allocation.
4. Discrete cell-by-cell locomotion (no teleportation).
5. Sensor-limited perception and environmental discovery.
6. Hidden hazard detection and dynamic A* route replanning.
7. On-scene emergency operations (configurable service duration).
8. Incident resolution and fleet resource release.
9. Structured simulation event logging and visualization.
"""

import os
import sys
import warnings

# Suppress headless animation deletion warnings
warnings.filterwarnings("ignore", category=UserWarning, module="matplotlib.animation")

# Ensure root workspace directory is on module search path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import matplotlib
# Default to headless Agg backend if running non-interactively
if not os.environ.get("DISPLAY") and sys.platform != "darwin":
    matplotlib.use("Agg")

import matplotlib.pyplot as plt

from models.position import Position
from models.incident import Incident, IncidentType, IncidentStatus
from models.responder import Responder, ResponderSpecialization
from models.rescue_vehicle import RescueVehicle, VehicleType
from core.rescue_manager import RescueManager
from environment.cell import TerrainType
from environment.actual_grid import ActualGrid
from environment.knowledge_grid import KnowledgeGrid
from simulation.sensor import Sensor
from simulation.rescue_simulator import RescueSimulator


def build_disaster_scenario():
    """Construct a deterministic 14x9 disaster environment with known and hidden hazards."""
    cols, rows = 14, 9

    # 1. Ground Truth ActualGrid
    actual_grid = ActualGrid(rows=rows, cols=cols, default_terrain=TerrainType.NORMAL)

    # Arterial highway roads (fast transit, cost 1.0)
    for x in range(13):
        actual_grid.add_road(Position(x, 1))
    for y in range(8):
        actual_grid.add_road(Position(0, y))
    for y in range(1, 8):
        actual_grid.add_road(Position(12, y))

    # Damaged urban ground (rough terrain, cost 4.0)
    for x in range(2, 11):
        actual_grid.get_cell(Position(x, 4)).set_terrain(TerrainType.ROUGH)

    # Environmental obstacles
    actual_grid.add_collapsed_building(Position(6, 2))
    actual_grid.add_collapsed_building(Position(6, 3))
    actual_grid.add_flood_zone(Position(9, 5))
    actual_grid.add_flood_zone(Position(9, 6))
    actual_grid.add_fire_zone(Position(3, 7))
    actual_grid.add_fire_zone(Position(4, 7))

    # Hidden Physical Hazard: Rubble collapsed across highway at (4, 1)
    # This obstacle is present in reality, but unknown to the vehicle prior to sensory detection!
    actual_grid.add_collapsed_building(Position(4, 1))

    # 2. Agent KnowledgeGrid (Initially all unknown except known baseline street network)
    knowledge_grid = KnowledgeGrid(rows=rows, cols=cols, default_terrain=TerrainType.UNKNOWN)

    # Prior baseline city GIS transit records:
    # Streets are recorded as open corridors, but post-disaster hazards (like collapsed rubble at (4,1))
    # are completely unknown to dispatch until detected on-site by sensors!
    known_streets = [
        *[Position(x, 0) for x in range(13)],
        *[Position(x, 1) for x in range(13)],
        *[Position(x, 2) for x in range(13)],
        *[Position(x, 4) for x in range(13)],
        *[Position(x, 7) for x in range(13)],
        *[Position(0, y) for y in range(8)],
        *[Position(12, y) for y in range(1, 8)],
        Position(11, 4),
        Position(7, 7),
    ]

    for p in known_streets:
        k_cell = knowledge_grid.get_cell(p)
        a_cell = actual_grid.get_cell(p)
        # Highway bypass row 1 is believed to be open ROAD (including (4, 1))
        if p.y == 1:
            k_cell.set_terrain(TerrainType.ROAD)
        elif p.x == 0 or p.x == 12:
            k_cell.set_terrain(TerrainType.ROAD)
        else:
            k_cell.set_terrain(a_cell.terrain)
        k_cell.set_obstacle(False)
        k_cell.set_walkable(True)
        knowledge_grid._revealed.add(p)

    sensor = Sensor(radius=2)
    return actual_grid, knowledge_grid, sensor


def main():
    print("=" * 76)
    print("   RescueGrid — Complete Disaster Response Simulation Demo (Phase 9.3)   ")
    print("=" * 76)

    # Step 1: Environment Setup
    actual_grid, knowledge_grid, sensor = build_disaster_scenario()
    manager = RescueManager()
    simulator = RescueSimulator(
        actual_grid=actual_grid,
        knowledge_grid=knowledge_grid,
        sensor=sensor,
        manager=manager,
        planner_func="astar",
    )

    print("\n[1. Environment Setup]")
    print(f"- Grid Dimensions   : {actual_grid.cols} columns x {actual_grid.rows} rows (126 cells)")
    print(f"- Onboard Sensor    : Manhattan detection radius r = {sensor.radius}")
    print(f"- Route Planner     : {simulator.planner_name} (Cost-optimal)")

    # Step 2: Register Responders and Vehicles at Depot (0, 0)
    depot = Position(0, 0)
    responders = [
        Responder("RES-F1", "Captain Miller", ResponderSpecialization.FIREFIGHTER, depot),
        Responder("RES-P1", "Dr. Sarah Chen", ResponderSpecialization.PARAMEDIC, depot),
        Responder("RES-S1", "Officer Hayes", ResponderSpecialization.RESCUE_SPECIALIST, depot),
    ]
    vehicles = [
        RescueVehicle("VEH-ENG1", VehicleType.FIRE_ENGINE, depot),
        RescueVehicle("VEH-AMB1", VehicleType.AMBULANCE, depot),
        RescueVehicle("VEH-VAN1", VehicleType.RESCUE_VAN, depot),
    ]

    for r in responders:
        simulator.register_responder(r)
    for v in vehicles:
        simulator.register_vehicle(v)

    print("\n[2. Fleet Registration at Depot (0, 0)]")
    for r in responders:
        print(f"  • Responder : <{r.get_id()}> {r.get_name()} ({r.get_specialization().value})")
    for v in vehicles:
        print(f"  • Vehicle   : <{v.get_id()}> ({v.get_type().value})")

    # Step 3: Register Heterogeneous Emergency Incidents
    incidents = [
        Incident("INC-FIRE", IncidentType.FIRE, severity=5, position=Position(8, 1)),
        Incident("INC-MED", IncidentType.MEDICAL, severity=4, position=Position(11, 4)),
        Incident("INC-FLOOD", IncidentType.FLOOD, severity=2, position=Position(7, 7)),
    ]

    for inc in incidents:
        simulator.register_incident(inc)

    print("\n[3. Reported Disaster Incidents]")
    for inc in incidents:
        print(f"  • Incident <{inc.get_id()}>: {inc.get_type().value} | Severity {inc.get_severity()}/5 @ {inc.get_position()}")

    # Step 4: Incident Prioritization
    print("\n[4. Incident Prioritization by Severity]")
    prioritized = simulator.prioritize_incidents()
    for rank, inc in enumerate(prioritized, 1):
        print(f"  Priority {rank}: Incident <{inc.get_id()}> (Severity {inc.get_severity()}, Type {inc.get_type().value})")

    # Step 5: Execute Integrated Multi-Incident Simulation Loop
    print("\n[5. Running Simulation Event Loop...]")
    print("  • Allocating fleet via Multi-Agent CSP solver...")
    print("  • Moving vehicles cell-by-cell along planned routes...")
    print("  • Scanning environment with onboard sensors...")
    print("  • Dynamically replanning upon unexpected obstacle detection...")
    print("  • Performing on-scene emergency operations...")
    print("  • Resolving incidents and returning resources to pool...")

    report = simulator.run_simulation(
        max_steps_per_mission=1000,
        service_duration=2,  # 2 service ticks per incident
        allow_partial=True,
    )

    print("\n" + report.summary())

    # Step 6: Telemetry and Event Log Sample
    print("\n[6. Key Lifecycle Telemetry Events]")
    events = simulator.get_event_log()
    key_types = {
        "RESOURCES_ALLOCATED",
        "ROUTE_CALCULATED",
        "HAZARD_DISCOVERED",
        "ROUTE_REPLANNED",
        "VEHICLE_ARRIVED",
        "INCIDENT_RESOLVED",
        "RESOURCES_RELEASED",
    }
    filtered_events = [e for e in events if e.event_type in key_types]
    for e in filtered_events:
        print(f"  {e.to_string()}")

    # Step 7: Visualization Artifact Generation
    output_png = os.path.join(
        os.path.abspath(os.path.join(os.path.dirname(__file__), "..")),
        "output",
        "demo_full_simulation.png",
    )
    print(f"\n[7. Generating Simulation State Visualization -> {output_png}]")
    fig, ax = simulator.render_simulation_state(
        title="RescueGrid Complete Disaster Simulation (Phase 9.3)",
        save_path=output_png,
    )
    plt.close(fig)
    print("  Successfully generated state visualization artifact.")

    print("\n" + "=" * 76)
    print("Phase 9.3 Disaster Response Simulation Demonstration completed successfully.")
    print("=" * 76)


if __name__ == "__main__":
    main()
