"""
Comprehensive unit test suite for Hill Climbing Search in RescueGrid (Phase 7).
Verifies Steepest-Ascent local search, Manhattan heuristic minimization,
tie-breaking rules, cycle prevention, local optima traps, weighted terrain
sub-optimality, KnowledgeGrid compatibility, and metric contracts.
"""

import os
import sys
import unittest

# Ensure root workspace directory is on module search path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from models.position import Position
from environment.cell import Cell, TerrainType, TerrainCostConfig
from environment.grid import Grid
from environment.actual_grid import ActualGrid
from environment.knowledge_grid import KnowledgeGrid
from algorithms.search_result import SearchResult
from algorithms.search_utils import (
    validate_search_inputs,
    is_valid_path,
    calculate_path_cost,
    manhattan_distance,
    PositionOutOfBoundsError,
)
from algorithms.astar import astar
from algorithms.hill_climbing import hill_climbing, HillClimbingSearch


class TestHillClimbingInputValidation(unittest.TestCase):
    """Test Suite 1: Input type validation and grid boundary enforcement."""

    def setUp(self) -> None:
        self.grid = Grid(rows=5, cols=5)
        self.start = Position(0, 0)
        self.goal = Position(4, 4)

    def test_invalid_grid_types(self) -> None:
        """Reject non-Grid types with TypeError."""
        for bad_grid in [None, "grid", 123, [1, 2], True]:
            with self.assertRaises(TypeError):
                hill_climbing(bad_grid, self.start, self.goal)  # type: ignore

    def test_invalid_position_types(self) -> None:
        """Reject non-Position start and goal types with TypeError."""
        for bad_pos in [None, (0, 0), "0,0", 123, False]:
            with self.assertRaises(TypeError):
                hill_climbing(self.grid, bad_pos, self.goal)  # type: ignore
            with self.assertRaises(TypeError):
                hill_climbing(self.grid, self.start, bad_pos)  # type: ignore

    def test_out_of_bounds_positions(self) -> None:
        """Reject out-of-bounds start and goal coordinates."""
        out_positions = [Position(-1, 0), Position(0, -1), Position(5, 0), Position(0, 5)]
        for bad_pos in out_positions:
            with self.assertRaises(PositionOutOfBoundsError):
                hill_climbing(self.grid, bad_pos, self.goal)
            with self.assertRaises(PositionOutOfBoundsError):
                hill_climbing(self.grid, self.start, bad_pos)


class TestHillClimbingBasicFunctionality(unittest.TestCase):
    """Test Suite 2: Basic route finding, path validity, and cost calculation."""

    def setUp(self) -> None:
        self.grid = Grid(rows=6, cols=6, default_terrain=TerrainType.NORMAL)

    def test_reaches_goal_on_open_grid(self) -> None:
        """Hill Climbing reaches goal on an open, unobstructed grid."""
        start = Position(0, 0)
        goal = Position(4, 3)
        res = hill_climbing(self.grid, start, goal)

        self.assertTrue(res.found)
        self.assertEqual(res.start_position, start)
        self.assertEqual(res.goal_position, goal)
        self.assertTrue(is_valid_path(self.grid, res.path, start, goal))
        self.assertEqual(res.path[0], start)
        self.assertEqual(res.path[-1], goal)
        self.assertEqual(res.path_length, len(res.path) - 1)
        # Manhattan distance is 4 + 3 = 7 steps
        self.assertEqual(res.path_length, 7)

    def test_start_equals_goal_trivial_case(self) -> None:
        """When start == goal on a walkable cell, return zero-step path [start]."""
        pos = Position(2, 2)
        res = hill_climbing(self.grid, pos, pos)

        self.assertTrue(res.found)
        self.assertEqual(res.path, [pos])
        self.assertEqual(res.path_length, 0)
        self.assertEqual(res.total_cost, 0.0)
        self.assertEqual(res.nodes_explored, 1)

    def test_movement_cost_start_cell_uncharged(self) -> None:
        """Verify that starting cell is not charged in total_cost."""
        start = Position(0, 0)
        goal = Position(2, 0)
        res = hill_climbing(self.grid, start, goal)

        self.assertTrue(res.found)
        # Path: (0,0) -> (1,0) -> (2,0). NORMAL cost = 2.0 per entered cell. Total = 4.0
        self.assertEqual(res.total_cost, 4.0)

    def test_search_result_metadata(self) -> None:
        """Validate SearchResult metadata fields and execution time."""
        res = hill_climbing(self.grid, Position(0, 0), Position(2, 2))
        self.assertEqual(res.algorithm_name, "Hill Climbing")
        self.assertGreater(res.execution_time_ms, 0.0)
        self.assertEqual(res.nodes_explored, len(res.visited_order))


class TestHillClimbingObstaclesAndBoundaries(unittest.TestCase):
    """Test Suite 3: Blocked endpoints, hazards, boundaries, and cycle avoidance."""

    def setUp(self) -> None:
        self.grid = Grid(rows=5, cols=5, default_terrain=TerrainType.NORMAL)

    def test_blocked_start_position(self) -> None:
        """Starting cell with obstacle or blocked terrain fails immediately."""
        self.grid.add_collapsed_building(0, 0)
        res = hill_climbing(self.grid, Position(0, 0), Position(4, 4))
        self.assertFalse(res.found)
        self.assertEqual(res.path, [])
        self.assertIsNone(res.total_cost)

    def test_blocked_goal_position(self) -> None:
        """Goal cell with obstacle or blocked terrain fails immediately."""
        self.grid.add_flood_zone(4, 4)
        res = hill_climbing(self.grid, Position(0, 0), Position(4, 4))
        self.assertFalse(res.found)
        self.assertEqual(res.path, [])
        self.assertIsNone(res.total_cost)

    def test_does_not_traverse_blocked_cells(self) -> None:
        """Hill Climbing path never contains blocked or obstacle cells."""
        self.grid.add_road(0, 0)
        self.grid.add_road(1, 0)
        self.grid.add_collapsed_building(2, 0)
        self.grid.add_road(3, 0)
        self.grid.add_road(4, 0)
        # Force a path that can succeed by stepping down
        self.grid.add_road(1, 1)
        self.grid.add_road(2, 1)
        self.grid.add_road(3, 1)

        res = hill_climbing(self.grid, Position(0, 0), Position(4, 0))
        # If it found a path or failed, it must NEVER step on (2, 0)
        self.assertNotIn(Position(2, 0), res.path)
        self.assertNotIn(Position(2, 0), res.visited_order)

    def test_does_not_revisit_positions(self) -> None:
        """Hill Climbing avoids cycles: strictly decreasing heuristic guarantees positions are never revisited."""
        res = hill_climbing(self.grid, Position(0, 0), Position(3, 3))
        if res.found:
            self.assertEqual(len(res.path), len(set(res.path)))
        self.assertEqual(len(res.visited_order), len(set(res.visited_order)))

    def test_unreachable_goal_surrounded_by_obstacles(self) -> None:
        """Destination enclosed by obstacles must return found=False and empty path."""
        # Enclose goal (4, 4) with rubble at (3, 4) and (4, 3)
        self.grid.add_collapsed_building(3, 4)
        self.grid.add_collapsed_building(4, 3)

        res = hill_climbing(self.grid, Position(0, 0), Position(4, 4))
        self.assertFalse(res.found)
        self.assertEqual(res.path, [])
        self.assertIsNone(res.total_cost)

    def test_does_not_move_outside_grid_boundaries(self) -> None:
        """Hill Climbing stays strictly inside grid boundaries at corners and edges."""
        start = Position(0, 0)
        goal = Position(0, 4)
        res = hill_climbing(self.grid, start, goal)
        self.assertTrue(res.found)
        for p in res.path:
            self.assertTrue(self.grid.is_inside(p))
            self.assertGreaterEqual(p.x, 0)
            self.assertLess(p.x, self.grid.cols)
            self.assertGreaterEqual(p.y, 0)
            self.assertLess(p.y, self.grid.rows)


class TestHillClimbingLocalOptimaAndLimitations(unittest.TestCase):
    """Test Suite 4: Demonstrating genuine failure modes and lack of backtracking."""

    def test_local_optimum_wall_barrier(self) -> None:
        """Demonstrate trapping at a local optimum when reaching goal requires moving away.

        Grid layout (5 cols x 5 rows):
        Start: (0, 2), Goal: (4, 2).
        A vertical barrier wall blocks column 2 from row 0 to row 4:
        (2, 0), (2, 1), (2, 2), (2, 3), (2, 4) are all blocked!
        At (1, 2), distance is |1-4| + |2-2| = 3.
        Neighbours are (1, 1) [d=4], (1, 3) [d=4], and (0, 2) [visited].
        None strictly improves upon d=3.
        Hill Climbing MUST terminate unsuccessfully at (1, 2) without backtracking!
        """
        grid = Grid(rows=5, cols=5, default_terrain=TerrainType.NORMAL)
        for r in range(5):
            grid.add_collapsed_building(2, r)

        start = Position(0, 2)
        goal = Position(4, 2)

        hc_res = hill_climbing(grid, start, goal)
        self.assertFalse(hc_res.found)
        self.assertEqual(hc_res.path, [])
        self.assertIsNone(hc_res.total_cost)
        # It visited (0, 2) and (1, 2) before getting stuck
        self.assertEqual(hc_res.visited_order, [Position(0, 2), Position(1, 2)])

    def test_local_optimum_u_shaped_trap(self) -> None:
        """Demonstrate trapping inside a U-shaped obstacle pocket.

        Start is placed inside a pocket opening to the West.
        Goal is to the East.
        Moving out of the pocket requires moving West (increasing Manhattan distance).
        Hill Climbing refuses to move away from goal and fails.
        In contrast, A* successfully escapes the pocket and reaches the goal.
        """
        grid = Grid(rows=7, cols=7, default_terrain=TerrainType.NORMAL)
        # U-shaped cup facing West:
        # Top wall: (2, 2), (3, 2), (4, 2)
        # Back wall: (4, 2), (4, 3), (4, 4)
        # Bottom wall: (2, 4), (3, 4), (4, 4)
        for c in [2, 3, 4]:
            grid.add_collapsed_building(c, 2)
            grid.add_collapsed_building(c, 4)
        grid.add_collapsed_building(4, 3)

        start = Position(3, 3)  # inside the trap
        goal = Position(6, 3)   # behind the back wall

        # Hill Climbing gets trapped immediately
        hc_res = hill_climbing(grid, start, goal)
        self.assertFalse(hc_res.found)
        self.assertEqual(hc_res.path, [])

        # A* systematically escapes and reaches the goal
        astar_res = astar(grid, start, goal)
        self.assertTrue(astar_res.found)
        self.assertGreater(len(astar_res.path), 0)

    def test_refusal_to_backtrack(self) -> None:
        """Confirms Hill Climbing does not backtrack when reaching a dead end."""
        grid = Grid(rows=3, cols=3, default_terrain=TerrainType.NORMAL)
        # Block (1, 0), (2, 1), (1, 2)
        grid.add_collapsed_building(1, 0)
        grid.add_collapsed_building(2, 1)
        grid.add_collapsed_building(1, 2)

        start = Position(0, 1)
        goal = Position(2, 2)

        res = hill_climbing(grid, start, goal)
        # From (0, 1), best move is (1, 1).
        # At (1, 1), all neighbours towards goal are blocked; (0, 1) is visited.
        # It must report failure without backtracking to other starts or paths.
        self.assertFalse(res.found)
        self.assertEqual(res.path, [])


class TestHillClimbingWeightedTerrainSuboptimality(unittest.TestCase):
    """Test Suite 5: Cost calculation and demonstrating sub-optimality under weighted terrain."""

    def test_hill_climbing_chooses_heuristic_over_cost_optimality(self) -> None:
        """Hill Climbing chooses a high-cost direct path over a low-cost detour.

        Layout:
        Start: (0, 1), Goal: (2, 1).
        - Direct route through (1, 1) has terrain ROUGH (cost 4.0).
        - Detour through row 0 [(0, 0), (1, 0), (2, 0)] has terrain ROAD (cost 1.0).
        At (0, 1):
        - (1, 1) has Manhattan distance |1 - 2| + |1 - 1| = 1.
        - (0, 0) has Manhattan distance |0 - 2| + |0 - 1| = 3.
        Hill Climbing strictly minimizes heuristic, so it picks (1, 1) despite higher cost!
        """
        grid = Grid(rows=3, cols=3, default_terrain=TerrainType.NORMAL)
        # Direct path is ROUGH
        grid.add_rough_terrain(1, 1)
        grid.add_normal_terrain = lambda x, y: None  # goal is NORMAL (cost 2)
        # Detour is ROAD
        grid.add_road(0, 0)
        grid.add_road(1, 0)
        grid.add_road(2, 0)

        start = Position(0, 1)
        goal = Position(2, 1)

        hc_res = hill_climbing(grid, start, goal)
        astar_res = astar(grid, start, goal)

        self.assertTrue(hc_res.found)
        self.assertTrue(astar_res.found)

        # Hill climbing takes direct rough route: cost = 4.0 (rough) + 2.0 (normal goal) = 6.0
        self.assertEqual(hc_res.total_cost, 6.0)
        self.assertEqual(hc_res.path, [Position(0, 1), Position(1, 1), Position(2, 1)])

        # A* takes the cheaper road bypass: cost = 1.0 + 1.0 + 1.0 + 2.0 = 5.0
        self.assertEqual(astar_res.total_cost, 5.0)
        self.assertLess(astar_res.total_cost, hc_res.total_cost)

    def test_tie_breaking_by_movement_cost(self) -> None:
        """When two neighbours have equal heuristic, prefer lower movement cost."""
        grid = Grid(rows=3, cols=3, default_terrain=TerrainType.NORMAL)
        start = Position(0, 0)
        goal = Position(2, 2)

        # From (0, 0), neighbours are (0, 1) [DOWN] and (1, 0) [RIGHT].
        # Both have Manhattan distance to (2, 2) = |x-2| + |y-2| = 1 + 2 = 3.
        # Make (1, 0) a ROAD (cost 1.0) and (0, 1) ROUGH (cost 4.0).
        grid.add_road(1, 0)
        grid.add_rough_terrain(0, 1)

        res = hill_climbing(grid, start, goal)
        self.assertTrue(res.found)
        # First step from start should be (1, 0) due to lower cost tie-breaker
        self.assertEqual(res.path[1], Position(1, 0))


class TestHillClimbingKnowledgeGridCompatibility(unittest.TestCase):
    """Test Suite 6: Partial observability and KnowledgeGrid integration."""

    def test_cannot_traverse_unknown_cells(self) -> None:
        """Hill Climbing treats UNKNOWN cells as non-walkable and refuses traversal."""
        k_grid = KnowledgeGrid(rows=4, cols=4, default_terrain=TerrainType.UNKNOWN)
        start = Position(0, 0)
        goal = Position(3, 3)

        res = hill_climbing(k_grid, start, goal)
        self.assertFalse(res.found)
        self.assertEqual(res.path, [])

    def test_succeeds_on_revealed_corridor_in_knowledge_grid(self) -> None:
        """Hill Climbing succeeds on KnowledgeGrid when a direct corridor is revealed."""
        actual = ActualGrid(rows=4, cols=4, default_terrain=TerrainType.NORMAL)
        knowledge = actual.create_knowledge_grid(default_terrain=TerrainType.UNKNOWN)

        # Reveal a straight direct corridor from (0, 0) to (3, 0)
        for c in range(4):
            knowledge.reveal_cell(Position(c, 0), actual)

        res = hill_climbing(knowledge, Position(0, 0), Position(3, 0))
        self.assertTrue(res.found)
        self.assertEqual(res.path_length, 3)
        self.assertEqual(res.path, [Position(0, 0), Position(1, 0), Position(2, 0), Position(3, 0)])

    def test_does_not_inspect_actual_grid(self) -> None:
        """Hill Climbing operates strictly on the supplied KnowledgeGrid."""
        actual = ActualGrid(rows=4, cols=4)
        actual.add_road(1, 0)  # road exists in reality
        knowledge = actual.create_knowledge_grid()  # but is unknown to knowledge grid

        # Reveal only start
        knowledge.reveal_cell(Position(0, 0), actual)

        res = hill_climbing(knowledge, Position(0, 0), Position(3, 0))
        # Cannot see the road in actual grid; fails because (1, 0) is UNKNOWN
        self.assertFalse(res.found)


class TestHillClimbingClassWrapperAndDeterminism(unittest.TestCase):
    """Test Suite 7: Class wrapper methods and deterministic execution."""

    def setUp(self) -> None:
        self.grid = Grid(rows=5, cols=5, default_terrain=TerrainType.NORMAL)
        self.start = Position(0, 0)
        self.goal = Position(3, 3)

    def test_class_wrapper_static_method(self) -> None:
        """HillClimbingSearch.search static method returns identical result to function."""
        res_fn = hill_climbing(self.grid, self.start, self.goal)
        res_cls = HillClimbingSearch.search(self.grid, self.start, self.goal)

        self.assertEqual(res_fn.found, res_cls.found)
        self.assertEqual(res_fn.path, res_cls.path)
        self.assertEqual(res_fn.total_cost, res_cls.total_cost)

    def test_class_wrapper_instance_callable(self) -> None:
        """HillClimbingSearch instance call returns identical result."""
        searcher = HillClimbingSearch()
        res_call = searcher(self.grid, self.start, self.goal)
        res_fn = hill_climbing(self.grid, self.start, self.goal)

        self.assertEqual(res_call.found, res_fn.found)
        self.assertEqual(res_call.path, res_fn.path)

    def test_determinism(self) -> None:
        """Repeated runs on identical grid yield identical trajectories."""
        res1 = hill_climbing(self.grid, self.start, self.goal)
        res2 = hill_climbing(self.grid, self.start, self.goal)

        self.assertEqual(res1.found, res2.found)
        self.assertEqual(res1.path, res2.path)
        self.assertEqual(res1.visited_order, res2.visited_order)
        self.assertEqual(res1.total_cost, res2.total_cost)


if __name__ == "__main__":
    unittest.main()
