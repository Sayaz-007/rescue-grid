#ifndef RESCUEGRID_RESCUEMANAGER_H
#define RESCUEGRID_RESCUEMANAGER_H

#include "rescuegrid/Incident.h"
#include "rescuegrid/Responder.h"
#include "rescuegrid/RescueVehicle.h"

#include <vector>
#include <string>
#include <cstddef>

namespace rescuegrid
{
    //Coordinates emergency incidents, responders, and rescue vehicle fleets.
    //The RescueManager serves as the central control entity in RescueGrid.
    //It encapsulates the storage and lifecycle of incidents, responders, and
    //vehicles, and enforces deterministic resource dispatching and lifecycle
    //status synchronization.

    class RescueManager
    {
        public:
            // Default constructor initializing empty collections.
            RescueManager() = default;

            //Registration Methods

            void registerIncident(const Incident& incident); //registers an incident into the management system
            void registerResponder(const Responder& responder); //registers a responder 
            void registerVehicle(const RescueVehicle& vehicle); //registers a new vehicle

            //checks whether incident/responder/vehicle with given id is registered
            bool hasIncident(const std::string& id) const; 
            bool hasResponder(const std::string& id) const;
            bool hasVehicle(const std::string& id) const;

             //searches for an incident/responder/vehicle by their id and returns pointer if found, read only overloaded version for theconst version
            Incident* findIncident(const std::string& id);
            const Incident* findIncident(const std::string& id) const;
            Responder* findResponder(const std::string& id);
            const Responder* findResponder(const std::string& id) const;
            RescueVehicle* findVehicle(const std::string& id);
            const RescueVehicle* findVehicle(const std::string& id) const;

            //get functions
            const std::vector<Incident>& getIncidents() const;
            const std::vector<Responder>& getResponders() const;
            const std::vector<RescueVehicle>& getVehicles() const;
            std::size_t getIncidentCount() const;
            std::size_t getResponderCount() const;
            std::size_t getVehicleCount() const;
            std::size_t getAvailableResponderCount() const;
            std::size_t getAvailableVehicleCount() const;

            //Dispatch and Operational Logic
            bool dispatchResources(const std::string& incidentId);
            void updateIncidentStatus(const std::string& incidentId, IncidentStatus newStatus);

        private:
            std::vector<Incident> m_incidents;
            std::vector<Responder> m_responders;
            std::vector<RescueVehicle> m_vehicles;
    };

}

#endif
