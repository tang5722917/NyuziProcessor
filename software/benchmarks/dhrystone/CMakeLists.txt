#
# Copyright 2018 Jeff Bush
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

project(dhrystone)
include(nyuzi)

add_nyuzi_executable(dhrystone
    SOURCES
    dhry_1.c
    dhry_2.c)

# The instructions with Dhrystone indicate function inlining should be
# disabled.
target_compile_options(dhrystone PRIVATE -fno-inline-functions -w)
target_compile_definitions(dhrystone PRIVATE TIME=1)
target_link_libraries(dhrystone
    c
    os-bare)
