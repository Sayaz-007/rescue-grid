#include "rescuegrid/Position.h"
#include "rescuegrid/Incident.h"
#include "rescuegrid/Responder.h"
#include "rescuegrid/RescueVehicle.h"
#include "rescuegrid/RescueManager.h"
#include "rescuegrid/menu.h"

#include <iostream>
#include <string>
#include <sstream>
#include <limits>
#include <stdexcept>

// ============================================================================
// Safe Input Helper Functions
// ============================================================================

namespace rescuegrid
{

/**
 * @brief Reads a trimmed line of text from standard input.
 * @param outStr Destination string.
 * @return True if read succeeded, false on EOF or stream failure.
 */
bool readLine(std::string& outStr) {
    if (!std::getline(std::cin, outStr)) {
        return false;
    }
    // Trim leading whitespace
    size_t start = outStr.find_first_not_of(" \t\r\n");
    if (start == std::string::npos) {
        outStr.clear();
        return true;
    }
    // Trim trailing whitespace
    size_t end = outStr.find_last_not_of(" \t\r\n");
    outStr = outStr.substr(start, end - start + 1);
    return true;
}

/**
 * @brief Prompts repeatedly until a non-empty string is provided.
 * @param prompt Prompt message displayed to the user.
 * @param outStr Destination string.
 * @return True if a valid string was read, false on EOF.
 */
bool readNonEmptyString(const std::string& prompt, std::string& outStr) {
    while (true) {
        std::cout<<prompt;
        if (!readLine(outStr)) {
            return false;
        }
        if (!outStr.empty()) {
            return true;
        }
        std::cout<<"  [!] Input cannot be blank. Please try again.\n";
    }
}

/**
 * @brief Prompts repeatedly until a valid integer within [minVal, maxVal] is entered.
 * @param prompt Prompt message displayed to the user.
 * @param outVal Destination integer.
 * @param minVal Minimum acceptable value.
 * @param maxVal Maximum acceptable value.
 * @return True if a valid integer was read, false on EOF.
 */
bool readInt(const std::string& prompt,int& outVal,int minVal = std::numeric_limits<int>::min(),int maxVal = std::numeric_limits<int>::max())
{
    while (true) {
        std::cout<<prompt;
        std::string line;
        if (!readLine(line)) {
            return false;
        }

        if (line.empty()) {
            std::cout<<"  [!] Input cannot be empty. Please enter a valid number.\n";
            continue;
        }

        std::istringstream iss(line);
        int parsed = 0;
        char extra = '\0';
        if ((iss >> parsed) && !(iss >> extra)) {
            if (parsed >= minVal && parsed <= maxVal) {
                outVal = parsed;
                return true;
            }
            std::cout<<"  [!] Value must be between "<<minVal<<" and "<<maxVal<<". Please try again.\n";
        } else {
            std::cout<<"  [!] Invalid numeric format. Please enter an integer.\n";
        }
    }
}


// ============================================================================
// Menu Action Handlers
// ============================================================================

void handleRegisterIncident(RescueManager& manager)
{
    std::cout<<"\n--- Register New Incident ---\n";
    std::string id;
    if (!readNonEmptyString("Enter Incident ID (e.g., INC-101): ", id)) return;

    if (manager.hasIncident(id)) {
        std::cout<<"  [!] An incident with ID '"<<id<<"' already exists.\n";
        return;
    }

    std::cout<<"Select Incident Type:\n";
    std::cout<<"  1. Fire\n";
    std::cout<<"  2. Flood\n";
    std::cout<<"  3. Structural Collapse\n";
    int typeChoice = 0;
    if (!readInt("Enter choice (1-3): ", typeChoice, 1, 3)) return;

    IncidentType type = IncidentType::Fire;
    if (typeChoice == 2) type = IncidentType::Flood;
    else if (typeChoice == 3) type = IncidentType::StructuralCollapse;

    int severity = 0;
    if (!readInt("Enter Severity rating (1 to 5): ", severity, 1, 5)) return;

    int x = 0;
    int y = 0;
    if (!readInt("Enter Grid Coordinate X: ", x)) return;
    if (!readInt("Enter Grid Coordinate Y: ", y)) return;

    try {
        Incident incident(id, type, severity, Position(x, y));
        manager.registerIncident(incident);
        std::cout<<"  [+] Incident registered successfully: "<<incident.toString()<<"\n";
    } catch (const std::exception& ex) {
        std::cout<<"  [!] Error registering incident: "<<ex.what()<<"\n";
    }
}

void handleListIncidents(const RescueManager& manager)
{
    std::cout<<"\n--- Registered Incidents ("<<manager.getIncidentCount()<<") ---\n";
    const auto& incidents = manager.getIncidents();
    if (incidents.empty()) {
        std::cout<<"  No incidents currently registered.\n";
        return;
    }
    for (size_t i = 0; i < incidents.size(); ++i) {
        std::cout<<"  "<<(i + 1)<<". "<<incidents[i].toString()<<"\n";
    }
}

void handleSearchIncident(const RescueManager& manager)
{
    std::cout<<"\n--- Search Incident by ID ---\n";
    std::string id;
    if (!readNonEmptyString("Enter Incident ID to search: ", id)) return;

    const Incident* incident = manager.findIncident(id);
    if (incident) {
        std::cout<<"  [+] Found: "<<incident->toString()<<"\n";
        std::cout<<"      Grid Location: "<<incident->getPosition()<<"\n";
    } else {
        std::cout<<"  [-] No incident found with ID '"<<id<<"'.\n";
    }
}

void handleRegisterResponder(RescueManager& manager)
{
    std::cout<<"\n--- Register New Responder ---\n";
    std::string id;
    if (!readNonEmptyString("Enter Responder ID (e.g., RES-01): ", id)) return;

    if (manager.hasResponder(id)) {
        std::cout<<"  [!] A responder with ID '"<<id<<"' already exists.\n";
        return;
    }

    std::string name;
    if (!readNonEmptyString("Enter Responder Full Name: ", name)) return;

    std::cout<<"Select Specialization:\n";
    std::cout<<"  1. Firefighter\n";
    std::cout<<"  2. Paramedic\n";
    std::cout<<"  3. Rescue Specialist\n";
    int specChoice = 0;
    if (!readInt("Enter choice (1-3): ", specChoice, 1, 3)) return;

    ResponderSpecialization spec = ResponderSpecialization::Firefighter;
    if (specChoice == 2) spec = ResponderSpecialization::Paramedic;
    else if (specChoice == 3) spec = ResponderSpecialization::RescueSpecialist;

    int x = 0;
    int y = 0;
    if (!readInt("Enter Initial Station Coordinate X: ", x)) return;
    if (!readInt("Enter Initial Station Coordinate Y: ", y)) return;

    try {
        Responder responder(id, name, spec, Position(x, y));
        manager.registerResponder(responder);
        std::cout<<"  [+] Responder registered successfully: "<<responder.toString()<<"\n";
    } catch (const std::exception& ex) {
        std::cout<<"  [!] Error registering responder: "<<ex.what()<<"\n";
    }
}

void handleListResponders(const RescueManager& manager)
{
    std::cout<<"\n--- Registered Responders ("<<manager.getResponderCount()
             <<" total, "<<manager.getAvailableResponderCount()<<" available) ---\n";
    const auto& responders = manager.getResponders();
    if (responders.empty()) {
        std::cout<<"  No responders currently registered.\n";
        return;
    }
    for (size_t i = 0; i < responders.size(); ++i) {
        std::cout<<"  "<<(i + 1)<<". "<<responders[i].toString()<<"\n";
    }
}

void handleRegisterVehicle(RescueManager& manager)
{
    std::cout<<"\n--- Register New Rescue Vehicle ---\n";
    std::string id;
    if (!readNonEmptyString("Enter Vehicle ID (e.g., VEH-01): ", id)) return;

    if (manager.hasVehicle(id)) {
        std::cout<<"  [!] A vehicle with ID '"<<id<<"' already exists.\n";
        return;
    }

    std::cout<<"Select Vehicle Type:\n";
    std::cout<<"  1. Fire Engine\n";
    std::cout<<"  2. Ambulance\n";
    std::cout<<"  3. Rescue Van\n";
    int typeChoice = 0;
    if (!readInt("Enter choice (1-3): ", typeChoice, 1, 3)) return;

    VehicleType type = VehicleType::FireEngine;
    if (typeChoice == 2) type = VehicleType::Ambulance;
    else if (typeChoice == 3) type = VehicleType::RescueVan;

    int x = 0;
    int y = 0;
    if (!readInt("Enter Initial Station Coordinate X: ", x)) return;
    if (!readInt("Enter Initial Station Coordinate Y: ", y)) return;

    try {
        RescueVehicle vehicle(id, type, Position(x, y));
        manager.registerVehicle(vehicle);
        std::cout<<"  [+] Rescue vehicle registered successfully: "<<vehicle.toString()<<"\n";
    } catch (const std::exception& ex) {
        std::cout<<"  [!] Error registering vehicle: "<<ex.what()<<"\n";
    }
}

void handleListVehicles(const RescueManager& manager)
{
    std::cout<<"\n--- Registered Vehicles ("<<manager.getVehicleCount()
             <<" total, "<<manager.getAvailableVehicleCount()<<" available) ---\n";
    const auto& vehicles = manager.getVehicles();
    if (vehicles.empty()) {
        std::cout<<"  No vehicles currently registered.\n";
        return;
    }
    for (size_t i = 0; i < vehicles.size(); ++i) {
        std::cout<<"  "<<(i + 1)<<". "<<vehicles[i].toString()<<"\n";
    }
}

void handleDispatch(RescueManager& manager)
{
    std::cout<<"\n--- Dispatch Resources to Incident ---\n";
    std::string id;
    if (!readNonEmptyString("Enter Incident ID to receive dispatch: ", id)) return;

    try {
        manager.dispatchResources(id);
        const Incident* inc = manager.findIncident(id);
        std::cout<<"  [+] Dispatch successful!\n";
        if (inc) {
            std::cout<<"      "<<inc->toString()<<"\n";
            std::cout<<"      Dispatched to scene at: "<<inc->getPosition()<<"\n";
        }
    } catch (const std::exception& ex) {
        std::cout<<"  [-] Dispatch rejected: "<<ex.what()<<"\n";
    }
}

void handleUpdateIncidentStatus(RescueManager& manager)
{
    std::cout<<"\n--- Update Incident Status ---\n";
    std::string id;
    if (!readNonEmptyString("Enter Incident ID: ", id)) return;

    Incident* inc = manager.findIncident(id);
    if (!inc) {
        std::cout<<"  [-] Incident '"<<id<<"' does not exist.\n";
        return;
    }

    std::cout<<"Current Incident State: "<<inc->toString()<<"\n";
    std::cout<<"Select New Status:\n";
    std::cout<<"  1. Reported\n";
    std::cout<<"  2. InProgress\n";
    std::cout<<"  3. Resolved\n";
    int statusChoice = 0;
    if (!readInt("Enter choice (1-3): ", statusChoice, 1, 3)) return;

    IncidentStatus newStatus = IncidentStatus::Reported;
    if (statusChoice == 2) newStatus = IncidentStatus::InProgress;
    else if (statusChoice == 3) newStatus = IncidentStatus::Resolved;

    try {
        manager.updateIncidentStatus(id, newStatus);
        std::cout<<"  [+] Incident status updated successfully.\n";
        std::cout<<"      "<<inc->toString()<<"\n";
        if (newStatus == IncidentStatus::Resolved) {
            std::cout<<"      Note: Assigned resources have been released back to the available pool.\n";
        }
    } catch (const std::exception& ex) {
        std::cout<<"  [!] Failed to update status: "<<ex.what()<<"\n";
    }
}

/**
 * @brief Seeds the manager with realistic initial entities for convenient demonstration.
 */
void seedInitialData(RescueManager& manager)
{
    // Initial sample incidents
    manager.registerIncident(Incident("INC-101", IncidentType::Fire, 4, Position(15, 25)));
    manager.registerIncident(Incident("INC-102", IncidentType::Flood, 2, Position(40, 60)));

    // Initial sample responders
    manager.registerResponder(Responder("RES-01", "Capt. Aamir", ResponderSpecialization::Firefighter, Position(0, 0)));
    manager.registerResponder(Responder("RES-02", "Lt. Madhuchan", ResponderSpecialization::Paramedic, Position(0, 0)));

    // Initial sample vehicles
    manager.registerVehicle(RescueVehicle("VEH-01", VehicleType::FireEngine, Position(0, 0)));
    manager.registerVehicle(RescueVehicle("VEH-02", VehicleType::Ambulance, Position(0, 0)));
}
}
