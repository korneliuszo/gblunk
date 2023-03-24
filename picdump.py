#!/usr/bin/env python3
import gb_lunk
from PIL import Image
import sys

class Picdump():
    def __init__(self,conn):
        self.conn = conn
    def dump(self):
        self.conn.write(0x4000,bytes([0x00]))
        data=self.conn.read(0xA100,(112*128)//4)
        img=Image.new("P",(128,112))
        img.putpalette((255,255,255,127,127,127,63,63,63,0,0,0))
        for y in range(112):
            for x in range(128):
                xtile=x//8
                ytile=y//8*8
                lb=data[ytile*32+2*(y%8)+16*xtile]
                hb=data[ytile*32+2*(y%8)+16*xtile+1]
                val= (lb & (1<<(7-x%8)))>>(7-x%8)
                val|=((hb & (1<<(7-x%8)))>>(7-x%8))*2
                img.putpixel((x,y),val)
        return img
if __name__ == "__main__":
    p= Picdump(gb_lunk.GB_Lunk("/dev/serial/by-id/usb-Kaede_USB_to_Game_Boy_Link_Cable_1-if00"))
    p.dump().save(sys.argv[1])
