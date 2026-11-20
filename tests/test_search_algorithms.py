"""
Comprehensive unit test suite for AI search algorithms in RescueGrid.
Verifies Breadth-First Search (BFS), Depth-First Search (DFS), SearchResult,
input validation, boundary safety, detours, and failure handling.
"""

import os
import sys
import unittest

# Ensure root workspace directory is on module search path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from models.position import Position
from environment.cell import Cell, TerrainType
from environment.grid import Grid
from algorithms.search_result import SearchResult
from algorithms.search_utils import (
    validate_search_inputs,
    reconstruct_path,
    is_valid_path,
    render_grid_with_path,
    PositionOutOfBoundsError,
)
from algorithms.bfs import bfs, BreadthFirstSearch
from algorithms.dfs import dfs, DepthFirstSearch


class TestInputValidation(unittest.TestCase):
    """Test Suite 1: Input type validation and grid boundary enforcement."""

    def setUp(self) -> None:
        self.grid = Grid(rows=5, cols=5)
        self.start = Position(0, 0)
        self.goal = Position(4, 4)

    def test_invalid_grid_type(self) -> None:
        """Non-Grid instances must raise TypeError."""
        for invalid_grid in [None, "invalid_grid", 123, [1, 2, 3], True]:
            with self.assertRaises(TypeError):
                bfs(invalid_grid, self.start, self.goal)  # type: ignore
            with self.assertRaises(TypeError):
                dfs(invalid_grid, self.start, self.goal)  # type: ignore

    def test_invalid_start_position_type(self) -> None:
        """Non-Position start arguments must raise TypeError."""
        for invalid_pos in [None, (0, 0), [0, 0], "0, 0", 0, True]:
            with self.assertRaises(TypeError):
                bfs(self.grid, invalid_pos, self.goal)  # type: ignore
            with self.assertRaises(TypeError):
                dfs(self.grid, invalid_pos, self.goal)  # type: ignore

    def test_invalid_goal_position_type(self) -> None:
        """Non-Position goal arguments must raise TypeError."""
        for invalid_pos in [None, (4, 4), [4, 4], "4, 4", 4, False]:
            with self.assertRaises(TypeError):
                bfs(self.grid, self.start, invalid_pos)  # type: ignore
            with self.assertRaises(TypeError):
                dfs(self.grid, self.start, invalid_pos)  # type: ignore

    def test_out_of_bounds_start_position(self) -> None:
        """Start positions outside grid bounds must raise PositionOutOfBoundsError (ValueError, IndexError)."""
        out_of_bounds = [
            Position(-1, 0),
            Position(0, -1),
            Position(5, 2),
            Position(2, 5),
            Position(99, 99),
        ]
        for bad_pos in out_of_bounds:
            with self.assertRaises((ValueError, IndexError)):
                bfs(self.grid, bad_pos, self.goal)
            with self.assertRaises((ValueError, IndexError)):
                dfs(self.grid, bad_pos, self.goal)

    def test_out_of_bounds_goal_position(self) -> None:
        """Goal positions outside grid bounds must raise PositionOutOfBoundsError (ValueError, IndexError)."""
        out_of_bounds = [
            Position(-1, 0),
            Position(0, -1),
            Position(5, 2),
            Position(2, 5),
            Position(99, 99),
        ]
        for bad_pos in out_of_bounds:
            with self.assertRaises((ValueError, IndexError)):
                bfs(self.grid, self.start, bad_pos)
            with self.assertRaises((ValueError, IndexError)):
                dfs(self.grid, self.start, bad_pos)


class TestOpenGridSearch(unittest.TestCase):
    """Test Suite 2: Search algorithms on open, unobstructed grids."""

    def setUp(self) -> None:
        self.grid = Grid(rows=6, cols=6)

    def test_bfs_shortest_path_optimality(self) -> None:
        """BFS must find the strictly shortest route matching Manhattan distance."""
        start = Position(0, 0)
        goal = Position(5, 5)
        result = bfs(self.grid, start, goal)

        self.assertTrue(result.found)
        # Manhattan distance on 6x6 from (0,0) to (5,5) is 5 + 5 = 10 steps
        self.assertEqual(result.path_length, 10)
        self.assertEqual(result.total_cost, 10)
        self.assertEqual(len(result.path), 11)
        self.assertEqual(result.path[0], start)
        self.assertEqual(result.path[-1], goal)
        self.assertTrue(is_valid_path(self.grid, result.path, start, goal))
        self.assertGreater(result.nodes_explored, 0)
        self.assertEqual(result.nodes_explored, len(result.visited_order))
        self.assertGreaterEqual(result.execution_time_ms, 0.0)

    def test_dfs_valid_path_discovery(self) -> None:
        """DFS must find a valid, contiguous path to the goal."""
        start = Position(0, 0)
        goal = Position(5, 5)
        result = dfs(self.grid, start, goal)

        self.assertTrue(result.found)
        self.assertEqual(result.path[0], start)
        self.assertEqual(result.path[-1], goal)
        self.assertTrue(is_valid_path(self.grid, result.path, start, goal))
        self.assertEqual(result.path_length, len(result.path) - 1)
        self.assertEqual(result.total_cost, result.path_length)
        self.assertEqual(result.nodes_explored, len(result.visited_order))

    def test_horizontal_movement(self) -> None:
        """Linear horizontal route along a row."""
        start = Position(1, 2)
        goal = Position(4, 2)

        bfs_res = bfs(self.grid, start, goal)
        dfs_res = dfs(self.grid, start, goal)

        self.assertTrue(bfs_res.found)
        self.assertEqual(bfs_res.path_length, 3)
        self.assertTrue(is_valid_path(self.grid, bfs_res.path, start, goal))

        self.assertTrue(dfs_res.found)
        self.assertTrue(is_valid_path(self.grid, dfs_res.path, start, goal))

    def test_vertical_movement(self) -> None:
        """Linear vertical route along a column."""
        start = Position(3, 0)
        goal = Position(3, 4)

        bfs_res = bfs(self.grid, start, goal)
        dfs_res = dfs(self.grid, start, goal)

        self.assertTrue(bfs_res.found)
        self.assertEqual(bfs_res.path_length, 4)
        self.assertTrue(is_valid_path(self.grid, bfs_res.path, start, goal))

        self.assertTrue(dfs_res.found)
        self.assertTrue(is_valid_path(self.grid, dfs_res.path, start, goal))


class TestStartEqualsGoal(unittest.TestCase):
    """Test Suite 3: Behavior when start position equals destination position."""

    def test_walkable_start_equals_goal(self) -> None:
        """When start == goal on a walkable cell, return zero-step path [start]."""
        grid = Grid(rows=4, cols=4)
        target = Position(2, 2)

        for algo_func, name in [(bfs, "Breadth-First Search"), (dfs, "Depth-First Search")]:
            result = algo_func(grid, target, target)
            self.assertTrue(result.found, f"{name} should find goal when start==goal")
            self.assertEqual(result.path, [target])
            self.assertEqual(result.path_length, 0)
            self.assertEqual(result.total_cost, 0)
            self.assertEqual(result.nodes_explored, 1)
            self.assertEqual(result.visited_order, [target])

    def test_blocked_start_equals_goal(self) -> None:
        """When start == goal but the cell is blocked, no path can exist."""
        grid = Grid(rows=4, cols=4)
        target = Position(1, 1)
        grid.add_obstacle(target)

        for algo_func, name in [(bfs, "Breadth-First Search"), (dfs, "Depth-First Search")]:
            result = algo_func(grid, target, target)
            self.assertFalse(result.found, f"{name} must fail if target cell is blocked")
            self.assertEqual(result.path, [])
            self.assertEqual(result.path_length, 0)
            self.assertIsNone(result.total_cost)
            self.assertEqual(result.nodes_explored, 0)


class TestBlockedStartAndDestination(unittest.TestCase):
    """Test Suite 4: Searches with blocked starting or destination positions."""

    def setUp(self) -> None:
        self.grid = Grid(rows=5, cols=5)
        self.start = Position(0, 0)
        self.goal = Position(4, 4)

    def test_blocked_start_obstacle(self) -> None:
        """When start cell has an obstacle, return failure result."""
        self.grid.add_obstacle(self.start)

        for algo_func in [bfs, dfs]:
            res = algo_func(self.grid, self.start, self.goal)
            self.assertFalse(res.found)
            self.assertEqual(res.path, [])
            self.assertEqual(res.path_length, 0)
            self.assertIsNone(res.total_cost)
            self.assertEqual(res.nodes_explored, 0)

    def test_blocked_destination_obstacle(self) -> None:
        """When destination cell has an obstacle, return failure result."""
        self.grid.add_obstacle(self.goal)

        for algo_func in [bfs, dfs]:
            res = algo_func(self.grid, self.start, self.goal)
            self.assertFalse(res.found)
            self.assertEqual(res.path, [])
            self.assertEqual(res.path_length, 0)
            self.assertIsNone(res.total_cost)

    def test_blocked_start_hazard_terrains(self) -> None:
        """Start position on rubble, water, or fire zone must fail."""
        hazard_methods = [
            "add_collapsed_building",
            "add_flood_zone",
            "add_fire_zone",
        ]
        for method_name in hazard_methods:
            g = Grid(rows=4, cols=4)
            getattr(g, method_name)(Position(0, 0))
            bfs_res = bfs(g, Position(0, 0), Position(3, 3))
            dfs_res = dfs(g, Position(0, 0), Position(3, 3))
            self.assertFalse(bfs_res.found)
            self.assertFalse(dfs_res.found)

    def test_blocked_destination_hazard_terrains(self) -> None:
        """Goal position on rubble, water, or fire zone must fail."""
        hazard_methods = [
            "add_collapsed_building",
            "add_flood_zone",
            "add_fire_zone",
        ]
        for method_name in hazard_methods:
            g = Grid(rows=4, cols=4)
            getattr(g, method_name)(Position(3, 3))
            bfs_res = bfs(g, Position(0, 0), Position(3, 3))
            dfs_res = dfs(g, Position(0, 0), Position(3, 3))
            self.assertFalse(bfs_res.found)
            self.assertFalse(dfs_res.found)


class TestObstaclesAndDetours(unittest.TestCase):
    """Test Suite 5: Pathfinding around physical obstacles and hazardous terrain."""

    def test_wall_obstacle_detour(self) -> None:
        """Route must navigate around a vertical wall barrier."""
        # 5x5 grid with wall at col 2 from row 0 to row 3 (gap at row 4)
        grid = Grid(rows=5, cols=5)
        for r in range(4):
            grid.add_obstacle(Position(2, r))

        start = Position(0, 2)
        goal = Position(4, 2)

        bfs_res = bfs(grid, start, goal)
        dfs_res = dfs(grid, start, goal)

        self.assertTrue(bfs_res.found)
        self.assertTrue(dfs_res.found)

        # Neither path should touch any cell on the wall
        for r in range(4):
            wall_pos = Position(2, r)
            self.assertNotIn(wall_pos, bfs_res.path)
            self.assertNotIn(wall_pos, dfs_res.path)

        # Paths must be valid, contiguous routes
        self.assertTrue(is_valid_path(grid, bfs_res.path, start, goal))
        self.assertTrue(is_valid_path(grid, dfs_res.path, start, goal))

        # BFS detour length is strictly optimal:
        # (0,2)->(1,2)->(1,3)->(1,4)->(2,4)->(3,4)->(3,3)->(3,2)->(4,2) = 8 steps
        self.assertEqual(bfs_res.path_length, 8)

    def test_disaster_multi_hazard_detour(self) -> None:
        """Route must navigate through mixed rubble, flood, and fire hazards."""
        grid = Grid(rows=6, cols=6)
        # Add rubble
        grid.add_collapsed_building(Position(1, 1))
        grid.add_collapsed_building(Position(1, 2))
        # Add flood water
        grid.add_flood_zone(Position(3, 2))
        grid.add_flood_zone(Position(3, 3))
        # Add active fire
        grid.add_fire_zone(Position(2, 4))

        start = Position(0, 0)
        goal = Position(5, 5)

        bfs_res = bfs(grid, start, goal)
        dfs_res = dfs(grid, start, goal)

        self.assertTrue(bfs_res.found)
        self.assertTrue(dfs_res.found)

        self.assertTrue(is_valid_path(grid, bfs_res.path, start, goal))
        self.assertTrue(is_valid_path(grid, dfs_res.path, start, goal))

        # Ensure no hazards are traversed
        hazardous = {Position(1, 1), Position(1, 2), Position(3, 2), Position(3, 3), Position(2, 4)}
        for pos in bfs_res.path:
            self.assertNotIn(pos, hazardous)
        for pos in dfs_res.path:
            self.assertNotIn(pos, hazardous)


class TestUnreachableDestinations(unittest.TestCase):
    """Test Suite 6: Behavior when destination is partitioned or unreachable."""

    def test_enclosed_destination(self) -> None:
        """Goal enclosed by obstacles must return found=False and empty path."""
        grid = Grid(rows=5, cols=5)
        goal = Position(4, 4)
        # Block all neighbours to (4, 4): (3, 4) and (4, 3)
        grid.add_obstacle(Position(3, 4))
        grid.add_obstacle(Position(4, 3))

        start = Position(0, 0)
        bfs_res = bfs(grid, start, goal)
        dfs_res = dfs(grid, start, goal)

        self.assertFalse(bfs_res.found)
        self.assertEqual(bfs_res.path, [])
        self.assertEqual(bfs_res.path_length, 0)
        self.assertIsNone(bfs_res.total_cost)

        self.assertFalse(dfs_res.found)
        self.assertEqual(dfs_res.path, [])
        self.assertEqual(dfs_res.path_length, 0)
        self.assertIsNone(dfs_res.total_cost)

    def test_bisected_grid_partition(self) -> None:
        """Full column barrier dividing the grid prevents cross-barrier path."""
        grid = Grid(rows=6, cols=6)
        # Wall down entire column 3
        for r in range(6):
            grid.add_obstacle(Position(3, r))

        start = Position(1, 2)
        goal = Position(5, 2)

        bfs_res = bfs(grid, start, goal)
        dfs_res = dfs(grid, start, goal)

        self.assertFalse(bfs_res.found)
        self.assertFalse(dfs_res.found)
        self.assertEqual(bfs_res.path, [])
        self.assertEqual(dfs_res.path, [])


class TestBoundaryPositions(unittest.TestCase):
    """Test Suite 7: Boundary position traversal and edge confinement."""

    def test_corner_to_corner_traversal(self) -> None:
        """Search between diagonal extreme corners of the grid."""
        grid = Grid(rows=8, cols=10)
        corners = [
            (Position(0, 0), Position(9, 7)),
            (Position(9, 0), Position(0, 7)),
            (Position(0, 7), Position(9, 0)),
            (Position(9, 7), Position(0, 0)),
        ]
        for s, g in corners:
            bfs_res = bfs(grid, s, g)
            self.assertTrue(bfs_res.found)
            self.assertEqual(bfs_res.path_length, (10 - 1) + (8 - 1))  # 9 + 7 = 16
            self.assertTrue(is_valid_path(grid, bfs_res.path, s, g))

            dfs_res = dfs(grid, s, g)
            self.assertTrue(dfs_res.found)
            self.assertTrue(is_valid_path(grid, dfs_res.path, s, g))

    def test_perimeter_edge_traversal(self) -> None:
        """Search along the outer perimeter edges."""
        grid = Grid(rows=5, cols=5)

        # Top edge
        res = bfs(grid, Position(0, 0), Position(4, 0))
        self.assertTrue(res.found)
        self.assertEqual(res.path_length, 4)

        # Bottom edge
        res = bfs(grid, Position(0, 4), Position(4, 4))
        self.assertTrue(res.found)
        self.assertEqual(res.path_length, 4)

        # Left edge
        res = bfs(grid, Position(0, 0), Position(0, 4))
        self.assertTrue(res.found)
        self.assertEqual(res.path_length, 4)

        # Right edge
        res = bfs(grid, Position(4, 0), Position(4, 4))
        self.assertTrue(res.found)
        self.assertEqual(res.path_length, 4)


class TestGridImmutability(unittest.TestCase):
    """Test Suite 8: Verify algorithms do not modify or corrupt the input grid."""

    def test_grid_remains_unchanged(self) -> None:
        """Grid cell states and string representation must remain identical before and after search."""
        grid = Grid(rows=5, cols=5)
        grid.add_collapsed_building(Position(1, 1))
        grid.add_flood_zone(Position(2, 3))
        grid.add_fire_zone(Position(3, 1))
        grid.add_road(Position(0, 4))

        repr_before = grid.to_string()

        # Run multiple searches
        bfs(grid, Position(0, 0), Position(4, 4))
        dfs(grid, Position(0, 0), Position(4, 4))
        bfs(grid, Position(0, 0), Position(1, 1))  # Blocked goal

        repr_after = grid.to_string()
        self.assertEqual(repr_before, repr_after)

        # Verify cell attributes directly
        self.assertTrue(grid.get_cell(Position(1, 1)).is_obstacle)
        self.assertEqual(grid.get_cell(Position(1, 1)).terrain, TerrainType.RUBBLE)
        self.assertEqual(grid.get_cell(Position(2, 3)).terrain, TerrainType.WATER)
        self.assertEqual(grid.get_cell(Position(3, 1)).terrain, TerrainType.FIRE_ZONE)
        self.assertEqual(grid.get_cell(Position(0, 4)).terrain, TerrainType.ROAD)


class TestDeterministicOrdering(unittest.TestCase):
    """Test Suite 9: Determinism in neighbour expansion and route reproduction."""

    def test_bfs_determinism(self) -> None:
        """Repeated BFS runs on identical grid state must yield identical paths."""
        grid = Grid(rows=6, cols=6)
        grid.add_obstacle(Position(2, 2))
        grid.add_obstacle(Position(3, 3))

        start = Position(0, 0)
        goal = Position(5, 5)

        run1 = bfs(grid, start, goal)
        run2 = bfs(grid, start, goal)

        self.assertEqual(run1.path, run2.path)
        self.assertEqual(run1.visited_order, run2.visited_order)
        self.assertEqual(run1.nodes_explored, run2.nodes_explored)
        self.assertEqual(run1.path_length, run2.path_length)

    def test_dfs_determinism(self) -> None:
        """Repeated DFS runs on identical grid state must yield identical paths."""
        grid = Grid(rows=6, cols=6)
        grid.add_obstacle(Position(2, 2))
        grid.add_obstacle(Position(3, 3))

        start = Position(0, 0)
        goal = Position(5, 5)

        run1 = dfs(grid, start, goal)
        run2 = dfs(grid, start, goal)

        self.assertEqual(run1.path, run2.path)
        self.assertEqual(run1.visited_order, run2.visited_order)
        self.assertEqual(run1.nodes_explored, run2.nodes_explored)
        self.assertEqual(run1.path_length, run2.path_length)

    def test_class_wrappers(self) -> None:
        """BreadthFirstSearch and DepthFirstSearch class wrappers execute correctly."""
        grid = Grid(rows=4, cols=4)
        start = Position(0, 0)
        goal = Position(3, 3)

        bfs_class_res = BreadthFirstSearch.search(grid, start, goal)
        dfs_class_res = DepthFirstSearch.search(grid, start, goal)

        self.assertTrue(bfs_class_res.found)
        self.assertTrue(dfs_class_res.found)

        # Instance callables
        bfs_instance = BreadthFirstSearch()
        dfs_instance = DepthFirstSearch()
        self.assertTrue(bfs_instance(grid, start, goal).found)
        self.assertTrue(dfs_instance(grid, start, goal).found)


class TestSearchResultStructure(unittest.TestCase):
    """Test Suite 10: SearchResult fields, invariants, serialization, and string representations."""

    def test_result_attributes(self) -> None:
        """Verify all required SearchResult attributes are populated accurately."""
        start = Position(0, 0)
        goal = Position(2, 2)
        path = [Position(0, 0), Position(1, 0), Position(2, 0), Position(2, 1), Position(2, 2)]
        visited = [Position(0, 0), Position(1, 0), Position(0, 1), Position(2, 0), Position(2, 1), Position(2, 2)]

        result = SearchResult(
            algorithm_name="Breadth-First Search",
            start_position=start,
            goal_position=goal,
            found=True,
            path=path,
            visited_order=visited,
            execution_time_ms=1.234,
        )

        self.assertEqual(result.algorithm_name, "Breadth-First Search")
        self.assertEqual(result.start_position, start)
        self.assertEqual(result.goal_position, goal)
        self.assertTrue(result.found)
        self.assertEqual(result.path, path)
        self.assertEqual(result.visited_order, visited)
        self.assertEqual(result.nodes_explored, 6)
        self.assertEqual(result.path_length, 4)
        self.assertEqual(result.total_cost, 4)
        self.assertEqual(result.execution_time_ms, 1.234)

    def test_result_to_dict_and_strings(self) -> None:
        """Verify dictionary conversion and string representations."""
        start = Position(0, 0)
        goal = Position(1, 0)
        path = [start, goal]
        result = SearchResult(
            algorithm_name="Breadth-First Search",
            start_position=start,
            goal_position=goal,
            found=True,
            path=path,
            execution_time_ms=0.5,
        )

        d = result.to_dict()
        self.assertEqual(d["algorithm_name"], "Breadth-First Search")
        self.assertTrue(d["found"])
        self.assertEqual(d["path_length"], 1)
        self.assertEqual(d["total_cost"], 1)

        summary_str = result.summary()
        self.assertIn("Breadth-First Search", summary_str)
        self.assertIn("SUCCESS", summary_str)
        self.assertIn(str(start), summary_str)
        self.assertIn(str(goal), summary_str)

        repr_str = repr(result)
        self.assertIn("SearchResult", repr_str)
        self.assertIn("Breadth-First Search", repr_str)


class TestSearchUtils(unittest.TestCase):
    """Test Suite 11: Validation helpers, path reconstruction, and visualizers."""

    def test_reconstruct_path_failure_modes(self) -> None:
        """Path reconstruction returns empty list when goal is unlinked."""
        start = Position(0, 0)
        goal = Position(3, 3)

        # Empty parent map
        self.assertEqual(reconstruct_path({}, start, goal), [])

        # Goal not in parent map
        self.assertEqual(reconstruct_path({start: None}, start, goal), [])

        # Disconnected chain
        bad_parents = {
            goal: Position(2, 2),
            Position(2, 2): Position(1, 1),
            # Missing link to start
        }
        self.assertEqual(reconstruct_path(bad_parents, start, goal), [])

    def test_is_valid_path_checks(self) -> None:
        """is_valid_path validates boundary, walkability, and continuity."""
        grid = Grid(rows=4, cols=4)
        start = Position(0, 0)
        goal = Position(2, 0)

        # Valid path
        valid = [Position(0, 0), Position(1, 0), Position(2, 0)]
        self.assertTrue(is_valid_path(grid, valid, start, goal))

        # Empty path
        self.assertFalse(is_valid_path(grid, [], start, goal))

        # Incorrect endpoints
        self.assertFalse(is_valid_path(grid, valid, Position(0, 1), goal))
        self.assertFalse(is_valid_path(grid, valid, start, Position(3, 0)))

        # Non-cardinal step (diagonal jump)
        diag = [Position(0, 0), Position(1, 1), Position(2, 0)]
        self.assertFalse(is_valid_path(grid, diag, start, goal))

        # Path traversing blocked cell
        grid.add_obstacle(Position(1, 0))
        self.assertFalse(is_valid_path(grid, valid, start, goal))

    def test_render_grid_with_path(self) -> None:
        """render_grid_with_path formats grid containing start 'S', goal 'G', and path '*'."""
        grid = Grid(rows=3, cols=3)
        path = [Position(0, 0), Position(1, 0), Position(2, 0)]
        rendered = render_grid_with_path(grid, path)

        self.assertIn("S", rendered)
        self.assertIn("G", rendered)
        self.assertIn("*", rendered)


if __name__ == "__main__":
    unittest.main()
