"""
Knowledge Grid representation in RescueGrid (Phase 6).
Represents what the rescue vehicle/agent currently knows about the disaster environment.
Unknown cells remain mystery states ('?') until discovered via vehicle sensor scans.
"""

import math
from typing import Set, List, Optional, Union, Iterable, Tuple, Any
from models.position import Position
from environment.cell import Cell, TerrainType
from environment.grid import Grid


class KnowledgeGrid(Grid):
    """Represents the agent's partial knowledge of the disaster environment.

    In a realistic disaster response, an agent does not initially possess complete
    situational awareness. Unexplored cells remain UNKNOWN mystery states ('?').
    Unknown cells cannot be treated as confirmed safe and are excluded from path
    generation until revealed by sensors.

    All route planning algorithms (BFS, DFS, UCS, A*) run strictly upon the
    Knowledge Grid in partially observable simulation scenarios.
    """

    def __init__(
        self,
        rows: int,
        cols: int,
        default_terrain: TerrainType = TerrainType.UNKNOWN,
    ) -> None:
        """Initialize a Knowledge Grid.

        Args:
            rows: Total number of rows (height).
            cols: Total number of columns (width).
            default_terrain: Default initial terrain (default: TerrainType.UNKNOWN).
        """
        super().__init__(rows=rows, cols=cols, default_terrain=default_terrain)
        self._revealed: Set[Position] = set()

        # If initialized with a known terrain category, all cells are initially revealed
        if default_terrain not in (TerrainType.UNKNOWN, TerrainType.Unknown):
            for r in range(rows):
                for c in range(cols):
                    self._revealed.add(Position(c, r))

    # Knowledge & Discovery State
    def is_revealed(
        self,
        x_or_pos: Union[Position, int],
        y: Optional[int] = None,
    ) -> bool:
        """Check whether the given coordinate has been revealed.

        Args:
            x_or_pos: Position instance or integer X coordinate.
            y: Integer Y coordinate if x_or_pos is an integer.

        Returns:
            True if cell has been revealed, False otherwise.

        Raises:
            IndexError: If coordinates lie outside grid boundaries.
        """
        cx, cy = self._resolve_coordinates(x_or_pos, y)
        if not (0 <= cx < self._cols and 0 <= cy < self._rows):
            raise IndexError(
                f"Coordinates ({cx}, {cy}) are outside grid boundaries "
                f"[cols={self._cols}, rows={self._rows}]."
            )
        return Position(cx, cy) in self._revealed

    def is_unknown(
        self,
        x_or_pos: Union[Position, int],
        y: Optional[int] = None,
    ) -> bool:
        """Check whether the given coordinate remains an unknown mystery state.

        Args:
            x_or_pos: Position instance or integer X coordinate.
            y: Integer Y coordinate if x_or_pos is an integer.

        Returns:
            True if cell is unknown, False if revealed.
        """
        return not self.is_revealed(x_or_pos, y)

    @property
    def revealed_count(self) -> int:
        """Return the total number of revealed cells."""
        return len(self._revealed)

    @property
    def unknown_count(self) -> int:
        """Return the total number of unrevealed (unknown) cells."""
        return self.total_cells - len(self._revealed)

    def get_revealed_positions(self) -> Set[Position]:
        """Return a copy of the set of all revealed Position coordinates."""
        return set(self._revealed)

    def get_unknown_positions(self) -> Set[Position]:
        """Return a set of all currently unknown Position coordinates."""
        unknown = set()
        for r in range(self._rows):
            for c in range(self._cols):
                pos = Position(c, r)
                if pos not in self._revealed:
                    unknown.add(pos)
        return unknown

    # Discovery & Revelation Mechanisms
    def reveal_cell(
        self,
        x_or_pos: Union[Position, int],
        y_or_actual: Any = None,
        actual_grid: Optional[Any] = None,
    ) -> bool:
        """Reveal a single cell from the physical ground-truth Actual Grid.

        Supports two invocation signatures:
        - reveal_cell(Position(x, y), actual_grid)
        - reveal_cell(x, y, actual_grid)

        Args:
            x_or_pos: Position instance or integer X coordinate.
            y_or_actual: Actual Grid instance if first arg is Position, or integer Y coordinate.
            actual_grid: Actual Grid instance if first two args are integer coordinates.

        Returns:
            True if this cell was newly revealed, False if it was already known.

        Raises:
            TypeError: If coordinates or actual_grid are of invalid types.
            IndexError: If coordinates are out of bounds.
        """
        if isinstance(x_or_pos, Position):
            if actual_grid is not None:
                raise TypeError("Unexpected third argument when Position is provided.")
            grid_source = y_or_actual
            cx, cy = x_or_pos.x, x_or_pos.y
            pos = x_or_pos
        else:
            cx, cy = self._resolve_coordinates(x_or_pos, y_or_actual)
            grid_source = actual_grid
            pos = Position(cx, cy)

        if not isinstance(grid_source, Grid):
            raise TypeError(f"Actual grid source must be a Grid instance, got {type(grid_source).__name__}.")

        if not (0 <= cx < self._cols and 0 <= cy < self._rows):
            raise IndexError(
                f"Coordinates ({cx}, {cy}) are outside grid boundaries "
                f"[cols={self._cols}, rows={self._rows}]."
            )
        if not grid_source.is_inside(pos):
            raise IndexError(f"Position {pos} is outside actual grid boundaries.")

        was_new = pos not in self._revealed

        # Copy physical attributes from actual cell to knowledge cell
        actual_cell = grid_source.get_cell(pos)
        knowledge_cell = self.get_cell(pos)

        knowledge_cell.set_terrain(actual_cell.terrain)
        knowledge_cell.set_obstacle(actual_cell.is_obstacle)
        knowledge_cell.set_walkable(actual_cell.is_walkable)

        if actual_cell._custom_cost is not None:
            knowledge_cell.set_movement_cost(actual_cell._custom_cost)
        else:
            knowledge_cell.set_movement_cost(None)

        if actual_cell.occupant_id is not None:
            knowledge_cell.set_occupant(actual_cell.occupant_id)
        else:
            knowledge_cell.clear_occupant()

        self._revealed.add(pos)
        return was_new

    def reveal_region(
        self,
        positions: Iterable[Position],
        actual_grid: Grid,
    ) -> List[Position]:
        """Reveal a collection of coordinates from the Actual Grid.

        Args:
            positions: Iterable collection of Position coordinates.
            actual_grid: Physical ground-truth Grid.

        Returns:
            List of positions that were newly revealed during this operation.
        """
        newly_revealed: List[Position] = []
        for pos in positions:
            if not isinstance(pos, Position):
                raise TypeError("All items in positions must be Position instances.")
            if self.is_inside(pos) and actual_grid.is_inside(pos):
                if self.reveal_cell(pos, actual_grid):
                    newly_revealed.append(pos)
        return newly_revealed

    def reveal_radius(
        self,
        center: Position,
        radius: int,
        actual_grid: Grid,
    ) -> List[Position]:
        """Reveal all in-bounds cells within a Manhattan distance radius of a center position.

        Manhattan distance metric: |x - center.x| + |y - center.y| <= radius.

        Args:
            center: Sensor center Position.
            radius: Non-negative integer sensor radius (0 = center only, 1 = adjacent, 2 = radius 2).
            actual_grid: Physical ground-truth Grid.

        Returns:
            List of positions that were newly revealed during this scan.

        Raises:
            TypeError: If center is not Position, radius is non-integer, or actual_grid is not Grid.
            ValueError: If radius is negative.
            IndexError: If center is outside grid boundaries.
        """
        if not isinstance(center, Position):
            raise TypeError(f"Sensor center must be a Position, got {type(center).__name__}.")
        if isinstance(radius, bool) or not isinstance(radius, int):
            raise TypeError("Sensor radius must be an integer.")
        if radius < 0:
            raise ValueError("Sensor radius must be a non-negative integer.")
        if not isinstance(actual_grid, Grid):
            raise TypeError(f"actual_grid must be a Grid instance, got {type(actual_grid).__name__}.")
        if not self.is_inside(center):
            raise IndexError(f"Center position {center} is outside grid boundaries.")

        newly_revealed: List[Position] = []

        # Scan bounding box constrained by grid dimensions and sensor radius
        min_x = max(0, center.x - radius)
        max_x = min(self._cols - 1, center.x + radius)
        min_y = max(0, center.y - radius)
        max_y = min(self._rows - 1, center.y + radius)

        for cy in range(min_y, max_y + 1):
            for cx in range(min_x, max_x + 1):
                dist = abs(cx - center.x) + abs(cy - center.y)
                if dist <= radius:
                    pos = Position(cx, cy)
                    if actual_grid.is_inside(pos):
                        if self.reveal_cell(pos, actual_grid):
                            newly_revealed.append(pos)

        return newly_revealed

    def initialize_known_positions(
        self,
        positions: Iterable[Position],
        actual_grid: Grid,
    ) -> None:
        """Helper to reveal an initial baseline of known positions (e.g., base map).

        Args:
            positions: Coordinates to reveal.
            actual_grid: Ground truth Grid.
        """
        self.reveal_region(positions, actual_grid)

    def mark_as_unknown(
        self,
        x_or_pos: Union[Position, int],
        y: Optional[int] = None,
    ) -> None:
        """Explicitly reset a cell to an UNKNOWN mystery state.

        Args:
            x_or_pos: Position instance or integer X coordinate.
            y: Integer Y coordinate if x_or_pos is an integer.
        """
        cx, cy = self._resolve_coordinates(x_or_pos, y)
        pos = Position(cx, cy)
        cell = self.get_cell(pos)
        cell.set_terrain(TerrainType.UNKNOWN)
        cell.set_obstacle(False)
        cell.set_walkable(False)
        cell.set_movement_cost(None)
        self._revealed.discard(pos)
