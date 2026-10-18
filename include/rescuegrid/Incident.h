#ifndef RESCUEGRID_INCIDENT_H
#define RESCUEGRID_INCIDENT_H

#include "rescuegrid/Position.h"

#include <string>

namespace rescuegrid {

/**
 * @brief Categorization of disaster events within the simulator.
 */
enum class IncidentType {
    Fire,
    Flood,
    StructuralCollapse
};

/**
 * @brief Lifecycle status of an incident.
 */
enum class IncidentStatus {
    Reported,
    InProgress,
    Resolved
};

/**
 * @brief Represents an emergency event occurring at a location on the grid.
 *
 * Encapsulates the incident identifier, emergency type, validated severity
 * rating (1 to 5), grid coordinates, and lifecycle status.
 */
class Incident {
public:
    /**
     * @brief Constructs and validates a new Incident.
     * @param id Unique identifier for the incident (cannot be empty).
     * @param type The category of emergency event.
     * @param severity Emergency severity on a scale of 1 (minor) to 5 (catastrophic).
     * @param position Grid location where the incident occurred.
     * @param status Initial lifecycle status (defaults to Reported).
     * @throws std::invalid_argument if id is empty or severity is outside [1, 5].
     */
    Incident(const std::string& id,
             IncidentType type,
             int severity,
             const Position& position,
             IncidentStatus status = IncidentStatus::Reported);

    /**
     * @brief Gets the incident identifier.
     * @return Reference to the ID string.
     */
    const std::string& getId() const;

    /**
     * @brief Gets the emergency type.
     * @return IncidentType enum value.
     */
    IncidentType getType() const;

    /**
     * @brief Gets the incident severity rating.
     * @return Severity integer between 1 and 5.
     */
    int getSeverity() const;

    /**
     * @brief Gets the location of the incident.
     * @return Reference to the Position object.
     */
    const Position& getPosition() const;

    /**
     * @brief Gets the current lifecycle status.
     * @return IncidentStatus enum value.
     */
    IncidentStatus getStatus() const;

    /**
     * @brief Controlled update of the incident lifecycle status.
     * @param newStatus The updated lifecycle status.
     */
    void setStatus(IncidentStatus newStatus);

    /**
     * @brief Converts the incident type to a readable string.
     * @return String representation of IncidentType.
     */
    std::string getTypeString() const;

    /**
     * @brief Converts the incident status to a readable string.
     * @return String representation of IncidentStatus.
     */
    std::string getStatusString() const;

    /**
     * @brief Formats full incident details as a readable string.
     * @return Formatted multi-property string.
     */
    std::string toString() const;

    /**
     * @brief Prints incident details to standard output.
     */
    void display() const;

private:
    std::string m_id;
    IncidentType m_type;
    int m_severity;
    Position m_position;
    IncidentStatus m_status;
};

} // namespace rescuegrid

#endif // RESCUEGRID_INCIDENT_H
