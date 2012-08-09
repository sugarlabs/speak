# Copyright (C) 2009, Aleksey Lim
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA

import gi
gi.require_version('Gst', '1.0')

from gi.repository import Gst
from gi.repository import GObject
import subprocess

import logging
import re

logger = logging.getLogger('speak')

PITCH_MAX = 200
RATE_MAX = 200

GObject.threads_init()
Gst.init(None)


class BaseAudioGrab(GObject.GObject):
    __gsignals__ = {
        'new-buffer': (GObject.SIGNAL_RUN_FIRST,
        None, [GObject.TYPE_PYOBJECT])}

    def __init__(self):
        GObject.GObject.__init__(self)
        self.pipeline = None
        self.handle = None
        self._was_message = False
        
    def speak(self, status, text):
        # 175 is default value, min is 80
        rate = 60 + int(((175 - 80) * 2) * status.rate / RATE_MAX)
        wavpath = "/tmp/speak.wav"

        subprocess.call(["espeak", "-w", wavpath, "-p", str(status.pitch),
                "-s", str(rate), "-v", status.voice.name, text],
                stdout=subprocess.PIPE)
                
        self.stop_sound_device()
        
        self.make_pipeline(wavpath)
        
    def restart_sound_device(self):
        try:
            self.pipeline.set_state(Gst.State.NULL)
            self.pipeline.set_state(Gst.State.READY)
            self.pipeline.set_state(Gst.State.PLAYING)
        except:
            pass

    def stop_sound_device(self):
        if self.pipeline is None:
            return
        try:
            self.pipeline.set_state(Gst.State.NULL)
            self.pipeline.set_state(Gst.State.READY)
            self._new_buffer('')
        except:
            pass

    def make_pipeline(self, wavpath):
        if self.pipeline is not None:
            self.pipeline.set_state(Gst.State.NULL)
            del(self.pipeline)
            
        self.pipeline = Gst.Pipeline()
        
        file = Gst.ElementFactory.make("filesrc", "espeak")
        wavparse = Gst.ElementFactory.make("wavparse", "wavparse")
        audioconvert = Gst.ElementFactory.make("audioconvert", "audioconvert")
        tee = Gst.ElementFactory.make('tee', "tee")
        # FIXME: alsasink no more, pulseaudio causes:
        # gst_object_unref: assertion `((GObject *) object)->ref_count > 0' failed
        playsink = Gst.ElementFactory.make("playsink", "playsink")
        queue1 = Gst.ElementFactory.make("queue", "queue1")
        fakesink = Gst.ElementFactory.make("fakesink", "fakesink")
        queue2 = Gst.ElementFactory.make("queue", "queue2")
        
        self.pipeline.add(file)
        self.pipeline.add(wavparse)
        self.pipeline.add(audioconvert)
        self.pipeline.add(tee)
        self.pipeline.add(queue1)
        self.pipeline.add(playsink)
        self.pipeline.add(queue2)
        self.pipeline.add(fakesink)
        
        file.link(wavparse)
        wavparse.link(tee)
        
        tee.link(queue1)
        queue1.link(audioconvert)
        audioconvert.link(playsink)
        
        tee.link(queue2)
        queue2.link(fakesink)
        
        file.set_property("location", wavpath)
        
        fakesink.connect('handoff', self.on_buffer)
        
        self._was_message = False
        bus = self.pipeline.get_bus()
        bus.add_signal_watch()
        bus.connect('message', self.gstmessage_cb)
        
        self.pipeline.set_state(Gst.State.PLAYING)
    
    def gstmessage_cb(self, bus, message):
        self._was_message = True
        
        if message.type == Gst.MessageType.WARNING:
            def check_after_warnings():
                if not self._was_message:
                    self.stop_sound_device()
                return True
            
            logger.debug(message.type)
            self._was_message = False
            if self.handle:
                GObject.source_remove(self.handle)
                self.handle = GObject.timeout_add(500,
                    self._new_buffer, str(buffer))
                    
        elif  message.type == Gst.MessageType.EOS:
            self.pipeline.set_state(Gst.State.NULL)
            
        elif message.type == Gst.MessageType.ERROR:
            err, debug = message.parse_error()
            logger.debug(err)
            self.stop_sound_device()
            
    def on_buffer(self, element, buffer, pad):
        # FIXME: currently not running handoff
        if self.handle:
            GObject.source_remove(self.handle)
            self.handle = GObject.timeout_add(100,
                self._new_buffer, str(buffer))
        return True
    
    def _new_buffer(self, buf):
        self.emit("new-buffer", buf)
        return False


def voices():
    out = []
    result = subprocess.Popen(["espeak", "--voices"],
        stdout=subprocess.PIPE).communicate()[0]

    for line in result.split('\n'):
        m = re.match(r'\s*\d+\s+([\w-]+)\s+([MF])\s+([\w_-]+)\s+(.+)', line)
        if not m:
            continue
        language, gender, name, stuff = m.groups()
        if stuff.startswith('mb/'):  # or \
                #name in ('en-rhotic','english_rp','english_wmids'):
            # these voices don't produce sound
            continue
        out.append((language, name))

    return out
