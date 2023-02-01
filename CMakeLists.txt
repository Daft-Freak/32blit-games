cmake_minimum_required(VERSION 3.9)

project(32blit-games)

FILE(GLOB SUBDIRS ${CMAKE_CURRENT_LIST_DIR}/repos/**/*)

FOREACH(dir ${SUBDIRS})
    add_subdirectory(${dir})
ENDFOREACH()
