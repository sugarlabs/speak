import pygst
pygst.require("0.10")
import gst
import pygtk
import gtk, gobject
import signal, os
import time
import dbus
import audioop
from struct import *

class AudioGrab(gobject.GObject):
    __gsignals__ = {
        'new-buffer': (gobject.SIGNAL_RUN_FIRST, None, [gobject.TYPE_PYOBJECT])
    }

    def __init__(self, datastore, _jobject):
        gobject.GObject.__init__(self)
        self.pipeline = None

    def playfile(self, filename):
        # build a pipeline that reads the given file
        # and sends it to both the real audio output
        # and a fake one that we use to draw from
        p = 'filesrc name=file-source ! decodebin ! tee name=tee tee.! audioconvert ! alsasink tee.! queue ! audioconvert name=conv'
        self.pipeline = gst.parse_launch(p)
        
        # make a fakesink to capture audio
        fakesink = gst.element_factory_make("fakesink", "fakesink")
        fakesink.connect("handoff",self.on_buffer)
        fakesink.set_property("signal-handoffs",True)
        self.pipeline.add(fakesink)

        # attach it to the pipeline
        conv = self.pipeline.get_by_name("conv")
        gst.element_link_many(conv, fakesink)
        
        # set the source file
        self.pipeline.get_by_name("file-source").set_property('location', filename)
        
        # play
        self.restart_sound_device()
        
        # how do we detect when the sample has finished playing?
        # we should stop the sound device and stop emitting buffers
        # to save on CPU and battery usage when there is no audio playing
        
    def on_quit(self):
        self.pipeline.set_state(gst.STATE_NULL)

    def _new_buffer(self, buf):
        # pass captured audio to anyone who is interested via the main thread
        self.emit("new-buffer", buf)
        return False

    def on_buffer(self,element,buffer,pad):
        # we got a new buffer of data, ask for another
        gobject.timeout_add(100, self._new_buffer, str(buffer))
        return True

    def stop_sound_device(self):
        self.pipeline.set_state(gst.STATE_NULL)

    def restart_sound_device(self):
        self.pipeline.set_state(gst.STATE_PLAYING)

