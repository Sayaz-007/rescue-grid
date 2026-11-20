"""
RescueVehicle model representing emergency response vehicles in RescueGrid.
"""

from enum import Enum
from typing import Any, Union
from models.position import Position


class VehicleType(str, Enum):
    """Classification of emergency response vehicles in the fleet."""
    FIRE_ENGINE = "FireEngine"
    AMBULANCE = "Ambulance"
    RESCUE_VAN = "RescueVan"

    # CamelCase aliases for C++ convention compatibility
    FireEngine = "FireEngine"
    Ambulance = "Ambulance"
    RescueVan = "RescueVan"


class RescueVehicle:
    """Represents a specialized rescue vehicle operating on the grid.

    Encapsulates the vehicle identifier, vehicular classification,
    current coordinates, and operational deployment availability.
    """

    def __init__(
        self,
        vehicle_id: str,
        vehicle_type: VehicleType,
        position: Position,
        is_available: bool = True,
    ) -> None:
        """Initialize and validate a RescueVehicle.

        Args:
            vehicle_id: Unique vehicle identifier.
            vehicle_type: Vehicle classification from VehicleType enum.
            position: Initial grid Position.
            is_available: Initial operational availability (default: True).

        Raises:
            ValueError: If vehicle_id is empty.
            TypeError: If position or vehicle_type has an invalid type.
        """
        if not vehicle_id or not vehicle_id.strip():
            raise ValueError("Vehicle ID cannot be empty.")

        if not isinstance(position, Position):
            raise TypeError("Vehicle position must be an instance of Position.")

        if not isinstance(vehicle_type, VehicleType):
            raise TypeError("Vehicle type must be a VehicleType enum value.")

        self._id: str = vehicle_id.strip()
        self._type: VehicleType = vehicle_type
        self._position: Position = position
        self._is_available: bool = bool(is_available)

    # Property accessors
    @property
    def id(self) -> str:
        """Return the unique vehicle identifier."""
        return self._id

    @property
    def type(self) -> VehicleType:
        """Return the vehicle classification enum."""
        return self._type

    @property
    def position(self) -> Position:
        """Return the current grid position."""
        return self._position

    # Getter methods (PEP 8 and C++ naming)
    def get_id(self) -> str:
        """Return the unique vehicle identifier."""
        return self._id

    def get_type(self) -> VehicleType:
        """Return the vehicle classification."""
        return self._type

    def get_position(self) -> Position:
        """Return the current grid position."""
        return self._position

    def is_available(self) -> bool:
        """Return True if available for deployment, False otherwise."""
        return self._is_available

    def set_position(self, new_position: Union[Position, int], y: int | None = None) -> None:
        """Update vehicle position.

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
        """Set fleet availability status."""
        self._is_available = bool(available)

    def get_type_string(self) -> str:
        """Return human-readable string for the vehicle type."""
        if self._type in (VehicleType.FIRE_ENGINE, VehicleType.FireEngine):
            return "FireEngine"
        if self._type in (VehicleType.AMBULANCE, VehicleType.Ambulance):
            return "Ambulance"
        if self._type in (VehicleType.RESCUE_VAN, VehicleType.RescueVan):
            return "RescueVan"
        return "Unknown"

    def to_string(self) -> str:
        """Return formatted string detailing rescue vehicle state."""
        return (
            f"RescueVehicle [ID: {self._id}, Type: {self.get_type_string()}, "
            f"Location: {self._position.to_string()}, "
            f"Available: {'Yes' if self._is_available else 'No'}]"
        )

    def display(self) -> None:
        """Print vehicle details to standard output."""
        print(self.to_string())

    def __str__(self) -> str:
        return self.to_string()

    def __repr__(self) -> str:
        return (
            f"RescueVehicle(id='{self._id}', type={self._type!r}, "
            f"position={self._position!r}, is_available={self._is_available})"
        )

    # C++ compatibility aliases
    getId = get_id
    getType = get_type
    getPosition = get_position
    isAvailable = is_available
    setPosition = set_position
    setAvailability = set_availability
    getTypeString = get_type_string
    toString = to_string
