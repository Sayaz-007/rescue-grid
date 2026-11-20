"""
RescueGrid Analysis Package.

Provides performance analysis, benchmarking, and algorithm comparison utilities
for evaluating AI search and optimization algorithms.
"""

from analysis.algorithm_comparison import (
    ComparisonRecord,
    ComparisonReport,
    ComparisonScenario,
    PathfindingComparator,
    compare_pathfinding_algorithms,
    create_scenario_a_open,
    create_scenario_b_obstacles,
    create_scenario_c_weighted,
    create_scenario_d_no_solution,
    get_standard_scenarios,
)

__all__ = [
    "ComparisonRecord",
    "ComparisonReport",
    "ComparisonScenario",
    "PathfindingComparator",
    "compare_pathfinding_algorithms",
    "create_scenario_a_open",
    "create_scenario_b_obstacles",
    "create_scenario_c_weighted",
    "create_scenario_d_no_solution",
    "get_standard_scenarios",
]
