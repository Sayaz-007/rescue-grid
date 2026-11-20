"""
Depth-First Search (DFS) pathfinding algorithm for RescueGrid.
Explores paths deeply along branches before backtracking, using a LIFO stack.
"""

import time
from typing import Dict, List, Optional, Set
from models.position import Position
from environment.grid import Grid
from algorithms.search_result import SearchResult
from algorithms.search_utils import validate_search_inputs, reconstruct_path


def dfs(grid: Grid, start: Position, goal: Position) -> SearchResult:
    """Find a valid path from start to goal on a 2D Grid using Depth-First Search.

    DFS explores state space deeply down each branch before backtracking, utilizing
    a Python list as a Last-In-First-Out (LIFO) stack.

    Note: Depth-First Search does NOT guarantee the shortest path, but will discover
    a valid path if one exists within a finite traversable space.

    Neighbour ordering accounts for stack insertion order:
    The grid generates neighbours in cardinal order [UP, DOWN, LEFT, RIGHT]. To explore
    them in this deterministic priority order, neighbours are pushed onto the LIFO stack
    in reverse order [RIGHT, LEFT, DOWN, UP], ensuring that UP is on top and popped first.

    Args:
        grid: Bounded 2D simulation Grid environment.
        start: Starting Position of the rescue vehicle.
        goal: Target destination Position (e.g. incident location).

    Returns:
        SearchResult containing the route, visited order, metrics, and timing.

    Raises:
        TypeError: If grid is not Grid, or start/goal is not Position.
        PositionOutOfBoundsError (ValueError, IndexError): If start or goal is out of bounds.
    """
    start_time = time.perf_counter()

    # Input validation
    validate_search_inputs(grid, start, goal)

    algorithm_name = "Depth-First Search"

    # Handle blocked starting position or blocked destination
    if not grid.is_walkable(start) or not grid.is_walkable(goal):
        end_time = time.perf_counter()
        return SearchResult(
            algorithm_name=algorithm_name,
            start_position=start,
            goal_position=goal,
            found=False,
            path=[],
            visited_order=[],
            nodes_explored=0,
            path_length=0,
            total_cost=None,
            execution_time_ms=(end_time - start_time) * 1000.0,
        )

    # LIFO stack for frontier exploration
    stack: List[Position] = [start]

    # Discovered set preventing redundant insertion and infinite loops
    discovered: Set[Position] = {start}

    # Parent map for path reconstruction
    parent: Dict[Position, Optional[Position]] = {start: None}

    # Tracking expansion order for analysis and visualization
    visited_order: List[Position] = []
    found: bool = False

    while stack:
        curr = stack.pop()
        visited_order.append(curr)

        # Goal test upon expansion
        if curr == goal:
            found = True
            break

        # Retrieve walkable neighbours in cardinal order: UP, DOWN, LEFT, RIGHT
        neighbours = grid.get_walkable_neighbours(curr)

        # Account for stack insertion order: push in reverse order so that
        # the first cardinal neighbour (UP) is on top of the stack and popped first
        for neighbour in reversed(neighbours):
            if neighbour not in discovered:
                discovered.add(neighbour)
                parent[neighbour] = curr
                stack.append(neighbour)

    end_time = time.perf_counter()
    execution_time_ms = (end_time - start_time) * 1000.0

    if found:
        path = reconstruct_path(parent, start, goal)
        path_length = len(path) - 1
        total_cost = path_length
    else:
        path = []
        path_length = 0
        total_cost = None

    return SearchResult(
        algorithm_name=algorithm_name,
        start_position=start,
        goal_position=goal,
        found=found,
        path=path,
        visited_order=visited_order,
        nodes_explored=len(visited_order),
        path_length=path_length,
        total_cost=total_cost,
        execution_time_ms=execution_time_ms,
    )


class DepthFirstSearch:
    """Class wrapper for Depth-First Search algorithm execution."""

    @staticmethod
    def search(grid: Grid, start: Position, goal: Position) -> SearchResult:
        """Execute Depth-First Search on the provided grid environment."""
        return dfs(grid, start, goal)

    def __call__(self, grid: Grid, start: Position, goal: Position) -> SearchResult:
        """Allow instance callable execution."""
        return dfs(grid, start, goal)
