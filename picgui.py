#!/usr/bin/env python3
import sys

import gi
gi.require_version('Gst', '1.0')
gi.require_version('GstVideo', '1.0')
from gi.repository import GObject, Gst, GstVideo

Gst.init(sys.argv)

from PySide6.QtUiTools import QUiLoader
from PySide6.QtWidgets import QApplication, QWidget, QFileDialog
from PySide6.QtCore import QFile, QIODevice, QObject, Slot

import gb_lunk
import picdump

class GstDisplay():
    def __init__(self, wind):
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



class CoreLogic(QObject):
    def __init__(self, parent, appsrc,window):
        super().__init__(parent)
        self.lunk =gb_lunk.GB_Lunk("/dev/serial/by-id/usb-Kaede_USB_to_Game_Boy_Link_Cable_1-if00")
        self.dumper = picdump.Picdump(self.lunk)
        self.appsrc=appsrc
        self.window = window

    def snap(self,window):

        conf = dump_cfg(window)
        
        self.dumper.capture(conf)


        image=self.dumper.dump()
        image=image.convert("RGB")
        data=image.tobytes()
        buf = Gst.Buffer.new_allocate(None, len(data), None)
        buf.fill(0, data)
        retval = self.appsrc.emit('push-buffer', buf)
        if retval != Gst.FlowReturn.OK:
            print(retval)


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

    window.player = GstDisplay(window.video)
    
    corelogic = CoreLogic(window, window.player.source, window)

    window.Snap.clicked.connect(lambda x: corelogic.snap(window))
    def save(window):
        name = QFileDialog.getSaveFileName(window, 'Save File')
        file = open(name[0],'wb')
        file.write(dump_cfg(window))
        file.close()
    window.Save.clicked.connect(lambda : save(window))
    
    window.show()

    sys.exit(app.exec())
