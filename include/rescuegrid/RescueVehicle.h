#ifndef RESCUEGRID_RESCUEVEHICLE_H
#define RESCUEGRID_RESCUEVEHICLE_H

#include "rescuegrid/Position.h"

#include <string>

namespace rescuegrid
{
    enum class VehicleType
    {
        FireEngine,
        Ambulance,
        RescueVan
    };

    //Represents a specialized rescue vehicle operating on the grid. 
    //Encapsulates the vehicle identifier, vehicular classification,
    //current coordinates, and operational deployment availability.
    class RescueVehicle
    {
        public:
            /**
             * @brief Constructs and validates a RescueVehicle.
             * @param id Unique identification code for the vehicle (cannot be empty).
             * @param type Vehicle classification.
             * @param position Initial position on the grid.
             * @param isAvailable Operational availability flag (defaults to true).
             * @throws std::invalid_argument if id is empty.
             */
            RescueVehicle(const std::string& id,VehicleType type,const Position& position,bool isAvailable = true);

            //get functions
            const std::string& getId() const;
            VehicleType getType() const;
            const Position& getPosition() const;
            bool isAvailable() const;

            //set functions
            void setPosition(const Position& newPosition);
            void setPosition(int x, int y);
            void setAvailability(bool available);
            std::string getTypeString() const; //converts vehicle type enum to string

            //display functions 
            std::string toString() const;
            void display() const;

        private:
            std::string m_id;
            VehicleType m_type;
            Position m_position;
            bool m_isAvailable;
    };

}

#endif
