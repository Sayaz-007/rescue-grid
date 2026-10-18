#ifndef RESCUEGRID_POSITION_H
#define RESCUEGRID_POSITION_H

#include <string>
#include <ostream>

namespace rescuegrid {

/**
 * @brief Represents a 2D discrete coordinate in the simulation grid.
 *
 * Position encapsulates integer x and y coordinates, ensuring that
 * location data remains grouped and immutable from outside without
 * explicit member operations.
 */
class Position {
public:
    /**
     * @brief Default constructor initializing coordinates to origin (0, 0).
     */
    Position();

    /**
     * @brief Parameterized constructor initializing coordinates to specified values.
     * @param x Horizontal coordinate.
     * @param y Vertical coordinate.
     */
    Position(int x, int y);

    /**
     * @brief Equality operator comparing coordinates.
     * @param other The position to compare with.
     * @return True if both x and y coordinates match, false otherwise.
     */
    bool operator==(const Position& other) const;

    /**
     * @brief Inequality operator comparing coordinates.
     * @param other The position to compare with.
     * @return True if either coordinate differs, false otherwise.
     */
    bool operator!=(const Position& other) const;

    /**
     * @brief Friend function for stream insertion output formatting.
     * @param os Target output stream.
     * @param pos Position instance to write.
     * @return Reference to the target output stream for chaining.
     */
    friend std::ostream& operator<<(std::ostream& os, const Position& pos);

    /**
     * @brief Gets the horizontal coordinate.
     * @return Current x coordinate.
     */
    int getX() const;

    /**
     * @brief Gets the vertical coordinate.
     * @return Current y coordinate.
     */
    int getY() const;

    /**
     * @brief Formats the position as a human-readable string.
     * @return String in format "(x, y)".
     */
    std::string toString() const;

    /**
     * @brief Displays the formatted position to standard output.
     */
    void display() const;

private:
    int m_x;
    int m_y;
};

} // namespace rescuegrid

#endif // RESCUEGRID_POSITION_H
