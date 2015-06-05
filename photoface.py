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
import cStringIO
from struct import unpack

import gtk
import numpy.core
import sugar.graphics.style as style

import voice
import local_espeak as espeak
from faceselect import Eye
from faceselect import Mouth
from face import remove_curses

logger = logging.getLogger('speak')


_EYE_CIRCUMFERENCE = 3
_BALL_DIST_CIRC_RATIO = 27


def _b64_to_pixbuf(b64):
    data = base64.b64decode(b64)
    path = '/tmp/{}.jpeg'.format(uuid.uuid4())

    with open(path, 'wb') as f:
        f.write(data)
    pixbuf = gtk.gdk.pixbuf_new_from_file(path)

    os.remove(path)
    return pixbuf


class Status(object):

    def __init__(self):
        self.voice = voice.defaultVoice()
        self.pitch = espeak.PITCH_MAX / 2
        self.rate = espeak.RATE_MAX / 2

    def serialize(self):
        fake_file = cStringIO.StringIO()
        self.pixbuf.save_to_callback(fake_file.write, 'jpeg')
        pixbuf_b64 = base64.b64encode(fake_file.getvalue())

        fake_file = cStringIO.StringIO()
        self.mouth.pixbuf.save_to_callback(fake_file.write, 'jpeg')
        mouth_pixbuf_b64 = base64.b64encode(fake_file.getvalue())

        mouth_dict = self.mouth.__dict__
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


class View(gtk.DrawingArea):
    def __init__(self, pixbuf, left_eye, right_eye, mouth,
                 fill_color=style.COLOR_BUTTON_GREY):
        gtk.DrawingArea.__init__(self)


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

        self._audio = espeak.AudioGrab()
        self._audio.connect('new-buffer', self.__new_buffer_cb)
        self._pending = None

        self.connect('expose-event', self.__draw_cb)

    def _redraw(self):
        alloc = self.get_allocation()
        self.queue_draw_area(0, 0, alloc.width, alloc.height)

    def __draw_cb(self, widget, cr):
        cr = widget.window.cairo_create()
        alloc = widget.get_allocation()

        offset_x = (alloc.width - self.status.pixbuf.get_width()) / 2
        offset_y = (alloc.height - self.status.pixbuf.get_height()) / 2

        # Background Color
        cr.rectangle(0, 0, alloc.width, alloc.height)
        cr.set_source_color(self._color.get_gdk_color())
        cr.fill()

        # Face Pixbuf
        cr.rectangle(offset_x, offset_y, alloc.width, alloc.height)
        cr.set_source_pixbuf(self.status.pixbuf, offset_x, offset_y)
        cr.fill()

        # Mouth
        self._process_buffer()
        volume = min(self._volume / 30000.0, 1.0)

        # Draw a background for when the mouth moves
        cr.rectangle(offset_x + self.status.mouth.x,
                     offset_y + self.status.mouth.y,
                     self.status.mouth.w,
                     self.status.mouth.h)
        cr.set_source_color(self._color.get_gdk_color())
        cr.fill()

        volume_offset = 100.0 * volume
        cr.rectangle(offset_x + self.status.mouth.x,
                     offset_y + self.status.mouth.y + volume_offset,
                     self.status.mouth.w,
                     self.status.mouth.h)
        cr.set_source_pixbuf(self.status.mouth.pixbuf,
                             offset_x + self.status.mouth.x,
                             offset_y + self.status.mouth.y + volume_offset)
        cr.fill()

        # Eye centers
        for eye in (self.status.left_eye, self.status.right_eye):
            cr.arc(eye.center[0] + offset_x, eye.center[1] + offset_y,
                   eye.circ, 0, 2 * math.pi)
            cr.set_source_rgb(1.0, 1.0, 1.0)
            cr.fill()

            if self._look_x is None or self._look_y is None:
                look_x = eye.center[0] + offset_x + alloc.x
                look_y = eye.center[1] + offset_y + alloc.y
                x, y, circ = self._compute_pupil(eye, offset_x, offset_y,
                                                 look_x, look_y)
            else:
                x, y, circ = self._compute_pupil(eye, offset_x, offset_y,
                                                 self._look_x, self._look_y)
            cr.arc(x - alloc.x, y - alloc.y, circ, 0, 2 * math.pi)
            cr.set_source_rgb(0.0, 0.0, 0.0)
            cr.fill()

    # Thanks to xeyes :)
    def _compute_pupil(self, eye, offset_x, offset_y, look_x, look_y):
        CIRC = eye.circ / _EYE_CIRCUMFERENCE
        EYE_X, EYE_Y = self.translate_coordinates(
                self.get_toplevel(),
                int(eye.center[0] + offset_x),
                int(eye.center[1] + offset_y))
        EYE_HWIDTH = CIRC
        EYE_HHEIGHT = CIRC
        BALL_DIST = EYE_HWIDTH / (eye.circ / _BALL_DIST_CIRC_RATIO * 4)

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

    def _process_buffer(self):
        if len(self._main_buffers) == 0 or len(self._newest_buffer) == 0:
            self._volume = 0
        else:
            self._volume = numpy.core.max(self._main_buffers)

    def __new_buffer_cb(self, obj, buf):
        if len(buf) < 28:
            self._newest_buffer = []
        else:
            self._newest_buffer = list(
                unpack(str(int(len(buf)) / 2) + 'h', buf))
            self._main_buffers += self._newest_buffer
            if(len(self._main_buffers) > self._buffer_size):
                del self._main_buffers[0:(len(self._main_buffers) - \
                        self._buffer_size)]

        self._redraw()
        return True

    def set_border_state(self, state):
        pass

    def look_ahead(self):
        self._look_x = None
        self._look_y = None
        self._redraw()

    def look_at(self, pos=None):
        if pos is None:
            display = gtk.gdk.display_get_default()
            screen, self._look_x, self._look_y, mods = display.get_pointer()
        else:
            self._look_x, self._look_y = pos
        self._redraw()
        

    def update(self, status=None):
        pass

    def set_voice(self, voice):
        self.status.voice = voice
        self.say_notification(voice.friendlyname)

    def say(self, something):
        curse_free = remove_curses(something)
        self._audio.speak(self._pending or self.status, curse_free)

    def say_notification(self, something):
        status = (self._pending or self.status).clone()
        status.voice = voice.defaultVoice()
        self._audio.speak(status, something)

    def shut_up(self):
        self._audio.stop_sound_device()
