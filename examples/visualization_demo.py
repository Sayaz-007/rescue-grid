"""
RescueGrid — Grid Visualization and Path Animation Demonstration (Phase 9.2).

Demonstrates Matplotlib-based 2D disaster grid visualization, search exploration
overlays, side-by-side algorithm comparison grids, performance charts,
and route animations.
"""

import os
import sys
from typing import Tuple
import warnings
warnings.filterwarnings("ignore", message=".*Animation was deleted without rendering anything.*")

# Ensure root workspace directory is on Python search path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import matplotlib
# If running without interactive display or in CI, default to headless Agg backend
if not os.environ.get("DISPLAY") and sys.platform != "darwin":
    matplotlib.use("Agg")

import matplotlib.pyplot as plt

from environment.cell import TerrainType, TerrainCostConfig
from environment.grid import Grid
from models.position import Position
from algorithms.bfs import bfs
from algorithms.ucs import ucs
from algorithms.astar import astar
from algorithms.search_utils import calculate_path_cost
from visualization.grid_visualizer import (
    GridVisualizer,
    visualize_grid,
    visualize_search,
    visualize_comparison,
    plot_performance_charts,
)


def create_disaster_showcase_grid() -> Tuple[Grid, Position, Position]:
    """Construct an illustrative 8-row by 12-column disaster simulation grid.

    Features:
    - Arterial highway road bypass along Row 1 (Movement cost = 1.0).
    - Damaged rough terrain transit corridor along Row 4 (Movement cost = 4.0).
    - Collapsed building rubble hazards blocking direct central passage.
    - Deep flood water hazard zone.
    - Active fire zone hazard.
    - Normal urban ground elsewhere (Movement cost = 2.0).
    """
    grid = Grid(rows=8, cols=12, default_terrain=TerrainType.NORMAL)

    # 1. Paved Highway Bypass along Row 1 (Fast transit: cost 1)
    for x in range(11):
        grid.add_road(Position(x, 1))
    grid.add_road(Position(0, 2))   # Access ramp from depot
    grid.add_road(Position(0, 3))
    grid.add_road(Position(10, 2))  # Egress ramp to incident
    grid.add_road(Position(10, 3))

    # 2. Damaged Rough Ground along Row 4 (High resistance: cost 4)
    for x in range(1, 10):
        grid.add_rough_terrain(Position(x, 4))

    # 3. Structural Rubble Hazards (Impassable collapsed buildings)
    grid.add_collapsed_building(Position(3, 2))
    grid.add_collapsed_building(Position(3, 3))
    grid.add_collapsed_building(Position(4, 3))

    # 4. Deep Flood Water Hazards (Impassable)
    grid.add_flood_zone(Position(7, 2))
    grid.add_flood_zone(Position(7, 3))

    # 5. Active Fire Zone Hazards (Impassable)
    grid.add_fire_zone(Position(5, 5))
    grid.add_fire_zone(Position(6, 5))

    start = Position(0, 4)   # Rescue Dispatch Depot
    goal = Position(10, 4)   # Disaster Incident Site

    return grid, start, goal


def run_visualization_demo() -> None:
    """Execute visualization demonstration."""
    print("=" * 80)
    print("       RescueGrid — Grid Visualization & Path Animation (Phase 9.2)         ")
    print("=" * 80)

    grid, start, goal = create_disaster_showcase_grid()

    print("\n[Environment Configuration]")
    print(f"- Grid Dimensions : {grid.cols} cols x {grid.rows} rows ({grid.total_cells} cells)")
    print(f"- Depot Start (S) : {start}")
    print(f"- Incident Goal (G): {goal}")
    print("\nTerrain Movement Costs:")
    print(f"  • ROAD ('=')       : {TerrainCostConfig.get_cost(TerrainType.ROAD)} cost/step (Paved arterial bypass)")
    print(f"  • NORMAL ('.')     : {TerrainCostConfig.get_cost(TerrainType.NORMAL)} cost/step (Standard urban surface)")
    print(f"  • ROUGH (':')      : {TerrainCostConfig.get_cost(TerrainType.ROUGH)} cost/step (Damaged high-resistance corridor)")
    print("  • RUBBLE ('X')     : Impassable hazard")
    print("  • WATER ('W')      : Impassable hazard")
    print("  • FIRE_ZONE ('F')  : Impassable hazard")

    # Execute pathfinding algorithms
    print("\n>>> Executing AI Pathfinding Algorithms...")
    print("  1. Running Breadth-First Search (BFS)...")
    bfs_result = bfs(grid, start, goal)

    print("  2. Running Uniform-Cost Search (UCS)...")
    ucs_result = ucs(grid, start, goal)

    print("  3. Running A* Search (A*)...")
    astar_result = astar(grid, start, goal)

    # Summary performance table
    bfs_wcost = calculate_path_cost(grid, bfs_result.path)
    print("\n" + "=" * 80)
    print(f"{'Algorithm':<22} | {'Found':<6} | {'Steps':<7} | {'Total Cost':<12} | {'Explored':<10} | {'Time (ms)':<10}")
    print("-" * 80)
    for r, wcost in [(bfs_result, bfs_wcost), (ucs_result, ucs_result.total_cost), (astar_result, astar_result.total_cost)]:
        print(f"{r.algorithm_name:<22} | {str(r.found):<6} | {r.path_length:<7} | {wcost:<12.1f} | {r.nodes_explored:<10} | {r.execution_time_ms:<10.3f}")
    print("=" * 80)

    # Prepare output directory for figures
    output_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "output"))
    os.makedirs(output_dir, exist_ok=True)

    viz = GridVisualizer(cell_size=0.85, show_legend=True)

    # 1. Visualize A* Search Result (Exploration + Final Route)
    print("\n[1/3] Generating A* Search Visualization...")
    fig_astar, _ = viz.visualize_search(grid, astar_result)
    path_astar_img = os.path.join(output_dir, "demo_astar_search.png")
    fig_astar.savefig(path_astar_img, bbox_inches="tight")
    plt.close(fig_astar)
    print(f"      Saved: {path_astar_img}")

    # 2. Side-by-Side Algorithm Comparison
    print("\n[2/3] Generating Side-by-Side Comparative Grid (BFS vs UCS vs A*)...")
    fig_comp, _ = viz.visualize_comparison(grid, [bfs_result, ucs_result, astar_result], ncols=3)
    path_comp_img = os.path.join(output_dir, "demo_comparison_grid.png")
    fig_comp.savefig(path_comp_img, bbox_inches="tight")
    plt.close(fig_comp)
    print(f"      Saved: {path_comp_img}")

    # 3. Performance Metrics Bar Charts
    print("\n[3/3] Generating Performance Benchmark Charts (2x2 Metrics)...")
    fig_charts, _ = viz.plot_performance_charts(
        [bfs_result, ucs_result, astar_result],
        title="Disaster Transit Corridor Benchmark Performance"
    )
    path_charts_img = os.path.join(output_dir, "demo_performance_charts.png")
    fig_charts.savefig(path_charts_img, bbox_inches="tight")
    plt.close(fig_charts)
    print(f"      Saved: {path_charts_img}")

    # Optional Animation verification
    print("\n>>> Testing A* Exploration & Route Animation Object...")
    anim = viz.animate_search(grid, astar_result, interval_ms=40)
    print(f"    Animation successfully generated: {type(anim).__name__} (deterministic frames)")

    print("\n" + "=" * 80)
    print("Phase 9.2 Visualization Demonstration completed successfully.")
    print("Generated charts and grid figures are available in:")
    print(f"  {output_dir}")
    print("=" * 80 + "\n")


if __name__ == "__main__":
    run_visualization_demo()
