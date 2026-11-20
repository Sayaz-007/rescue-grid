"""
Responder model representing emergency response personnel in RescueGrid.
"""

from enum import Enum
from typing import Any, Union
from models.position import Position


class ResponderSpecialization(str, Enum):
    """Specialization categories for emergency response personnel."""
    FIREFIGHTER = "Firefighter"
    PARAMEDIC = "Paramedic"
    RESCUE_SPECIALIST = "RescueSpecialist"

    # CamelCase aliases for C++ convention compatibility
    Firefighter = "Firefighter"
    Paramedic = "Paramedic"
    RescueSpecialist = "RescueSpecialist"


class Responder:
    """Represents an individual emergency responder operating in the grid.

    Encapsulates responder identification, personnel name, specialization,
    current geographic coordinates, and operational availability status.
    """

    def __init__(
        self,
        responder_id: str,
        name: str,
        specialization: ResponderSpecialization,
        position: Position,
        is_available: bool = True,
    ) -> None:
        """Initialize and validate a Responder.

        Args:
            responder_id: Unique personnel code.
            name: Full name of the responder.
            specialization: Specialization from ResponderSpecialization enum.
            position: Initial grid Position.
            is_available: Initial operational availability (default: True).

        Raises:
            ValueError: If responder_id or name is empty.
            TypeError: If position or specialization has an invalid type.
        """
        if not responder_id or not responder_id.strip():
            raise ValueError("responder ID cannot be empty")

        if not name or not name.strip():
            raise ValueError("responder name cannot be empty")

        if not isinstance(position, Position):
            raise TypeError("Responder position must be an instance of Position.")

        if not isinstance(specialization, ResponderSpecialization):
            raise TypeError("Specialization must be a ResponderSpecialization enum value.")

        self._id: str = responder_id.strip()
        self._name: str = name.strip()
        self._specialization: ResponderSpecialization = specialization
        self._position: Position = position
        self._is_available: bool = bool(is_available)

    # Property accessors
    @property
    def id(self) -> str:
        """Return the unique responder identifier."""
        return self._id

    @property
    def name(self) -> str:
        """Return the responder's full name."""
        return self._name

    @property
    def specialization(self) -> ResponderSpecialization:
        """Return the specialization category enum."""
        return self._specialization

    @property
    def position(self) -> Position:
        """Return the current grid position."""
        return self._position

    # Getter methods (PEP 8 and C++ naming)
    def get_id(self) -> str:
        """Return the unique responder identifier."""
        return self._id

    def get_name(self) -> str:
        """Return the responder's full name."""
        return self._name

    def get_specialization(self) -> ResponderSpecialization:
        """Return the specialization category."""
        return self._specialization

    def get_position(self) -> Position:
        """Return the current grid position."""
        return self._position

    def is_available(self) -> bool:
        """Return True if available for deployment, False otherwise."""
        return self._is_available

    def set_position(self, new_position: Union[Position, int], y: int | None = None) -> None:
        """Update responder position.

        Supports multiple argument forms:
        - Passing a Position instance: set_position(Position(x, y))
        - Passing discrete coordinates: set_position(x, y)
        """
        if isinstance(new_position, Position):
            self._position = new_position
        elif (
            isinstance(new_position, int)
            and isinstance(y, int)
            and not isinstance(new_position, bool)
            and not isinstance(y, bool)
        ):
            self._position = Position(new_position, y)
        else:
            raise TypeError("Invalid position arguments. Expected Position or (int, int).")

    def set_availability(self, available: bool) -> None:
        """Set operational availability status."""
        self._is_available = bool(available)

    def get_specialization_string(self) -> str:
        """Return human-readable string for the specialization."""
        if self._specialization in (ResponderSpecialization.FIREFIGHTER, ResponderSpecialization.Firefighter):
            return "Firefighter"
        if self._specialization in (ResponderSpecialization.PARAMEDIC, ResponderSpecialization.Paramedic):
            return "Paramedic"
        if self._specialization in (ResponderSpecialization.RESCUE_SPECIALIST, ResponderSpecialization.RescueSpecialist):
            return "RescueSpecialist"
        return "Unknown"

    def to_string(self) -> str:
        """Return formatted string detailing responder state."""
        return (
            f"RESPONDER [ID: {self._id}, Name: {self._name}, "
            f"Specialization: {self.get_specialization_string()}, "
            f"Location: {self._position.to_string()}, "
            f"Available: {'Yes' if self._is_available else 'No'}]"
        )

    def display(self) -> None:
        """Print responder details to standard output."""
        print(self.to_string())

    def __str__(self) -> str:
        return self.to_string()

    def __repr__(self) -> str:
        return (
            f"Responder(id='{self._id}', name='{self._name}', "
            f"specialization={self._specialization!r}, "
            f"position={self._position!r}, is_available={self._is_available})"
        )

    # C++ compatibility aliases
    getId = get_id
    getName = get_name
    getSpecialization = get_specialization
    getPosition = get_position
    isAvailable = is_available
    setPosition = set_position
    setAvailability = set_availability
    getSpecializationString = get_specialization_string
    toString = to_string
