"""
Unit test suite for the RescueGrid 2D environment module.
Verifies Grid, Cell, TerrainType, boundary safety, and neighbour calculations.
"""

import os
import sys
import unittest

# Ensure the root project directory is on the module search path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from models.position import Position
from environment.cell import Cell, TerrainType
from environment.grid import Grid


class TestGridCreation(unittest.TestCase):
    """Test 1: Grid creation, configurable dimensions, and default cell states."""

    def test_grid_initialization(self) -> None:
        grid = Grid(rows=6, cols=8)
        self.assertEqual(grid.rows, 6)
        self.assertEqual(grid.cols, 8)
        self.assertEqual(grid.width, 8)
        self.assertEqual(grid.height, 6)
        self.assertEqual(grid.total_cells, 48)

        # Verify all cells are initialized to default state
        for r in range(6):
            for c in range(8):
                cell = grid.get_cell(c, r)
                self.assertEqual(cell.position, Position(c, r))
                self.assertEqual(cell.terrain, TerrainType.NORMAL)
                self.assertFalse(cell.is_obstacle)
                self.assertTrue(cell.is_walkable)


class TestInvalidGridDimensions(unittest.TestCase):
    """Test 2: Validation of grid dimension parameters."""

    def test_non_positive_dimensions(self) -> None:
        with self.assertRaises(ValueError):
            Grid(rows=0, cols=5)
        with self.assertRaises(ValueError):
            Grid(rows=5, cols=0)
        with self.assertRaises(ValueError):
            Grid(rows=-3, cols=10)
        with self.assertRaises(ValueError):
            Grid(rows=10, cols=-2)

    def test_non_integer_dimensions(self) -> None:
        with self.assertRaises(TypeError):
            Grid(rows="10", cols=10)  # type: ignore
        with self.assertRaises(TypeError):
            Grid(rows=10, cols=5.5)  # type: ignore
        with self.assertRaises(TypeError):
            Grid(rows=True, cols=10)  # type: ignore


class TestPositionBoundaryValidation(unittest.TestCase):
    """Test 3: Checking coordinates inside vs outside grid boundaries."""

    def test_is_inside(self) -> None:
        grid = Grid(rows=10, cols=15)

        # Valid boundary coordinates
        self.assertTrue(grid.is_inside(Position(0, 0)))
        self.assertTrue(grid.is_inside(Position(14, 9)))
        self.assertTrue(grid.is_inside(0, 0))
        self.assertTrue(grid.is_inside(14, 9))
        self.assertTrue(grid.is_inside(Position(7, 4)))

        # Out-of-bounds coordinates
        self.assertFalse(grid.is_inside(Position(-1, 0)))
        self.assertFalse(grid.is_inside(Position(0, -1)))
        self.assertFalse(grid.is_inside(Position(15, 0)))
        self.assertFalse(grid.is_inside(Position(0, 10)))
        self.assertFalse(grid.is_inside(Position(100, 100)))
        self.assertFalse(grid.is_inside(-1, 5))
        self.assertFalse(grid.is_inside(5, -1))
        self.assertFalse(grid.is_inside(15, 5))
        self.assertFalse(grid.is_inside(5, 10))

    def test_invalid_types_for_is_inside(self) -> None:
        grid = Grid(rows=5, cols=5)
        self.assertFalse(grid.is_inside("invalid", 2))  # type: ignore
        self.assertFalse(grid.is_inside(None))  # type: ignore


class TestCellRetrieval(unittest.TestCase):
    """Test 4: Retrieving Cell instances by Position or coordinate pairs."""

    def test_get_cell_variations(self) -> None:
        grid = Grid(rows=8, cols=12)

        # Retrieval by Position object
        pos = Position(5, 3)
        cell1 = grid.get_cell(pos)
        self.assertEqual(cell1.position, Position(5, 3))
        self.assertEqual(cell1.x, 5)
        self.assertEqual(cell1.y, 3)
        self.assertEqual(cell1.col, 5)
        self.assertEqual(cell1.row, 3)

        # Retrieval by (x, y) integers
        cell2 = grid.get_cell(5, 3)
        self.assertIs(cell1, cell2, "get_cell(pos) and get_cell(x, y) must return identical Cell instance")

        # Retrieval by row and column
        cell3 = grid.get_cell_by_rc(row=3, col=5)
        self.assertIs(cell1, cell3)


class TestObstaclePlacement(unittest.TestCase):
    """Test 5: Placing obstacles on cells and checking state updates."""

    def test_add_obstacle(self) -> None:
        grid = Grid(rows=5, cols=5)
        target = Position(2, 3)

        self.assertFalse(grid.has_obstacle(target))
        self.assertTrue(grid.is_walkable(target))

        grid.add_obstacle(target)

        self.assertTrue(grid.has_obstacle(target))
        self.assertFalse(grid.is_walkable(target))

        cell = grid.get_cell(target)
        self.assertTrue(cell.is_obstacle)
        self.assertTrue(cell.has_obstacle())
        self.assertFalse(cell.is_walkable)


class TestObstacleRemoval(unittest.TestCase):
    """Test 6: Removing obstacles and restoring walkability."""

    def test_remove_obstacle(self) -> None:
        grid = Grid(rows=5, cols=5)
        target = Position(1, 4)

        grid.add_obstacle(target)
        self.assertTrue(grid.has_obstacle(target))
        self.assertFalse(grid.is_walkable(target))

        grid.remove_obstacle(target)
        self.assertFalse(grid.has_obstacle(target))
        self.assertTrue(grid.is_walkable(target))

        cell = grid.get_cell(target)
        self.assertFalse(cell.is_obstacle)
        self.assertTrue(cell.is_walkable)


class TestWalkabilityChecks(unittest.TestCase):
    """Test 7: Verification of cell walkability and boundary safety."""

    def test_walkability_states(self) -> None:
        grid = Grid(rows=4, cols=4)
        pos = Position(2, 2)

        self.assertTrue(grid.is_walkable(pos))

        # Explicitly set walkable to False
        grid.set_walkable(pos, False)
        self.assertFalse(grid.is_walkable(pos))

        # Explicitly set walkable to True
        grid.set_walkable(pos, True)
        self.assertTrue(grid.is_walkable(pos))

    def test_walkability_outside_grid(self) -> None:
        grid = Grid(rows=4, cols=4)
        # Out-of-bounds positions must return False safely without raising exceptions
        self.assertFalse(grid.is_walkable(Position(-1, 0)))
        self.assertFalse(grid.is_walkable(Position(4, 4)))
        self.assertFalse(grid.is_walkable(10, 10))


class TestTerrainUpdates(unittest.TestCase):
    """Test 8: Updating surface terrain and disaster scenario helpers."""

    def test_set_terrain(self) -> None:
        grid = Grid(rows=5, cols=5)
        pos = Position(3, 1)

        grid.set_terrain(pos, TerrainType.ROAD)
        self.assertEqual(grid.get_cell(pos).terrain, TerrainType.ROAD)

        grid.set_terrain(3, 1, TerrainType.WATER)
        self.assertEqual(grid.get_cell(pos).terrain, TerrainType.WATER)

    def test_disaster_helpers(self) -> None:
        grid = Grid(rows=6, cols=6)

        # 1. Collapsed building: rubble + blocked
        cb_pos = Position(1, 1)
        grid.add_collapsed_building(cb_pos)
        self.assertEqual(grid.get_cell(cb_pos).terrain, TerrainType.RUBBLE)
        self.assertTrue(grid.has_obstacle(cb_pos))
        self.assertFalse(grid.is_walkable(cb_pos))

        # 2. Fire zone: fire + blocked
        fire_pos = Position(2, 2)
        grid.add_fire_zone(fire_pos)
        self.assertEqual(grid.get_cell(fire_pos).terrain, TerrainType.FIRE_ZONE)
        self.assertTrue(grid.has_obstacle(fire_pos))
        self.assertFalse(grid.is_walkable(fire_pos))

        # 3. Flood zone: water + blocked
        flood_pos = Position(3, 3)
        grid.add_flood_zone(flood_pos)
        self.assertEqual(grid.get_cell(flood_pos).terrain, TerrainType.WATER)
        self.assertTrue(grid.has_obstacle(flood_pos))
        self.assertFalse(grid.is_walkable(flood_pos))

        # 4. Open road: road + walkable
        road_pos = Position(4, 4)
        grid.add_road(road_pos)
        self.assertEqual(grid.get_cell(road_pos).terrain, TerrainType.ROAD)
        self.assertFalse(grid.has_obstacle(road_pos))
        self.assertTrue(grid.is_walkable(road_pos))

    def test_invalid_terrain_type(self) -> None:
        grid = Grid(rows=3, cols=3)
        with self.assertRaises(TypeError):
            grid.set_terrain(Position(0, 0), "NotATerrainType")  # type: ignore


class TestNeighbourRetrieval(unittest.TestCase):
    """Test 9: Cardinal 4-direction neighbour retrieval and walkability filtering."""

    def test_interior_neighbours(self) -> None:
        grid = Grid(rows=5, cols=5)
        center = Position(2, 2)

        neighbours = grid.get_neighbours(center)
        self.assertEqual(len(neighbours), 4)

        expected = {
            Position(2, 1),  # UP
            Position(2, 3),  # DOWN
            Position(1, 2),  # LEFT
            Position(3, 2),  # RIGHT
        }
        self.assertEqual(set(neighbours), expected)

    def test_walkable_neighbours_filtering(self) -> None:
        grid = Grid(rows=5, cols=5)
        center = Position(2, 2)

        # Place obstacles on UP and RIGHT
        grid.add_obstacle(Position(2, 1))  # UP
        grid.add_obstacle(Position(3, 2))  # RIGHT

        # All neighbours includes blocked cells
        all_neighbours = grid.get_neighbours(center, walkable_only=False)
        self.assertEqual(len(all_neighbours), 4)

        # Walkable neighbours excludes blocked cells
        walkable_neighbours = grid.get_walkable_neighbours(center)
        self.assertEqual(len(walkable_neighbours), 2)

        expected_walkable = {
            Position(2, 3),  # DOWN
            Position(1, 2),  # LEFT
        }
        self.assertEqual(set(walkable_neighbours), expected_walkable)


class TestBoundaryNeighbourBehaviour(unittest.TestCase):
    """Test 10: Boundary behaviour ensuring out-of-grid neighbours are excluded."""

    def test_corners(self) -> None:
        grid = Grid(rows=5, cols=5)

        # Top-left corner (0, 0): UP and LEFT are outside
        tl_neighbours = grid.get_neighbours(Position(0, 0))
        self.assertEqual(len(tl_neighbours), 2)
        self.assertEqual(set(tl_neighbours), {Position(0, 1), Position(1, 0)})

        # Bottom-right corner (4, 4): DOWN and RIGHT are outside
        br_neighbours = grid.get_neighbours(Position(4, 4))
        self.assertEqual(len(br_neighbours), 2)
        self.assertEqual(set(br_neighbours), {Position(4, 3), Position(3, 4)})

    def test_edges(self) -> None:
        grid = Grid(rows=5, cols=5)

        # Top edge (2, 0): UP is outside
        top_neighbours = grid.get_neighbours(Position(2, 0))
        self.assertEqual(len(top_neighbours), 3)
        self.assertEqual(set(top_neighbours), {Position(2, 1), Position(1, 0), Position(3, 0)})

        # Left edge (0, 2): LEFT is outside
        left_neighbours = grid.get_neighbours(Position(0, 2))
        self.assertEqual(len(left_neighbours), 3)
        self.assertEqual(set(left_neighbours), {Position(0, 1), Position(0, 3), Position(1, 2)})


class TestInvalidCoordinateHandling(unittest.TestCase):
    """Test 11: Safety and exception behaviour for out-of-bounds coordinate queries."""

    def test_out_of_bounds_retrievals(self) -> None:
        grid = Grid(rows=5, cols=5)

        with self.assertRaises(IndexError):
            grid.get_cell(Position(5, 5))
        with self.assertRaises(IndexError):
            grid.get_cell(Position(-1, 2))
        with self.assertRaises(IndexError):
            grid.get_cell(2, -1)
        with self.assertRaises(IndexError):
            grid.get_cell(10, 2)

    def test_out_of_bounds_mutations(self) -> None:
        grid = Grid(rows=5, cols=5)

        with self.assertRaises(IndexError):
            grid.add_obstacle(Position(99, 99))
        with self.assertRaises(IndexError):
            grid.remove_obstacle(Position(-2, -2))
        with self.assertRaises(IndexError):
            grid.get_neighbours(Position(10, 10))

    def test_invalid_types_for_get_cell(self) -> None:
        grid = Grid(rows=5, cols=5)
        with self.assertRaises(TypeError):
            grid.get_cell("not_a_pos", 2)  # type: ignore


class TestGridRepresentation(unittest.TestCase):
    """Test 12: Visual representation, ASCII rendering, and cell symbols."""

    def test_grid_string_rendering(self) -> None:
        grid = Grid(rows=3, cols=3)
        grid.add_road(Position(1, 0))
        grid.add_obstacle(Position(1, 1))
        grid.add_flood_zone(Position(2, 2))

        rendered = grid.to_string()
        self.assertIsInstance(rendered, str)
        self.assertTrue(len(rendered) > 0)

        # Check that row indices are in output
        self.assertIn(" 0 |", rendered)
        self.assertIn(" 1 |", rendered)
        self.assertIn(" 2 |", rendered)

        # Symbols check
        self.assertEqual(grid.get_cell(1, 0).get_symbol(), "=")
        self.assertEqual(grid.get_cell(1, 1).get_symbol(), "#")
        self.assertEqual(grid.get_cell(2, 2).get_symbol(), "W")
        self.assertEqual(grid.get_cell(0, 0).get_symbol(), ".")

        # __repr__ check
        self.assertEqual(repr(grid), "Grid(rows=3, cols=3)")


class TestGridValidationAndTraversalSafety(unittest.TestCase):
    """Test Suite 13: Phase 2.1 Refinements for strict validation, terrain consistency, and traversal safety."""

    def test_remove_obstacle_from_fire_zone(self) -> None:
        """Removing an obstacle from a fire zone must NOT make the cell walkable."""
        grid = Grid(rows=5, cols=5)
        pos = Position(2, 2)

        grid.add_fire_zone(pos, blocked=True)
        self.assertEqual(grid.get_cell(pos).terrain, TerrainType.FIRE_ZONE)
        self.assertTrue(grid.has_obstacle(pos))
        self.assertFalse(grid.is_walkable(pos))

        # Remove the obstacle
        grid.remove_obstacle(pos)
        self.assertFalse(grid.has_obstacle(pos), "Obstacle flag must be cleared")
        self.assertFalse(grid.is_walkable(pos), "Fire zone must remain blocked/non-walkable even without obstacle")

    def test_remove_obstacle_from_flood_zone(self) -> None:
        """Removing an obstacle from a flooded area must NOT make the cell walkable."""
        grid = Grid(rows=5, cols=5)
        pos = Position(1, 3)

        grid.add_flood_zone(pos, blocked=True)
        self.assertEqual(grid.get_cell(pos).terrain, TerrainType.WATER)
        self.assertTrue(grid.has_obstacle(pos))
        self.assertFalse(grid.is_walkable(pos))

        # Remove the obstacle
        grid.remove_obstacle(pos)
        self.assertFalse(grid.has_obstacle(pos), "Obstacle flag must be cleared")
        self.assertFalse(grid.is_walkable(pos), "Water/flood zone must remain blocked/non-walkable")

    def test_remove_obstacle_from_rubble(self) -> None:
        """Removing an obstacle from rubble must NOT make the cell walkable."""
        grid = Grid(rows=5, cols=5)
        pos = Position(0, 4)

        grid.add_collapsed_building(pos)
        self.assertEqual(grid.get_cell(pos).terrain, TerrainType.RUBBLE)
        self.assertTrue(grid.has_obstacle(pos))
        self.assertFalse(grid.is_walkable(pos))

        # Remove the obstacle
        grid.remove_obstacle(pos)
        self.assertFalse(grid.has_obstacle(pos), "Obstacle flag must be cleared")
        self.assertFalse(grid.is_walkable(pos), "Rubble must remain blocked/non-walkable")

    def test_invalid_default_terrain(self) -> None:
        """Grid constructor must reject non-TerrainType default_terrain values."""
        with self.assertRaises(TypeError):
            Grid(rows=5, cols=5, default_terrain="INVALID")  # type: ignore
        with self.assertRaises(TypeError):
            Grid(rows=5, cols=5, default_terrain=123)  # type: ignore
        with self.assertRaises(TypeError):
            Grid(rows=5, cols=5, default_terrain=None)  # type: ignore

    def test_invalid_cell_constructor_arguments(self) -> None:
        """Cell constructor must strictly validate position, terrain, is_obstacle, and is_walkable types."""
        pos = Position(0, 0)

        with self.assertRaises(TypeError):
            Cell("not_a_pos")  # type: ignore
        with self.assertRaises(TypeError):
            Cell(pos, terrain="not_a_terrain")  # type: ignore
        with self.assertRaises(TypeError):
            Cell(pos, is_obstacle="True")  # type: ignore
        with self.assertRaises(TypeError):
            Cell(pos, is_obstacle=1)  # type: ignore
        with self.assertRaises(TypeError):
            Cell(pos, is_walkable="False")  # type: ignore
        with self.assertRaises(TypeError):
            Cell(pos, is_walkable=0)  # type: ignore

    def test_contradictory_obstacle_walkability_states(self) -> None:
        """Contradictory obstacle/walkability combinations must be rejected with ValueError."""
        pos = Position(1, 1)

        # Constructor contradiction
        with self.assertRaises(ValueError):
            Cell(pos, is_obstacle=True, is_walkable=True)

        # Cell direct mutator contradiction
        cell = Cell(pos, is_obstacle=True)
        with self.assertRaises(ValueError):
            cell.set_walkable(True)

        # Grid mutator contradiction
        grid = Grid(rows=5, cols=5)
        grid.add_obstacle(pos)
        with self.assertRaises(ValueError):
            grid.set_walkable(pos, True)
        with self.assertRaises(ValueError):
            grid.set_walkable(1, 1, True)

    def test_float_coordinates_rejected(self) -> None:
        """Float coordinates must be strictly rejected with TypeError."""
        grid = Grid(rows=5, cols=5)

        with self.assertRaises(TypeError):
            grid.get_cell(2.5, 3)  # type: ignore
        with self.assertRaises(TypeError):
            grid.get_cell(2, 3.5)  # type: ignore
        with self.assertRaises(TypeError):
            grid.get_cell_by_rc(2.5, 3)  # type: ignore
        with self.assertRaises(TypeError):
            grid.add_obstacle(2.5, 3)  # type: ignore
        with self.assertRaises(TypeError):
            grid.remove_obstacle(2.5, 3)  # type: ignore
        with self.assertRaises(TypeError):
            grid.set_terrain(2.5, 3, TerrainType.ROAD)  # type: ignore
        with self.assertRaises(TypeError):
            grid.set_walkable(2.5, 3, False)  # type: ignore
        with self.assertRaises(TypeError):
            grid.get_neighbours(2.5, 3)  # type: ignore

        self.assertFalse(grid.is_inside(2.5, 3))  # type: ignore
        self.assertFalse(grid.is_walkable(2.5, 3))  # type: ignore

    def test_string_coordinates_rejected(self) -> None:
        """Numeric strings must NOT be silently converted via int(); they must raise TypeError."""
        grid = Grid(rows=5, cols=5)

        with self.assertRaises(TypeError):
            grid.get_cell("2", "3")  # type: ignore
        with self.assertRaises(TypeError):
            grid.get_cell(2, "3")  # type: ignore
        with self.assertRaises(TypeError):
            grid.get_cell_by_rc("2", "3")  # type: ignore
        with self.assertRaises(TypeError):
            grid.add_obstacle("2", "3")  # type: ignore
        with self.assertRaises(TypeError):
            grid.remove_obstacle("2", "3")  # type: ignore
        with self.assertRaises(TypeError):
            grid.set_terrain("2", "3", TerrainType.ROAD)  # type: ignore
        with self.assertRaises(TypeError):
            grid.set_walkable("2", "3", False)  # type: ignore
        with self.assertRaises(TypeError):
            grid.get_neighbours("2", "3")  # type: ignore

        self.assertFalse(grid.is_inside("2", "3"))  # type: ignore
        self.assertFalse(grid.is_walkable("2", "3"))  # type: ignore

    def test_boolean_coordinates_rejected(self) -> None:
        """Boolean coordinates (True/False) must be rejected with TypeError (not treated as 1/0)."""
        grid = Grid(rows=5, cols=5)

        with self.assertRaises(TypeError):
            grid.get_cell(True, 2)  # type: ignore
        with self.assertRaises(TypeError):
            grid.get_cell(2, False)  # type: ignore
        with self.assertRaises(TypeError):
            grid.get_cell_by_rc(True, 2)  # type: ignore
        with self.assertRaises(TypeError):
            grid.add_obstacle(True, False)  # type: ignore
        with self.assertRaises(TypeError):
            grid.remove_obstacle(True, False)  # type: ignore
        with self.assertRaises(TypeError):
            grid.set_terrain(True, 2, TerrainType.ROAD)  # type: ignore
        with self.assertRaises(TypeError):
            grid.set_walkable(True, 2, False)  # type: ignore
        with self.assertRaises(TypeError):
            grid.get_neighbours(True, 2)  # type: ignore

        self.assertFalse(grid.is_inside(True, 2))  # type: ignore
        self.assertFalse(grid.is_walkable(True, 2))  # type: ignore

    def test_invalid_terrain_updates(self) -> None:
        """Updating terrain with non-TerrainType values must raise TypeError."""
        grid = Grid(rows=5, cols=5)
        pos = Position(1, 1)
        cell = grid.get_cell(pos)

        with self.assertRaises(TypeError):
            cell.set_terrain("NOT_TERRAIN")  # type: ignore
        with self.assertRaises(TypeError):
            grid.set_terrain(pos, "NOT_TERRAIN")  # type: ignore
        with self.assertRaises(TypeError):
            grid.set_terrain(1, 1, "NOT_TERRAIN")  # type: ignore
        with self.assertRaises(TypeError):
            grid.set_terrain(1, 1, 999)  # type: ignore
        with self.assertRaises(TypeError):
            grid.set_terrain(1, 1, None)  # type: ignore

    def test_changing_terrain_walkability_behaviour(self) -> None:
        """Changing terrain must correctly update default walkability while respecting active obstacles."""
        grid = Grid(rows=5, cols=5)
        pos = Position(2, 2)
        cell = grid.get_cell(pos)

        # 1. Normal terrain starts walkable
        self.assertEqual(cell.terrain, TerrainType.NORMAL)
        self.assertTrue(cell.is_walkable)

        # 2. Transition to FIRE_ZONE: automatically becomes non-walkable
        grid.set_terrain(pos, TerrainType.FIRE_ZONE)
        self.assertEqual(cell.terrain, TerrainType.FIRE_ZONE)
        self.assertFalse(cell.is_walkable)

        # 3. Transition to ROAD: automatically becomes walkable
        grid.set_terrain(pos, TerrainType.ROAD)
        self.assertEqual(cell.terrain, TerrainType.ROAD)
        self.assertTrue(cell.is_walkable)

        # 4. Transition to WATER: automatically becomes non-walkable
        grid.set_terrain(pos, TerrainType.WATER)
        self.assertEqual(cell.terrain, TerrainType.WATER)
        self.assertFalse(cell.is_walkable)

        # 5. Transition to RUBBLE: automatically becomes non-walkable
        grid.set_terrain(pos, TerrainType.RUBBLE)
        self.assertEqual(cell.terrain, TerrainType.RUBBLE)
        self.assertFalse(cell.is_walkable)

        # 6. Transition back to ROAD: becomes walkable
        grid.set_terrain(pos, TerrainType.ROAD)
        self.assertTrue(cell.is_walkable)

        # 7. Add obstacle to ROAD: non-walkable
        grid.add_obstacle(pos)
        self.assertTrue(cell.is_obstacle)
        self.assertFalse(cell.is_walkable)

        # 8. Change terrain to NORMAL while obstacle is present: must remain non-walkable
        grid.set_terrain(pos, TerrainType.NORMAL)
        self.assertTrue(cell.is_obstacle)
        self.assertFalse(cell.is_walkable)

        # 9. Change terrain to WATER while obstacle is present: must remain non-walkable
        grid.set_terrain(pos, TerrainType.WATER)
        self.assertTrue(cell.is_obstacle)
        self.assertFalse(cell.is_walkable)

        # 10. Remove obstacle while terrain is WATER: obstacle is cleared, but cell remains non-walkable
        grid.remove_obstacle(pos)
        self.assertFalse(cell.is_obstacle)
        self.assertFalse(cell.is_walkable)

        # 11. Change terrain to ROAD: becomes walkable
        grid.set_terrain(pos, TerrainType.ROAD)
        self.assertFalse(cell.is_obstacle)
        self.assertTrue(cell.is_walkable)

    def test_existing_valid_grid_operations(self) -> None:
        """Comprehensive verification of standard grid setup, obstacles, roads, and neighbour traversal."""
        grid = Grid(rows=8, cols=8, default_terrain=TerrainType.NORMAL)

        # Setup road network
        grid.add_road(Position(2, 0))
        grid.add_road(Position(2, 1))
        grid.add_road(Position(2, 2))
        grid.add_road(Position(2, 3))

        # Setup disaster obstacles
        grid.add_collapsed_building(Position(1, 2))
        grid.add_fire_zone(Position(3, 2))

        # Check walkability around intersection (2, 2)
        center = Position(2, 2)
        self.assertTrue(grid.is_walkable(center))
        self.assertFalse(grid.is_walkable(Position(1, 2)))  # Rubble
        self.assertFalse(grid.is_walkable(Position(3, 2)))  # Fire

        walkable_neighbours = grid.get_walkable_neighbours(center)
        # UP (2, 1) and DOWN (2, 3) are open road, LEFT (1, 2) and RIGHT (3, 2) are blocked
        self.assertEqual(len(walkable_neighbours), 2)
        self.assertEqual(set(walkable_neighbours), {Position(2, 1), Position(2, 3)})


if __name__ == "__main__":
    unittest.main()
