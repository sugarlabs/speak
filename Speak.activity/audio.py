# Speak.activity
# A simple front end to the espeak text-to-speech engine on the XO laptop
#
# Copyright (C) 2008  Joshua Minor
# This file is part of Speak.activity
#
# Parts of Speak.activity are based on code from Measure.activity
# Copyright (C) 2007  Arjun Sarwal - arjun@laptop.org
# 
#     Speak.activity is free software: you can redistribute it and/or modify
#     it under the terms of the GNU General Public License as published by
#     the Free Software Foundation, either version 3 of the License, or
#     (at your option) any later version.
# 
#     Foobar is distributed in the hope that it will be useful,
#     but WITHOUT ANY WARRANTY; without even the implied warranty of
#     MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#     GNU General Public License for more details.
# 
#     You should have received a copy of the GNU General Public License
#     along with Foobar.  If not, see <http://www.gnu.org/licenses/>.

# This code is a stripped down version of the audio grabber from Measure

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
        self.stop_sound_device()
        
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

    def playfd(self, fd):
        self.stop_sound_device()

        # build a pipeline that reads the given file
        # and sends it to both the real audio output
        # and a fake one that we use to draw from
        if self.pipeline is None:
            p = 'fdsrc name=fd-source ! wavparse ! tee name=tee tee.! audioconvert ! alsasink tee.! queue ! audioconvert name=conv'
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
        self.pipeline.get_by_name("fd-source").set_property('fd', fd)

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
        if self.pipeline is not None:
            self.pipeline.set_state(gst.STATE_NULL)

    def restart_sound_device(self):
        self.pipeline.set_state(gst.STATE_PLAYING)

