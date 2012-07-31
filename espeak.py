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
logger = logging.getLogger('speak')

supported = True

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
        
        sink = self.pipeline.get_by_name('sink')
        
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
                        
            elif  message.type in (Gst.MessageType.EOS, Gst.MessageType.ERROR):
                logger.debug(message.type)
                self.stop_sound_device()
                
        self._was_message = False
        bus = self.pipeline.get_bus()
        bus.add_signal_watch()
        bus.connect('message', gstmessage_cb)
        
    def _new_buffer(self, buf):
        self.emit("new-buffer", buf)
        return False

# load proper espeak plugin
try:
    import gi
    gi.require_version('Gst', '1.0')
    from gi.repository import Gst
    Gst.element_factory_make('espeak', 'espeak')
    from espeak_gst import AudioGrabGst as AudioGrab
    from espeak_gst import *
    logger.info('use gst-plugins-espeak')
except Exception, e:
    logger.info('disable gst-plugins-espeak: %s' % e)
    if subprocess.call('which espeak', shell=True) == 0:
        from espeak_cmd import AudioGrabCmd as AudioGrab
        from espeak_cmd import *
    else:
        logger.info('disable espeak_cmd')
        supported = False
