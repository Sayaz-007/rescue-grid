"""
Cell representation for the 2D disaster simulation grid.
"""

import math
from enum import Enum
from typing import Optional, Any, Dict, Union
from models.position import Position


class TerrainType(str, Enum):
    """Categorization of surface terrain types in the disaster area."""
    NORMAL = "Normal"
    ROAD = "Road"
    ROUGH = "Rough"
    RUBBLE = "Rubble"
    WATER = "Water"
    FIRE_ZONE = "FireZone"
    UNKNOWN = "Unknown"

    # Aliases for convenience
    Normal = "Normal"
    Road = "Road"
    Rough = "Rough"
    Rubble = "Rubble"
    Water = "Water"
    FireZone = "FireZone"
    Unknown = "Unknown"

    @property
    def is_default_walkable(self) -> bool:
        """Return True if this terrain category is inherently walkable by default.

        Default traversal rules:
        - NORMAL:    Walkable (True)
        - ROAD:      Walkable (True)
        - ROUGH:     Walkable (True)
        - RUBBLE:    Blocked  (False)
        - WATER:     Blocked  (False)
        - FIRE_ZONE: Blocked  (False)
        - UNKNOWN:   Blocked  (False, mystery state excluded from planning until discovered)
        """
        return self in (
            TerrainType.NORMAL,
            TerrainType.ROAD,
            TerrainType.ROUGH,
            TerrainType.Normal,
            TerrainType.Road,
            TerrainType.Rough,
        )


class TerrainCostConfig:
    """Centralized configuration for default terrain movement costs.

    Only traversable terrains receive finite positive movement costs:
    - ROAD: 1.0
    - NORMAL: 2.0
    - ROUGH: 4.0
    - RUBBLE, WATER, FIRE_ZONE: Infinity / unavailable
    """

    _default_costs: Dict[TerrainType, float] = {
        TerrainType.ROAD: 1.0,
        TerrainType.NORMAL: 2.0,
        TerrainType.ROUGH: 4.0,
    }

    @classmethod
    def get_cost(cls, terrain: TerrainType) -> float:
        """Return configured movement cost for traversable terrain, or infinity if blocked."""
        if not isinstance(terrain, TerrainType):
            raise TypeError("Terrain must be a valid TerrainType enum.")
        if terrain in (TerrainType.ROAD, TerrainType.Road):
            return cls._default_costs.get(TerrainType.ROAD, 1.0)
        if terrain in (TerrainType.NORMAL, TerrainType.Normal):
            return cls._default_costs.get(TerrainType.NORMAL, 2.0)
        if terrain in (TerrainType.ROUGH, TerrainType.Rough):
            return cls._default_costs.get(TerrainType.ROUGH, 4.0)
        return float("inf")

    @classmethod
    def get_min_traversable_cost(cls) -> float:
        """Return the lowest movement cost among all traversable terrain types."""
        traversable_costs = [
            cost
            for terrain, cost in cls._default_costs.items()
            if terrain.is_default_walkable and math.isfinite(cost) and cost > 0
        ]
        return min(traversable_costs) if traversable_costs else 1.0

    @classmethod
    def set_cost(cls, terrain: TerrainType, cost: Union[int, float]) -> None:
        """Configure movement cost for a traversable terrain type.

        Raises:
            TypeError: If terrain is not TerrainType, or cost is non-numeric/bool.
            ValueError: If terrain is non-traversable or cost is non-positive/infinite/NaN.
        """
        if not isinstance(terrain, TerrainType):
            raise TypeError("Terrain must be a valid TerrainType enum.")
        if not terrain.is_default_walkable:
            raise ValueError(f"Cannot assign finite movement cost to non-traversable terrain '{terrain.value}'.")
        if isinstance(cost, bool) or not isinstance(cost, (int, float)):
            raise TypeError("Movement cost must be a numeric value (int or float).")
        if cost <= 0 or math.isnan(cost) or math.isinf(cost):
            raise ValueError("Movement cost must be a strictly positive finite number.")

        key = (
            TerrainType.ROAD
            if terrain in (TerrainType.ROAD, TerrainType.Road)
            else (
                TerrainType.NORMAL
                if terrain in (TerrainType.NORMAL, TerrainType.Normal)
                else TerrainType.ROUGH
            )
        )
        cls._default_costs[key] = float(cost)

    @classmethod
    def reset_defaults(cls) -> None:
        """Reset all terrain costs to their standard default values."""
        cls._default_costs = {
            TerrainType.ROAD: 1.0,
            TerrainType.NORMAL: 2.0,
            TerrainType.ROUGH: 4.0,
        }


class Cell:
    """Represents a discrete cell within the 2D simulation grid.

    Encapsulates a grid Position, terrain classification, obstacle status,
    and operational walkability for agents and vehicles.
    """

    def __init__(
        self,
        position: Position,
        terrain: TerrainType = TerrainType.NORMAL,
        is_obstacle: bool = False,
        is_walkable: Optional[bool] = None,
        movement_cost: Optional[Union[int, float]] = None,
    ) -> None:
        """Initialize a Cell at a discrete Position.

        Args:
            position: Discrete coordinates of the cell as a Position instance.
            terrain: Terrain classification (default: TerrainType.NORMAL).
            is_obstacle: Whether this cell contains an obstacle (default: False).
            is_walkable: Explicit walkability override. If omitted, defaults to
                False if is_obstacle is True or terrain is non-walkable,
                otherwise True for walkable terrain.
            movement_cost: Optional custom movement cost override. If omitted,
                derives dynamically from terrain classification.

        Raises:
            TypeError: If position, terrain, is_obstacle, is_walkable, or movement_cost has an invalid type.
            ValueError: If is_obstacle is True and is_walkable is explicitly True (contradictory state),
                or if movement_cost is non-positive or assigned to a non-walkable cell.
        """
        if not isinstance(position, Position):
            raise TypeError("Cell position must be a valid Position instance.")
        if not isinstance(terrain, TerrainType):
            raise TypeError("Terrain must be a valid TerrainType enum value.")
        if not isinstance(is_obstacle, bool):
            raise TypeError("is_obstacle must be a boolean.")
        if is_walkable is not None and not isinstance(is_walkable, bool):
            raise TypeError("is_walkable must be a boolean.")

        if is_obstacle and is_walkable is True:
            raise ValueError("Cell cannot contain an obstacle and be marked as walkable simultaneously.")

        self._position: Position = position
        self._terrain: TerrainType = terrain
        self._is_obstacle: bool = is_obstacle

        if is_walkable is not None:
            self._is_walkable: bool = is_walkable
        else:
            self._is_walkable: bool = not is_obstacle and terrain.is_default_walkable

        self._occupant_id: Optional[str] = None
        self._custom_cost: Optional[float] = None

        if movement_cost is not None:
            self.set_movement_cost(movement_cost)

    # Properties & Accessors
    @property
    def position(self) -> Position:
        """Return the discrete grid Position of the cell."""
        return self._position

    @property
    def x(self) -> int:
        """Return the X coordinate (column index)."""
        return self._position.x

    @property
    def y(self) -> int:
        """Return the Y coordinate (row index)."""
        return self._position.y

    @property
    def col(self) -> int:
        """Return the column index (alias for x)."""
        return self._position.x

    @property
    def row(self) -> int:
        """Return the row index (alias for y)."""
        return self._position.y

    @property
    def terrain(self) -> TerrainType:
        """Return current terrain classification."""
        return self._terrain

    @property
    def is_obstacle(self) -> bool:
        """Return True if this cell contains an obstacle."""
        return self._is_obstacle

    def has_obstacle(self) -> bool:
        """Check whether this cell contains an obstacle (method alias)."""
        return self._is_obstacle

    @property
    def is_walkable(self) -> bool:
        """Return True if this cell is walkable for response units."""
        return self._is_walkable

    @property
    def movement_cost(self) -> float:
        """Return the effective movement cost of entering this cell.

        Traversable cells return a strictly positive finite cost (1 for ROAD, 2 for NORMAL,
        4 for ROUGH, or custom override). Non-traversable or obstacle cells return float('inf').
        """
        if not self._is_walkable or self._is_obstacle:
            return float("inf")
        if self._custom_cost is not None:
            return self._custom_cost
        return TerrainCostConfig.get_cost(self._terrain)

    @property
    def cost(self) -> float:
        """Return movement cost of entering this cell (property alias)."""
        return self.movement_cost

    def get_movement_cost(self) -> float:
        """Return movement cost of entering this cell (getter method)."""
        return self.movement_cost

    def get_cost(self) -> float:
        """Return movement cost of entering this cell (getter method alias)."""
        return self.movement_cost

    @property
    def has_finite_cost(self) -> bool:
        """Return True if this cell has a finite positive movement cost."""
        return math.isfinite(self.movement_cost)

    @property
    def occupant_id(self) -> Optional[str]:
        """Return the identifier of any occupant at this cell, or None."""
        return self._occupant_id

    # Mutators
    def set_movement_cost(self, cost: Optional[Union[int, float]]) -> None:
        """Assign a custom movement cost override for this cell.

        Args:
            cost: Strictly positive finite number, or None to revert to terrain default.

        Raises:
            TypeError: If cost is not numeric (or is boolean).
            ValueError: If cost is non-positive, NaN, infinite, or assigned to a non-walkable cell.
        """
        if cost is None:
            self._custom_cost = None
            return
        if isinstance(cost, bool) or not isinstance(cost, (int, float)):
            raise TypeError("Movement cost must be a numeric value (int or float).")
        if cost <= 0 or math.isnan(cost) or math.isinf(cost):
            raise ValueError("Movement cost must be a strictly positive finite number.")
        if not self._is_walkable or self._is_obstacle:
            raise ValueError("Cannot assign movement cost to a non-walkable cell or obstacle.")
        self._custom_cost = float(cost)

    set_cost = set_movement_cost

    def set_obstacle(self, is_obstacle: bool) -> None:
        """Set or remove an obstacle from this cell.

        Placing an obstacle marks the cell as non-walkable.
        Removing an obstacle restores walkability only if the cell's surface
        terrain is inherently walkable (NORMAL, ROAD, or ROUGH). Hazardous terrain
        (WATER, FIRE_ZONE, RUBBLE) remains blocked.

        Raises:
            TypeError: If is_obstacle is not a boolean.
        """
        if not isinstance(is_obstacle, bool):
            raise TypeError("is_obstacle must be a boolean.")

        self._is_obstacle = is_obstacle
        if self._is_obstacle:
            self._is_walkable = False
        else:
            self._is_walkable = self._terrain.is_default_walkable

    def set_walkable(self, walkable: bool) -> None:
        """Explicitly update cell walkability.

        An explicit override can mark inherently non-walkable terrain (e.g. WATER)
        as walkable (representing an emergency pontoon bridge or cleared path),
        provided no physical obstacle is present.

        Args:
            walkable: Desired walkability boolean flag.

        Raises:
            TypeError: If walkable is not a boolean.
            ValueError: If attempting to mark a cell containing an active obstacle as walkable.
        """
        if not isinstance(walkable, bool):
            raise TypeError("walkable must be a boolean.")

        if walkable and self._is_obstacle:
            raise ValueError(
                "Cannot mark a cell with an active obstacle as walkable. "
                "Remove the obstacle first."
            )
        self._is_walkable = walkable

    def set_terrain(self, terrain: TerrainType) -> None:
        """Update the terrain category of this cell.

        Preserves obstacle presence if active, or updates walkability to the new
        terrain's default traversal behavior.

        Raises:
            TypeError: If terrain is not a TerrainType enum value.
        """
        if not isinstance(terrain, TerrainType):
            raise TypeError("Terrain must be a valid TerrainType enum value.")

        self._terrain = terrain
        if self._is_obstacle:
            self._is_walkable = False
        else:
            self._is_walkable = terrain.is_default_walkable

    def set_occupant(self, occupant_id: Optional[str]) -> None:
        """Set the occupant identifier at this cell."""
        self._occupant_id = occupant_id

    def clear_occupant(self) -> None:
        """Clear the occupant from this cell."""
        self._occupant_id = None

    def get_symbol(self) -> str:
        """Return a single-character visual representation for grid rendering."""
        if self._occupant_id is not None:
            return self._occupant_id[0].upper()
        if self._terrain in (TerrainType.UNKNOWN, TerrainType.Unknown):
            return "?"
        if self._is_obstacle or not self._is_walkable:
            if self._terrain in (TerrainType.RUBBLE, TerrainType.Rubble):
                return "X"
            if self._terrain in (TerrainType.FIRE_ZONE, TerrainType.FireZone):
                return "F"
            if self._terrain in (TerrainType.WATER, TerrainType.Water):
                return "W"
            return "#"
        if self._terrain in (TerrainType.ROAD, TerrainType.Road):
            return "="
        if self._terrain in (TerrainType.ROUGH, TerrainType.Rough):
            return ":"
        if self._terrain in (TerrainType.RUBBLE, TerrainType.Rubble):
            return "^"
        if self._terrain in (TerrainType.WATER, TerrainType.Water):
            return "~"
        if self._terrain in (TerrainType.FIRE_ZONE, TerrainType.FireZone):
            return "*"
        return "."

    def __str__(self) -> str:
        cost_str = f"{self.movement_cost}" if self.has_finite_cost else "inf"
        return (
            f"Cell(pos={self._position}, terrain={self._terrain.value}, "
            f"obstacle={self._is_obstacle}, walkable={self._is_walkable}, cost={cost_str})"
        )

    def __repr__(self) -> str:
        return (
            f"Cell(position={self._position!r}, terrain={self._terrain!r}, "
            f"is_obstacle={self._is_obstacle}, is_walkable={self._is_walkable}, "
            f"movement_cost={self.movement_cost})"
        )
