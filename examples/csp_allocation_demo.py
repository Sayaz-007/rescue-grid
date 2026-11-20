"""
RescueGrid — Multi-Agent Resource Allocation Demonstration (Phase 8).

Demonstrates:
1. Scenario A: Successful 4-incident resource allocation under constraint competition.
   - Shows why naive sequential greedy allocation deadlocks/fails.
   - Shows how CSP backtracking with MRV, Degree Heuristic, LCV, and Forward Checking
     preserves scarce specialist resources and finds a complete valid assignment.
2. Scenario B: Infeasible allocation due to specialist resource bottleneck.
   - Shows how CSP correctly detects impossibility without invalid resource assignments.
"""

import os
import sys

# Ensure root workspace directory is on module search path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from models.position import Position
from models.incident import Incident, IncidentType
from models.responder import Responder, ResponderSpecialization
from models.rescue_vehicle import RescueVehicle, VehicleType
from core.rescue_manager import RescueManager
from algorithms.csp import CSPSolver, allocate_resources_csp


def run_scenario_a() -> None:
    print("=" * 78)
    print("SCENARIO A: 4-INCIDENT DISASTER ALLOCATION UNDER RESOURCE CONTENTION")
    print("=" * 78)

    # 1. Active Incidents
    incidents = [
        Incident("INC-101", IncidentType.STRUCTURAL_COLLAPSE, 5, Position(4, 2)),
        Incident("INC-102", IncidentType.FLOOD, 4, Position(1, 6)),
        Incident("INC-103", IncidentType.FIRE, 4, Position(8, 3)),
        Incident("INC-104", IncidentType.MEDICAL, 3, Position(5, 7)),
    ]

    # 2. Response Fleet
    base_station = Position(0, 0)
    responders = [
        Responder("RES-01", "Carlos Cruz", ResponderSpecialization.RESCUE_SPECIALIST, base_station),
        Responder("RES-02", "Marcus Vance", ResponderSpecialization.FIREFIGHTER, base_station),
        Responder("RES-03", "Elena Rostova", ResponderSpecialization.FIREFIGHTER, base_station),
        Responder("RES-04", "Sarah Chen", ResponderSpecialization.PARAMEDIC, base_station),
    ]

    vehicles = [
        RescueVehicle("VEH-01", VehicleType.RESCUE_VAN, base_station),
        RescueVehicle("VEH-02", VehicleType.FIRE_ENGINE, base_station),
        RescueVehicle("VEH-03", VehicleType.FIRE_ENGINE, base_station),
        RescueVehicle("VEH-04", VehicleType.AMBULANCE, base_station),
    ]

    print("\n1. Active Emergency Incidents:")
    for inc in incidents:
        print(f"   [{inc.id}] Type: {inc.get_type_string():<18} | Severity: {inc.severity}/5 | Location: {inc.position}")

    print("\n2. Available Response Fleet Personnel:")
    for r in responders:
        print(f"   [{r.id}] Name: {r.name:<16} | Specialization: {r.get_specialization_string():<16} | Available: {r.is_available()}")

    print("\n3. Available Response Fleet Vehicles:")
    for v in vehicles:
        print(f"   [{v.id}] Classification: {v.get_type_string():<14} | Location: {v.position} | Available: {v.is_available()}")

    # 4. Domain Analysis
    solver = CSPSolver()
    domains = solver.build_initial_domains(incidents, responders, vehicles)

    print("\n4. Initial Candidate Domain Sizes (MRV Analysis):")
    for inc in incidents:
        candidates = domains[inc.id]
        print(f"   - {inc.id} ({inc.get_type_string()}): {len(candidates)} feasible (Responder, Vehicle) combinations")
        for resp, veh in candidates:
            print(f"       -> ({resp.id}:{resp.get_specialization_string()}, {veh.id}:{veh.get_type_string()})")

    # 5. Why Naive Sequential Greedy Allocation Fails
    print("\n" + "-" * 78)
    print("5. CONTRAST: Why Naive Sequential Greedy Allocation Fails")
    print("-" * 78)
    print("   If a naive scheduler processes incidents in order [INC-102 (Flood), INC-101 (Collapse), ...]:")
    print("   - Step 1: INC-102 (Flood) can use RES-01 (Rescue Specialist) + VEH-01 (Rescue Van).")
    print("             Naive allocator greedily assigns RES-01 + VEH-01 to INC-102.")
    print("   - Step 2: INC-101 (Structural Collapse) requires RESCUE_SPECIALIST and RESCUE_VAN.")
    print("             Neither RES-01 nor VEH-01 is available. No other specialists exist!")
    print("   - DEADLOCK: Naive allocation halts with INC-101 unassigned (Allocation Failure).")

    # 6. CSP Execution
    print("\n" + "-" * 78)
    print("6. CSP SOLVER EXECUTION (MRV + Degree + LCV + Forward Checking)")
    print("-" * 78)
    res = solver.solve(incidents, responders, vehicles)

    print(f"   Solver Outcome   : {res.status}")
    print(f"   Complete Solution: {'YES' if res.is_complete else 'NO'}")
    print(f"   Nodes Explored   : {res.nodes_explored}")
    print(f"   Backtracks       : {res.backtracks}")
    print(f"   Constraint Checks: {res.constraint_checks}")
    print(f"   Execution Time   : {res.execution_time_ms:.4f} ms")

    print("\n7. Final Constraint-Satisfied Assignments:")
    for inc_id in sorted(res.assignments.keys()):
        resp, veh = res.assignments[inc_id]
        inc = next(i for i in incidents if i.id == inc_id)
        print(
            f"   Incident {inc.id} ({inc.get_type_string():<18}, Sev {inc.severity}) -> "
            f"Responder: {resp.id} ({resp.name}, {resp.get_specialization_string()}) | "
            f"Vehicle: {veh.id} ({veh.get_type_string()})"
        )

    print("\n8. Resource Fleet Utilization:")
    assigned_resps = {resp.id for resp, _ in res.assignments.values()}
    assigned_vehs = {veh.id for _, veh in res.assignments.values()}
    print(f"   Responders Deployed: {len(assigned_resps)} / {len(responders)} ({100 * len(assigned_resps) / len(responders):.0f}%)")
    print(f"   Vehicles Deployed  : {len(assigned_vehs)} / {len(vehicles)} ({100 * len(assigned_vehs) / len(vehicles):.0f}%)")


def run_scenario_b() -> None:
    print("\n" + "=" * 78)
    print("SCENARIO B: INFEASIBLE ALLOCATION (SPECIALIST RESOURCE BOTTLENECK)")
    print("=" * 78)

    base_station = Position(0, 0)

    # Two structural collapse emergencies occur simultaneously
    incidents = [
        Incident("INC-201", IncidentType.STRUCTURAL_COLLAPSE, 5, Position(3, 3)),
        Incident("INC-202", IncidentType.STRUCTURAL_COLLAPSE, 4, Position(7, 5)),
    ]

    # Only one rescue specialist exists in the entire fleet
    responders = [
        Responder("RES-01", "Carlos Cruz", ResponderSpecialization.RESCUE_SPECIALIST, base_station),
        Responder("RES-02", "Marcus Vance", ResponderSpecialization.FIREFIGHTER, base_station),
    ]

    vehicles = [
        RescueVehicle("VEH-01", VehicleType.RESCUE_VAN, base_station),
        RescueVehicle("VEH-02", VehicleType.RESCUE_VAN, base_station),
    ]

    print("\n1. Active Incidents:")
    for inc in incidents:
        print(f"   [{inc.id}] Type: {inc.get_type_string()} | Requires: RESCUE_SPECIALIST + RESCUE_VAN")

    print("\n2. Fleet Inventory:")
    for r in responders:
        print(f"   [{r.id}] Name: {r.name} | Spec: {r.get_specialization_string()}")

    solver = CSPSolver()
    res = solver.solve(incidents, responders, vehicles)

    print(f"\n3. CSP Solver Result:")
    print(f"   Status          : {res.status}")
    print(f"   Complete        : {'YES' if res.is_complete else 'NO'}")
    print(f"   Allocated Count : {res.assigned_count} / {res.target_incident_count}")
    print(f"   Unassigned List : {res.unassigned_incident_ids}")
    print(f"   Nodes Explored  : {res.nodes_explored}")
    print(f"   Backtracks      : {res.backtracks}")
    print(f"   Constraint Checks: {res.constraint_checks}")

    print("\n4. Architectural & Safety Analysis:")
    print("   - Pigeonhole Bottleneck: 2 incidents require RESCUE_SPECIALIST, but only 1 specialist exists.")
    print("   - Constraint 5 (Resource Uniqueness): Assigning RES-01 to INC-201 causes an immediate")
    print("     domain wipeout on INC-202 during Forward Checking.")
    print("   - Invariant Preserved: Solver correctly refuses to double-assign RES-01 or substitute an")
    print("     incompatible FIREFIGHTER. It reports FAILED and commits zero partial changes.")


def main() -> None:
    print("\n" + "=" * 78)
    print("       RescueGrid — Multi-Agent Resource Allocation (CSP Phase 8)       ")
    print("=" * 78)
    run_scenario_a()
    run_scenario_b()
    print("\n" + "=" * 78)
    print("CSP Demonstration completed successfully.")
    print("=" * 78 + "\n")


if __name__ == "__main__":
    main()
