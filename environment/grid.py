"""
Grid environment modeling a 2D disaster-affected area in RescueGrid.
"""

from typing import List, Optional, Tuple, Union
from models.position import Position
from environment.cell import Cell, TerrainType, TerrainCostConfig


class Grid:
    """Represents a bounded 2D discrete grid of cells in a disaster area.

    Encapsulates a matrix of Cell objects, validating boundaries, tracking
    walkability and obstacles, and computing cardinal neighbours for response units.
    """

    def __init__(
        self,
        rows: int,
        cols: int,
        default_terrain: TerrainType = TerrainType.NORMAL,
    ) -> None:
        """Initialize a bounded 2D grid with configurable rows and columns.

        Args:
            rows: Total number of rows (vertical dimension / height).
            cols: Total number of columns (horizontal dimension / width).
            default_terrain: Initial surface terrain for all cells (default: TerrainType.NORMAL).

        Raises:
            TypeError: If rows or cols is not an integer (booleans rejected),
                or if default_terrain is not a valid TerrainType.
            ValueError: If rows or cols is not greater than zero.
        """
        if isinstance(rows, bool) or not isinstance(rows, int):
            raise TypeError("Grid rows must be an integer.")
        if isinstance(cols, bool) or not isinstance(cols, int):
            raise TypeError("Grid columns must be an integer.")
        if rows <= 0:
            raise ValueError("Grid rows must be a positive integer greater than zero.")
        if cols <= 0:
            raise ValueError("Grid columns must be a positive integer greater than zero.")
        if not isinstance(default_terrain, TerrainType):
            raise TypeError("default_terrain must be a valid TerrainType enum value.")

        self._rows: int = rows
        self._cols: int = cols
        self._default_terrain: TerrainType = default_terrain

        # Build 2D matrix of Cell objects indexed by [row][col]
        # where col represents X coordinate (0 <= x < cols)
        # and row represents Y coordinate (0 <= y < rows)
        self._cells: List[List[Cell]] = []
        for r in range(rows):
            row_cells: List[Cell] = []
            for c in range(cols):
                pos = Position(x=c, y=r)
                row_cells.append(Cell(position=pos, terrain=default_terrain))
            self._cells.append(row_cells)

    # Dimensions & Properties
    @property
    def rows(self) -> int:
        """Return total number of rows in the grid."""
        return self._rows

    @property
    def cols(self) -> int:
        """Return total number of columns in the grid."""
        return self._cols

    @property
    def width(self) -> int:
        """Return width (columns) of the grid."""
        return self._cols

    @property
    def height(self) -> int:
        """Return height (rows) of the grid."""
        return self._rows

    @property
    def total_cells(self) -> int:
        """Return total count of cells in the grid."""
        return self._rows * self._cols

    # Coordinate Extraction & Boundary Validation
    def _resolve_coordinates(
        self,
        x_or_pos: Union[Position, int],
        y: Optional[int] = None,
    ) -> Tuple[int, int]:
        """Normalize coordinates from either a Position object or discrete (x, y) integers.

        Args:
            x_or_pos: A Position object or integer X coordinate.
            y: Integer Y coordinate if x_or_pos is an integer.

        Returns:
            Tuple of (x, y) integers.

        Raises:
            TypeError: If arguments do not match expected types or are booleans/floats/strings.
        """
        if isinstance(x_or_pos, Position):
            if y is not None:
                raise TypeError("Unexpected second coordinate argument when Position object is provided.")
            return x_or_pos.x, x_or_pos.y
        if (
            not isinstance(x_or_pos, bool)
            and isinstance(x_or_pos, int)
            and not isinstance(y, bool)
            and isinstance(y, int)
        ):
            return x_or_pos, y
        raise TypeError("Coordinates must be provided as a Position or as two integers (x, y).")

    def is_inside(
        self,
        x_or_pos: Union[Position, int],
        y: Optional[int] = None,
    ) -> bool:
        """Check whether the given coordinates lie within the bounded grid.

        Returns False safely if coordinates are invalid or out of bounds.
        """
        try:
            cx, cy = self._resolve_coordinates(x_or_pos, y)
            return 0 <= cx < self._cols and 0 <= cy < self._rows
        except TypeError:
            return False

    is_valid_position = is_inside

    # Cell Retrieval
    def get_cell(
        self,
        x_or_pos: Union[Position, int],
        y: Optional[int] = None,
    ) -> Cell:
        """Retrieve the Cell at the specified coordinates.

        Supports both:
        - get_cell(Position(x, y))
        - get_cell(x, y)

        Args:
            x_or_pos: Position instance or integer X coordinate (column).
            y: Integer Y coordinate (row) if x_or_pos is integer.

        Returns:
            The Cell instance at that position.

        Raises:
            TypeError: If coordinates have invalid types (rejecting floats, strings, booleans).
            IndexError: If coordinates are outside grid bounds.
        """
        cx, cy = self._resolve_coordinates(x_or_pos, y)
        if not (0 <= cx < self._cols and 0 <= cy < self._rows):
            raise IndexError(
                f"Coordinates ({cx}, {cy}) are outside grid boundaries "
                f"[cols={self._cols}, rows={self._rows}]."
            )
        return self._cells[cy][cx]

    def get_cell_by_rc(self, row: int, col: int) -> Cell:
        """Retrieve a cell by row and column index.

        Args:
            row: Row index (0 <= row < rows).
            col: Column index (0 <= col < cols).

        Returns:
            Cell at the given row and column.

        Raises:
            TypeError: If row or col is not an integer.
            IndexError: If row or col is outside grid boundaries.
        """
        if isinstance(row, bool) or not isinstance(row, int):
            raise TypeError("Row coordinate must be an integer.")
        if isinstance(col, bool) or not isinstance(col, int):
            raise TypeError("Column coordinate must be an integer.")
        return self.get_cell(col, row)

    # Walkability & Obstacle Inspection
    def is_walkable(
        self,
        x_or_pos: Union[Position, int],
        y: Optional[int] = None,
    ) -> bool:
        """Check whether a position is valid and walkable.

        Returns False safely if the position is outside the grid.
        """
        if not self.is_inside(x_or_pos, y):
            return False
        return self.get_cell(x_or_pos, y).is_walkable

    def has_obstacle(
        self,
        x_or_pos: Union[Position, int],
        y: Optional[int] = None,
    ) -> bool:
        """Check whether a position contains an obstacle.

        Returns False safely if the position is outside the grid.
        """
        if not self.is_inside(x_or_pos, y):
            return False
        return self.get_cell(x_or_pos, y).is_obstacle

    # Obstacle Placement and Removal
    def add_obstacle(
        self,
        x_or_pos: Union[Position, int],
        y: Optional[int] = None,
    ) -> None:
        """Place an obstacle at the specified coordinates, marking the cell non-walkable.

        Raises:
            TypeError: If coordinates have invalid types.
            IndexError: If coordinates are out of bounds.
        """
        cell = self.get_cell(x_or_pos, y)
        cell.set_obstacle(True)

    def remove_obstacle(
        self,
        x_or_pos: Union[Position, int],
        y: Optional[int] = None,
    ) -> None:
        """Remove an obstacle from the specified coordinates.

        Restores walkability only if the cell's terrain is inherently walkable.
        Hazardous terrain (WATER, FIRE_ZONE, RUBBLE) remains blocked.

        Raises:
            TypeError: If coordinates have invalid types.
            IndexError: If coordinates are out of bounds.
        """
        cell = self.get_cell(x_or_pos, y)
        cell.set_obstacle(False)

    def set_walkable(
        self,
        x_or_pos: Union[Position, int],
        y_or_walkable: Union[int, bool],
        walkable: Optional[bool] = None,
    ) -> None:
        """Update walkability of a cell directly.

        Supports:
        - set_walkable(Position(x, y), True/False)
        - set_walkable(x, y, True/False)

        Raises:
            TypeError: If coordinates or walkable flag has invalid types.
            ValueError: If attempting to mark a cell containing an active obstacle as walkable.
            IndexError: If coordinates are out of bounds.
        """
        if isinstance(x_or_pos, Position):
            if walkable is not None:
                raise TypeError("Unexpected third argument when Position is provided.")
            if not isinstance(y_or_walkable, bool):
                raise TypeError("Walkable flag must be a boolean.")
            cell = self.get_cell(x_or_pos)
            cell.set_walkable(y_or_walkable)
        else:
            if isinstance(x_or_pos, bool) or not isinstance(x_or_pos, int):
                raise TypeError("X coordinate must be an integer.")
            if isinstance(y_or_walkable, bool) or not isinstance(y_or_walkable, int):
                raise TypeError("Y coordinate must be an integer.")
            if walkable is None or not isinstance(walkable, bool):
                raise TypeError("Walkable flag must be a boolean.")
            cell = self.get_cell(x_or_pos, y_or_walkable)
            cell.set_walkable(walkable)

    # Terrain Updates
    def set_terrain(
        self,
        x_or_pos: Union[Position, int],
        y_or_terrain: Union[int, TerrainType],
        terrain: Optional[TerrainType] = None,
    ) -> None:
        """Update the terrain classification of a cell.

        Supports:
        - set_terrain(Position(x, y), TerrainType.WATER)
        - set_terrain(x, y, TerrainType.WATER)

        Raises:
            TypeError: If coordinates or terrain has invalid types.
            IndexError: If coordinates are out of bounds.
        """
        if isinstance(x_or_pos, Position):
            if terrain is not None:
                raise TypeError("Unexpected third argument when Position is provided.")
            if not isinstance(y_or_terrain, TerrainType):
                raise TypeError("Expected TerrainType as second argument when first is Position.")
            cell = self.get_cell(x_or_pos)
            cell.set_terrain(y_or_terrain)
        else:
            if isinstance(x_or_pos, bool) or not isinstance(x_or_pos, int):
                raise TypeError("X coordinate must be an integer.")
            if isinstance(y_or_terrain, bool) or not isinstance(y_or_terrain, int):
                raise TypeError("Y coordinate must be an integer.")
            if terrain is None or not isinstance(terrain, TerrainType):
                raise TypeError("Expected TerrainType as third argument when coordinates are integers.")
            cell = self.get_cell(x_or_pos, y_or_terrain)
            cell.set_terrain(terrain)

    # Disaster Scenario Modeling Helpers
    def add_collapsed_building(
        self,
        x_or_pos: Union[Position, int],
        y: Optional[int] = None,
    ) -> None:
        """Model a collapsed building: sets obstacle and assigns Rubble terrain."""
        cell = self.get_cell(x_or_pos, y)
        cell.set_terrain(TerrainType.RUBBLE)
        cell.set_obstacle(True)

    def add_fire_zone(
        self,
        x_or_pos: Union[Position, int],
        y: Optional[int] = None,
        blocked: bool = True,
    ) -> None:
        """Model an active fire hazard zone."""
        cell = self.get_cell(x_or_pos, y)
        cell.set_terrain(TerrainType.FIRE_ZONE)
        if blocked:
            cell.set_obstacle(True)

    def add_flood_zone(
        self,
        x_or_pos: Union[Position, int],
        y: Optional[int] = None,
        blocked: bool = True,
    ) -> None:
        """Model an urban flooded area."""
        cell = self.get_cell(x_or_pos, y)
        cell.set_terrain(TerrainType.WATER)
        if blocked:
            cell.set_obstacle(True)

    def add_road(
        self,
        x_or_pos: Union[Position, int],
        y: Optional[int] = None,
    ) -> None:
        """Model an open transit road (walkable, no obstacle)."""
        cell = self.get_cell(x_or_pos, y)
        cell.set_terrain(TerrainType.ROAD)
        cell.set_obstacle(False)

    def add_rough_terrain(
        self,
        x_or_pos: Union[Position, int],
        y: Optional[int] = None,
    ) -> None:
        """Model a rough, damaged transit zone (walkable, movement cost = 4)."""
        cell = self.get_cell(x_or_pos, y)
        cell.set_terrain(TerrainType.ROUGH)
        cell.set_obstacle(False)

    # Movement Cost Inspection & Updates
    def get_movement_cost(
        self,
        x_or_pos: Union[Position, int],
        y: Optional[int] = None,
    ) -> float:
        """Retrieve the movement cost of entering the cell at coordinates.

        Returns float('inf') if coordinates are invalid or cell is non-walkable.
        """
        if not self.is_inside(x_or_pos, y):
            return float("inf")
        return self.get_cell(x_or_pos, y).movement_cost

    get_cost = get_movement_cost

    def set_cell_cost(
        self,
        x_or_pos: Union[Position, int],
        y_or_cost: Union[int, float],
        cost: Optional[Union[int, float]] = None,
    ) -> None:
        """Update the custom movement cost of a cell directly.

        Supports:
        - set_cell_cost(Position(x, y), cost)
        - set_cell_cost(x, y, cost)

        Raises:
            TypeError: If coordinates or cost have invalid types.
            ValueError: If cost is non-positive or cell is non-walkable.
            IndexError: If coordinates are out of bounds.
        """
        if isinstance(x_or_pos, Position):
            if cost is not None:
                raise TypeError("Unexpected third argument when Position is provided.")
            cell = self.get_cell(x_or_pos)
            cell.set_movement_cost(y_or_cost)
        else:
            if isinstance(x_or_pos, bool) or not isinstance(x_or_pos, int):
                raise TypeError("X coordinate must be an integer.")
            if isinstance(y_or_cost, bool) or not isinstance(y_or_cost, int):
                raise TypeError("Y coordinate must be an integer.")
            cell = self.get_cell(x_or_pos, y_or_cost)
            cell.set_movement_cost(cost)

    def get_min_traversable_cost(self) -> float:
        """Return the lowest movement cost across all traversable cells in this grid."""
        min_cost = TerrainCostConfig.get_min_traversable_cost()
        for row in self._cells:
            for cell in row:
                if cell.is_walkable and not cell.is_obstacle:
                    cost = cell.movement_cost
                    if cost < min_cost:
                        min_cost = cost
        return min_cost

    # Cardinal Neighbour Retrieval
    def get_neighbours(
        self,
        x_or_pos: Union[Position, int],
        y: Optional[int] = None,
        walkable_only: bool = False,
    ) -> List[Position]:
        """Retrieve valid neighbouring positions in the four cardinal directions.

        Supported directions:
        - UP:    (x, y - 1)
        - DOWN:  (x, y + 1)
        - LEFT:  (x - 1, y)
        - RIGHT: (x + 1, y)

        Diagonal movements are strictly excluded at this stage.

        Args:
            x_or_pos: Starting Position or integer X coordinate.
            y: Integer Y coordinate if x_or_pos is an integer.
            walkable_only: If True, filters out blocked or obstacle cells.

        Returns:
            List of valid in-bounds Position objects.

        Raises:
            TypeError: If coordinates have invalid types.
            IndexError: If the source position itself is outside the grid.
        """
        cx, cy = self._resolve_coordinates(x_or_pos, y)
        if not (0 <= cx < self._cols and 0 <= cy < self._rows):
            raise IndexError(
                f"Source coordinates ({cx}, {cy}) are outside grid boundaries "
                f"[cols={self._cols}, rows={self._rows}]."
            )

        # 4 cardinal offsets (UP, DOWN, LEFT, RIGHT)
        candidates: List[Tuple[int, int]] = [
            (cx, cy - 1),  # UP
            (cx, cy + 1),  # DOWN
            (cx - 1, cy),  # LEFT
            (cx + 1, cy),  # RIGHT
        ]

        valid_neighbours: List[Position] = []
        for nx, ny in candidates:
            if 0 <= nx < self._cols and 0 <= ny < self._rows:
                cand_pos = Position(nx, ny)
                if not walkable_only or self._cells[ny][nx].is_walkable:
                    valid_neighbours.append(cand_pos)

        return valid_neighbours

    # Compatibility Aliases
    get_neighbors = get_neighbours

    def get_walkable_neighbours(
        self,
        x_or_pos: Union[Position, int],
        y: Optional[int] = None,
    ) -> List[Position]:
        """Convenience method to retrieve only walkable in-bounds cardinal neighbours."""
        return self.get_neighbours(x_or_pos, y, walkable_only=True)

    get_walkable_neighbors = get_walkable_neighbours

    # String & ASCII Representation
    def to_string(self) -> str:
        """Render a readable ASCII representation of the 2D grid."""
        lines: List[str] = []
        # Header with column indices
        col_header = "    " + " ".join(f"{c % 10}" for c in range(self._cols))
        lines.append(col_header)
        lines.append("    " + "-" * (self._cols * 2 - 1))

        for r in range(self._rows):
            row_symbols = " ".join(self._cells[r][c].get_symbol() for c in range(self._cols))
            lines.append(f"{r:2d} | {row_symbols}")

        return "\n".join(lines)

    def display(self) -> None:
        """Print readable grid representation to standard output."""
        print(self.to_string())

    def __str__(self) -> str:
        return self.to_string()

    def __repr__(self) -> str:
        return f"Grid(rows={self._rows}, cols={self._cols})"
