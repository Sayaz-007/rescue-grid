#include "rescuegrid/Position.h"
#include "rescuegrid/Incident.h"
#include "rescuegrid/Responder.h"
#include "rescuegrid/RescueVehicle.h"
#include "rescuegrid/RescueManager.h"

#include <iostream>
#include <sstream>
#include <string>
#include <stdexcept>
#include <vector>

using namespace rescuegrid;

// Simple test assertion helper
#define EXPECT_TRUE(cond, msg) \
    do { \
        if (!(cond)) { \
            std::cerr << "  [FAIL] " << msg << " (" << __FILE__ << ":" << __LINE__ << ")\n"; \
            return false; \
        } \
    } while (false)

#define EXPECT_EQ(val1, val2, msg) \
    do { \
        if (!((val1) == (val2))) { \
            std::cerr << "  [FAIL] " << msg << ": expected equal (" << __FILE__ << ":" << __LINE__ << ")\n"; \
            return false; \
        } \
    } while (false)

#define EXPECT_THROW(stmt, ex_type, msg) \
    do { \
        bool threw = false; \
        try { \
            stmt; \
        } catch (const ex_type&) { \
            threw = true; \
        } catch (...) { \
            std::cerr << "  [FAIL] " << msg << ": unexpected exception type (" << __FILE__ << ":" << __LINE__ << ")\n"; \
            return false; \
        } \
        if (!threw) { \
            std::cerr << "  [FAIL] " << msg << ": expected exception not thrown (" << __FILE__ << ":" << __LINE__ << ")\n"; \
            return false; \
        } \
    } while (false)

// ============================================================================
// Phase 2 Core Tests (Preserved)
// ============================================================================

bool testPositionCoordinates() {
    std::cout << "Running testPositionCoordinates...\n";

    Position defaultPos;
    EXPECT_EQ(defaultPos.getX(), 0, "Default Position X coordinate");
    EXPECT_EQ(defaultPos.getY(), 0, "Default Position Y coordinate");
    EXPECT_EQ(defaultPos.toString(), "(0, 0)", "Default Position toString format");

    Position customPos(15, -42);
    EXPECT_EQ(customPos.getX(), 15, "Custom Position X coordinate");
    EXPECT_EQ(customPos.getY(), -42, "Custom Position Y coordinate");
    EXPECT_EQ(customPos.toString(), "(15, -42)", "Custom Position toString format");

    return true;
}

bool testIncidentConstructionAndValidation() {
    std::cout << "Running testIncidentConstructionAndValidation...\n";

    Position loc(5, 10);

    // Valid incident
    Incident inc("INC-101", IncidentType::Fire, 4, loc);
    EXPECT_EQ(inc.getId(), "INC-101", "Incident ID match");
    EXPECT_EQ(inc.getSeverity(), 4, "Incident severity match");
    EXPECT_EQ(inc.getTypeString(), "Fire", "Incident type string");
    EXPECT_EQ(inc.getStatus(), IncidentStatus::Reported, "Default incident status");
    EXPECT_EQ(inc.getPosition().getX(), 5, "Incident position X");
    EXPECT_EQ(inc.getPosition().getY(), 10, "Incident position Y");

    // Severity boundary validations (valid: 1 and 5)
    Incident incMin("INC-MIN", IncidentType::Flood, 1, loc);
    EXPECT_EQ(incMin.getSeverity(), 1, "Incident min severity 1");

    Incident incMax("INC-MAX", IncidentType::StructuralCollapse, 5, loc);
    EXPECT_EQ(incMax.getSeverity(), 5, "Incident max severity 5");

    // Invalid severity < 1
    EXPECT_THROW(
        Incident("INC-ERR", IncidentType::Fire, 0, loc),
        std::invalid_argument,
        "Severity 0 should throw invalid_argument"
    );

    // Invalid severity > 5
    EXPECT_THROW(
        Incident("INC-ERR", IncidentType::Fire, 6, loc),
        std::invalid_argument,
        "Severity 6 should throw invalid_argument"
    );

    // Empty ID
    EXPECT_THROW(
        Incident("", IncidentType::Fire, 3, loc),
        std::invalid_argument,
        "Empty Incident ID should throw invalid_argument"
    );

    return true;
}

bool testIncidentStatusUpdates() {
    std::cout << "Running testIncidentStatusUpdates...\n";

    Position loc(2, 8);
    Incident inc("INC-202", IncidentType::Flood, 2, loc);

    EXPECT_EQ(inc.getStatus(), IncidentStatus::Reported, "Initial status Reported");
    EXPECT_EQ(inc.getStatusString(), "Reported", "Initial status string Reported");

    inc.setStatus(IncidentStatus::InProgress);
    EXPECT_EQ(inc.getStatus(), IncidentStatus::InProgress, "Updated status InProgress");
    EXPECT_EQ(inc.getStatusString(), "InProgress", "Updated status string InProgress");

    inc.setStatus(IncidentStatus::Resolved);
    EXPECT_EQ(inc.getStatus(), IncidentStatus::Resolved, "Updated status Resolved");
    EXPECT_EQ(inc.getStatusString(), "Resolved", "Updated status string Resolved");

    return true;
}

bool testResponderConstructionAndUpdates() {
    std::cout << "Running testResponderConstructionAndUpdates...\n";

    Position homeBase(0, 0);

    // Valid responder
    Responder resp("RES-01", "Marcus Vance", ResponderSpecialization::Firefighter, homeBase);
    EXPECT_EQ(resp.getId(), "RES-01", "Responder ID match");
    EXPECT_EQ(resp.getName(), "Marcus Vance", "Responder name match");
    EXPECT_EQ(resp.getSpecializationString(), "Firefighter", "Specialization string match");
    EXPECT_TRUE(resp.isAvailable(), "Responder default availability should be true");
    EXPECT_EQ(resp.getPosition().getX(), 0, "Initial position X");
    EXPECT_EQ(resp.getPosition().getY(), 0, "Initial position Y");

    // Position update
    Position dispatchTarget(12, 34);
    resp.setPosition(dispatchTarget);
    EXPECT_EQ(resp.getPosition().getX(), 12, "Updated position X");
    EXPECT_EQ(resp.getPosition().getY(), 34, "Updated position Y");

    // Overloaded position update: setPosition(int, int)
    resp.setPosition(56, 78);
    EXPECT_EQ(resp.getPosition().getX(), 56, "Overloaded position X");
    EXPECT_EQ(resp.getPosition().getY(), 78, "Overloaded position Y");
    EXPECT_EQ(resp.getPosition(), Position(56, 78), "Overloaded position matches Position(56, 78)");

    // Availability update
    resp.setAvailability(false);
    EXPECT_TRUE(!resp.isAvailable(), "Updated availability should be false");

    resp.setAvailability(true);
    EXPECT_TRUE(resp.isAvailable(), "Updated availability should be true");

    // Empty name validation
    EXPECT_THROW(
        Responder("RES-ERR", "", ResponderSpecialization::Paramedic, homeBase),
        std::invalid_argument,
        "Empty Responder name should throw invalid_argument"
    );

    // Empty ID validation
    EXPECT_THROW(
        Responder("", "Valid Name", ResponderSpecialization::Paramedic, homeBase),
        std::invalid_argument,
        "Empty Responder ID should throw invalid_argument"
    );

    return true;
}

bool testRescueVehicleConstructionAndUpdates() {
    std::cout << "Running testRescueVehicleConstructionAndUpdates...\n";

    Position station(4, 4);

    // Valid vehicle
    RescueVehicle vehicle("VEH-10", VehicleType::Ambulance, station);
    EXPECT_EQ(vehicle.getId(), "VEH-10", "Vehicle ID match");
    EXPECT_EQ(vehicle.getTypeString(), "Ambulance", "Vehicle type string match");
    EXPECT_TRUE(vehicle.isAvailable(), "Vehicle default availability should be true");
    EXPECT_EQ(vehicle.getPosition().getX(), 4, "Initial vehicle position X");
    EXPECT_EQ(vehicle.getPosition().getY(), 4, "Initial vehicle position Y");

    // Position update
    Position scene(20, 30);
    vehicle.setPosition(scene);
    EXPECT_EQ(vehicle.getPosition().getX(), 20, "Updated vehicle position X");
    EXPECT_EQ(vehicle.getPosition().getY(), 30, "Updated vehicle position Y");

    // Overloaded position update: setPosition(int, int)
    vehicle.setPosition(77, 88);
    EXPECT_EQ(vehicle.getPosition().getX(), 77, "Overloaded vehicle position X");
    EXPECT_EQ(vehicle.getPosition().getY(), 88, "Overloaded vehicle position Y");
    EXPECT_EQ(vehicle.getPosition(), Position(77, 88), "Overloaded vehicle position matches Position(77, 88)");

    // Availability update
    vehicle.setAvailability(false);
    EXPECT_TRUE(!vehicle.isAvailable(), "Updated vehicle availability should be false");

    // Empty ID validation
    EXPECT_THROW(
        RescueVehicle("", VehicleType::RescueVan, station),
        std::invalid_argument,
        "Empty Vehicle ID should throw invalid_argument"
    );

    return true;
}

// ============================================================================
// Phase 3 Manager, Search, and Dispatch Tests
// ============================================================================

bool testManagerRegistrationAndListing() {
    std::cout << "Running testManagerRegistrationAndListing...\n";

    RescueManager manager;
    EXPECT_EQ(manager.getIncidentCount(), 0, "Initial incident count should be 0");
    EXPECT_EQ(manager.getResponderCount(), 0, "Initial responder count should be 0");
    EXPECT_EQ(manager.getVehicleCount(), 0, "Initial vehicle count should be 0");

    // Register incidents
    manager.registerIncident(Incident("INC-1", IncidentType::Fire, 3, Position(10, 10)));
    manager.registerIncident(Incident("INC-2", IncidentType::Flood, 5, Position(20, 20)));
    EXPECT_EQ(manager.getIncidentCount(), 2, "Incident count after registration");
    EXPECT_EQ(manager.getIncidents()[0].getId(), "INC-1", "First incident ID");
    EXPECT_EQ(manager.getIncidents()[1].getId(), "INC-2", "Second incident ID");

    // Register responders
    manager.registerResponder(Responder("R-1", "Alice", ResponderSpecialization::Firefighter, Position(0, 0)));
    manager.registerResponder(Responder("R-2", "Bob", ResponderSpecialization::Paramedic, Position(0, 0)));
    EXPECT_EQ(manager.getResponderCount(), 2, "Responder count after registration");
    EXPECT_EQ(manager.getAvailableResponderCount(), 2, "Available responder count");

    // Register vehicles
    manager.registerVehicle(RescueVehicle("V-1", VehicleType::FireEngine, Position(0, 0)));
    manager.registerVehicle(RescueVehicle("V-2", VehicleType::Ambulance, Position(0, 0)));
    EXPECT_EQ(manager.getVehicleCount(), 2, "Vehicle count after registration");
    EXPECT_EQ(manager.getAvailableVehicleCount(), 2, "Available vehicle count");

    return true;
}

bool testManagerSearchAndDuplicateHandling() {
    std::cout << "Running testManagerSearchAndDuplicateHandling...\n";

    RescueManager manager;
    manager.registerIncident(Incident("INC-A", IncidentType::Fire, 2, Position(5, 5)));
    manager.registerResponder(Responder("R-A", "Carlos", ResponderSpecialization::RescueSpecialist, Position(0, 0)));
    manager.registerVehicle(RescueVehicle("V-A", VehicleType::RescueVan, Position(0, 0)));

    // Existing searches
    const Incident* foundInc = manager.findIncident("INC-A");
    EXPECT_TRUE(foundInc != nullptr, "Incident INC-A should be found");
    EXPECT_EQ(foundInc->getId(), "INC-A", "Found incident ID matches");
    EXPECT_EQ(foundInc->getSeverity(), 2, "Found incident severity matches");

    EXPECT_TRUE(manager.hasIncident("INC-A"), "hasIncident returns true for INC-A");
    EXPECT_TRUE(manager.hasResponder("R-A"), "hasResponder returns true for R-A");
    EXPECT_TRUE(manager.hasVehicle("V-A"), "hasVehicle returns true for V-A");

    // Missing searches
    EXPECT_TRUE(manager.findIncident("NON-EXISTENT") == nullptr, "Missing incident returns nullptr");
    EXPECT_TRUE(manager.findResponder("NON-EXISTENT") == nullptr, "Missing responder returns nullptr");
    EXPECT_TRUE(manager.findVehicle("NON-EXISTENT") == nullptr, "Missing vehicle returns nullptr");
    EXPECT_TRUE(!manager.hasIncident("NON-EXISTENT"), "hasIncident returns false for missing ID");

    // Duplicate registrations
    EXPECT_THROW(
        manager.registerIncident(Incident("INC-A", IncidentType::Flood, 1, Position(1, 1))),
        std::invalid_argument,
        "Duplicate incident registration should throw invalid_argument"
    );

    EXPECT_THROW(
        manager.registerResponder(Responder("R-A", "Duplicate Name", ResponderSpecialization::Paramedic, Position(0, 0))),
        std::invalid_argument,
        "Duplicate responder registration should throw invalid_argument"
    );

    EXPECT_THROW(
        manager.registerVehicle(RescueVehicle("V-A", VehicleType::FireEngine, Position(0, 0))),
        std::invalid_argument,
        "Duplicate vehicle registration should throw invalid_argument"
    );

    return true;
}

bool testDispatchResourcesSuccess() {
    std::cout << "Running testDispatchResourcesSuccess...\n";

    RescueManager manager;
    manager.registerIncident(Incident("INC-DISP", IncidentType::Fire, 4, Position(50, 75)));
    manager.registerResponder(Responder("R-DISP", "Elena", ResponderSpecialization::Firefighter, Position(0, 0)));
    manager.registerVehicle(RescueVehicle("V-DISP", VehicleType::FireEngine, Position(0, 0)));

    EXPECT_EQ(manager.getAvailableResponderCount(), 1, "Initially 1 available responder");
    EXPECT_EQ(manager.getAvailableVehicleCount(), 1, "Initially 1 available vehicle");

    // Execute dispatch
    bool result = manager.dispatchResources("INC-DISP");
    EXPECT_TRUE(result, "Dispatch should return true on success");

    // Verify incident state
    const Incident* inc = manager.findIncident("INC-DISP");
    EXPECT_TRUE(inc != nullptr, "Incident must exist");
    EXPECT_EQ(inc->getStatus(), IncidentStatus::InProgress, "Incident status should be InProgress");
    EXPECT_TRUE(inc->hasAssignedResources(), "Incident should have assigned resources");
    EXPECT_EQ(inc->getAssignedResponderId(), "R-DISP", "Assigned responder ID match");
    EXPECT_EQ(inc->getAssignedVehicleId(), "V-DISP", "Assigned vehicle ID match");

    // Verify responder state
    const Responder* resp = manager.findResponder("R-DISP");
    EXPECT_TRUE(resp != nullptr, "Responder must exist");
    EXPECT_TRUE(!resp->isAvailable(), "Responder should now be unavailable");
    EXPECT_EQ(resp->getPosition().getX(), 50, "Responder moved to incident X");
    EXPECT_EQ(resp->getPosition().getY(), 75, "Responder moved to incident Y");

    // Verify vehicle state
    const RescueVehicle* veh = manager.findVehicle("V-DISP");
    EXPECT_TRUE(veh != nullptr, "Vehicle must exist");
    EXPECT_TRUE(!veh->isAvailable(), "Vehicle should now be unavailable");
    EXPECT_EQ(veh->getPosition().getX(), 50, "Vehicle moved to incident X");
    EXPECT_EQ(veh->getPosition().getY(), 75, "Vehicle moved to incident Y");

    EXPECT_EQ(manager.getAvailableResponderCount(), 0, "0 available responders remaining");
    EXPECT_EQ(manager.getAvailableVehicleCount(), 0, "0 available vehicles remaining");

    return true;
}

bool testDispatchResourcesUnavailableAndRejection() {
    std::cout << "Running testDispatchResourcesUnavailableAndRejection...\n";

    RescueManager manager;

    // 1. Dispatching to non-existent incident
    EXPECT_THROW(
        manager.dispatchResources("MISSING-INC"),
        std::invalid_argument,
        "Dispatch to missing incident should throw invalid_argument"
    );

    // 2. Incident exists, but no responders or vehicles registered
    manager.registerIncident(Incident("INC-NO-RES", IncidentType::Flood, 3, Position(10, 10)));
    EXPECT_THROW(
        manager.dispatchResources("INC-NO-RES"),
        std::runtime_error,
        "Dispatch with no responders should throw runtime_error"
    );

    // 3. Responder registered, but no vehicles registered
    manager.registerResponder(Responder("R-1", "Dan", ResponderSpecialization::Paramedic, Position(0, 0)));
    EXPECT_THROW(
        manager.dispatchResources("INC-NO-RES"),
        std::runtime_error,
        "Dispatch with no vehicles should throw runtime_error"
    );

    // 4. Vehicle registered -> now dispatch can succeed
    manager.registerVehicle(RescueVehicle("V-1", VehicleType::Ambulance, Position(0, 0)));
    manager.dispatchResources("INC-NO-RES");

    // 5. Attempting to dispatch again to an incident already InProgress
    EXPECT_THROW(
        manager.dispatchResources("INC-NO-RES"),
        std::logic_error,
        "Dispatch to already InProgress incident should throw logic_error"
    );

    // 6. Attempting to dispatch to a Resolved incident
    manager.registerIncident(Incident("INC-RESOLVED", IncidentType::Fire, 1, Position(2, 2), IncidentStatus::Resolved));
    EXPECT_THROW(
        manager.dispatchResources("INC-RESOLVED"),
        std::logic_error,
        "Dispatch to already Resolved incident should throw logic_error"
    );

    return true;
}

bool testPreventDoubleAssignment() {
    std::cout << "Running testPreventDoubleAssignment...\n";

    RescueManager manager;
    manager.registerIncident(Incident("INC-1", IncidentType::Fire, 2, Position(10, 10)));
    manager.registerIncident(Incident("INC-2", IncidentType::Flood, 4, Position(20, 20)));

    // Register only ONE responder and ONE vehicle
    manager.registerResponder(Responder("R-SOLE", "Solo Responder", ResponderSpecialization::RescueSpecialist, Position(0, 0)));
    manager.registerVehicle(RescueVehicle("V-SOLE", VehicleType::RescueVan, Position(0, 0)));

    // Dispatch INC-1
    manager.dispatchResources("INC-1");

    // Attempt to dispatch INC-2: must fail because all resources are busy
    EXPECT_THROW(
        manager.dispatchResources("INC-2"),
        std::runtime_error,
        "Dispatching INC-2 with busy resources should throw runtime_error"
    );

    // Verify INC-2 was NOT modified
    const Incident* inc2 = manager.findIncident("INC-2");
    EXPECT_EQ(inc2->getStatus(), IncidentStatus::Reported, "INC-2 must remain Reported");
    EXPECT_TRUE(!inc2->hasAssignedResources(), "INC-2 must not have resources assigned");

    return true;
}

bool testStatusUpdateAndResourceRelease() {
    std::cout << "Running testStatusUpdateAndResourceRelease...\n";

    RescueManager manager;
    manager.registerIncident(Incident("INC-X", IncidentType::Fire, 3, Position(30, 30)));
    manager.registerIncident(Incident("INC-Y", IncidentType::Flood, 2, Position(40, 40)));

    manager.registerResponder(Responder("R-SHARED", "Shared Responder", ResponderSpecialization::Firefighter, Position(0, 0)));
    manager.registerVehicle(RescueVehicle("V-SHARED", VehicleType::FireEngine, Position(0, 0)));

    // Dispatch INC-X
    manager.dispatchResources("INC-X");
    EXPECT_EQ(manager.getAvailableResponderCount(), 0, "No available responders while INC-X in progress");

    // Resolve INC-X
    manager.updateIncidentStatus("INC-X", IncidentStatus::Resolved);

    // Verify INC-X resolved and resources freed
    const Incident* incX = manager.findIncident("INC-X");
    EXPECT_EQ(incX->getStatus(), IncidentStatus::Resolved, "INC-X is Resolved");
    EXPECT_TRUE(!incX->hasAssignedResources(), "INC-X released resource bindings");

    const Responder* resp = manager.findResponder("R-SHARED");
    EXPECT_TRUE(resp->isAvailable(), "Responder is available again after INC-X resolution");

    const RescueVehicle* veh = manager.findVehicle("V-SHARED");
    EXPECT_TRUE(veh->isAvailable(), "Vehicle is available again after INC-X resolution");

    EXPECT_EQ(manager.getAvailableResponderCount(), 1, "1 available responder after release");
    EXPECT_EQ(manager.getAvailableVehicleCount(), 1, "1 available vehicle after release");

    // Now INC-Y can be dispatched successfully using the released resources!
    bool yResult = manager.dispatchResources("INC-Y");
    EXPECT_TRUE(yResult, "INC-Y dispatch succeeds using freed resources");

    const Incident* incY = manager.findIncident("INC-Y");
    EXPECT_EQ(incY->getStatus(), IncidentStatus::InProgress, "INC-Y is now InProgress");
    EXPECT_EQ(incY->getAssignedResponderId(), "R-SHARED", "INC-Y assigned to R-SHARED");

    // Non-existent incident status update throws invalid_argument
    EXPECT_THROW(
        manager.updateIncidentStatus("MISSING", IncidentStatus::Resolved),
        std::invalid_argument,
        "Updating non-existent incident should throw invalid_argument"
    );

    return true;
}

bool testIncidentLifecycleAndInvalidTransitions() {
    std::cout << "Running testIncidentLifecycleAndInvalidTransitions...\n";

    RescueManager manager;

    // 1. Attempting to mark an incident InProgress without a successful dispatch
    manager.registerIncident(Incident("INC-L1", IncidentType::Fire, 2, Position(10, 10)));
    EXPECT_THROW(
        manager.updateIncidentStatus("INC-L1", IncidentStatus::InProgress),
        std::logic_error,
        "Direct Reported -> InProgress transition without dispatch must throw logic_error"
    );
    const Incident* incL1 = manager.findIncident("INC-L1");
    EXPECT_EQ(incL1->getStatus(), IncidentStatus::Reported, "Incident must remain Reported after rejected transition");
    EXPECT_TRUE(!incL1->hasAssignedResources(), "Incident must have no assigned resources");

    // 2. Dispatch resources to make INC-L1 active (InProgress)
    manager.registerResponder(Responder("R-L1", "Responder 1", ResponderSpecialization::Firefighter, Position(0, 0)));
    manager.registerVehicle(RescueVehicle("V-L1", VehicleType::FireEngine, Position(0, 0)));
    manager.dispatchResources("INC-L1");

    EXPECT_EQ(incL1->getStatus(), IncidentStatus::InProgress, "INC-L1 is now InProgress");
    EXPECT_TRUE(incL1->hasAssignedResources(), "INC-L1 now has assigned resources");
    const Responder* respL1 = manager.findResponder("R-L1");
    const RescueVehicle* vehL1 = manager.findVehicle("V-L1");
    EXPECT_TRUE(!respL1->isAvailable(), "R-L1 is unavailable during active dispatch");
    EXPECT_TRUE(!vehL1->isAvailable(), "V-L1 is unavailable during active dispatch");

    // 3. Attempting to move an active incident with assigned resources back to Reported
    EXPECT_THROW(
        manager.updateIncidentStatus("INC-L1", IncidentStatus::Reported),
        std::logic_error,
        "Active incident cannot be reverted from InProgress to Reported"
    );

    // Confirm rejected transition leaves resource assignments and availability unchanged
    EXPECT_EQ(incL1->getStatus(), IncidentStatus::InProgress, "INC-L1 must remain InProgress");
    EXPECT_TRUE(incL1->hasAssignedResources(), "INC-L1 must still retain assigned resources");
    EXPECT_EQ(incL1->getAssignedResponderId(), "R-L1", "Assigned responder must still be R-L1");
    EXPECT_EQ(incL1->getAssignedVehicleId(), "V-L1", "Assigned vehicle must still be V-L1");
    EXPECT_TRUE(!respL1->isAvailable(), "R-L1 must remain unavailable after rejected transition");
    EXPECT_TRUE(!vehL1->isAvailable(), "V-L1 must remain unavailable after rejected transition");

    // 4. Valid resolution releases assigned resources
    manager.updateIncidentStatus("INC-L1", IncidentStatus::Resolved);
    EXPECT_EQ(incL1->getStatus(), IncidentStatus::Resolved, "INC-L1 is now Resolved");
    EXPECT_TRUE(!incL1->hasAssignedResources(), "INC-L1 resources must be cleared");
    EXPECT_TRUE(respL1->isAvailable(), "R-L1 must be released to available");
    EXPECT_TRUE(vehL1->isAvailable(), "V-L1 must be released to available");

    // 5. Attempting to reopen a Resolved incident
    EXPECT_THROW(
        manager.updateIncidentStatus("INC-L1", IncidentStatus::Reported),
        std::logic_error,
        "Resolved incident cannot be reopened to Reported"
    );
    EXPECT_THROW(
        manager.updateIncidentStatus("INC-L1", IncidentStatus::InProgress),
        std::logic_error,
        "Resolved incident cannot be reopened to InProgress"
    );
    EXPECT_THROW(
        manager.updateIncidentStatus("INC-L1", IncidentStatus::Resolved),
        std::logic_error,
        "Resolved incident cannot transition to Resolved again"
    );
    EXPECT_THROW(
        manager.dispatchResources("INC-L1"),
        std::logic_error,
        "Resolved incident cannot receive dispatch"
    );
    EXPECT_EQ(incL1->getStatus(), IncidentStatus::Resolved, "INC-L1 remains Resolved");

    // 6. Direct Reported -> Resolved transition without dispatch (e.g. false alarm)
    manager.registerIncident(Incident("INC-L2", IncidentType::Flood, 1, Position(20, 20)));
    manager.updateIncidentStatus("INC-L2", IncidentStatus::Resolved);
    const Incident* incL2 = manager.findIncident("INC-L2");
    EXPECT_EQ(incL2->getStatus(), IncidentStatus::Resolved, "Reported incident directly resolved");
    EXPECT_TRUE(!incL2->hasAssignedResources(), "Directly resolved incident has no assigned resources");
    EXPECT_THROW(
        manager.updateIncidentStatus("INC-L2", IncidentStatus::Reported),
        std::logic_error,
        "Directly resolved incident cannot be reopened"
    );

    // 7. Resolving one incident must NOT release resources belonging to another incident
    RescueManager isoManager;
    isoManager.registerIncident(Incident("INC-ISO1", IncidentType::Fire, 3, Position(30, 30)));
    isoManager.registerIncident(Incident("INC-ISO2", IncidentType::Flood, 4, Position(40, 40)));
    isoManager.registerResponder(Responder("R-ISO1", "Resp ISO 1", ResponderSpecialization::Firefighter, Position(0, 0)));
    isoManager.registerResponder(Responder("R-ISO2", "Resp ISO 2", ResponderSpecialization::Paramedic, Position(0, 0)));
    isoManager.registerVehicle(RescueVehicle("V-ISO1", VehicleType::FireEngine, Position(0, 0)));
    isoManager.registerVehicle(RescueVehicle("V-ISO2", VehicleType::Ambulance, Position(0, 0)));

    isoManager.dispatchResources("INC-ISO1");
    isoManager.dispatchResources("INC-ISO2");

    // Both incidents are active
    const Incident* incIso1 = isoManager.findIncident("INC-ISO1");
    const Incident* incIso2 = isoManager.findIncident("INC-ISO2");
    const Responder* respIso1 = isoManager.findResponder("R-ISO1");
    const Responder* respIso2 = isoManager.findResponder("R-ISO2");
    const RescueVehicle* vehIso1 = isoManager.findVehicle("V-ISO1");
    const RescueVehicle* vehIso2 = isoManager.findVehicle("V-ISO2");

    EXPECT_TRUE(!respIso1->isAvailable(), "R-ISO1 busy with INC-ISO1");
    EXPECT_TRUE(!respIso2->isAvailable(), "R-ISO2 busy with INC-ISO2");

    // Resolve INC-ISO1 only
    isoManager.updateIncidentStatus("INC-ISO1", IncidentStatus::Resolved);

    // Verify INC-ISO1 freed its resources
    EXPECT_EQ(incIso1->getStatus(), IncidentStatus::Resolved, "INC-ISO1 is resolved");
    EXPECT_TRUE(respIso1->isAvailable(), "R-ISO1 is now available");
    EXPECT_TRUE(vehIso1->isAvailable(), "V-ISO1 is now available");

    // Verify INC-ISO2 resources are UNTOUCHED
    EXPECT_EQ(incIso2->getStatus(), IncidentStatus::InProgress, "INC-ISO2 remains InProgress");
    EXPECT_TRUE(incIso2->hasAssignedResources(), "INC-ISO2 retains assigned resources");
    EXPECT_EQ(incIso2->getAssignedResponderId(), "R-ISO2", "INC-ISO2 still assigned to R-ISO2");
    EXPECT_EQ(incIso2->getAssignedVehicleId(), "V-ISO2", "INC-ISO2 still assigned to V-ISO2");
    EXPECT_TRUE(!respIso2->isAvailable(), "R-ISO2 remains unavailable");
    EXPECT_TRUE(!vehIso2->isAvailable(), "V-ISO2 remains unavailable");

    return true;
}

// ============================================================================
// Phase 4 Operator and Function Overloading Tests
// ============================================================================

bool testPositionOperatorsAndOverloading() {
    std::cout << "Running testPositionOperatorsAndOverloading...\n";

    // Requirement 6: Default constructor initializes to (0, 0)
    Position pDefault;
    EXPECT_EQ(pDefault.getX(), 0, "Default Position constructor X is 0");
    EXPECT_EQ(pDefault.getY(), 0, "Default Position constructor Y is 0");
    EXPECT_EQ(pDefault.toString(), "(0, 0)", "Default Position toString format");

    // Requirement 7: Parameterized constructor initializes to given coordinates
    Position pParam(15, 20);
    EXPECT_EQ(pParam.getX(), 15, "Parameterized Position constructor X");
    EXPECT_EQ(pParam.getY(), 20, "Parameterized Position constructor Y");
    EXPECT_EQ(pParam.toString(), "(15, 20)", "Parameterized Position toString format");

    Position pNegative(-8, -42);
    EXPECT_EQ(pNegative.getX(), -8, "Negative Position constructor X");
    EXPECT_EQ(pNegative.getY(), -42, "Negative Position constructor Y");

    // Requirement 1: pos1 == pos2 returns true when coordinates are identical
    Position p1(10, 20);
    Position p2(10, 20);
    EXPECT_TRUE(p1 == p2, "Identical positions must compare equal with operator==");
    EXPECT_TRUE(pDefault == Position(0, 0), "Default position equals Position(0, 0)");

    // Requirement 2: pos1 != pos2 returns true when x differs, y differs, or both differ
    Position pDiffX(11, 20);
    Position pDiffY(10, 21);
    Position pDiffBoth(99, 88);

    EXPECT_TRUE(p1 != pDiffX, "operator!= returns true when X differs");
    EXPECT_TRUE(p1 != pDiffY, "operator!= returns true when Y differs");
    EXPECT_TRUE(p1 != pDiffBoth, "operator!= returns true when both X and Y differ");

    EXPECT_TRUE(!(p1 == pDiffX), "operator== returns false when X differs");
    EXPECT_TRUE(!(p1 == pDiffY), "operator== returns false when Y differs");
    EXPECT_TRUE(!(p1 == pDiffBoth), "operator== returns false when both X and Y differ");

    // Requirement 3: operator!= is the logical inverse of operator==
    EXPECT_TRUE((p1 == p2) == !(p1 != p2), "operator!= must be logical inverse of operator== for equal positions");
    EXPECT_TRUE((p1 == pDiffX) == !(p1 != pDiffX), "operator!= must be logical inverse of operator== for diff X");
    EXPECT_TRUE((p1 == pDiffY) == !(p1 != pDiffY), "operator!= must be logical inverse of operator== for diff Y");
    EXPECT_TRUE((p1 == pDiffBoth) == !(p1 != pDiffBoth), "operator!= must be logical inverse of operator== for diff both");

    // Requirement 4: Stream insertion formatting: std::ostringstream << Position(15, 20) -> "(15, 20)"
    std::ostringstream oss;
    oss << Position(15, 20);
    EXPECT_EQ(oss.str(), "(15, 20)", "Stream insertion matches (15, 20)");

    // Requirement 5: Stream insertion chaining: oss << "At " << pos << " confirmed"
    std::ostringstream ossChain;
    Position loc(1, 2);
    ossChain << "At " << loc << " confirmed";
    EXPECT_EQ(ossChain.str(), "At (1, 2) confirmed", "Stream insertion chaining produces expected output");

    // Stream insertion matches toString() output
    std::ostringstream ossMatch;
    Position matchPos(33, -99);
    ossMatch << matchPos;
    EXPECT_EQ(ossMatch.str(), matchPos.toString(), "Stream insertion matches toString() result");

    // Requirement 8: Overloaded Responder::setPosition(int, int) matches setPosition(Position)
    Position basePos(0, 0);
    Responder resp1("R-OV1", "Alice", ResponderSpecialization::Firefighter, basePos);
    Responder resp2("R-OV2", "Bob", ResponderSpecialization::Firefighter, basePos);

    resp1.setPosition(Position(25, 35));
    resp2.setPosition(25, 35);
    EXPECT_EQ(resp2.getPosition(), resp1.getPosition(), "Responder setPosition(int, int) matches setPosition(Position)");
    EXPECT_EQ(resp2.getPosition().getX(), 25, "Responder X after setPosition(int, int)");
    EXPECT_EQ(resp2.getPosition().getY(), 35, "Responder Y after setPosition(int, int)");

    // Requirement 9: Overloaded RescueVehicle::setPosition(int, int) matches setPosition(Position)
    RescueVehicle veh1("V-OV1", VehicleType::FireEngine, basePos);
    RescueVehicle veh2("V-OV2", VehicleType::FireEngine, basePos);

    veh1.setPosition(Position(45, 55));
    veh2.setPosition(45, 55);
    EXPECT_EQ(veh2.getPosition(), veh1.getPosition(), "RescueVehicle setPosition(int, int) matches setPosition(Position)");
    EXPECT_EQ(veh2.getPosition().getX(), 45, "RescueVehicle X after setPosition(int, int)");
    EXPECT_EQ(veh2.getPosition().getY(), 55, "RescueVehicle Y after setPosition(int, int)");

    return true;
}

// ============================================================================
// Test Suite Runner
// ============================================================================

int main() {
    std::cout << "========================================\n";
    std::cout << "   RescueGrid Comprehensive Unit Tests  \n";
    std::cout << "========================================\n";

    int passed = 0;
    int total = 13;

    // Phase 2 Core Tests
    if (testPositionCoordinates()) {
        std::cout << "  [PASS] testPositionCoordinates\n";
        passed++;
    }
    if (testIncidentConstructionAndValidation()) {
        std::cout << "  [PASS] testIncidentConstructionAndValidation\n";
        passed++;
    }
    if (testIncidentStatusUpdates()) {
        std::cout << "  [PASS] testIncidentStatusUpdates\n";
        passed++;
    }
    if (testResponderConstructionAndUpdates()) {
        std::cout << "  [PASS] testResponderConstructionAndUpdates\n";
        passed++;
    }
    if (testRescueVehicleConstructionAndUpdates()) {
        std::cout << "  [PASS] testRescueVehicleConstructionAndUpdates\n";
        passed++;
    }

    // Phase 3 Manager, Search, and Dispatch Tests
    if (testManagerRegistrationAndListing()) {
        std::cout << "  [PASS] testManagerRegistrationAndListing\n";
        passed++;
    }
    if (testManagerSearchAndDuplicateHandling()) {
        std::cout << "  [PASS] testManagerSearchAndDuplicateHandling\n";
        passed++;
    }
    if (testDispatchResourcesSuccess()) {
        std::cout << "  [PASS] testDispatchResourcesSuccess\n";
        passed++;
    }
    if (testDispatchResourcesUnavailableAndRejection()) {
        std::cout << "  [PASS] testDispatchResourcesUnavailableAndRejection\n";
        passed++;
    }
    if (testPreventDoubleAssignment()) {
        std::cout << "  [PASS] testPreventDoubleAssignment\n";
        passed++;
    }
    if (testStatusUpdateAndResourceRelease()) {
        std::cout << "  [PASS] testStatusUpdateAndResourceRelease\n";
        passed++;
    }
    if (testIncidentLifecycleAndInvalidTransitions()) {
        std::cout << "  [PASS] testIncidentLifecycleAndInvalidTransitions\n";
        passed++;
    }

    // Phase 4 Operator and Function Overloading Tests
    if (testPositionOperatorsAndOverloading()) {
        std::cout << "  [PASS] testPositionOperatorsAndOverloading\n";
        passed++;
    }

    std::cout << "----------------------------------------\n";
    std::cout << "Results: " << passed << "/" << total << " test suites passed.\n";
    std::cout << "========================================\n";

    return (passed == total) ? 0 : 1;
}
