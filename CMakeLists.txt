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

# Core domain library
add_library(rescuegrid_core STATIC
    src/Position.cpp
    src/Incident.cpp
    src/Responder.cpp
    src/RescueVehicle.cpp
    src/RescueManager.cpp
    src/menu.cpp
)

target_include_directories(rescuegrid_core
    PUBLIC
        $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/include>
        $<INSTALL_INTERFACE:include>
    PRIVATE
        ${CMAKE_CURRENT_SOURCE_DIR}/src
)

# Application executable target
add_executable(RescueGrid
    src/main.cpp
)

target_link_libraries(RescueGrid PRIVATE rescuegrid_core)

# Compiler warning flags
if(MSVC)
    target_compile_options(rescuegrid_core PRIVATE /W4 /permissive-)
    target_compile_options(RescueGrid PRIVATE /W4 /permissive-)
else()
    target_compile_options(rescuegrid_core PRIVATE -Wall -Wextra -Wpedantic)
    target_compile_options(RescueGrid PRIVATE -Wall -Wextra -Wpedantic)
endif()

# Automated unit testing target and CTest integration
enable_testing()

add_executable(rescuegrid_tests
    tests/test_main.cpp
)

target_link_libraries(rescuegrid_tests PRIVATE rescuegrid_core)

if(MSVC)
    target_compile_options(rescuegrid_tests PRIVATE /W4 /permissive-)
else()
    target_compile_options(rescuegrid_tests PRIVATE -Wall -Wextra -Wpedantic)
endif()

add_test(NAME CoreClassTests COMMAND rescuegrid_tests)
