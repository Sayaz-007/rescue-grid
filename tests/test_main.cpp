#include "rescuegrid/Position.h"
#include "rescuegrid/Incident.h"
#include "rescuegrid/Responder.h"
#include "rescuegrid/RescueVehicle.h"

#include <iostream>
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

int main() {
    std::cout << "========================================\n";
    std::cout << "    RescueGrid Core Classes Unit Tests  \n";
    std::cout << "========================================\n";

    int passed = 0;
    int total = 5;

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

    std::cout << "----------------------------------------\n";
    std::cout << "Results: " << passed << "/" << total << " test suites passed.\n";
    std::cout << "========================================\n";

    return (passed == total) ? 0 : 1;
}
