#ifndef RESCUEGRID_POSITION_H
#define RESCUEGRID_POSITION_H

#include <string>
#include <ostream>

namespace rescuegrid{


 //Represents a 2D discrete coordinate in the simulation grid.
 //Position encapsulates integer x and y coordinates, ensuring that location data remains grouped and immutable from outside without explicit member operations.

class Position
{
    public:
        Position(); //default constructor
        Position(int x, int y); //parametrized constructor
        bool operator==(const Position& other) const; //overloaded == operator for comparing coords
        bool operator!=(const Position& other) const; //this is kinda unnecessary as we have == but kept it just incase we decide to use
        friend std::ostream& operator<<(std::ostream& o, const Position& pos); //friend function for overloading output <<
        
        //get functions
        int getX() const;
        int getY() const;

        //display functions
        std::string toString() const;
        void display() const;

    private:
        int m_x;
        int m_y;
};

}

#endif
