#include "rescuegrid/Position.h"
#include "rescuegrid/Incident.h"
#include "rescuegrid/Responder.h"
#include "rescuegrid/RescueVehicle.h"
#include "rescuegrid/RescueManager.h"
#include "rescuegrid/menu.h"
#include <iostream>
#include <string>
#include <sstream>
#include <limits>
#include <stdexcept>

using namespace rescuegrid;
int main() 
{
    std::cout<<"====================================================\n";
    std::cout<<"                    RescueGrid                      \n";
    std::cout<<"====================================================\n";
    std::cout<<"Description : Disaster response and evacuation simulator\n";
    std::cout<<"Phase       : Phase 4 - Mid-Semester OOP Demonstration\n";
    std::cout<<"Status      : System initialized successfully.\n";
    std::cout<<"====================================================\n";

    RescueManager manager;
    seedInitialData(manager);
    std::cout<<"Preloaded demonstration data:\n";
    std::cout<<"  - 2 Incidents  (INC-101, INC-102)\n";
    std::cout<<"  - 2 Responders (RES-01, RES-02)\n";
    std::cout<<"  - 2 Vehicles   (VEH-01, VEH-02)\n";

    bool running = true;
    while (running){
        std::cout<<"\n----------------------------------------------------\n";
        std::cout<<"                 RESCUEGRID MAIN MENU               \n";
        std::cout<<"----------------------------------------------------\n";
        std::cout<<" 1. Register an incident\n";
        std::cout<<" 2. List all incidents\n";
        std::cout<<" 3. Search for an incident by ID\n";
        std::cout<<" 4. Register a responder\n";
        std::cout<<" 5. List all responders\n";
        std::cout<<" 6. Register a rescue vehicle\n";
        std::cout<<" 7. List all rescue vehicles\n";
        std::cout<<" 8. Dispatch resources to an incident\n";
        std::cout<<" 9. Update an incident's status\n";
        std::cout<<" 10. Exit\n";
        std::cout<<"----------------------------------------------------\n";

        int choice=0;
        if (!readInt("Select an option (1-10): ", choice, 1, 10)) {
            // EOF encountered on standard input (e.g. piped input or end of test script)
            std::cout<<"\n[!] End of input stream reached. Exiting RescueGrid.\n";
            break;
        }

        switch (choice) {
            case 1:
                handleRegisterIncident(manager);
                break;
            case 2:
                handleListIncidents(manager);
                break;
            case 3:
                handleSearchIncident(manager);
                break;
            case 4:
                handleRegisterResponder(manager);
                break;
            case 5:
                handleListResponders(manager);
                break;
            case 6:
                handleRegisterVehicle(manager);
                break;
            case 7:
                handleListVehicles(manager);
                break;
            case 8:
                handleDispatch(manager);
                break;
            case 9:
                handleUpdateIncidentStatus(manager);
                break;
            case 10:
                std::cout<<"\nExiting RescueGrid Simulator. Thank you!\n";
                running = false;
                break;
            default:
                std::cout<<"  [!] Unknown option. Please select 1 through 10.\n";
                break;
        }
    }

    return 0;
}
