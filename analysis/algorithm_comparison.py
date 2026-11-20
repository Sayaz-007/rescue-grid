"""
Unified AI Pathfinding Comparison Module for RescueGrid (Phase 9.1).

Integrates and benchmarks five discrete pathfinding algorithms under
identical environmental configurations:
1. Breadth-First Search (BFS) [Unweighted graph search baseline]
2. Depth-First Search (DFS) [Unweighted graph search baseline]
3. Uniform-Cost Search (UCS) [Cost-optimal weighted search]
4. A* Search (A*) [Heuristically guided cost-optimal weighted search]
5. Hill Climbing (HC) [Incomplete local search heuristic]

Architectural Note on Constraint Satisfaction Problems (CSP):
CSP multi-agent resource allocation is intentionally excluded from spatial
pathfinding comparisons. Pathfinding algorithms find 2D routes across a grid,
whereas CSP solves combinatorial resource assignment (matching available responders
and vehicles to simultaneous emergency incidents under capability and exclusivity
constraints).
"""

import os
import sys
import time
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Tuple, Union

# Ensure root directory is on Python search path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from environment.cell import TerrainCostConfig, TerrainType
from environment.grid import Grid
from models.position import Position
from algorithms.search_result import SearchResult
from algorithms.search_utils import (
    calculate_path_cost,
    is_valid_path,
    validate_search_inputs,
)
from algorithms.bfs import BreadthFirstSearch
from algorithms.dfs import DepthFirstSearch
from algorithms.ucs import UniformCostSearch
from algorithms.astar import AStarSearch
from algorithms.hill_climbing import HillClimbingSearch


@dataclass
class ComparisonRecord:
    """Encapsulates benchmark metrics for a single algorithm execution."""

    algorithm: str
    solution_found: bool
    execution_time_ms: float
    nodes_explored: int
    path_length: Optional[int]
    total_cost: Optional[Union[int, float]]
    search_cost: Optional[Union[int, float]] = None
    path: List[Position] = field(default_factory=list)
    search_result: Optional[SearchResult] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert metric record into a standardized dictionary representation."""
        cost_val = self.total_cost
        if isinstance(cost_val, float):
            cost_val = round(cost_val, 4)
        return {
            "algorithm": self.algorithm,
            "solution_found": self.solution_found,
            "execution_time_ms": round(self.execution_time_ms, 4),
            "nodes_explored": self.nodes_explored,
            "path_length": self.path_length,
            "total_cost": cost_val,
        }

    def summary(self) -> str:
        """Single-line summary string of algorithm performance."""
        status = "FOUND" if self.solution_found else "NOT FOUND"
        len_str = str(self.path_length) if self.path_length is not None else "None"
        cost_str = str(self.total_cost) if self.total_cost is not None else "None"
        return (
            f"[{self.algorithm}] {status} | "
            f"Time: {self.execution_time_ms:.4f} ms | "
            f"Explored: {self.nodes_explored} nodes | "
            f"Length: {len_str} steps | "
            f"Cost: {cost_str}"
        )


class ComparisonReport:
    """Structured report holding comparative benchmark records across algorithms."""

    def __init__(
        self,
        scenario_name: str,
        grid: Grid,
        start: Position,
        goal: Position,
        records: List[ComparisonRecord],
    ) -> None:
        self.scenario_name: str = scenario_name
        self.grid: Grid = grid
        self.start: Position = start
        self.goal: Position = goal
        self.records: List[ComparisonRecord] = list(records)

    def get_record(self, algorithm_name: str) -> Optional[ComparisonRecord]:
        """Retrieve record by algorithm name or prefix/alias (e.g. 'BFS', 'A*', 'UCS')."""
        name_lower = algorithm_name.strip().lower()
        alias_map = {
            "bfs": "breadth-first search",
            "dfs": "depth-first search",
            "ucs": "uniform-cost search",
            "astar": "a* search",
            "a*": "a* search",
            "hc": "hill climbing",
        }
        resolved = alias_map.get(name_lower, name_lower)

        for rec in self.records:
            if rec.algorithm.lower() == resolved or rec.algorithm.lower() == name_lower:
                return rec
        for rec in self.records:
            if resolved in rec.algorithm.lower() or name_lower in rec.algorithm.lower():
                return rec
        return None

    def __getitem__(self, key: Union[int, str]) -> ComparisonRecord:
        """Index access by integer index or algorithm name."""
        if isinstance(key, int):
            return self.records[key]
        rec = self.get_record(key)
        if rec is not None:
            return rec
        raise KeyError(f"No benchmark record found for algorithm '{key}'.")

    def __len__(self) -> int:
        return len(self.records)

    def __iter__(self):
        return iter(self.records)

    def to_dict(self) -> Dict[str, Any]:
        """Convert entire report into a structured dictionary."""
        return {
            "scenario_name": self.scenario_name,
            "start": str(self.start),
            "goal": str(self.goal),
            "grid_dimensions": f"{self.grid.cols}x{self.grid.rows}",
            "results": [rec.to_dict() for rec in self.records],
        }

    def to_table(self, markdown: bool = False) -> str:
        """Render performance metrics table matching Phase 9.1 specification.

        Columns:
        | Algorithm | Solution Found | Execution Time (ms) | Nodes Explored | Path Length | Total Cost |

        Args:
            markdown: If True, outputs GitHub-flavored Markdown. Otherwise, ASCII box format.
        """
        headers = [
            "Algorithm",
            "Solution Found",
            "Execution Time (ms)",
            "Nodes Explored",
            "Path Length",
            "Total Cost",
        ]

        rows: List[List[str]] = []
        for rec in self.records:
            sol_str = str(rec.solution_found)
            time_str = f"{rec.execution_time_ms:.4f}"
            nodes_str = str(rec.nodes_explored)
            len_str = str(rec.path_length) if rec.path_length is not None else "None"
            if rec.total_cost is None:
                cost_str = "None"
            elif isinstance(rec.total_cost, float):
                cost_str = f"{rec.total_cost:.1f}" if rec.total_cost.is_integer() else f"{rec.total_cost:.4f}"
            else:
                cost_str = str(rec.total_cost)

            rows.append([
                rec.algorithm,
                sol_str,
                time_str,
                nodes_str,
                len_str,
                cost_str,
            ])

        if markdown:
            col_aligns = [":---", ":---:", "---:", "---:", "---:", "---:"]
            lines = [
                "| " + " | ".join(headers) + " |",
                "| " + " | ".join(col_aligns) + " |",
            ]
            for row in rows:
                lines.append("| " + " | ".join(row) + " |")
            return "\n".join(lines)

        # ASCII Box Table
        col_widths = [len(h) for h in headers]
        for row in rows:
            for i, val in enumerate(row):
                col_widths[i] = max(col_widths[i], len(val))

        def make_separator(char: str = "-") -> str:
            return "+" + "+".join(char * (w + 2) for w in col_widths) + "+"

        header_line = "| " + " | ".join(h.ljust(col_widths[i]) for i, h in enumerate(headers)) + " |"

        body_lines: List[str] = []
        for row in rows:
            formatted_cells = [
                row[0].ljust(col_widths[0]),
                row[1].center(col_widths[1]),
                row[2].rjust(col_widths[2]),
                row[3].rjust(col_widths[3]),
                row[4].rjust(col_widths[4]),
                row[5].rjust(col_widths[5]),
            ]
            body_lines.append("| " + " | ".join(formatted_cells) + " |")

        sep = make_separator()
        table_lines = [sep, header_line, sep] + body_lines + [sep]
        return "\n".join(table_lines)

    def __str__(self) -> str:
        return self.to_table(markdown=False)


class ComparisonScenario:
    """Encapsulates a reproducible deterministic simulation scenario."""

    def __init__(
        self,
        name: str,
        description: str,
        grid: Grid,
        start: Position,
        goal: Position,
    ) -> None:
        self.name: str = name
        self.description: str = description
        self.grid: Grid = grid
        self.start: Position = start
        self.goal: Position = goal

    def run(self, algorithms: Optional[List[str]] = None) -> ComparisonReport:
        """Execute benchmark comparison on this scenario."""
        return compare_pathfinding_algorithms(
            grid=self.grid,
            start=self.start,
            goal=self.goal,
            algorithms=algorithms,
            scenario_name=self.name,
        )


# Mapping of supported pathfinding algorithms
_ALGORITHM_REGISTRY: Dict[str, Tuple[str, Any]] = {
    "bfs": ("Breadth-First Search", BreadthFirstSearch),
    "breadth_first": ("Breadth-First Search", BreadthFirstSearch),
    "breadth-first": ("Breadth-First Search", BreadthFirstSearch),
    "breadth-first search": ("Breadth-First Search", BreadthFirstSearch),
    "dfs": ("Depth-First Search", DepthFirstSearch),
    "depth_first": ("Depth-First Search", DepthFirstSearch),
    "depth-first": ("Depth-First Search", DepthFirstSearch),
    "depth-first search": ("Depth-First Search", DepthFirstSearch),
    "ucs": ("Uniform-Cost Search", UniformCostSearch),
    "uniform_cost": ("Uniform-Cost Search", UniformCostSearch),
    "uniform-cost": ("Uniform-Cost Search", UniformCostSearch),
    "uniform-cost search": ("Uniform-Cost Search", UniformCostSearch),
    "astar": ("A* Search", AStarSearch),
    "a*": ("A* Search", AStarSearch),
    "a_star": ("A* Search", AStarSearch),
    "a* search": ("A* Search", AStarSearch),
    "hill_climbing": ("Hill Climbing", HillClimbingSearch),
    "hill-climbing": ("Hill Climbing", HillClimbingSearch),
    "hill climbing": ("Hill Climbing", HillClimbingSearch),
    "hc": ("Hill Climbing", HillClimbingSearch),
}

_DEFAULT_ALGORITHM_KEYS = ["bfs", "dfs", "ucs", "astar", "hill_climbing"]


def compare_pathfinding_algorithms(
    grid: Grid,
    start: Position,
    goal: Position,
    algorithms: Optional[List[str]] = None,
    scenario_name: str = "Pathfinding Benchmark",
) -> ComparisonReport:
    """Execute each applicable pathfinding algorithm independently on the identical grid.

    All algorithms receive the exact same grid, start position, goal position,
    and terrain configuration without mutating the grid between runs.

    Args:
        grid: Simulation Grid environment.
        start: Starting dispatch Position.
        goal: Target destination Position.
        algorithms: Optional list of algorithm identifiers to run. Defaults to all 5:
                    ['bfs', 'dfs', 'ucs', 'astar', 'hill_climbing'].
        scenario_name: Identifier for the scenario being evaluated.

    Returns:
        Structured ComparisonReport containing individual ComparisonRecords.

    Raises:
        TypeError: If grid or positions are of incorrect types.
        PositionOutOfBoundsError: If start or goal is outside grid boundaries.
        ValueError: If an unknown algorithm identifier is provided, or if CSP is requested.
    """
    validate_search_inputs(grid, start, goal)

    # Resolve algorithm list
    selected_keys: List[str]
    if algorithms is None:
        selected_keys = list(_DEFAULT_ALGORITHM_KEYS)
    else:
        selected_keys = []
        for algo in algorithms:
            cleaned = algo.strip().lower()
            if cleaned == "csp" or "constraint" in cleaned:
                raise ValueError(
                    "CSP solves multi-agent resource allocation, not spatial grid pathfinding. "
                    "It cannot be compared directly in grid pathfinding benchmarks."
                )
            if cleaned not in _ALGORITHM_REGISTRY:
                raise ValueError(
                    f"Unknown algorithm identifier '{algo}'. Supported: "
                    f"['bfs', 'dfs', 'ucs', 'astar', 'hill_climbing']."
                )
            selected_keys.append(cleaned)

    # Snapshot grid state to verify immutability
    grid_snapshot = [
        (c, r, grid.get_cell(Position(c, r)).terrain, grid.is_walkable(Position(c, r)), grid.get_movement_cost(Position(c, r)))
        for r in range(grid.rows)
        for c in range(grid.cols)
    ]

    records: List[ComparisonRecord] = []

    for key in selected_keys:
        algo_name, handler = _ALGORITHM_REGISTRY[key]
        search_fn = getattr(handler, "search", handler)

        # High-resolution wall-clock timer
        t_start = time.perf_counter()
        try:
            search_result = search_fn(grid, start, goal)
        finally:
            t_elapsed_ms = (time.perf_counter() - t_start) * 1000.0

            # Verify grid remains completely unmutated even if search encounters an error
            current_state = [
                (c, r, grid.get_cell(Position(c, r)).terrain, grid.is_walkable(Position(c, r)), grid.get_movement_cost(Position(c, r)))
                for r in range(grid.rows)
                for c in range(grid.cols)
            ]
            if current_state != grid_snapshot:
                raise RuntimeError(f"Algorithm '{algo_name}' mutated the grid state during execution!")

        # Process metrics
        solution_found = bool(search_result.found)
        nodes_explored = int(search_result.nodes_explored)

        if solution_found:
            path_len: Optional[int] = search_result.path_length
            # Calculate true weighted movement cost of discovered path on the grid
            evaluated_cost = calculate_path_cost(grid, search_result.path)
            if isinstance(evaluated_cost, float) and evaluated_cost.is_integer():
                total_cost: Optional[Union[int, float]] = int(evaluated_cost)
            else:
                total_cost = evaluated_cost
        else:
            path_len = None
            total_cost = None

        record = ComparisonRecord(
            algorithm=search_result.algorithm_name,
            solution_found=solution_found,
            execution_time_ms=t_elapsed_ms,
            nodes_explored=nodes_explored,
            path_length=path_len,
            total_cost=total_cost,
            search_cost=search_result.total_cost,
            path=list(search_result.path),
            search_result=search_result,
        )
        records.append(record)

    return ComparisonReport(
        scenario_name=scenario_name,
        grid=grid,
        start=start,
        goal=goal,
        records=records,
    )


class PathfindingComparator:
    """Unified comparator engine providing static and programmatic benchmark APIs."""

    @classmethod
    def compare(
        cls,
        grid: Grid,
        start: Position,
        goal: Position,
        algorithms: Optional[List[str]] = None,
        scenario_name: str = "Pathfinding Benchmark",
    ) -> ComparisonReport:
        """Execute pathfinding comparison on the supplied grid and coordinates."""
        return compare_pathfinding_algorithms(
            grid=grid,
            start=start,
            goal=goal,
            algorithms=algorithms,
            scenario_name=scenario_name,
        )

    @classmethod
    def run_scenario(
        cls,
        scenario: ComparisonScenario,
        algorithms: Optional[List[str]] = None,
    ) -> ComparisonReport:
        """Run benchmark on a ComparisonScenario."""
        return scenario.run(algorithms=algorithms)

    @classmethod
    def run_all_standard_scenarios(
        cls,
        algorithms: Optional[List[str]] = None,
    ) -> Dict[str, ComparisonReport]:
        """Execute benchmarks across all four standard scenarios."""
        scenarios = get_standard_scenarios()
        return {key: sc.run(algorithms=algorithms) for key, sc in scenarios.items()}


# =============================================================================
# STANDARD DETERMINISTIC SCENARIO GENERATORS
# =============================================================================

def create_scenario_a_open(rows: int = 10, cols: int = 10) -> ComparisonScenario:
    """Scenario A: Open Grid.

    A simple 10x10 grid without obstacles or difficult terrain.
    Purpose: Compare baseline search behavior on unobstructed uniform terrain.
    """
    grid = Grid(rows=rows, cols=cols, default_terrain=TerrainType.NORMAL)
    start = Position(0, 0)
    goal = Position(cols - 1, rows - 1)
    return ComparisonScenario(
        name="Scenario A: Open Grid",
        description="Unobstructed 10x10 uniform normal terrain comparing baseline search behaviors.",
        grid=grid,
        start=start,
        goal=goal,
    )


def create_scenario_b_obstacles(rows: int = 10, cols: int = 10) -> ComparisonScenario:
    """Scenario B: Obstacle-Dense Grid.

    A 10x10 grid containing multiple rubble, water, and fire obstacles.
    Purpose: Evaluate how algorithms navigate multi-bend detours when direct
    routes are blocked, and demonstrate local-search entrapment in Hill Climbing.
    """
    grid = Grid(rows=rows, cols=cols, default_terrain=TerrainType.NORMAL)

    # 1. Vertical collapsed building rubble barrier blocking direct x=3 line
    for y in range(0, 7):
        grid.add_collapsed_building(Position(3, y))

    # 2. Vertical flood water zone blocking eastern line at x=6
    for y in range(3, 10):
        grid.add_flood_zone(Position(6, y))

    # 3. Active fire zone hazards in the central traversal corridor
    grid.add_fire_zone(Position(4, 8))
    grid.add_fire_zone(Position(5, 8))

    start = Position(0, 0)
    goal = Position(cols - 1, rows - 1)

    return ComparisonScenario(
        name="Scenario B: Obstacle-Dense Grid",
        description="Complex 10x10 hazard zone with rubble, flood, and fire barriers forcing multi-bend detours.",
        grid=grid,
        start=start,
        goal=goal,
    )


def create_scenario_c_weighted(rows: int = 7, cols: int = 12) -> ComparisonScenario:
    """Scenario C: Weighted Terrain Grid.

    A 7x12 grid containing roads, normal terrain, and rough terrain.
    Purpose: Demonstrate why UCS and A* find cheaper routes than BFS by selecting
    a longer road bypass (cost 1) over a shorter rough corridor (cost 4).
    """
    grid = Grid(rows=rows, cols=cols, default_terrain=TerrainType.NORMAL)

    # 1. Paved highway arterial along row 1 (Movement cost = 1)
    for x in range(10):
        grid.add_road(Position(x, 1))
    grid.add_road(Position(0, 2))  # Access road from start row
    grid.add_road(Position(9, 2))  # Egress road to goal row

    # 2. Damaged rough terrain corridor along row 3 (Movement cost = 4)
    for x in range(1, 9):
        grid.add_rough_terrain(Position(x, 3))

    # 3. Structural rubble hazards south of corridor
    grid.add_collapsed_building(Position(3, 4))
    grid.add_collapsed_building(Position(4, 4))
    grid.add_collapsed_building(Position(5, 4))

    start = Position(0, 3)
    goal = Position(9, 3)

    return ComparisonScenario(
        name="Scenario C: Weighted Terrain Grid",
        description="7x12 grid contrasting a direct expensive rough corridor against a longer cheap road bypass.",
        grid=grid,
        start=start,
        goal=goal,
    )


def create_scenario_d_no_solution(rows: int = 8, cols: int = 8) -> ComparisonScenario:
    """Scenario D: No-Solution Grid.

    An 8x8 grid where the goal is completely partitioned from start by hazard obstacles.
    Purpose: Verify that all algorithms terminate gracefully and report failure without crashing.
    """
    grid = Grid(rows=rows, cols=cols, default_terrain=TerrainType.NORMAL)

    # Continuous vertical barrier completely bisecting the grid along column 4
    for y in range(rows):
        if y % 3 == 0:
            grid.add_collapsed_building(Position(4, y))
        elif y % 3 == 1:
            grid.add_flood_zone(Position(4, y))
        else:
            grid.add_fire_zone(Position(4, y))

    start = Position(0, 0)
    goal = Position(cols - 1, rows - 1)

    return ComparisonScenario(
        name="Scenario D: No-Solution Grid",
        description="8x8 disaster grid with complete barrier partition verifying graceful search failure reporting.",
        grid=grid,
        start=start,
        goal=goal,
    )


def get_standard_scenarios() -> Dict[str, ComparisonScenario]:
    """Retrieve mapping of all four reproducible benchmark scenarios."""
    return {
        "scenario_a": create_scenario_a_open(),
        "scenario_b": create_scenario_b_obstacles(),
        "scenario_c": create_scenario_c_weighted(),
        "scenario_d": create_scenario_d_no_solution(),
    }


if __name__ == "__main__":
    print("=" * 80)
    print("RescueGrid — Unified Pathfinding Algorithm Benchmark Suite (Phase 9.1)")
    print("=" * 80)

    scenarios = get_standard_scenarios()
    for sc_key, scenario in scenarios.items():
        print(f"\nEvaluating {scenario.name}...")
        report = scenario.run()
        print(report.to_table(markdown=False))
