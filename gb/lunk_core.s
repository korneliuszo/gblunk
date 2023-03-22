_SB_REG      = 0xFF01    ; Serial IO data buffer
_SC_REG      = 0xFF02    ; Serial IO control register

	.globl _lunk_core

	.area _RAMCODE

; HL must contain _SC_REG address
.macro WAIT_SIO ?notyet
notyet:
        bit     7, (hl)
        jr      nz, notyet
.endm
.macro READ_SIO
        WAIT_SIO
        ldh     a, (_SB_REG)
        ld      (hl), #0x80
.endm
.macro WRITE_SIO
        WAIT_SIO
        ldh     (_SB_REG), a
        ld      (hl), #0x80
.endm
_lunk_core::
        ld      hl, #_SC_REG
        ld      (hl), #0x80
loop:
        READ_SIO
        cp      #'W'
        jr      NZ, read
        READ_SIO
        ld      c, a  ; c == count
        READ_SIO
        ld      d, a
        READ_SIO
        ld      e, a  ; de == address
write_loop:
        READ_SIO
        ld      (de), a
        inc     de
        dec     c
        jr      nz, write_loop
        jr      loop
read:
        cp      #'R'
        jr      nz, loop
        READ_SIO
        ld      c, a
        READ_SIO
        ld      d, a
        READ_SIO
        ld      e, a
read_loop:
        ld      a, (de)
        WRITE_SIO
        inc     de
        dec     c
        jr      nz, read_loop
        WAIT_SIO
        ld      (hl), #0x80
        jr      loop
