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

import logging
logger = logging.getLogger('speak')

import gst
import local_espeak as espeak

PITCH_MAX = 200
RATE_MAX = 200

class AudioGrabGst(espeak.BaseAudioGrab):
    def speak(self, status, text):
        # XXX workaround for http://bugs.sugarlabs.org/ticket/1801
        if not [i for i in unicode(text, 'utf-8', errors='ignore') \
                if i.isalnum()]:
            return

        self.make_pipeline('espeak name=espeak ! wavenc')
        src = self.pipeline.get_by_name('espeak')

        pitch = int(status.pitch) - 120
        rate = int(status.rate) - 120

        logger.debug('pitch=%d rate=%d voice=%s text=%s' % (pitch, rate,
                status.voice.name, text))

        src.props.text = text
        src.props.pitch = pitch
        src.props.rate = rate
        src.props.voice = status.voice.name

        self.restart_sound_device()

def voices():
    out = []

    for i in gst.element_factory_make('espeak').props.voices:
        name, language, dialect = i
        #if name in ('en-rhotic','english_rp','english_wmids'):
            # these voices don't produce sound
         #   continue
        out.append((language, name))

    return out
