cmake_minimum_required(VERSION 3.16)
project(IELTSFormQt LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

find_package(Qt6 6.2 REQUIRED COMPONENTS Widgets)

qt_standard_project_setup()

set(SOURCES
    src/main.cpp
    src/MainWindow.cpp
    src/SectionPanel.cpp
)

set(HEADERS
    src/MainWindow.h
    src/SectionPanel.h
)

qt_add_executable(ielts_form_qt
    ${SOURCES}
    ${HEADERS}
)

target_link_libraries(ielts_form_qt PRIVATE Qt6::Widgets)

install(TARGETS ielts_form_qt
    RUNTIME DESTINATION bin
)

