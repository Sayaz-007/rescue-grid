"""
Sensor mechanism for partial observability in RescueGrid (Phase 6).
Simulates onboard vehicle sensors scanning environmental reality within a
configurable Manhattan distance radius.
"""

from typing import List, Union
from models.position import Position
from environment.grid import Grid
from environment.knowledge_grid import KnowledgeGrid


class Sensor:
    """Configurable proximity sensor for emergency response vehicles.

    Uses Manhattan distance (|x1 - x2| + |y1 - y2|) to discover nearby cells:
    - Distance 0: Always reveals the current cell.
    - Distance 1: Reveals orthogonally adjacent cells.
    - Distance 2: Reveals cells within radius 2 (default).
    - Greater than radius: Cells remain unknown until approached.
    """

    def __init__(self, radius: int = 2) -> None:
        """Initialize a Sensor with a configurable detection radius.

        Args:
            radius: Non-negative integer detection radius in Manhattan distance (default: 2).

        Raises:
            TypeError: If radius is not an integer or is a boolean.
            ValueError: If radius is negative.
        """
        self._set_validated_radius(radius)

    def _set_validated_radius(self, radius: int) -> None:
        if isinstance(radius, bool) or not isinstance(radius, int):
            raise TypeError("Sensor radius must be an integer.")
        if radius < 0:
            raise ValueError("Sensor radius must be a non-negative integer (>= 0).")
        self._radius: int = radius

    @property
    def radius(self) -> int:
        """Return the current sensor detection radius."""
        return self._radius

    def set_radius(self, radius: int) -> None:
        """Update the sensor detection radius.

        Args:
            radius: Non-negative integer.

        Raises:
            TypeError: If radius is non-integer or boolean.
            ValueError: If radius is negative.
        """
        self._set_validated_radius(radius)

    def get_detectable_positions(self, center: Position, grid: Grid) -> List[Position]:
        """Compute all in-bounds grid positions within the sensor detection radius.

        Args:
            center: Current vehicle Position.
            grid: Grid defining dimensions.

        Returns:
            List of valid in-bounds Positions where Manhattan distance <= radius.

        Raises:
            TypeError: If center is not Position or grid is not Grid.
            IndexError: If center is outside grid bounds.
        """
        if not isinstance(center, Position):
            raise TypeError(f"Center must be a Position instance, got {type(center).__name__}.")
        if not isinstance(grid, Grid):
            raise TypeError(f"grid must be a Grid instance, got {type(grid).__name__}.")
        if not grid.is_inside(center):
            raise IndexError(f"Center position {center} is outside grid boundaries.")

        detectable: List[Position] = []
        min_x = max(0, center.x - self._radius)
        max_x = min(grid.cols - 1, center.x + self._radius)
        min_y = max(0, center.y - self._radius)
        max_y = min(grid.rows - 1, center.y + self._radius)

        for cy in range(min_y, max_y + 1):
            for cx in range(min_x, max_x + 1):
                dist = abs(cx - center.x) + abs(cy - center.y)
                if dist <= self._radius:
                    detectable.append(Position(cx, cy))

        return detectable

    def sense(
        self,
        center: Position,
        actual_grid: Grid,
        knowledge_grid: KnowledgeGrid,
    ) -> List[Position]:
        """Perform a sensor scan around the center position, updating the Knowledge Grid.

        Args:
            center: Current position of the rescue vehicle.
            actual_grid: Complete physical Ground Truth environment.
            knowledge_grid: Agent's internal Knowledge Grid to update with discovered data.

        Returns:
            List of Positions that were newly revealed during this scan.

        Raises:
            TypeError: If inputs have invalid types.
            IndexError: If center is outside grid boundaries.
        """
        if not isinstance(knowledge_grid, KnowledgeGrid):
            raise TypeError(
                f"knowledge_grid must be a KnowledgeGrid instance, got {type(knowledge_grid).__name__}."
            )
        return knowledge_grid.reveal_radius(center, self._radius, actual_grid)

    def __repr__(self) -> str:
        return f"Sensor(radius={self._radius})"
