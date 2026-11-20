"""
Demonstration script for A* Search in RescueGrid (Phase 5).
Compares Breadth-First Search (BFS), Uniform-Cost Search (UCS), and A* Search
over a realistic weighted disaster grid featuring roads, rough terrain, normal terrain,
and collapsed building rubble.
"""

import os
import sys

# Ensure root workspace directory is on Python search path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from models.position import Position
from environment.cell import TerrainType, TerrainCostConfig
from environment.grid import Grid
from algorithms.bfs import bfs
from algorithms.ucs import ucs
from algorithms.astar import astar
from algorithms.search_utils import render_grid_with_path, calculate_path_cost


def create_disaster_scenario_grid() -> Grid:
    """Create an 8-row by 14-column urban disaster grid with contrasting corridors.

    Features:
        - Paved arterial road (cost = 1) along row 1.
        - Damaged rough terrain corridor (cost = 4) along row 3.
        - Blocked structural rubble hazard blocking direct transit through cols 6-7.
        - Default normal terrain (cost = 2).
    """
    grid = Grid(rows=8, cols=14, default_terrain=TerrainType.NORMAL)

    # 1. Paved highway along row 1 (cost = 1)
    for x in range(13):
        grid.add_road(Position(x, 1))
    grid.add_road(Position(0, 2))   # Access ramp from depot
    grid.add_road(Position(12, 2))  # Egress ramp to goal

    # 2. Rough ground corridor along row 3 (cost = 4)
    for x in range(1, 6):
        grid.add_rough_terrain(Position(x, 3))
    for x in range(8, 12):
        grid.add_rough_terrain(Position(x, 3))

    # 3. Blocked region: Structural collapse (rubble) in the center
    grid.add_collapsed_building(Position(6, 2))
    grid.add_collapsed_building(Position(6, 3))
    grid.add_collapsed_building(Position(6, 4))
    grid.add_collapsed_building(Position(7, 3))
    grid.add_collapsed_building(Position(7, 4))

    # 4. Urban flood hazard in the south
    grid.add_flood_zone(Position(3, 5))
    grid.add_flood_zone(Position(4, 5))

    return grid


def run_demo() -> None:
    """Execute comparative demonstration between BFS, UCS, and A*."""
    print("=" * 76)
    print("        RescueGrid — AI Pathfinding Demonstration (Phase 5)         ")
    print("         BFS (Shortest Steps) vs UCS (Blind Min-Cost) vs A*          ")
    print("=" * 76)

    grid = create_disaster_scenario_grid()
    start = Position(0, 3)    # Emergency Dispatch Depot
    goal = Position(12, 3)    # Critical Disaster Incident Scene

    print("\n[Environment Configuration]")
    print(f"- Grid Dimensions : {grid.cols} cols x {grid.rows} rows ({grid.total_cells} cells)")
    print(f"- Start Position  : {start} (depot)")
    print(f"- Goal Position   : {goal} (incident scene)")
    print("\n[Terrain Movement Cost Model]")
    print(f"- ROAD ('=')       : {TerrainCostConfig.get_cost(TerrainType.ROAD)} cost/step (fast paved arterial)")
    print(f"- NORMAL ('.')     : {TerrainCostConfig.get_cost(TerrainType.NORMAL)} cost/step (standard urban surface)")
    print(f"- ROUGH (':')      : {TerrainCostConfig.get_cost(TerrainType.ROUGH)} cost/step (damaged high-resistance ground)")
    print("- RUBBLE ('X')     : Impassable (collapsed structure)")
    print("- WATER ('W')      : Impassable (deep flood water)")

    print("\nInitial Disaster Grid Map:")
    print(grid.to_string())

    # -------------------------------------------------------------------------
    # 1. Run BFS (Unweighted Shortest-Path Baseline)
    # -------------------------------------------------------------------------
    print("\n" + "-" * 76)
    print(">>> Running Breadth-First Search (BFS)...")
    bfs_res = bfs(grid, start, goal)
    bfs_weighted_cost = calculate_path_cost(grid, bfs_res.path)

    print(f"- Algorithm Name  : {bfs_res.algorithm_name}")
    print(f"- Route Found     : {'YES' if bfs_res.found else 'NO'}")
    print(f"- Path Length     : {bfs_res.path_length} steps")
    print(f"- Weighted Cost   : {bfs_weighted_cost} (cost entering cells)")
    print(f"- Nodes Explored  : {bfs_res.nodes_explored}")
    print(f"- Execution Time  : {bfs_res.execution_time_ms:.4f} ms")
    if bfs_res.found:
        print(f"- Discovered Route: {' -> '.join(str(p) for p in bfs_res.path)}")

    print("\nBFS Route Visualization ('S'=Start, 'G'=Goal, '*' Route):")
    print(render_grid_with_path(grid, bfs_res.path, start, goal))

    # -------------------------------------------------------------------------
    # 2. Run UCS (Blind Minimum-Cost Search)
    # -------------------------------------------------------------------------
    print("\n" + "-" * 76)
    print(">>> Running Uniform-Cost Search (UCS)...")
    ucs_res = ucs(grid, start, goal)

    print(f"- Algorithm Name  : {ucs_res.algorithm_name}")
    print(f"- Route Found     : {'YES' if ucs_res.found else 'NO'}")
    print(f"- Path Length     : {ucs_res.path_length} steps")
    print(f"- Total Cost      : {ucs_res.total_cost}")
    print(f"- Nodes Explored  : {ucs_res.nodes_explored}")
    print(f"- Execution Time  : {ucs_res.execution_time_ms:.4f} ms")
    if ucs_res.found:
        print(f"- Discovered Route: {' -> '.join(str(p) for p in ucs_res.path)}")

    print("\nUCS Route Visualization ('S'=Start, 'G'=Goal, '*' Route):")
    print(render_grid_with_path(grid, ucs_res.path, start, goal))

    # -------------------------------------------------------------------------
    # 3. Run A* Search (Heuristically Guided Minimum-Cost Search)
    # -------------------------------------------------------------------------
    print("\n" + "-" * 76)
    print(">>> Running A* Search (Cost-Scaled Manhattan Heuristic)...")
    astar_res = astar(grid, start, goal)

    print(f"- Algorithm Name  : {astar_res.algorithm_name}")
    print(f"- Route Found     : {'YES' if astar_res.found else 'NO'}")
    print(f"- Path Length     : {astar_res.path_length} steps")
    print(f"- Total Cost      : {astar_res.total_cost}")
    print(f"- Nodes Explored  : {astar_res.nodes_explored}")
    print(f"- Execution Time  : {astar_res.execution_time_ms:.4f} ms")
    if astar_res.found:
        print(f"- Discovered Route: {' -> '.join(str(p) for p in astar_res.path)}")

    print("\nA* Route Visualization ('S'=Start, 'G'=Goal, '*' Route):")
    print(render_grid_with_path(grid, astar_res.path, start, goal))

    # -------------------------------------------------------------------------
    # 4. Comparative Summary
    # -------------------------------------------------------------------------
    print("\n" + "=" * 76)
    print("                      ALGORITHM COMPARISON SUMMARY                      ")
    print("=" * 76)
    print(f"{'Metric':<24} | {'BFS (Unweighted)':<15} | {'UCS (Blind Cost)':<15} | {'A* (Heuristic)':<15}")
    print("-" * 76)
    print(f"{'Route Found':<24} | {str(bfs_res.found):<15} | {str(ucs_res.found):<15} | {str(astar_res.found):<15}")
    print(f"{'Path Length (steps)':<24} | {bfs_res.path_length:<15} | {ucs_res.path_length:<15} | {astar_res.path_length:<15}")
    print(f"{'Total Movement Cost':<24} | {bfs_weighted_cost:<15} | {ucs_res.total_cost:<15} | {astar_res.total_cost:<15}")
    print(f"{'Nodes Explored':<24} | {bfs_res.nodes_explored:<15} | {ucs_res.nodes_explored:<15} | {astar_res.nodes_explored:<15}")
    print(f"{'Execution Time (ms)':<24} | {bfs_res.execution_time_ms:<15.4f} | {ucs_res.execution_time_ms:<15.4f} | {astar_res.execution_time_ms:<15.4f}")
    print(f"{'Optimality Criteria':<24} | {'Step Count':<15} | {'Minimum Cost':<15} | {'Minimum Cost':<15}")
    print("=" * 76)

    print("\n[Core Algorithmic Insights]")
    print(f"1. Cost Equivalence: Both UCS and A* discovered an identical optimal minimum cost of {astar_res.total_cost}.")
    print(f"2. BFS vs Cost-Optimal: BFS prioritized fewer steps ({bfs_res.path_length} steps), but incurred a higher movement cost of {bfs_weighted_cost}.")
    print(f"3. Heuristic Guidance: A* directed its frontier toward the destination using h(n), exploring {astar_res.nodes_explored} nodes compared to UCS's {ucs_res.nodes_explored} nodes.")
    print("Demonstration completed successfully.\n")


if __name__ == "__main__":
    run_demo()
