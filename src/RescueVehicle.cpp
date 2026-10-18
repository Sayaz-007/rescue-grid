#include "rescuegrid/RescueVehicle.h"

#include <iostream>
#include <stdexcept>

namespace rescuegrid {

RescueVehicle::RescueVehicle(const std::string& id,
                             VehicleType type,
                             const Position& position,
                             bool isAvailable)
    : m_id(id),
      m_type(type),
      m_position(position),
      m_isAvailable(isAvailable) {
    if (m_id.empty()) {
        throw std::invalid_argument("Vehicle ID cannot be empty.");
    }
}

const std::string& RescueVehicle::getId() const {
    return m_id;
}

VehicleType RescueVehicle::getType() const {
    return m_type;
}

const Position& RescueVehicle::getPosition() const {
    return m_position;
}

bool RescueVehicle::isAvailable() const {
    return m_isAvailable;
}

void RescueVehicle::setPosition(const Position& newPosition) {
    m_position = newPosition;
}

void RescueVehicle::setPosition(int x, int y) {
    setPosition(Position(x, y));
}

void RescueVehicle::setAvailability(bool available) {
    m_isAvailable = available;
}

std::string RescueVehicle::getTypeString() const {
    switch (m_type) {
        case VehicleType::FireEngine:
            return "FireEngine";
        case VehicleType::Ambulance:
            return "Ambulance";
        case VehicleType::RescueVan:
            return "RescueVan";
        default:
            return "Unknown";
    }
}

std::string RescueVehicle::toString() const {
    return "RescueVehicle [ID: " + m_id +
           ", Type: " + getTypeString() +
           ", Location: " + m_position.toString() +
           ", Available: " + (m_isAvailable ? "Yes" : "No") + "]";
}

void RescueVehicle::display() const {
    std::cout << toString() << "\n";
}

} // namespace rescuegrid
