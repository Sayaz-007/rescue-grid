#ifndef RESCUEGRID_INCIDENT_H
#define RESCUEGRID_INCIDENT_H

#include"rescuegrid/Position.h"
#include<string>

namespace rescuegrid {
enum class IncidentType //enum(enum class is another version of enum) basically makes a custom data type(like int has 1,2..., the enum incidenttype creates a datatype with valid values fire,flood etc)
{ 
    Fire,
    Flood,
    StructuralCollapse
};

enum class IncidentStatus //enum for the current status of the incident
{ 
    Reported,
    InProgress,
    Resolved
};


//Represents an emergency event occurring at a location on the grid.
//Encapsulates the incident identifier, emergency type, validated severity
//rating (1 to 5), grid coordinates, and lifecycle status.
class Incident
{
    public:
        //constructor for incident class
        Incident(const std::string& id,IncidentType type,int severity,const Position& position,IncidentStatus status=IncidentStatus::Reported);
        
        //get functions
        const std::string& getId() const; 
        IncidentType getType() const;
        int getSeverity() const;
        const Position& getPosition() const;
        IncidentStatus getStatus() const;
        void setStatus(IncidentStatus newStatus);
        std::string getTypeString() const;
        std::string getStatusString() const;
        bool hasAssignedResources() const;
        const std::string& getAssignedResponderId() const;
        const std::string& getAssignedVehicleId() const;

        void assignResources(const std::string& responderId, const std::string& vehicleId);
        void releaseResources();

        //display functions
        std::string toString() const;
        void display() const;

    private:
        std::string m_id;
        IncidentType m_type;
        int m_severity;
        Position m_position;
        IncidentStatus m_status;
        std::string m_assignedResponderId;
        std::string m_assignedVehicleId;
};

}

#endif
