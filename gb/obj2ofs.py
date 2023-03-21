#!/usr/bin/env python3

import sys

def obj2ofs(filename, section, define):
    if len(define) > 0:
        print('const void __at(0x{:4X}) {:s};'.format(int(define), section))

    detected = False
    with open(filename) as f:
        line = f.readline()
        while line:
            decoded_line = [x.strip() for x in line.split(' ')]
            if decoded_line[0] == 'A':
                detected = (decoded_line[1] == section)
            if (detected and decoded_line[0] == 'S'):
                print('const void __at(0x{:04X}) {:s};'.format(int(define) + int(decoded_line[2][5:], base=16), decoded_line[1][1:]))
            line = f.readline()
    return

if __name__=='__main__':
    obj2ofs(sys.argv[1], sys.argv[2], sys.argv[3])
