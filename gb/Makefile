CC	= /opt/gbdk/bin/lcc -Wa-l -Wl-m
SDLD = /opt/gbdk/bin/sdld

RAM_CODE_ADDR = 50176

# CFLAGS	=

BINS	= lunk.gb

all:	$(BINS)

%.o:	%.c
	$(CC) $(CFLAGS) -c -o $@ $<

%.o:	%.s
	$(CC) $(CFLAGS) -c -o $@ $<

%.s:	%.c
	$(CC) $(CFLAGS) -S -o $@ $<

%.gb:	%.o
	$(CC) -o $@ $<

lunk_core.ihx: lunk_core.o
	$(SDLD) -n -i -k -Wl"-b _RAMCODE=$(RAM_CODE_ADDR)" -o ./lunk_core.ihx ./lunk_core.o
lunk_core.bin: lunk_core.ihx
	objcopy --input-target=ihex --output-target=binary lunk_core.ihx lunk_core.bin
lunk_core.h: lunk_core.ihx
	python3 ./obj2ofs.py ./lunk_core.o _RAMCODE $(RAM_CODE_ADDR) >./lunk_core.h
	
lunk.o: lunk_core.h lunk_core.bin


clean:
	rm -f *.o *.lst *.map *.gb *.ihx *.sym *.cdb *.adb *.asm *.bin lunk_core.h

# Link file, and write 0x80 at position 0x143 in header
lunk.gb:	lunk.o
	$(CC) $(CFLAGS) -o lunk.gb lunk.o
