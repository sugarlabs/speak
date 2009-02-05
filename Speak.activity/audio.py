# Speak.activity
# A simple front end to the espeak text-to-speech engine on the XO laptop
# http://wiki.laptop.org/go/Speak
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
#     Speak.activity is distributed in the hope that it will be useful,
#     but WITHOUT ANY WARRANTY; without even the implied warranty of
#     MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#     GNU General Public License for more details.
# 
#     You should have received a copy of the GNU General Public License
#     along with Speak.activity.  If not, see <http://www.gnu.org/licenses/>.

# This code is a stripped down version of the audio grabber from Measure

import pygst
pygst.require("0.10")
import gst
import pygtk
import gtk, gobject
import signal, os
import time
import dbus
import logging
from struct import *

logger = logging.getLogger('speak')

class AudioGrab(gobject.GObject):
    __gsignals__ = {
        'new-buffer': (gobject.SIGNAL_RUN_FIRST, None, [gobject.TYPE_PYOBJECT])
    }

    def __init__(self):
        gobject.GObject.__init__(self)
        self.pipeline = None

    def playfile(self, status, text):
        pitch = int(status.pitch)
        rate = int(status.rate)
        # espeak uses 80 to 370
        rate = 80 + (370-80) * rate / 100

        logger.debug('pitch=%d rate=%d voice=%s text=%s' % (pitch, rate,
                status.voice.name, text))

        self.stop_sound_device()
        self._quiet = False
        
        # build a pipeline that reads the given file
        # and sends it to both the real audio output
        # and a fake one that we use to draw from
        p = 'espeak text="%s" pitch=%d rate=%d voice=%s ' \
            '! decodebin ' \
            '! tee name=tee ' \
            'tee.! audioconvert ' \
                '! alsasink ' \
            'tee.! queue ' \
                '! audioconvert name=conv' \
                % (text, pitch, rate, status.voice.name)
        self.pipeline = gst.parse_launch(p)
        
        # make a fakesink to capture audio
        fakesink = gst.element_factory_make("fakesink", "fakesink")
        fakesink.connect("handoff",self.on_buffer)
        fakesink.set_property("signal-handoffs",True)
        self.pipeline.add(fakesink)

        bus = self.pipeline.get_bus()
        bus.add_signal_watch()
        bus.connect('message', self._gstmessage_cb)

        # attach it to the pipeline
        conv = self.pipeline.get_by_name("conv")
        gst.element_link_many(conv, fakesink)
        
        # play
        self.restart_sound_device()
        
        # how do we detect when the sample has finished playing?
        # we should stop the sound device and stop emitting buffers
        # to save on CPU and battery usage when there is no audio playing

    def _gstmessage_cb(self, bus, message):
        type = message.type

        if type == gst.MESSAGE_EOS:
            # END OF SOUND FILE
            self.stop_sound_device()
        elif type == gst.MESSAGE_ERROR:
            self.stop_sound_device()

    def on_quit(self):
        self.pipeline.set_state(gst.STATE_NULL)

    def _new_buffer(self, buf):
        if not self._quiet:
            # pass captured audio to anyone who is interested via the main thread
            self.emit("new-buffer", buf)
        return False

    def on_buffer(self,element,buffer,pad):
        # we got a new buffer of data, ask for another
        gobject.timeout_add(100, self._new_buffer, str(buffer))
        return True

    def stop_sound_device(self):
        if self.pipeline is None:
            return

        self.pipeline.set_state(gst.STATE_NULL)
        # Shut theirs mouths down
        self._new_buffer('')
        self._quiet = True

    def restart_sound_device(self):
        self.pipeline.set_state(gst.STATE_NULL)
        self.pipeline.set_state(gst.STATE_PLAYING)

