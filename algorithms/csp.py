"""
Multi-Agent Resource Allocation using Constraint Satisfaction Problems (CSP) for RescueGrid (Phase 8).

Implements a formal backtracking CSP solver with:
- Minimum Remaining Values (MRV) variable selection heuristic
- Degree heuristic for MRV tie-breaking (resource contention graph)
- Least Constraining Value (LCV) domain value ordering
- Forward checking with domain wipeout detection
- Complete vs. partial allocation distinguishing
- Atomic, side-effect-free execution
"""

import time
from typing import Any, Callable, Dict, List, Optional, Sequence, Set, Tuple, Union
from models.position import Position
from models.incident import Incident, IncidentType, IncidentStatus
from models.responder import Responder, ResponderSpecialization
from models.rescue_vehicle import RescueVehicle, VehicleType
from algorithms.csp_result import CSPResult


# =============================================================================
# Standard Domain Compatibility Mapping Tables
# =============================================================================

DEFAULT_RESPONDER_COMPATIBILITY: Dict[str, Tuple[ResponderSpecialization, ...]] = {
    IncidentType.FIRE.value: (ResponderSpecialization.FIREFIGHTER,),
    IncidentType.STRUCTURAL_COLLAPSE.value: (ResponderSpecialization.RESCUE_SPECIALIST,),
    IncidentType.MEDICAL.value: (ResponderSpecialization.PARAMEDIC,),
    IncidentType.FLOOD.value: (
        ResponderSpecialization.RESCUE_SPECIALIST,
        ResponderSpecialization.FIREFIGHTER,
    ),
}

DEFAULT_VEHICLE_COMPATIBILITY: Dict[str, Tuple[VehicleType, ...]] = {
    IncidentType.FIRE.value: (VehicleType.FIRE_ENGINE,),
    IncidentType.STRUCTURAL_COLLAPSE.value: (VehicleType.RESCUE_VAN,),
    IncidentType.MEDICAL.value: (VehicleType.AMBULANCE,),
    IncidentType.FLOOD.value: (
        VehicleType.RESCUE_VAN,
        VehicleType.FIRE_ENGINE,
    ),
}


def _manhattan_distance(p1: Position, p2: Position) -> int:
    """Calculate L1 Manhattan distance between two positions."""
    return abs(p1.x - p2.x) + abs(p1.y - p2.y)


class CSPSolver:
    """Constraint Satisfaction Problem solver for multi-agent rescue resource allocation.

    Formulates resource allocation as a CSP:
    - Variables X: Active emergency incidents requiring resource assignment.
    - Domains D: Feasible (Responder, RescueVehicle) candidate pairs satisfying
      availability, responder specialization, and vehicle compatibility.
    - Constraints C:
      1. Responder availability (available and not assigned elsewhere).
      2. Vehicle availability (available and not assigned elsewhere).
      3. Responder specialization compatibility with incident type.
      4. Vehicle type compatibility with incident type.
      5. Resource uniqueness (all-different: no responder or vehicle double-assigned).
      6. Incident eligibility (resolved or already-serviced incidents excluded).
      7. Atomic assignment (both responder and vehicle or neither).
    """

    def __init__(
        self,
        responder_compatibility: Optional[Dict[str, Sequence[ResponderSpecialization]]] = None,
        vehicle_compatibility: Optional[Dict[str, Sequence[VehicleType]]] = None,
        enable_mrv: bool = True,
        enable_degree: bool = True,
        enable_lcv: bool = True,
        enable_forward_checking: bool = True,
    ) -> None:
        """Initialize CSP solver configuration.

        Args:
            responder_compatibility: Custom incident-type-to-responder-specialization mapping.
            vehicle_compatibility: Custom incident-type-to-vehicle-type mapping.
            enable_mrv: Enable Minimum Remaining Values variable selection.
            enable_degree: Enable Degree Heuristic for MRV tie-breaking.
            enable_lcv: Enable Least Constraining Value candidate ordering.
            enable_forward_checking: Enable Forward Checking domain pruning.
        """
        self._resp_compat = responder_compatibility or DEFAULT_RESPONDER_COMPATIBILITY
        self._veh_compat = vehicle_compatibility or DEFAULT_VEHICLE_COMPATIBILITY
        self._enable_mrv = bool(enable_mrv)
        self._enable_degree = bool(enable_degree)
        self._enable_lcv = bool(enable_lcv)
        self._enable_forward_checking = bool(enable_forward_checking)

        # Search execution metrics
        self._nodes_explored: int = 0
        self._backtracks: int = 0
        self._constraint_checks: int = 0
        self._best_partial_assignment: Dict[str, Tuple[Responder, RescueVehicle]] = {}

    # =========================================================================
    # Compatibility and Domain Construction
    # =========================================================================

    def get_compatible_specializations(
        self, incident: Incident
    ) -> Tuple[ResponderSpecialization, ...]:
        """Return compatible responder specializations for an incident."""
        if incident.required_specialization is not None:
            return (incident.required_specialization,)
        type_key = incident.type.value if hasattr(incident.type, "value") else str(incident.type)
        return tuple(self._resp_compat.get(type_key, ()))

    def get_compatible_vehicle_types(
        self, incident: Incident
    ) -> Tuple[VehicleType, ...]:
        """Return compatible vehicle types for an incident."""
        if incident.required_vehicle_type is not None:
            return (incident.required_vehicle_type,)
        type_key = incident.type.value if hasattr(incident.type, "value") else str(incident.type)
        return tuple(self._veh_compat.get(type_key, ()))

    def build_initial_domains(
        self,
        incidents: Sequence[Incident],
        responders: Sequence[Responder],
        vehicles: Sequence[RescueVehicle],
    ) -> Dict[str, List[Tuple[Responder, RescueVehicle]]]:
        """Construct candidate resource pair domains for all eligible incidents.

        Only combinations satisfying availability and compatibility enter the domain.
        """
        # Filter available resources
        avail_responders = [r for r in responders if r.is_available()]
        avail_vehicles = [v for v in vehicles if v.is_available()]

        domains: Dict[str, List[Tuple[Responder, RescueVehicle]]] = {}

        for inc in incidents:
            compat_specs = set(self.get_compatible_specializations(inc))
            compat_vehs = set(self.get_compatible_vehicle_types(inc))

            eligible_resps = [
                r for r in avail_responders if r.specialization in compat_specs
            ]
            eligible_vehs = [
                v for v in avail_vehicles if v.type in compat_vehs
            ]

            pairs: List[Tuple[Responder, RescueVehicle]] = []
            for r in eligible_resps:
                for v in eligible_vehs:
                    pairs.append((r, v))

            # Deterministic initial ordering by IDs
            pairs.sort(key=lambda pair: (pair[0].id, pair[1].id))
            domains[inc.id] = pairs

        return domains

    # =========================================================================
    # Heuristics: MRV, Degree, and LCV
    # =========================================================================

    def _select_variable(
        self,
        unassigned_incidents: List[Incident],
        domains: Dict[str, List[Tuple[Responder, RescueVehicle]]],
    ) -> Incident:
        """Select the next unassigned variable using MRV and Degree Heuristic.

        1. Primary: Minimum Remaining Values (smallest domain size).
        2. Secondary: Degree Heuristic (most resource contention edges with other unassigned).
        3. Tertiary: Deterministic alphabetical ordering by incident ID.
        """
        if not self._enable_mrv:
            # Deterministic default order by ID if MRV disabled
            return min(unassigned_incidents, key=lambda inc: inc.id)

        # 1. Compute domain sizes
        min_domain_size = min(len(domains[inc.id]) for inc in unassigned_incidents)
        mrv_candidates = [
            inc for inc in unassigned_incidents if len(domains[inc.id]) == min_domain_size
        ]

        if len(mrv_candidates) == 1 or not self._enable_degree:
            return min(mrv_candidates, key=lambda inc: inc.id)

        # 2. Degree Heuristic: count conflicts with other unassigned variables
        def calculate_degree(target_inc: Incident) -> int:
            target_resps = {r.id for (r, v) in domains[target_inc.id]}
            target_vehs = {v.id for (r, v) in domains[target_inc.id]}
            degree = 0
            for other_inc in unassigned_incidents:
                if other_inc.id == target_inc.id:
                    continue
                other_resps = {r.id for (r, v) in domains[other_inc.id]}
                other_vehs = {v.id for (r, v) in domains[other_inc.id]}
                if bool(target_resps & other_resps) or bool(target_vehs & other_vehs):
                    degree += 1
            return degree

        # Select candidate with highest degree, breaking ties deterministically by ID
        return min(mrv_candidates, key=lambda inc: (-calculate_degree(inc), inc.id))

    def _order_domain_values(
        self,
        incident: Incident,
        candidate_values: List[Tuple[Responder, RescueVehicle]],
        unassigned_incidents: List[Incident],
        domains: Dict[str, List[Tuple[Responder, RescueVehicle]]],
    ) -> List[Tuple[Responder, RescueVehicle]]:
        """Order candidate values using Least Constraining Value (LCV) heuristic.

        Prefer candidate pair that rules out the fewest choices for other unassigned incidents.
        Tie-breaking:
        1. Fewest constrained options for others.
        2. Lowest total Manhattan distance to incident location.
        3. Deterministic alphabetical IDs.
        """
        if not self._enable_lcv or len(unassigned_incidents) <= 1:
            # Sort by distance then ID
            return sorted(
                candidate_values,
                key=lambda pair: (
                    _manhattan_distance(pair[0].position, incident.position)
                    + _manhattan_distance(pair[1].position, incident.position),
                    pair[0].id,
                    pair[1].id,
                ),
            )

        other_incidents = [inc for inc in unassigned_incidents if inc.id != incident.id]

        def lcv_cost(pair: Tuple[Responder, RescueVehicle]) -> Tuple[int, int, str, str]:
            resp, veh = pair
            constrained_choices = 0
            for other_inc in other_incidents:
                for other_r, other_v in domains[other_inc.id]:
                    if other_r.id == resp.id or other_v.id == veh.id:
                        constrained_choices += 1

            dist = _manhattan_distance(resp.position, incident.position) + _manhattan_distance(
                veh.position, incident.position
            )
            return (constrained_choices, dist, resp.id, veh.id)

        return sorted(candidate_values, key=lcv_cost)

    # =========================================================================
    # Constraint Consistency & Forward Checking
    # =========================================================================

    def _is_consistent(
        self,
        candidate: Tuple[Responder, RescueVehicle],
        assignment: Dict[str, Tuple[Responder, RescueVehicle]],
    ) -> bool:
        """Check hard constraints against current partial assignment."""
        self._constraint_checks += 1
        resp, veh = candidate

        # Resource uniqueness: verify neither resource is already allocated
        for assigned_resp, assigned_veh in assignment.values():
            if assigned_resp.id == resp.id or assigned_veh.id == veh.id:
                return False

        return True

    def _forward_check(
        self,
        assigned_inc: Incident,
        assigned_pair: Tuple[Responder, RescueVehicle],
        unassigned_incidents: List[Incident],
        domains: Dict[str, List[Tuple[Responder, RescueVehicle]]],
    ) -> Tuple[bool, Dict[str, List[Tuple[Responder, RescueVehicle]]]]:
        """Perform forward checking pruning.

        Removes conflicting resources from remaining unassigned variables.
        Detects empty domains immediately (domain wipeout).
        """
        if not self._enable_forward_checking:
            return True, {k: list(v) for k, v in domains.items()}

        resp, veh = assigned_pair
        new_domains: Dict[str, List[Tuple[Responder, RescueVehicle]]] = {}

        for inc in unassigned_incidents:
            if inc.id == assigned_inc.id:
                continue

            pruned = [
                (r, v)
                for (r, v) in domains[inc.id]
                if r.id != resp.id and v.id != veh.id
            ]

            if not pruned:
                # Domain wipeout detected
                return False, {}

            new_domains[inc.id] = pruned

        return True, new_domains

    # =========================================================================
    # Backtracking Search
    # =========================================================================

    def _backtrack(
        self,
        assignment: Dict[str, Tuple[Responder, RescueVehicle]],
        domains: Dict[str, List[Tuple[Responder, RescueVehicle]]],
        unassigned_incidents: List[Incident],
    ) -> bool:
        """Recursive backtracking search engine."""
        # Update best partial assignment snapshot
        if len(assignment) > len(self._best_partial_assignment):
            self._best_partial_assignment = dict(assignment)

        # Base case: All incidents successfully assigned
        if not unassigned_incidents:
            return True

        # Variable selection: MRV + Degree + ID
        var = self._select_variable(unassigned_incidents, domains)

        # Value ordering: LCV + Distance + ID
        ordered_values = self._order_domain_values(
            var, domains[var.id], unassigned_incidents, domains
        )

        for candidate_pair in ordered_values:
            self._nodes_explored += 1

            # Constraint check
            if not self._is_consistent(candidate_pair, assignment):
                continue

            # Forward check
            is_viable, pruned_domains = self._forward_check(
                var, candidate_pair, unassigned_incidents, domains
            )
            if not is_viable:
                self._backtracks += 1
                continue

            # Provisionally assign
            assignment[var.id] = candidate_pair
            next_unassigned = [inc for inc in unassigned_incidents if inc.id != var.id]

            # Recurse
            success = self._backtrack(assignment, pruned_domains, next_unassigned)
            if success:
                return True

            # Backtrack
            del assignment[var.id]
            self._backtracks += 1

        return False

    # =========================================================================
    # Public Solver Interface
    # =========================================================================

    def solve(
        self,
        incidents: Sequence[Incident],
        responders: Sequence[Responder],
        vehicles: Sequence[RescueVehicle],
        allow_partial: bool = False,
    ) -> CSPResult:
        """Execute CSP resource allocation.

        Args:
            incidents: Collection of Incident objects requiring resource assignment.
            responders: Collection of fleet Responder objects.
            vehicles: Collection of fleet RescueVehicle objects.
            allow_partial: If True, return maximum partial allocation when complete
                allocation is impossible. Default False.

        Returns:
            CSPResult containing status ('COMPLETE', 'PARTIAL', 'FAILED'),
            assignments dictionary, unassigned incidents list, and search metrics.

        Raises:
            TypeError: If arguments are not collections of appropriate domain objects.
        """
        start_time = time.perf_counter()

        # Input validation
        if not isinstance(incidents, (list, tuple, set)):
            raise TypeError("incidents must be a sequence of Incident objects.")
        if not isinstance(responders, (list, tuple, set)):
            raise TypeError("responders must be a sequence of Responder objects.")
        if not isinstance(vehicles, (list, tuple, set)):
            raise TypeError("vehicles must be a sequence of RescueVehicle objects.")

        for inc in incidents:
            if not isinstance(inc, Incident):
                raise TypeError(f"Expected Incident instance, received {type(inc)}.")
        for resp in responders:
            if not isinstance(resp, Responder):
                raise TypeError(f"Expected Responder instance, received {type(resp)}.")
        for veh in vehicles:
            if not isinstance(veh, RescueVehicle):
                raise TypeError(f"Expected RescueVehicle instance, received {type(veh)}.")

        # Reset search metrics
        self._nodes_explored = 0
        self._backtracks = 0
        self._constraint_checks = 0
        self._best_partial_assignment = {}

        algorithm_name = "Backtracking CSP (MRV + Degree + LCV + Forward Checking)"

        # Filter eligible incidents: exclude Resolved or already assigned incidents
        eligible_incidents: List[Incident] = [
            inc
            for inc in incidents
            if inc.status not in (IncidentStatus.RESOLVED, IncidentStatus.Resolved)
            and not inc.has_assigned_resources()
        ]

        total_target_count = len(eligible_incidents)

        # Trivial case: Zero eligible incidents
        if total_target_count == 0:
            elapsed_ms = (time.perf_counter() - start_time) * 1000.0
            return CSPResult(
                algorithm_name=algorithm_name,
                status="COMPLETE",
                is_complete=True,
                assignments={},
                unassigned_incident_ids=[],
                target_incident_count=0,
                nodes_explored=0,
                backtracks=0,
                constraint_checks=0,
                execution_time_ms=elapsed_ms,
            )

        # Build initial candidate domains
        domains = self.build_initial_domains(
            eligible_incidents, responders, vehicles
        )

        # Quick check: If any eligible incident has an empty initial domain, complete assignment is impossible
        has_empty_domain = any(len(domains[inc.id]) == 0 for inc in eligible_incidents)

        assignment: Dict[str, Tuple[Responder, RescueVehicle]] = {}
        success = False

        if not has_empty_domain:
            success = self._backtrack(assignment, domains, list(eligible_incidents))

        elapsed_ms = (time.perf_counter() - start_time) * 1000.0

        if success:
            return CSPResult(
                algorithm_name=algorithm_name,
                status="COMPLETE",
                is_complete=True,
                assignments=assignment,
                unassigned_incident_ids=[],
                target_incident_count=total_target_count,
                nodes_explored=self._nodes_explored,
                backtracks=self._backtracks,
                constraint_checks=self._constraint_checks,
                execution_time_ms=elapsed_ms,
            )

        # Complete allocation failed
        if allow_partial:
            partial_assignments = self._find_best_partial_assignment(eligible_incidents, domains)
            if partial_assignments:
                assigned_ids = set(partial_assignments.keys())
                unassigned_ids = [inc.id for inc in eligible_incidents if inc.id not in assigned_ids]
                return CSPResult(
                    algorithm_name=algorithm_name,
                    status="PARTIAL",
                    is_complete=False,
                    assignments=partial_assignments,
                    unassigned_incident_ids=unassigned_ids,
                    target_incident_count=total_target_count,
                    nodes_explored=self._nodes_explored,
                    backtracks=self._backtracks,
                    constraint_checks=self._constraint_checks,
                    execution_time_ms=elapsed_ms,
                )

        # Unsuccessful / Infeasible complete allocation
        return CSPResult(
            algorithm_name=algorithm_name,
            status="FAILED",
            is_complete=False,
            assignments={},
            unassigned_incident_ids=[inc.id for inc in eligible_incidents],
            target_incident_count=total_target_count,
            nodes_explored=self._nodes_explored,
            backtracks=self._backtracks,
            constraint_checks=self._constraint_checks,
            execution_time_ms=elapsed_ms,
        )

    def _find_best_partial_assignment(
        self,
        incidents: Sequence[Incident],
        domains: Dict[str, List[Tuple[Responder, RescueVehicle]]],
    ) -> Dict[str, Tuple[Responder, RescueVehicle]]:
        """Construct best feasible non-conflicting partial allocation when complete is impossible."""
        partial_assignments: Dict[str, Tuple[Responder, RescueVehicle]] = {}
        used_responders: Set[str] = set()
        used_vehicles: Set[str] = set()

        # Prioritize by smallest domain (MRV) then highest severity, then ID
        sorted_incidents = sorted(
            incidents,
            key=lambda inc: (len(domains.get(inc.id, [])), -inc.severity, inc.id),
        )

        for inc in sorted_incidents:
            for resp, veh in domains.get(inc.id, []):
                self._constraint_checks += 1
                if resp.id not in used_responders and veh.id not in used_vehicles:
                    partial_assignments[inc.id] = (resp, veh)
                    used_responders.add(resp.id)
                    used_vehicles.add(veh.id)
                    break

        return partial_assignments


def allocate_resources_csp(
    incidents: Sequence[Incident],
    responders: Sequence[Responder],
    vehicles: Sequence[RescueVehicle],
    allow_partial: bool = False,
    solver: Optional[CSPSolver] = None,
) -> CSPResult:
    """Convenience function to execute CSP resource allocation."""
    active_solver = solver if solver is not None else CSPSolver()
    return active_solver.solve(
        incidents, responders, vehicles, allow_partial=allow_partial
    )
