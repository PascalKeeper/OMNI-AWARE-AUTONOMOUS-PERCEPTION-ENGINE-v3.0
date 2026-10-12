 cmake_minimum_required(VERSION 3.16)
project(omni_aware_cpp LANGUAGES CXX)

set(CXX_STANDARD 17)
set(CXX_STANDARD_REQUIRED ON)

# Reference build (x86_64 dev machine)
add_executable(omni_aware omni_aware.cpp)
target_compile_options(omni_aware PRIVATE -O3 -march=native)

# Cross-compile target for aarch64 (Tesla HW4-like ARM)
# Usage: cmake -DCMAKE_CXX_FLAGS="-march=armv8-a+crypto" ...
add_executable(omni_aware_arm omni_aware.cpp)
target_compile_options(omni_aware_arm PRIVATE -O3)

# Install
install(TARGETS omni_aware DESTINATION bin)