#ifndef RESCUEGRID_RESCUEMANAGER_H
#define RESCUEGRID_RESCUEMANAGER_H

#include "rescuegrid/Incident.h"
#include "rescuegrid/Responder.h"
#include "rescuegrid/RescueVehicle.h"

#include <vector>
#include <string>
#include <cstddef>

namespace rescuegrid {

/**
 * @brief Coordinates emergency incidents, responders, and rescue vehicle fleets.
 *
 * The RescueManager serves as the central control entity in RescueGrid.
 * It encapsulates the storage and lifecycle of incidents, responders, and
 * vehicles, and enforces deterministic resource dispatching and lifecycle
 * status synchronization.
 */
class RescueManager {
public:
    /**
     * @brief Default constructor initializing empty collections.
     */
    RescueManager() = default;

    // --- Registration Methods ---

    /**
     * @brief Registers a new incident into the management system.
     * @param incident The incident entity to register.
     * @throws std::invalid_argument if an incident with the same ID already exists.
     */
    void registerIncident(const Incident& incident);

    /**
     * @brief Registers a new responder into personnel records.
     * @param responder The responder entity to register.
     * @throws std::invalid_argument if a responder with the same ID already exists.
     */
    void registerResponder(const Responder& responder);

    /**
     * @brief Registers a new rescue vehicle into fleet records.
     * @param vehicle The rescue vehicle entity to register.
     * @throws std::invalid_argument if a vehicle with the same ID already exists.
     */
    void registerVehicle(const RescueVehicle& vehicle);

    // --- Search and Inspection Methods ---

    /**
     * @brief Checks whether an incident with the specified ID is registered.
     * @param id The incident identifier to query.
     * @return True if registered, false otherwise.
     */
    bool hasIncident(const std::string& id) const;

    /**
     * @brief Checks whether a responder with the specified ID is registered.
     * @param id The responder identifier to query.
     * @return True if registered, false otherwise.
     */
    bool hasResponder(const std::string& id) const;

    /**
     * @brief Checks whether a rescue vehicle with the specified ID is registered.
     * @param id The vehicle identifier to query.
     * @return True if registered, false otherwise.
     */
    bool hasVehicle(const std::string& id) const;

    /**
     * @brief Searches for an incident by ID (non-const version for internal updates).
     * @param id The incident identifier.
     * @return Pointer to the found Incident, or nullptr if not found.
     */
    Incident* findIncident(const std::string& id);

    /**
     * @brief Searches for an incident by ID (const version for read-only queries).
     * @param id The incident identifier.
     * @return Const pointer to the found Incident, or nullptr if not found.
     */
    const Incident* findIncident(const std::string& id) const;

    /**
     * @brief Searches for a responder by ID (non-const version).
     * @param id The responder identifier.
     * @return Pointer to the found Responder, or nullptr if not found.
     */
    Responder* findResponder(const std::string& id);

    /**
     * @brief Searches for a responder by ID (const version).
     * @param id The responder identifier.
     * @return Const pointer to the found Responder, or nullptr if not found.
     */
    const Responder* findResponder(const std::string& id) const;

    /**
     * @brief Searches for a rescue vehicle by ID (non-const version).
     * @param id The vehicle identifier.
     * @return Pointer to the found RescueVehicle, or nullptr if not found.
     */
    RescueVehicle* findVehicle(const std::string& id);

    /**
     * @brief Searches for a rescue vehicle by ID (const version).
     * @param id The vehicle identifier.
     * @return Const pointer to the found RescueVehicle, or nullptr if not found.
     */
    const RescueVehicle* findVehicle(const std::string& id) const;

    // --- Collection Accessors ---

    /**
     * @brief Gets read-only access to all registered incidents.
     * @return Const reference to the incident vector.
     */
    const std::vector<Incident>& getIncidents() const;

    /**
     * @brief Gets read-only access to all registered responders.
     * @return Const reference to the responder vector.
     */
    const std::vector<Responder>& getResponders() const;

    /**
     * @brief Gets read-only access to all registered rescue vehicles.
     * @return Const reference to the vehicle vector.
     */
    const std::vector<RescueVehicle>& getVehicles() const;

    // --- Dispatch and Operational Logic ---

    /**
     * @brief Dispatches the first available responder and vehicle to an incident.
     *
     * Validates that the incident exists, is eligible to receive resources, and that
     * both an available responder and rescue vehicle exist. Upon assignment:
     * - The assigned responder and vehicle are marked unavailable.
     * - Their positions are updated to the incident location.
     * - The incident records their IDs and changes status to InProgress.
     *
     * @param incidentId Identifier of the incident requesting dispatch.
     * @return True upon successful dispatch.
     * @throws std::invalid_argument if incidentId is not found.
     * @throws std::logic_error if the incident cannot receive resources.
     * @throws std::runtime_error if either responders or vehicles are unavailable.
     */
    bool dispatchResources(const std::string& incidentId);

    /**
     * @brief Updates the lifecycle status of an incident following strict lifecycle rules.
     *
     * Validates permitted lifecycle transitions:
     * - Reported -> Resolved: Permitted (e.g., false alarms or direct resolution).
     * - InProgress -> Resolved: Permitted; automatically releases assigned responder
     *   and vehicle back to the available pool.
     * - Reported -> InProgress: Prohibited via this method; dispatchResources() must be used.
     * - InProgress -> Reported: Prohibited to prevent leaving assigned resources stranded.
     * - Resolved -> Any: Prohibited; Resolved is a terminal status.
     *
     * @param incidentId Identifier of the incident.
     * @param newStatus The updated lifecycle status.
     * @throws std::invalid_argument if incidentId is not found.
     * @throws std::logic_error if the requested status transition is invalid.
     */
    void updateIncidentStatus(const std::string& incidentId, IncidentStatus newStatus);

    // --- Metrics and Statistics ---

    /**
     * @brief Gets the total count of registered incidents.
     */
    std::size_t getIncidentCount() const;

    /**
     * @brief Gets the total count of registered responders.
     */
    std::size_t getResponderCount() const;

    /**
     * @brief Gets the total count of registered rescue vehicles.
     */
    std::size_t getVehicleCount() const;

    /**
     * @brief Gets the number of currently available responders.
     */
    std::size_t getAvailableResponderCount() const;

    /**
     * @brief Gets the number of currently available rescue vehicles.
     */
    std::size_t getAvailableVehicleCount() const;

private:
    std::vector<Incident> m_incidents;
    std::vector<Responder> m_responders;
    std::vector<RescueVehicle> m_vehicles;
};

} // namespace rescuegrid

#endif // RESCUEGRID_RESCUEMANAGER_H
