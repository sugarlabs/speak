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

import gst
import gobject
import subprocess

import logging
logger = logging.getLogger('speak')

supported = True


class BaseAudioGrab(gobject.GObject):
    __gsignals__ = {
        'new-buffer': (gobject.SIGNAL_RUN_FIRST, None, [gobject.TYPE_PYOBJECT])
    }

    def __init__(self):
        gobject.GObject.__init__(self)
        self.pipeline = None
        self.quiet = True

    def restart_sound_device(self):
        self.quiet = False

        self.pipeline.set_state(gst.STATE_NULL)
        self.pipeline.set_state(gst.STATE_PLAYING)

    def stop_sound_device(self):
        if self.pipeline is None:
            return

        self.pipeline.set_state(gst.STATE_NULL)
        # Shut theirs mouths down
        self._new_buffer('')

        self.quiet = True

    def make_pipeline(self, cmd):
        if self.pipeline is not None:
            self.stop_sound_device()
            del self.pipeline

        # build a pipeline that reads the given file
        # and sends it to both the real audio output
        # and a fake one that we use to draw from
        self.pipeline = gst.parse_launch(
                cmd + ' ' \
                '! decodebin ' \
                '! tee name=tee ' \
                'tee.! audioconvert ' \
                    '! alsasink ' \
                'tee.! queue ' \
                    '! audioconvert ! fakesink name=sink')

        def on_buffer(element, buffer, pad):
            # we got a new buffer of data, ask for another
            gobject.timeout_add(100, self._new_buffer, str(buffer))
            return True

        sink = self.pipeline.get_by_name('sink')
        sink.props.signal_handoffs = True
        sink.connect('handoff', on_buffer)

        def gstmessage_cb(bus, message):
            self._was_message = True

            if message.type == gst.MESSAGE_WARNING:
                def check_after_warnings():
                    if not self._was_message:
                        self.stop_sound_device()
                    return True

                logger.debug(message.type)
                self._was_message = False
                gobject.timeout_add(500, self._new_buffer, str(buffer))

            elif  message.type in (gst.MESSAGE_EOS, gst.MESSAGE_ERROR):
                logger.debug(message.type)
                self.stop_sound_device()

        self._was_message = False
        bus = self.pipeline.get_bus()
        bus.add_signal_watch()
        bus.connect('message', gstmessage_cb)

    def _new_buffer(self, buf):
        if not self.quiet:
            # pass captured audio to anyone who is interested
            self.emit("new-buffer", buf)
        return False

# load proper espeak plugin
try:
    import gst
    gst.element_factory_make('espeak')
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
