"""
Utility functions and validation helpers for AI search algorithms in RescueGrid.
"""

from typing import Dict, List, Optional, Any, Set
from models.position import Position
from environment.grid import Grid


class PositionOutOfBoundsError(ValueError, IndexError):
    """Raised when a start or goal position lies outside bounded grid dimensions."""
    pass


def validate_search_inputs(grid: Any, start: Any, goal: Any) -> None:
    """Validate that grid, start, and goal inputs conform to expected types and bounds.

    Args:
        grid: Instance of Grid.
        start: Instance of Position.
        goal: Instance of Position.

    Raises:
        TypeError: If grid is not a Grid, or start/goal is not a Position.
        PositionOutOfBoundsError (ValueError, IndexError): If start or goal lies
            outside bounded grid coordinates.
    """
    if not isinstance(grid, Grid):
        raise TypeError(f"Grid must be an instance of Grid, got {type(grid).__name__}.")
    if not isinstance(start, Position):
        raise TypeError(f"Start coordinate must be an instance of Position, got {type(start).__name__}.")
    if not isinstance(goal, Position):
        raise TypeError(f"Goal coordinate must be an instance of Position, got {type(goal).__name__}.")

    if not grid.is_inside(start):
        raise PositionOutOfBoundsError(
            f"Start position {start} is outside grid boundaries [cols={grid.cols}, rows={grid.rows}]."
        )
    if not grid.is_inside(goal):
        raise PositionOutOfBoundsError(
            f"Goal position {goal} is outside grid boundaries [cols={grid.cols}, rows={grid.rows}]."
        )


def reconstruct_path(
    parent: Dict[Position, Optional[Position]],
    start: Position,
    goal: Position,
) -> List[Position]:
    """Reconstruct sequential path from start to goal using parent pointers.

    Args:
        parent: Dictionary mapping child Position to predecessor Position.
        start: Starting Position.
        goal: Target destination Position.

    Returns:
        Ordered list of Positions from start to goal inclusive, or empty list
        if goal cannot be traced back to start.
    """
    if goal not in parent:
        return []

    path: List[Position] = []
    curr: Optional[Position] = goal

    while curr is not None:
        path.append(curr)
        curr = parent.get(curr)

    path.reverse()

    if path and path[0] == start and path[-1] == goal:
        return path
    return []


def is_valid_path(
    grid: Grid,
    path: List[Position],
    start: Position,
    goal: Position,
) -> bool:
    """Verify that a path constitutes a valid, unbroken cardinal route across walkable cells.

    Args:
        grid: Simulation Grid environment.
        path: Ordered list of Positions representing the traversed route.
        start: Expected start Position.
        goal: Expected goal Position.

    Returns:
        True if the path is valid, contiguous, and non-blocked; False otherwise.
    """
    if not path:
        return False
    if path[0] != start or path[-1] != goal:
        return False

    for i, pos in enumerate(path):
        if not grid.is_inside(pos):
            return False
        if not grid.is_walkable(pos):
            return False
        if i > 0:
            prev = path[i - 1]
            manhattan = abs(pos.x - prev.x) + abs(pos.y - prev.y)
            if manhattan != 1:
                return False

    return True


def manhattan_distance(pos1: Position, pos2: Position) -> int:
    """Calculate the L1 Manhattan distance between two discrete 2D grid coordinates.

    Args:
        pos1: First Position.
        pos2: Second Position.

    Returns:
        Integer Manhattan distance |x1 - x2| + |y1 - y2|.
    """
    return abs(pos1.x - pos2.x) + abs(pos1.y - pos2.y)


def manhattan_heuristic(
    pos: Position,
    goal: Position,
    min_cost: float = 1.0,
) -> float:
    """Calculate the cost-scaled Manhattan distance heuristic for A* pathfinding.

    Formula:
        h(n) = Manhattan(n, goal) * min_traversable_movement_cost

    Admissibility:
        In a 4-connected discrete grid, any valid route from current cell n to goal
        requires at least Manhattan(n, goal) orthogonal steps. Since all traversable
        terrains incur an entering cost c >= min_cost > 0, the true minimum cost
        to reach the goal h*(n) satisfies:
            h*(n) >= Manhattan(n, goal) * min_cost = h(n)
        Because h(n) <= h*(n) for all valid states, the heuristic is strictly admissible
        and will never overestimate the actual remaining movement cost.

    Consistency (Monotonicity):
        For any single cardinal transition from n to an adjacent cell n':
            |Manhattan(n, goal) - Manhattan(n', goal)| <= 1
        Scaling by min_cost:
            |h(n) - h(n')| <= 1 * min_cost <= c(n, n')
        Therefore, h(n) <= c(n, n') + h(n'), satisfying the triangle inequality.
        Consistency guarantees that whenever a node is expanded in A*, its g-cost
        is already optimal.

    Args:
        pos: Current Position n.
        goal: Target destination Position.
        min_cost: Minimum movement cost among traversable terrain types (default: 1.0).

    Returns:
        Non-negative float heuristic estimate h(n).
    """
    return float(manhattan_distance(pos, goal) * min_cost)


def calculate_path_cost(grid: Grid, path: List[Position]) -> float:
    """Calculate total accumulated movement cost along a path according to RescueGrid convention.

    Convention:
        The starting cell (path[0]) is not charged.
        The cost of entering a cell is its movement cost.
        Total cost = cost(path[1]) + cost(path[2]) + ... + cost(path[-1]).
        Empty paths or paths containing only the start position have cost 0.0.

    Args:
        grid: Simulation Grid providing cell movement costs.
        path: Sequential list of Positions in the route.

    Returns:
        Accumulated movement cost as a float.
    """
    if not path or len(path) <= 1:
        return 0.0
    return sum(grid.get_movement_cost(pos) for pos in path[1:])


def render_grid_with_path(
    grid: Grid,
    path: Optional[List[Position]] = None,
    start: Optional[Position] = None,
    goal: Optional[Position] = None,
) -> str:
    """Render an ASCII visualization of the grid with route overlay without mutating the grid.

    Symbols:
        'S': Starting position
        'G': Goal / Incident position
        '*': Intermediate path step
        '.': Normal walkable cell (cost = 2)
        '=': Road cell (cost = 1)
        ':': Rough terrain cell (cost = 4)
        '#': General obstacle (impassable)
        'X': Rubble / Collapsed building (impassable)
        'W': Deep flood water (impassable)
        'F': Active fire zone (impassable)

    Args:
        grid: 2D Grid environment.
        path: Optional list of Positions in the route.
        start: Optional start Position (defaults to path[0] if path provided).
        goal: Optional goal Position (defaults to path[-1] if path provided).

    Returns:
        Formatted multi-line ASCII grid string.
    """
    path_set: Set[Position] = set(path) if path else set()
    s_pos = start if start is not None else (path[0] if path else None)
    g_pos = goal if goal is not None else (path[-1] if path else None)

    lines: List[str] = []
    col_header = "    " + " ".join(f"{c % 10}" for c in range(grid.cols))
    lines.append(col_header)
    lines.append("    " + "-" * (grid.cols * 2 - 1))

    for r in range(grid.rows):
        row_symbols: List[str] = []
        for c in range(grid.cols):
            pos = Position(c, r)
            if s_pos is not None and pos == s_pos:
                row_symbols.append("S")
            elif g_pos is not None and pos == g_pos:
                row_symbols.append("G")
            elif pos in path_set:
                row_symbols.append("*")
            else:
                row_symbols.append(grid.get_cell(pos).get_symbol())
        lines.append(f"{r:2d} | " + " ".join(row_symbols))

    return "\n".join(lines)
