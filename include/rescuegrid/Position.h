#ifndef RESCUEGRID_POSITION_H
#define RESCUEGRID_POSITION_H

#include <string>

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
     * @brief Constructs a Position with specified x and y coordinates.
     * @param x Horizontal coordinate (defaults to 0).
     * @param y Vertical coordinate (defaults to 0).
     */
    explicit Position(int x = 0, int y = 0);

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
