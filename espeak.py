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
        self.handle1 = None
        self.handle2 = None
        
    def speak(self, status, text):
        # 175 is default value, min is 80
        rate = 60 + int(((175 - 80) * 2) * status.rate / RATE_MAX)
        wavpath = "/tmp/speak.wav"

        subprocess.call(["espeak", "-w", wavpath, "-p", str(status.pitch),
                "-s", str(rate), "-v", status.voice.name, text],
                stdout=subprocess.PIPE)
                
        self.stop_sound_device()
        
        self.make_pipeline(wavpath)
        
        # play
        self.restart_sound_device()
        
    def restart_sound_device(self):
        self.pipeline.set_state(Gst.State.NULL)
        self.pipeline.set_state(Gst.State.PLAYING)

    def stop_sound_device(self):
        if self.pipeline is None:
            return
        self.pipeline.set_state(Gst.State.NULL)
        self._new_buffer('')

    def make_pipeline(self, wavpath):
        if self.pipeline is not None:
            self.stop_sound_device()
            del self.pipeline

        self.pipeline = Gst.Pipeline()
        self.player = Gst.ElementFactory.make("playbin", "espeak")
        self.pipeline.add(self.player)
        self.player.set_property("uri", Gst.filename_to_uri(wavpath))
        self.pipeline.set_state(Gst.State.PLAYING)
        
        def on_buffer(element, buffer, pad):
            if self.andle1:
                GObject.source_remove(self.self.andle1)
                self.andle1 = GObject.timeout_add(100,
                    self._new_buffer, str(buffer))
            return True
        
        def gstmessage_cb(bus, message):
            self._was_message = True
            
            if message.type == Gst.MessageType.WARNING:
                def check_after_warnings():
                    if not self._was_message:
                        self.stop_sound_device()
                    return True
                
                logger.debug(message.type)
                self._was_message = False
                if self.andle2:
                    GObject.source_remove(self.self.andle2)
                    self.andle2 = GObject.timeout_add(500,
                        self._new_buffer, str(buffer))
                        
            elif  message.type == Gst.MessageType.EOS:
                pass
            
            elif message.type == Gst.MessageType.ERROR:
                logger.debug(message.type)
                self.stop_sound_device()
                
        self._was_message = False
        bus = self.pipeline.get_bus()
        bus.add_signal_watch()
        bus.connect('message', gstmessage_cb)
        
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
