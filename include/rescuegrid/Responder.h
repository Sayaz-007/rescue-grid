#ifndef RESCUEGRID_RESPONDER_H
#define RESCUEGRID_RESPONDER_H

#include "rescuegrid/Position.h"

#include <string>

namespace rescuegrid {

/**
 * @brief Professional specialization of emergency response personnel.
 */
enum class ResponderSpecialization {
    Firefighter,
    Paramedic,
    RescueSpecialist
};

/**
 * @brief Represents an individual emergency responder operating in the grid.
 *
 * Encapsulates responder identification, personnel name, specialization,
 * current geographic coordinates, and operational availability status.
 *
 * Designed as a concrete domain entity with standard virtual destruction,
 * allowing seamless transition into an abstract inheritance hierarchy in
 * future development phases.
 */
class Responder {
public:
    /**
     * @brief Constructs and validates an emergency Responder.
     * @param id Unique identification code for the responder (cannot be empty).
     * @param name Full name of the responder (cannot be empty).
     * @param specialization The domain expertise of the responder.
     * @param position Initial position on the grid.
     * @param isAvailable Operational availability flag (defaults to true).
     * @throws std::invalid_argument if id or name is empty.
     */
    Responder(const std::string& id,
              const std::string& name,
              ResponderSpecialization specialization,
              const Position& position,
              bool isAvailable = true);

    /**
     * @brief Virtual destructor to support future polymorphic hierarchies.
     */
    virtual ~Responder() = default;

    /**
     * @brief Gets the responder identifier.
     * @return Reference to the ID string.
     */
    const std::string& getId() const;

    /**
     * @brief Gets the responder name.
     * @return Reference to the name string.
     */
    const std::string& getName() const;

    /**
     * @brief Gets the responder specialization.
     * @return ResponderSpecialization enum value.
     */
    ResponderSpecialization getSpecialization() const;

    /**
     * @brief Gets the current position of the responder.
     * @return Reference to the Position object.
     */
    const Position& getPosition() const;

    /**
     * @brief Checks if the responder is currently available for dispatch.
     * @return True if available, false if busy or dispatched.
     */
    bool isAvailable() const;

    /**
     * @brief Controlled method to update the responder's grid coordinates.
     * @param newPosition The new position coordinates.
     */
    void setPosition(const Position& newPosition);

    /**
     * @brief Controlled method to update the responder's availability.
     * @param available New availability flag.
     */
    void setAvailability(bool available);

    /**
     * @brief Converts the responder specialization to a readable string.
     * @return String representation of ResponderSpecialization.
     */
    std::string getSpecializationString() const;

    /**
     * @brief Formats responder details as a readable string.
     * @return Formatted multi-property string.
     */
    std::string toString() const;

    /**
     * @brief Prints responder details to standard output.
     */
    void display() const;

private:
    std::string m_id;
    std::string m_name;
    ResponderSpecialization m_specialization;
    Position m_position;
    bool m_isAvailable;
};

} // namespace rescuegrid

#endif // RESCUEGRID_RESPONDER_H
