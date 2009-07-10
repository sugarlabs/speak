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


from sugar.activity import activity
from sugar.presence import presenceservice
import logging 
import gtk
import gobject
import pango
import cjson
from gettext import gettext as _

from sugar.graphics.toolbutton import ToolButton
from port.widgets import ComboBox, ToolComboBox
from port.activity import SharedActivity

import eye
import glasses
import mouth
import fft_mouth
import waveform_mouth
import voice
import face
import brain
import chat
import espeak
from messenger import Messenger, SERVICE

logger = logging.getLogger('speak')

BOT_TOOLBAR = 3
CHAT_TOOLBAR = 4

class SpeakActivity(SharedActivity):
    def __init__(self, handle):
        self.notebook = gtk.Notebook()
        
        SharedActivity.__init__(self, self.notebook, SERVICE, handle)
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
        self.notebook.show()
        self.notebook.props.show_border = False
        self.notebook.props.show_tabs = False

        box.show_all()
        self.notebook.append_page(box)

        self.chat = chat.View()
        self.chat.show_all()
        self.notebook.append_page(self.chat)

        # make some toolbars
        self.toolbox = activity.ActivityToolbox(self)
        self.set_toolbox(self.toolbox)
        self.toolbox.show()
        #activitybar = toolbox.get_activity_toolbar()
        self.toolbox.connect('current-toolbar-changed', self._toolbar_changed_cb)

        voicebar = self.make_voice_bar()
        self.toolbox.add_toolbar(_('Voice'), voicebar)
        voicebar.show()
        
        facebar = self.make_face_bar()
        self.toolbox.add_toolbar(_('Face'), facebar)
        facebar.show()
        
        self.bot = brain.Toolbar(self)
        self.toolbox.add_toolbar(_('Robot'), self.bot)
        self.bot.show()

        chatbar = chat.Toolbar(self.chat)
        self.toolbox.add_toolbar(_('Chat'), chatbar)
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

    def new_instance(self):
        self.voice_combo.connect('changed', self.voice_changed_cb)
        self.pitchadj.connect("value_changed", self.pitch_adjusted_cb, self.pitchadj)
        self.rateadj.connect("value_changed", self.rate_adjusted_cb, self.rateadj)
        self.mouth_shape_combo.connect('changed', self.mouth_changed_cb, False)
        self.mouth_changed_cb(self.mouth_shape_combo, True)
        self.numeyesadj.connect("value_changed", self.eyes_changed_cb, False)
        self.eye_shape_combo.connect('changed', self.eyes_changed_cb, False)
        self.eyes_changed_cb(None, True)

        self.face.look_ahead()

        # say hello to the user
        presenceService = presenceservice.get_instance()
        xoOwner = presenceService.get_owner()
        self.face.say_notification(_("Hello %s.  Type something.") \
                % xoOwner.props.nick)

    def resume_instance(self, file_path):
        cfg = cjson.decode(file(file_path, 'r').read())

        status = self.face.status = face.Status().deserialize(cfg['status'])
        self.change_voice(status.voice.friendlyname, True)
        self.pitchadj.value = self.face.status.pitch
        self.rateadj.value = self.face.status.rate
        self.mouth_shape_combo.select(status.mouth)
        self.eye_shape_combo.select(status.eyes[0])
        self.numeyesadj.value = len(status.eyes)

        self.entry.props.text = cfg['text']
        for i in cfg['history']:
            self.entrycombo.append_text(i)

        self.new_instance()

    def save_instance(self, file_path):
        cfg = { 'status'  : self.face.status.serialize(),
                'text'    : self.entry.props.text,
                'history' : map(lambda i: i[0], self.entrycombo.get_model()) }
        file(file_path, 'w').write(cjson.encode(cfg))
        
    def share_instance(self, connection, is_initiator):
        self.chat.messenger = Messenger(connection, is_initiator, self.chat)

    def change_voice(self, voice, silent):
        self.voice_combo.select(voice,
                column=1,
                silent_cb=(silent and self.voice_changed_cb or None))
        self.face.status.voice = self.voice_combo.get_active_item()[0]

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
                espeak.PITCH_MAX, 1, espeak.PITCH_MAX/10, 0)
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

        self.rateadj = gtk.Adjustment(self.face.status.rate, 0, espeak.RATE_MAX,
                1, espeak.RATE_MAX/10, 0)
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
        self.face.say_notification(self.face.status.voice.friendlyname)

    def pitch_adjusted_cb(self, get, data=None):
        self.face.status.pitch = get.value
        self.face.say_notification(_("pitch adjusted"))

    def rate_adjusted_cb(self, get, data=None):
        self.face.status.rate = get.value
        self.face.say_notification(_("rate adjusted"))

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
            self.face.say_notification(_("mouth changed"))

    def eyes_changed_cb(self, ignored, quiet):
        if self.numeyesadj is None:
            return

        self.face.status.eyes = [self.eye_shape_combo.props.value] \
                * int(self.numeyesadj.value)
        self.face.update()

        # this SegFaults: self.face.say(self.eye_shape_combo.get_active_text())
        if not quiet:
            self.face.say_notification(_("eyes changed"))
        
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
            if self.toolbox.get_current_toolbar() == BOT_TOOLBAR:
                self.face.say(self.bot.respond(text))
            else:
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
            self.face.shut_up()
            self.chat.shut_up()

    def _toolbar_changed_cb(self, widget, index):
        if index == CHAT_TOOLBAR:
            self.face.shut_up()
            self.chat.update(self.face.status)
            self.notebook.set_current_page(1)
        else:
            self.chat.shut_up()
            self.notebook.set_current_page(0)
            if index == BOT_TOOLBAR:
                self.bot.update_voice()

# activate gtk threads when this module loads
gtk.gdk.threads_init()
