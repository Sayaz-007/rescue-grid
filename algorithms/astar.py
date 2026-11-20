"""
A* Search algorithm for RescueGrid.
Combines cumulative movement cost g(n) with an admissible cost-scaled Manhattan distance
heuristic h(n) to find the minimum-cost route guided toward the incident destination.
"""

import heapq
import math
import time
from typing import Callable, Dict, List, Optional, Set, Tuple
from models.position import Position
from environment.cell import TerrainCostConfig
from environment.grid import Grid
from algorithms.search_result import SearchResult
from algorithms.search_utils import (
    validate_search_inputs,
    reconstruct_path,
    manhattan_heuristic,
)


def astar(
    grid: Grid,
    start: Position,
    goal: Position,
    heuristic_func: Optional[Callable[[Position, Position, float], float]] = None,
) -> SearchResult:
    """Find the minimum-cost path from start to goal on a 2D Grid using A* Search.

    Evaluation Function:
        f(n) = g(n) + h(n)
        where:
        - g(n): Actual cumulative movement cost from start to current cell n.
        - h(n): Admissible estimate of remaining cost to goal:
                h(n) = Manhattan(n, goal) * min_traversable_movement_cost.
        - f(n): Estimated total cost of complete route passing through n.

    Optimality & Consistency:
        Because all movement costs are positive (c >= 1.0 > 0) and the cost-scaled
        Manhattan heuristic satisfies the triangle inequality h(n) <= c(n, n') + h(n'),
        the heuristic is consistent (monotonic).
        Consequently:
        - The first time any state is removed from the priority queue, its g-cost
          is already guaranteed to be optimal.
        - A closed state never strictly needs reopening under consistent heuristics,
          though this implementation defensively supports reopening if an improved
          path is ever discovered.

    Frontier & Tie-Breaking:
        - Min-heap priority queue using Python's `heapq`.
        - Queue elements: (f_score, h_score, entry_counter, position)
          - f_score: Primary ordering (lowest estimated total cost expanded first).
          - h_score: Secondary tie-breaker (favours states closer to goal when f matches).
          - entry_counter: Tertiary deterministic FIFO tie-breaker avoiding '<' on Position.

    Args:
        grid: Bounded 2D simulation Grid environment with weighted terrain.
        start: Starting Position of the rescue vehicle.
        goal: Target destination Position (disaster incident scene).
        heuristic_func: Optional heuristic function signature (pos, goal, min_cost) -> float.
            Defaults to cost-scaled Manhattan heuristic.

    Returns:
        SearchResult containing the minimum-cost route, visited order, metrics, and timing.

    Raises:
        TypeError: If grid is not Grid, or start/goal is not Position.
        PositionOutOfBoundsError (ValueError, IndexError): If start or goal is out of bounds.
    """
    start_time = time.perf_counter()

    # Input type and boundary validation
    validate_search_inputs(grid, start, goal)

    algorithm_name = "A* Search"

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

    # Obtain minimum traversable movement cost from grid/terrain configuration
    if hasattr(grid, "get_min_traversable_cost"):
        min_cost = grid.get_min_traversable_cost()
    else:
        min_cost = TerrainCostConfig.get_min_traversable_cost()

    h_func = heuristic_func if heuristic_func is not None else manhattan_heuristic

    # Requirement 1: Initialize starting state's g-cost to zero
    g_score: Dict[Position, float] = {start: 0.0}
    parent: Dict[Position, Optional[Position]] = {start: None}

    # Tracking expanded states and expansion order
    closed_set: Set[Position] = set()
    visited_order: List[Position] = []
    found: bool = False

    # Requirement 2: Insert start state with priority f(start)
    entry_counter: int = 0
    h_start = h_func(start, goal, min_cost)
    f_start = 0.0 + h_start
    frontier: List[Tuple[float, float, int, Position]] = []
    heapq.heappush(frontier, (f_start, h_start, entry_counter, start))

    while frontier:
        # Requirement 3: Expand the state with the smallest f-value
        curr_f, curr_h, _, curr = heapq.heappop(frontier)
        curr_g = curr_f - curr_h

        # Requirement 8: Handle outdated priority-queue entries correctly
        if curr_g > g_score.get(curr, float("inf")):
            continue

        if curr in closed_set:
            continue
        closed_set.add(curr)
        visited_order.append(curr)

        # Requirement 9: Accept the goal only when removed from priority queue with best cost
        if curr == goal:
            found = True
            break

        # Requirement 4: Generate only valid traversable neighbours
        for neighbour in grid.get_walkable_neighbours(curr):
            step_cost = grid.get_movement_cost(neighbour)
            if not grid.is_walkable(neighbour) or math.isinf(step_cost):
                continue

            # Requirement 5: Calculate tentative g-cost using cost of entering neighbouring cell
            tentative_g = curr_g + step_cost

            # Requirement 6: Update parent and g-cost whenever a cheaper route is discovered
            if tentative_g < g_score.get(neighbour, float("inf")):
                g_score[neighbour] = tentative_g
                parent[neighbour] = curr

                # Handle improved paths to previously closed states (reopening support)
                if neighbour in closed_set:
                    closed_set.remove(neighbour)

                # Requirement 7: Calculate new f-value
                h_val = h_func(neighbour, goal, min_cost)
                f_val = tentative_g + h_val
                entry_counter += 1
                heapq.heappush(frontier, (f_val, h_val, entry_counter, neighbour))

    end_time = time.perf_counter()
    execution_time_ms = (end_time - start_time) * 1000.0

    if found:
        # Requirement 10: Reconstruct final route using existing shared utilities
        path = reconstruct_path(parent, start, goal)
        path_length = len(path) - 1
        total_cost: Optional[float] = g_score[goal]
        if total_cost is not None and isinstance(total_cost, float) and total_cost.is_integer():
            total_cost = int(total_cost)
    else:
        path = []
        path_length = 0
        total_cost = None

    # Requirement 11: Return existing SearchResult structure
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


class AStarSearch:
    """Class wrapper for A* Search algorithm execution."""

    @staticmethod
    def search(
        grid: Grid,
        start: Position,
        goal: Position,
        heuristic_func: Optional[Callable[[Position, Position, float], float]] = None,
    ) -> SearchResult:
        """Execute A* Search on the provided grid environment."""
        return astar(grid, start, goal, heuristic_func=heuristic_func)

    def __call__(
        self,
        grid: Grid,
        start: Position,
        goal: Position,
        heuristic_func: Optional[Callable[[Position, Position, float], float]] = None,
    ) -> SearchResult:
        """Allow instance callable execution."""
        return astar(grid, start, goal, heuristic_func=heuristic_func)
