#include "rescuegrid/Incident.h"
#include <iostream>
#include <stdexcept>

//function definitions for all the functions in the incident.h file
namespace rescuegrid
{
    Incident::Incident(const std::string& id,IncidentType type,int severity,const Position& position,IncidentStatus status):m_id(id),m_type(type),m_severity(severity),m_position(position),m_status(status),m_assignedResponderId(""),m_assignedVehicleId("")
    {
        if(m_id.empty()){
            throw std::invalid_argument("Incident ID cannot be empty");
        }
        if(m_severity<1||m_severity>5){
            throw std::invalid_argument("Severity must be between 1 and 5(inclusive).");
        }
    }

    const std::string& Incident::getId() const
    {
        return m_id;
    }

    IncidentType Incident::getType() const
    {
        return m_type;
    }

    int Incident::getSeverity() const
    {
        return m_severity;
    }

    const Position& Incident::getPosition() const
    {
        return m_position;
    }

    IncidentStatus Incident::getStatus() const
    {
        return m_status;
    }

    void Incident::setStatus(IncidentStatus newStatus)
    {
        m_status = newStatus;
    }

    std::string Incident::getTypeString() const
    {
        switch(m_type){
            case IncidentType::Fire:
                return "Fire";
            case IncidentType::Flood:
                return "Flood";
            case IncidentType::StructuralCollapse:
                return "StructuralCollapse";
            default:
                return "Unknown";
        }
    }

    std::string Incident::getStatusString() const
    {
        switch(m_status){
            case IncidentStatus::Reported:
                return "Reported";
            case IncidentStatus::InProgress:
                return "InProgress";
            case IncidentStatus::Resolved:
                return "Resolved";
            default:
                return "Unknown";
        }
    }

    bool Incident::hasAssignedResources() const
    {
        return !m_assignedResponderId.empty() && !m_assignedVehicleId.empty();
    }

    const std::string& Incident::getAssignedResponderId() const
    {
        return m_assignedResponderId;
    }

    const std::string& Incident::getAssignedVehicleId() const
    {
        return m_assignedVehicleId;
    }

    void Incident::assignResources(const std::string& responderId, const std::string& vehicleId)
    {
        m_assignedResponderId=responderId;
        m_assignedVehicleId=vehicleId;
    }

    void Incident::releaseResources()
    {
        m_assignedResponderId.clear();
        m_assignedVehicleId.clear();
    }

    std::string Incident::toString() const
    {
        std::string result = "Incident [ID: "+m_id+
            ", Type: "+getTypeString()+
            ", Severity: "+std::to_string(m_severity)+"/5"+
            ", Location: "+m_position.toString()+
            ", Status: "+getStatusString();
        if(hasAssignedResources()){
            result+=", Assigned: (Responder: "+m_assignedResponderId+
                    ", Vehicle: "+m_assignedVehicleId +")";
        }
        result+="]";
        return result;
    }

    void Incident::display() const
    {
        std::cout<<toString()<<"\n";
    }

}
