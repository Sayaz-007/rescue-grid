#ifndef RESCUEGRID_RESCUEVEHICLE_H
#define RESCUEGRID_RESCUEVEHICLE_H

#include "rescuegrid/Position.h"

#include <string>

namespace rescuegrid {

/**
 * @brief Categorization of emergency rescue vehicles.
 */
enum class VehicleType {
    FireEngine,
    Ambulance,
    RescueVan
};

/**
 * @brief Represents a specialized rescue vehicle operating on the grid.
 *
 * Encapsulates the vehicle identifier, vehicular classification,
 * current coordinates, and operational deployment availability.
 */
class RescueVehicle {
public:
    /**
     * @brief Constructs and validates a RescueVehicle.
     * @param id Unique identification code for the vehicle (cannot be empty).
     * @param type Vehicle classification.
     * @param position Initial position on the grid.
     * @param isAvailable Operational availability flag (defaults to true).
     * @throws std::invalid_argument if id is empty.
     */
    RescueVehicle(const std::string& id,
                  VehicleType type,
                  const Position& position,
                  bool isAvailable = true);

    /**
     * @brief Gets the vehicle identifier.
     * @return Reference to the ID string.
     */
    const std::string& getId() const;

    /**
     * @brief Gets the vehicle type.
     * @return VehicleType enum value.
     */
    VehicleType getType() const;

    /**
     * @brief Gets the current location of the vehicle.
     * @return Reference to the Position object.
     */
    const Position& getPosition() const;

    /**
     * @brief Checks if the vehicle is available for dispatch.
     * @return True if available, false if in service.
     */
    bool isAvailable() const;

    /**
     * @brief Controlled method to update the vehicle's position.
     * @param newPosition The updated coordinates.
     */
    void setPosition(const Position& newPosition);

    /**
     * @brief Controlled method to update vehicle availability.
     * @param available Updated availability status.
     */
    void setAvailability(bool available);

    /**
     * @brief Converts the vehicle type to a readable string.
     * @return String representation of VehicleType.
     */
    std::string getTypeString() const;

    /**
     * @brief Formats vehicle details as a readable string.
     * @return Formatted multi-property string.
     */
    std::string toString() const;

    /**
     * @brief Prints vehicle details to standard output.
     */
    void display() const;

private:
    std::string m_id;
    VehicleType m_type;
    Position m_position;
    bool m_isAvailable;
};

} // namespace rescuegrid

#endif // RESCUEGRID_RESCUEVEHICLE_H
