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
import cjson

from gi.repository import Gtk
from gi.repository import Gdk

import sugar3.graphics.style as style

import espeak
import eye
import glasses
from mouth import Mouth
from mouth import FFTMouth
from mouth import WaveformMouth
import voice

logger = logging.getLogger('speak')

FACE_PAD = 2


class Status():
    def __init__(self):
        self.voice = voice.defaultVoice()
        self.pitch = espeak.PITCH_MAX / 2
        self.rate = espeak.RATE_MAX / 2

        self.eyes = [eye.Eye] * 2
        self.mouth = Mouth

    def serialize(self):
        eyes = {eye.Eye: 1, glasses.Glasses: 2}
        
        mouths = {Mouth: 1,
            FFTMouth: 2,
            WaveformMouth: 3}

        return cjson.encode({
            'voice': {'language': self.voice.language,
            'name': self.voice.name},
            'pitch': self.pitch,
            'rate': self.rate,
            'eyes': [eyes[i] for i in self.eyes],
            'mouth': mouths[self.mouth]})

    def deserialize(self, buf):
        eyes = {1: eye.Eye, 2: glasses.Glasses}
        
        mouths = {1: Mouth,
            2: FFTMouth,
            3: WaveformMouth}

        data = cjson.decode(buf)
        self.voice = voice.Voice(data['voice']['language'],
                data['voice']['name'])
        self.pitch = data['pitch']
        self.rate = data['rate']
        self.eyes = [eyes[i] for i in data['eyes']]
        self.mouth = mouths[data['mouth']]

        return self

    def clone(self):
        new = Status()
        new.voice = self.voice
        new.pitch = self.pitch
        new.rate = self.rate
        new.eyes = self.eyes
        new.mouth = self.mouth
        return new


class View(Gtk.EventBox):
    """Face."""
    
    def __init__(self, fill_color=style.COLOR_BUTTON_GREY):
        Gtk.EventBox.__init__(self)
        
        self.status = Status()
        self.fill_color = fill_color
        self.modify_bg(0, self.fill_color.get_gdk_color())
        
        self._audio = espeak.AudioGrab()
        
        self._eyes = []
        self._eyebox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        
        self._mouth = None
        self._mouthbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        
        box.pack_start(self._eyebox, True, True, 0)
        box.pack_start(self._mouthbox, True, True, 0)
        
        self.add(box)
        self.show_all()

    def look_ahead(self):
        """ Look. . ."""
        
        if self._eyes:
            map(lambda e: e.look_ahead(), self._eyes)
            
    def look_at(self, pos=None):
        """ Look. . ."""
        
        if self._eyes:
            if pos is None:
                display = Gdk.Display.get_default()
                screen, x, y, modifiers = display.get_pointer()
            else:
                x, y = pos
            map(lambda e, x=x, y=y: e.look_at(x, y), self._eyes)
            
    def update(self, status=None):
        """ Re packaged the mouth and eyes according to quantity."""
        
        if status: self.status = status
        
        for eye in self._eyes:
            self._eyebox.remove(eye)
            
        for child in self._mouthbox.get_children():
            self._mouthbox.remove(child)
            
        self._eyes = []
        for i in self.status.eyes:
            eye = i(self.fill_color)
            self._eyes.append(eye)
            
        for eye in self._eyes:
            self._eyebox.pack_start(eye, True, True, 0)
            
        self._mouth = self.status.mouth(self._audio, self.fill_color)
        self._mouthbox.pack_start(self._mouth, True, True, 0)
        
        self.show_all()

    def set_voice(self, voice):
        self.status.voice = voice
        self.say_notification(voice.friendlyname)

    def say(self, something):
        self._audio.speak(self.status, something)

    def say_notification(self, something):
        status = self.status.clone()
        status.voice = voice.defaultVoice()
        self._audio.speak(status, something)

    def shut_up(self):
        self._audio.stop_sound_device()
