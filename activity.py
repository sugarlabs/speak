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


from sugar3.presence import presenceservice
import logging
from gi.repository import Gtk
from gi.repository import Gdk
from gi.repository import Pango
import cjson
from gettext import gettext as _

from sugar3.graphics.toolbarbox import ToolbarButton
from sugar3.graphics.radiotoolbutton import RadioToolButton

from combobox import ComboBox
from sugar3.graphics.toolbarbox import ToolbarBox
from shared_activity import SharedActivity
from sugar3.activity.widgets import ActivityToolbarButton
from sugar3.activity.widgets import StopButton

from toolitem import ToolWidget
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

MODE_TYPE = 1
MODE_BOT = 2
MODE_CHAT = 3

_NEW_INSTANCE = 0
_NEW_INSTANCE = 1
_PRE_INSTANCE = 2
_POST_INSTANCE = 3


class CursorFactory:

    __shared_state = {"cursors": {}}

    def __init__(self):
        self.__dict__ = self.__shared_state

    def get_cursor(self, cur_type):
        if not cur_type in self.cursors:
            cur = Gdk.Cursor.new(cur_type)
            self.cursors[cur_type] = cur
        return self.cursors[cur_type]


class SpeakActivity(SharedActivity):
    def __init__(self, handle):
        self.notebook = Gtk.Notebook()
        self.notebook.connect_after('map', self.__map_canvasactivity_cb)

        SharedActivity.__init__(self, self.notebook, SERVICE, handle)

        self._cursor = None
        self.set_cursor(Gdk.CursorType.LEFT_PTR)
        self.__resume_filename = None
        self.__postponed_share = []
        self.__on_save_instance = []
        self.__state = _NEW_INSTANCE
        self._mode = MODE_TYPE
        self.numeyesadj = None

        # make an audio device for playing back and rendering audio
        self.connect("notify::active", self._activeCb)

        # make a box to type into
        self.entrycombo = Gtk.ComboBoxText.new_with_entry()
        self.entrycombo.connect("changed", self._combo_changed_cb)
        self.entry = self.entrycombo.get_child()
        self.entry.can_activate_accel(True)
        self.entry.connect('activate', self._entry_activate_cb)
        self.entry.connect("key-press-event", self._entry_key_press_cb)
        self.input_font = Pango.FontDescription('sans bold 24')
        self.entry.modify_font(self.input_font)

        self.face = face.View()
        self.face.show()

        # layout the screen
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        box.set_homogeneous(False)
        box.pack_start(self.face, True, True, 0)
        box.pack_start(self.entrycombo, False, True, 0)

        self.add_events(Gdk.EventMask.POINTER_MOTION_HINT_MASK
                | Gdk.EventMask.POINTER_MOTION_MASK)
        
        self.connect("motion_notify_event", self._mouse_moved_cb)

        box.add_events(Gdk.EventMask.BUTTON_PRESS_MASK)
        box.connect("button_press_event", self._mouse_clicked_cb)

        # desktop
        self.notebook.show()
        self.notebook.props.show_border = False
        self.notebook.props.show_tabs = False

        box.show_all()
        self.notebook.append_page(box, Gtk.Label(""))

        self.chat = chat.View()
        self.chat.show_all()
        self.notebook.append_page(self.chat, Gtk.Label(""))

        # make the text box active right away
        self.entry.grab_focus()
        self.entry.connect("move-cursor", self._cursor_moved_cb)
        self.entry.connect("changed", self._cursor_moved_cb)

        # toolbar
        toolbox = ToolbarBox()

        toolbox.toolbar.insert(ActivityToolbarButton(self), -1)

        self.voices = ComboBox()
        for name in sorted(voice.allVoices().keys()):
            vn = voice.allVoices()[name]
            n = name[:26] + ".."
            self.voices.append_item(vn, n)

        self.voices.select(voice.defaultVoice())
        all_voices = self.voices.get_model()
        brain_voices = brain.get_voices()

        #toolbar: speak mode button
        mode_type = RadioToolButton(
                named_icon='mode-type',
                tooltip=_('Type something to hear it'))
        mode_type.connect('toggled', self.__toggled_mode_type_cb, all_voices)
        toolbox.toolbar.insert(mode_type, -1)

        #toolbar: robot mode button
        mode_robot = RadioToolButton(
                named_icon='mode-robot',
                group=mode_type,
                tooltip=_('Ask robot any question'))
        mode_robot.connect('toggled', self.__toggled_mode_robot_cb,
                brain_voices)
        toolbox.toolbar.insert(mode_robot, -1)

        #toolbar: mode chat button
        mode_chat = RadioToolButton(
                named_icon='mode-chat',
                group=mode_type,
                tooltip=_('Voice chat'))
        mode_chat.connect('toggled', self.__toggled_mode_chat_cb, all_voices)
        toolbox.toolbar.insert(mode_chat, -1)

        voices_toolitem = ToolWidget(widget=self.voices)
        toolbox.toolbar.insert(voices_toolitem, -1)

        #toolbar: voice button
        voice_button = ToolbarButton(
                page=self.make_voice_bar(),
                label=_('Voice'),
                icon_name='voice')
        toolbox.toolbar.insert(voice_button, -1)

        #toolbar: face button
        face_button = ToolbarButton(
                page=self.make_face_bar(),
                label=_('Face'),
                icon_name='face')
        toolbox.toolbar.insert(face_button, -1)
       
        #separator
        separator = Gtk.SeparatorToolItem()
        separator.set_draw(False)
        separator.set_expand(True)
        toolbox.toolbar.insert(separator, -1)
                
        toolbox.toolbar.insert(StopButton(self), -1)

        toolbox.show_all()
        self.toolbar_box = toolbox

    def _share(self, tube_conn, initiator):
        logging.debug('Activity._share state=%s' % self.__state)

        if self.__state == _NEW_INSTANCE:
            self.__postponed_share.append((tube_conn, initiator))
            self.__state = _PRE_INSTANCE
        elif self.__state == _PRE_INSTANCE:
            self.__postponed_share.append((tube_conn, initiator))
            self.__instance()
        elif self.__state == _POST_INSTANCE:
            self.share_instance(tube_conn, initiator)

    def set_cursor(self, cursor):
        if not isinstance(cursor, Gdk.Cursor):
            cursor = CursorFactory().get_cursor(cursor)

        if self._cursor != cursor:
            self._cursor = cursor
            self.get_property('window').set_cursor(self._cursor)

    def __map_canvasactivity_cb(self, widget):
        logging.debug('Activity.__map_canvasactivity_cb state=%s' % \
                self.__state)

        if self.__state == _NEW_INSTANCE:
            self.__instance()
        elif self.__state == _NEW_INSTANCE:
            self.__state = _PRE_INSTANCE
        elif self.__state == _PRE_INSTANCE:
            self.__instance()

        return False

    def __instance(self):
        logging.debug('Activity.__instance')

        if self.__resume_filename:
            self.resume_instance(self.__resume_filename)
        else:
            self.new_instance()

        for i in self.__postponed_share:
            self.share_instance(*i)
        self.__postponed_share = []

        self.__state = _POST_INSTANCE

    def read_file(self, file_path):
        self.__resume_filename = file_path
        if self.__state == _NEW_INSTANCE:
            self.__state = _PRE_INSTANCE
        elif self.__state == _PRE_INSTANCE:
            self.__instance()

    def write_file(self, file_path):
        for cb, args in self.__on_save_instance:
            cb(*args)
        self.save_instance(file_path)

    def new_instance(self):
        self.voices.connect('changed', self.__changed_voices_cb)
        self.pitchadj.connect("value_changed", self.pitch_adjusted_cb,
                              self.pitchadj)
        self.rateadj.connect("value_changed", self.rate_adjusted_cb,
                             self.rateadj)
        self.mouth_shape_combo.connect('changed', self.mouth_changed_cb, False)
        self.mouth_changed_cb(self.mouth_shape_combo, True)
        self.numeyesadj.connect("value_changed", self.eyes_changed_cb, False)
        self.eye_shape_combo.connect('changed', self.eyes_changed_cb, False)
        self.eyes_changed_cb(None, True)

        self.face.look_ahead()

        # say hello to the user
        presenceService = presenceservice.get_instance()
        xoOwner = presenceService.get_owner()
        self.face.say_notification(_("Hello %s. Please Type something.") \
                % xoOwner.props.nick)

    def resume_instance(self, file_path):
        cfg = cjson.decode(file(file_path, 'r').read())

        status = self.face.status = face.Status().deserialize(cfg['status'])
        self.voices.select(status.voice)
        self.pitchadj.set_value(self.face.status.pitch)
        self.rateadj.set_value(self.face.status.rate)
        self.mouth_shape_combo.select(status.mouth)
        self.eye_shape_combo.select(status.eyes[0])
        self.numeyesadj.set_value(len(status.eyes))

        self.entry.props.text = cfg['text'].encode('utf-8', 'ignore')
        for i in cfg['history']:
            self.entrycombo.append_text(i.encode('utf-8', 'ignore'))

        self.new_instance()

    def save_instance(self, file_path):
        cfg = {'status': self.face.status.serialize(),
                'text': unicode(self.entry.props.text, 'utf-8', 'ignore'),
                'history': [unicode(i[0], 'utf-8', 'ignore') \
                        for i in self.entrycombo.get_model()],
                }
        file(file_path, 'w').write(cjson.encode(cfg))

    def share_instance(self, connection, is_initiator):
        self.chat.messenger = Messenger(connection, is_initiator, self.chat)

    def _cursor_moved_cb(self, entry, *ignored):
        # make the eyes track the motion of the text cursor
        index = entry.props.cursor_position
        layout = entry.get_layout()
        pos = layout.get_cursor_pos(index)
        x = pos[0].x / Pango.SCALE - entry.props.scroll_offset
        y = entry.get_allocation().y
        self.face.look_at(pos=(x, y))

    def get_mouse(self):
        display = Gdk.Display.get_default()
        screen, mouseX, mouseY, modifiers = display.get_pointer()
        return mouseX, mouseY

    def _mouse_moved_cb(self, widget, event):
        # make the eyes track the motion of the mouse cursor
        self.face.look_at()
        self.chat.look_at()
    
    def _mouse_clicked_cb(self, widget, event):
        pass

    def make_voice_bar(self):
        voicebar = Gtk.Toolbar()

        self.pitchadj = Gtk.Adjustment(self.face.status.pitch, 0,
                espeak.PITCH_MAX, 1, espeak.PITCH_MAX / 10, 0)
        pitchbar = Gtk.Scale(orientation = Gtk.Orientation.HORIZONTAL)
        pitchbar.set_adjustment(self.pitchadj)
        pitchbar.set_draw_value(False)
        # FIXME: Gtk.UPDATE_DISCONTINUOUS
        # pitchbar.set_inverted(True)
        #pitchbar.set_update_policy(Gtk.UPDATE_DISCONTINUOUS)
        pitchbar.set_size_request(240, 15)

        pitchbar_toolitem = ToolWidget(
                widget=pitchbar,
                label_text=_('Pitch:'))
        voicebar.insert(pitchbar_toolitem, -1)

        self.rateadj = Gtk.Adjustment(self.face.status.rate, 0,
                                   espeak.RATE_MAX, 1, espeak.RATE_MAX / 10, 0)
        ratebar = Gtk.Scale(orientation = Gtk.Orientation.HORIZONTAL)
        ratebar.set_adjustment(self.rateadj)
        ratebar.set_draw_value(False)
        # FIXME: Gtk.UPDATE_DISCONTINUOUS
        # ratebar.set_inverted(True)
        #ratebar.set_update_policy(Gtk.UPDATE_DISCONTINUOUS)
        ratebar.set_size_request(240, 15)

        ratebar_toolitem = ToolWidget(
                widget=ratebar,
                label_text=_('Rate:'))
        voicebar.insert(ratebar_toolitem, -1)

        voicebar.show_all()
        return voicebar

    def pitch_adjusted_cb(self, get, data=None):
        self.face.status.pitch = get.value
        self.face.say_notification(_("pitch adjusted"))

    def rate_adjusted_cb(self, get, data=None):
        self.face.status.rate = get.value
        self.face.say_notification(_("rate adjusted"))

    def make_face_bar(self):
        facebar = Gtk.Toolbar()

        self.mouth_shape_combo = ComboBox()
        self.mouth_shape_combo.append_item(mouth.Mouth, _("Simple"))
        self.mouth_shape_combo.append_item(waveform_mouth.WaveformMouth,
                                           _("Waveform"))
        self.mouth_shape_combo.append_item(fft_mouth.FFTMouth, _("Frequency"))
        self.mouth_shape_combo.set_active(0)

        mouth_shape_toolitem = ToolWidget(
                widget=self.mouth_shape_combo,
                label_text=_('Mouth:'))
        facebar.insert(mouth_shape_toolitem, -1)

        self.eye_shape_combo = ComboBox()
        self.eye_shape_combo.append_item(eye.Eye, _("Round"))
        self.eye_shape_combo.append_item(glasses.Glasses, _("Glasses"))
        self.eye_shape_combo.set_active(0)

        eye_shape_toolitem = ToolWidget(
                widget=self.eye_shape_combo,
                label_text=_('Eyes:'))
        facebar.insert(eye_shape_toolitem, -1)

        self.numeyesadj = Gtk.Adjustment(2, 1, 5, 1, 1, 0)
        numeyesbar = Gtk.Scale(orientation = Gtk.Orientation.HORIZONTAL)
        numeyesbar.set_adjustment(self.numeyesadj)
        numeyesbar.set_draw_value(False)
        # FIXME: Gtk.UPDATE_DISCONTINUOUS
        #numeyesbar.set_update_policy(Gtk.UPDATE_DISCONTINUOUS)
        numeyesbar.set_size_request(240, 15)

        numeyesbar_toolitem = ToolWidget(
                widget=numeyesbar,
                label_text=_('Eyes number:'))
        facebar.insert(numeyesbar_toolitem, -1)

        facebar.show_all()
        return facebar

    def mouth_changed_cb(self, combo, quiet):
        self.face.status.mouth = combo.props.value
        self._update_face()

        # this SegFaults: self.face.say(combo.get_active_text())
        if not quiet:
            self.face.say_notification(_("mouth changed"))

    def eyes_changed_cb(self, ignored, quiet):
        if self.numeyesadj is None:
            return

        self.face.status.eyes = [self.eye_shape_combo.props.value] \
                * int(self.numeyesadj.get_value())
        self._update_face()

        # this SegFaults: self.face.say(self.eye_shape_combo.get_active_text())
        if not quiet:
            self.face.say_notification(_("eyes changed"))

    def _update_face(self):
        self.face.update()
        self.chat.update(self.face.status)

    def _combo_changed_cb(self, combo):
        # when a new item is chosen, make sure the text is selected
        if not self.entry.is_focus():
            self.entry.grab_focus()
            self.entry.select_region(0, -1)

    def _entry_key_press_cb(self, combo, event):
        # make the up/down arrows navigate through our history
        keyname = Gdk.keyval_name(event.keyval)
        if keyname == "Up":
            index = self.entrycombo.get_active()
            if index > 0:
                index -= 1
            self.entrycombo.set_active(index)
            self.entry.select_region(0, -1)
            return True
        elif keyname == "Down":
            index = self.entrycombo.get_active()
            if index < len(self.entrycombo.get_model()) - 1:
                index += 1
            self.entrycombo.set_active(index)
            self.entry.select_region(0, -1)
            return True
        return False

    def _entry_activate_cb(self, entry):
        # the user pressed Return, say the text and clear it out
        text = entry.props.text
        if text:
            self.face.look_ahead()

            # speak the text
            if self._mode == MODE_BOT:
                self.face.say(
                        brain.respond(self.voices.props.value, text))
            else:
                self.face.say(text)

            # add this text to our history unless
            # it is the same as the last item
            history = self.entrycombo.get_model()
            if len(history) == 0 or history[-1][0] != text:
                self.entrycombo.append_text(text)
                # don't let the history get too big
                while len(history) > 20:
                    self.entrycombo.remove_text(0)
                # select the new item
                self.entrycombo.set_active(len(history) - 1)
            # select the whole text
            entry.select_region(0, -1)

    def _activeCb(self, widget, pspec):
        # only generate sound when this activity is active
        if not self.props.active:
            self.face.shut_up()
            self.chat.shut_up()

    def _set_voice(self, new_voice):
        try:
            self.voices.handler_block_by_func(self.__changed_voices_cb)
            self.voices.select(new_voice)
            self.face.status.voice = new_voice
        finally:
            self.voices.handler_unblock_by_func(self.__changed_voices_cb)

    def __toggled_mode_type_cb(self, button, voices_model):
        if not button.props.active:
            return

        self._mode = MODE_TYPE
        self.chat.shut_up()
        self.face.shut_up()
        self.notebook.set_current_page(0)

        old_voice = self.voices.props.value
        self.voices.set_model(voices_model)
        self._set_voice(old_voice)

    def __toggled_mode_robot_cb(self, button, voices_model):
        if not button.props.active:
            return

        self._mode = MODE_BOT
        self.chat.shut_up()
        self.face.shut_up()
        self.notebook.set_current_page(0)

        old_voice = self.voices.props.value
        self.voices.set_model(voices_model)

        new_voice = [i[0] for i in voices_model
                if i[0].short_name == old_voice.short_name]
        if not new_voice:
            new_voice = brain.get_default_voice()
            sorry = _("Sorry, I can't speak %(old_voice)s, " \
                      "let's talk %(new_voice)s instead.") % {
                              'old_voice': old_voice.friendlyname,
                              'new_voice': new_voice.friendlyname,
                              }
        else:
            new_voice = new_voice[0]
            sorry = None

        self._set_voice(new_voice)

        if not brain.load(self, self.voices.props.value, sorry):
            if sorry:
                self.face.say_notification(sorry)

    def __toggled_mode_chat_cb(self, button, voices_model):
        if not button.props.active:
            return

        is_first_session = not self.chat.me.get_mapped()

        self._mode = MODE_CHAT
        self.face.shut_up()
        self.notebook.set_current_page(1)

        old_voice = self.voices.props.value
        self.voices.set_model(voices_model)
        self._set_voice(old_voice)

        if is_first_session:
            self.chat.me.say_notification(
                    _("You are in off-line mode, share and invite someone."))

    def __changed_voices_cb(self, combo):
        voice = combo.props.value
        self.face.set_voice(voice)
        if self._mode == MODE_BOT:
            brain.load(self, voice)


# activate gtk threads when this module loads
Gdk.threads_init()
