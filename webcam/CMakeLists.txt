cmake_minimum_required(VERSION 3.13)
# initialize the SDK based on PICO_SDK_PATH
# note: this must happen before project()
include(pico_sdk_import.cmake)
project(gbuvc)
 
pico_sdk_init()

add_executable(gbuvc)

pico_generate_pio_header(gbuvc ${CMAKE_CURRENT_LIST_DIR}/pio/spi.pio)

target_include_directories(gbuvc PRIVATE ${CMAKE_CURRENT_LIST_DIR})

target_sources(gbuvc PRIVATE
        main.c

        usb_descriptors.c

        # PIO components
        pio/pio_spi.c
        default_params.s
        )

#pico_set_binary_type(gbuvc copy_to_ram)        
target_link_libraries(gbuvc PRIVATE pico_stdlib hardware_pio tinyusb_device tinyusb_board)
pico_add_extra_outputs(gbuvc)

