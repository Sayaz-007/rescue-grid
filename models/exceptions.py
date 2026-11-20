"""
Custom exception hierarchy for the RescueGrid disaster response simulation.
Defined in models to ensure clean unidirectional architecture (core -> models)
and prevent circular imports.
"""


class RescueGridError(Exception):
    """Base exception class for all RescueGrid domain errors."""
    pass


class DuplicateEntityError(RescueGridError, ValueError):
    """Raised when registering an entity with an existing ID."""
    pass


class EntityNotFoundError(RescueGridError, ValueError):
    """Raised when an incident, responder, or vehicle cannot be found."""
    pass


class ResourceUnavailableError(RescueGridError, RuntimeError):
    """Raised when no responder or rescue vehicle is available for dispatch."""
    pass


class InvalidStatusTransitionError(RescueGridError, RuntimeError):
    """Raised when an invalid incident lifecycle status transition is attempted."""
    pass


# Compatibility alias
LogicError = InvalidStatusTransitionError
