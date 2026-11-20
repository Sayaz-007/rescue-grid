"""
Actual Grid environment representing physical ground truth in RescueGrid (Phase 6).
Used exclusively by the simulation environment to represent complete disaster reality
and reveal environmental information to the agent's Knowledge Grid.
"""

from typing import Optional, Union, Tuple
from models.position import Position
from environment.cell import Cell, TerrainType
from environment.grid import Grid


class ActualGrid(Grid):
    """Represents the complete, objective underlying disaster environment (Ground Truth).

    The Actual Grid contains all physical terrain features (roads, normal ground,
    rough ground, collapsed rubble, flood waters, fire zones) and true movement costs.

    Architectural Boundary Rule:
    Route-planning algorithms (BFS, DFS, UCS, A*) must NEVER be provided direct
    access to the Actual Grid. They operate strictly upon the Knowledge Grid.
    The simulation environment alone queries the Actual Grid to reveal sensor data
    and validate physical agent locomotion.
    """

    def __init__(
        self,
        rows: int,
        cols: int,
        default_terrain: TerrainType = TerrainType.NORMAL,
    ) -> None:
        """Initialize an ActualGrid ground-truth environment.

        Args:
            rows: Total number of rows (height).
            cols: Total number of columns (width).
            default_terrain: Default surface terrain (default: TerrainType.NORMAL).
        """
        super().__init__(rows=rows, cols=cols, default_terrain=default_terrain)

    def create_knowledge_grid(
        self,
        default_terrain: TerrainType = TerrainType.UNKNOWN,
    ) -> "KnowledgeGrid":
        """Instantiate a companion Knowledge Grid with matching dimensions.

        Args:
            default_terrain: Default unrevealed terrain (default: TerrainType.UNKNOWN).

        Returns:
            A new KnowledgeGrid of identical dimensions, ready for simulation exploration.
        """
        from environment.knowledge_grid import KnowledgeGrid
        return KnowledgeGrid(rows=self.rows, cols=self.cols, default_terrain=default_terrain)

    @classmethod
    def from_grid(cls, grid: Grid) -> "ActualGrid":
        """Construct an ActualGrid by copying the terrain and cell states of an existing Grid.

        Args:
            grid: Source Grid instance.

        Returns:
            A new ActualGrid containing an exact copy of the source grid's state.

        Raises:
            TypeError: If grid is not an instance of Grid.
        """
        if not isinstance(grid, Grid):
            raise TypeError(f"Source must be a Grid instance, got {type(grid).__name__}.")

        actual = cls(rows=grid.rows, cols=grid.cols)
        for r in range(grid.rows):
            for c in range(grid.cols):
                src_cell = grid.get_cell(c, r)
                dst_cell = actual.get_cell(c, r)
                dst_cell.set_terrain(src_cell.terrain)
                dst_cell.set_obstacle(src_cell.is_obstacle)
                dst_cell.set_walkable(src_cell.is_walkable)
                if src_cell._custom_cost is not None:
                    dst_cell.set_movement_cost(src_cell._custom_cost)
                if src_cell.occupant_id is not None:
                    dst_cell.set_occupant(src_cell.occupant_id)
        return actual

    def clone(self) -> "ActualGrid":
        """Create an independent deep copy of this ActualGrid."""
        return ActualGrid.from_grid(self)
