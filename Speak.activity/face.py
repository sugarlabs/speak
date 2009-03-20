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


import logging 
import gtk
import cjson
from gettext import gettext as _

import sugar.graphics.style as style

import audio
import eye
import glasses
import mouth
import voice
import fft_mouth
import waveform_mouth

logger = logging.getLogger('speak')

FACE_PAD = 2

class Status:
    def __init__(self):
        self.voice = voice.defaultVoice()
        self.pitch = audio.PITCH_DEFAULT
        self.rate = audio.RATE_DEFAULT
        self.eyes = [eye.Eye] * 2
        self.mouth = mouth.Mouth

    def serialize(self):
        eyes    = { eye.Eye : 1,
                    glasses.Glasses : 2 }
        mouths  = { mouth.Mouth : 1,
                    fft_mouth.FFTMouth : 2,
                    waveform_mouth.WaveformMouth : 3 }

        return cjson.encode({
            'voice' : { 'language'  : self.voice.language,
                        'name'      : self.voice.name },
            'pitch' : self.pitch,
            'rate'  : self.rate,
            'eyes'  : [eyes[i] for i in self.eyes],
            'mouth' : mouths[self.mouth] })

    def deserialize(self, buf):
        eyes    = { 1: eye.Eye,
                    2: glasses.Glasses }
        mouths  = { 1: mouth.Mouth,
                    2: fft_mouth.FFTMouth,
                    3: waveform_mouth.WaveformMouth }

        data = cjson.decode(buf)
        self.voice = voice.Voice(data['voice']['language'],
                data['voice']['name'])
        self.pitch = data['pitch']
        self.rate = data['rate']
        self.eyes = [eyes[i] for i in data['eyes']]
        self.mouth = mouths[data['mouth']]

        return self

class View(gtk.EventBox):
    def __init__(self, fill_color=style.COLOR_BUTTON_GREY):
        gtk.EventBox.__init__(self)

        self.status = Status()
        self.fill_color = fill_color

        self.connect('size-allocate', self._size_allocate_cb)

        self._audio = audio.AudioGrab()

        # make an empty box for some eyes
        self._eyes = None
        self._eyebox = gtk.HBox()
        self._eyebox.show()
        
        # make an empty box to put the mouth in
        self._mouth = None
        self._mouthbox = gtk.HBox()
        self._mouthbox.show()
        
        # layout the screen
        box = gtk.VBox(homogeneous=False)
        box.pack_start(self._eyebox)
        box.pack_start(self._mouthbox, False)
        box.set_border_width(FACE_PAD)
        self.modify_bg(gtk.STATE_NORMAL, self.fill_color.get_gdk_color())
        self.add(box)

        self._mapped = False
        self._peding = None
        self.connect("map_event",self._map_event)

        self.update()
        
    def _map_event(self, widget, event):
        self._mapped = True
        if self._peding:
            self.update(self._peding)
            self._peding = None

    def look_ahead(self):
        if self._eyes:
            map(lambda e: e.look_ahead(), self._eyes)

    def look_at(self, x, y):
        if self._eyes:
            map(lambda e, x=x, y=y: e.look_at(x,y), self._eyes)

    def update(self, status = None):
        if not status:
            status = self.status
        else:
            if not self._mapped:
                self._peding = status
                return
            self.status = status

        if self._eyes:
            for eye in self._eyes:
                self._eyebox.remove(eye)
        if self._mouth:
            self._mouthbox.remove(self._mouth)

        self._eyes = []

        for i in status.eyes:
            eye = i(self.fill_color)
            self._eyes.append(eye)
            self._eyebox.pack_start(eye, padding=FACE_PAD)
            eye.show()

        self._mouth = status.mouth(self._audio, self.fill_color)
        self._mouth.show()
        self._mouthbox.add(self._mouth)

        # enable mouse move events so we can track the eyes while the mouse is over the mouth
        #self._mouth.add_events(gtk.gdk.POINTER_MOTION_MASK)

    def say(self, something):
        self._audio.speak(self._peding or self.status, something)
    
    def shut_up(self):
        self._audio.stop_sound_device()

    def _size_allocate_cb(self, widget, allocation):
        self._mouthbox.set_size_request(-1, int(allocation.height/2.5))
