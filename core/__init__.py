"""
Core package for RescueGrid simulation management and coordination.
"""

from core.exceptions import (
    RescueGridError,
    DuplicateEntityError,
    EntityNotFoundError,
    ResourceUnavailableError,
    InvalidStatusTransitionError,
    LogicError,
)
from core.rescue_manager import RescueManager

__all__ = [
    "RescueManager",
    "RescueGridError",
    "DuplicateEntityError",
    "EntityNotFoundError",
    "ResourceUnavailableError",
    "InvalidStatusTransitionError",
    "LogicError",
]
