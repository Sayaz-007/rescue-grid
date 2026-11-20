"""
Unit test suite for Uniform-Cost Search (UCS) and weighted terrain movement costs in RescueGrid.
Verifies cost-optimal route discovery, priority queue dynamics, outdated entry discarding,
illustrative terrain costs, and failure conventions.
"""

import math
import os
import sys
import unittest

# Ensure root workspace directory is on module search path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from models.position import Position
from environment.cell import Cell, TerrainType, TerrainCostConfig
from environment.grid import Grid
from algorithms.search_result import SearchResult
from algorithms.search_utils import (
    validate_search_inputs,
    is_valid_path,
    calculate_path_cost,
    PositionOutOfBoundsError,
)
from algorithms.bfs import bfs
from algorithms.ucs import ucs, UniformCostSearch


class TestTerrainMovementCosts(unittest.TestCase):
    """Test Suite 1: Terrain movement cost configuration, validation, and cell overrides."""

    def tearDown(self) -> None:
        # Reset terrain costs after each test
        TerrainCostConfig.reset_defaults()

    def test_default_terrain_costs(self) -> None:
        """Verify standard Phase 4 terrain costs: ROAD=1, NORMAL=2, ROUGH=4, Hazards=inf."""
        self.assertEqual(TerrainCostConfig.get_cost(TerrainType.ROAD), 1.0)
        self.assertEqual(TerrainCostConfig.get_cost(TerrainType.NORMAL), 2.0)
        self.assertEqual(TerrainCostConfig.get_cost(TerrainType.ROUGH), 4.0)

        # Non-traversable terrains must have infinite movement cost
        self.assertTrue(math.isinf(TerrainCostConfig.get_cost(TerrainType.RUBBLE)))
        self.assertTrue(math.isinf(TerrainCostConfig.get_cost(TerrainType.WATER)))
        self.assertTrue(math.isinf(TerrainCostConfig.get_cost(TerrainType.FIRE_ZONE)))

    def test_cell_movement_costs(self) -> None:
        """Verify Cell reflects terrain movement cost by default."""
        c_road = Cell(Position(0, 0), terrain=TerrainType.ROAD)
        c_norm = Cell(Position(0, 1), terrain=TerrainType.NORMAL)
        c_rough = Cell(Position(0, 2), terrain=TerrainType.ROUGH)
        c_rubble = Cell(Position(0, 3), terrain=TerrainType.RUBBLE)

        self.assertEqual(c_road.movement_cost, 1.0)
        self.assertEqual(c_norm.movement_cost, 2.0)
        self.assertEqual(c_rough.movement_cost, 4.0)
        self.assertTrue(math.isinf(c_rubble.movement_cost))
        self.assertFalse(c_rubble.has_finite_cost)

    def test_obstacle_cells_have_infinite_cost(self) -> None:
        """Placing an obstacle must immediately make movement cost infinite."""
        cell = Cell(Position(0, 0), terrain=TerrainType.ROAD)
        self.assertEqual(cell.movement_cost, 1.0)
        cell.set_obstacle(True)
        self.assertTrue(math.isinf(cell.movement_cost))

    def test_invalid_terrain_cost_configuration(self) -> None:
        """Setting invalid movement costs must be strictly rejected."""
        # Non-positive or zero
        with self.assertRaises(ValueError):
            TerrainCostConfig.set_cost(TerrainType.ROAD, 0)
        with self.assertRaises(ValueError):
            TerrainCostConfig.set_cost(TerrainType.ROAD, -5)

        # NaN or Infinite
        with self.assertRaises(ValueError):
            TerrainCostConfig.set_cost(TerrainType.ROAD, float("nan"))
        with self.assertRaises(ValueError):
            TerrainCostConfig.set_cost(TerrainType.ROAD, float("inf"))

        # Non-numeric or boolean
        with self.assertRaises(TypeError):
            TerrainCostConfig.set_cost(TerrainType.ROAD, "cheap")  # type: ignore
        with self.assertRaises(TypeError):
            TerrainCostConfig.set_cost(TerrainType.ROAD, True)  # type: ignore

        # Cannot assign finite cost to non-traversable terrain
        with self.assertRaises(ValueError):
            TerrainCostConfig.set_cost(TerrainType.RUBBLE, 5.0)
        with self.assertRaises(ValueError):
            TerrainCostConfig.set_cost(TerrainType.WATER, 3.0)
        with self.assertRaises(ValueError):
            TerrainCostConfig.set_cost(TerrainType.FIRE_ZONE, 2.0)

    def test_custom_cell_cost_override(self) -> None:
        """Individual cells can receive custom valid cost overrides."""
        cell = Cell(Position(0, 0), terrain=TerrainType.NORMAL)
        self.assertEqual(cell.movement_cost, 2.0)

        # Override to 10.5
        cell.set_movement_cost(10.5)
        self.assertEqual(cell.movement_cost, 10.5)

        # Clear override
        cell.set_movement_cost(None)
        self.assertEqual(cell.movement_cost, 2.0)

    def test_custom_cell_cost_validation(self) -> None:
        """Invalid cell cost overrides must raise appropriate exceptions."""
        cell = Cell(Position(0, 0), terrain=TerrainType.NORMAL)

        with self.assertRaises(ValueError):
            cell.set_movement_cost(-1)
        with self.assertRaises(ValueError):
            cell.set_movement_cost(0)
        with self.assertRaises(TypeError):
            cell.set_movement_cost("free")  # type: ignore
        with self.assertRaises(TypeError):
            cell.set_movement_cost(False)  # type: ignore

        # Cannot set cost on a non-walkable cell
        obstacle_cell = Cell(Position(1, 1), is_obstacle=True)
        with self.assertRaises(ValueError):
            obstacle_cell.set_movement_cost(5)


class TestUCSInputValidation(unittest.TestCase):
    """Test Suite 2: UCS parameter type and boundary validation."""

    def setUp(self) -> None:
        self.grid = Grid(rows=5, cols=5)
        self.start = Position(0, 0)
        self.goal = Position(4, 4)

    def test_invalid_types(self) -> None:
        """UCS must reject non-Grid and non-Position types with TypeError."""
        for bad_grid in [None, "grid", 123, []]:
            with self.assertRaises(TypeError):
                ucs(bad_grid, self.start, self.goal)  # type: ignore

        for bad_pos in [None, (0, 0), "0,0", 0]:
            with self.assertRaises(TypeError):
                ucs(self.grid, bad_pos, self.goal)  # type: ignore
            with self.assertRaises(TypeError):
                ucs(self.grid, self.start, bad_pos)  # type: ignore

    def test_out_of_bounds_positions(self) -> None:
        """UCS must reject out-of-bounds start and goal coordinates."""
        bad_positions = [Position(-1, 0), Position(0, -1), Position(5, 5), Position(10, 2)]
        for bad_pos in bad_positions:
            with self.assertRaises((ValueError, IndexError)):
                ucs(self.grid, bad_pos, self.goal)
            with self.assertRaises((ValueError, IndexError)):
                ucs(self.grid, self.start, bad_pos)


class TestUCSOpenGridUniformCosts(unittest.TestCase):
    """Test Suite 3: UCS on open grid with uniform costs matches BFS."""

    def test_uniform_cost_matches_bfs(self) -> None:
        """On an open grid with uniform costs, UCS finds shortest path matching BFS."""
        grid = Grid(rows=6, cols=6, default_terrain=TerrainType.ROAD)  # All cost 1
        start = Position(0, 0)
        goal = Position(5, 5)

        ucs_res = ucs(grid, start, goal)
        bfs_res = bfs(grid, start, goal)

        self.assertTrue(ucs_res.found)
        self.assertTrue(bfs_res.found)
        # Manhattan distance is 10 steps
        self.assertEqual(ucs_res.path_length, 10)
        self.assertEqual(bfs_res.path_length, 10)
        self.assertEqual(ucs_res.total_cost, 10)
        self.assertTrue(is_valid_path(grid, ucs_res.path, start, goal))


class TestUCSWeightedRouteSelection(unittest.TestCase):
    """Test Suite 4: UCS finds minimum-cost path over shorter but more expensive paths."""

    def test_longer_cheaper_route_vs_shorter_expensive_route(self) -> None:
        """Demonstrate UCS choosing a longer route with lower cost over a shorter route with higher cost.

        Grid layout (5 rows x 7 cols):
        - Start at (0, 2), Goal at (6, 2).
        - Center row (row 2) direct route: 6 steps of ROUGH terrain (cost 4 each) = 21 (with goal Road).
        - North bypass (row 0-1) road route: 10 steps of ROAD terrain (cost 1 each) = 10.
        - BFS chooses the direct route (length 6).
        - UCS chooses the road route (length 10, cost 10).
        """
        grid = Grid(rows=5, cols=7, default_terrain=TerrainType.NORMAL)

        # Create direct rough terrain route along row 2
        for x in range(1, 6):
            grid.add_rough_terrain(Position(x, 2))

        # Create road bypass route along row 0
        for x in range(7):
            grid.add_road(Position(x, 0))
        grid.add_road(Position(0, 1))
        grid.add_road(Position(6, 1))
        grid.add_road(Position(6, 2))  # Goal is Road

        start = Position(0, 2)
        goal = Position(6, 2)

        ucs_res = ucs(grid, start, goal)
        bfs_res = bfs(grid, start, goal)

        self.assertTrue(ucs_res.found)
        self.assertTrue(bfs_res.found)

        # BFS chooses shortest path in steps (direct rough path: length 6)
        self.assertEqual(bfs_res.path_length, 6)
        bfs_weighted_cost = calculate_path_cost(grid, bfs_res.path)
        self.assertEqual(bfs_weighted_cost, 21)  # 5 steps rough (4*5) + goal road (1) = 21

        # UCS chooses minimum-cost path (road bypass: length 10, cost 10)
        self.assertEqual(ucs_res.path_length, 10)
        self.assertEqual(ucs_res.total_cost, 10)
        self.assertLess(ucs_res.total_cost, bfs_weighted_cost)
        self.assertTrue(is_valid_path(grid, ucs_res.path, start, goal))

    def test_multiple_routes_with_different_costs(self) -> None:
        """UCS evaluates three parallel corridors (Road, Normal, Rough) and selects Road."""
        grid = Grid(rows=5, cols=5)
        # Row 1: ROAD (cost 1 each)
        for x in range(1, 4):
            grid.add_road(Position(x, 1))
        # Row 2: NORMAL (cost 2 each - default)
        # Row 3: ROUGH (cost 4 each)
        for x in range(1, 4):
            grid.add_rough_terrain(Position(x, 3))

        start = Position(0, 2)
        goal = Position(4, 2)

        ucs_res = ucs(grid, start, goal)
        self.assertTrue(ucs_res.found)

        # UCS route traverses the road on row 1:
        # (0,2)->(0,1)->(1,1)->(2,1)->(3,1)->(4,1)->(4,2)
        # Entering: (0,1)[2] + (1,1)[1] + (2,1)[1] + (3,1)[1] + (4,1)[1] + (4,2)[2] = 8
        # Direct through row 2 (Normal): (1,2)[2] + (2,2)[2] + (3,2)[2] + (4,2)[2] = 8
        # Either way cost is <= 8, strictly less than rough corridor (16)
        self.assertLessEqual(ucs_res.total_cost, 8)
        self.assertTrue(is_valid_path(grid, ucs_res.path, start, goal))


class TestUCSObstaclesAndDetours(unittest.TestCase):
    """Test Suite 5: Pathfinding around physical obstacles and hazards."""

    def test_obstacles_forcing_detour(self) -> None:
        """UCS navigates around a wall obstacle while choosing the cheapest side."""
        grid = Grid(rows=6, cols=6)
        # Wall across col 2 from row 1 to row 4
        for r in range(1, 5):
            grid.add_obstacle(Position(2, r))

        # South detour through row 5 is paved ROAD
        for x in range(6):
            grid.add_road(Position(x, 5))

        start = Position(1, 2)
        goal = Position(4, 2)

        ucs_res = ucs(grid, start, goal)
        self.assertTrue(ucs_res.found)
        self.assertTrue(is_valid_path(grid, ucs_res.path, start, goal))

        # Verify no obstacles in path
        for r in range(1, 5):
            self.assertNotIn(Position(2, r), ucs_res.path)

    def test_no_blocked_terrain_in_path(self) -> None:
        """UCS path must never contain rubble, flood water, or fire zones."""
        grid = Grid(rows=6, cols=6)
        grid.add_collapsed_building(Position(1, 1))
        grid.add_flood_zone(Position(2, 2))
        grid.add_fire_zone(Position(3, 3))

        ucs_res = ucs(grid, Position(0, 0), Position(5, 5))
        self.assertTrue(ucs_res.found)

        hazards = {Position(1, 1), Position(2, 2), Position(3, 3)}
        for step in ucs_res.path:
            self.assertNotIn(step, hazards)


class TestUCSUnreachableAndBlocked(unittest.TestCase):
    """Test Suite 6: Failure handling for unreachable or blocked positions."""

    def test_unreachable_destination(self) -> None:
        """Walled-off destination must return found=False, path=[], total_cost=None."""
        grid = Grid(rows=4, cols=4)
        goal = Position(3, 3)
        grid.add_obstacle(Position(2, 3))
        grid.add_obstacle(Position(3, 2))

        result = ucs(grid, Position(0, 0), goal)
        self.assertFalse(result.found)
        self.assertEqual(result.path, [])
        self.assertEqual(result.path_length, 0)
        self.assertIsNone(result.total_cost)

    def test_blocked_start(self) -> None:
        """Blocked starting cell must return failure result immediately."""
        grid = Grid(rows=4, cols=4)
        start = Position(0, 0)
        grid.add_obstacle(start)

        result = ucs(grid, start, Position(3, 3))
        self.assertFalse(result.found)
        self.assertEqual(result.path, [])
        self.assertEqual(result.path_length, 0)
        self.assertIsNone(result.total_cost)
        self.assertEqual(result.nodes_explored, 0)

    def test_blocked_goal(self) -> None:
        """Blocked destination cell must return failure result."""
        grid = Grid(rows=4, cols=4)
        goal = Position(3, 3)
        grid.add_obstacle(goal)

        result = ucs(grid, Position(0, 0), goal)
        self.assertFalse(result.found)
        self.assertEqual(result.path, [])
        self.assertEqual(result.path_length, 0)
        self.assertIsNone(result.total_cost)


class TestUCSStartEqualsGoal(unittest.TestCase):
    """Test Suite 7: Search where start position equals goal position."""

    def test_walkable_start_equals_goal(self) -> None:
        """When start == goal on a walkable cell, return zero-cost path [start]."""
        grid = Grid(rows=4, cols=4)
        pos = Position(2, 2)

        result = ucs(grid, pos, pos)
        self.assertTrue(result.found)
        self.assertEqual(result.path, [pos])
        self.assertEqual(result.path_length, 0)
        self.assertEqual(result.total_cost, 0)
        self.assertEqual(result.nodes_explored, 1)

    def test_blocked_start_equals_goal(self) -> None:
        """When start == goal on a blocked cell, return failure result."""
        grid = Grid(rows=4, cols=4)
        pos = Position(1, 1)
        grid.add_obstacle(pos)

        result = ucs(grid, pos, pos)
        self.assertFalse(result.found)
        self.assertEqual(result.path, [])
        self.assertEqual(result.path_length, 0)
        self.assertIsNone(result.total_cost)


class TestCostCalculationConvention(unittest.TestCase):
    """Test Suite 8: Cost calculation convention and path cost validation."""

    def test_cost_convention_start_not_charged(self) -> None:
        """Verify that the starting cell is not charged in total path cost."""
        grid = Grid(rows=3, cols=3)
        # Start is Rough (cost 4), destination is Road (cost 1)
        grid.add_rough_terrain(Position(0, 0))
        grid.add_road(Position(1, 0))

        result = ucs(grid, Position(0, 0), Position(1, 0))
        self.assertTrue(result.found)
        self.assertEqual(result.path, [Position(0, 0), Position(1, 0)])
        # Only entering (1, 0) is charged (cost = 1), not (0, 0) (cost = 4)
        self.assertEqual(result.total_cost, 1)
        self.assertEqual(calculate_path_cost(grid, result.path), 1.0)


class TestUCSOutdatedQueueEntries(unittest.TestCase):
    """Test Suite 9: Outdated priority-queue entry handling."""

    def test_outdated_entries_superseded(self) -> None:
        """Verify that when a cheaper route to a node is found, outdated entries are discarded."""
        # Topology:
        # Start at (0, 0), Goal at (2, 1)
        # Intermediate node (1, 1) can be reached via:
        # - North-East: (0, 0) -> (1, 0) [cost 10] -> (1, 1) [cost 2] = 12
        # - South-East: (0, 0) -> (0, 1) [cost 1]  -> (1, 1) [cost 2] = 3
        grid = Grid(rows=3, cols=3, default_terrain=TerrainType.NORMAL)

        # Make (1, 0) expensive
        grid.set_cell_cost(Position(1, 0), 10.0)
        # Make (0, 1) cheap road
        grid.add_road(Position(0, 1))

        start = Position(0, 0)
        goal = Position(2, 1)

        result = ucs(grid, start, goal)
        self.assertTrue(result.found)
        # Expected path goes through cheap (0, 1) -> (1, 1) -> (2, 1)
        self.assertIn(Position(0, 1), result.path)
        self.assertNotIn(Position(1, 0), result.path)
        # Cost: (0,1)[1] + (1,1)[2] + (2,1)[2] = 5
        self.assertEqual(result.total_cost, 5)


class TestUCSClassWrapperAndDeterminism(unittest.TestCase):
    """Test Suite 10: Class wrapper execution and determinism."""

    def test_class_wrapper(self) -> None:
        """UniformCostSearch class methods execute identically to ucs function."""
        grid = Grid(rows=4, cols=4)
        start = Position(0, 0)
        goal = Position(3, 3)

        res1 = UniformCostSearch.search(grid, start, goal)
        self.assertTrue(res1.found)

        instance = UniformCostSearch()
        res2 = instance(grid, start, goal)
        self.assertTrue(res2.found)
        self.assertEqual(res1.path, res2.path)
        self.assertEqual(res1.total_cost, res2.total_cost)

    def test_determinism(self) -> None:
        """Repeated runs of UCS on identical grid state yield identical routes."""
        grid = Grid(rows=5, cols=5)
        grid.add_road(Position(1, 0))
        grid.add_rough_terrain(Position(0, 1))

        run1 = ucs(grid, Position(0, 0), Position(4, 4))
        run2 = ucs(grid, Position(0, 0), Position(4, 4))

        self.assertEqual(run1.path, run2.path)
        self.assertEqual(run1.total_cost, run2.total_cost)
        self.assertEqual(run1.visited_order, run2.visited_order)


if __name__ == "__main__":
    unittest.main()
