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


import sys
import os
from urllib import (quote, unquote)
import subprocess
import random
from sugar.activity import activity
from sugar.datastore import datastore
from sugar.presence import presenceservice
import logging 
import gtk
import gobject
import pango
from gettext import gettext as _

# try:
#     sys.path.append('/usr/lib/python2.4/site-packages') # for speechd
#     import speechd.client
# except:
#     print "Speech-dispatcher not found."

from sugar.graphics.toolbutton import ToolButton
from sugar.graphics.toolcombobox import ToolComboBox
from sugar.graphics.combobox import ComboBox

import pygst
pygst.require("0.10")
import gst

import audio
import eye
import glasses
import mouth
import voice
import fft_mouth
import waveform_mouth

PITCH_MAX = 100
RATE_MAX = 100

class View(gtk.VBox):
    def __init__(self):
        gtk.VBox.__init__(self, homogeneous=False)

        #self.voice = random.choice(self.voices.values())
        self.voice = voice.defaultVoice()
        self.pitch = PITCH_MAX/2
        self.rate = RATE_MAX/2

        self._audio = audio.AudioGrab()
        self._synth = None
        # try:
        #     self._synth = speechd.client.SSIPClient("Speak.activity")
        #     try:
        #         # Try some speechd v0.6.6 features
        #         print "Output modules:", self._synth.list_output_modules()
        #         print "Voices:", self._synth.list_synthesis_voices()
        #     except:
        #         pass
        # except:
        #     self._synth = None
        #     print "Falling back to espeak command line tool."

        # make an empty box for some eyes
        self._eyes = None
        self._eyebox = gtk.HBox()
        self._eyebox.show()
        
        # make an empty box to put the mouth in
        self._mouth = None
        self._mouthbox = gtk.HBox()
        self._mouthbox.show()
        
        # layout the screen
        self.pack_start(self._eyebox, expand=False)
        self.pack_start(self._mouthbox)
        
    def look_ahead(self):
        map(lambda e: e.look_ahead(), self._eyes)

    def look_at(self, x, y):
        map(lambda e, x=x, y=y: e.look_at(x,y), self._eyes)

    def implant_eyes(self, klass, number):
        if self._eyes:
            for eye in self._eyes:
                self._eyebox.remove(eye)

        self._eyes = []

        for i in range(int(number)):
            eye = klass()
            self._eyes.append(eye)
            self._eyebox.pack_start(eye)
            eye.set_size_request(300,300)
            eye.show()

    def implant_mouth(self, klass):
        if self._mouth:
            self._mouthbox.remove(self._mouth)

        self._mouth = klass(self._audio)
        self._mouth.show()
        self._mouthbox.add(self._mouth)

        # enable mouse move events so we can track the eyes while the mouse is over the mouth
        #self._mouth.add_events(gtk.gdk.POINTER_MOTION_MASK)

    def say(self, something):
        if self._audio is None:
            return
        
        logging.debug('%s: %s' % (self.voice.name, something))
        pitch = int(self.pitch)
        rate = int(self.rate)

        if self._synth is not None:
            # speechd uses -100 to 100
            pitch = pitch*2 - 100
            # speechd uses -100 to 100
            rate = rate*2 - 100

            self._synth.set_rate(rate)
            self._synth.set_pitch(pitch)
            self._synth.set_language(self.voice.language)
            self._synth.speak(something) #, callback=self._synth_cb)
        else:
            # espeak uses 0 to 99
            pitch = pitch
            # espeak uses 80 to 370
            rate = 80 + (370-80) * rate / 100

            logging.error(">> %d:%d" %(pitch, rate))

            # ideally we would stream the audio instead of writing to disk each time...
            wavpath = "/tmp/speak.wav"
            subprocess.call(["espeak", "-w", wavpath, "-p", str(pitch), "-s", str(rate), "-v", self.voice.name, something], stdout=subprocess.PIPE)
            self._audio.playfile(wavpath)
    
    def quiet(self):
        self._audio.stop_sound_device()

    def verbose(self):
        self._audio.restart_sound_device()
