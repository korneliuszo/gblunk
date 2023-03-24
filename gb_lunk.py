
import serial
import struct

class GB_Lunk:
    def __init__(self,port):
        self.c = serial.Serial(port,30000)
    
    def write_chunk(self,addr,data):
        l=len(data)
        l = min(l,256)
        pkt=struct.pack(">cBH",b"W",l%256,addr) + data[:l]
        self.c.write(pkt)
        self.c.flush()
        self.c.read(len(pkt))
        return l
    
    def read_chunk(self,addr,l):
        l = min(l,256)
        pkt=struct.pack(">cBHb",b"R",l%256,addr,0) + bytes(l)
        self.c.write(pkt)
        self.c.flush()
        self.c.read(5)
        return self.c.read(l)

    def write(self,addr,data):
        [self.write_chunk(addr+i,data[i:i+256]) for i in range(0, len(data), 256)]
        return
    def read(self,addr,l):
        return b"".join([self.read_chunk(addr+i,min(256,l-i)) for i in range(0, l, 256)])

