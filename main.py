"""
Main executable entry point for the RescueGrid disaster response simulator.
Independent Python implementation for Artificial Intelligence with Python course.
"""

import sys
from core.rescue_manager import RescueManager
from menu import (
    set_initial_data,
    read_int,
    handle_register_incident,
    handle_list_incidents,
    handle_search_incident,
    handle_register_responder,
    handle_list_responders,
    handle_register_vehicle,
    handle_list_vehicles,
    handle_dispatch,
    handle_update_incident_status,
)


def print_banner() -> None:
    """Print the startup header banner."""
    print("====================================================")
    print("                    RescueGrid                      ")
    print("====================================================")
    print("Description : Disaster response and evacuation simulator")
    print("Course      : Artificial Intelligence with Python")
    print("Phase       : Python Implementation & Domain Modeling")
    print("Status      : System initialized successfully.")
    print("====================================================")


def print_menu() -> None:
    """Print the 10-option main menu."""
    print("\n----------------------------------------------------")
    print("                 RESCUEGRID MAIN MENU               ")
    print("----------------------------------------------------")
    print(" 1. Register an incident")
    print(" 2. List all incidents")
    print(" 3. Search for an incident by ID")
    print(" 4. Register a responder")
    print(" 5. List all responders")
    print(" 6. Register a rescue vehicle")
    print(" 7. List all rescue vehicles")
    print(" 8. Dispatch resources to an incident")
    print(" 9. Update an incident's status")
    print(" 10. Exit")
    print("----------------------------------------------------")


def main() -> None:
    """Initialize manager, preload demonstration data, and run menu loop."""
    print_banner()

    manager = RescueManager()
    set_initial_data(manager)

    print("Preloaded demonstration data:")
    print("  - 2 Incidents  (INC-101, INC-102)")
    print("  - 2 Responders (RES-01, RES-02)")
    print("  - 2 Vehicles   (VEH-01, VEH-02)")

    running = True
    while running:
        print_menu()
        choice = read_int("Select an option (1-10): ", 1, 10)
        if choice is None:
            # EOF encountered on standard input (piped test input or Ctrl+D/Z)
            print("\n[!] End of input stream reached. Exiting RescueGrid.")
            break

        if choice == 1:
            handle_register_incident(manager)
        elif choice == 2:
            handle_list_incidents(manager)
        elif choice == 3:
            handle_search_incident(manager)
        elif choice == 4:
            handle_register_responder(manager)
        elif choice == 5:
            handle_list_responders(manager)
        elif choice == 6:
            handle_register_vehicle(manager)
        elif choice == 7:
            handle_list_vehicles(manager)
        elif choice == 8:
            handle_dispatch(manager)
        elif choice == 9:
            handle_update_incident_status(manager)
        elif choice == 10:
            print("\nExiting RescueGrid Simulator. Thank you!")
            running = False
        else:
            print("  [!] Unknown option. Please select 1 through 10.")


if __name__ == "__main__":
    main()
