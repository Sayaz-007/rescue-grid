"""
Discrete 2D position representation for the RescueGrid simulation.
"""

from typing import Any


class Position:
    """Represents a 2D discrete coordinate (x, y) on the simulation grid.

    Position encapsulates integer x and y coordinates, ensuring that location
    data remains grouped, validated, and accessible.
    """

    def __init__(self, x: int = 0, y: int = 0) -> None:
        """Initialize a Position with integer coordinates (defaults to 0, 0).
        
        Args:
            x: Integer x-coordinate (default: 0).
            y: Integer y-coordinate (default: 0).

        Raises:
            TypeError: If x or y is not an integer (or is a boolean).
        """
        if not isinstance(x, int) or isinstance(x, bool):
            raise TypeError("Position X coordinate must be an integer.")
        if not isinstance(y, int) or isinstance(y, bool):
            raise TypeError("Position Y coordinate must be an integer.")
        self._x: int = x
        self._y: int = y

    @property
    def x(self) -> int:
        """Return the discrete X coordinate."""
        return self._x

    @property
    def y(self) -> int:
        """Return the discrete Y coordinate."""
        return self._y

    def get_x(self) -> int:
        """Return the discrete X coordinate (getter method)."""
        return self._x

    def get_y(self) -> int:
        """Return the discrete Y coordinate (getter method)."""
        return self._y

    # C++ compatibility aliases
    getX = get_x
    getY = get_y

    def to_string(self) -> str:
        """Return formatted coordinate string representation: '(x, y)'."""
        return f"({self._x}, {self._y})"

    # C++ compatibility alias
    toString = to_string

    def display(self) -> None:
        """Print the string representation to standard output."""
        print(self.to_string())

    def __str__(self) -> str:
        """Return standard user-facing string representation."""
        return self.to_string()

    def __repr__(self) -> str:
        """Return canonical string representation for debugging."""
        return f"Position({self._x}, {self._y})"

    def __eq__(self, other: Any) -> bool:
        """Check equality with another Position object.
        
        Returns True if and only if both X and Y coordinates match.
        """
        if not isinstance(other, Position):
            return False
        return self._x == other._x and self._y == other._y

    def __ne__(self, other: Any) -> bool:
        """Check inequality with another Position object.
        
        Logically equivalent to not (self == other).
        """
        return not (self == other)

    def __hash__(self) -> int:
        """Support hashing for use as dictionary keys or in sets."""
        return hash((self._x, self._y))
