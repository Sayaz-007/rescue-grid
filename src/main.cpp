#include "rescuegrid/Position.h"
#include "rescuegrid/Incident.h"
#include "rescuegrid/Responder.h"
#include "rescuegrid/RescueVehicle.h"

#include <iostream>
#include <stdexcept>

using namespace rescuegrid;

int main() {
    std::cout << "====================================================\n";
    std::cout << "                    RescueGrid                      \n";
    std::cout << "====================================================\n";
    std::cout << "Description : Disaster response and evacuation simulator\n";
    std::cout << "Phase       : Phase 2 - Core Classes and Encapsulation\n";
    std::cout << "Status      : System initialized successfully.\n";
    std::cout << "====================================================\n\n";

    // 1. Position Demonstration
    std::cout << "--- 1. Positioning Setup ---\n";
    Position commandCenter(10, 20);
    Position incidentLocation(45, 80);
    std::cout << "Command Center Location : " << commandCenter.toString() << "\n";
    std::cout << "Incident Location       : " << incidentLocation.toString() << "\n\n";

    // 2. Incident Demonstration
    std::cout << "--- 2. Incident Creation ---\n";
    Incident fireIncident("INC-001", IncidentType::Fire, 4, incidentLocation);
    fireIncident.display();
    std::cout << "\n";

    // 3. Responder Demonstration
    std::cout << "--- 3. Responder Personnel ---\n";
    Responder firefighter("RES-101", "Capt. Maya Lin", ResponderSpecialization::Firefighter, commandCenter);
    firefighter.display();
    std::cout << "\n";

    // 4. Rescue Vehicle Demonstration
    std::cout << "--- 4. Rescue Vehicle Fleet ---\n";
    RescueVehicle fireEngine("VEH-501", VehicleType::FireEngine, commandCenter);
    fireEngine.display();
    std::cout << "\n";

    // 5. Controlled State Updates (Dispatch Operation)
    std::cout << "--- 5. Controlled State and Availability Updates ---\n";
    std::cout << "Action: Dispatching responder and vehicle to INC-001...\n";

    // Update Incident status
    fireIncident.setStatus(IncidentStatus::InProgress);

    // Update Responder position & availability
    firefighter.setPosition(fireIncident.getPosition());
    firefighter.setAvailability(false);

    // Update Vehicle position & availability
    fireEngine.setPosition(fireIncident.getPosition());
    fireEngine.setAvailability(false);

    std::cout << "Post-Dispatch States:\n";
    fireIncident.display();
    firefighter.display();
    fireEngine.display();
    std::cout << "\n";

    std::cout << "Action: Resolving incident and returning units to base...\n";
    fireIncident.setStatus(IncidentStatus::Resolved);
    firefighter.setPosition(commandCenter);
    firefighter.setAvailability(true);
    fireEngine.setPosition(commandCenter);
    fireEngine.setAvailability(true);

    std::cout << "Post-Resolution States:\n";
    fireIncident.display();
    firefighter.display();
    fireEngine.display();
    std::cout << "\n";

    // 6. Graceful Handling of Invalid Input Exceptions
    std::cout << "--- 6. Input Validation & Exception Handling ---\n";

    // Case A: Invalid Severity (> 5)
    try {
        std::cout << "Attempting to create incident with invalid severity (9/5)...\n";
        Incident invalidIncident("INC-ERR", IncidentType::Flood, 9, incidentLocation);
        std::cout << "ERROR: Invalid incident was unexpectedly created!\n";
    } catch (const std::invalid_argument& ex) {
        std::cout << "Caught expected exception: " << ex.what() << "\n";
    }

    // Case B: Empty Responder Name
    try {
        std::cout << "Attempting to create responder with empty name...\n";
        Responder invalidResponder("RES-ERR", "", ResponderSpecialization::Paramedic, commandCenter);
        std::cout << "ERROR: Invalid responder was unexpectedly created!\n";
    } catch (const std::invalid_argument& ex) {
        std::cout << "Caught expected exception: " << ex.what() << "\n";
    }

    // Case C: Empty Vehicle ID
    try {
        std::cout << "Attempting to create vehicle with empty ID...\n";
        RescueVehicle invalidVehicle("", VehicleType::RescueVan, commandCenter);
        std::cout << "ERROR: Invalid vehicle was unexpectedly created!\n";
    } catch (const std::invalid_argument& ex) {
        std::cout << "Caught expected exception: " << ex.what() << "\n";
    }

    std::cout << "\n====================================================\n";
    std::cout << "Phase 2 demonstration completed successfully.\n";
    std::cout << "====================================================\n";

    return 0;
}
