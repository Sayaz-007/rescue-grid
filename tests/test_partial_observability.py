"""
Comprehensive unit test suite for Partial Observability, Mystery States,
and Dynamic Replanning in RescueGrid (Phase 6).
Verifies KnowledgeGrid, ActualGrid, Sensor mechanisms, architectural isolation,
safe step-by-step vehicle locomotion, obstacle discovery, and replanning.
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
from simulation.sensor import Sensor
from simulation.rescue_simulator import (
    RescueSimulator,
    SimulationResult,
    SimulationStepRecord,
)
from algorithms.bfs import bfs
from algorithms.dfs import dfs
from algorithms.ucs import ucs
from algorithms.astar import astar


class TestKnowledgeGridMysteryStates(unittest.TestCase):
    """Test Suite 1: Mystery states, initialization, and KnowledgeGrid contracts."""

    def setUp(self) -> None:
        self.k_grid = KnowledgeGrid(rows=5, cols=5)

    def test_default_all_cells_unknown(self) -> None:
        """New KnowledgeGrid defaults to all cells having TerrainType.UNKNOWN."""
        self.assertEqual(self.k_grid.revealed_count, 0)
        self.assertEqual(self.k_grid.unknown_count, 25)
        for r in range(5):
            for c in range(5):
                pos = Position(c, r)
                cell = self.k_grid.get_cell(pos)
                self.assertEqual(cell.terrain, TerrainType.UNKNOWN)
                self.assertFalse(cell.is_walkable)
                self.assertEqual(cell.movement_cost, float("inf"))
                self.assertTrue(self.k_grid.is_unknown(pos))
                self.assertFalse(self.k_grid.is_revealed(pos))
                self.assertEqual(cell.get_symbol(), "?")

    def test_revealed_and_unknown_coordinate_queries(self) -> None:
        """Coordinate resolution handles both Position and integer pairs."""
        self.assertTrue(self.k_grid.is_unknown(0, 0))
        self.assertFalse(self.k_grid.is_revealed(0, 0))
        with self.assertRaises(IndexError):
            self.k_grid.is_revealed(10, 10)
        with self.assertRaises(IndexError):
            self.k_grid.is_unknown(Position(-1, 0))

    def test_mark_as_unknown(self) -> None:
        """Marking a cell as unknown resets its terrain, walkability, and revealed status."""
        actual = ActualGrid(rows=5, cols=5)
        pos = Position(2, 2)
        self.k_grid.reveal_cell(pos, actual)
        self.assertTrue(self.k_grid.is_revealed(pos))
        self.assertEqual(self.k_grid.revealed_count, 1)

        self.k_grid.mark_as_unknown(pos)
        self.assertFalse(self.k_grid.is_revealed(pos))
        self.assertTrue(self.k_grid.is_unknown(pos))
        self.assertEqual(self.k_grid.revealed_count, 0)
        self.assertEqual(self.k_grid.get_cell(pos).get_symbol(), "?")

    def test_ascii_rendering_displays_question_marks(self) -> None:
        """ASCII grid string renders '?' for unknown cells."""
        rendered = self.k_grid.to_string()
        self.assertIn("?", rendered)
        # 5 rows x 5 cols of '?'
        self.assertEqual(rendered.count("?"), 25)


class TestSensorDiscoveryMechanism(unittest.TestCase):
    """Test Suite 2: Proximity sensor discovery and Manhattan distance radius scanning."""

    def setUp(self) -> None:
        self.actual = ActualGrid(rows=6, cols=6)
        self.knowledge = self.actual.create_knowledge_grid()

    def test_sensor_radius_validation(self) -> None:
        """Sensor strictly validates radius argument."""
        with self.assertRaises(TypeError):
            Sensor(radius="2")  # type: ignore
        with self.assertRaises(TypeError):
            Sensor(radius=True)  # type: ignore
        with self.assertRaises(TypeError):
            Sensor(radius=1.5)  # type: ignore
        with self.assertRaises(ValueError):
            Sensor(radius=-1)

        sensor = Sensor(radius=2)
        self.assertEqual(sensor.radius, 2)
        sensor.set_radius(3)
        self.assertEqual(sensor.radius, 3)

    def test_sensor_radius_zero(self) -> None:
        """Radius 0 reveals only the current center cell."""
        sensor = Sensor(radius=0)
        center = Position(3, 3)
        revealed = sensor.sense(center, self.actual, self.knowledge)
        self.assertEqual(revealed, [center])
        self.assertEqual(self.knowledge.revealed_count, 1)
        self.assertTrue(self.knowledge.is_revealed(center))

    def test_sensor_radius_one(self) -> None:
        """Radius 1 reveals center and the 4 orthogonal cardinal neighbours."""
        sensor = Sensor(radius=1)
        center = Position(3, 3)
        revealed = sensor.sense(center, self.actual, self.knowledge)
        expected = {Position(3, 3), Position(3, 2), Position(3, 4), Position(2, 3), Position(4, 3)}
        self.assertEqual(set(revealed), expected)
        self.assertEqual(self.knowledge.revealed_count, 5)

    def test_sensor_radius_two(self) -> None:
        """Radius 2 reveals all cells with Manhattan distance <= 2 (13 cells in open grid)."""
        sensor = Sensor(radius=2)
        center = Position(3, 3)
        revealed = sensor.sense(center, self.actual, self.knowledge)
        self.assertEqual(len(revealed), 13)
        for pos in revealed:
            manhattan = abs(pos.x - center.x) + abs(pos.y - center.y)
            self.assertLessEqual(manhattan, 2)
            self.assertTrue(self.knowledge.is_revealed(pos))

    def test_sensor_boundary_handling(self) -> None:
        """Sensor respects grid boundaries at corners and edges without errors."""
        sensor = Sensor(radius=2)
        # Corner position (0, 0): bounds [0..2, 0..2] where x+y <= 2
        # (0,0), (1,0), (2,0), (0,1), (1,1), (0,2) => 6 cells
        corner = Position(0, 0)
        revealed = sensor.sense(corner, self.actual, self.knowledge)
        self.assertEqual(len(revealed), 6)
        for p in revealed:
            self.assertTrue(self.actual.is_inside(p))
            self.assertTrue(self.knowledge.is_inside(p))

    def test_sensor_detectable_positions(self) -> None:
        """get_detectable_positions returns correct coordinate list without modifying grid."""
        sensor = Sensor(radius=1)
        center = Position(1, 1)
        positions = sensor.get_detectable_positions(center, self.actual)
        self.assertEqual(len(positions), 5)
        self.assertEqual(self.knowledge.revealed_count, 0)  # unchanged


class TestTerrainRevelationAndPersistence(unittest.TestCase):
    """Test Suite 3: Cell attribute copying, hazard revelation, and persistence."""

    def setUp(self) -> None:
        self.actual = ActualGrid(rows=5, cols=5)
        self.actual.add_road(1, 1)
        self.actual.add_rough_terrain(2, 2)
        self.actual.add_collapsed_building(3, 3)
        self.actual.add_flood_zone(4, 4)
        self.actual.add_fire_zone(0, 4)
        self.knowledge = self.actual.create_knowledge_grid()

    def test_traversable_terrain_revelation(self) -> None:
        """Road and Rough terrain attributes are accurately transferred."""
        self.knowledge.reveal_cell(Position(1, 1), self.actual)
        cell_road = self.knowledge.get_cell(1, 1)
        self.assertEqual(cell_road.terrain, TerrainType.ROAD)
        self.assertTrue(cell_road.is_walkable)
        self.assertEqual(cell_road.movement_cost, 1.0)
        self.assertEqual(cell_road.get_symbol(), "=")

        self.knowledge.reveal_cell(Position(2, 2), self.actual)
        cell_rough = self.knowledge.get_cell(2, 2)
        self.assertEqual(cell_rough.terrain, TerrainType.ROUGH)
        self.assertTrue(cell_rough.is_walkable)
        self.assertEqual(cell_rough.movement_cost, 4.0)
        self.assertEqual(cell_rough.get_symbol(), ":")

    def test_blocked_hazard_revelation(self) -> None:
        """Hazardous terrains (Rubble, Water, FireZone) remain blocked upon discovery."""
        self.knowledge.reveal_cell(Position(3, 3), self.actual)
        cell_rubble = self.knowledge.get_cell(3, 3)
        self.assertEqual(cell_rubble.terrain, TerrainType.RUBBLE)
        self.assertFalse(cell_rubble.is_walkable)
        self.assertEqual(cell_rubble.movement_cost, float("inf"))
        self.assertEqual(cell_rubble.get_symbol(), "X")

        self.knowledge.reveal_cell(Position(4, 4), self.actual)
        cell_water = self.knowledge.get_cell(4, 4)
        self.assertEqual(cell_water.terrain, TerrainType.WATER)
        self.assertFalse(cell_water.is_walkable)
        self.assertEqual(cell_water.get_symbol(), "W")

        self.knowledge.reveal_cell(Position(0, 4), self.actual)
        cell_fire = self.knowledge.get_cell(0, 4)
        self.assertEqual(cell_fire.terrain, TerrainType.FIRE_ZONE)
        self.assertFalse(cell_fire.is_walkable)
        self.assertEqual(cell_fire.get_symbol(), "F")

    def test_information_persistence_across_scans(self) -> None:
        """Revealing an already revealed cell returns False and preserves data."""
        pos = Position(1, 1)
        is_first = self.knowledge.reveal_cell(pos, self.actual)
        self.assertTrue(is_first)

        is_second = self.knowledge.reveal_cell(pos, self.actual)
        self.assertFalse(is_second)
        self.assertEqual(self.knowledge.revealed_count, 1)
        self.assertEqual(self.knowledge.get_cell(pos).terrain, TerrainType.ROAD)


class TestPlannersExcludeUnknownCells(unittest.TestCase):
    """Test Suite 4: Route planners cannot traverse unrevealed unknown mystery states."""

    def setUp(self) -> None:
        # 5x5 grid with start (0, 0) and goal (4, 4)
        self.actual = ActualGrid(rows=5, cols=5, default_terrain=TerrainType.NORMAL)
        self.knowledge = self.actual.create_knowledge_grid(default_terrain=TerrainType.UNKNOWN)
        self.start = Position(0, 0)
        self.goal = Position(4, 4)

    def test_astar_fails_when_goal_is_unknown(self) -> None:
        """A* returns found=False because UNKNOWN goal is non-walkable."""
        res = astar(self.knowledge, self.start, self.goal)
        self.assertFalse(res.found)
        self.assertEqual(res.path, [])

    def test_all_planners_fail_on_all_unknown_grid(self) -> None:
        """BFS, DFS, UCS, and A* all fail to find a path across an unknown grid."""
        for planner in [bfs, dfs, ucs, astar]:
            res = planner(self.knowledge, self.start, self.goal)
            self.assertFalse(res.found, f"{res.algorithm_name} must not find route through unknown cells.")
            self.assertEqual(res.path, [])

    def test_planners_cannot_cross_unknown_barrier(self) -> None:
        """A corridor interrupted by an UNKNOWN cell cannot be crossed by A*."""
        # Reveal path from (0,0) to (2,0) and (4,0)
        # Position (3, 0) is left UNKNOWN
        for c in [0, 1, 2, 4]:
            self.knowledge.reveal_cell(Position(c, 0), self.actual)

        res = astar(self.knowledge, Position(0, 0), Position(4, 0))
        self.assertFalse(res.found)

        # Now reveal the missing cell (3, 0)
        self.knowledge.reveal_cell(Position(3, 0), self.actual)
        res_after = astar(self.knowledge, Position(0, 0), Position(4, 0))
        self.assertTrue(res_after.found)
        self.assertEqual(len(res_after.path), 5)


class TestArchitecturalSafetyAndIsolation(unittest.TestCase):
    """Test Suite 5: Ground truth isolation and protection from planning algorithms."""

    def test_actual_grid_not_passed_to_planner(self) -> None:
        """Simulator only supplies KnowledgeGrid to the route planner."""
        actual = ActualGrid(rows=4, cols=4)
        knowledge = actual.create_knowledge_grid()
        # Plant hidden obstacle in ActualGrid
        actual.add_flood_zone(2, 2)

        supplied_grids = []

        def spy_planner(grid, start, goal):
            supplied_grids.append(grid)
            return astar(grid, start, goal)

        sim = RescueSimulator(actual_grid=actual, knowledge_grid=knowledge, planner_func=spy_planner)
        sim.run(Position(0, 0), Position(0, 1))

        self.assertGreater(len(supplied_grids), 0)
        for g in supplied_grids:
            self.assertIs(g, knowledge)
            self.assertIsNot(g, actual)
            self.assertIsInstance(g, KnowledgeGrid)

    def test_hidden_obstacle_remains_hidden_outside_sensor_range(self) -> None:
        """Obstacle at (5, 5) remains unknown when vehicle is at (0, 0) with radius 2."""
        actual = ActualGrid(rows=7, cols=7)
        actual.add_flood_zone(5, 5)
        knowledge = actual.create_knowledge_grid()

        sensor = Sensor(radius=2)
        sensor.sense(Position(0, 0), actual, knowledge)

        self.assertFalse(knowledge.is_revealed(5, 5))
        self.assertTrue(knowledge.is_unknown(5, 5))
        self.assertEqual(knowledge.get_cell(5, 5).terrain, TerrainType.UNKNOWN)


class TestVehicleLocomotionAndSafetyInvariants(unittest.TestCase):
    """Test Suite 6: Step-by-step movement, contiguous traversal, and safety invariants."""

    def setUp(self) -> None:
        self.actual = ActualGrid(rows=5, cols=5, default_terrain=TerrainType.NORMAL)
        self.knowledge = self.actual.create_knowledge_grid()
        # Reveal a contiguous strip
        for c in range(5):
            self.knowledge.reveal_cell(Position(c, 0), self.actual)

    def test_step_by_step_contiguous_locomotion(self) -> None:
        """Vehicle moves strictly 1 cell per step along cardinal adjacencies."""
        sim = RescueSimulator(actual_grid=self.actual, knowledge_grid=self.knowledge)
        result = sim.run(Position(0, 0), Position(4, 0))

        self.assertTrue(result.destination_reached)
        self.assertEqual(result.total_steps, 4)
        self.assertEqual(len(result.traversed_path), 5)

        for i in range(len(result.traversed_path) - 1):
            p1 = result.traversed_path[i]
            p2 = result.traversed_path[i + 1]
            dist = abs(p1.x - p2.x) + abs(p1.y - p2.y)
            self.assertEqual(dist, 1, f"Move from {p1} to {p2} is not a valid 1-step cardinal move.")

    def test_vehicle_never_enters_actually_blocked_cell(self) -> None:
        """Vehicle stops and replans before entering an actually blocked cell."""
        # Route appears clear in knowledge grid
        for c in range(5):
            cell = self.knowledge.get_cell(c, 0)
            cell.set_terrain(TerrainType.ROAD)
            cell.set_walkable(True)
            self.knowledge._revealed.add(Position(c, 0))

        # In ActualGrid, cell (2, 0) is blocked by RUBBLE
        self.actual.add_collapsed_building(2, 0)

        # Alternative route around it (row 1)
        for c in range(5):
            self.actual.add_road(c, 1)
            cell = self.knowledge.get_cell(c, 1)
            cell.set_terrain(TerrainType.ROAD)
            cell.set_walkable(True)
            self.knowledge._revealed.add(Position(c, 1))

        sim = RescueSimulator(actual_grid=self.actual, knowledge_grid=self.knowledge, sensor=Sensor(radius=1))
        result = sim.run(Position(0, 0), Position(4, 0))

        self.assertTrue(result.destination_reached)
        self.assertNotIn(Position(2, 0), result.traversed_path)
        # Verify that every cell the vehicle stepped on was physically walkable
        for pos in result.traversed_path:
            self.assertTrue(self.actual.is_walkable(pos), f"Vehicle entered blocked cell at {pos}!")


class TestDynamicReplanning(unittest.TestCase):
    """Test Suite 7: Dynamic route invalidation, obstacle detection, and replanning."""

    def test_replanning_triggered_upon_discovering_obstacle(self) -> None:
        """Vehicle replans route when sensor discovers an obstacle ahead."""
        actual = ActualGrid(rows=4, cols=6, default_terrain=TerrainType.NORMAL)
        # Direct route along row 0
        for c in range(6):
            actual.add_road(c, 0)
        # Block row 0 at (3, 0)
        actual.add_collapsed_building(3, 0)

        # Bypass route along row 1
        for c in range(6):
            actual.add_road(c, 1)
        actual.add_road(0, 1)
        actual.add_road(5, 1)

        knowledge = actual.create_knowledge_grid(default_terrain=TerrainType.UNKNOWN)
        # Initial knowledge has row 0 and row 1 believed to be open roads
        for c in range(6):
            for r in [0, 1]:
                pos = Position(c, r)
                cell = knowledge.get_cell(pos)
                cell.set_terrain(TerrainType.ROAD)
                cell.set_walkable(True)
                knowledge._revealed.add(pos)

        sim = RescueSimulator(actual_grid=actual, knowledge_grid=knowledge, sensor=Sensor(radius=2))
        result = sim.run(Position(0, 0), Position(5, 0))

        self.assertTrue(result.destination_reached)
        self.assertGreaterEqual(result.replanning_count, 1)
        self.assertNotIn(Position(3, 0), result.traversed_path)

    def test_simulation_failure_when_no_feasible_route_exists(self) -> None:
        """Simulator terminates gracefully when destination is completely unreachable."""
        actual = ActualGrid(rows=4, cols=4, default_terrain=TerrainType.NORMAL)
        # Ring of rubble completely surrounding destination (3, 3)
        actual.add_collapsed_building(2, 3)
        actual.add_collapsed_building(3, 2)
        actual.add_collapsed_building(2, 2)

        knowledge = actual.create_knowledge_grid(default_terrain=TerrainType.NORMAL)
        # In knowledge, goal (3, 3) is initially thought to be reachable
        knowledge.get_cell(3, 3).set_walkable(True)

        sim = RescueSimulator(actual_grid=actual, knowledge_grid=knowledge, sensor=Sensor(radius=2))
        result = sim.run(Position(0, 0), Position(3, 3))

        self.assertFalse(result.destination_reached)
        self.assertIsNotNone(result.failure_reason)


class TestCostAccountingAndMetrics(unittest.TestCase):
    """Test Suite 8: Cost accounting on ActualGrid and performance metrics tracking."""

    def test_cost_calculated_on_actual_grid(self) -> None:
        """Actual movement cost uses ActualGrid cell costs, not KnowledgeGrid."""
        actual = ActualGrid(rows=3, cols=3, default_terrain=TerrainType.NORMAL)
        # In actual grid, (1, 0) has cost 4.0 (Rough), (2, 0) has cost 1.0 (Road)
        actual.add_rough_terrain(1, 0)
        actual.add_road(2, 0)

        knowledge = actual.create_knowledge_grid()
        # In knowledge grid, artificially mark (1, 0) and (2, 0) as Road (cost 1.0)
        for pos in [Position(0, 0), Position(1, 0), Position(2, 0)]:
            cell = knowledge.get_cell(pos)
            cell.set_terrain(TerrainType.ROAD)
            cell.set_walkable(True)
            knowledge._revealed.add(pos)

        sim = RescueSimulator(actual_grid=actual, knowledge_grid=knowledge)
        result = sim.run(Position(0, 0), Position(2, 0))

        self.assertTrue(result.destination_reached)
        self.assertEqual(result.total_steps, 2)
        # Cost is entering (1, 0) [cost 4] + entering (2, 0) [cost 1] = 5.0
        self.assertEqual(result.actual_cost, 5.0)

    def test_start_equals_goal_trivial_metrics(self) -> None:
        """When start equals goal, zero steps and zero cost are recorded."""
        actual = ActualGrid(rows=3, cols=3)
        knowledge = actual.create_knowledge_grid()
        sim = RescueSimulator(actual_grid=actual, knowledge_grid=knowledge)
        result = sim.run(Position(1, 1), Position(1, 1))

        self.assertTrue(result.destination_reached)
        self.assertEqual(result.total_steps, 0)
        self.assertEqual(result.actual_cost, 0.0)
        self.assertEqual(result.replanning_count, 0)


class TestSimulationReproducibility(unittest.TestCase):
    """Test Suite 9: Deterministic behavior across repeated executions."""

    def test_identical_runs_produce_identical_metrics(self) -> None:
        """Running the simulation twice on identical instances produces identical results."""
        def make_setup():
            actual = ActualGrid(rows=4, cols=6)
            for c in range(6):
                actual.add_road(c, 1)
            actual.add_collapsed_building(3, 1)
            for c in range(6):
                actual.add_road(c, 2)
            actual.add_road(0, 2)
            actual.add_road(5, 2)
            knowledge = actual.create_knowledge_grid()
            for c in range(6):
                for r in [1, 2]:
                    p = Position(c, r)
                    cell = knowledge.get_cell(p)
                    cell.set_terrain(TerrainType.ROAD)
                    cell.set_walkable(True)
                    knowledge._revealed.add(p)
            return actual, knowledge

        act1, kno1 = make_setup()
        sim1 = RescueSimulator(act1, kno1)
        res1 = sim1.run(Position(0, 1), Position(5, 1))

        act2, kno2 = make_setup()
        sim2 = RescueSimulator(act2, kno2)
        res2 = sim2.run(Position(0, 1), Position(5, 1))

        self.assertEqual(res1.destination_reached, res2.destination_reached)
        self.assertEqual(res1.total_steps, res2.total_steps)
        self.assertEqual(res1.actual_cost, res2.actual_cost)
        self.assertEqual(res1.replanning_count, res2.replanning_count)
        self.assertEqual(res1.traversed_path, res2.traversed_path)


if __name__ == "__main__":
    unittest.main()
