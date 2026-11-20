"""
Demonstration scenario for partial observability and dynamic replanning in RescueGrid (Phase 6).
Demonstrates an emergency rescue vehicle navigating an urban disaster zone where:
- The complete physical environment is represented by the ActualGrid.
- The vehicle navigates strictly using its internal KnowledgeGrid.
- Mystery states ('?') represent unconfirmed/unexplored areas.
- Approaching an undiscovered flood hazard invalidates the original route.
- A* dynamically replans an alternative route to safely reach the destination.
"""

import os
import sys

# Ensure root workspace directory is on module search path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from models.position import Position
from environment.cell import TerrainType
from environment.actual_grid import ActualGrid
from environment.knowledge_grid import KnowledgeGrid
from simulation.sensor import Sensor
from simulation.rescue_simulator import RescueSimulator


def build_demonstration_scenario():
    """Build the physical Actual Grid and initial Knowledge Grid for the demo."""
    cols, rows = 14, 8

    # 1. Create Ground Truth Physical Environment (ActualGrid)
    actual_grid = ActualGrid(rows=rows, cols=cols, default_terrain=TerrainType.NORMAL)

    # Add North Bypass Road (Row 1 from col 0 to 12)
    for c in range(13):
        actual_grid.add_road(c, 1)

    # Road connectors between Row 1 and Row 3 at Depot and Goal
    actual_grid.add_road(0, 2)
    actual_grid.add_road(12, 2)

    # Direct arterial road along Row 3
    for c in range(13):
        actual_grid.add_road(c, 3)

    # DISASTER GROUND TRUTH:
    # A sudden flood zone and collapsed rubble block the direct arterial at (6, 3) and (7, 3)
    actual_grid.add_flood_zone(6, 3, blocked=True)
    actual_grid.add_flood_zone(7, 3, blocked=True)
    actual_grid.add_collapsed_building(6, 4)
    actual_grid.add_collapsed_building(7, 4)

    # Rough damaged terrain surrounding the disaster core
    for c in [5, 8]:
        actual_grid.add_rough_terrain(c, 3)
        actual_grid.add_rough_terrain(c, 4)

    # Collapsed buildings in side sectors
    actual_grid.add_collapsed_building(4, 5)
    actual_grid.add_collapsed_building(5, 5)
    actual_grid.add_collapsed_building(8, 2)
    actual_grid.add_collapsed_building(9, 2)

    # 2. Create Knowledge Grid (Agent's Initial Knowledge)
    # Default is all cells UNKNOWN ('?')
    knowledge_grid = actual_grid.create_knowledge_grid(default_terrain=TerrainType.UNKNOWN)

    # Prior city GIS / dispatch data:
    # The pre-disaster road layout is recorded as known roads in the Knowledge Grid.
    # The flood hazard at (6, 3) and (7, 3) is UNDISCOVERED (dispatch still thinks row 3 is open).
    # All off-road urban blocks remain UNKNOWN mystery states ('?').
    road_positions = [
        # North bypass
        *[Position(c, 1) for c in range(13)],
        Position(0, 2),
        Position(12, 2),
        # Direct arterial (pre-disaster record)
        *[Position(c, 3) for c in range(13)],
    ]
    for pos in road_positions:
        cell = knowledge_grid.get_cell(pos)
        cell.set_terrain(TerrainType.ROAD)
        cell.set_obstacle(False)
        cell.set_walkable(True)
        knowledge_grid._revealed.add(pos)

    start_pos = Position(0, 3)
    goal_pos = Position(12, 3)

    return actual_grid, knowledge_grid, start_pos, goal_pos


def render_grid_with_path(grid, path, start, goal, current=None, revealed_positions=None):
    """Render 2D ASCII grid with path markers and vehicle position."""
    lines = []
    lines.append("    " + " ".join(f"{c % 10}" for c in range(grid.cols)))
    lines.append("    " + "-" * (grid.cols * 2 - 1))

    path_set = set(path) if path else set()

    for r in range(grid.rows):
        row_symbols = []
        for c in range(grid.cols):
            p = Position(c, r)
            if current is not None and p == current:
                row_symbols.append("V")  # Vehicle
            elif p == start:
                row_symbols.append("S")  # Start
            elif p == goal:
                row_symbols.append("G")  # Goal
            elif p in path_set:
                row_symbols.append("*")  # Planned path waypoint
            elif revealed_positions is not None and p not in revealed_positions:
                row_symbols.append("?")  # Mystery state
            else:
                row_symbols.append(grid.get_cell(p).get_symbol())
        lines.append(f"{r:2d} | {' '.join(row_symbols)}")

    return "\n".join(lines)


def main():
    print("=" * 76)
    print("    RescueGrid — Partial Observability & Dynamic Replanning (Phase 6)    ")
    print("=" * 76)

    actual_grid, knowledge_grid, start, goal = build_demonstration_scenario()

    print("\n[Scenario Description]")
    print(f"- Start (Depot)        : {start}")
    print(f"- Destination (Scene)  : {goal}")
    print(f"- Sensor Radius        : 2 (Manhattan distance)")
    print(f"- Total Grid Cells     : {actual_grid.total_cells} ({actual_grid.cols} cols x {actual_grid.rows} rows)")
    print(f"- Initial Known Cells  : {knowledge_grid.revealed_count}")
    print(f"- Initial Unknown ('?'): {knowledge_grid.unknown_count} (mystery states excluded from planning)")

    print("\n" + "-" * 76)
    print("1. GROUND TRUTH PHYSICAL MAP (ActualGrid - Hidden from Route Planner)")
    print("-" * 76)
    print("Legend: '=' Road, '.' Normal, ':' Rough, 'W' Flood, 'X' Rubble, '#' Obstacle\n")
    print(actual_grid.to_string())

    print("\n" + "-" * 76)
    print("2. AGENT'S INITIAL KNOWLEDGE STATE (KnowledgeGrid - Used by A*)")
    print("-" * 76)
    print("Legend: '?' UNKNOWN mystery state, '=' Known Road, 'S' Start, 'G' Goal\n")
    print(render_grid_with_path(knowledge_grid, [], start, goal))

    # Initialize sensor and simulator
    sensor = Sensor(radius=2)
    simulator = RescueSimulator(
        actual_grid=actual_grid,
        knowledge_grid=knowledge_grid,
        sensor=sensor,
    )

    print("\n" + "-" * 76)
    print("3. EXECUTING STEP-BY-STEP SIMULATION WITH SENSORY DISCOVERY")
    print("-" * 76)

    result = simulator.run(start, goal)

    # Print interesting simulation milestones
    for record in result.step_history:
        if record.action in ("INITIALIZE", "REPLAN", "ARRIVED", "BLOCKED") or record.step_number in (1, 4):
            print(f"\n>>> [Step {record.step_number}] Action: {record.action}")
            print(f"    Vehicle Position: {record.vehicle_position}")
            print(f"    Notes: {record.notes}")
            if record.newly_revealed:
                revealed_str = ", ".join(f"({p.x}, {p.y})" for p in record.newly_revealed[:6])
                if len(record.newly_revealed) > 6:
                    revealed_str += f" (+{len(record.newly_revealed) - 6} more)"
                print(f"    Newly Discovered Cells: {revealed_str}")
            if record.planned_route:
                route_str = " -> ".join(f"({p.x}, {p.y})" for p in record.planned_route[:8])
                if len(record.planned_route) > 8:
                    route_str += f" -> ... -> ({goal.x}, {goal.y})"
                print(f"    Planned Route: {route_str}")

            # Display knowledge grid map snapshot at critical moments
            if record.action in ("INITIALIZE", "REPLAN", "ARRIVED"):
                print(f"\nKnowledge Grid Snapshot at Step {record.step_number} ('V' = Vehicle):")
                print(render_grid_with_path(
                    knowledge_grid,
                    record.planned_route,
                    start,
                    goal,
                    current=record.vehicle_position,
                    revealed_positions=record.revealed_positions,
                ))

    print("\n" + "=" * 76)
    print("                      FINAL SIMULATION METRICS                      ")
    print("=" * 76)
    print(result.summary())

    print("\n[Algorithmic Insights]")
    print("1. Strict Architectural Separation:")
    print("   A* operated strictly on the KnowledgeGrid. It possessed zero knowledge of")
    print("   the flood at (6, 3) until the vehicle's onboard sensor approached within radius 2.")
    print("2. Dynamic Replanning:")
    print(f"   Upon discovering the impassable flood at (6, 3), the vehicle stopped before")
    print(f"   entering the hazard and triggered A* replanning ({result.replanning_count} replan operations).")
    print("3. Safe Arrival:")
    print(f"   The vehicle successfully detoured along the north bypass and safely reached {goal}.")
    print("=" * 76)


if __name__ == "__main__":
    main()
