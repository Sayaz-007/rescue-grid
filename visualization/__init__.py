"""
RescueGrid Visualization Package.

Provides 2D grid rendering, search exploration overlays, route animations,
and comparative performance charts using Matplotlib.
"""

from visualization.grid_visualizer import (
    DEFAULT_TERRAIN_COLORS,
    GridVisualizer,
    visualize_grid,
    visualize_search,
    animate_search,
    visualize_comparison,
    plot_performance_charts,
)

__all__ = [
    "DEFAULT_TERRAIN_COLORS",
    "GridVisualizer",
    "visualize_grid",
    "visualize_search",
    "animate_search",
    "visualize_comparison",
    "plot_performance_charts",
]
