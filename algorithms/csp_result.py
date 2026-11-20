"""
Result model representing the outcome of a Multi-Agent Constraint Satisfaction (CSP)
resource allocation search in RescueGrid (Phase 8).
"""

from typing import Any, Dict, List, Optional, Tuple
from models.responder import Responder
from models.rescue_vehicle import RescueVehicle


class CSPResult:
    """Encapsulates the outcome, assignments, and search metrics of a CSP allocation.

    Distinguishes clearly between:
    - COMPLETE: All requested incidents received feasible, non-conflicting resources.
    - PARTIAL: A subset of incidents received feasible resources (when partial mode permitted).
    - FAILED: No feasible complete allocation could be constructed.
    """

    def __init__(
        self,
        algorithm_name: str,
        status: str,
        is_complete: bool,
        assignments: Dict[str, Tuple[Responder, RescueVehicle]],
        unassigned_incident_ids: List[str],
        target_incident_count: int,
        nodes_explored: int,
        backtracks: int,
        constraint_checks: int,
        execution_time_ms: float,
    ) -> None:
        """Initialize a CSP allocation result.

        Args:
            algorithm_name: Descriptive name of the CSP search algorithm.
            status: Allocation status outcome: 'COMPLETE', 'PARTIAL', or 'FAILED'.
            is_complete: True if every target incident was successfully allocated.
            assignments: Mapping from incident ID to (Responder, RescueVehicle) tuple.
            unassigned_incident_ids: List of incident IDs left without assigned resources.
            target_incident_count: Total count of eligible incidents considered.
            nodes_explored: Number of assignment attempts (search tree nodes).
            backtracks: Number of recursive backtrack events triggered.
            constraint_checks: Number of hard constraint checks evaluated.
            execution_time_ms: Total search execution time in milliseconds.
        """
        self._algorithm_name: str = algorithm_name
        self._status: str = status
        self._is_complete: bool = bool(is_complete)
        self._assignments: Dict[str, Tuple[Responder, RescueVehicle]] = dict(assignments)
        self._unassigned_incident_ids: List[str] = list(unassigned_incident_ids)
        self._target_incident_count: int = target_incident_count
        self._nodes_explored: int = nodes_explored
        self._backtracks: int = backtracks
        self._constraint_checks: int = constraint_checks
        self._execution_time_ms: float = execution_time_ms

    @property
    def algorithm_name(self) -> str:
        """Return the name of the CSP solver."""
        return self._algorithm_name

    @property
    def status(self) -> str:
        """Return status string ('COMPLETE', 'PARTIAL', or 'FAILED')."""
        return self._status

    @property
    def is_complete(self) -> bool:
        """Return True if all target incidents were allocated."""
        return self._is_complete

    @property
    def assignments(self) -> Dict[str, Tuple[Responder, RescueVehicle]]:
        """Return a copy of incident-to-resource assignments."""
        return dict(self._assignments)

    @property
    def unassigned_incident_ids(self) -> List[str]:
        """Return a copy of unassigned incident identifiers."""
        return list(self._unassigned_incident_ids)

    @property
    def target_incident_count(self) -> int:
        """Return total number of target incidents."""
        return self._target_incident_count

    @property
    def assigned_count(self) -> int:
        """Return number of successfully assigned incidents."""
        return len(self._assignments)

    @property
    def unassigned_count(self) -> int:
        """Return number of unassigned incidents."""
        return len(self._unassigned_incident_ids)

    @property
    def nodes_explored(self) -> int:
        """Return number of search nodes evaluated."""
        return self._nodes_explored

    @property
    def backtracks(self) -> int:
        """Return total number of backtrack operations."""
        return self._backtracks

    @property
    def constraint_checks(self) -> int:
        """Return total number of constraint consistency validations."""
        return self._constraint_checks

    @property
    def execution_time_ms(self) -> float:
        """Return search execution wall time in milliseconds."""
        return self._execution_time_ms

    def has_assignment(self, incident_id: str) -> bool:
        """Check if a specific incident has an assigned resource pair."""
        return incident_id in self._assignments

    def get_assignment(self, incident_id: str) -> Optional[Tuple[Responder, RescueVehicle]]:
        """Return (Responder, RescueVehicle) assigned to incident_id, or None."""
        return self._assignments.get(incident_id)

    def get_assigned_responder(self, incident_id: str) -> Optional[Responder]:
        """Return Responder assigned to incident_id, or None."""
        pair = self._assignments.get(incident_id)
        return pair[0] if pair is not None else None

    def get_assigned_vehicle(self, incident_id: str) -> Optional[RescueVehicle]:
        """Return RescueVehicle assigned to incident_id, or None."""
        pair = self._assignments.get(incident_id)
        return pair[1] if pair is not None else None

    def to_dict(self) -> Dict[str, Any]:
        """Convert allocation outcome and metrics into a standard dictionary."""
        return {
            "algorithm_name": self._algorithm_name,
            "status": self._status,
            "is_complete": self._is_complete,
            "target_incidents": self._target_incident_count,
            "assigned_count": len(self._assignments),
            "unassigned_count": len(self._unassigned_incident_ids),
            "assignments": {
                inc_id: {
                    "responder_id": resp.get_id(),
                    "responder_name": resp.get_name(),
                    "specialization": resp.get_specialization_string(),
                    "vehicle_id": veh.get_id(),
                    "vehicle_type": veh.get_type_string(),
                }
                for inc_id, (resp, veh) in self._assignments.items()
            },
            "unassigned_incident_ids": list(self._unassigned_incident_ids),
            "nodes_explored": self._nodes_explored,
            "backtracks": self._backtracks,
            "constraint_checks": self._constraint_checks,
            "execution_time_ms": self._execution_time_ms,
        }

    def to_string(self) -> str:
        """Format a human-readable summary of the CSP allocation."""
        lines = [
            f"CSP Allocation Result [{self._algorithm_name}]",
            f"  Status          : {self._status}",
            f"  Complete        : {'YES' if self._is_complete else 'NO'}",
            f"  Allocated       : {len(self._assignments)} / {self._target_incident_count} incidents",
            f"  Nodes Explored  : {self._nodes_explored}",
            f"  Backtracks      : {self._backtracks}",
            f"  Constraint Check: {self._constraint_checks}",
            f"  Execution Time  : {self._execution_time_ms:.4f} ms",
        ]
        if self._assignments:
            lines.append("  Assignments:")
            for inc_id, (resp, veh) in sorted(self._assignments.items()):
                lines.append(
                    f"    - Incident {inc_id} -> "
                    f"Responder: {resp.get_id()} ({resp.get_name()}, {resp.get_specialization_string()}) | "
                    f"Vehicle: {veh.get_id()} ({veh.get_type_string()})"
                )
        if self._unassigned_incident_ids:
            lines.append(f"  Unassigned Incidents: {', '.join(sorted(self._unassigned_incident_ids))}")
        return "\n".join(lines)

    def display(self) -> None:
        """Print formatted allocation summary to stdout."""
        print(self.to_string())

    def __str__(self) -> str:
        return self.to_string()

    def __repr__(self) -> str:
        return (
            f"CSPResult(status='{self._status}', is_complete={self._is_complete}, "
            f"assigned={len(self._assignments)}/{self._target_incident_count}, "
            f"nodes={self._nodes_explored}, backtracks={self._backtracks}, "
            f"time_ms={self._execution_time_ms:.3f})"
        )
