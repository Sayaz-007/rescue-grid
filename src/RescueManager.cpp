#include"rescuegrid/RescueManager.h"
#include<stdexcept>

namespace rescuegrid
{

    void RescueManager::registerIncident(const Incident& incident)
    {
        if (hasIncident(incident.getId()))
            throw std::invalid_argument("Incident with ID <"+incident.getId() +"> already exists.");
        m_incidents.push_back(incident);
    }

    void RescueManager::registerResponder(const Responder& responder)
    {
        if (hasResponder(responder.getId()))
            throw std::invalid_argument("Responder with ID <"+responder.getId()+"> already exists.");
        m_responders.push_back(responder);
    }

    void RescueManager::registerVehicle(const RescueVehicle& vehicle)
    {
        if (hasVehicle(vehicle.getId()))
            throw std::invalid_argument("Vehicle with ID <"+vehicle.getId()+"> already exists.");
        m_vehicles.push_back(vehicle);
    }

    bool RescueManager::hasIncident(const std::string& id) const
    {
        return findIncident(id)!=nullptr;
    }

    bool RescueManager::hasResponder(const std::string& id) const
    {
        return findResponder(id)!=nullptr;
    }

    bool RescueManager::hasVehicle(const std::string& id) const
    {
        return findVehicle(id)!=nullptr;
    }

    Incident* RescueManager::findIncident(const std::string& id)
    {
        for(auto& incident : m_incidents)
        {
            if (incident.getId()==id)
            return &incident;
        }
        return nullptr;
    }

    const Incident* RescueManager::findIncident(const std::string& id) const
    {
        for(const auto& incident:m_incidents)
        {
            if (incident.getId()==id)
            return &incident;
        }
        return nullptr;
    }

    Responder* RescueManager::findResponder(const std::string& id)
    {
        for(auto& responder:m_responders)
        {
            if(responder.getId()==id)
            return &responder;
        }
        return nullptr;
    }

    const Responder* RescueManager::findResponder(const std::string& id) const
    {
        for(const auto& responder:m_responders)
        {
            if (responder.getId()==id)
            return &responder;
        }
        return nullptr;
    }

    RescueVehicle* RescueManager::findVehicle(const std::string& id)
    {
        for(auto& vehicle:m_vehicles)
        {
            if (vehicle.getId()==id)
            return &vehicle;
        }
        return nullptr;
    }

    const RescueVehicle* RescueManager::findVehicle(const std::string& id) const
    {
        for(const auto& vehicle : m_vehicles)
        {
            if (vehicle.getId()==id)
            return &vehicle;
        }
        return nullptr;
    }

    const std::vector<Incident>& RescueManager::getIncidents() const
    {
        return m_incidents;
    }

    const std::vector<Responder>& RescueManager::getResponders() const
    {
        return m_responders;
    }

    const std::vector<RescueVehicle>& RescueManager::getVehicles() const
    {
        return m_vehicles;
    }

    bool RescueManager::dispatchResources(const std::string& incidentId)
    {
        Incident* inc=findIncident(incidentId);
        if (!inc)
        {
            throw std::invalid_argument("Incident with ID <"+incidentId+"> does not exist");
        }

        if (inc->getStatus()==IncidentStatus::Resolved)
        {
            throw std::logic_error("Incident <"+incidentId+"> is already resolved and cannot receive resources");
        }

        if (inc->getStatus()==IncidentStatus::InProgress||inc->hasAssignedResources())
        {
            throw std::logic_error("Incident <"+incidentId+"> already has active resources assigned");
        }

        //select the first available responder
        Responder* availableResp=nullptr;
        for (auto& resp:m_responders)
        {
            if (resp.isAvailable()) {
                availableResp=&resp;
                break;
            }
        }
        if (!availableResp)
        {
            throw std::runtime_error("Dispatch failed: No rescue vehicles available :(");
        }

        //select the first available rescue vehicle
        RescueVehicle* availableVeh=nullptr;
        for (auto& veh:m_vehicles)
        {
            if(veh.isAvailable())
            {
                availableVeh=&veh;
                break;
            }
        }
        if (!availableVeh) {
            throw std::runtime_error("Dispatch failed: No rescue vehicles available :(");
        }

        //mark resources unavailable
        availableResp->setAvailability(false);
        availableVeh->setAvailability(false);

        //update their positions to the incident location
        availableResp->setPosition(inc->getPosition());
        availableVeh->setPosition(inc->getPosition());

        //assign to incident and transition status
        inc->assignResources(availableResp->getId(), availableVeh->getId());
        inc->setStatus(IncidentStatus::InProgress);

        return true;
    }

    void RescueManager::updateIncidentStatus(const std::string& incidentId, IncidentStatus newStatus)
    {
        Incident* inc=findIncident(incidentId);
        if(!inc)
            throw std::invalid_argument("Incident with ID <"+incidentId+"> does not exist");

        IncidentStatus currentStatus=inc->getStatus();

        if(currentStatus==IncidentStatus::Resolved)
            throw std::logic_error("Resolved incident <"+incidentId+"> cannot transition to another status.");

        if(currentStatus==IncidentStatus::Reported)
        {
            if(newStatus==IncidentStatus::InProgress)
                throw std::logic_error("Incident <"+incidentId+"> cannot transition directly from Reported to InProgress; use dispatchResources() to assign resources.");
            if(newStatus==IncidentStatus::Reported)
                throw std::logic_error("Incident <"+incidentId+"> is already in Reported status.");
            if(newStatus == IncidentStatus::Resolved){
                // Valid transition: directly resolving a reported incident (e.g., false alarm)
                inc->setStatus(IncidentStatus::Resolved);
                return;
            }
        }

        if(currentStatus==IncidentStatus::InProgress)
        {
            if(newStatus==IncidentStatus::Reported)
            {
                throw std::logic_error("Active incident <"+incidentId+ "> is already in progress and cannot be changed to reported!");
            }
            if(newStatus==IncidentStatus::InProgress) {
                throw std::logic_error("Incident <"+incidentId+"> is already in progress");
            }
            if(newStatus==IncidentStatus::Resolved)
            {
                if(inc->hasAssignedResources())
                {
                    Responder* resp=findResponder(inc->getAssignedResponderId());
                    if(resp)
                    {
                        resp->setAvailability(true);
                    }
                    RescueVehicle* veh=findVehicle(inc->getAssignedVehicleId());
                    if(veh)
                    {
                        veh->setAvailability(true);
                    }
                    inc->releaseResources();
                }
                inc->setStatus(IncidentStatus::Resolved);
                return;
            }
        }

        throw std::logic_error("Invalid status transition requested for incident <"+incidentId+">");
    }

    std::size_t RescueManager::getIncidentCount() const
    {
        return m_incidents.size();
    }

    std::size_t RescueManager::getResponderCount() const
    {
        return m_responders.size();
    }

    std::size_t RescueManager::getVehicleCount() const
    {
        return m_vehicles.size();
    }

    std::size_t RescueManager::getAvailableResponderCount() const
    {
        std::size_t count=0;
        for(const auto& resp:m_responders)
        {
            if(resp.isAvailable())
                ++count;
        }
        return count;
    }

    std::size_t RescueManager::getAvailableVehicleCount() const
    {
        std::size_t count=0;
        for(const auto& veh:m_vehicles)
        {
            if(veh.isAvailable())
            ++count;
        }
        return count;
    }

}
