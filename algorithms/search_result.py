"""
SearchResult data model for AI search and pathfinding in RescueGrid.
Encapsulates route discovery state, paths, exploration order, and performance metrics.
"""

from typing import List, Optional, Union, Dict, Any
from models.position import Position


class SearchResult:
    """Encapsulates the outcome and performance metrics of a pathfinding search.

    Standardized metric conventions across all search algorithms:
    - For successful routes:
        path_length = len(path) - 1
        total_cost = cumulative movement cost (weighted for UCS, uniform path_length for BFS/DFS)
    - For unsuccessful searches:
        found = False
        path = []
        path_length = 0
        total_cost = None
    """

    def __init__(
        self,
        algorithm_name: str,
        start_position: Position,
        goal_position: Position,
        found: bool,
        path: Optional[List[Position]] = None,
        visited_order: Optional[List[Position]] = None,
        nodes_explored: int = 0,
        path_length: Optional[int] = None,
        total_cost: Optional[Union[int, float]] = None,
        execution_time_ms: float = 0.0,
    ) -> None:
        """Initialize search result with route details and performance metrics.

        Args:
            algorithm_name: Identifier of the search algorithm (e.g. 'Uniform-Cost Search').
            start_position: Starting Position of the rescue vehicle.
            goal_position: Target destination Position.
            found: Boolean flag indicating if a valid path to goal was discovered.
            path: Sequential list of Positions from start to goal (inclusive).
            visited_order: Order in which positions were explored/expanded during search.
            nodes_explored: Total count of nodes expanded/visited during search.
            path_length: Number of movement steps in the path (len(path) - 1).
            total_cost: Total accumulated path traversal cost (None for unsuccessful search).
            execution_time_ms: Wall-clock execution time in milliseconds.
        """
        self.algorithm_name: str = algorithm_name
        self.start_position: Position = start_position
        self.goal_position: Position = goal_position
        self.found: bool = found
        self.visited_order: List[Position] = list(visited_order) if visited_order is not None else []

        if nodes_explored > 0:
            self.nodes_explored: int = nodes_explored
        else:
            self.nodes_explored = len(self.visited_order)

        if not self.found:
            self.path: List[Position] = []
            self.path_length: int = 0
            self.total_cost: Optional[Union[int, float]] = None
        else:
            self.path = list(path) if path is not None else []
            if path_length is not None:
                self.path_length = path_length
            else:
                self.path_length = (len(self.path) - 1) if len(self.path) > 0 else 0

            if total_cost is not None:
                self.total_cost = total_cost
            else:
                self.total_cost = self.path_length

        self.execution_time_ms: float = float(execution_time_ms)

    def to_dict(self) -> Dict[str, Any]:
        """Convert search result metrics into a dictionary representation."""
        return {
            "algorithm_name": self.algorithm_name,
            "start_position": str(self.start_position),
            "goal_position": str(self.goal_position),
            "found": self.found,
            "path": [str(pos) for pos in self.path],
            "visited_order": [str(pos) for pos in self.visited_order],
            "nodes_explored": self.nodes_explored,
            "path_length": self.path_length,
            "total_cost": self.total_cost,
            "execution_time_ms": round(self.execution_time_ms, 4),
        }

    def summary(self) -> str:
        """Return a formatted single-line summary of search performance."""
        status = "SUCCESS" if self.found else "FAILURE"
        cost_str = "None" if self.total_cost is None else (
            f"{self.total_cost:.4f}" if isinstance(self.total_cost, float) else str(self.total_cost)
        )
        return (
            f"[{self.algorithm_name}] {status} | "
            f"Start: {self.start_position} -> Goal: {self.goal_position} | "
            f"Path Length: {self.path_length} | Total Cost: {cost_str} | "
            f"Nodes Explored: {self.nodes_explored} | Time: {self.execution_time_ms:.4f} ms"
        )

    def __str__(self) -> str:
        return self.summary()

    def __repr__(self) -> str:
        cost_repr = repr(self.total_cost)
        return (
            f"SearchResult(algorithm_name={self.algorithm_name!r}, "
            f"start_position={self.start_position!r}, "
            f"goal_position={self.goal_position!r}, "
            f"found={self.found!r}, "
            f"path_length={self.path_length!r}, "
            f"total_cost={cost_repr}, "
            f"nodes_explored={self.nodes_explored!r}, "
            f"execution_time_ms={self.execution_time_ms:.4f})"
        )
