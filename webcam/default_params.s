.syntax unified
.cpu cortex-m0plus
.thumb


.section .rodata
.global default_params
default_params:
.incbin "default_params.bin"
.word 0
