#!/bin/bash


./reboot.py
sleep 2
../picotool/picotool load build/gbuvc.uf2
../picotool/picotool reboot -a
