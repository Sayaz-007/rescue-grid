"""
AI search algorithms and pathfinding infrastructure for RescueGrid.
Provides Breadth-First Search (BFS), Depth-First Search (DFS),
Uniform-Cost Search (UCS), and A* Search implementations, data structures,
heuristics, and validation utilities.
"""

from algorithms.search_result import SearchResult
from algorithms.search_utils import (
    PositionOutOfBoundsError,
    validate_search_inputs,
    reconstruct_path,
    is_valid_path,
    calculate_path_cost,
    manhattan_distance,
    manhattan_heuristic,
    render_grid_with_path,
)
from algorithms.bfs import bfs, BreadthFirstSearch
from algorithms.dfs import dfs, DepthFirstSearch
from algorithms.ucs import ucs, UniformCostSearch
from algorithms.astar import astar, AStarSearch
from algorithms.hill_climbing import hill_climbing, HillClimbingSearch
from algorithms.csp_result import CSPResult
from algorithms.csp import CSPSolver, allocate_resources_csp

__all__ = [
    "SearchResult",
    "CSPResult",
    "PositionOutOfBoundsError",
    "validate_search_inputs",
    "reconstruct_path",
    "is_valid_path",
    "calculate_path_cost",
    "manhattan_distance",
    "manhattan_heuristic",
    "render_grid_with_path",
    "bfs",
    "dfs",
    "ucs",
    "astar",
    "hill_climbing",
    "CSPSolver",
    "allocate_resources_csp",
    "BreadthFirstSearch",
    "DepthFirstSearch",
    "UniformCostSearch",
    "AStarSearch",
    "HillClimbingSearch",
]
