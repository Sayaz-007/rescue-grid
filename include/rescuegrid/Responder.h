#ifndef RESCUEGRID_RESPONDER_H
#define RESCUEGRID_RESPONDER_H

#include "rescuegrid/Position.h"
#include <string>

namespace rescuegrid{  

    enum class ResponderSpecialization
    {
        Firefighter,
        Paramedic,
        RescueSpecialist
    };

     //Represents an individual emergency responder operating in the grid.
     //Encapsulates responder identification, personnel name, specialization,
     //current geographic coordinates, and operational availability status.
     //Designed as a concrete domain entity with standard virtual destruction,
     //allowing seamless transition into an abstract inheritance hierarchy in
     //future development phases.

    class Responder {
        public:
            Responder(const std::string& id,const std::string& name,ResponderSpecialization specialization,const Position& position,bool isAvailable = true);

            /**
             * @brief Virtual destructor to support future polymorphic hierarchies.
             */
            virtual ~Responder() = default;

            //get functions
            const std::string& getId() const;
            const std::string& getName() const;
            ResponderSpecialization getSpecialization() const;
            const Position& getPosition() const;
            bool isAvailable() const;

            //set functions
            void setPosition(const Position& newPosition);
            void setPosition(int x, int y);
            void setAvailability(bool available);
            std::string getSpecializationString() const;

            //display fuctions
            std::string toString() const;
            void display() const;

        private:
            std::string m_id;
            std::string m_name;
            ResponderSpecialization m_specialization;
            Position m_position;
            bool m_isAvailable;
    };

} // namespace rescuegrid

#endif // RESCUEGRID_RESPONDER_H
