#!/usr/bin/env python3
import sys

import gi
gi.require_version('Gst', '1.0')
gi.require_version('GstVideo', '1.0')
from gi.repository import GObject, Gst, GstVideo

Gst.init(sys.argv)

from PySide6.QtUiTools import QUiLoader
from PySide6.QtWidgets import QApplication, QWidget, QFileDialog
from PySide6.QtCore import QFile, QIODevice, QObject, Slot, QTimer

import gb_lunk
import picdump
import contrast_tables

class CDC_comm():
    def __init__(self, wind):
        self.lunk =gb_lunk.GB_Lunk("/dev/serial/by-id/usb-Kaede_USB_to_Game_Boy_Link_Cable_1-if00")
        self.dumper = picdump.Picdump(self.lunk)
        self.pipeline = Gst.parse_launch(
            'appsrc name=source caps=video/x-raw,format=RGB,width=128,height=112 is-live=true do-timestamp=true ! videoconvert name = convert ! xvimagesink name=sink')  # xvimagesink, ximagesink
        self.source = self.pipeline.get_by_name("source")
        self.videoconvert = self.pipeline.get_by_name("convert")
        self.sink = self.pipeline.get_by_name("sink")

        self.WinId = wind.winId()
        self.setup_pipeline()
        self.start_pipeline()

    def setup_pipeline(self):
        self.state = Gst.State.NULL

        if not self.pipeline or not self.source or not self.videoconvert or not self.sink:
            print("ERROR: Not all elements could be created")
            sys.exit(1)

        # instruct the bus to emit signals for each received message
        # and connect to the interesting signals
        bus = self.pipeline.get_bus()

        bus.add_signal_watch()
        bus.enable_sync_message_emission()
        bus.connect('sync-message::element', self.on_sync_message)

    def on_sync_message(self, bus, msg):
        if msg.get_structure().get_name() == 'prepare-window-handle':
            msg.src.set_window_handle(self.WinId)

    def start_pipeline(self):
        self.pipeline.set_state(Gst.State.PLAYING)

    def snap(self,window):
        conf = dump_cfg(window)
        self.dumper.capture(conf)
        image=self.dumper.dump()
        image=image.convert("RGB")
        data=image.tobytes()
        buf = Gst.Buffer.new_allocate(None, len(data), None)
        buf.fill(0, data)
        retval = self.source.emit('push-buffer', buf)
        if retval != Gst.FlowReturn.OK:
            print(retval)



def dump_cfg(window):
    return bytes([
        #A000
        window.A000.value(),
        #A001
        0x80 if window.A001_7.isChecked() else 0x00 |
        0x40 if window.A001_6.isChecked() else 0x00 |
        0x20 if window.A001_5.isChecked() else 0x00 |
        0x10 if window.A001_4.isChecked() else 0x00 |
        window.A001_30.value(),
        #A002
        (window.A0023.value() >> 8),
        #A003
        (window.A0023.value() & 0xFF),
        #A004
        (window.A004_74.value() << 4) |
        0x08 if window.A004_3.isChecked() else 0x00 |
        int(window.A004_20.value()/0.5),
        #A005
        0x80 if window.A005_7.isChecked() else 0x00 |
        0x40 if window.A005_6.isChecked() else 0x00 |
        0x20 if window.A005_50.value()>0 else 0x00 |
        abs(window.A005_50.value()//32),
        #A006-A035
        window.A006.value(),
        window.A007.value(),
        window.A008.value(),
        window.A009.value(),
        window.A00A.value(),
        window.A00B.value(),
        window.A00C.value(),
        window.A00D.value(),
        window.A00E.value(),
        window.A00F.value(),
        window.A010.value(),
        window.A011.value(),
        window.A012.value(),
        window.A013.value(),
        window.A014.value(),
        window.A015.value(),
        window.A016.value(),
        window.A017.value(),
        window.A018.value(),
        window.A019.value(),
        window.A01A.value(),
        window.A01B.value(),
        window.A01C.value(),
        window.A01D.value(),
        window.A01E.value(),
        window.A01F.value(),
        window.A020.value(),
        window.A021.value(),
        window.A022.value(),
        window.A023.value(),
        window.A024.value(),
        window.A025.value(),
        window.A026.value(),
        window.A027.value(),
        window.A028.value(),
        window.A029.value(),
        window.A02A.value(),
        window.A02B.value(),
        window.A02C.value(),
        window.A02D.value(),
        window.A02E.value(),
        window.A02F.value(),
        window.A030.value(),
        window.A031.value(),
        window.A032.value(),
        window.A013.value(),
        window.A034.value(),
        window.A035.value(),
       ])

def load_cfg(window,data):
    window.A000.setValue(data[0])
    window.A001_7.setChecked(bool(data[1]&0x80))
    window.A001_6.setChecked(bool(data[1]&0x40))
    window.A001_5.setChecked(bool(data[1]&0x20))
    window.A001_4.setChecked(bool(data[1]&0x10))
    window.A001_30.setValue(data[1]%0x0F)
    window.A0023.setValue((data[2]<<8)|data[3])
    window.A004_74.setValue(data[4]>>4)
    window.A004_3.setChecked(bool(data[4]&0x08))
    window.A004_20.setValue((data[4]&0x7)*0.5)
    window.A005_7.setChecked(bool(data[5]&0x80))
    window.A005_6.setChecked(bool(data[5]&0x40))
    window.A005_50.setValue((1 if data[5]&0x20 else -1)*(data[5]&0x1F)*32)
    window.A006.setValue(data[6])
    window.A007.setValue(data[7])
    window.A008.setValue(data[8])
    window.A009.setValue(data[9])
    window.A00A.setValue(data[0xA])
    window.A00B.setValue(data[0xB])
    window.A00C.setValue(data[0xC])
    window.A00D.setValue(data[0xD])
    window.A00E.setValue(data[0xE])
    window.A010.setValue(data[0x10])
    window.A011.setValue(data[0x11])
    window.A012.setValue(data[0x12])
    window.A013.setValue(data[0x13])
    window.A014.setValue(data[0x14])
    window.A015.setValue(data[0x15])
    window.A016.setValue(data[0x16])
    window.A017.setValue(data[0x17])
    window.A018.setValue(data[0x18])
    window.A019.setValue(data[0x19])
    window.A01A.setValue(data[0x1A])
    window.A01B.setValue(data[0x1B])
    window.A01C.setValue(data[0x1C])
    window.A01D.setValue(data[0x1D])
    window.A01E.setValue(data[0x1E])
    window.A01F.setValue(data[0x1F])
    window.A020.setValue(data[0x20])
    window.A021.setValue(data[0x21])
    window.A022.setValue(data[0x22])
    window.A023.setValue(data[0x23])
    window.A024.setValue(data[0x24])
    window.A025.setValue(data[0x25])
    window.A026.setValue(data[0x26])
    window.A027.setValue(data[0x27])
    window.A028.setValue(data[0x28])
    window.A029.setValue(data[0x29])
    window.A02A.setValue(data[0x2A])
    window.A02B.setValue(data[0x2B])
    window.A02C.setValue(data[0x2C])
    window.A02D.setValue(data[0x2D])
    window.A02E.setValue(data[0x2E])
    window.A02F.setValue(data[0x2F])
    window.A030.setValue(data[0x30])
    window.A031.setValue(data[0x31])
    window.A032.setValue(data[0x32])
    window.A033.setValue(data[0x33])
    window.A034.setValue(data[0x34])
    window.A035.setValue(data[0x35])

if __name__ == "__main__":
    app = QApplication(sys.argv)

    ui_file_name = "picgui.ui"
    ui_file = QFile(ui_file_name)
    if not ui_file.open(QIODevice.ReadOnly):
        print(f"Cannot open {ui_file_name}: {ui_file.errorString()}")
        sys.exit(-1)
    loader = QUiLoader()
    window = loader.load(ui_file)
    ui_file.close()
    if not window:
        print(loader.errorString())
        sys.exit(-1)

    def connect_cdc(window):
        window.player = CDC_comm(window.video)
        window.autorun.setEnabled(True)
        window.autorun_ms.setEnabled(True)
        window.Snap.setEnabled(True)
        window.CCDC.setEnabled(False)

    def setup_uvc(window):
        import usb.core
        import usb.util
        dev = usb.core.find(idVendor=0xcafe, idProduct=0x4020)
        dev.ctrl_transfer(usb.util.CTRL_TYPE_VENDOR | usb.util.CTRL_OUT,1,data_or_wLength=dump_cfg(window)) 

    window.CCDC.clicked.connect(lambda x: connect_cdc(window))
    window.Snap.clicked.connect(lambda x: window.player.snap(window))
    def save(window):
        name = QFileDialog.getSaveFileName(window, 'Save File')
        file = open(name[0],'wb')
        file.write(dump_cfg(window))
        file.close()
    def load(window):
        name = QFileDialog.getOpenFileName(window, 'Load File')
        file = open(name[0],'rb')
        data = file.read(-1)
        file.close()
        load_cfg(window,data)
    
    def loadtable(window):
        data = bytearray(dump_cfg(window))
        contrast = window.Tcontrast.value()
        if window.Tdither.isChecked():
            if window.Thighlight.isChecked():
                data[6:0x36] = bytes(contrast_tables.ditherHighLightValues[contrast])
            else:
                data[6:0x36] = bytes(contrast_tables.ditherLowLightValues[contrast])
        else:
            if window.Thighlight.isChecked():
                data[6:0x36] = bytes(contrast_tables.ditherNoHighLightValues[contrast])
            else:
                data[6:0x36] = bytes(contrast_tables.ditherNoLowLightValues[contrast])

        load_cfg(window,data)

    window.Save.clicked.connect(lambda : save(window))
    window.Read.clicked.connect(lambda : load(window))
    window.SetupUVC.clicked.connect(lambda : setup_uvc(window))
    window.Tloadtable.clicked.connect(lambda : loadtable(window))

    timer = QTimer(window)
    timer.timeout.connect(lambda: window.player.snap(window))
    timer.setInterval(100)
    window.autorun_ms.valueChanged.connect(timer.setInterval)
    window.autorun.stateChanged.connect(lambda x: timer.start() if x else timer.stop())
    window.show()

    sys.exit(app.exec())
