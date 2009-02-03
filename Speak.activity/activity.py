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

import eye
import glasses
import mouth
import fft_mouth
import waveform_mouth
import voice
import face
from toolbars import ChatToolbar
from chat import Chat

CHAT_TOOLBAR = 3

class SpeakActivity(activity.Activity):
    def __init__(self, handle):
        
        activity.Activity.__init__(self, handle)
        bounds = self.get_allocation()

        # pick a voice that espeak supports
        self.voices = voice.allVoices()

        # make an audio device for playing back and rendering audio
        self.connect( "notify::active", self._activeCb )

        # make a box to type into
        self.entrycombo = gtk.combo_box_entry_new_text()
        self.entrycombo.connect("changed", self._combo_changed_cb)
        self.entry = self.entrycombo.child
        self.entry.set_editable(True)
        self.entry.connect('activate', self._entry_activate_cb)
        self.entry.connect("key-press-event", self._entry_key_press_cb)
        self.input_font = pango.FontDescription(str='sans bold 24')
        self.entry.modify_font(self.input_font)

        self.face = face.View()
        self.face.show()

        # layout the screen
        box = gtk.VBox(homogeneous=False)
        box.pack_start(self.face)
        box.pack_start(self.entrycombo, expand=False)

        box.add_events(gtk.gdk.BUTTON_PRESS_MASK |
                       gtk.gdk.POINTER_MOTION_MASK)
        box.connect("motion_notify_event", self._mouse_moved_cb)
        box.connect("button_press_event", self._mouse_clicked_cb)

        # desktop
        self.notebook = gtk.Notebook()
        self.notebook.show()
        self.notebook.props.show_border = False
        self.notebook.props.show_tabs = False
        self.set_canvas(self.notebook)

        box.show_all()
        self.notebook.append_page(box)

        self.chat = Chat()
        self.chat.show_all()
        self.notebook.append_page(self.chat)

        # make some toolbars
        toolbox = activity.ActivityToolbox(self)
        self.set_toolbox(toolbox)
        toolbox.show()
        #activitybar = toolbox.get_activity_toolbar()
        toolbox.connect('current-toolbar-changed', self._toolbar_changed_cb)

        voicebar = self.make_voice_bar()
        toolbox.add_toolbar("Voice", voicebar)
        voicebar.show()
        
        facebar = self.make_face_bar()
        toolbox.add_toolbar("Face", facebar)
        facebar.show()
        
        chatbar = ChatToolbar()
        toolbox.add_toolbar(_('Chat'), chatbar)
        chatbar.show()

        # make the text box active right away
        self.entry.grab_focus()
        
        self.entry.connect("move-cursor", self._cursor_moved_cb)
        self.entry.connect("changed", self._cursor_moved_cb)

        # try to catch all mouse-moved events so the eyes will track wherever you go
        # this doesn't work for some reason I don't understand
        # it gets mouse motion over lots of stuff, but not sliders or comboboxes
        # import time
        # self.window.set_events(self.window.get_events() | gtk.gdk.POINTER_MOTION_MASK)
        # def event_filter(event, user_data=None):
        #     map(lambda w: w.queue_draw(), self.eyes)
        #     print time.asctime(), time.time(), event.get_coords(), event.get_root_coords()
        #     return gtk.gdk.FILTER_CONTINUE
        # self.window.add_filter(event_filter)
        # map(lambda c: c.forall(lambda w: w.add_events(gtk.gdk.POINTER_MOTION_MASK)), self.window.get_children())

        # start polling for mouse movement
        # self.mouseX = None
        # self.mouseY = None
        # def poll_mouse():
        #     display = gtk.gdk.display_get_default()
        #     screen, mouseX, mouseY, modifiers = display.get_pointer()
        #     if self.mouseX != mouseX or self.mouseY != mouseY:
        #         self.mouseX = mouseX
        #         self.mouseY = mouseY
        #         map(lambda w: w.queue_draw(), self.eyes)
        #     return True
        # gobject.timeout_add(100, poll_mouse)
        
        # say hello to the user
        presenceService = presenceservice.get_instance()
        xoOwner = presenceService.get_owner()
        self.face.say(_("Hello %s.  Type something.") % xoOwner.props.nick)

        # XXX do it after(possible) read_file() invoking
        # have to rely on calling read_file() from map_cb in sugar-toolkit
        self.connect_after('map', self.connect_to)

    def connect_to(self, widget):
        self.voice_combo.connect('changed', self.voice_changed_cb)
        self.pitchadj.connect("value_changed", self.pitch_adjusted_cb, self.pitchadj)
        self.rateadj.connect("value_changed", self.rate_adjusted_cb, self.rateadj)
        self.mouth_shape_combo.connect('changed', self.mouth_changed_cb, False)
        self.mouth_changed_cb(self.mouth_shape_combo, True)
        self.numeyesadj.connect("value_changed", self.eyes_changed_cb, False)
        self.eye_shape_combo.connect('changed', self.eyes_changed_cb, False)
        self.eyes_changed_cb(None, True)
        self.face.look_ahead()

    def write_file(self, file_path):
        f = open(file_path, "w")
        f.write("speak file format v1\n")
        f.write("voice=%s\n" % quote(self.face.status.voice.friendlyname))
        f.write("text=%s\n" % quote(self.entry.props.text))
        history = map(lambda i: i[0], self.entrycombo.get_model())
        f.write("history=[%s]\n" % ",".join(map(quote, history)))
        f.write("pitch=%d\n" % self.pitchadj.value)
        f.write("rate=%d\n" % self.rateadj.value)
        f.write("mouth_shape=%s\n" % quote(self.mouth_shape_combo.get_active_item()[1]))
        f.write("eye_shape=%s\n" % quote(self.eye_shape_combo.get_active_item()[1]))
        f.write("num_eyes=%d\n" % self.numeyesadj.value)
        f.close()
        
        f = open(file_path, "r")
        print f.readlines()
        f.close()
        
        
    def read_file(self, file_path):
        
        def pick_combo_item(combo, name):
            index = 0
            model = combo.get_model()
            for item in model:
                if item[1] == name:
                    combo.set_active(index)
                    return True
                index += 1
            return False
        
        f = open(file_path, "r")
        header = f.readline().strip()
        if header != "speak file format v1":
            print "Reading format from the future '%s', will try my best." % header
        for line in f.readlines():
            line = line.strip()
            index = line.find('=')
            key = line[:index]
            value = line[index+1:]
            if key == 'voice':
                voice_name = unquote(value)
                found = pick_combo_item(self.voice_combo, voice_name)
                if not found:
                    print "Unrecognized voice name: %s" % voice_name
            elif key == 'text':
                self.entry.props.text = unquote(value)
            elif key == 'history':
                if value[0]=='[' and value[-1]==']':
                    for item in value[1:-1].split(','):
                        self.entrycombo.append_text(unquote(item))
                else:
                    print "Unrecognized history: %s" % value
            elif key == 'pitch':
                self.pitchadj.value = int(value)
            elif key == 'rate':
                self.rateadj.value = int(value)
            elif key == 'mouth_shape':
                mouth_name = unquote(value)
                found = pick_combo_item(self.mouth_shape_combo, mouth_name)
                if not found:
                    print "Unrecognized mouth shape: %s" % mouth_name
            elif key == 'eye_shape':
                eye_name = unquote(value)
                found = pick_combo_item(self.eye_shape_combo, eye_name)
                if not found:
                    print "Unrecognized eye shape: %s" % eye_name
            elif key == 'num_eyes':
                self.numeyesadj.value = int(value)
            else:
                print "Ignoring unrecognized line: %s" % line
        f.close()

    def _cursor_moved_cb(self, entry, *ignored):
        # make the eyes track the motion of the text cursor
        index = entry.props.cursor_position
        layout = entry.get_layout()
        pos = layout.get_cursor_pos(index)
        x = pos[0][0] / pango.SCALE - entry.props.scroll_offset
        y = entry.get_allocation().y
        self.face.look_at(x, y)

    def get_mouse(self):
        display = gtk.gdk.display_get_default()
        screen, mouseX, mouseY, modifiers = display.get_pointer()
        return mouseX, mouseY

    def _mouse_moved_cb(self, widget, event):
        # make the eyes track the motion of the mouse cursor
        x,y = self.get_mouse()
        self.face.look_at(x, y)

    def _mouse_clicked_cb(self, widget, event):
        pass

    def make_voice_bar(self):
        voicebar = gtk.Toolbar()
        
        # button = ToolButton('change-voice')
        # button.set_tooltip("Change Voice")
        # button.connect('clicked', self.change_voice_cb)
        # voicebar.insert(button, -1)
        # button.show()
        
        self.voice_combo = ComboBox()
        voicenames = self.voices.keys()
        voicenames.sort()
        for name in voicenames:
            self.voice_combo.append_item(self.voices[name], name)
        self.voice_combo.set_active(voicenames.index(
            self.face.status.voice.friendlyname))
        combotool = ToolComboBox(self.voice_combo)
        voicebar.insert(combotool, -1)
        combotool.show()

        self.pitchadj = gtk.Adjustment(self.face.status.pitch, 0,
                face.PITCH_MAX, 1, face.PITCH_MAX/10, 0)
        pitchbar = gtk.HScale(self.pitchadj)
        pitchbar.set_draw_value(False)
        #pitchbar.set_inverted(True)
        pitchbar.set_update_policy(gtk.UPDATE_DISCONTINUOUS)
        pitchbar.set_size_request(240,15)
        pitchtool = gtk.ToolItem()
        pitchtool.add(pitchbar)
        pitchtool.show()
        voicebar.insert(pitchtool, -1)
        pitchbar.show()

        self.rateadj = gtk.Adjustment(self.face.status.rate, 0, face.RATE_MAX,
                1, face.RATE_MAX/10, 0)
        ratebar = gtk.HScale(self.rateadj)
        ratebar.set_draw_value(False)
        #ratebar.set_inverted(True)
        ratebar.set_update_policy(gtk.UPDATE_DISCONTINUOUS)
        ratebar.set_size_request(240,15)
        ratetool = gtk.ToolItem()
        ratetool.add(ratebar)
        ratetool.show()
        voicebar.insert(ratetool, -1)
        ratebar.show()
        
        return voicebar

    def voice_changed_cb(self, combo):
        self.face.status.voice = combo.props.value
        self.face.say(self.face.status.voice.friendlyname)

    def pitch_adjusted_cb(self, get, data=None):
        self.face.status.pitch = get.value
        self.face.say(_("pitch adjusted"))

    def rate_adjusted_cb(self, get, data=None):
        self.face.status.rate = get.value
        self.face.say(_("rate adjusted"))

    def make_face_bar(self):
        facebar = gtk.Toolbar()

        self.numeyesadj = None
        
        self.mouth_shape_combo = ComboBox()
        self.mouth_shape_combo.append_item(mouth.Mouth, _("Simple"))
        self.mouth_shape_combo.append_item(waveform_mouth.WaveformMouth, _("Waveform"))
        self.mouth_shape_combo.append_item(fft_mouth.FFTMouth, _("Frequency"))
        self.mouth_shape_combo.set_active(0)
        combotool = ToolComboBox(self.mouth_shape_combo)
        facebar.insert(combotool, -1)
        combotool.show()

        self.eye_shape_combo = ComboBox()
        self.eye_shape_combo.append_item(eye.Eye, _("Round"))
        self.eye_shape_combo.append_item(glasses.Glasses, _("Glasses"))
        combotool = ToolComboBox(self.eye_shape_combo)
        facebar.insert(combotool, -1)
        combotool.show()

        self.numeyesadj = gtk.Adjustment(2, 1, 5, 1, 1, 0)
        numeyesbar = gtk.HScale(self.numeyesadj)
        numeyesbar.set_draw_value(False)
        numeyesbar.set_update_policy(gtk.UPDATE_DISCONTINUOUS)
        numeyesbar.set_size_request(240,15)
        numeyestool = gtk.ToolItem()
        numeyestool.add(numeyesbar)
        numeyestool.show()
        facebar.insert(numeyestool, -1)
        numeyesbar.show()

        self.eye_shape_combo.set_active(0)
        
        return facebar

    def mouth_changed_cb(self, combo, quiet):
        self.face.status.mouth = combo.props.value
        self.face.update()

        # this SegFaults: self.face.say(combo.get_active_text())
        if not quiet:
            self.face.say(_("mouth changed"))

    def eyes_changed_cb(self, ignored, quiet):
        if self.numeyesadj is None:
            return

        self.face.status.eyes = [self.eye_shape_combo.props.value] \
                * int(self.numeyesadj.value)
        self.face.update()

        # this SegFaults: self.face.say(self.eye_shape_combo.get_active_text())
        if not quiet:
            self.face.say(_("eyes changed"))
        
    def _combo_changed_cb(self, combo):
        # when a new item is chosen, make sure the text is selected
        if not self.entry.is_focus():
            self.entry.grab_focus()
            self.entry.select_region(0,-1)

    def _entry_key_press_cb(self, combo, event):
        # make the up/down arrows navigate through our history
        keyname = gtk.gdk.keyval_name(event.keyval)
        if keyname == "Up":
            index = self.entrycombo.get_active()
            if index>0:
                index-=1
            self.entrycombo.set_active(index)
            self.entry.select_region(0,-1)
            return True
        elif keyname == "Down":
            index = self.entrycombo.get_active()
            if index<len(self.entrycombo.get_model())-1:
                index+=1
            self.entrycombo.set_active(index)
            self.entry.select_region(0,-1)
            return True
        return False

    def _entry_activate_cb(self, entry):
        # the user pressed Return, say the text and clear it out
        text = entry.props.text
        if text:
            self.face.look_ahead()
            
            # speak the text
            self.face.say(text)
            
            # add this text to our history unless it is the same as the last item
            history = self.entrycombo.get_model()
            if len(history)==0 or history[-1][0] != text:
                self.entrycombo.append_text(text)
                # don't let the history get too big
                while len(history)>20:
                    self.entrycombo.remove_text(0)
                # select the new item
                self.entrycombo.set_active(len(history)-1)
            # select the whole text
            entry.select_region(0,-1)

    def _synth_cb(self, callback_type, index_mark=None):
        print "synth callback:", callback_type, index_mark
        
    def _activeCb( self, widget, pspec ):
        # only generate sound when this activity is active
        if not self.props.active:
            self.face.quiet()
        else:
            self.face.verbose()

    def _toolbar_changed_cb(self, widget, index):
        if index == CHAT_TOOLBAR:
            self.chat.update(self.face.status)
            self.notebook.set_current_page(1)
        else:
            self.notebook.set_current_page(0)

    #def on_quit(self, data=None):
    #    self.audio.on_quit()    

# activate gtk threads when this module loads
gtk.gdk.threads_init()
