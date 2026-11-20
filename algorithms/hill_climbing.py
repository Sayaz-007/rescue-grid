"""
Hill Climbing local search algorithm for RescueGrid (Phase 7).
Implements deterministic Steepest-Ascent Hill Climbing minimizing Manhattan distance.
Demonstrates local optimization and genuine failure modes (local optima / plateaus)
without backtracking or global frontier queues.
"""

import time
from typing import Callable, List, Optional, Tuple, Union
from models.position import Position
from environment.grid import Grid
from algorithms.search_result import SearchResult
from algorithms.search_utils import (
    validate_search_inputs,
    calculate_path_cost,
    manhattan_distance,
    PositionOutOfBoundsError,
)


def hill_climbing(
    grid: Grid,
    start: Position,
    goal: Position,
    heuristic_func: Optional[Callable[[Position, Position], Union[int, float]]] = None,
    max_iterations: Optional[int] = None,
) -> SearchResult:
    """Execute deterministic Steepest-Ascent Hill Climbing minimizing heuristic distance.

    Algorithmic Characteristics:
    - Pure local-search strategy: maintains solely the current state, without a priority
      queue or global search frontier.
    - Memory Complexity: O(1) auxiliary search memory, excluding the storage required
      for the returned path and exploration metrics.
    - Steepest Ascent (descent on cost/heuristic): Evaluates all immediate walkable
      cardinal neighbours and chooses the neighbour that minimizes Manhattan distance
      to the goal.
    - Deterministic Tie-Breaking:
      1. Primary: Lowest heuristic value h(n).
      2. Secondary: Lowest movement cost of entering candidate cell.
      3. Tertiary: Cardinal neighbour generation order (UP, DOWN, LEFT, RIGHT).
    - Strict Improvement Invariant: Moves to candidate neighbour only if it strictly
      improves upon the current state's heuristic (h(next) < h(current)).
    - Cycle Avoidance: Because the heuristic must strictly decrease at every step,
      revisiting an earlier position is mathematically impossible (earlier states
      have strictly higher heuristics), eliminating the need for an auxiliary visited set.
    - Termination Conditions:
      1. Goal reached (success).
      2. No walkable neighbours exist (dead end).
      3. No neighbour strictly improves the heuristic (local optimum / plateau).
      4. Maximum iteration limit reached.
    - No Backtracking: If trapped in a local optimum, the search terminates with failure;
      it does not exhaustively backtrack or convert into another search algorithm.

    Args:
        grid: Simulation Grid (or KnowledgeGrid) environment.
        start: Starting Position of the rescue vehicle.
        goal: Target destination Position (disaster incident scene).
        heuristic_func: Optional custom heuristic function (pos, goal) -> number.
            Defaults to L1 Manhattan distance.
        max_iterations: Optional safeguard limit on maximum iterations. Defaults
            to 2 * total grid cells.

    Returns:
        SearchResult containing path, metrics, and execution timing.

    Raises:
        TypeError: If grid is not Grid, or start/goal is not Position.
        PositionOutOfBoundsError (ValueError, IndexError): If start or goal is out of bounds.
    """
    start_time = time.perf_counter()

    # Input type and boundary validation
    validate_search_inputs(grid, start, goal)

    algorithm_name = "Hill Climbing"

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

    # Handle trivial case: start equals goal
    if start == goal:
        end_time = time.perf_counter()
        return SearchResult(
            algorithm_name=algorithm_name,
            start_position=start,
            goal_position=goal,
            found=True,
            path=[start],
            visited_order=[start],
            nodes_explored=1,
            path_length=0,
            total_cost=0.0,
            execution_time_ms=(end_time - start_time) * 1000.0,
        )

    h_func = heuristic_func if heuristic_func is not None else manhattan_distance

    # Safeguard iteration boundary
    limit = max_iterations if max_iterations is not None else (grid.rows * grid.cols * 2)
    if limit < 1:
        limit = 1

    current = start
    path: List[Position] = [current]
    visited_order: List[Position] = [current]
    found: bool = False
    iterations: int = 0

    while current != goal and iterations < limit:
        # 1. Obtain current cell's valid, walkable cardinal neighbours
        neighbours = grid.get_neighbours(current, walkable_only=True)
        if not neighbours:
            # Dead end: no walkable adjacent cells
            break

        current_h = h_func(current, goal)

        # 2, 3, 4. Select candidate neighbour minimizing heuristic, tie-breaking by movement cost, then cardinal order
        # Python's min is stable, preserving cardinal neighbour order (UP, DOWN, LEFT, RIGHT) on ties
        best_neighbour = min(
            neighbours,
            key=lambda n: (h_func(n, goal), grid.get_cell(n).movement_cost)
        )
        best_h = h_func(best_neighbour, goal)

        # 5. Move to selected neighbour only if it strictly improves the heuristic.
        # Because h(next) < h(current) is strictly enforced, revisiting an earlier position
        # is mathematically impossible, ensuring O(1) auxiliary search memory without a visited set.
        if best_h >= current_h:
            # Local optimum / plateau: no strictly improving neighbour exists
            break

        # Move to selected neighbour
        current = best_neighbour
        path.append(current)
        visited_order.append(current)
        iterations += 1

        if current == goal:
            found = True
            break

    end_time = time.perf_counter()
    execution_time_ms = (end_time - start_time) * 1000.0

    if found:
        path_length = len(path) - 1
        total_cost = calculate_path_cost(grid, path)
        return SearchResult(
            algorithm_name=algorithm_name,
            start_position=start,
            goal_position=goal,
            found=True,
            path=path,
            visited_order=visited_order,
            nodes_explored=len(visited_order),
            path_length=path_length,
            total_cost=total_cost,
            execution_time_ms=execution_time_ms,
        )
    else:
        return SearchResult(
            algorithm_name=algorithm_name,
            start_position=start,
            goal_position=goal,
            found=False,
            path=[],
            visited_order=visited_order,
            nodes_explored=len(visited_order),
            path_length=0,
            total_cost=None,
            execution_time_ms=execution_time_ms,
        )


class HillClimbingSearch:
    """Class wrapper for Hill Climbing local search execution."""

    @staticmethod
    def search(
        grid: Grid,
        start: Position,
        goal: Position,
        heuristic_func: Optional[Callable[[Position, Position], Union[int, float]]] = None,
        max_iterations: Optional[int] = None,
    ) -> SearchResult:
        """Execute Hill Climbing search on the provided grid environment."""
        return hill_climbing(
            grid,
            start,
            goal,
            heuristic_func=heuristic_func,
            max_iterations=max_iterations,
        )

    def __call__(
        self,
        grid: Grid,
        start: Position,
        goal: Position,
        heuristic_func: Optional[Callable[[Position, Position], Union[int, float]]] = None,
        max_iterations: Optional[int] = None,
    ) -> SearchResult:
        """Allow instance callable execution."""
        return hill_climbing(
            grid,
            start,
            goal,
            heuristic_func=heuristic_func,
            max_iterations=max_iterations,
        )
