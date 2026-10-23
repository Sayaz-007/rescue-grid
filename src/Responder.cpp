#include "rescuegrid/Responder.h"
#include <iostream>
#include <stdexcept> //needed for using throw

namespace rescuegrid{  //we dont have to type rescuegrid:: everytime
//constructor
Responder::Responder(const std::string& id,const std::string& name,ResponderSpecialization specialization,const Position& position,bool isAvailable): m_id(id),m_name(name),m_specialization(specialization),m_position(position),m_isAvailable(isAvailable)
{
    if (m_id.empty())
    throw std::invalid_argument("responder ID cannot be empty");
    if (m_name.empty())
    throw std::invalid_argument("responder name cannot be empty");
}
//get functions to get the value of private members
const std::string& Responder::getId() const 
{
    return m_id;
}

const std::string& Responder::getName() const
{
    return m_name;
}

ResponderSpecialization Responder::getSpecialization() const
{
    return m_specialization;
}

const Position& Responder::getPosition() const //m_position is an object of the class position
{
    return m_position; //returns reference to the object
}

bool Responder::isAvailable() const
{
    return m_isAvailable;
}
//set functions to change teh value of priavte data members
void Responder::setPosition(const Position& newPosition)
{
    m_position=newPosition;
}

void Responder::setPosition(int x, int y)
{
    setPosition(Position(x, y));
}

void Responder::setAvailability(bool available)
{
    m_isAvailable=available;
}

std::string Responder::getSpecializationString() const //this is used for the ifnal 
{
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

std::string Responder::toString() const
{
    return "RESPONDER [ID: "+m_id+", Name: "+m_name+", Specialization: "+getSpecializationString()+", Location: "+m_position.toString()+", Available: "+(m_isAvailable?"Yes":"No")+"]";
}

void Responder::display() const
{
    std::cout << toString() << "\n";
}

}
