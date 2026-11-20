"""
Demonstration script for Hill Climbing Local Search in RescueGrid (Phase 7).
Illustrates:
1. Scenario A: Successful Hill Climbing along an unobstructed evacuation route.
2. Scenario B: Genuine Local Optimum failure (wall barrier trap) compared side-by-side with A*.
3. Comprehensive 5-Algorithm Comparison: BFS vs DFS vs UCS vs A* vs Hill Climbing.
"""

import os
import sys

# Ensure root workspace directory is on module search path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from models.position import Position
from environment.cell import TerrainType
from environment.grid import Grid
from algorithms.search_utils import render_grid_with_path, calculate_path_cost
from algorithms.bfs import bfs
from algorithms.dfs import dfs
from algorithms.ucs import ucs
from algorithms.astar import astar
from algorithms.hill_climbing import hill_climbing


def run_scenario_a():
    """Scenario A: Successful Hill Climbing on an unobstructed corridor."""
    print("\n" + "=" * 76)
    print("SCENARIO A: SUCCESSFUL HILL CLIMBING (Direct Evacuation Route)")
    print("=" * 76)

    grid = Grid(rows=6, cols=10, default_terrain=TerrainType.NORMAL)
    start = Position(0, 2)
    goal = Position(8, 2)

    # Paved road along row 2
    for c in range(10):
        grid.add_road(c, 2)

    # Some rubble obstacles far away that do not obstruct the direct path
    grid.add_collapsed_building(4, 0)
    grid.add_collapsed_building(5, 5)

    print("Disaster Grid Layout ('=' Road, '.' Normal, 'X' Rubble):")
    print(grid.to_string())

    print(f"\nDispatch Parameters:")
    print(f"- Start Position : {start}")
    print(f"- Goal Position  : {goal}")

    result = hill_climbing(grid, start, goal)

    print("\nHill Climbing Execution Outcome:")
    print(f"- Route Found    : {'YES' if result.found else 'NO'}")
    print(f"- Path Length    : {result.path_length} steps")
    print(f"- Total Movement Cost: {result.total_cost:.2f} (cost entering cells)")
    print(f"- Nodes Explored : {result.nodes_explored}")
    print(f"- Execution Time : {result.execution_time_ms:.4f} ms")
    route_str = " -> ".join(f"({p.x}, {p.y})" for p in result.path)
    print(f"- Traversed Route: {route_str}")

    print("\nRoute Visualization ('S'=Start, 'G'=Goal, '*' Route):")
    print(render_grid_with_path(grid, result.path, start, goal))


def run_scenario_b():
    """Scenario B: Local Optimum Failure (Wall Barrier) compared with A*."""
    print("\n" + "=" * 76)
    print("SCENARIO B: LOCAL OPTIMUM / WALL BARRIER TRAP (Hill Climbing vs A*)")
    print("=" * 76)

    cols, rows = 12, 7
    grid = Grid(rows=rows, cols=cols, default_terrain=TerrainType.NORMAL)

    start = Position(1, 3)
    goal = Position(9, 3)

    # Paved road along direct line
    for c in range(12):
        grid.add_road(c, 3)

    # North bypass corridor along row 1
    for c in range(12):
        grid.add_road(c, 1)
    grid.add_road(1, 2)
    grid.add_road(9, 2)

    # WALL BARRIER blocking the direct road at column 5:
    # A vertical wall from row 2 to row 5 forces a detour to the north (row 1).
    # To reach row 1 from (4, 3), the vehicle must move north to (4, 2) or west to (3, 3),
    # which INCREASES or maintains Manhattan distance to (9, 3).
    for r in range(2, 6):
        grid.add_collapsed_building(5, r)

    print("Disaster Grid Layout with Wall Barrier at Column 5:")
    print("('=' Road, '.' Normal, 'X' Rubble Wall Barrier)")
    print(grid.to_string())

    print(f"\nDispatch Parameters:")
    print(f"- Start Position : {start}")
    print(f"- Goal Position  : {goal}")
    print(f"- Initial Manhattan Distance: {abs(start.x - goal.x) + abs(start.y - goal.y)}")

    # 1. Run Hill Climbing
    print("\n>>> Running Hill Climbing (Steepest-Ascent Manhattan)...")
    hc_res = hill_climbing(grid, start, goal)

    print(f"- Route Found    : {'YES' if hc_res.found else 'NO (Trapped at Local Optimum)'}")
    print(f"- Path Length    : {hc_res.path_length}")
    print(f"- Total Cost     : {hc_res.total_cost}")
    print(f"- Nodes Explored : {hc_res.nodes_explored}")
    print(f"- Execution Time : {hc_res.execution_time_ms:.4f} ms")
    halt_pos = hc_res.visited_order[-1] if hc_res.visited_order else start
    visited_str = " -> ".join(f"({p.x}, {p.y})" for p in hc_res.visited_order)
    print(f"- Trajectory until halt: {visited_str}")
    print(f"- Halting Position: {halt_pos} (h = {abs(halt_pos.x - goal.x) + abs(halt_pos.y - goal.y)})")
    print(f"  Explanation: At {halt_pos}, moving north to (4, 2) has h = 6, moving west to (3, 3) has h = 6.")
    print(f"  Neither candidate improves upon current h = 5. Hill Climbing strictly refuses")
    print(f"  non-improving moves and halts.")

    # 2. Run A* on the same scenario
    print("\n>>> Running A* Search (Informed Systematic Search)...")
    astar_res = astar(grid, start, goal)

    print(f"- Route Found    : {'YES' if astar_res.found else 'NO'}")
    print(f"- Path Length    : {astar_res.path_length} steps")
    print(f"- Total Cost     : {astar_res.total_cost:.2f}")
    print(f"- Nodes Explored : {astar_res.nodes_explored}")
    print(f"- Execution Time : {astar_res.execution_time_ms:.4f} ms")
    astar_str = " -> ".join(f"({p.x}, {p.y})" for p in astar_res.path)
    print(f"- A* Solution Route: {astar_str}")

    print("\nHill Climbing Visited Trajectory ('V' Trapped State, '*' Traversed):")
    print(render_grid_with_path(grid, hc_res.visited_order, start, goal))

    print("\nA* Detour Solution ('*' Optimal Detour around Barrier):")
    print(render_grid_with_path(grid, astar_res.path, start, goal))


def run_algorithm_comparison():
    """Unified 5-Algorithm Comparison on a Weighted Disaster Grid."""
    print("\n" + "=" * 76)
    print("      COMPREHENSIVE 5-ALGORITHM COMPARISON BENCHMARK (PHASE 7)      ")
    print("=" * 76)

    grid = Grid(rows=7, cols=10, default_terrain=TerrainType.NORMAL)
    start = Position(0, 3)
    goal = Position(8, 3)

    # Paved road detour along row 1
    for c in range(9):
        grid.add_road(c, 1)
    grid.add_road(0, 2)
    grid.add_road(8, 2)

    # Direct corridor along row 3 has damaged ROUGH terrain (cost 4.0)
    for c in range(1, 8):
        grid.add_rough_terrain(c, 3)

    algorithms = [
        ("Breadth-First Search (BFS)", lambda: bfs(grid, start, goal)),
        ("Depth-First Search (DFS)", lambda: dfs(grid, start, goal)),
        ("Uniform-Cost Search (UCS)", lambda: ucs(grid, start, goal)),
        ("A* Search", lambda: astar(grid, start, goal)),
        ("Hill Climbing", lambda: hill_climbing(grid, start, goal)),
    ]

    results = []
    for name, runner in algorithms:
        res = runner()
        results.append((name, res))

    print(f"{'Algorithm':<28} | {'Found':<6} | {'Steps':<6} | {'Cost':<7} | {'Explored':<9} | {'Time (ms)':<9}")
    print("-" * 76)
    for name, res in results:
        found_str = "YES" if res.found else "NO"
        steps_str = str(res.path_length) if res.found else "N/A"
        cost_str = f"{calculate_path_cost(grid, res.path):.1f}" if res.found else "N/A"
        print(f"{name:<28} | {found_str:<6} | {steps_str:<6} | {cost_str:<7} | {res.nodes_explored:<9} | {res.execution_time_ms:<9.4f}")

    print("=" * 76)
    print("\n[Comparative Insights]")
    print("1. BFS: Finds shortest step-count route (8 steps), but blind to terrain costs (cost 30.0).")
    print("2. DFS: Explores deep branches; non-optimal route.")
    print("3. UCS: Guaranteed cost-optimal route (cost 13.0), exploring concentric cost contours.")
    print("4. A* : Guaranteed cost-optimal route (cost 13.0), expanding fewer nodes via heuristic pruning.")
    print("5. Hill Climbing: Greedily follows Manhattan distance. It successfully navigates the direct")
    print("   rough corridor (8 steps, cost 30.0) but fails to discover the cheaper road bypass (cost 13.0)")
    print("   because the road detour initially moves away from the goal (increasing Manhattan distance).")
    print("=" * 76)


def main():
    print("=" * 76)
    print("         RescueGrid — Local Search & Hill Climbing (Phase 7)         ")
    print("=" * 76)

    run_scenario_a()
    run_scenario_b()
    run_algorithm_comparison()
    print("\nDemonstration completed successfully.")


if __name__ == "__main__":
    main()
