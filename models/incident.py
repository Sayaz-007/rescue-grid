"""
Incident model representing emergency events in the RescueGrid simulation.
"""

from enum import Enum
from typing import Any, Optional
from models.position import Position
from models.responder import ResponderSpecialization
from models.rescue_vehicle import VehicleType
from models.exceptions import InvalidStatusTransitionError


class IncidentType(str, Enum):
    """Categorization of emergency incidents occurring in the grid."""
    FIRE = "Fire"
    FLOOD = "Flood"
    STRUCTURAL_COLLAPSE = "StructuralCollapse"
    MEDICAL = "Medical"

    # CamelCase aliases for C++ convention compatibility
    Fire = "Fire"
    Flood = "Flood"
    StructuralCollapse = "StructuralCollapse"
    Medical = "Medical"


class IncidentStatus(str, Enum):
    """Lifecycle status of an emergency incident."""
    REPORTED = "Reported"
    IN_PROGRESS = "InProgress"
    RESOLVED = "Resolved"
    FAILED = "Failed"

    # CamelCase aliases for C++ convention compatibility
    Reported = "Reported"
    InProgress = "InProgress"
    Resolved = "Resolved"
    Failed = "Failed"


class Incident:
    """Represents an active urban emergency event.

    Encapsulates the incident identifier, emergency type, validated severity
    rating (1 to 5), grid coordinates (Position), lifecycle status, and
    assigned resource identifiers.
    """

    def __init__(
        self,
        incident_id: str,
        incident_type: IncidentType,
        severity: int,
        position: Position,
        status: IncidentStatus = IncidentStatus.REPORTED,
        required_specialization: Optional[ResponderSpecialization] = None,
        required_vehicle_type: Optional[VehicleType] = None,
    ) -> None:
        """Initialize and validate an emergency Incident.

        Args:
            incident_id: Unique string identifier for the incident.
            incident_type: Classification from IncidentType enum.
            severity: Emergency severity level (integer 1 to 5).
            position: Grid coordinate Position object.
            status: Initial lifecycle status (default: IncidentStatus.REPORTED).
            required_specialization: Optional specific responder specialization requirement.
            required_vehicle_type: Optional specific rescue vehicle type requirement.

        Raises:
            ValueError: If incident_id is empty or severity is outside 1..5.
            TypeError: If position, incident_type, status, or optional requirements have an invalid type.
        """
        if not incident_id or not incident_id.strip():
            raise ValueError("Incident ID cannot be empty")

        if not isinstance(severity, int) or isinstance(severity, bool) or severity < 1 or severity > 5:
            raise ValueError("Severity must be between 1 and 5(inclusive).")

        if not isinstance(position, Position):
            raise TypeError("Incident position must be an instance of Position.")

        if not isinstance(incident_type, IncidentType):
            raise TypeError("Incident type must be a valid IncidentType enum value.")

        if not isinstance(status, IncidentStatus):
            raise TypeError("Incident status must be a valid IncidentStatus enum value.")

        if required_specialization is not None and not isinstance(required_specialization, ResponderSpecialization):
            raise TypeError("Required specialization must be a ResponderSpecialization enum value or None.")

        if required_vehicle_type is not None and not isinstance(required_vehicle_type, VehicleType):
            raise TypeError("Required vehicle type must be a VehicleType enum value or None.")

        self._id: str = incident_id.strip()
        self._type: IncidentType = incident_type
        self._severity: int = severity
        self._position: Position = position
        self._status: IncidentStatus = status
        self._required_specialization: Optional[ResponderSpecialization] = required_specialization
        self._required_vehicle_type: Optional[VehicleType] = required_vehicle_type
        self._assigned_responder_id: str = ""
        self._assigned_vehicle_id: str = ""
        self._failure_reason: Optional[str] = None
        self._manager: Optional[Any] = None

    def set_manager(self, manager: Any) -> None:
        """Bind managing RescueManager authority for lifecycle synchronization."""
        self._manager = manager

    def _set_status_direct(self, new_status: IncidentStatus) -> None:
        """Internal mutator used by RescueManager to update status without recursive delegation."""
        self._status = new_status

    # Property accessors
    @property
    def id(self) -> str:
        """Return the unique incident identifier."""
        return self._id

    @property
    def type(self) -> IncidentType:
        """Return the incident type enum."""
        return self._type

    @property
    def severity(self) -> int:
        """Return the integer severity rating (1 to 5)."""
        return self._severity

    @property
    def position(self) -> Position:
        """Return the grid position of the incident."""
        return self._position

    @property
    def status(self) -> IncidentStatus:
        """Return the current lifecycle status."""
        return self._status

    @property
    def assigned_responder_id(self) -> str:
        """Return assigned responder ID or empty string."""
        return self._assigned_responder_id

    @property
    def assigned_vehicle_id(self) -> str:
        """Return assigned vehicle ID or empty string."""
        return self._assigned_vehicle_id

    @property
    def failure_reason(self) -> Optional[str]:
        """Return the reason for mission failure, if applicable."""
        return self._failure_reason

    def get_failure_reason(self) -> Optional[str]:
        """Return the reason for mission failure, if applicable."""
        return self._failure_reason

    def set_failure_reason(self, reason: Optional[str]) -> None:
        """Record the reason for mission failure."""
        self._failure_reason = reason

    @property
    def required_specialization(self) -> Optional[ResponderSpecialization]:
        """Return explicitly required responder specialization, if configured."""
        return self._required_specialization

    @property
    def required_vehicle_type(self) -> Optional[VehicleType]:
        """Return explicitly required vehicle type, if configured."""
        return self._required_vehicle_type

    # Getter methods (PEP 8 and C++ naming)
    def get_id(self) -> str:
        """Return the unique incident identifier."""
        return self._id

    def get_type(self) -> IncidentType:
        """Return the incident type."""
        return self._type

    def get_severity(self) -> int:
        """Return the severity rating."""
        return self._severity

    def get_position(self) -> Position:
        """Return the incident grid position."""
        return self._position

    def get_status(self) -> IncidentStatus:
        """Return the incident lifecycle status."""
        return self._status

    def set_status(self, new_status: IncidentStatus) -> None:
        """Update incident lifecycle status.

        If this incident is registered with a RescueManager, status transitions
        are routed through the manager to enforce resource allocation and release invariants.
        For standalone incidents, standard lifecycle invariants are validated directly.
        """
        if not isinstance(new_status, IncidentStatus):
            raise TypeError("Status must be an instance of IncidentStatus.")

        if self._manager is not None:
            # Delegate to the managing RescueManager to ensure resource consistency & release
            self._manager.update_incident_status(self._id, new_status)
            return

        # Standalone incident transition validation
        current = self._status
        if current in (IncidentStatus.RESOLVED, IncidentStatus.Resolved):
            raise InvalidStatusTransitionError(
                f"Resolved incident <{self._id}> cannot transition to another status."
            )
        if current in (IncidentStatus.FAILED, IncidentStatus.Failed):
            raise InvalidStatusTransitionError(
                f"Failed incident <{self._id}> cannot transition to another status."
            )

        if current in (IncidentStatus.REPORTED, IncidentStatus.Reported):
            if new_status in (IncidentStatus.REPORTED, IncidentStatus.Reported):
                raise InvalidStatusTransitionError(
                    f"Incident <{self._id}> is already in Reported status."
                )

        if current in (IncidentStatus.IN_PROGRESS, IncidentStatus.InProgress):
            if new_status in (IncidentStatus.IN_PROGRESS, IncidentStatus.InProgress):
                raise InvalidStatusTransitionError(
                    f"Incident <{self._id}> is already in progress"
                )
            if new_status in (IncidentStatus.REPORTED, IncidentStatus.Reported):
                raise InvalidStatusTransitionError(
                    f"Active incident <{self._id}> is already in progress and cannot be changed to reported!"
                )

        self._status = new_status

    def get_type_string(self) -> str:
        """Return human-readable string for the incident type."""
        if self._type in (IncidentType.FIRE, IncidentType.Fire):
            return "Fire"
        if self._type in (IncidentType.FLOOD, IncidentType.Flood):
            return "Flood"
        if self._type in (IncidentType.STRUCTURAL_COLLAPSE, IncidentType.StructuralCollapse):
            return "StructuralCollapse"
        if self._type in (IncidentType.MEDICAL, getattr(IncidentType, "Medical", None)):
            return "Medical"
        return "Unknown"

    def get_required_specialization(self) -> Optional[ResponderSpecialization]:
        """Return explicitly required responder specialization, if configured."""
        return self._required_specialization

    def get_required_vehicle_type(self) -> Optional[VehicleType]:
        """Return explicitly required vehicle type, if configured."""
        return self._required_vehicle_type

    def get_status_string(self) -> str:
        """Return human-readable string for the incident status."""
        if self._status in (IncidentStatus.REPORTED, IncidentStatus.Reported):
            return "Reported"
        if self._status in (IncidentStatus.IN_PROGRESS, IncidentStatus.InProgress):
            return "InProgress"
        if self._status in (IncidentStatus.RESOLVED, IncidentStatus.Resolved):
            return "Resolved"
        if self._status in (IncidentStatus.FAILED, IncidentStatus.Failed):
            return "Failed"
        return "Unknown"

    def has_assigned_resources(self) -> bool:
        """Return True if both a responder and vehicle are actively assigned."""
        return bool(self._assigned_responder_id and self._assigned_vehicle_id)

    def get_assigned_responder_id(self) -> str:
        """Return the identifier of the assigned responder."""
        return self._assigned_responder_id

    def get_assigned_vehicle_id(self) -> str:
        """Return the identifier of the assigned rescue vehicle."""
        return self._assigned_vehicle_id

    def assign_resources(self, responder_id: str, vehicle_id: str) -> None:
        """Bind responder and vehicle identifiers to this incident."""
        self._assigned_responder_id = responder_id
        self._assigned_vehicle_id = vehicle_id

    def release_resources(self) -> None:
        """Clear assigned responder and vehicle bindings."""
        self._assigned_responder_id = ""
        self._assigned_vehicle_id = ""

    def to_string(self) -> str:
        """Return formatted string detailing incident state."""
        result = (
            f"Incident [ID: {self._id}, "
            f"Type: {self.get_type_string()}, "
            f"Severity: {self._severity}/5, "
            f"Location: {self._position.to_string()}, "
            f"Status: {self.get_status_string()}"
        )
        if self.has_assigned_resources():
            result += (
                f", Assigned: (Responder: {self._assigned_responder_id}, "
                f"Vehicle: {self._assigned_vehicle_id})"
            )
        result += "]"
        return result

    def display(self) -> None:
        """Print incident details to standard output."""
        print(self.to_string())

    def __str__(self) -> str:
        return self.to_string()

    def __repr__(self) -> str:
        return (
            f"Incident(id='{self._id}', type={self._type!r}, "
            f"severity={self._severity}, position={self._position!r}, "
            f"status={self._status!r})"
        )

    # C++ compatibility aliases
    getId = get_id
    getType = get_type
    getSeverity = get_severity
    getPosition = get_position
    getStatus = get_status
    setStatus = set_status
    getTypeString = get_type_string
    getStatusString = get_status_string
    hasAssignedResources = has_assigned_resources
    getAssignedResponderId = get_assigned_responder_id
    getAssignedVehicleId = get_assigned_vehicle_id
    getRequiredSpecialization = get_required_specialization
    getRequiredVehicleType = get_required_vehicle_type
    assignResources = assign_resources
    releaseResources = release_resources
    toString = to_string
