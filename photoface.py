# Speak.activity
# A simple front end to the espeak text-to-speech engine on the XO laptop
# http://wiki.laptop.org/go/Speak
#
# Copyright (C) 2014 Sam Parkinson
# This file is part of Speak.activity
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


import os
import json
import math
import uuid
import base64
import logging

import sugar3.graphics.style as style

import voice
import speech
from faceselect import Eye
from faceselect import Mouth

from gi.repository import Gtk
from gi.repository import Gdk
from gi.repository import GdkPixbuf

logger = logging.getLogger('speak')


_EYE_CIRCUMFERENCE = 3
_BALL_DIST_CIRC_RATIO = 27


def _b64_to_pixbuf(b64):
    data = base64.b64decode(b64)
    path = '/tmp/{}.png'.format(uuid.uuid4())

    with open(path, 'wb') as f:
        f.write(data)
    pixbuf = GdkPixbuf.Pixbuf.new_from_file(path)

    os.remove(path)
    return pixbuf


class Status(object):

    def __init__(self):
        self.voice = voice.defaultVoice()
        self.pitch = speech.PITCH_MAX // 2
        self.rate = speech.RATE_MAX // 2

    def serialize(self):
        success, data = self.pixbuf.save_to_bufferv('png', [], [])
        pixbuf_b64 = str(base64.b64encode(data), 'utf-8')

        success, data = self.mouth.pixbuf.save_to_bufferv('png', [], [])
        mouth_pixbuf_b64 = str(base64.b64encode(data), 'utf-8')

        mouth_dict = self.mouth.__dict__.copy()
        mouth_dict['pixbuf'] = mouth_pixbuf_b64

        return json.dumps({
            'voice': {'language': self.voice.language,
                      'name': self.voice.name},
            'pitch': self.pitch,
            'rate': self.rate,
            'left_eye': self.left_eye.__dict__,
            'right_eye': self.right_eye.__dict__,
            'mouth': mouth_dict,
            'pixbuf': pixbuf_b64})

    def deserialize(self, buf):
        data = json.loads(buf)

        self.voice = voice.Voice(data['voice']['language'],
                                 data['voice']['name'])
        self.pitch = data['pitch']
        self.rate = data['rate']

        self.left_eye = Eye(tuple(data['left_eye']['center']),
                            data['left_eye']['circ'])
        self.right_eye = Eye(tuple(data['right_eye']['center']),
                             data['right_eye']['circ'])
        self.pixbuf = _b64_to_pixbuf(data['pixbuf'])

        m = data['mouth']
        mouth_pixbuf = _b64_to_pixbuf(m['pixbuf'])
        self.mouth = Mouth()
        self.mouth.from_values(m['x'], m['y'], m['w'], m['h'], mouth_pixbuf)

        return self

    def clone(self):
        new = Status()
        new.voice = self.voice
        new.pitch = self.pitch
        new.rate = self.rate
        new.pixbuf = self.pixbuf
        new.left_eye = self.left_eye
        new.right_eye = self.right_eye
        new.mouth = self.mouth
        return new

    def get_args(self):
        return [self.pixbuf, self.left_eye, self.right_eye, self.mouth]


class View(Gtk.DrawingArea):
    def __init__(self, pixbuf, left_eye, right_eye, mouth,
                 fill_color=style.COLOR_BUTTON_GREY):
        Gtk.DrawingArea.__init__(self)

        self.status = Status()
        self._color = fill_color
        self.status.left_eye = left_eye
        self.status.right_eye = right_eye
        self.status.mouth = mouth
        self.status.pixbuf = pixbuf

        self._buffers = []
        self._buffer_size = 256
        self._main_buffers = []
        self._newest_buffer = []
        self._volume = 0
        self._look_x = None
        self._look_y = None

        self._audio = speech.get_speech()
        self._audio.connect('peak', self.__peak_cb)
        self._pending = None

        self.connect('draw', self.__draw_cb)

    def __draw_cb(self, widget, cr):
        bounds = widget.get_allocation()

        offset_x = (bounds.width - self.status.pixbuf.get_width()) // 2
        offset_y = (bounds.height - self.status.pixbuf.get_height()) // 2

        # Background Color
        cr.rectangle(0, 0, bounds.width, bounds.height)
        cr.set_source_rgba(*self._color.get_rgba())
        cr.fill()

        # Face Pixbuf
        cr.rectangle(offset_x, offset_y, bounds.width, bounds.height)
        Gdk.cairo_set_source_pixbuf(cr, self.status.pixbuf, offset_x, offset_y)
        cr.fill()

        # Mouth
        volume = min(self._volume / 30000.0, 1.0)

        # Draw a background for when the mouth moves
        cr.rectangle(offset_x + self.status.mouth.x,
                     offset_y + self.status.mouth.y,
                     self.status.mouth.w,
                     self.status.mouth.h)
        cr.set_source_rgba(*self._color.get_rgba())
        cr.fill()

        volume_offset = 100.0 * volume
        cr.rectangle(offset_x + self.status.mouth.x,
                     offset_y + self.status.mouth.y + volume_offset,
                     self.status.mouth.w,
                     self.status.mouth.h)
        Gdk.cairo_set_source_pixbuf(cr, self.status.mouth.pixbuf,
                                    offset_x + self.status.mouth.x,
                                    offset_y + self.status.mouth.y
                                    + volume_offset)
        cr.fill()

        # Eye centers
        for eye in (self.status.left_eye, self.status.right_eye):
            cr.arc(eye.center[0] + offset_x, eye.center[1] + offset_y,
                   eye.circ, 0, 2 * math.pi)
            cr.set_source_rgb(1.0, 1.0, 1.0)
            cr.fill()

            if self._look_x is None or self._look_y is None:
                look_x = eye.center[0] + offset_x + bounds.x
                look_y = eye.center[1] + offset_y + bounds.y
                x, y, circ = self._compute_pupil(eye, offset_x, offset_y,
                                                 look_x, look_y)
            else:
                x, y, circ = self._compute_pupil(eye, offset_x, offset_y,
                                                 self._look_x, self._look_y)
            cr.arc(x - bounds.x, y - bounds.y, circ, 0, 2 * math.pi)
            cr.set_source_rgb(0.0, 0.0, 0.0)
            cr.fill()

    # Thanks to xeyes :)
    def _compute_pupil(self, eye, offset_x, offset_y, look_x, look_y):
        CIRC = eye.circ // _EYE_CIRCUMFERENCE
        EYE_X, EYE_Y = self.translate_coordinates(
            self.get_toplevel(),
            int(eye.center[0] + offset_x),
            int(eye.center[1] + offset_y))
        EYE_HWIDTH = CIRC
        EYE_HHEIGHT = CIRC
        BALL_DIST = EYE_HWIDTH // (eye.circ // _BALL_DIST_CIRC_RATIO * 4)

        dx = look_x - EYE_X
        dy = look_y - EYE_Y

        if dx or dy:
            angle = math.atan2(dy, dx)
            cosa = math.cos(angle)
            sina = math.sin(angle)
            h = math.hypot(EYE_HHEIGHT * cosa, EYE_HWIDTH * sina)
            x = (EYE_HWIDTH * EYE_HHEIGHT) * cosa / h
            y = (EYE_HWIDTH * EYE_HHEIGHT) * sina / h
            dist = BALL_DIST * math.hypot(x, y)

            if dist < math.hypot(dx, dy):
                dx = dist * cosa
                dy = dist * sina

        return dx + EYE_X, dy + EYE_Y, CIRC

    def __peak_cb(self, me, volume):
        self._volume = volume
        self.queue_draw()

    def set_border_state(self, state):
        pass

    def look_ahead(self):
        self._look_x = None
        self._look_y = None
        self.queue_draw()

    def look_at(self, pos=None):
        if pos is None:
            display = Gdk.Display.get_default()
            screen, self._look_x, self._look_y, mods = display.get_pointer()
        else:
            self._look_x, self._look_y = pos
        self.queue_draw()

    def update(self, status=None):
        pass

    def set_voice(self, voice):
        self.status.voice = voice
        self.say_notification(voice.friendlyname)

    def say(self, something):
        self._audio.speak(self._pending or self.status, something)

    def say_notification(self, something):
        status = (self._pending or self.status).clone()
        status.voice = voice.defaultVoice()
        self._audio.speak(status, something)

    def shut_up(self):
        self._audio.stop_sound_device()
