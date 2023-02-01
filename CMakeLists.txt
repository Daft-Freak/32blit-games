cmake_minimum_required(VERSION 3.9)

project(32blit-games)

find_package(32BLIT CONFIG REQUIRED)

FILE(GLOB SUBDIRS ${CMAKE_CURRENT_LIST_DIR}/repos/**/*)

FOREACH(dir ${SUBDIRS})
    add_subdirectory(${dir})
ENDFOREACH()
