"""
Central disaster response coordination manager for RescueGrid.
"""

from typing import Any, List, Optional
from models.incident import Incident, IncidentStatus
from models.responder import Responder
from models.rescue_vehicle import RescueVehicle
from models.exceptions import (
    RescueGridError,
    DuplicateEntityError,
    EntityNotFoundError,
    ResourceUnavailableError,
    InvalidStatusTransitionError,
    LogicError,
)


class RescueManager:
    """Coordinates emergency incidents, responders, and rescue vehicle fleets.

    The RescueManager serves as the central control entity in RescueGrid.
    It encapsulates the storage and lifecycle of incidents, responders, and
    vehicles, and enforces deterministic resource dispatching and lifecycle
    status synchronization.
    """

    def __init__(self) -> None:
        """Initialize empty collections for incidents, responders, and vehicles."""
        self._incidents: List[Incident] = []
        self._responders: List[Responder] = []
        self._vehicles: List[RescueVehicle] = []

    # =========================================================================
    # Registration Methods
    # =========================================================================

    def register_incident(self, incident: Incident) -> None:
        """Register an incident into the management system.

        Args:
            incident: Incident object to register.

        Raises:
            TypeError: If incident is not an Incident instance.
            DuplicateEntityError (ValueError): If an incident with the same ID exists.
        """
        if not isinstance(incident, Incident):
            raise TypeError("Expected an instance of Incident.")
        if self.has_incident(incident.get_id()):
            raise DuplicateEntityError(
                f"Incident with ID <{incident.get_id()}> already exists."
            )
        incident.set_manager(self)
        self._incidents.append(incident)

    def register_responder(self, responder: Responder) -> None:
        """Register a responder into the management system.

        Args:
            responder: Responder object to register.

        Raises:
            TypeError: If responder is not a Responder instance.
            DuplicateEntityError (ValueError): If a responder with the same ID exists.
        """
        if not isinstance(responder, Responder):
            raise TypeError("Expected an instance of Responder.")
        if self.has_responder(responder.get_id()):
            raise DuplicateEntityError(
                f"Responder with ID <{responder.get_id()}> already exists."
            )
        self._responders.append(responder)

    def register_vehicle(self, vehicle: RescueVehicle) -> None:
        """Register a rescue vehicle into the management system.

        Args:
            vehicle: RescueVehicle object to register.

        Raises:
            TypeError: If vehicle is not a RescueVehicle instance.
            DuplicateEntityError (ValueError): If a vehicle with the same ID exists.
        """
        if not isinstance(vehicle, RescueVehicle):
            raise TypeError("Expected an instance of RescueVehicle.")
        if self.has_vehicle(vehicle.get_id()):
            raise DuplicateEntityError(
                f"Vehicle with ID <{vehicle.get_id()}> already exists."
            )
        self._vehicles.append(vehicle)

    # =========================================================================
    # Existence Check Methods
    # =========================================================================

    def has_incident(self, incident_id: str) -> bool:
        """Check whether an incident with the given ID is registered."""
        return self.find_incident(incident_id) is not None

    def has_responder(self, responder_id: str) -> bool:
        """Check whether a responder with the given ID is registered."""
        return self.find_responder(responder_id) is not None

    def has_vehicle(self, vehicle_id: str) -> bool:
        """Check whether a rescue vehicle with the given ID is registered."""
        return self.find_vehicle(vehicle_id) is not None

    # =========================================================================
    # Search & Retrieval Methods
    # =========================================================================

    def find_incident(self, incident_id: str) -> Optional[Incident]:
        """Search for an incident by ID. Returns None if not found."""
        for inc in self._incidents:
            if inc.get_id() == incident_id:
                return inc
        return None

    def find_responder(self, responder_id: str) -> Optional[Responder]:
        """Search for a responder by ID. Returns None if not found."""
        for resp in self._responders:
            if resp.get_id() == responder_id:
                return resp
        return None

    def find_vehicle(self, vehicle_id: str) -> Optional[RescueVehicle]:
        """Search for a rescue vehicle by ID. Returns None if not found."""
        for veh in self._vehicles:
            if veh.get_id() == vehicle_id:
                return veh
        return None

    # =========================================================================
    # Accessor & Count Methods
    # =========================================================================

    def get_incidents(self) -> List[Incident]:
        """Return a shallow copy of the registered incidents list to prevent external mutation."""
        return list(self._incidents)

    def get_responders(self) -> List[Responder]:
        """Return a shallow copy of the registered responders list to prevent external mutation."""
        return list(self._responders)

    def get_vehicles(self) -> List[RescueVehicle]:
        """Return a shallow copy of the registered rescue vehicles list to prevent external mutation."""
        return list(self._vehicles)

    def get_incident_count(self) -> int:
        """Return total number of registered incidents."""
        return len(self._incidents)

    def get_responder_count(self) -> int:
        """Return total number of registered responders."""
        return len(self._responders)

    def get_vehicle_count(self) -> int:
        """Return total number of registered vehicles."""
        return len(self._vehicles)

    def get_available_responder_count(self) -> int:
        """Return number of currently available responders."""
        return sum(1 for resp in self._responders if resp.is_available())

    def get_available_vehicle_count(self) -> int:
        """Return number of currently available vehicles."""
        return sum(1 for veh in self._vehicles if veh.is_available())

    # =========================================================================
    # Operational & Dispatch Logic
    # =========================================================================

    def dispatch_resources(self, incident_id: str) -> bool:
        """Coordinate and dispatch available resources to an incident.

        Steps:
        1. Verify incident exists and is not resolved or already active.
        2. Select first available responder and first available vehicle.
        3. Transition availability to unavailable.
        4. Move positions to the incident location.
        5. Bind identifiers to the incident and update status to InProgress.

        Args:
            incident_id: Identifier of the incident receiving dispatch.

        Returns:
            True on successful dispatch.

        Raises:
            EntityNotFoundError (ValueError): If incident does not exist.
            InvalidStatusTransitionError (RuntimeError): If incident is Resolved
                or already has assigned resources.
            ResourceUnavailableError (RuntimeError): If no responder or vehicle
                is available.
        """
        inc = self.find_incident(incident_id)
        if inc is None:
            raise EntityNotFoundError(f"Incident with ID <{incident_id}> does not exist")

        if inc.get_status() in (IncidentStatus.RESOLVED, IncidentStatus.Resolved):
            raise InvalidStatusTransitionError(
                f"Incident <{incident_id}> is already resolved and cannot receive resources"
            )

        if (
            inc.get_status() in (IncidentStatus.IN_PROGRESS, IncidentStatus.InProgress)
            or inc.has_assigned_resources()
        ):
            raise InvalidStatusTransitionError(
                f"Incident <{incident_id}> already has active resources assigned"
            )

        # Select first available responder
        available_resp: Optional[Responder] = None
        for resp in self._responders:
            if resp.is_available():
                available_resp = resp
                break

        if available_resp is None:
            raise ResourceUnavailableError(
                "Dispatch failed: No responders available :("
            )

        # Select first available rescue vehicle
        available_veh: Optional[RescueVehicle] = None
        for veh in self._vehicles:
            if veh.is_available():
                available_veh = veh
                break

        if available_veh is None:
            raise ResourceUnavailableError(
                "Dispatch failed: No rescue vehicles available :("
            )

        # Mark resources unavailable
        available_resp.set_availability(False)
        available_veh.set_availability(False)

        # Update positions to incident location
        available_resp.set_position(inc.get_position())
        available_veh.set_position(inc.get_position())

        # Assign resources and transition status
        inc._set_status_direct(IncidentStatus.IN_PROGRESS)
        inc.assign_resources(available_resp.get_id(), available_veh.get_id())

        return True

    def update_incident_status(self, incident_id: str, new_status: IncidentStatus) -> None:
        """Update an incident's lifecycle status with transition validation.

        Transition rules:
        - Reported -> InProgress: Prohibited directly; use dispatch_resources().
        - Reported -> Resolved: Permitted (e.g. false alarms).
        - InProgress -> Reported: Prohibited.
        - InProgress -> Resolved: Permitted; automatically releases bound resources.
        - Resolved -> Any: Prohibited (terminal state).

        Args:
            incident_id: Target incident identifier.
            new_status: Desired new IncidentStatus.

        Raises:
            EntityNotFoundError (ValueError): If incident does not exist.
            InvalidStatusTransitionError (RuntimeError): On invalid or redundant transition.
        """
        inc = self.find_incident(incident_id)
        if inc is None:
            raise EntityNotFoundError(f"Incident with ID <{incident_id}> does not exist")

        current_status = inc.get_status()

        if current_status in (IncidentStatus.RESOLVED, IncidentStatus.Resolved):
            raise InvalidStatusTransitionError(
                f"Resolved incident <{incident_id}> cannot transition to another status."
            )

        if current_status in (IncidentStatus.FAILED, IncidentStatus.Failed):
            raise InvalidStatusTransitionError(
                f"Failed incident <{incident_id}> cannot transition to another status."
            )

        if current_status in (IncidentStatus.REPORTED, IncidentStatus.Reported):
            if new_status in (IncidentStatus.IN_PROGRESS, IncidentStatus.InProgress):
                raise InvalidStatusTransitionError(
                    f"Incident <{incident_id}> cannot transition directly from Reported "
                    f"to InProgress; use dispatchResources() to assign resources."
                )
            if new_status in (IncidentStatus.REPORTED, IncidentStatus.Reported):
                raise InvalidStatusTransitionError(
                    f"Incident <{incident_id}> is already in Reported status."
                )
            if new_status in (IncidentStatus.RESOLVED, IncidentStatus.Resolved):
                inc._set_status_direct(IncidentStatus.RESOLVED)
                return
            if new_status in (IncidentStatus.FAILED, IncidentStatus.Failed):
                if inc.has_assigned_resources():
                    resp = self.find_responder(inc.get_assigned_responder_id())
                    if resp is not None:
                        resp.set_availability(True)
                    veh = self.find_vehicle(inc.get_assigned_vehicle_id())
                    if veh is not None:
                        veh.set_availability(True)
                    inc.release_resources()
                inc._set_status_direct(IncidentStatus.FAILED)
                return

        if current_status in (IncidentStatus.IN_PROGRESS, IncidentStatus.InProgress):
            if new_status in (IncidentStatus.REPORTED, IncidentStatus.Reported):
                raise InvalidStatusTransitionError(
                    f"Active incident <{incident_id}> is already in progress and cannot "
                    f"be changed to reported!"
                )
            if new_status in (IncidentStatus.IN_PROGRESS, IncidentStatus.InProgress):
                raise InvalidStatusTransitionError(
                    f"Incident <{incident_id}> is already in progress"
                )
            if new_status in (IncidentStatus.RESOLVED, IncidentStatus.Resolved):
                # Release assigned units
                if inc.has_assigned_resources():
                    resp = self.find_responder(inc.get_assigned_responder_id())
                    if resp is not None:
                        resp.set_availability(True)
                    veh = self.find_vehicle(inc.get_assigned_vehicle_id())
                    if veh is not None:
                        veh.set_availability(True)
                    inc.release_resources()
                inc._set_status_direct(IncidentStatus.RESOLVED)
                return
            if new_status in (IncidentStatus.FAILED, IncidentStatus.Failed):
                # Release assigned units upon failure
                if inc.has_assigned_resources():
                    resp = self.find_responder(inc.get_assigned_responder_id())
                    if resp is not None:
                        resp.set_availability(True)
                    veh = self.find_vehicle(inc.get_assigned_vehicle_id())
                    if veh is not None:
                        veh.set_availability(True)
                    inc.release_resources()
                inc._set_status_direct(IncidentStatus.FAILED)
                return

        raise InvalidStatusTransitionError(
            f"Invalid status transition requested for incident <{incident_id}>"
        )

    def allocate_resources_csp(
        self,
        incidents: Optional[List[Incident]] = None,
        allow_partial: bool = False,
        solver: Optional[Any] = None,
    ) -> Any:
        """Coordinate and allocate fleet resources across multiple incidents using CSP.

        Performs atomic multi-resource allocation:
        1. Validates that all target incidents exist and are registered.
        2. Solves the Multi-Agent Resource Allocation CSP using the provided or default solver.
        3. If complete allocation succeeds (or partial is allowed and assignments exist):
           Atomically commits assignments: updates availability, repositions units,
           binds resource identifiers, and advances incident statuses to InProgress.
        4. If allocation is not feasible (and allow_partial is False):
           Leaves all incidents, responders, and vehicles in their exact original states.

        Args:
            incidents: Optional list of Incident objects to allocate. Defaults to all
                registered incidents currently in REPORTED status without assigned resources.
            allow_partial: If True, commits the best partial allocation if complete
                allocation is not feasible. Default is False.
            solver: Optional custom CSPSolver instance. Defaults to CSPSolver().

        Returns:
            CSPResult containing allocation outcomes, assignments, and search metrics.

        Raises:
            TypeError: If incidents is not a list/sequence of Incident objects.
            EntityNotFoundError (ValueError): If an incident in the provided list is not registered.
        """
        from algorithms.csp import CSPSolver, CSPResult

        active_solver = solver if solver is not None else CSPSolver()

        if incidents is not None:
            if not isinstance(incidents, (list, tuple, set)):
                raise TypeError("Expected a sequence of Incident objects.")
            for inc in incidents:
                if not isinstance(inc, Incident):
                    raise TypeError(f"Expected an Incident instance, got {type(inc)}.")
                if not self.has_incident(inc.get_id()):
                    raise EntityNotFoundError(
                        f"Incident <{inc.get_id()}> is not registered in this RescueManager."
                    )
            target_incidents = list(incidents)
        else:
            target_incidents = [
                inc
                for inc in self._incidents
                if inc.get_status() in (IncidentStatus.REPORTED, IncidentStatus.Reported)
                and not inc.has_assigned_resources()
            ]

        avail_responders = [r for r in self._responders if r.is_available()]
        avail_vehicles = [v for v in self._vehicles if v.is_available()]

        result: CSPResult = active_solver.solve(
            target_incidents,
            avail_responders,
            avail_vehicles,
            allow_partial=allow_partial,
        )

        # Commit assignments atomically if complete (or partial allowed and non-empty)
        if result.is_complete or (allow_partial and result.assigned_count > 0):
            for inc_id, (resp, veh) in result.assignments.items():
                manager_inc = self.find_incident(inc_id)
                manager_resp = self.find_responder(resp.get_id())
                manager_veh = self.find_vehicle(veh.get_id())

                if manager_inc is not None and manager_resp is not None and manager_veh is not None:
                    manager_resp.set_availability(False)
                    manager_veh.set_availability(False)
                    manager_resp.set_position(manager_inc.get_position())
                    manager_veh.set_position(manager_inc.get_position())
                    manager_inc._set_status_direct(IncidentStatus.IN_PROGRESS)
                    manager_inc.assign_resources(manager_resp.get_id(), manager_veh.get_id())

        return result

    # =========================================================================
    # C++ Compatibility Aliases
    # =========================================================================
    registerIncident = register_incident
    registerResponder = register_responder
    registerVehicle = register_vehicle
    hasIncident = has_incident
    hasResponder = has_responder
    hasVehicle = has_vehicle
    findIncident = find_incident
    findResponder = find_responder
    findVehicle = find_vehicle
    getIncidents = get_incidents
    getResponders = get_responders
    getVehicles = get_vehicles
    getIncidentCount = get_incident_count
    getResponderCount = get_responder_count
    getVehicleCount = get_vehicle_count
    getAvailableResponderCount = get_available_responder_count
    getAvailableVehicleCount = get_available_vehicle_count
    dispatchResources = dispatch_resources
    updateIncidentStatus = update_incident_status
    allocateResourcesCSP = allocate_resources_csp
