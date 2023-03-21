#!/usr/bin/env python3

import usb.core
import usb.util


dev = usb.core.find(idVendor=0xcafe, idProduct=0x4001)
dev.ctrl_transfer(usb.util.CTRL_TYPE_VENDOR,usb.util.CTRL_OUT,0)

