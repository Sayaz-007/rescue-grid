"""
Comprehensive Unit Tests for RescueGrid Visualizer & Path Animation (Phase 9.2).

Validates:
1. Object-oriented GridVisualizer creation and parameter configuration.
2. Distinct terrain color mapping and hazard symbols ('X', 'W', 'F').
3. Start ('S') and Goal ('G') marker positioning.
4. Explored-cell overlays and final path rendering.
5. Graceful handling of search failures and empty paths.
6. Grid immutability invariants across all visualization routines.
7. KnowledgeGrid mystery states ('?') rendering without ground-truth leakage.
8. Performance benchmark charts (2x2) with correct handling of missing/N/A metrics.
9. FuncAnimation generation for successful and failed search outcomes.
10. Headless operation with Matplotlib 'Agg' backend without graphical desktop requirement.
"""

import unittest
import warnings
from typing import Any, List
# Suppress expected headless animation deletion warnings
warnings.filterwarnings("ignore", category=UserWarning, module="matplotlib.animation")
import matplotlib
# Enforce non-interactive headless backend for automated tests
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from environment.cell import Cell, TerrainType
from environment.grid import Grid
from environment.actual_grid import ActualGrid
from environment.knowledge_grid import KnowledgeGrid
from models.position import Position
from algorithms.search_result import SearchResult
from algorithms.bfs import bfs
from algorithms.ucs import ucs
from algorithms.astar import astar
from algorithms.hill_climbing import hill_climbing
from analysis.algorithm_comparison import (
    compare_pathfinding_algorithms,
    create_scenario_a_open,
    create_scenario_c_weighted,
    create_scenario_d_no_solution,
)
from visualization.grid_visualizer import (
    DEFAULT_TERRAIN_COLORS,
    EXPLORED_COLOR,
    GOAL_COLOR,
    PATH_COLOR,
    START_COLOR,
    GridVisualizer,
    animate_search,
    plot_performance_charts,
    visualize_comparison,
    visualize_grid,
    visualize_search,
)


class TestGridVisualizerInitialization(unittest.TestCase):
    """Test Suite 1: Visualizer initialization and parameter validation."""

    def test_default_initialization(self) -> None:
        """Visualizer initializes with sensible defaults."""
        viz = GridVisualizer()
        self.assertEqual(viz.cell_size, 0.8)
        self.assertIsNone(viz.show_coordinates)
        self.assertTrue(viz.show_legend)
        self.assertTrue(viz.show_grid_lines)
        self.assertEqual(viz.font_size, 9)
        self.assertAlmostEqual(viz.explored_alpha, 0.45)
        self.assertEqual(viz.terrain_colors[TerrainType.ROAD], "#E0E0E0")

    def test_custom_parameters_and_clamping(self) -> None:
        """Visualizer clamps alpha and accepts custom parameters."""
        viz = GridVisualizer(
            cell_size=1.2,
            show_coordinates=True,
            show_legend=False,
            font_size=12,
            explored_alpha=1.5,  # Exceeds 1.0, should be clamped to 1.0
        )
        self.assertEqual(viz.cell_size, 1.2)
        self.assertTrue(viz.show_coordinates)
        self.assertFalse(viz.show_legend)
        self.assertEqual(viz.font_size, 12)
        self.assertEqual(viz.explored_alpha, 1.0)

    def test_custom_terrain_palette_override(self) -> None:
        """Custom terrain color dictionary overrides default palette."""
        custom_palette = dict(DEFAULT_TERRAIN_COLORS)
        custom_palette[TerrainType.ROAD] = "#FFFFFF"
        viz = GridVisualizer(terrain_colors=custom_palette)
        self.assertEqual(viz.terrain_colors[TerrainType.ROAD], "#FFFFFF")
        self.assertEqual(viz.terrain_colors[TerrainType.NORMAL], DEFAULT_TERRAIN_COLORS[TerrainType.NORMAL])


class TestGridRenderingAndTerrains(unittest.TestCase):
    """Test Suite 2: Terrain rendering, hazard symbols, markers, and axis conventions."""

    def setUp(self) -> None:
        self.grid = Grid(rows=6, cols=8, default_terrain=TerrainType.NORMAL)
        self.grid.add_road(Position(1, 1))
        self.grid.add_rough_terrain(Position(2, 2))
        self.grid.add_collapsed_building(Position(3, 3))
        self.grid.add_flood_zone(Position(4, 3))
        self.grid.add_fire_zone(Position(5, 3))
        self.grid.add_obstacle(Position(6, 3))
        self.start = Position(0, 0)
        self.goal = Position(7, 5)
        self.viz = GridVisualizer()

    def tearDown(self) -> None:
        plt.close("all")

    def test_all_terrain_types_and_symbols_rendered(self) -> None:
        """Verify each terrain type and hazard symbol ('X', 'W', 'F', '#') is rendered."""
        fig, ax = self.viz.render_grid(self.grid, start=self.start, goal=self.goal)
        self.assertIsNotNone(fig)
        self.assertIsNotNone(ax)

        # Total patches must include all cells (48 cells) + start + goal (2 circles)
        self.assertGreaterEqual(len(ax.patches), self.grid.total_cells)

        # Inspect cell color and symbol resolution directly
        c_road, s_road, _ = self.viz._determine_cell_color_and_symbol(self.grid, Position(1, 1))
        self.assertEqual(c_road, DEFAULT_TERRAIN_COLORS[TerrainType.ROAD])
        self.assertIsNone(s_road)

        c_rough, s_rough, _ = self.viz._determine_cell_color_and_symbol(self.grid, Position(2, 2))
        self.assertEqual(c_rough, DEFAULT_TERRAIN_COLORS[TerrainType.ROUGH])
        self.assertIsNone(s_rough)

        c_rubble, s_rubble, _ = self.viz._determine_cell_color_and_symbol(self.grid, Position(3, 3))
        self.assertEqual(c_rubble, DEFAULT_TERRAIN_COLORS[TerrainType.RUBBLE])
        self.assertEqual(s_rubble, "X")

        c_water, s_water, _ = self.viz._determine_cell_color_and_symbol(self.grid, Position(4, 3))
        self.assertEqual(c_water, DEFAULT_TERRAIN_COLORS[TerrainType.WATER])
        self.assertEqual(s_water, "W")

        c_fire, s_fire, _ = self.viz._determine_cell_color_and_symbol(self.grid, Position(5, 3))
        self.assertEqual(c_fire, DEFAULT_TERRAIN_COLORS[TerrainType.FIRE_ZONE])
        self.assertEqual(s_fire, "F")

        c_obs, s_obs, _ = self.viz._determine_cell_color_and_symbol(self.grid, Position(6, 3))
        self.assertEqual(s_obs, "#")

    def test_start_and_goal_markers_placement(self) -> None:
        """Start ('S') and Goal ('G') markers are placed at exact discrete coordinates."""
        fig, ax = self.viz.render_grid(self.grid, start=self.start, goal=self.goal)

        # Verify axis limits contain grid boundaries
        xlim = ax.get_xlim()
        ylim = ax.get_ylim()
        self.assertEqual(xlim[0], -0.5)
        self.assertEqual(xlim[1], self.grid.cols - 0.5)

        # Verify y-axis is inverted (row 0 at top)
        self.assertTrue(ax.yaxis_inverted())
        self.assertEqual(ylim[0], self.grid.rows - 0.5)
        self.assertEqual(ylim[1], -0.5)

    def test_axis_labels_and_ticks(self) -> None:
        """Axis labels follow RescueGrid column (x) and row (y) convention."""
        fig, ax = self.viz.render_grid(self.grid)
        self.assertEqual(ax.get_xlabel(), "Column (x)")
        self.assertEqual(ax.get_ylabel(), "Row (y)")
        self.assertEqual(len(ax.get_xticks()), self.grid.cols)
        self.assertEqual(len(ax.get_yticks()), self.grid.rows)

    def test_legend_creation(self) -> None:
        """Legend is added when show_legend=True."""
        fig, ax = self.viz.render_grid(self.grid, show_legend=True)
        self.assertIsNotNone(ax.get_legend())


class TestSearchVisualization(unittest.TestCase):
    """Test Suite 3: Search exploration wavefronts, paths, and failure reporting."""

    def setUp(self) -> None:
        self.grid = Grid(rows=6, cols=6, default_terrain=TerrainType.NORMAL)
        self.grid.add_road(Position(1, 1))
        self.start = Position(0, 0)
        self.goal = Position(5, 5)
        self.viz = GridVisualizer()

    def tearDown(self) -> None:
        plt.close("all")

    def test_successful_search_rendering(self) -> None:
        """Successful search displays explored cells and final bright yellow route."""
        result = astar(self.grid, self.start, self.goal)
        self.assertTrue(result.found)

        fig, ax = self.viz.visualize_search(self.grid, result)
        self.assertIsNotNone(fig)
        self.assertIn("A* Search", ax.get_title())
        self.assertIn("Route Found", ax.get_title())

        # Verify path line exists
        self.assertGreaterEqual(len(ax.lines), 2)  # Understroke + yellow core

    def test_failed_search_rendering(self) -> None:
        """Failed search shows explored cells, no fabricated path, and explicit failure title."""
        # Enclose goal completely
        for y in range(6):
            self.grid.add_collapsed_building(Position(4, y))

        result = astar(self.grid, self.start, self.goal)
        self.assertFalse(result.found)

        fig, ax = self.viz.visualize_search(self.grid, result)
        self.assertIn("NO ROUTE FOUND", ax.get_title())
        # Explored patches should exist
        self.assertGreater(result.nodes_explored, 0)
        # No path lines should be drawn
        self.assertEqual(len(ax.lines), 0)

    def test_empty_path_handling(self) -> None:
        """Empty path result handles gracefully without errors."""
        res = SearchResult("Custom BFS", self.start, self.goal, False, path=[])
        fig, ax = self.viz.visualize_search(self.grid, res)
        self.assertIn("NO ROUTE FOUND", ax.get_title())

    def test_start_equals_goal_search(self) -> None:
        """Trivial search where start == goal renders single node path."""
        res = SearchResult("UCS", self.start, self.start, True, path=[self.start], path_length=0, total_cost=0)
        fig, ax = self.viz.visualize_search(self.grid, res)
        self.assertTrue(res.found)

    def test_none_search_result(self) -> None:
        """Passing result=None renders base grid cleanly."""
        fig, ax = self.viz.visualize_search(self.grid, result=None, title="Base Disaster Map")
        self.assertEqual(ax.get_title(), "Base Disaster Map")


class TestGridImmutability(unittest.TestCase):
    """Test Suite 4: Verifying visualizer operations never mutate underlying grid."""

    def setUp(self) -> None:
        self.grid = Grid(rows=7, cols=10, default_terrain=TerrainType.NORMAL)
        self.grid.add_road(Position(2, 2))
        self.grid.add_rough_terrain(Position(3, 3))
        self.grid.add_collapsed_building(Position(4, 4))
        self.start = Position(0, 0)
        self.goal = Position(9, 6)
        self.viz = GridVisualizer()

    def tearDown(self) -> None:
        plt.close("all")

    def _snapshot_grid(self, grid: Grid) -> List[Any]:
        return [
            (c, r, grid.get_cell(Position(c, r)).terrain, grid.is_walkable(Position(c, r)), grid.get_movement_cost(Position(c, r)))
            for r in range(grid.rows)
            for c in range(grid.cols)
        ]

    def test_grid_remains_unchanged_after_all_visualizations(self) -> None:
        """All visualizer methods guarantee 100% read-only grid access."""
        before = self._snapshot_grid(self.grid)

        # 1. Base rendering
        self.viz.render_grid(self.grid, start=self.start, goal=self.goal)
        self.assertEqual(self._snapshot_grid(self.grid), before)

        # 2. Search visualization
        res = astar(self.grid, self.start, self.goal)
        self.viz.visualize_search(self.grid, res)
        self.assertEqual(self._snapshot_grid(self.grid), before)

        # 3. Multi-algorithm comparison
        res_bfs = bfs(self.grid, self.start, self.goal)
        self.viz.visualize_comparison(self.grid, [res_bfs, res])
        self.assertEqual(self._snapshot_grid(self.grid), before)

        # 4. Search animation
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            _anim = self.viz.animate_search(self.grid, res)
        self.assertEqual(self._snapshot_grid(self.grid), before)


class TestKnowledgeGridSupport(unittest.TestCase):
    """Test Suite 5: KnowledgeGrid rendering in partial-observability scenarios."""

    def tearDown(self) -> None:
        plt.close("all")

    def test_knowledge_grid_mystery_cells_rendered_correctly(self) -> None:
        """Unknown mystery cells are rendered in dark slate grey with '?' without leaking ground truth."""
        actual = ActualGrid(6, 6)
        actual.add_road(Position(1, 1))
        actual.add_collapsed_building(Position(2, 2))

        kg = KnowledgeGrid(6, 6)
        kg.reveal_cell(Position(0, 0), actual)
        kg.reveal_cell(Position(1, 1), actual)

        viz = GridVisualizer()

        # Unrevealed cell (2, 2) has collapsed building in ActualGrid, but must be UNKNOWN in KnowledgeGrid
        color, symbol, _ = viz._determine_cell_color_and_symbol(kg, Position(2, 2))
        self.assertEqual(color, DEFAULT_TERRAIN_COLORS[TerrainType.UNKNOWN])
        self.assertEqual(symbol, "?")

        # Revealed cell (1, 1) is ROAD
        color_road, symbol_road, _ = viz._determine_cell_color_and_symbol(kg, Position(1, 1))
        self.assertEqual(color_road, DEFAULT_TERRAIN_COLORS[TerrainType.ROAD])
        self.assertIsNone(symbol_road)

        fig, ax = viz.render_grid(kg)
        self.assertIsNotNone(fig)


class TestSideBySideComparisonAndCharts(unittest.TestCase):
    """Test Suite 6: Multi-algorithm side-by-side grids and 2x2 performance charts."""

    def setUp(self) -> None:
        self.scenario = create_scenario_c_weighted()
        self.grid = self.scenario.grid
        self.start = self.scenario.start
        self.goal = self.scenario.goal
        self.viz = GridVisualizer()

    def tearDown(self) -> None:
        plt.close("all")

    def test_visualize_comparison_creates_subplots(self) -> None:
        """visualize_comparison creates expected number of subplots with proper labels."""
        r_bfs = bfs(self.grid, self.start, self.goal)
        r_ucs = ucs(self.grid, self.start, self.goal)
        r_ast = astar(self.grid, self.start, self.goal)

        fig, axes = self.viz.visualize_comparison(self.grid, [r_bfs, r_ucs, r_ast], ncols=3)
        self.assertEqual(len(axes), 3)
        self.assertIn("Breadth-First Search", axes[0].get_title())
        self.assertIn("Uniform-Cost Search", axes[1].get_title())
        self.assertIn("A* Search", axes[2].get_title())

    def test_plot_performance_charts_with_search_results(self) -> None:
        """plot_performance_charts generates 2x2 bar chart grid from SearchResult list."""
        r_bfs = bfs(self.grid, self.start, self.goal)
        r_ucs = ucs(self.grid, self.start, self.goal)
        r_ast = astar(self.grid, self.start, self.goal)

        fig, axes = self.viz.plot_performance_charts([r_bfs, r_ucs, r_ast])
        self.assertEqual(axes.shape, (2, 2))
        self.assertIn("Nodes Explored", axes[0, 0].get_title())
        self.assertIn("Execution Time", axes[0, 1].get_title())
        self.assertIn("Path Length", axes[1, 0].get_title())
        self.assertIn("Total Movement Cost", axes[1, 1].get_title())

    def test_plot_performance_charts_with_comparison_report(self) -> None:
        """plot_performance_charts accepts ComparisonReport directly."""
        report = self.scenario.run()
        fig, axes = self.viz.plot_performance_charts(report)
        self.assertEqual(axes.shape, (2, 2))

    def test_plot_performance_charts_handles_missing_metrics_gracefully(self) -> None:
        """Unsuccessful searches display 'N/A' annotations rather than misleading zero bars."""
        sc_d = create_scenario_d_no_solution()
        report_d = sc_d.run()

        fig, axes = self.viz.plot_performance_charts(report_d)
        self.assertEqual(axes.shape, (2, 2))

    def test_csp_rejected_from_pathfinding_charts(self) -> None:
        """Attempting to chart CSP multi-agent results raises ValueError."""
        csp_dummy = SearchResult("CSP Multi-Agent Allocation", self.start, self.goal, True, [])
        with self.assertRaises(ValueError) as ctx:
            self.viz.plot_performance_charts([csp_dummy])
        self.assertIn("CSP", str(ctx.exception))


class TestAnimationCreation(unittest.TestCase):
    """Test Suite 7: FuncAnimation generation and edge case handling."""

    def setUp(self) -> None:
        self.grid = Grid(rows=5, cols=5, default_terrain=TerrainType.NORMAL)
        self.start = Position(0, 0)
        self.goal = Position(4, 4)
        self.viz = GridVisualizer()

    def tearDown(self) -> None:
        plt.close("all")

    def test_animation_creation_success(self) -> None:
        """animate_search creates deterministic FuncAnimation without errors."""
        res = astar(self.grid, self.start, self.goal)
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            anim = self.viz.animate_search(self.grid, res, interval_ms=30)
        self.assertIsNotNone(anim)

    def test_animation_handles_failed_search(self) -> None:
        """animate_search handles unsuccessful search result without crashing."""
        for y in range(5):
            self.grid.add_collapsed_building(Position(3, y))
        res = astar(self.grid, self.start, self.goal)
        self.assertFalse(res.found)

        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            anim = self.viz.animate_search(self.grid, res)
        self.assertIsNotNone(anim)

    def test_animation_handles_empty_path(self) -> None:
        """animate_search handles empty path gracefully."""
        res = SearchResult("BFS", self.start, self.goal, False, path=[], visited_order=[self.start])
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            anim = self.viz.animate_search(self.grid, res)
        self.assertIsNotNone(anim)


class TestInputValidationAndFunctionalAPIs(unittest.TestCase):
    """Test Suite 8: Type checking, validation, and module-level functional helpers."""

    def tearDown(self) -> None:
        plt.close("all")

    def test_render_grid_invalid_type(self) -> None:
        """Non-Grid input raises TypeError."""
        viz = GridVisualizer()
        with self.assertRaises(TypeError):
            viz.render_grid("not_a_grid")

    def test_animate_search_invalid_result_type(self) -> None:
        """Non-SearchResult input raises TypeError."""
        viz = GridVisualizer()
        grid = Grid(4, 4)
        with self.assertRaises(TypeError):
            viz.animate_search(grid, "not_a_result")

    def test_visualize_comparison_empty_list(self) -> None:
        """Empty results list raises ValueError."""
        viz = GridVisualizer()
        grid = Grid(4, 4)
        with self.assertRaises(ValueError):
            viz.visualize_comparison(grid, [])

    def test_plot_performance_charts_invalid_type(self) -> None:
        """Invalid container type raises TypeError."""
        viz = GridVisualizer()
        with self.assertRaises(TypeError):
            viz.plot_performance_charts("invalid_container")

    def test_module_level_convenience_functions(self) -> None:
        """Module-level helpers visualize_grid, visualize_search, etc. work identically."""
        grid = Grid(4, 4)
        s, g = Position(0, 0), Position(3, 3)

        fig1, ax1 = visualize_grid(grid, start=s, goal=g)
        self.assertIsNotNone(fig1)

        res = bfs(grid, s, g)
        fig2, ax2 = visualize_search(grid, res)
        self.assertIsNotNone(fig2)

        fig3, axes3 = visualize_comparison(grid, [res])
        self.assertEqual(len(axes3), 1)

        fig4, axes4 = plot_performance_charts([res])
        self.assertEqual(axes4.shape, (2, 2))


if __name__ == "__main__":
    unittest.main()
