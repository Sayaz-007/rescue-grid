cmake_minimum_required(VERSION 3.15)

project(RescueGrid
    VERSION 0.1.0
    DESCRIPTION "Disaster response and evacuation simulator"
    LANGUAGES CXX
)

# Standard C++ configuration
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

# Export compile commands for tool integration
set(CMAKE_EXPORT_COMPILE_COMMANDS ON)

# Application executable target
add_executable(RescueGrid
    src/main.cpp
)

# Include directories
target_include_directories(RescueGrid
    PRIVATE
        ${CMAKE_CURRENT_SOURCE_DIR}/src
    PUBLIC
        $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/include>
        $<INSTALL_INTERFACE:include>
)

# Compiler warning flags
if(MSVC)
    target_compile_options(RescueGrid PRIVATE /W4 /permissive-)
else()
    target_compile_options(RescueGrid PRIVATE -Wall -Wextra -Wpedantic)
endif()
