#include "rescuegrid/Position.h"

#include <iostream>

namespace rescuegrid {

Position::Position()
    : m_x(0), m_y(0) {}

Position::Position(int x, int y)
    : m_x(x), m_y(y) {}

bool Position::operator==(const Position& other) const {
    return m_x == other.m_x && m_y == other.m_y;
}

bool Position::operator!=(const Position& other) const {
    return !(*this == other);
}

std::ostream& operator<<(std::ostream& os, const Position& pos) {
    os << "(" << pos.m_x << ", " << pos.m_y << ")";
    return os;
}

int Position::getX() const {
    return m_x;
}

int Position::getY() const {
    return m_y;
}

std::string Position::toString() const {
    return "(" + std::to_string(m_x) + ", " + std::to_string(m_y) + ")";
}

void Position::display() const {
    std::cout << toString() << "\n";
}

} // namespace rescuegrid
