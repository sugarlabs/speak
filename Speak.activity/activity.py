# coding: UTF8

import commands, subprocess
import random
from sugar.activity import activity
from sugar.datastore import datastore
from sugar.presence import presenceservice
import logging 
import sys, os
import gtk
import gobject
import pango

import pygst
pygst.require("0.10")
import gst

import audio
import eye
import mouth

class SpeakActivity(activity.Activity):
    def __init__(self, handle):
        
        activity.Activity.__init__(self, handle)
        bounds = self.get_allocation()

        toolbox = activity.ActivityToolbox(self)
        self.set_toolbox(toolbox)
        toolbox.show()

        self.entry = gtk.Entry()
        self.entry.set_editable(True)
        self.entry.connect('activate', self.entry_activate_cb)
        self.input_font = pango.FontDescription(str='sans bold 24')
        self.entry.modify_font(self.input_font)

        self.eyes = [eye.Eye(), eye.Eye()]
        eyeBox = gtk.HBox()
        eyeBox.pack_start(self.eyes[0])
        eyeBox.pack_start(self.eyes[1])
        map(lambda e: e.set_size_request(300,300), self.eyes)
        
        self.ACTIVE = True
        self.connect( "notify::active", self._activeCb )
        self.audio = audio.AudioGrab(datastore, self._jobject)
        self.mouth = mouth.Mouth(self.audio)
        
        box = gtk.VBox(homogeneous=False)
        box.pack_start(eyeBox, expand=False)
        box.pack_start(self.mouth)
        box.pack_start(self.entry, expand=False)
        
        self.set_canvas(box)
        box.show_all()

        self.entry.grab_focus()

        gobject.timeout_add(100, self._timeout_cb)
        
        presenceService = presenceservice.get_instance()
        xoOwner = presenceService.get_owner()
        self.say("Hi %s, my name is Otto.  Type something." % xoOwner.props.nick)

    def _timeout_cb(self):
        self.mouth.queue_draw();
        return True

    def entry_activate_cb(self, entry):
        text = entry.props.text
        if text:
            self.say(text)
            entry.props.text = ''
        
    def speak(self, widget, data=None):
        self.say(random.choice(["Let's go to Annas","Hi Opal, how are you?"]))
    
    def say(self, something):
        wavpath = "/tmp/speak.wav"
        subprocess.call(["espeak", "-w", wavpath, something])
        #subprocess.call(["playwave", wavpath])
        self.audio.playfile(wavpath)
    
    def _activeCb( self, widget, pspec ):
        if (not self.props.active and self.ACTIVE):
            self.audio.stop_sound_device()
        elif (self.props.active and not self.ACTIVE):
            self.audio.restart_sound_device()
        self.ACTIVE = self.props.active

    def on_quit(self, data=None):
        self.audio.on_quit()    

# activate gtk threads when this module loads
gtk.gdk.threads_init()
