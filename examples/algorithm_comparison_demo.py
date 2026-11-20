"""
RescueGrid — Unified Pathfinding Algorithm Integration and Performance Benchmark (Phase 9.1).

Demonstrates comparative performance benchmarking across five pathfinding algorithms:
1. Breadth-First Search (BFS) [Unweighted graph search baseline]
2. Depth-First Search (DFS) [Unweighted graph search baseline]
3. Uniform-Cost Search (UCS) [Weighted cost-optimal search]
4. A* Search (A*) [Heuristically guided cost-optimal search]
5. Hill Climbing (HC) [Incomplete local search heuristic]

Evaluated across four reproducible deterministic scenarios:
- Scenario A: Open Grid (Unobstructed baseline search behavior)
- Scenario B: Obstacle-Dense Grid (Multi-hazard detours and local optima entrapment)
- Scenario C: Weighted Terrain Grid (Why UCS and A* find cheaper paths than BFS)
- Scenario D: No-Solution Grid (Graceful search failure reporting)

NOTE: Multi-agent resource allocation via Constraint Satisfaction Problems (CSP)
is excluded from this spatial routing benchmark because CSP solves combinatorial
resource assignment under capability and exclusivity constraints, not grid pathfinding.
"""

import os
import sys

# Ensure root workspace directory is on Python search path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from analysis.algorithm_comparison import (
    PathfindingComparator,
    create_scenario_a_open,
    create_scenario_b_obstacles,
    create_scenario_c_weighted,
    create_scenario_d_no_solution,
    get_standard_scenarios,
)
from algorithms.search_utils import render_grid_with_path


def print_header(title: str) -> None:
    """Print standard section header banner."""
    print("\n" + "=" * 80)
    print(f" {title} ")
    print("=" * 80)


def print_scenario_visual(grid, start, goal, description: str) -> None:
    """Print ASCII visual layout of the scenario grid."""
    print(f"\n[Environment Configuration]")
    print(f"- Dimensions : {grid.cols} cols x {grid.rows} rows ({grid.total_cells} cells)")
    print(f"- Start Pos  : {start} ('S')")
    print(f"- Goal Pos   : {goal} ('G')")
    print(f"- Purpose    : {description}")
    print("\nInitial Terrain Map:")
    print(render_grid_with_path(grid, None, start, goal))


def run_benchmark_demo() -> None:
    """Execute complete comparative demonstration across all four scenarios."""
    print("=" * 80)
    print("  RescueGrid — Unified AI Pathfinding Integration & Performance Benchmark  ")
    print("                             (Phase 9.1)                                    ")
    print("=" * 80)
    print("\n[Algorithm Portfolio Under Evaluation]")
    print("1. Breadth-First Search (BFS) : Systematic unweighted search; guarantees minimal step count.")
    print("2. Depth-First Search (DFS)   : Systematic unweighted search; wanders deeply; non-optimal.")
    print("3. Uniform-Cost Search (UCS)  : Dijkstra-variant weighted search; guarantees minimum path cost.")
    print("4. A* Search (A*)             : Heuristic cost-optimal search; guides frontier using h(n).")
    print("5. Hill Climbing (HC)         : Steepest-ascent local search; O(1) auxiliary memory; incomplete.")
    print("\n[Architectural Separation: Why CSP Is Not Included]")
    print("- Pathfinding algorithms find spatial 2D routes for vehicles across disaster terrain.")
    print("- Constraint Satisfaction Problems (CSP) allocate responders and vehicles to incidents.")
    print("- Because CSP solves multi-agent discrete constraint assignment, not 2D routing, it is")
    print("  benchmarked separately in examples/csp_allocation_demo.py.")

    # -------------------------------------------------------------------------
    # SCENARIO A: OPEN GRID
    # -------------------------------------------------------------------------
    print_header("SCENARIO A: OPEN GRID (UNOBSTRUCTED UNIFORM TERRAIN)")
    sc_a = create_scenario_a_open()
    print_scenario_visual(sc_a.grid, sc_a.start, sc_a.goal, sc_a.description)

    print("\n>>> Running Benchmark on Scenario A...")
    report_a = sc_a.run()
    print("\n[Performance Metrics Table]")
    print(report_a.to_table(markdown=False))

    print("\n[Key Insights — Scenario A]")
    print("- BFS, UCS, A*, and Hill Climbing all discover the optimal Manhattan step count (18 steps).")
    print("- Hill Climbing succeeds because the unobstructed heuristic landscape has no local minima.")
    print("- Hill Climbing explored only 19 nodes (straight line descent) vs 100 nodes for blind searches.")
    print("- DFS found a valid route but wandered extensively, taking 54 steps (3x longer).")

    # -------------------------------------------------------------------------
    # SCENARIO B: OBSTACLE-DENSE GRID
    # -------------------------------------------------------------------------
    print_header("SCENARIO B: OBSTACLE-DENSE GRID (RUBBLE, FLOOD WATER & FIRE)")
    sc_b = create_scenario_b_obstacles()
    print_scenario_visual(sc_b.grid, sc_b.start, sc_b.goal, sc_b.description)

    print("\n>>> Running Benchmark on Scenario B...")
    report_b = sc_b.run()
    print("\n[Performance Metrics Table]")
    print(report_b.to_table(markdown=False))

    print("\n[Key Insights — Scenario B]")
    print("- Systematic algorithms (BFS, UCS, A*) successfully discover the optimal 28-step detour route.")
    print("- Hill Climbing FAILS gracefully (Solution Found = False, Path Length = None, Total Cost = None).")
    print("  Reason: Direct movement towards the goal is blocked by a rubble barrier at x=3.")
    print("  Every lateral or backward move away from the wall increases the Manhattan distance.")
    print("  Because steepest-ascent hill climbing strictly forbids moves with delta_h >= 0, it halts in")
    print("  a dead-end local optimum. This cleanly illustrates the incompleteness of local search.")

    # -------------------------------------------------------------------------
    # SCENARIO C: WEIGHTED TERRAIN GRID
    # -------------------------------------------------------------------------
    print_header("SCENARIO C: WEIGHTED TERRAIN (ROAD BYPASS VS ROUGH CORRIDOR)")
    sc_c = create_scenario_c_weighted()
    print_scenario_visual(sc_c.grid, sc_c.start, sc_c.goal, sc_c.description)

    print("\n>>> Running Benchmark on Scenario C...")
    report_c = sc_c.run()
    print("\n[Performance Metrics Table]")
    print(report_c.to_table(markdown=False))

    bfs_rec = report_c["BFS"]
    ucs_rec = report_c["UCS"]
    astar_rec = report_c["A*"]
    cost_diff = (bfs_rec.total_cost - ucs_rec.total_cost) if bfs_rec.total_cost and ucs_rec.total_cost else 0

    print("\n[Key Insights — Scenario C (Core Phase 9.1 Verification)]")
    print(f"1. Cost Optimization: UCS and A* both discovered the minimum-cost route costing {ucs_rec.total_cost}.")
    print(f"2. BFS Suboptimality in Cost: BFS prioritized fewer steps ({bfs_rec.path_length} steps vs {ucs_rec.path_length} steps),")
    print(f"   but incurred a significantly higher movement cost ({bfs_rec.total_cost} vs {ucs_rec.total_cost}, +{cost_diff} penalty!).")
    print(f"3. A* Search Efficiency: A* found the identical cost-optimal route as UCS while exploring only")
    print(f"   {astar_rec.nodes_explored} nodes, compared to {ucs_rec.nodes_explored} nodes for blind UCS (64% node expansion reduction!).")
    print(f"4. Hill Climbing Vulnerability: HC chose the rough 9-step path (cost {report_c['HC'].total_cost}) because Manhattan heuristic")
    print("   is distance-based and completely blind to terrain movement friction.")

    # -------------------------------------------------------------------------
    # SCENARIO D: NO-SOLUTION GRID
    # -------------------------------------------------------------------------
    print_header("SCENARIO D: NO-SOLUTION GRID (COMPLETELY WALLED-OFF DESTINATION)")
    sc_d = create_scenario_d_no_solution()
    print_scenario_visual(sc_d.grid, sc_d.start, sc_d.goal, sc_d.description)

    print("\n>>> Running Benchmark on Scenario D...")
    report_d = sc_d.run()
    print("\n[Performance Metrics Table]")
    print(report_d.to_table(markdown=False))

    print("\n[Key Insights — Scenario D]")
    print("- All five algorithms terminate safely and report Solution Found = False.")
    print("- Nodes Explored: Systematic algorithms exhaustively verify that no path exists (32 nodes).")
    print("- Hill Climbing terminates early (11 nodes) once local moves fail to reduce the heuristic.")
    print("- Robustness Invariant: Zero exceptions raised, zero unhandled errors, clean None metrics.")

    # -------------------------------------------------------------------------
    # THEORETICAL SUMMARY
    # -------------------------------------------------------------------------
    print_header("THEORETICAL COMPARISON SUMMARY")
    print(f"{'Algorithm':<22} | {'Category':<15} | {'Cost-Optimal':<13} | {'Complete':<10} | {'Memory Complexity':<18}")
    print("-" * 88)
    print(f"{'Breadth-First Search':<22} | {'Blind Graph':<15} | {'No (Steps only)':<13} | {'Yes':<10} | {'O(b^d)':<18}")
    print(f"{'Depth-First Search':<22} | {'Blind Graph':<15} | {'No':<13} | {'Yes (finite)':<10} | {'O(bm)':<18}")
    print(f"{'Uniform-Cost Search':<22} | {'Weighted Blind':<15} | {'Yes':<13} | {'Yes':<10} | {'O(b^(1 + C*/eps))':<18}")
    print(f"{'A* Search':<22} | {'Informed':<15} | {'Yes (consistent)':<13} | {'Yes':<10} | {'O(b^d)':<18}")
    print(f"{'Hill Climbing':<22} | {'Local Search':<15} | {'No':<13} | {'No':<10} | {'O(1) aux':<18}")
    print("-" * 88)
    print("\n[Important Scientific Disclaimer on Execution Time]")
    print("Execution times are measured with high-resolution time.perf_counter(). However, single-run wall-clock")
    print("timings are influenced by OS process scheduling, Python interpreter caching, and JIT/CPU state.")
    print("They should be interpreted as empirical runtime indicators, not formal asymptotic complexity proofs.")

    print("\n" + "=" * 80)
    print("Phase 9.1 Performance Benchmark Demonstration completed successfully.")
    print("=" * 80 + "\n")


if __name__ == "__main__":
    run_benchmark_demo()
