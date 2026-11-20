"""
Re-export custom exceptions for backwards compatibility with core package consumers.
"""

from models.exceptions import (
    RescueGridError,
    DuplicateEntityError,
    EntityNotFoundError,
    ResourceUnavailableError,
    InvalidStatusTransitionError,
    LogicError,
)

__all__ = [
    "RescueGridError",
    "DuplicateEntityError",
    "EntityNotFoundError",
    "ResourceUnavailableError",
    "InvalidStatusTransitionError",
    "LogicError",
]
