"""
RescueGrid 2D Grid Visualizer and Search Animator (Phase 9.2).

Provides Matplotlib-based rendering for simulation grids, search exploration
wavefronts, route animations, multi-algorithm side-by-side comparisons,
and performance metric charts.
"""

import math
from typing import Any, Dict, List, Optional, Tuple, Union

import matplotlib
import matplotlib.axes
import matplotlib.figure
import matplotlib.lines as mlines
import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation

from environment.cell import Cell, TerrainType
from environment.grid import Grid
from environment.knowledge_grid import KnowledgeGrid
from models.position import Position
from algorithms.search_result import SearchResult
from analysis.algorithm_comparison import ComparisonReport


# Standard Terrain Color Palette (Phase 9.2 Specification)
DEFAULT_TERRAIN_COLORS: Dict[TerrainType, str] = {
    TerrainType.ROAD: "#E0E0E0",       # Light grey paved transit
    TerrainType.NORMAL: "#E8F5E9",     # Soft light green / beige urban terrain
    TerrainType.ROUGH: "#8D6E63",      # Earthy brown rough damaged terrain
    TerrainType.RUBBLE: "#424242",     # Dark grey collapsed building rubble
    TerrainType.WATER: "#2196F3",      # Blue deep flood water hazard
    TerrainType.FIRE_ZONE: "#FF5722",  # Vivid red-orange active fire zone
    TerrainType.UNKNOWN: "#263238",    # Dark slate grey mystery state
}

GENERAL_OBSTACLE_COLOR = "#616161"     # General impassable obstacle
EXPLORED_COLOR = "#64B5F6"             # Light blue overlay for explored nodes
PATH_COLOR = "#FFD600"                 # Bright golden yellow for final route
PATH_BORDER_COLOR = "#212121"          # Dark border for path high contrast
START_COLOR = "#2E7D32"                # Deep green start marker
GOAL_COLOR = "#C62828"                 # Deep red goal marker
GRID_LINE_COLOR = "#B0BEC5"            # Subtle grid line separation


class GridVisualizer:
    """Object-oriented 2D grid visualizer and path animation engine for RescueGrid."""

    def __init__(
        self,
        cell_size: float = 0.8,
        show_coordinates: Optional[bool] = None,
        show_legend: bool = True,
        show_grid_lines: bool = True,
        font_size: int = 9,
        explored_alpha: float = 0.45,
        terrain_colors: Optional[Dict[TerrainType, str]] = None,
    ) -> None:
        """Initialize the visualizer with configurable rendering parameters.

        Args:
            cell_size: Target visual scale factor for grid cells (in inches per cell).
            show_coordinates: Whether to render (x,y) text in each cell.
                              If None, auto-enables for grids <= 20x20.
            show_legend: Whether to draw a descriptive legend.
            show_grid_lines: Whether to draw cell boundary grid lines.
            font_size: Base font size for cell annotations and labels.
            explored_alpha: Opacity factor for explored cell overlay (0.0 to 1.0).
            terrain_colors: Custom mapping of TerrainType to hex color strings.
        """
        self.cell_size: float = max(0.2, float(cell_size))
        self.show_coordinates: Optional[bool] = show_coordinates
        self.show_legend: bool = show_legend
        self.show_grid_lines: bool = show_grid_lines
        self.font_size: int = font_size
        self.explored_alpha: float = max(0.1, min(1.0, float(explored_alpha)))
        self.terrain_colors: Dict[TerrainType, str] = dict(
            terrain_colors if terrain_colors is not None else DEFAULT_TERRAIN_COLORS
        )

    def _determine_cell_color_and_symbol(
        self, grid: Grid, pos: Position
    ) -> Tuple[str, Optional[str], str]:
        """Determine fill color, hazard symbol, and text color for a cell without mutating grid.

        Returns:
            Tuple of (fill_color_hex, symbol_string_or_None, text_color_hex).
        """
        cell: Cell = grid.get_cell(pos)

        # KnowledgeGrid mystery cell handling
        if isinstance(grid, KnowledgeGrid) and grid.is_unknown(pos):
            return self.terrain_colors[TerrainType.UNKNOWN], "?", "#B0BEC5"

        terrain = cell.terrain
        if terrain == TerrainType.RUBBLE:
            return self.terrain_colors[TerrainType.RUBBLE], "X", "#FFFFFF"
        elif terrain == TerrainType.WATER:
            return self.terrain_colors[TerrainType.WATER], "W", "#FFFFFF"
        elif terrain == TerrainType.FIRE_ZONE:
            return self.terrain_colors[TerrainType.FIRE_ZONE], "F", "#FFFFFF"
        elif terrain == TerrainType.UNKNOWN:
            return self.terrain_colors[TerrainType.UNKNOWN], "?", "#B0BEC5"
        elif not grid.is_walkable(pos) or cell.has_obstacle():
            return GENERAL_OBSTACLE_COLOR, "#", "#FFFFFF"
        elif terrain == TerrainType.ROAD:
            return self.terrain_colors[TerrainType.ROAD], None, "#424242"
        elif terrain == TerrainType.ROUGH:
            return self.terrain_colors[TerrainType.ROUGH], None, "#FFFFFF"
        else:
            return self.terrain_colors.get(TerrainType.NORMAL, "#E8F5E9"), None, "#424242"

    def _build_legend_handles(self, grid: Grid, has_search: bool = False) -> List[Any]:
        """Construct proxy artist handles for the plot legend based on active grid features."""
        handles: List[Any] = []

        # Traversable terrains
        handles.append(
            mpatches.Patch(facecolor=self.terrain_colors[TerrainType.NORMAL], edgecolor=GRID_LINE_COLOR, label="Normal Ground")
        )
        handles.append(
            mpatches.Patch(facecolor=self.terrain_colors[TerrainType.ROAD], edgecolor=GRID_LINE_COLOR, label="Paved Road")
        )
        handles.append(
            mpatches.Patch(facecolor=self.terrain_colors[TerrainType.ROUGH], edgecolor=GRID_LINE_COLOR, label="Rough Terrain")
        )

        # Hazards & Obstacles
        handles.append(
            mpatches.Patch(facecolor=self.terrain_colors[TerrainType.RUBBLE], edgecolor="#212121", label="Rubble ('X')")
        )
        handles.append(
            mpatches.Patch(facecolor=self.terrain_colors[TerrainType.WATER], edgecolor="#0D47A1", label="Flood Water ('W')")
        )
        handles.append(
            mpatches.Patch(facecolor=self.terrain_colors[TerrainType.FIRE_ZONE], edgecolor="#BF360C", label="Fire Zone ('F')")
        )

        # Mystery states if KnowledgeGrid
        if isinstance(grid, KnowledgeGrid):
            handles.append(
                mpatches.Patch(facecolor=self.terrain_colors[TerrainType.UNKNOWN], edgecolor="#37474F", label="Unknown ('?')")
            )

        # Search Markers
        handles.append(
            mlines.Line2D(
                [], [], marker="o", color="w", markerfacecolor=START_COLOR,
                markeredgecolor="#1B5E20", markersize=10, label="Start ('S')"
            )
        )
        handles.append(
            mlines.Line2D(
                [], [], marker="o", color="w", markerfacecolor=GOAL_COLOR,
                markeredgecolor="#B71C1C", markersize=10, label="Goal ('G')"
            )
        )

        if has_search:
            handles.append(
                mpatches.Patch(facecolor=EXPLORED_COLOR, alpha=self.explored_alpha, edgecolor="none", label="Explored Nodes")
            )
            handles.append(
                mlines.Line2D(
                    [], [], color=PATH_COLOR, linewidth=3.5,
                    marker="o", markersize=6, markerfacecolor=PATH_COLOR,
                    markeredgecolor=PATH_BORDER_COLOR, label="Final Route"
                )
            )

        return handles

    def render_grid(
        self,
        grid: Grid,
        ax: Optional[matplotlib.axes.Axes] = None,
        start: Optional[Position] = None,
        goal: Optional[Position] = None,
        title: Optional[str] = None,
        show_coordinates: Optional[bool] = None,
        show_legend: Optional[bool] = None,
    ) -> Tuple[matplotlib.figure.Figure, matplotlib.axes.Axes]:
        """Render base 2D disaster grid with terrain fills, obstacles, and markers.

        Args:
            grid: Grid or KnowledgeGrid environment instance.
            ax: Optional Matplotlib Axes. If None, creates a new figure and axes.
            start: Optional start Position to highlight.
            goal: Optional goal Position to highlight.
            title: Optional plot title string.
            show_coordinates: Explicit coordinate toggle (defaults to class setting).
            show_legend: Explicit legend toggle (defaults to class setting).

        Returns:
            Tuple of (Figure, Axes).
        """
        if not isinstance(grid, Grid):
            raise TypeError(f"Expected Grid instance, got {type(grid).__name__}.")

        cols, rows = grid.cols, grid.rows

        # Auto-detect coordinate display if not explicitly overridden
        if show_coordinates is None:
            coord_toggle = (cols <= 20 and rows <= 20) if self.show_coordinates is None else self.show_coordinates
        else:
            coord_toggle = show_coordinates

        draw_legend = self.show_legend if show_legend is None else show_legend

        fig: matplotlib.figure.Figure
        if ax is None:
            width = max(5.0, cols * self.cell_size + (2.5 if draw_legend else 1.0))
            height = max(4.0, rows * self.cell_size + 1.2)
            fig, ax = plt.subplots(figsize=(width, height), dpi=100)
        else:
            fig = ax.get_figure()

        # Render cells
        edge_col = GRID_LINE_COLOR if self.show_grid_lines else "none"
        line_w = 0.8 if self.show_grid_lines else 0.0

        for r in range(rows):
            for c in range(cols):
                pos = Position(c, r)
                color, symbol, text_color = self._determine_cell_color_and_symbol(grid, pos)

                rect = mpatches.Rectangle(
                    (c - 0.5, r - 0.5), 1.0, 1.0,
                    facecolor=color, edgecolor=edge_col,
                    linewidth=line_w, zorder=1
                )
                ax.add_patch(rect)

                # Render hazard or mystery symbol
                if symbol is not None:
                    ax.text(
                        c, r, symbol,
                        ha="center", va="center",
                        fontsize=self.font_size + 2,
                        fontweight="bold", color=text_color,
                        zorder=2
                    )
                elif coord_toggle:
                    ax.text(
                        c, r, f"{c},{r}",
                        ha="center", va="center",
                        fontsize=max(5, self.font_size - 3),
                        color=text_color, alpha=0.75,
                        zorder=2
                    )

        # Coordinate axes setup
        ax.set_xlim(-0.5, cols - 0.5)
        ax.set_ylim(-0.5, rows - 0.5)
        ax.invert_yaxis()  # Row 0 at top to match screen / matrix coordinates
        ax.set_aspect("equal")

        ax.set_xticks(range(cols))
        ax.set_yticks(range(rows))
        ax.set_xlabel("Column (x)", fontsize=self.font_size, fontweight="bold")
        ax.set_ylabel("Row (y)", fontsize=self.font_size, fontweight="bold")
        ax.tick_params(labelsize=max(6, self.font_size - 2))

        # Start and Goal markers
        if start is not None and grid.is_inside(start):
            start_circle = mpatches.Circle(
                (start.x, start.y), 0.38,
                facecolor=START_COLOR, edgecolor="#1B5E20",
                linewidth=1.8, zorder=5
            )
            ax.add_patch(start_circle)
            ax.text(
                start.x, start.y, "S",
                ha="center", va="center",
                fontsize=self.font_size + 1, fontweight="bold",
                color="#FFFFFF", zorder=6
            )

        if goal is not None and grid.is_inside(goal):
            goal_circle = mpatches.Circle(
                (goal.x, goal.y), 0.38,
                facecolor=GOAL_COLOR, edgecolor="#B71C1C",
                linewidth=1.8, zorder=5
            )
            ax.add_patch(goal_circle)
            ax.text(
                goal.x, goal.y, "G",
                ha="center", va="center",
                fontsize=self.font_size + 1, fontweight="bold",
                color="#FFFFFF", zorder=6
            )

        if title is not None:
            ax.set_title(title, fontsize=self.font_size + 2, fontweight="bold", pad=12)

        if draw_legend:
            handles = self._build_legend_handles(grid, has_search=False)
            ax.legend(
                handles=handles,
                loc="upper left",
                bbox_to_anchor=(1.02, 1.0),
                borderaxespad=0.0,
                fontsize=max(7, self.font_size - 1),
                frameon=True,
                facecolor="#FAFAFA",
                edgecolor="#CFD8DC",
            )

        fig.tight_layout()
        return fig, ax

    def visualize_search(
        self,
        grid: Grid,
        result: Optional[SearchResult] = None,
        ax: Optional[matplotlib.axes.Axes] = None,
        title: Optional[str] = None,
        show_explored: bool = True,
        show_path: bool = True,
        show_coordinates: Optional[bool] = None,
        show_legend: Optional[bool] = None,
    ) -> Tuple[matplotlib.figure.Figure, matplotlib.axes.Axes]:
        """Visualize grid overlaid with search exploration wavefront and final discovered route.

        Args:
            grid: Simulation Grid or KnowledgeGrid.
            result: SearchResult from any pathfinding algorithm (BFS, DFS, UCS, A*, HC).
            ax: Optional Matplotlib Axes.
            title: Optional override title string.
            show_explored: Whether to draw light blue overlay on explored cells.
            show_path: Whether to draw the final route.
            show_coordinates: Coordinate toggle.
            show_legend: Legend toggle.

        Returns:
            Tuple of (Figure, Axes).
        """
        start_pos = result.start_position if result is not None else None
        goal_pos = result.goal_position if result is not None else None

        draw_legend = self.show_legend if show_legend is None else show_legend

        fig, ax = self.render_grid(
            grid=grid,
            ax=ax,
            start=start_pos,
            goal=goal_pos,
            title=None,
            show_coordinates=show_coordinates,
            show_legend=False,  # Legend added with search handles below
        )

        if result is not None:
            # 1. Explored cells overlay
            if show_explored and result.visited_order:
                for pos in result.visited_order:
                    # Do not obscure start or goal completely
                    if pos == start_pos or pos == goal_pos:
                        continue
                    if grid.is_inside(pos):
                        explored_patch = mpatches.Rectangle(
                            (pos.x - 0.5, pos.y - 0.5), 1.0, 1.0,
                            facecolor=EXPLORED_COLOR, alpha=self.explored_alpha,
                            edgecolor="none", zorder=3
                        )
                        ax.add_patch(explored_patch)

            # 2. Final path route
            if show_path and result.found and result.path and len(result.path) > 1:
                xs = [p.x for p in result.path]
                ys = [p.y for p in result.path]

                # Contrast under-stroke
                ax.plot(
                    xs, ys, color=PATH_BORDER_COLOR,
                    linewidth=5.0, solid_capstyle="round",
                    zorder=4
                )
                # Bright yellow foreground path
                ax.plot(
                    xs, ys, color=PATH_COLOR,
                    linewidth=3.2, marker="o",
                    markersize=6, markerfacecolor=PATH_COLOR,
                    markeredgecolor=PATH_BORDER_COLOR,
                    markeredgewidth=1.0, zorder=4
                )

            # Title construction
            if title is None:
                algo = result.algorithm_name
                if result.found:
                    cost_str = (
                        f"{result.total_cost:.1f}" if isinstance(result.total_cost, float) and result.total_cost.is_integer()
                        else str(result.total_cost)
                    )
                    constructed_title = (
                        f"[{algo}] Route Found\n"
                        f"Length: {result.path_length} steps | Cost: {cost_str} | Explored: {result.nodes_explored} nodes"
                    )
                else:
                    constructed_title = (
                        f"[{algo}] NO ROUTE FOUND (Search Failure)\n"
                        f"Explored: {result.nodes_explored} nodes | Path: None | Cost: None"
                    )
            else:
                constructed_title = title

            ax.set_title(constructed_title, fontsize=self.font_size + 1, fontweight="bold", pad=12)
        elif title is not None:
            ax.set_title(title, fontsize=self.font_size + 1, fontweight="bold", pad=12)

        if draw_legend:
            handles = self._build_legend_handles(grid, has_search=(result is not None))
            ax.legend(
                handles=handles,
                loc="upper left",
                bbox_to_anchor=(1.02, 1.0),
                borderaxespad=0.0,
                fontsize=max(7, self.font_size - 1),
                frameon=True,
                facecolor="#FAFAFA",
                edgecolor="#CFD8DC",
            )

        fig.tight_layout()
        return fig, ax

    def animate_search(
        self,
        grid: Grid,
        result: SearchResult,
        interval_ms: int = 50,
        repeat: bool = False,
        step_size: int = 1,
        ax: Optional[matplotlib.axes.Axes] = None,
    ) -> FuncAnimation:
        """Create a deterministic animation showing progressive exploration and path revelation.

        Animation phases:
        Phase 1: Progressively reveals explored cells in `result.visited_order`.
        Phase 2: If `result.found`, reveals the final route step-by-step from start to goal.
        Phase 3: Completed state with final performance metrics banner.
        If `not result.found`: Stops exploration and displays "NO ROUTE FOUND".

        Args:
            grid: Simulation Grid environment.
            result: SearchResult to animate.
            interval_ms: Milliseconds per animation frame.
            repeat: Whether the animation loops continuously.
            step_size: Number of explored nodes revealed per frame.
            ax: Optional Matplotlib Axes.

        Returns:
            Matplotlib FuncAnimation instance.
        """
        if not isinstance(result, SearchResult):
            raise TypeError(f"Expected SearchResult instance, got {type(result).__name__}.")

        start_pos = result.start_position
        goal_pos = result.goal_position

        fig, ax = self.render_grid(
            grid=grid,
            ax=ax,
            start=start_pos,
            goal=goal_pos,
            title=f"[{result.algorithm_name}] Initializing Search...",
            show_legend=self.show_legend,
        )

        visited = list(result.visited_order)
        path = list(result.path) if (result.found and result.path) else []

        # Prepare frame groups
        # Exploration frames: slice visited list in chunks of step_size
        step = max(1, int(step_size))
        explored_chunks: List[List[Position]] = []
        for i in range(0, len(visited), step):
            explored_chunks.append(visited[: i + step])
        if not explored_chunks:
            explored_chunks = [[]]

        # Path frames: progressively reveal path nodes
        path_chunks: List[List[Position]] = []
        if path:
            for i in range(1, len(path) + 1):
                path_chunks.append(path[:i])

        total_frames = len(explored_chunks) + len(path_chunks) + 5  # 5 freeze frames at end

        # Graphic artist containers
        explored_patches: List[mpatches.Rectangle] = []
        path_line_border, = ax.plot([], [], color=PATH_BORDER_COLOR, linewidth=5.0, solid_capstyle="round", zorder=4)
        path_line_core, = ax.plot(
            [], [], color=PATH_COLOR, linewidth=3.2,
            marker="o", markersize=6, markerfacecolor=PATH_COLOR,
            markeredgecolor=PATH_BORDER_COLOR, markeredgewidth=1.0, zorder=4
        )

        def init():
            for p in explored_patches:
                p.remove()
            explored_patches.clear()
            path_line_border.set_data([], [])
            path_line_core.set_data([], [])
            return [path_line_border, path_line_core]

        def update(frame_idx: int):
            # Phase 1: Exploration
            if frame_idx < len(explored_chunks):
                current_visited = explored_chunks[frame_idx]
                ax.set_title(
                    f"[{result.algorithm_name}] Searching... (Nodes Explored: {len(current_visited)})",
                    fontsize=self.font_size + 1, fontweight="bold", pad=12
                )
                # Add newly explored patches
                for pos in current_visited:
                    if pos == start_pos or pos == goal_pos:
                        continue
                    if grid.is_inside(pos):
                        p = mpatches.Rectangle(
                            (pos.x - 0.5, pos.y - 0.5), 1.0, 1.0,
                            facecolor=EXPLORED_COLOR, alpha=self.explored_alpha,
                            edgecolor="none", zorder=3
                        )
                        ax.add_patch(p)
                        explored_patches.append(p)

            # Phase 2: Route Revelation
            elif frame_idx < len(explored_chunks) + len(path_chunks):
                path_idx = frame_idx - len(explored_chunks)
                curr_path = path_chunks[path_idx]
                xs = [p.x for p in curr_path]
                ys = [p.y for p in curr_path]
                path_line_border.set_data(xs, ys)
                path_line_core.set_data(xs, ys)
                ax.set_title(
                    f"[{result.algorithm_name}] Revealing Path ({path_idx + 1}/{len(path)} steps)",
                    fontsize=self.font_size + 1, fontweight="bold", pad=12
                )

            # Phase 3: Final State
            else:
                if result.found and path:
                    xs = [p.x for p in path]
                    ys = [p.y for p in path]
                    path_line_border.set_data(xs, ys)
                    path_line_core.set_data(xs, ys)
                    cost_str = (
                        f"{result.total_cost:.1f}" if isinstance(result.total_cost, float) and result.total_cost.is_integer()
                        else str(result.total_cost)
                    )
                    ax.set_title(
                        f"[{result.algorithm_name}] COMPLETE | Steps: {result.path_length} | Cost: {cost_str} | Explored: {result.nodes_explored}",
                        fontsize=self.font_size + 1, fontweight="bold", pad=12
                    )
                else:
                    ax.set_title(
                        f"[{result.algorithm_name}] NO ROUTE FOUND (Search Exhausted / Dead End)",
                        fontsize=self.font_size + 1, fontweight="bold", pad=12
                    )

            return [path_line_border, path_line_core] + explored_patches

        anim = FuncAnimation(
            fig, update, init_func=init,
            frames=total_frames, interval=interval_ms,
            repeat=repeat, blit=False
        )
        anim._draw_was_started = True
        return anim

    def visualize_comparison(
        self,
        grid: Grid,
        results: List[SearchResult],
        ncols: int = 3,
        figsize: Optional[Tuple[float, float]] = None,
        show_explored: bool = True,
        show_path: bool = True,
    ) -> Tuple[matplotlib.figure.Figure, List[matplotlib.axes.Axes]]:
        """Render side-by-side comparative grid subplots for multiple search algorithm outcomes.

        Args:
            grid: Original simulation Grid.
            results: List of SearchResult objects to display side-by-side.
            ncols: Number of subplot columns per row.
            figsize: Total figure size (width, height) in inches.
            show_explored: Whether to draw explored cells on each subplot.
            show_path: Whether to draw final paths.

        Returns:
            Tuple of (Figure, List of Axes).
        """
        if not results:
            raise ValueError("Results list cannot be empty.")

        n_plots = len(results)
        cols_count = min(ncols, n_plots)
        rows_count = math.ceil(n_plots / cols_count)

        if figsize is None:
            fig_w = cols_count * max(4.0, grid.cols * 0.45 + 1.0)
            fig_h = rows_count * max(3.5, grid.rows * 0.45 + 1.2)
            fig_size = (fig_w, fig_h)
        else:
            fig_size = figsize

        fig, axes = plt.subplots(rows_count, cols_count, figsize=fig_size, dpi=100)
        axes_list: List[matplotlib.axes.Axes] = (
            list(axes.flatten()) if hasattr(axes, "flatten") else [axes]
        )

        for i, res in enumerate(results):
            ax = axes_list[i]
            # Subplot title
            cost_str = (
                f"{res.total_cost:.1f}" if isinstance(res.total_cost, float) and res.total_cost.is_integer()
                else str(res.total_cost)
            )
            status_tag = "SUCCESS" if res.found else "FAILED"
            sub_title = (
                f"[{res.algorithm_name}] {status_tag}\n"
                f"Steps: {res.path_length if res.found else 'N/A'} | Cost: {cost_str if res.found else 'N/A'} | Explored: {res.nodes_explored}"
            )

            self.visualize_search(
                grid=grid,
                result=res,
                ax=ax,
                title=sub_title,
                show_explored=show_explored,
                show_path=show_path,
                show_coordinates=False,  # Keep multi-plot clean
                show_legend=False,
            )

        # Hide extra unused subplots
        for j in range(n_plots, len(axes_list)):
            axes_list[j].set_visible(False)

        # Single unified legend at the top
        handles = self._build_legend_handles(grid, has_search=True)
        fig.legend(
            handles=handles,
            loc="lower center",
            bbox_to_anchor=(0.5, 0.0),
            ncol=min(6, len(handles)),
            fontsize=self.font_size - 1,
            frameon=True,
            facecolor="#FAFAFA",
        )

        fig.tight_layout()
        fig.subplots_adjust(bottom=0.12)
        return fig, axes_list[:n_plots]

    def plot_performance_charts(
        self,
        report_or_results: Union[ComparisonReport, List[SearchResult]],
        figsize: Tuple[float, float] = (12, 8),
        title: Optional[str] = "AI Pathfinding Performance Benchmarks",
    ) -> Tuple[matplotlib.figure.Figure, Any]:
        """Generate a 2x2 grid of bar charts comparing performance metrics across algorithms.

        Charts:
        1. Top-Left: Nodes Explored (Search Effort / State Expansions)
        2. Top-Right: Execution Time in milliseconds (Wall-Clock Runtime)
        3. Bottom-Left: Path Length in movement steps (Unweighted Step Count)
        4. Bottom-Right: Total Path Cost (Weighted Movement Cost)

        Handles missing values and search failures correctly without misleading zero values.

        Args:
            report_or_results: ComparisonReport instance or list of SearchResult instances.
            figsize: Figure size tuple (width, height) in inches.
            title: Overall figure suptitle.

        Returns:
            Tuple of (Figure, 2x2 Axes array).
        """
        # Parse records
        records: List[Dict[str, Any]] = []
        if isinstance(report_or_results, ComparisonReport):
            for rec in report_or_results:
                records.append({
                    "name": rec.algorithm,
                    "found": rec.solution_found,
                    "nodes": rec.nodes_explored,
                    "time_ms": rec.execution_time_ms,
                    "length": rec.path_length,
                    "cost": rec.total_cost,
                })
        elif isinstance(report_or_results, list):
            for item in report_or_results:
                if not isinstance(item, SearchResult):
                    raise TypeError(f"Expected SearchResult in list, got {type(item).__name__}.")
                # Guard against CSP results
                if "csp" in item.algorithm_name.lower():
                    raise ValueError(
                        "CSP multi-agent allocation cannot be benchmarked in spatial pathfinding charts."
                    )
                records.append({
                    "name": item.algorithm_name,
                    "found": item.found,
                    "nodes": item.nodes_explored,
                    "time_ms": item.execution_time_ms,
                    "length": item.path_length if item.found else None,
                    "cost": item.total_cost if item.found else None,
                })
        else:
            raise TypeError(
                f"Expected ComparisonReport or List[SearchResult], got {type(report_or_results).__name__}."
            )

        if not records:
            raise ValueError("No records provided to plot performance charts.")

        names = [r["name"] for r in records]
        x_indices = range(len(names))

        # Consistent palette for algorithms
        algo_palette = ["#1976D2", "#388E3C", "#F57C00", "#7B1FA2", "#C2185B", "#00796B"]
        colors = [algo_palette[i % len(algo_palette)] for i in range(len(names))]

        fig, axes = plt.subplots(2, 2, figsize=figsize, dpi=100)

        # -------------------------------------------------------------
        # 1. Nodes Explored (Search Effort)
        # -------------------------------------------------------------
        ax_nodes = axes[0, 0]
        nodes_vals = [r["nodes"] for r in records]
        bars_nodes = ax_nodes.bar(x_indices, nodes_vals, color=colors, edgecolor="#212121", linewidth=0.8)
        ax_nodes.set_title("Search Effort: Nodes Explored", fontsize=11, fontweight="bold")
        ax_nodes.set_ylabel("Expanded States Count", fontsize=10)
        ax_nodes.set_xticks(x_indices)
        ax_nodes.set_xticklabels(names, rotation=20, ha="right", fontsize=9)
        ax_nodes.grid(axis="y", linestyle="--", alpha=0.5)

        for bar, val in zip(bars_nodes, nodes_vals):
            ax_nodes.annotate(
                f"{val}",
                xy=(bar.get_x() + bar.get_width() / 2, bar.get_height()),
                xytext=(0, 3), textcoords="offset points",
                ha="center", va="bottom", fontsize=8, fontweight="bold"
            )

        # -------------------------------------------------------------
        # 2. Execution Time (ms)
        # -------------------------------------------------------------
        ax_time = axes[0, 1]
        time_vals = [r["time_ms"] for r in records]
        bars_time = ax_time.bar(x_indices, time_vals, color=colors, edgecolor="#212121", linewidth=0.8)
        ax_time.set_title("Runtime: Execution Time (ms)", fontsize=11, fontweight="bold")
        ax_time.set_ylabel("Wall-Clock Time (ms)", fontsize=10)
        ax_time.set_xticks(x_indices)
        ax_time.set_xticklabels(names, rotation=20, ha="right", fontsize=9)
        ax_time.grid(axis="y", linestyle="--", alpha=0.5)

        for bar, val in zip(bars_time, time_vals):
            ax_time.annotate(
                f"{val:.3f} ms",
                xy=(bar.get_x() + bar.get_width() / 2, bar.get_height()),
                xytext=(0, 3), textcoords="offset points",
                ha="center", va="bottom", fontsize=8, fontweight="bold"
            )

        # -------------------------------------------------------------
        # 3. Path Length (Number of Steps)
        # -------------------------------------------------------------
        ax_len = axes[1, 0]
        len_vals = [r["length"] if r["length"] is not None else 0 for r in records]
        bars_len = ax_len.bar(x_indices, len_vals, color=colors, edgecolor="#212121", linewidth=0.8)
        ax_len.set_title("Path Length: Movement Steps", fontsize=11, fontweight="bold")
        ax_len.set_ylabel("Number of Steps", fontsize=10)
        ax_len.set_xticks(x_indices)
        ax_len.set_xticklabels(names, rotation=20, ha="right", fontsize=9)
        ax_len.grid(axis="y", linestyle="--", alpha=0.5)

        # Annotate values or mark N/A for failed searches
        max_len = max(len_vals) if len_vals else 1
        for bar, r in zip(bars_len, records):
            if r["found"] and r["length"] is not None:
                ax_len.annotate(
                    f"{r['length']}",
                    xy=(bar.get_x() + bar.get_width() / 2, bar.get_height()),
                    xytext=(0, 3), textcoords="offset points",
                    ha="center", va="bottom", fontsize=8, fontweight="bold"
                )
            else:
                bar.set_hatch("//")
                bar.set_alpha(0.3)
                ax_len.annotate(
                    "N/A (Failed)",
                    xy=(bar.get_x() + bar.get_width() / 2, 0.05 * max_len),
                    xytext=(0, 5), textcoords="offset points",
                    ha="center", va="bottom", fontsize=8, color="#D32F2F", fontweight="bold"
                )

        # -------------------------------------------------------------
        # 4. Total Path Cost (Weighted Terrain Cost)
        # -------------------------------------------------------------
        ax_cost = axes[1, 1]
        cost_vals = [float(r["cost"]) if r["cost"] is not None else 0.0 for r in records]
        bars_cost = ax_cost.bar(x_indices, cost_vals, color=colors, edgecolor="#212121", linewidth=0.8)
        ax_cost.set_title("Path Quality: Total Movement Cost", fontsize=11, fontweight="bold")
        ax_cost.set_ylabel("Accumulated Terrain Cost", fontsize=10)
        ax_cost.set_xticks(x_indices)
        ax_cost.set_xticklabels(names, rotation=20, ha="right", fontsize=9)
        ax_cost.grid(axis="y", linestyle="--", alpha=0.5)

        max_cost = max(cost_vals) if cost_vals else 1.0
        for bar, r in zip(bars_cost, records):
            if r["found"] and r["cost"] is not None:
                cost_num = r["cost"]
                txt = f"{cost_num:.1f}" if isinstance(cost_num, float) and cost_num.is_integer() else f"{cost_num:.2f}"
                ax_cost.annotate(
                    txt,
                    xy=(bar.get_x() + bar.get_width() / 2, bar.get_height()),
                    xytext=(0, 3), textcoords="offset points",
                    ha="center", va="bottom", fontsize=8, fontweight="bold"
                )
            else:
                bar.set_hatch("//")
                bar.set_alpha(0.3)
                ax_cost.annotate(
                    "N/A (No Path)",
                    xy=(bar.get_x() + bar.get_width() / 2, 0.05 * max_cost),
                    xytext=(0, 5), textcoords="offset points",
                    ha="center", va="bottom", fontsize=8, color="#D32F2F", fontweight="bold"
                )

        if title is not None:
            fig.suptitle(title, fontsize=14, fontweight="bold", y=0.98)

        fig.tight_layout()
        fig.subplots_adjust(top=0.92)
        return fig, axes


# Convenience Module-Level Functional APIs

def visualize_grid(
    grid: Grid,
    start: Optional[Position] = None,
    goal: Optional[Position] = None,
    title: Optional[str] = None,
    **kwargs: Any,
) -> Tuple[matplotlib.figure.Figure, matplotlib.axes.Axes]:
    """Convenience helper to render a 2D grid."""
    viz = GridVisualizer(**kwargs)
    return viz.render_grid(grid, start=start, goal=goal, title=title)


def visualize_search(
    grid: Grid,
    result: Optional[SearchResult] = None,
    title: Optional[str] = None,
    **kwargs: Any,
) -> Tuple[matplotlib.figure.Figure, matplotlib.axes.Axes]:
    """Convenience helper to render a search exploration and route."""
    viz = GridVisualizer(**kwargs)
    return viz.visualize_search(grid, result=result, title=title)


def animate_search(
    grid: Grid,
    result: SearchResult,
    interval_ms: int = 50,
    repeat: bool = False,
    **kwargs: Any,
) -> FuncAnimation:
    """Convenience helper to create a search animation."""
    viz = GridVisualizer(**kwargs)
    return viz.animate_search(grid, result=result, interval_ms=interval_ms, repeat=repeat)


def visualize_comparison(
    grid: Grid,
    results: List[SearchResult],
    ncols: int = 3,
    **kwargs: Any,
) -> Tuple[matplotlib.figure.Figure, List[matplotlib.axes.Axes]]:
    """Convenience helper to render side-by-side comparison subplots."""
    viz = GridVisualizer(**kwargs)
    return viz.visualize_comparison(grid, results=results, ncols=ncols)


def plot_performance_charts(
    report_or_results: Union[ComparisonReport, List[SearchResult]],
    figsize: Tuple[float, float] = (12, 8),
    title: Optional[str] = "AI Pathfinding Performance Benchmarks",
) -> Tuple[matplotlib.figure.Figure, Any]:
    """Convenience helper to render 2x2 performance metric comparison charts."""
    viz = GridVisualizer()
    return viz.plot_performance_charts(report_or_results, figsize=figsize, title=title)
