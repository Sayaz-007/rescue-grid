"""
Comprehensive unit test suite for A* Search in RescueGrid (Phase 5).
Verifies heuristic admissibility, consistency, cost-optimal route discovery,
equivalence with Uniform-Cost Search (UCS), detour handling, and failure modes.
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
    manhattan_distance,
    manhattan_heuristic,
    PositionOutOfBoundsError,
)
from algorithms.bfs import bfs
from algorithms.ucs import ucs
from algorithms.astar import astar, AStarSearch


class TestAStarInputValidation(unittest.TestCase):
    """Test Suite 1: Input type validation and grid boundary enforcement for A*."""

    def setUp(self) -> None:
        self.grid = Grid(rows=5, cols=5)
        self.start = Position(0, 0)
        self.goal = Position(4, 4)

    def test_invalid_types(self) -> None:
        """A* must reject non-Grid and non-Position types with TypeError."""
        for bad_grid in [None, "grid", 123, [1, 2], True]:
            with self.assertRaises(TypeError):
                astar(bad_grid, self.start, self.goal)  # type: ignore

        for bad_pos in [None, (0, 0), "0,0", 123, False]:
            with self.assertRaises(TypeError):
                astar(self.grid, bad_pos, self.goal)  # type: ignore
            with self.assertRaises(TypeError):
                astar(self.grid, self.start, bad_pos)  # type: ignore

    def test_out_of_bounds_positions(self) -> None:
        """A* must reject out-of-bounds start and goal coordinates."""
        bad_positions = [Position(-1, 0), Position(0, -1), Position(5, 5), Position(10, 2)]
        for bad_pos in bad_positions:
            with self.assertRaises((ValueError, IndexError)):
                astar(self.grid, bad_pos, self.goal)
            with self.assertRaises((ValueError, IndexError)):
                astar(self.grid, self.start, bad_pos)


class TestAStarHeuristicProperties(unittest.TestCase):
    """Test Suite 2: Mathematical properties of the cost-scaled Manhattan heuristic."""

    def test_manhattan_distance(self) -> None:
        """Verify L1 Manhattan distance calculation."""
        p1 = Position(1, 2)
        p2 = Position(4, 6)
        # |1 - 4| + |2 - 6| = 3 + 4 = 7
        self.assertEqual(manhattan_distance(p1, p2), 7)
        self.assertEqual(manhattan_distance(p2, p1), 7)
        self.assertEqual(manhattan_distance(p1, p1), 0)

    def test_heuristic_zero_at_destination(self) -> None:
        """The heuristic must return zero when evaluated at the destination cell."""
        dest = Position(5, 5)
        self.assertEqual(manhattan_heuristic(dest, dest, min_cost=1.0), 0.0)
        self.assertEqual(manhattan_heuristic(dest, dest, min_cost=2.0), 0.0)
        self.assertEqual(manhattan_heuristic(dest, dest, min_cost=4.0), 0.0)

    def test_heuristic_admissibility_and_consistency(self) -> None:
        """Verify that h(n) <= h*(n) (admissible) and h(n) <= c(n, n') + h(n') (consistent)."""
        grid = Grid(rows=6, cols=6, default_terrain=TerrainType.NORMAL)
        goal = Position(5, 5)
        min_cost = TerrainCostConfig.get_min_traversable_cost()  # 1.0

        for r in range(6):
            for c in range(6):
                curr = Position(c, r)
                h_curr = manhattan_heuristic(curr, goal, min_cost)

                # Find actual minimum cost to goal using UCS (ground truth h*(n))
                actual_result = ucs(grid, curr, goal)
                if actual_result.found:
                    actual_cost = actual_result.total_cost
                    # Admissibility check: h(n) must never overestimate h*(n)
                    self.assertLessEqual(
                        h_curr,
                        actual_cost,
                        f"Heuristic {h_curr} overestimated actual cost {actual_cost} at {curr}",
                    )

                # Consistency check: h(curr) <= c(curr, neighbour) + h(neighbour)
                for neighbour in grid.get_walkable_neighbours(curr):
                    h_neighbour = manhattan_heuristic(neighbour, goal, min_cost)
                    step_cost = grid.get_movement_cost(neighbour)
                    self.assertLessEqual(
                        h_curr,
                        step_cost + h_neighbour + 1e-9,
                        f"Consistency violated between {curr} and {neighbour}",
                    )


class TestAStarOpenGridUniformCost(unittest.TestCase):
    """Test Suite 3: A* on open grids with uniform costs."""

    def test_open_grid_road_terrain(self) -> None:
        """On a uniform ROAD grid (cost = 1), A* finds optimal shortest path."""
        grid = Grid(rows=6, cols=6, default_terrain=TerrainType.ROAD)
        start = Position(0, 0)
        goal = Position(5, 5)

        result = astar(grid, start, goal)
        self.assertTrue(result.found)
        # Manhattan distance: 5 + 5 = 10 steps
        self.assertEqual(result.path_length, 10)
        self.assertEqual(result.total_cost, 10)
        self.assertTrue(is_valid_path(grid, result.path, start, goal))

    def test_open_grid_normal_terrain(self) -> None:
        """On a uniform NORMAL grid (cost = 2), A* finds optimal path with total_cost = length * 2."""
        grid = Grid(rows=5, cols=5, default_terrain=TerrainType.NORMAL)
        start = Position(0, 0)
        goal = Position(4, 4)

        result = astar(grid, start, goal)
        self.assertTrue(result.found)
        self.assertEqual(result.path_length, 8)
        self.assertEqual(result.total_cost, 8 * 2)  # 16
        self.assertTrue(is_valid_path(grid, result.path, start, goal))


class TestAStarWeightedRouteSelection(unittest.TestCase):
    """Test Suite 4: A* selects minimum-cost path over shorter but more expensive routes."""

    def test_longer_cheaper_route_selection(self) -> None:
        """A* selects longer road bypass over shorter rough corridor.

        Grid layout (5 rows x 7 cols):
        - Start at (0, 2), Goal at (6, 2).
        - Direct rough corridor: 6 steps (entering 5 rough cells [4 each] + goal road [1]) = 21.
        - North road bypass: 10 steps of ROAD (cost 1 each) = 10.
        - A* must choose the road bypass (cost 10, length 10).
        """
        grid = Grid(rows=5, cols=7, default_terrain=TerrainType.NORMAL)

        # Direct rough corridor along row 2
        for x in range(1, 6):
            grid.add_rough_terrain(Position(x, 2))

        # Paved road bypass along row 0
        for x in range(7):
            grid.add_road(Position(x, 0))
        grid.add_road(Position(0, 1))
        grid.add_road(Position(6, 1))
        grid.add_road(Position(6, 2))  # Goal is road

        start = Position(0, 2)
        goal = Position(6, 2)

        astar_res = astar(grid, start, goal)
        ucs_res = ucs(grid, start, goal)
        bfs_res = bfs(grid, start, goal)

        self.assertTrue(astar_res.found)
        self.assertTrue(ucs_res.found)
        self.assertTrue(bfs_res.found)

        # BFS chooses shorter route (6 steps, cost 21)
        self.assertEqual(bfs_res.path_length, 6)
        self.assertEqual(calculate_path_cost(grid, bfs_res.path), 21)

        # A* chooses minimum-cost route matching UCS (10 steps, cost 10)
        self.assertEqual(astar_res.path_length, 10)
        self.assertEqual(astar_res.total_cost, 10)
        self.assertEqual(astar_res.total_cost, ucs_res.total_cost)
        self.assertTrue(is_valid_path(grid, astar_res.path, start, goal))


class TestAStarObstaclesAndDetours(unittest.TestCase):
    """Test Suite 5: Pathfinding around physical obstacles and hazardous terrain."""

    def test_wall_obstacle_detour(self) -> None:
        """A* navigates around a vertical barrier wall."""
        grid = Grid(rows=6, cols=6)
        # Wall across col 2 from row 0 to row 4 (gap at row 5)
        for r in range(5):
            grid.add_obstacle(Position(2, r))

        start = Position(0, 2)
        goal = Position(4, 2)

        result = astar(grid, start, goal)
        self.assertTrue(result.found)
        self.assertTrue(is_valid_path(grid, result.path, start, goal))

        # Verify no obstacles in path
        for r in range(5):
            self.assertNotIn(Position(2, r), result.path)

    def test_no_blocked_hazards_in_path(self) -> None:
        """A* routes must never traverse rubble, flood water, or fire zones."""
        grid = Grid(rows=6, cols=6)
        grid.add_collapsed_building(Position(1, 1))
        grid.add_flood_zone(Position(2, 2))
        grid.add_fire_zone(Position(3, 3))

        start = Position(0, 0)
        goal = Position(5, 5)

        result = astar(grid, start, goal)
        self.assertTrue(result.found)

        hazards = {Position(1, 1), Position(2, 2), Position(3, 3)}
        for step in result.path:
            self.assertNotIn(step, hazards)


class TestAStarUnreachableAndBlocked(unittest.TestCase):
    """Test Suite 6: Failure handling for unreachable and blocked destinations."""

    def test_unreachable_destination(self) -> None:
        """Enclosed destination must return found=False, path=[], total_cost=None."""
        grid = Grid(rows=4, cols=4)
        goal = Position(3, 3)
        grid.add_obstacle(Position(2, 3))
        grid.add_obstacle(Position(3, 2))

        result = astar(grid, Position(0, 0), goal)
        self.assertFalse(result.found)
        self.assertEqual(result.path, [])
        self.assertEqual(result.path_length, 0)
        self.assertIsNone(result.total_cost)

    def test_blocked_start(self) -> None:
        """Blocked starting cell returns failure result immediately."""
        grid = Grid(rows=4, cols=4)
        start = Position(0, 0)
        grid.add_obstacle(start)

        result = astar(grid, start, Position(3, 3))
        self.assertFalse(result.found)
        self.assertEqual(result.path, [])
        self.assertEqual(result.path_length, 0)
        self.assertIsNone(result.total_cost)
        self.assertEqual(result.nodes_explored, 0)

    def test_blocked_goal(self) -> None:
        """Blocked destination cell returns failure result."""
        grid = Grid(rows=4, cols=4)
        goal = Position(3, 3)
        grid.add_obstacle(goal)

        result = astar(grid, Position(0, 0), goal)
        self.assertFalse(result.found)
        self.assertEqual(result.path, [])
        self.assertEqual(result.path_length, 0)
        self.assertIsNone(result.total_cost)

    def test_hazard_blocked_start_and_goal(self) -> None:
        """Start or goal on rubble, water, or fire zone fails."""
        for setter in ["add_collapsed_building", "add_flood_zone", "add_fire_zone"]:
            g = Grid(rows=4, cols=4)
            getattr(g, setter)(Position(0, 0))
            self.assertFalse(astar(g, Position(0, 0), Position(3, 3)).found)

            g2 = Grid(rows=4, cols=4)
            getattr(g2, setter)(Position(3, 3))
            self.assertFalse(astar(g2, Position(0, 0), Position(3, 3)).found)


class TestAStarStartEqualsGoal(unittest.TestCase):
    """Test Suite 7: Search where start position equals goal position."""

    def test_walkable_start_equals_goal(self) -> None:
        """When start == goal on a walkable cell, return zero-cost path [start]."""
        grid = Grid(rows=4, cols=4)
        pos = Position(2, 2)

        result = astar(grid, pos, pos)
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

        result = astar(grid, pos, pos)
        self.assertFalse(result.found)
        self.assertEqual(result.path, [])
        self.assertEqual(result.path_length, 0)
        self.assertIsNone(result.total_cost)


class TestAStarCostCalculation(unittest.TestCase):
    """Test Suite 8: Cost calculation convention and path cost validation."""

    def test_start_not_charged(self) -> None:
        """Verify that starting cell is not charged in A* total cost."""
        grid = Grid(rows=3, cols=3)
        # Start is Rough (cost 4), destination is Road (cost 1)
        grid.add_rough_terrain(Position(0, 0))
        grid.add_road(Position(1, 0))

        result = astar(grid, Position(0, 0), Position(1, 0))
        self.assertTrue(result.found)
        self.assertEqual(result.path, [Position(0, 0), Position(1, 0)])
        # Entering (1, 0) costs 1; start (0, 0) is not charged
        self.assertEqual(result.total_cost, 1)
        self.assertEqual(calculate_path_cost(grid, result.path), 1.0)


class TestAStarUcsEquivalence(unittest.TestCase):
    """Test Suite 9: Cost equivalence between A* and UCS across multiple varied disaster maps."""

    def test_equivalence_open_road_grid(self) -> None:
        """Map 1: Open uniform road grid."""
        grid = Grid(rows=7, cols=7, default_terrain=TerrainType.ROAD)
        start, goal = Position(0, 0), Position(6, 6)

        a_res = astar(grid, start, goal)
        u_res = ucs(grid, start, goal)
        self.assertTrue(a_res.found)
        self.assertEqual(a_res.total_cost, u_res.total_cost)
        self.assertTrue(is_valid_path(grid, a_res.path, start, goal))

    def test_equivalence_open_normal_grid(self) -> None:
        """Map 2: Open uniform normal grid."""
        grid = Grid(rows=6, cols=8, default_terrain=TerrainType.NORMAL)
        start, goal = Position(1, 1), Position(7, 5)

        a_res = astar(grid, start, goal)
        u_res = ucs(grid, start, goal)
        self.assertTrue(a_res.found)
        self.assertEqual(a_res.total_cost, u_res.total_cost)
        self.assertTrue(is_valid_path(grid, a_res.path, start, goal))

    def test_equivalence_mixed_terrain_corridors(self) -> None:
        """Map 3: Mixed terrain corridors with Roads, Normal, and Rough ground."""
        grid = Grid(rows=8, cols=10, default_terrain=TerrainType.NORMAL)
        for x in range(10):
            grid.add_road(Position(x, 0))
            grid.add_road(Position(x, 7))
        for x in range(2, 8):
            grid.add_rough_terrain(Position(x, 3))
            grid.add_rough_terrain(Position(x, 4))

        start, goal = Position(0, 3), Position(9, 4)

        a_res = astar(grid, start, goal)
        u_res = ucs(grid, start, goal)
        self.assertTrue(a_res.found)
        self.assertEqual(a_res.total_cost, u_res.total_cost)
        self.assertTrue(is_valid_path(grid, a_res.path, start, goal))

    def test_equivalence_maze_barriers(self) -> None:
        """Map 4: Obstacle maze requiring multi-bend detours."""
        grid = Grid(rows=8, cols=8)
        # Horizontal barrier with right gap
        for x in range(6):
            grid.add_obstacle(Position(x, 2))
        # Horizontal barrier with left gap
        for x in range(2, 8):
            grid.add_obstacle(Position(x, 5))

        start, goal = Position(0, 0), Position(7, 7)

        a_res = astar(grid, start, goal)
        u_res = ucs(grid, start, goal)
        self.assertTrue(a_res.found)
        self.assertEqual(a_res.total_cost, u_res.total_cost)
        self.assertTrue(is_valid_path(grid, a_res.path, start, goal))

    def test_equivalence_disaster_multi_hazard(self) -> None:
        """Map 5: Complex disaster zone with rubble, floods, fire, and paved roads."""
        grid = Grid(rows=9, cols=11, default_terrain=TerrainType.NORMAL)
        # Hazards
        grid.add_collapsed_building(Position(3, 2))
        grid.add_collapsed_building(Position(3, 3))
        grid.add_collapsed_building(Position(3, 4))
        grid.add_flood_zone(Position(6, 4))
        grid.add_flood_zone(Position(6, 5))
        grid.add_fire_zone(Position(8, 2))
        grid.add_fire_zone(Position(8, 3))
        # Roads
        for x in range(11):
            grid.add_road(Position(x, 1))

        start, goal = Position(0, 0), Position(10, 8)

        a_res = astar(grid, start, goal)
        u_res = ucs(grid, start, goal)
        self.assertTrue(a_res.found)
        self.assertEqual(a_res.total_cost, u_res.total_cost)
        self.assertTrue(is_valid_path(grid, a_res.path, start, goal))


class TestAStarGridImmutabilityAndDeterminism(unittest.TestCase):
    """Test Suite 10: Grid immutability, determinism, and class wrappers."""

    def test_grid_immutability(self) -> None:
        """A* execution must not alter any cell states or grid representation."""
        grid = Grid(rows=5, cols=5)
        grid.add_road(Position(1, 1))
        grid.add_rough_terrain(Position(2, 2))
        grid.add_obstacle(Position(3, 3))

        before_repr = grid.to_string()
        astar(grid, Position(0, 0), Position(4, 4))
        after_repr = grid.to_string()

        self.assertEqual(before_repr, after_repr)
        self.assertEqual(grid.get_cell(Position(1, 1)).terrain, TerrainType.ROAD)
        self.assertEqual(grid.get_cell(Position(2, 2)).terrain, TerrainType.ROUGH)
        self.assertTrue(grid.get_cell(Position(3, 3)).is_obstacle)

    def test_determinism(self) -> None:
        """Repeated A* runs on identical grid state yield identical results."""
        grid = Grid(rows=6, cols=6)
        grid.add_road(Position(1, 1))
        grid.add_rough_terrain(Position(2, 2))

        run1 = astar(grid, Position(0, 0), Position(5, 5))
        run2 = astar(grid, Position(0, 0), Position(5, 5))

        self.assertEqual(run1.path, run2.path)
        self.assertEqual(run1.total_cost, run2.total_cost)
        self.assertEqual(run1.visited_order, run2.visited_order)
        self.assertEqual(run1.nodes_explored, run2.nodes_explored)

    def test_class_wrapper(self) -> None:
        """AStarSearch class methods execute identically to astar function."""
        grid = Grid(rows=4, cols=4)
        start, goal = Position(0, 0), Position(3, 3)

        res1 = AStarSearch.search(grid, start, goal)
        res2 = AStarSearch()(grid, start, goal)

        self.assertTrue(res1.found)
        self.assertEqual(res1.path, res2.path)
        self.assertEqual(res1.total_cost, res2.total_cost)


if __name__ == "__main__":
    unittest.main()
