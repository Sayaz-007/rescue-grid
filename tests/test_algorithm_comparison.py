"""
Comprehensive Unit Tests for Algorithm Integration & Performance Benchmark (Phase 9.1).

Validates:
1. Unified multi-algorithm pathfinding benchmark execution (BFS, DFS, UCS, A*, Hill Climbing).
2. Result collection, data models, table rendering, and dictionary serialization.
3. Four deterministic standard scenarios (Open, Obstacle-Dense, Weighted Terrain, No-Solution).
4. Fair comparison invariants: grid immutability, identical environment states across runs.
5. Path cost consistency and verification that UCS/A* discover cheaper paths than BFS.
6. Graceful failure handling and proper representation of Hill Climbing entrapment.
7. Rejection of invalid inputs, unknown algorithms, and CSP misuse.
"""

import unittest
from unittest.mock import patch, MagicMock
from typing import Dict, List, Optional

from environment.cell import TerrainType, TerrainCostConfig
from environment.grid import Grid
from models.position import Position
from algorithms.search_utils import (
    PositionOutOfBoundsError,
    calculate_path_cost,
    is_valid_path,
    manhattan_distance,
)
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


class TestComparisonExecution(unittest.TestCase):
    """Test Suite 1: Algorithm invocation, registry resolution, and execution controls."""

    def setUp(self) -> None:
        self.grid = Grid(rows=6, cols=6, default_terrain=TerrainType.NORMAL)
        self.start = Position(0, 0)
        self.goal = Position(5, 5)

    def test_default_all_five_algorithms_executed(self) -> None:
        """Benchmark executes all five pathfinding algorithms in standard order by default."""
        report = compare_pathfinding_algorithms(self.grid, self.start, self.goal)
        self.assertEqual(len(report), 5)

        expected_names = [
            "Breadth-First Search",
            "Depth-First Search",
            "Uniform-Cost Search",
            "A* Search",
            "Hill Climbing",
        ]
        actual_names = [rec.algorithm for rec in report]
        self.assertEqual(actual_names, expected_names)

    def test_custom_algorithm_subset(self) -> None:
        """Benchmark can execute a specific requested subset of algorithms."""
        report = compare_pathfinding_algorithms(
            self.grid, self.start, self.goal, algorithms=["bfs", "astar"]
        )
        self.assertEqual(len(report), 2)
        self.assertEqual(report[0].algorithm, "Breadth-First Search")
        self.assertEqual(report[1].algorithm, "A* Search")

    def test_case_insensitive_and_alias_algorithm_names(self) -> None:
        """Algorithm identifiers support aliases and mixed case ('BFS', 'UCS', 'a*', 'HC')."""
        report = compare_pathfinding_algorithms(
            self.grid, self.start, self.goal, algorithms=["BFS", "UCS", "a*", "HC", "dfs"]
        )
        self.assertEqual(len(report), 5)
        self.assertEqual(report[0].algorithm, "Breadth-First Search")
        self.assertEqual(report[1].algorithm, "Uniform-Cost Search")
        self.assertEqual(report[2].algorithm, "A* Search")
        self.assertEqual(report[3].algorithm, "Hill Climbing")
        self.assertEqual(report[4].algorithm, "Depth-First Search")

    def test_unknown_algorithm_rejected(self) -> None:
        """Specifying an unknown algorithm name raises ValueError."""
        with self.assertRaises(ValueError):
            compare_pathfinding_algorithms(
                self.grid, self.start, self.goal, algorithms=["bfs", "dijkstra_unknown"]
            )

    def test_csp_rejected_with_explanatory_error(self) -> None:
        """Requesting CSP pathfinding raises ValueError explaining problem domain separation."""
        with self.assertRaises(ValueError) as ctx:
            compare_pathfinding_algorithms(
                self.grid, self.start, self.goal, algorithms=["bfs", "csp"]
            )
        self.assertIn("CSP solves multi-agent resource allocation", str(ctx.exception))


class TestResultCollectionAndDataModel(unittest.TestCase):
    """Test Suite 2: Data structures, metric contracts, indexing, and serializations."""

    def setUp(self) -> None:
        self.grid = Grid(rows=5, cols=5, default_terrain=TerrainType.NORMAL)
        self.start = Position(0, 0)
        self.goal = Position(4, 4)

    def test_record_attributes_populated(self) -> None:
        """ComparisonRecord populates all required metrics conforming to Phase 9.1."""
        report = compare_pathfinding_algorithms(self.grid, self.start, self.goal, algorithms=["bfs"])
        rec: ComparisonRecord = report[0]

        self.assertEqual(rec.algorithm, "Breadth-First Search")
        self.assertTrue(rec.solution_found)
        self.assertIsInstance(rec.execution_time_ms, float)
        self.assertGreater(rec.execution_time_ms, 0.0)
        self.assertIsInstance(rec.nodes_explored, int)
        self.assertGreater(rec.nodes_explored, 0)
        self.assertEqual(rec.path_length, 8)
        self.assertEqual(rec.total_cost, 16)  # 8 steps * 2 cost
        self.assertIsNotNone(rec.search_result)
        self.assertEqual(len(rec.path), 9)

    def test_record_to_dict(self) -> None:
        """ComparisonRecord.to_dict() outputs exact metric dictionary format."""
        report = compare_pathfinding_algorithms(self.grid, self.start, self.goal, algorithms=["ucs"])
        rec = report[0]
        data = rec.to_dict()

        expected_keys = {
            "algorithm",
            "solution_found",
            "execution_time_ms",
            "nodes_explored",
            "path_length",
            "total_cost",
        }
        self.assertEqual(set(data.keys()), expected_keys)
        self.assertEqual(data["algorithm"], "Uniform-Cost Search")
        self.assertTrue(data["solution_found"])
        self.assertEqual(data["path_length"], 8)
        self.assertEqual(data["total_cost"], 16)

    def test_record_summary_format(self) -> None:
        """ComparisonRecord.summary() returns single-line human-readable string."""
        report = compare_pathfinding_algorithms(self.grid, self.start, self.goal, algorithms=["astar"])
        rec = report[0]
        summary_str = rec.summary()
        self.assertIn("[A* Search]", summary_str)
        self.assertIn("FOUND", summary_str)
        self.assertIn("Length: 8 steps", summary_str)
        self.assertIn("Cost: 16", summary_str)

    def test_report_indexing_and_lookup(self) -> None:
        """ComparisonReport supports integer index, full name lookup, and alias lookup."""
        report = compare_pathfinding_algorithms(self.grid, self.start, self.goal)

        # Integer indexing
        self.assertEqual(report[0].algorithm, "Breadth-First Search")
        self.assertEqual(report[3].algorithm, "A* Search")

        # Exact name lookup
        self.assertEqual(report["Breadth-First Search"].algorithm, "Breadth-First Search")
        self.assertEqual(report["Uniform-Cost Search"].algorithm, "Uniform-Cost Search")

        # Alias lookup
        self.assertEqual(report["BFS"].algorithm, "Breadth-First Search")
        self.assertEqual(report["dfs"].algorithm, "Depth-First Search")
        self.assertEqual(report["ucs"].algorithm, "Uniform-Cost Search")
        self.assertEqual(report["a*"].algorithm, "A* Search")
        self.assertEqual(report["astar"].algorithm, "A* Search")
        self.assertEqual(report["hc"].algorithm, "Hill Climbing")

    def test_report_missing_key_raises_key_error(self) -> None:
        """Looking up a non-existent algorithm in ComparisonReport raises KeyError."""
        report = compare_pathfinding_algorithms(self.grid, self.start, self.goal, algorithms=["bfs"])
        with self.assertRaises(KeyError):
            _ = report["NonExistentAlgorithm"]

    def test_report_iteration_and_len(self) -> None:
        """ComparisonReport implements sequence protocol (__len__, __iter__)."""
        report = compare_pathfinding_algorithms(self.grid, self.start, self.goal)
        self.assertEqual(len(report), 5)
        names = [r.algorithm for r in report]
        self.assertEqual(len(names), 5)

    def test_report_to_dict(self) -> None:
        """ComparisonReport.to_dict() provides structured scenario dictionary."""
        report = compare_pathfinding_algorithms(
            self.grid, self.start, self.goal, scenario_name="Custom Benchmark"
        )
        data = report.to_dict()

        self.assertEqual(data["scenario_name"], "Custom Benchmark")
        self.assertEqual(data["start"], "(0, 0)")
        self.assertEqual(data["goal"], "(4, 4)")
        self.assertEqual(data["grid_dimensions"], "5x5")
        self.assertEqual(len(data["results"]), 5)

    def test_report_to_table_ascii(self) -> None:
        """ComparisonReport.to_table() renders ASCII box table matching required columns."""
        report = compare_pathfinding_algorithms(self.grid, self.start, self.goal)
        table_str = report.to_table(markdown=False)

        # Check column headers
        self.assertIn("Algorithm", table_str)
        self.assertIn("Solution Found", table_str)
        self.assertIn("Execution Time (ms)", table_str)
        self.assertIn("Nodes Explored", table_str)
        self.assertIn("Path Length", table_str)
        self.assertIn("Total Cost", table_str)

        # Check all algorithm rows present
        self.assertIn("Breadth-First Search", table_str)
        self.assertIn("Depth-First Search", table_str)
        self.assertIn("Uniform-Cost Search", table_str)
        self.assertIn("A* Search", table_str)
        self.assertIn("Hill Climbing", table_str)

    def test_report_to_table_markdown(self) -> None:
        """ComparisonReport.to_table(markdown=True) renders valid GitHub-flavored Markdown table."""
        report = compare_pathfinding_algorithms(self.grid, self.start, self.goal)
        md_str = report.to_table(markdown=True)

        lines = md_str.strip().split("\n")
        self.assertGreaterEqual(len(lines), 7)  # Header, aligner, 5 rows
        self.assertTrue(lines[0].startswith("| Algorithm |"))
        self.assertTrue(lines[1].startswith("| :--- |"))
        self.assertIn("Breadth-First Search", md_str)


class TestStandardScenarios(unittest.TestCase):
    """Test Suite 3: Validation of the four standard reproducible scenarios."""

    def test_scenario_a_open_grid(self) -> None:
        """Scenario A (Open Grid): Unobstructed search behavior."""
        scenario = create_scenario_a_open()
        self.assertEqual(scenario.grid.cols, 10)
        self.assertEqual(scenario.grid.rows, 10)

        report = scenario.run()
        self.assertEqual(len(report), 5)

        # All algorithms must find a valid path
        for rec in report:
            self.assertTrue(rec.solution_found, f"{rec.algorithm} should find path on open grid.")
            self.assertIsNotNone(rec.path_length)
            self.assertIsNotNone(rec.total_cost)

        # BFS, UCS, A*, and Hill Climbing discover the 18-step optimal Manhattan route
        self.assertEqual(report["BFS"].path_length, 18)
        self.assertEqual(report["UCS"].path_length, 18)
        self.assertEqual(report["A*"].path_length, 18)
        self.assertEqual(report["HC"].path_length, 18)

        # Cost: 18 steps on NORMAL terrain (cost 2 each) = 36
        self.assertEqual(report["BFS"].total_cost, 36)
        self.assertEqual(report["UCS"].total_cost, 36)
        self.assertEqual(report["A*"].total_cost, 36)
        self.assertEqual(report["HC"].total_cost, 36)

        # Hill Climbing descends monotonically in 19 node expansions
        self.assertEqual(report["HC"].nodes_explored, 19)

    def test_scenario_b_obstacle_dense_grid(self) -> None:
        """Scenario B (Obstacle-Dense): Multi-hazard detour navigation and HC entrapment."""
        scenario = create_scenario_b_obstacles()
        report = scenario.run()

        # Systematic graph searches find the 28-step detour route
        bfs_rec = report["BFS"]
        ucs_rec = report["UCS"]
        astar_rec = report["A*"]
        dfs_rec = report["DFS"]

        self.assertTrue(bfs_rec.solution_found)
        self.assertTrue(ucs_rec.solution_found)
        self.assertTrue(astar_rec.solution_found)
        self.assertTrue(dfs_rec.solution_found)

        self.assertEqual(bfs_rec.path_length, 28)
        self.assertEqual(ucs_rec.path_length, 28)
        self.assertEqual(astar_rec.path_length, 28)

        # Local search (Hill Climbing) gets trapped at the rubble wall and fails gracefully
        hc_rec = report["HC"]
        self.assertFalse(hc_rec.solution_found)
        self.assertIsNone(hc_rec.path_length)
        self.assertIsNone(hc_rec.total_cost)
        self.assertEqual(len(hc_rec.path), 0)
        self.assertGreater(hc_rec.nodes_explored, 0)

    def test_scenario_c_weighted_terrain_grid(self) -> None:
        """Scenario C (Weighted Terrain): Proves why UCS and A* find cheaper paths than BFS."""
        scenario = create_scenario_c_weighted()
        report = scenario.run()

        bfs_rec = report["BFS"]
        ucs_rec = report["UCS"]
        astar_rec = report["A*"]
        hc_rec = report["HC"]

        self.assertTrue(bfs_rec.solution_found)
        self.assertTrue(ucs_rec.solution_found)
        self.assertTrue(astar_rec.solution_found)
        self.assertTrue(hc_rec.solution_found)

        # BFS chooses shortest step count (direct rough path: 9 steps)
        self.assertEqual(bfs_rec.path_length, 9)
        self.assertEqual(bfs_rec.total_cost, 34)  # 8 rough (4*8=32) + 1 normal (2) = 34

        # UCS and A* select the longer 13-step road bypass to minimize cost
        self.assertEqual(ucs_rec.path_length, 13)
        self.assertEqual(astar_rec.path_length, 13)
        self.assertEqual(ucs_rec.total_cost, 14)
        self.assertEqual(astar_rec.total_cost, 14)

        # CRITICAL VALIDATION: UCS and A* paths are strictly cheaper than BFS
        self.assertLess(ucs_rec.total_cost, bfs_rec.total_cost)
        self.assertLess(astar_rec.total_cost, bfs_rec.total_cost)

        # CRITICAL VALIDATION: A* expands significantly fewer nodes than blind UCS
        self.assertLess(astar_rec.nodes_explored, ucs_rec.nodes_explored)
        self.assertEqual(astar_rec.nodes_explored, 19)
        self.assertEqual(ucs_rec.nodes_explored, 53)

        # Hill Climbing is blind to movement costs; it takes the expensive 9-step path
        self.assertEqual(hc_rec.path_length, 9)
        self.assertEqual(hc_rec.total_cost, 34)

    def test_scenario_d_no_solution_grid(self) -> None:
        """Scenario D (No-Solution): Walled-off goal reports graceful failure across all algorithms."""
        scenario = create_scenario_d_no_solution()
        report = scenario.run()

        for rec in report:
            self.assertFalse(rec.solution_found, f"{rec.algorithm} must report found=False on partitioned grid.")
            self.assertIsNone(rec.path_length, f"{rec.algorithm} path_length must be None.")
            self.assertIsNone(rec.total_cost, f"{rec.algorithm} total_cost must be None.")
            self.assertEqual(len(rec.path), 0, f"{rec.algorithm} path must be empty.")
            self.assertGreater(rec.nodes_explored, 0)


class TestGridImmutabilityAndWalkability(unittest.TestCase):
    """Test Suite 4: Grid state preservation, walkability, and route validity."""

    def test_grid_unchanged_after_comparison(self) -> None:
        """Grid cells, terrains, costs, and walkability remain identical before and after comparison."""
        scenario = create_scenario_c_weighted()
        grid = scenario.grid

        # Snapshot before
        before_state = [
            (
                c,
                r,
                grid.get_cell(Position(c, r)).terrain,
                grid.is_walkable(Position(c, r)),
                grid.get_movement_cost(Position(c, r)),
            )
            for r in range(grid.rows)
            for c in range(grid.cols)
        ]

        # Execute comparison across all five algorithms
        scenario.run()

        # Snapshot after
        after_state = [
            (
                c,
                r,
                grid.get_cell(Position(c, r)).terrain,
                grid.is_walkable(Position(c, r)),
                grid.get_movement_cost(Position(c, r)),
            )
            for r in range(grid.rows)
            for c in range(grid.cols)
        ]

        self.assertEqual(before_state, after_state)

    def test_discovered_paths_strictly_walkable_and_cardinal(self) -> None:
        """Discovered routes never traverse impassable hazard cells and maintain cardinal connectivity."""
        for sc_factory in [create_scenario_a_open, create_scenario_b_obstacles, create_scenario_c_weighted]:
            scenario = sc_factory()
            report = scenario.run()

            for rec in report:
                if rec.solution_found:
                    self.assertTrue(
                        is_valid_path(scenario.grid, rec.path, scenario.start, scenario.goal),
                        f"Path for {rec.algorithm} in {scenario.name} must be valid and continuous.",
                    )

    def test_consistency_of_reported_path_costs(self) -> None:
        """Reported total_cost matches calculate_path_cost exactly for all discovered paths."""
        scenario = create_scenario_c_weighted()
        report = scenario.run()

        for rec in report:
            if rec.solution_found:
                evaluated = calculate_path_cost(scenario.grid, rec.path)
                self.assertEqual(rec.total_cost, evaluated)


class TestDeterministicScenarioGeneration(unittest.TestCase):
    """Test Suite 5: Scenario generator determinism and catalog integrity."""

    def test_deterministic_reproducibility(self) -> None:
        """Repeated invocations of scenario generators yield identical grid topologies and results."""
        sc1 = create_scenario_c_weighted()
        sc2 = create_scenario_c_weighted()

        self.assertEqual(sc1.grid.to_string(), sc2.grid.to_string())
        self.assertEqual(sc1.start, sc2.start)
        self.assertEqual(sc1.goal, sc2.goal)

        rep1 = sc1.run(algorithms=["bfs", "ucs", "astar"])
        rep2 = sc2.run(algorithms=["bfs", "ucs", "astar"])

        for r1, r2 in zip(rep1, rep2):
            self.assertEqual(r1.algorithm, r2.algorithm)
            self.assertEqual(r1.solution_found, r2.solution_found)
            self.assertEqual(r1.path_length, r2.path_length)
            self.assertEqual(r1.total_cost, r2.total_cost)
            self.assertEqual(r1.nodes_explored, r2.nodes_explored)
            self.assertEqual(r1.path, r2.path)

    def test_get_standard_scenarios_keys(self) -> None:
        """get_standard_scenarios returns four standard scenario instances."""
        scenarios = get_standard_scenarios()
        expected_keys = {"scenario_a", "scenario_b", "scenario_c", "scenario_d"}
        self.assertEqual(set(scenarios.keys()), expected_keys)


class TestEdgeCasesAndValidation(unittest.TestCase):
    """Test Suite 6: Input validation, boundary checks, and comparator static APIs."""

    def test_invalid_grid_type(self) -> None:
        """Non-Grid input raises TypeError."""
        with self.assertRaises(TypeError):
            compare_pathfinding_algorithms("not_a_grid", Position(0, 0), Position(1, 1))

    def test_invalid_position_types(self) -> None:
        """Non-Position inputs raise TypeError."""
        grid = Grid(rows=4, cols=4)
        with self.assertRaises(TypeError):
            compare_pathfinding_algorithms(grid, (0, 0), Position(1, 1))
        with self.assertRaises(TypeError):
            compare_pathfinding_algorithms(grid, Position(0, 0), (1, 1))

    def test_out_of_bounds_positions(self) -> None:
        """Out-of-bounds start or goal coordinates raise PositionOutOfBoundsError."""
        grid = Grid(rows=5, cols=5)
        with self.assertRaises(PositionOutOfBoundsError):
            compare_pathfinding_algorithms(grid, Position(-1, 0), Position(2, 2))
        with self.assertRaises(PositionOutOfBoundsError):
            compare_pathfinding_algorithms(grid, Position(0, 0), Position(5, 5))

    def test_start_equals_goal_walkable(self) -> None:
        """When start == goal on a walkable cell, all algorithms return 0 steps and cost 0."""
        grid = Grid(rows=4, cols=4, default_terrain=TerrainType.NORMAL)
        pos = Position(1, 1)

        report = compare_pathfinding_algorithms(grid, pos, pos)
        for rec in report:
            self.assertTrue(rec.solution_found)
            self.assertEqual(rec.path_length, 0)
            self.assertEqual(rec.total_cost, 0)
            self.assertEqual(rec.path, [pos])

    def test_start_equals_goal_blocked(self) -> None:
        """When start == goal on a blocked hazard cell, all algorithms report failure."""
        grid = Grid(rows=4, cols=4)
        pos = Position(1, 1)
        grid.add_collapsed_building(pos)

        report = compare_pathfinding_algorithms(grid, pos, pos)
        for rec in report:
            self.assertFalse(rec.solution_found)
            self.assertIsNone(rec.path_length)
            self.assertIsNone(rec.total_cost)
            self.assertEqual(rec.path, [])

    def test_comparator_class_methods(self) -> None:
        """PathfindingComparator class methods work identically to standalone functions."""
        grid = Grid(rows=4, cols=4)
        s, g = Position(0, 0), Position(3, 3)

        rep1 = PathfindingComparator.compare(grid, s, g, algorithms=["bfs"])
        self.assertEqual(len(rep1), 1)

        sc = create_scenario_a_open(4, 4)
        rep2 = PathfindingComparator.run_scenario(sc, algorithms=["ucs"])
        self.assertEqual(len(rep2), 1)

        all_reports = PathfindingComparator.run_all_standard_scenarios(algorithms=["astar"])
        self.assertEqual(len(all_reports), 4)


class TestExceptionHandlingAndFailureReporting(unittest.TestCase):
    """Test Suite 7: Distinction between legitimate search failure and unexpected errors."""

    def setUp(self) -> None:
        self.grid = Grid(rows=5, cols=5, default_terrain=TerrainType.NORMAL)
        self.start = Position(0, 0)
        self.goal = Position(4, 4)

    def test_normal_unreachable_destination_reported_as_unsuccessful(self) -> None:
        """Legitimate unreachable destination returns normal unsuccessful SearchResult without exceptions."""
        grid = Grid(rows=5, cols=5, default_terrain=TerrainType.NORMAL)
        # Wall off destination completely
        for y in range(5):
            grid.add_collapsed_building(Position(3, y))

        report = compare_pathfinding_algorithms(grid, self.start, self.goal)
        self.assertEqual(len(report), 5)

        for rec in report:
            self.assertFalse(rec.solution_found)
            self.assertIsNone(rec.path_length)
            self.assertIsNone(rec.total_cost)
            self.assertEqual(rec.path, [])
            self.assertIsNotNone(rec.search_result)
            self.assertFalse(rec.search_result.found)
            self.assertEqual(rec.search_result.path, [])

    def test_unexpected_exception_from_search_function_propagates(self) -> None:
        """Unexpected programming exception in a search algorithm is not suppressed into found=False."""
        from algorithms.bfs import BreadthFirstSearch

        with patch.object(BreadthFirstSearch, "search", side_effect=ZeroDivisionError("Unexpected algorithm bug")):
            with self.assertRaises(ZeroDivisionError) as ctx:
                compare_pathfinding_algorithms(self.grid, self.start, self.goal, algorithms=["bfs"])
            self.assertIn("Unexpected algorithm bug", str(ctx.exception))

    def test_unexpected_exception_halts_benchmark_and_remains_visible(self) -> None:
        """Unexpected error during multi-algorithm benchmark propagates immediately to caller."""
        from algorithms.astar import AStarSearch

        with patch.object(AStarSearch, "search", side_effect=RuntimeError("A* priority queue corrupted")):
            with self.assertRaises(RuntimeError) as ctx:
                compare_pathfinding_algorithms(
                    self.grid, self.start, self.goal, algorithms=["bfs", "astar", "ucs"]
                )
            self.assertIn("A* priority queue corrupted", str(ctx.exception))

    def test_other_algorithms_and_normal_benchmarks_unaffected(self) -> None:
        """Normal execution across all algorithms and standard scenarios remains completely unaffected."""
        scenarios = get_standard_scenarios()
        for name, sc in scenarios.items():
            report = sc.run()
            self.assertEqual(len(report), 5)
            # Scenario D is legitimate failure, Scenarios A and C are legitimate success
            if name == "scenario_d":
                self.assertFalse(report["BFS"].solution_found)
            elif name in ("scenario_a", "scenario_c"):
                self.assertTrue(report["BFS"].solution_found)

    def test_grid_immutability_enforced_when_algorithm_mutates_grid(self) -> None:
        """When an algorithm illegitimately mutates the grid, RuntimeError is raised."""
        from algorithms.bfs import BreadthFirstSearch
        from algorithms.search_result import SearchResult

        def rogue_search(grid, start, goal):
            # Mutate grid state illegitimately
            grid.add_collapsed_building(Position(1, 1))
            return SearchResult("Breadth-First Search", start, goal, True, [start, goal])

        with patch.object(BreadthFirstSearch, "search", side_effect=rogue_search):
            with self.assertRaises(RuntimeError) as ctx:
                compare_pathfinding_algorithms(self.grid, self.start, self.goal, algorithms=["bfs"])
            self.assertIn("mutated the grid state during execution", str(ctx.exception))

    def test_grid_immutability_checked_even_when_algorithm_raises_exception(self) -> None:
        """If an algorithm mutates the grid and then raises an exception, the mutation is detected."""
        from algorithms.bfs import BreadthFirstSearch

        def crashing_and_mutating_search(grid, start, goal):
            grid.add_collapsed_building(Position(2, 2))
            raise ValueError("Bug inside search")

        with patch.object(BreadthFirstSearch, "search", side_effect=crashing_and_mutating_search):
            with self.assertRaises(RuntimeError) as ctx:
                compare_pathfinding_algorithms(self.grid, self.start, self.goal, algorithms=["bfs"])
            self.assertIn("mutated the grid state during execution", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
