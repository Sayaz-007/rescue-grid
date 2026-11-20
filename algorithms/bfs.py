"""
Breadth-First Search (BFS) pathfinding algorithm for RescueGrid.
Explores nodes uniformly in levels, guaranteeing the shortest path in terms of movement steps.
"""

import time
from collections import deque
from typing import Deque, Dict, List, Optional, Set
from models.position import Position
from environment.grid import Grid
from algorithms.search_result import SearchResult
from algorithms.search_utils import validate_search_inputs, reconstruct_path


def bfs(grid: Grid, start: Position, goal: Position) -> SearchResult:
    """Find the shortest path from start to goal on a 2D Grid using Breadth-First Search.

    BFS explores state space in frontier levels using a First-In-First-Out (FIFO) queue.
    Because all movements have uniform cost (1 per step), the first time the goal
    state is dequeued, it is guaranteed to have the minimal path length.

    Deterministic neighbour ordering is preserved using Grid's cardinal order:
    UP (x, y - 1), DOWN (x, y + 1), LEFT (x - 1, y), RIGHT (x + 1, y).

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

    algorithm_name = "Breadth-First Search"

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

    # FIFO queue for frontier exploration
    queue: Deque[Position] = deque([start])

    # Discovered set tracking positions already added to the queue
    discovered: Set[Position] = {start}

    # Parent map for path reconstruction
    parent: Dict[Position, Optional[Position]] = {start: None}

    # Tracking expansion order for analysis and visualization
    visited_order: List[Position] = []
    found: bool = False

    while queue:
        curr = queue.popleft()
        visited_order.append(curr)

        # Goal test upon expansion
        if curr == goal:
            found = True
            break

        # Expand neighbours in deterministic cardinal order: UP, DOWN, LEFT, RIGHT
        for neighbour in grid.get_walkable_neighbours(curr):
            if neighbour not in discovered:
                discovered.add(neighbour)
                parent[neighbour] = curr
                queue.append(neighbour)

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


class BreadthFirstSearch:
    """Class wrapper for Breadth-First Search algorithm execution."""

    @staticmethod
    def search(grid: Grid, start: Position, goal: Position) -> SearchResult:
        """Execute Breadth-First Search on the provided grid environment."""
        return bfs(grid, start, goal)

    def __call__(self, grid: Grid, start: Position, goal: Position) -> SearchResult:
        """Allow instance callable execution."""
        return bfs(grid, start, goal)
