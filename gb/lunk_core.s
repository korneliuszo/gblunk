_SB_REG      = 0xFF01    ; Serial IO data buffer
_SC_REG      = 0xFF02    ; Serial IO control register

	.globl _lunk_core

	.area _RAMCODE

.macro READ_SIO ?notyet
notyet:
	ldh	a, (_SC_REG + 0)
	rlca
	jr	C, notyet
	ldh	a, (_SB_REG + 0)
	ld c, a
	ld	a, #0x80
	ldh	(_SC_REG + 0), a
.endm

.macro WRITE_SIO ?notyet
notyet:
	ldh	a, (_SC_REG + 0)
	rlca
	jr	C, notyet
	ld a, c
	ldh	(_SB_REG + 0), a
	ld	a, #0x80
	ldh	(_SC_REG + 0), a
.endm

read:
	cp #0x52 ; 'R'
	jr	NZ, _lunk_core
	READ_SIO
	ld b, c
	READ_SIO
	ld h, c
	READ_SIO
	ld l, c
read_loop:
	ld a,(HLI)
	ld c, a
	WRITE_SIO
	dec b
	jr NZ, read_loop
	notyet:
	ldh	a, (_SC_REG + 0)
	rlca
	jr	C, notyet
	jr loop

_lunk_core:
	ld	a, #0x80
	ldh	(_SC_REG + 0), a
loop:
	READ_SIO
	ld a, c
	cp #0x57 ; 'W'
	jr	NZ, read
	READ_SIO
	ld b, c
	READ_SIO
	ld h, c
	READ_SIO
	ld l, c
write_loop:
	READ_SIO
	ld a, c
	ld (HLI), a
	dec b
	jr NZ, write_loop
	jr loop

