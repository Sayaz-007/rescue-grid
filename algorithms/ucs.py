"""
Uniform-Cost Search (UCS) pathfinding algorithm for RescueGrid.
Explores state space using a min-heap priority queue, guaranteeing minimum-cost routes
over weighted, non-negative terrain graphs.
"""

import heapq
import time
from typing import Dict, List, Optional, Tuple
from models.position import Position
from environment.grid import Grid
from algorithms.search_result import SearchResult
from algorithms.search_utils import validate_search_inputs, reconstruct_path


def ucs(grid: Grid, start: Position, goal: Position) -> SearchResult:
    """Find the minimum-cost path from start to goal on a 2D Grid using Uniform-Cost Search.

    Uniform-Cost Search (Dijkstra's algorithm on state graphs) expands nodes in order of
    cumulative path cost using Python's `heapq` priority queue.

    Cost Convention:
        - The starting cell (start) is not charged (initial cost = 0.0).
        - The cost of entering each subsequent cell is that cell's movement cost.
        - Total path cost for [start, c1, ..., goal] = cost(c1) + ... + cost(goal).
        - Blocked or obstacle cells have infinite cost and are never enqueued.

    Frontier & State Management:
        - Priority Queue: Min-heap of (cumulative_cost, entry_id, position) tuples.
        - The monotonically increasing `entry_id` breaks ties deterministically
          and prevents direct comparison between Position instances.
        - Best-known cost dictionary (`cost_so_far`) tracks optimal costs to discovered positions.
        - Outdated priority-queue entries (superseded by later cheaper routes) are safely discarded.
        - The goal test is performed only when the goal state is dequeued with its minimal cost.

    Args:
        grid: Bounded 2D simulation Grid environment with weighted terrain.
        start: Starting Position of the rescue vehicle.
        goal: Target destination Position (e.g. disaster scene).

    Returns:
        SearchResult containing the minimum-cost route, visited order, metrics, and timing.

    Raises:
        TypeError: If grid is not Grid, or start/goal is not Position.
        PositionOutOfBoundsError (ValueError, IndexError): If start or goal is out of bounds.
    """
    start_time = time.perf_counter()

    # Input type and boundary validation
    validate_search_inputs(grid, start, goal)

    algorithm_name = "Uniform-Cost Search"

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

    # Requirement 1: Start with cumulative cost zero
    # Priority queue stores tuples: (cumulative_cost, entry_counter, position)
    entry_counter: int = 0
    frontier: List[Tuple[float, int, Position]] = []
    heapq.heappush(frontier, (0.0, entry_counter, start))

    # Requirement 4: Maintain a best-known cost dictionary
    cost_so_far: Dict[Position, float] = {start: 0.0}

    # Requirement 5: Parent map updated whenever a cheaper route is discovered
    parent: Dict[Position, Optional[Position]] = {start: None}

    visited_order: List[Position] = []
    found: bool = False

    while frontier:
        # Requirement 2: Always expand frontier state with smallest cumulative cost
        curr_cost, _, curr = heapq.heappop(frontier)

        # Requirement 6: Handle outdated priority-queue entries correctly
        # If a cheaper route to curr was already processed, skip this obsolete entry
        if curr_cost > cost_so_far.get(curr, float("inf")):
            continue

        visited_order.append(curr)

        # Requirement 7: Accept goal only when removed from priority queue with best cost
        if curr == goal:
            found = True
            break

        # Expand traversable cardinal neighbours in deterministic order: UP, DOWN, LEFT, RIGHT
        for neighbour in grid.get_walkable_neighbours(curr):
            # Requirement 8: Never enqueue blocked cells
            step_cost = grid.get_movement_cost(neighbour)
            if not grid.is_walkable(neighbour) or step_cost == float("inf"):
                continue

            # Requirement 3: Calculate the cost of entering each neighbouring cell
            new_cost = curr_cost + step_cost

            # Requirement 5: Update parent whenever a cheaper route is discovered
            if new_cost < cost_so_far.get(neighbour, float("inf")):
                cost_so_far[neighbour] = new_cost
                parent[neighbour] = curr
                entry_counter += 1
                heapq.heappush(frontier, (new_cost, entry_counter, neighbour))

    end_time = time.perf_counter()
    execution_time_ms = (end_time - start_time) * 1000.0

    if found:
        # Requirement 9: Reconstruct minimum-cost path
        path = reconstruct_path(parent, start, goal)
        path_length = len(path) - 1
        total_cost: Optional[float] = cost_so_far[goal]
        # Format as int if whole number, keeping numerical equality
        if total_cost is not None and isinstance(total_cost, float) and total_cost.is_integer():
            total_cost = int(total_cost)
    else:
        path = []
        path_length = 0
        total_cost = None

    # Requirement 10: Return existing common SearchResult structure
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


class UniformCostSearch:
    """Class wrapper for Uniform-Cost Search algorithm execution."""

    @staticmethod
    def search(grid: Grid, start: Position, goal: Position) -> SearchResult:
        """Execute Uniform-Cost Search on the provided grid environment."""
        return ucs(grid, start, goal)

    def __call__(self, grid: Grid, start: Position, goal: Position) -> SearchResult:
        """Allow instance callable execution."""
        return ucs(grid, start, goal)
