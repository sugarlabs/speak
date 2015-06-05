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
# New face features
# Copyright (C) 2014  Walter Bender
# Copyright (C) 2014  Sam Parkinson
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
import json

import sugar.graphics.style as style

import local_espeak as espeak
import eye
import glasses
import eyelashes
import halfmoon
import sleepy
import sunglasses
import wireframes
import mouth
import voice
import fft_mouth
import waveform_mouth

logger = logging.getLogger('speak')

FACE_PAD = style.GRID_CELL_SIZE

class Status:
    def __init__(self):
        self.voice = voice.defaultVoice()
        self.pitch = espeak.PITCH_MAX / 2
        self.rate = espeak.RATE_MAX / 2

        self.eyes = [eye.Eye] * 2
        self.mouth = mouth.Mouth

    def serialize(self):
        eyes    = { eye.Eye: 1,
                    glasses.Glasses: 2,
                    eyelashes.Eyelashes: 3,
                    halfmoon.Halfmoon: 4,
                    sunglasses.Sunglasses: 5,
                    wireframes.Wireframes: 6,
                    sleepy.Sleepy: 7}
        mouths  = { mouth.Mouth: 1,
                    fft_mouth.FFTMouth: 2,
                    waveform_mouth.WaveformMouth: 3 }

        return json.dumps({
            'voice': {'language': self.voice.language,
                        'name': self.voice.name},
            'pitch': self.pitch,
            'rate': self.rate,
            'eyes': [eyes[i] for i in self.eyes],
            'mouth': mouths[self.mouth]})

    def deserialize(self, buf):
        eyes    = { 1: eye.Eye,
                    2: glasses.Glasses,
                    3: eyelashes.Eyelashes,
                    4: halfmoon.Halfmoon,
                    5: sunglasses.Sunglasses,
                    6: wireframes.Wireframes,
                    7: sleepy.Sleepy}
        mouths  = { 1: mouth.Mouth,
                    2: fft_mouth.FFTMouth,
                    3: waveform_mouth.WaveformMouth }

        data = json.loads(buf)
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


class View(gtk.EventBox):
    def __init__(self, fill_color=style.COLOR_BUTTON_GREY):
        gtk.EventBox.__init__(self)

        self.status = Status()
        self.fill_color = fill_color

        self.connect('size-allocate', self._size_allocate_cb)

        self._audio = espeak.AudioGrab()

        # make an empty box for some eyes
        self._eyes = None
        self._eyebox = gtk.HBox()
        self._eyebox.show()

        # make an empty box to put the mouth in
        self._mouth = None
        self._mouthbox = gtk.HBox()
        self._mouthbox.show()

        # layout the screen
        self._box = gtk.VBox(homogeneous=False)
        self._box.pack_start(self._eyebox)
        self._box.pack_start(self._mouthbox, False)
        self._box.set_border_width(FACE_PAD)
        self.modify_bg(gtk.STATE_NORMAL, self.fill_color.get_gdk_color())
        self.add(self._box)

        self._peding = None
        self.connect('map', self.__map_cb)

        self.update()

    def set_border_state(self, state):
        if state:
            self._box.set_border_width(FACE_PAD)
        else:
            self._box.set_border_width(0)

    def __map_cb(self, widget):
        if self._peding:
            self.update(self._peding)
            self._peding = None

    def look_ahead(self):
        if self._eyes:
            map(lambda e: e.look_ahead(), self._eyes)

    def look_at(self, pos=None):
        if self._eyes:
            if pos is None:
                display = gtk.gdk.display_get_default()
                screen_, x, y, modifiers_ = display.get_pointer()
            else:
                x, y = pos
            map(lambda e, x=x, y=y: e.look_at(x, y), self._eyes)

    def update(self, status = None):
        if not status:
            status = self.status
        else:
            if not self.flags() & gtk.MAPPED:
                self._peding = status
                return
            self.status = status

        if self._eyes:
            for eye in self._eyes:
                self._eyebox.remove(eye)
        if self._mouth:
            self._mouthbox.remove(self._mouth)

        self._eyes = []

        for e, i in enumerate(status.eyes):
            eye = i(self.fill_color)
            if eye.has_left_center_right():
                if e == 0:
                    if len(status.eyes) > 1:  # Left
                        eye.set_eye(0)
                    else:
                        eye.set_eye(1)  # Center if only 1 eye
                elif e == len(status.eyes) - 1:  # Right
                    eye.set_eye(2)
                else:  # Center
                    eye.set_eye(1)
            self._eyes.append(eye)
            if eye.has_padding():
                self._eyebox.pack_start(eye, padding=int(FACE_PAD / 4))
            else:
                self._eyebox.pack_start(eye)
            eye.show()

        self._mouth = status.mouth(self._audio, self.fill_color)
        self._mouth.show()
        self._mouthbox.add(self._mouth)

        # enable mouse move events so we can track the eyes while the
        # mouse is over the mouth
        # self._mouth.add_events(gtk.gdk.POINTER_MOTION_MASK)

    def set_voice(self, voice):
        self.status.voice = voice
        self.say_notification(voice.friendlyname)

    def say(self, something):
        curse_free = remove_curses(something)
        self._audio.speak(self._peding or self.status, curse_free)

    def say_notification(self, something):
        status = (self._peding or self.status).clone()
        status.voice = voice.defaultVoice()
        self._audio.speak(status, something)

    def shut_up(self):
        self._audio.stop_sound_device()

    def _size_allocate_cb(self, widget, allocation):
        self._mouthbox.set_size_request(-1, int(allocation.height/2.5))


CURSES = ['fuck', 'fucks', 'fucking', 'fucker', 'fucked', 'fuckk', 'fuckks',
          'fuckking', 'fuckker', 'shit', 'shits', 'shitting', 'shitter',
          'shitt', 'shitts', 'cunt', 'cunts', 'cunting', 'cunted', 'cuntt',
          'cunnt', 'asshole', 'assholes', 'arsehole', 'arseholes', 'dickhead',
          'dickheads', 'shithead', 'shitheads', 'fuckhead', 'fuckheads',
          'fuckwit', 'fuckwits', 'twat', 'twatted', 'twatter', 'twatting',
          'kunt', 'kunts', 'kunting', 'kuntz', 'fuk', 'fukn', 'fuker', 'fukr',
          'fukker', 'fukkr', 'fuks', 'fukk', 'phuk', 'phukker', 'phukking',
          'fukin', 'piss', 'pissed', 'fag', 'fags', 'gaylord', 'gaylords',
          'pissing', 'poofter', 'softcock', 'wanker', 'wankers', 'shiiiit',
          'pisses', 'nigger', 'niggers', 'nigga', 'niggas', 'motherfuck',
          'mutherfuck', 'muthafuck', 'motherfuk', 'mutherfuk', 'muthafuk',
          'motherfucker', 'mutherfucker', 'muthafucker', 'motherfukr',
          'motherfuker', 'motherfukker', 'motherfukkr', 'mutherfukr',
          'mutherfukker', 'mutherfukkr', 'muthafukr', 'muthafukkr',
          'muthafuckr', 'shiit', 'motherfuckerz', 'mutherfuckerz',
          'mothafuckerz', 'motherfukrz', 'motherfukkrz', 'muthafukrz',
          'muthafuking', 'motherfucking', 'mothafucking', 'muthafuking',
          'mothafuking', 'motherfuking', 'mothafukking', 'muthafukking',
          'motherfukking']


def remove_curses(something):
    ''' Speak Swear Filter List '''
    curse_free = ''
    words = something.split()
    for word in words:
        if word in CURSES:
            curse_free += '#!#! '
        else:
            curse_free += word
            curse_free += ' '
    return curse_free
