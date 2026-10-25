#ifndef RESCUEGRID_MENU_H
#define RESCUEGRID_MENU_H

#include<string>
#include<limits>
#include "rescuegrid/RescueManager.h"
#include "rescuegrid/Position.h"

namespace rescuegrid
{
    bool readLine(std::string& outStr);
    bool readNonEmptyString(const std::string& prompt, std::string& outStr);
    bool readInt(const std::string& prompt,int& outVal,int minVal = std::numeric_limits<int>::min(),int maxVal =std::numeric_limits<int>::max());
    void handleRegisterIncident(RescueManager& manager);
    void handleListIncidents(const RescueManager& manager);
    void handleSearchIncident(const RescueManager& manager);
    void handleRegisterResponder(RescueManager& manager);
    void handleListResponders(const RescueManager& manager);
    void handleRegisterVehicle(RescueManager& manager);
    void handleListVehicles(const RescueManager& manager);
    void handleDispatch(RescueManager& manager);
    void handleUpdateIncidentStatus(RescueManager& manager);
    void seedInitialData(RescueManager& manager);
}

#endif