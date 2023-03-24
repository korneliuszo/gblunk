#include <gb/gb.h>
#include <gbdk/incbin.h>

#include <stdint.h>
#include <stdio.h>
#include <string.h>

INCBIN(ramcode, "lunk_core.bin")
INCBIN_EXTERN(ramcode)

#include "lunk_core.h"

typedef void (*my_ram_function_t)(void);

void main(void)
{
    memcpy(&_RAMCODE,ramcode,INCBIN_SIZE(ramcode));
    puts("Lunk v2.1 by Kaede");
    disable_interrupts();
    ((my_ram_function_t)&lunk_core)();
}
