"""
Demonstration script for Uniform-Cost Search (UCS) in RescueGrid (Phase 4).
Illustrates the difference between shortest-path search (BFS) and minimum-cost
search (UCS) over weighted terrain (Roads vs Rough Terrain vs Normal).
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
from algorithms.search_utils import render_grid_with_path, calculate_path_cost


def create_weighted_disaster_grid() -> Grid:
    """Create a 7-row by 12-column grid modeling contrasting transit corridors.

    Layout:
        - Row 3: Direct east-west corridor composed of ROUGH terrain (cost = 4).
        - Rows 0-1: North perimeter bypass composed of paved ROAD (cost = 1).
        - Remainder: NORMAL surface terrain (cost = 2).
    """
    grid = Grid(rows=7, cols=12, default_terrain=TerrainType.NORMAL)

    # 1. Paved highway bypass along Row 1 (Movement cost = 1)
    for x in range(10):
        grid.add_road(Position(x, 1))
    grid.add_road(Position(0, 2))  # Access road to Row 1
    grid.add_road(Position(9, 2))  # Egress road to Goal

    # 2. Damaged rough transit corridor along Row 3 (Movement cost = 4)
    for x in range(1, 9):
        grid.add_rough_terrain(Position(x, 3))

    # 3. Structural rubble hazards south of the corridor
    grid.add_collapsed_building(Position(3, 4))
    grid.add_collapsed_building(Position(4, 4))
    grid.add_collapsed_building(Position(5, 4))

    return grid


def run_demo() -> None:
    """Execute comparative demonstration between BFS and UCS."""
    print("=" * 72)
    print("       RescueGrid — Minimum-Cost AI Search Demonstration (Phase 4)      ")
    print("       Shortest-Path Search (BFS) vs Minimum-Cost Search (UCS)          ")
    print("=" * 72)

    grid = create_weighted_disaster_grid()
    start = Position(0, 3)   # Rescue Dispatch Depot
    goal = Position(9, 3)    # Critical Incident Scene

    print("\n[Environment Configuration]")
    print(f"- Grid Dimensions : {grid.cols} cols x {grid.rows} rows ({grid.total_cells} cells)")
    print(f"- Start Position  : {start} (depot)")
    print(f"- Goal Position   : {goal} (incident scene)")
    print("\n[Movement Cost Model]")
    print(f"- ROAD ('=')       : {TerrainCostConfig.get_cost(TerrainType.ROAD)} cost/step (fast paved transit)")
    print(f"- NORMAL ('.')     : {TerrainCostConfig.get_cost(TerrainType.NORMAL)} cost/step (standard urban terrain)")
    print(f"- ROUGH (':')      : {TerrainCostConfig.get_cost(TerrainType.ROUGH)} cost/step (damaged, high-resistance terrain)")
    print("- RUBBLE ('X')     : Impassable (blocked obstacle)")

    print("\nInitial Grid Map:")
    print(grid.to_string())

    # -------------------------------------------------------------------------
    # 1. Run BFS (Baseline unweighted shortest-path search)
    # -------------------------------------------------------------------------
    print("\n" + "-" * 72)
    print(">>> Running Breadth-First Search (BFS) [Optimizes Step Count]...")
    bfs_result = bfs(grid, start, goal)
    bfs_weighted_cost = calculate_path_cost(grid, bfs_result.path)

    print(f"- Algorithm Name  : {bfs_result.algorithm_name}")
    print(f"- Route Found     : {'YES' if bfs_result.found else 'NO'}")
    print(f"- Path Length     : {bfs_result.path_length} steps")
    print(f"- Weighted Cost   : {bfs_weighted_cost} (evaluated entering cell costs)")
    print(f"- Nodes Explored  : {bfs_result.nodes_explored}")
    print(f"- Execution Time  : {bfs_result.execution_time_ms:.4f} ms")
    if bfs_result.found:
        print(f"- Discovered Route: {' -> '.join(str(p) for p in bfs_result.path)}")

    print("\nBFS Route Visualization ('S'=Start, 'G'=Goal, '*' Route):")
    print(render_grid_with_path(grid, bfs_result.path, start, goal))

    # -------------------------------------------------------------------------
    # 2. Run UCS (Weighted minimum-cost search)
    # -------------------------------------------------------------------------
    print("\n" + "-" * 72)
    print(">>> Running Uniform-Cost Search (UCS) [Optimizes Movement Cost]...")
    ucs_result = ucs(grid, start, goal)

    print(f"- Algorithm Name  : {ucs_result.algorithm_name}")
    print(f"- Route Found     : {'YES' if ucs_result.found else 'NO'}")
    print(f"- Path Length     : {ucs_result.path_length} steps")
    print(f"- Total Cost      : {ucs_result.total_cost}")
    print(f"- Nodes Explored  : {ucs_result.nodes_explored}")
    print(f"- Execution Time  : {ucs_result.execution_time_ms:.4f} ms")
    if ucs_result.found:
        print(f"- Discovered Route: {' -> '.join(str(p) for p in ucs_result.path)}")

    print("\nUCS Route Visualization ('S'=Start, 'G'=Goal, '*' Route):")
    print(render_grid_with_path(grid, ucs_result.path, start, goal))

    # -------------------------------------------------------------------------
    # 3. Comparative Summary
    # -------------------------------------------------------------------------
    print("\n" + "=" * 72)
    print("                      ALGORITHM COMPARISON SUMMARY                      ")
    print("=" * 72)
    print(f"{'Metric':<25} | {'BFS (Shortest Steps)':<22} | {'UCS (Minimum Cost)':<22}")
    print("-" * 72)
    print(f"{'Route Found':<25} | {str(bfs_result.found):<22} | {str(ucs_result.found):<22}")
    print(f"{'Path Length (steps)':<25} | {bfs_result.path_length:<22} | {ucs_result.path_length:<22}")
    print(f"{'Total Movement Cost':<25} | {bfs_weighted_cost:<22} | {ucs_result.total_cost:<22}")
    print(f"{'Nodes Explored':<25} | {bfs_result.nodes_explored:<22} | {ucs_result.nodes_explored:<22}")
    print(f"{'Execution Time (ms)':<25} | {bfs_result.execution_time_ms:<22.4f} | {ucs_result.execution_time_ms:<22.4f}")
    print(f"{'Optimality Criteria':<25} | {'Step Count (Unweighted)':<22} | {'Cumulative Cost (Weighted)':<22}")
    print("=" * 72)

    print("\n[Key Observation]")
    print(f"BFS chose the direct route of {bfs_result.path_length} steps through Rough terrain, incurring total cost {bfs_weighted_cost}.")
    print(f"UCS chose the longer detour of {ucs_result.path_length} steps via paved Roads, achieving total cost {ucs_result.total_cost}.")
    print(f"UCS saved {bfs_weighted_cost - ucs_result.total_cost} cost units ({((bfs_weighted_cost - ucs_result.total_cost) / bfs_weighted_cost) * 100:.1f}% reduction) despite {ucs_result.path_length - bfs_result.path_length} additional movement steps.")
    print("Demonstration completed successfully.\n")


if __name__ == "__main__":
    run_demo()
