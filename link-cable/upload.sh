#!/bin/bash


./reboot.py
sleep 2
../picotool/picotool load build/gbusb.uf2
../picotool/picotool reboot -a
