"""
Demonstration script for AI search algorithms in RescueGrid.
Demonstrates Breadth-First Search (BFS) and Depth-First Search (DFS)
in a simulated disaster environment with obstacles, rubble, floods, and fire zones.
"""

import os
import sys

# Ensure root workspace directory is on Python search path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from models.position import Position
from environment.grid import Grid
from environment.cell import TerrainType
from algorithms.bfs import bfs
from algorithms.dfs import dfs
from algorithms.search_utils import render_grid_with_path


def create_disaster_grid() -> Grid:
    """Create a sample 8-row by 12-column urban disaster grid with varied hazards."""
    # 8 rows (height, y: 0..7), 12 columns (width, x: 0..11)
    grid = Grid(rows=8, cols=12, default_terrain=TerrainType.NORMAL)

    # Establish an east-west transit road along row 3
    for x in range(12):
        grid.add_road(Position(x, 3))

    # Add disaster hazards requiring detours:
    # 1. Structural rubble from collapsed buildings
    grid.add_collapsed_building(Position(3, 1))
    grid.add_collapsed_building(Position(3, 2))
    grid.add_collapsed_building(Position(3, 3))
    grid.add_collapsed_building(Position(3, 4))

    # 2. Flash flood water hazard zone
    grid.add_flood_zone(Position(6, 2))
    grid.add_flood_zone(Position(6, 3))
    grid.add_flood_zone(Position(6, 4))
    grid.add_flood_zone(Position(7, 3))

    # 3. Active fire zone
    grid.add_fire_zone(Position(8, 5))
    grid.add_fire_zone(Position(8, 6))
    grid.add_fire_zone(Position(9, 5))

    # 4. Physical barricades / debris
    grid.add_obstacle(Position(1, 5))
    grid.add_obstacle(Position(2, 5))

    return grid


def run_demo() -> None:
    """Execute search demonstration comparing BFS and DFS."""
    print("=" * 68)
    print("        RescueGrid — AI Search Demonstration (Phase 3)        ")
    print("        Breadth-First Search (BFS) vs Depth-First Search (DFS) ")
    print("=" * 68)

    # Step 1 & 2: Create sample grid with obstacles
    grid = create_disaster_grid()

    # Step 3: Define start and goal positions
    start = Position(0, 0)   # Emergency Dispatch Depot
    goal = Position(10, 6)   # Severe Incident Location

    print(f"\n[Environment Setup]")
    print(f"- Grid Dimensions : {grid.cols} columns x {grid.rows} rows ({grid.total_cells} cells)")
    print(f"- Dispatch Start  : {start} (depot)")
    print(f"- Incident Target : {goal} (disaster scene)")
    print("\nInitial Disaster Grid Map:")
    print("Legend: '.' Normal, '=' Road, 'X' Rubble, 'W' Water, 'F' Fire, '#' Obstacle")
    print(grid.to_string())

    # Step 4: Run BFS
    print("\n" + "-" * 68)
    print(">>> Running Breadth-First Search (BFS)...")
    bfs_result = bfs(grid, start, goal)

    # Step 5 & 6: Print BFS results
    print(f"- Route Found    : {'YES' if bfs_result.found else 'NO'}")
    print(f"- Path Length    : {bfs_result.path_length} steps")
    print(f"- Total Cost     : {bfs_result.total_cost}")
    print(f"- Nodes Explored : {bfs_result.nodes_explored}")
    print(f"- Execution Time : {bfs_result.execution_time_ms:.4f} ms")
    if bfs_result.found:
        route_str = " -> ".join(str(p) for p in bfs_result.path)
        print(f"- Discovered Path: {route_str}")

    # Step 7: Display grid with BFS route overlay
    print("\nBFS Route Visualization ('S'=Start, 'G'=Goal, '*' Route):")
    print(render_grid_with_path(grid, bfs_result.path, start, goal))

    # Step 4: Run DFS
    print("\n" + "-" * 68)
    print(">>> Running Depth-First Search (DFS)...")
    dfs_result = dfs(grid, start, goal)

    # Step 5 & 6: Print DFS results
    print(f"- Route Found    : {'YES' if dfs_result.found else 'NO'}")
    print(f"- Path Length    : {dfs_result.path_length} steps")
    print(f"- Total Cost     : {dfs_result.total_cost}")
    print(f"- Nodes Explored : {dfs_result.nodes_explored}")
    print(f"- Execution Time : {dfs_result.execution_time_ms:.4f} ms")
    if dfs_result.found:
        route_str = " -> ".join(str(p) for p in dfs_result.path)
        print(f"- Discovered Path: {route_str}")

    # Step 7: Display grid with DFS route overlay
    print("\nDFS Route Visualization ('S'=Start, 'G'=Goal, '*' Route):")
    print(render_grid_with_path(grid, dfs_result.path, start, goal))

    # Comparative Summary
    print("\n" + "=" * 68)
    print("                   ALGORITHM COMPARISON SUMMARY                     ")
    print("=" * 68)
    print(f"{'Metric':<22} | {'BFS (Breadth-First)':<20} | {'DFS (Depth-First)':<20}")
    print("-" * 68)
    print(f"{'Route Found':<22} | {str(bfs_result.found):<20} | {str(dfs_result.found):<20}")
    print(f"{'Path Length (steps)':<22} | {bfs_result.path_length:<20} | {dfs_result.path_length:<20}")
    print(f"{'Total Cost':<22} | {bfs_result.total_cost:<20} | {dfs_result.total_cost:<20}")
    print(f"{'Nodes Explored':<22} | {bfs_result.nodes_explored:<20} | {dfs_result.nodes_explored:<20}")
    print(f"{'Execution Time (ms)':<22} | {bfs_result.execution_time_ms:<20.4f} | {dfs_result.execution_time_ms:<20.4f}")
    print(f"{'Optimality':<22} | {'Guaranteed Shortest':<20} | {'Suboptimal/Deep':<20}")
    print("=" * 68)

    # Step 8: Demonstration of unreachable scenario
    print("\n>>> Demonstrating Unreachable Scenario (Trapped Casualty)...")
    unreachable_grid = Grid(rows=5, cols=5)
    unreachable_goal = Position(4, 4)
    # Surround goal completely with rubble
    unreachable_grid.add_collapsed_building(Position(3, 4))
    unreachable_grid.add_collapsed_building(Position(4, 3))
    unreachable_grid.add_collapsed_building(Position(3, 3))

    u_bfs = bfs(unreachable_grid, Position(0, 0), unreachable_goal)
    u_dfs = dfs(unreachable_grid, Position(0, 0), unreachable_goal)
    print(f"- BFS on Unreachable Goal: found={u_bfs.found}, path={u_bfs.path}, explored={u_bfs.nodes_explored}")
    print(f"- DFS on Unreachable Goal: found={u_dfs.found}, path={u_dfs.path}, explored={u_dfs.nodes_explored}")
    print("Demonstration completed successfully.\n")


if __name__ == "__main__":
    run_demo()
