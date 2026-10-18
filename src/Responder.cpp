#include "rescuegrid/Responder.h"

#include <iostream>
#include <stdexcept>

namespace rescuegrid {

Responder::Responder(const std::string& id,
                     const std::string& name,
                     ResponderSpecialization specialization,
                     const Position& position,
                     bool isAvailable)
    : m_id(id),
      m_name(name),
      m_specialization(specialization),
      m_position(position),
      m_isAvailable(isAvailable) {
    if (m_id.empty()) {
        throw std::invalid_argument("Responder ID cannot be empty.");
    }
    if (m_name.empty()) {
        throw std::invalid_argument("Responder name cannot be empty.");
    }
}

const std::string& Responder::getId() const {
    return m_id;
}

const std::string& Responder::getName() const {
    return m_name;
}

ResponderSpecialization Responder::getSpecialization() const {
    return m_specialization;
}

const Position& Responder::getPosition() const {
    return m_position;
}

bool Responder::isAvailable() const {
    return m_isAvailable;
}

void Responder::setPosition(const Position& newPosition) {
    m_position = newPosition;
}

void Responder::setAvailability(bool available) {
    m_isAvailable = available;
}

std::string Responder::getSpecializationString() const {
    switch (m_specialization) {
        case ResponderSpecialization::Firefighter:
            return "Firefighter";
        case ResponderSpecialization::Paramedic:
            return "Paramedic";
        case ResponderSpecialization::RescueSpecialist:
            return "RescueSpecialist";
        default:
            return "Unknown";
    }
}

std::string Responder::toString() const {
    return "Responder [ID: " + m_id +
           ", Name: " + m_name +
           ", Specialization: " + getSpecializationString() +
           ", Location: " + m_position.toString() +
           ", Available: " + (m_isAvailable ? "Yes" : "No") + "]";
}

void Responder::display() const {
    std::cout << toString() << "\n";
}

} // namespace rescuegrid
