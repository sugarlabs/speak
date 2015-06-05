# Speak.activity
# A simple front end to the espeak text-to-speech engine on the XO laptop
# http://wiki.laptop.org/go/Speak
#
# Copyright (C) 2008  Joshua Minor
# Copyright (C) 2014  Walter Bender (major refactoring)
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

from telepathy.interfaces import CHANNEL_INTERFACE
from telepathy.interfaces import CHANNEL_INTERFACE_GROUP
from telepathy.interfaces import CHANNEL_TYPE_TEXT
from telepathy.interfaces import CONN_INTERFACE_ALIASING
from telepathy.constants import CHANNEL_GROUP_FLAG_CHANNEL_SPECIFIC_HANDLES
from telepathy.constants import CHANNEL_TEXT_MESSAGE_TYPE_NORMAL
from telepathy.client import Connection
from telepathy.client import Channel

import logging
import os
import subprocess
import gtk
import gobject
import pango
import json
import random
from gettext import gettext as _

from sugar.activity import activity
from sugar.presence import presenceservice
from sugar.graphics import style
from sugar.graphics.toolbutton import ToolButton
from sugar.graphics.radiotoolbutton import RadioToolButton
from sugar.graphics.combobox import ComboBox
from sugar.graphics.toolbarbox import ToolbarBox, ToolbarButton
from sugar.activity.widgets import ActivityToolbarButton
from sugar.activity.widgets import StopButton
from sugar.graphics.objectchooser import ObjectChooser

from sugar import mime
from sugar import profile

import eye
import glasses
import eyelashes
import halfmoon
import sleepy
import sunglasses
import wireframes

import mouth
import fft_mouth
import waveform_mouth

import face
import photoface

import voice as voice_model
import brain
import chat

from faceselect import FaceSelector

import local_espeak as espeak

SERVICE = 'org.sugarlabs.Speak'
IFACE = SERVICE
PATH = '/org/sugarlabs/Speak'

logger = logging.getLogger('speak')

ACCELEROMETER_DEVICE = '/sys/devices/platform/lis3lv02d/position'
MODE_TYPE = 1
MODE_BOT = 2
MODE_CHAT = 3
FACE_CARTOON = 1
FACE_PHOTO = 2
MOUTHS = [mouth.Mouth, fft_mouth.FFTMouth, waveform_mouth.WaveformMouth]
NUMBERS = ['one', 'two', 'three', 'four', 'five']
SLEEPY_EYES = sleepy.Sleepy
EYE_DICT = {
    'eyes': {'label': _('Round'), 'widget': eye.Eye, 'index': 1},
    'glasses': {'label': _('Glasses'), 'widget': glasses.Glasses, 'index': 2},
    'halfmoon': {'label': _('Half moon'), 'widget': halfmoon.Halfmoon,
                 'index': 3},
    'eyelashes': {'label': _('Eye lashes'), 'widget': eyelashes.Eyelashes,
                  'index': 4},
    'sunglasses': {'label': _('Sunglasses'), 'widget': sunglasses.Sunglasses,
                   'index': 5},
    'wireframes': {'label': _('Wire frames'), 'widget': wireframes.Wireframes,
                   'index': 6},
    }
DELAY_BEFORE_SPEAKING = 1500  # milleseconds
IDLE_DELAY = 120000  # milleseconds
IDLE_PHRASES = ['zzzzzzzzz', _('I am bored.'), _('Talk to me.'),
                _('I am sleepy.'), _('Are you still there?'),
                _('Please type something.'),
                _('Do you have anything to say to me?'), _('Hello?')]
SIDEWAYS_PHRASES = [_('Whoa! Sideways!'), _("I'm on my side."), _('Uh oh.'),
                    _('Wheeeee!'), _('Hey! Put me down!'), _('Falling over!')]
SLASH = '-x-SLASH-x-'  # slash safe encoding


def _luminance(color):
    ''' Calculate luminance value '''
    return int(color[1:3], 16) * 0.3 + int(color[3:5], 16) * 0.6 + \
        int(color[5:7], 16) * 0.1


def _lighter_color(colors):
    ''' Which color is lighter? Use that one for the text nick color '''
    if _luminance(colors[0]) > _luminance(colors[1]):
        return 0
    return 1


def _has_accelerometer():
    return os.path.exists(ACCELEROMETER_DEVICE) and _is_tablet_mode()


def _is_tablet_mode():
    if not os.path.exists('/dev/input/event4'):
        return False
    try:
        output = subprocess.call(
            ['evtest', '--query', '/dev/input/event4', 'EV_SW',
             'SW_TABLET_MODE'])
    except (OSError, subprocess.CalledProcessError):
        return False
    if str(output) == '10':
        return True
    return False


class SpeakActivity(activity.Activity):
    def __init__(self, handle):
        super(SpeakActivity, self).__init__(handle)

        self._notebook = gtk.Notebook()
        self.set_canvas(self._notebook)
        self._notebook.show()

        self._colors = profile.get_color().to_string().split(',')
        lighter = style.Color(self._colors[
            _lighter_color(self._colors)])

        self._mode = MODE_TYPE
        self._tablet_mode = _is_tablet_mode()
        self._robot_idle_id = None
        self._active_eyes = None
        self._active_number_of_eyes = None
        self._current_voice = None
        self._face_type = FACE_CARTOON

        # make an audio device for playing back and rendering audio
        self.connect('notify::active', self._active_cb)
        self._cfg = {}

        # make a box to type into
        self._entry_box = gtk.HBox()

        if self._tablet_mode:
            self._entry = gtk.Entry()
            self._entry_box.pack_start(self._entry, expand=True)
            talk_button = ToolButton('microphone')
            talk_button.set_tooltip(_('Speak'))
            talk_button.connect('clicked', self._talk_cb)
            self._entry_box.pack_end(talk_button, expand=False)
        else:
            self._entrycombo = gtk.combo_box_entry_new_text()
            self._entrycombo.connect('changed', self._combo_changed_cb)
            self._entry = self._entrycombo.child
            self._entry.set_size_request(-1, style.GRID_CELL_SIZE)
            self._entry_box.pack_start(self._entrycombo, expand=True)
        self._entry.set_editable(True)
        self._entry.connect('activate', self._entry_activate_cb)
        self._entry.connect('key-press-event', self._entry_key_press_cb)
        self._entry.modify_font(pango.FontDescription(str='sans bold 24'))
        self._entry_box.show()

        self.face = face.View(fill_color=lighter)
        self._cartoon_face = self.face
        self.face.set_size_request(
            -1, gtk.gdk.screen_height() - 2 * style.GRID_CELL_SIZE)
        self.face.show()

        # layout the screen
        self._box = gtk.VBox(homogeneous=False)
        if self._tablet_mode:
            self._box.pack_start(self._entry_box, expand=False)
            self._box.pack_start(self.face)
        else:
            self._box.pack_start(self.face, expand=True)
            self._box.pack_start(self._entry_box)

        self.add_events(gtk.gdk.POINTER_MOTION_HINT_MASK
                        | gtk.gdk.POINTER_MOTION_MASK)
        self.connect('motion_notify_event', self._mouse_moved_cb)

        self._box.add_events(gtk.gdk.BUTTON_PRESS_MASK)
        self._box.connect('button_press_event', self._mouse_clicked_cb)

        # desktop
        self._notebook.show()
        self._notebook.props.show_border = False
        self._notebook.props.show_tabs = False

        self._box.show_all()
        self._notebook.append_page(self._box)

        self._chat = chat.View()
        self._chat.show_all()
        self._notebook.append_page(self._chat)

        # make the text box active right away
        if not self._tablet_mode:
            self._entry.grab_focus()

        self._entry.connect('move-cursor', self._cursor_moved_cb)
        self._entry.connect('changed', self._cursor_moved_cb)

        toolbox = ToolbarBox()
        self._activity_button = ActivityToolbarButton(self)
        self._activity_button.connect('clicked', self._configure_cb)

        toolbox.toolbar.insert(self._activity_button, -1)

        self._mode_type = RadioToolButton(
            named_icon='mode-type',
            tooltip=_('Type something to hear it'))
        self._mode_type.connect('toggled', self.__toggled_mode_type_cb)
        toolbox.toolbar.insert(self._mode_type, -1)

        mode_robot = RadioToolButton(
            named_icon='mode-robot',
            group=self._mode_type,
            tooltip=_('Ask robot any question'))
        mode_robot.connect('toggled', self.__toggled_mode_robot_cb)
        toolbox.toolbar.insert(mode_robot, -1)

        self._mode_chat = RadioToolButton(
            named_icon='mode-chat',
            group=self._mode_type,
            tooltip=_('Voice chat'))
        self._mode_chat.connect('toggled', self.__toggled_mode_chat_cb)
        toolbox.toolbar.insert(self._mode_chat, -1)

        self._voice_button = ToolbarButton(
            page=self._make_voice_bar(),
            label=_('Voice'),
            icon_name='voice')
        self._voice_button.connect('clicked', self._configure_cb)
        toolbox.toolbar.insert(self._voice_button, -1)

        self._face_button = ToolbarButton(
            page=self._make_face_bar(),
            label=_('Face'),
            icon_name='face')
        self._face_button.connect('clicked', self._configure_cb)
        toolbox.toolbar.insert(self._face_button, -1)

        separator = gtk.SeparatorToolItem()
        separator.set_draw(False)
        separator.set_expand(True)
        toolbox.toolbar.insert(separator, -1)

        toolbox.toolbar.insert(StopButton(self), -1)

        toolbox.show_all()
        self.toolbar_box = toolbox

        gtk.gdk.screen_get_default().connect('size-changed',
                                             self._configure_cb)

        self._first_time = True
        self._new_instance()

        self._configure_cb()
        self._poll_accelerometer()

        if self.shared_activity:
            # we are joining the activity
            self.connect('joined', self._joined_cb)
            if self.get_shared():
                # we have already joined
                self._joined_cb(self)
            self._mode_chat.set_active(True)
            self._setup_chat_mode()
        elif handle.uri:
            # XMPP non-sugar3 incoming chat, not sharable
            self._activity_button.props.page.share.props.visible = \
                False
            self._one_to_one_connection(handle.uri)
        else:
            # we are creating the activity
            self.connect('shared', self._shared_cb)

    def _toolbar_expanded(self):
        if self._activity_button.is_expanded():
            return True
        if self._voice_button.is_expanded():
            return True
        if self._face_button.is_expanded():
            return True
        return False

    def _configure_cb(self, event=None):
        self._entry.set_size_request(-1, style.GRID_CELL_SIZE)
        if self._toolbar_expanded():
            self.face.set_size_request(
                -1, gtk.gdk.screen_height() - 3 * style.GRID_CELL_SIZE)
            self._chat.resize_chat_box(expanded=True)
            self._chat.resize_buddy_list()
        else:
            self.face.set_size_request(
                -1, gtk.gdk.screen_height() - 2 * style.GRID_CELL_SIZE)
            self._chat.resize_chat_box()
            self._chat.resize_buddy_list()

    def _new_instance(self):
        if self._first_time:
            # self.voices.connect('changed', self.__changed_voices_cb)
            self.pitchadj.connect('value_changed', self._pitch_adjusted_cb,
                                  self.pitchadj)
            self.rateadj.connect('value_changed', self._rate_adjusted_cb,
                                 self.rateadj)
        if self._active_number_of_eyes is None:
            self._number_of_eyes_changed_event_cb(None, None, 'two', True)
        if self._active_eyes is None:
            self._eyes_changed_event_cb(None, None, 'eyes', True)

        self._mouth_changed_cb(None, True)

        self.face.look_ahead()

        presenceService = presenceservice.get_instance()
        self.owner = presenceService.get_owner()
        if self._first_time:
            # say hello to the user
            if self._tablet_mode:
                self._entry.props.text = _('Hello %s.') \
                    % self.owner.props.nick.encode('utf-8', 'ignore')
            self.face.say_notification(_('Hello %s. Please Type something.')
                                       % self.owner.props.nick)
        else:
            if self._tablet_mode:
                self._entry.props.text = _('Welcome back %s.') \
                    % self.owner.props.nick.encode('utf-8', 'ignore')
            self.face.say_notification(_('Welcome back %s.')
                                       % self.owner.props.nick)
        self._set_idle_phrase(speak=False)
        self._first_time = False

    def read_file(self, file_path):
        self._cfg = json.loads(file(file_path, 'r').read())

        current_voice = self.face.status.voice

        type_ = self._cfg['face_type']
        lighter = style.Color(self._colors[_lighter_color(self._colors)])
        if type_ == self._face_type:
            status = self.face.status = \
                face.Status().deserialize(self._cfg['status'])
        elif type_ == FACE_CARTOON:
            self._set_face(face.View(fill_color=lighter), FACE_CARTOON)
            self._cartoon_face = self.face
            status = self.face.status = \
                face.Status().deserialize(self._cfg['status'])
        else:
            status = photoface.Status().deserialize(self._cfg['status'])
            view = photoface.View(*status.get_args(), fill_color=lighter)
            status = view.status
            self._set_face(view, FACE_PHOTO)

        found_my_voice = False
        for name in self._voice_evboxes.keys():
            if self._voice_evboxes[name][1] == current_voice:
                self._voice_evboxes[name][0].modify_bg(
                    0, style.COLOR_BLACK.get_gdk_color())
            if self._voice_evboxes[name][1] == status.voice and \
               not found_my_voice:
                self._voice_evboxes[name][0].modify_bg(
                    0, style.COLOR_BUTTON_GREY.get_gdk_color())
                self.face.set_voice(status.voice)
                if self._mode == MODE_BOT:
                    brain.load(self, status.voice)
                found_my_voice = True

        self.pitchadj.value = self.face.status.pitch
        self.rateadj.value = self.face.status.rate

        if self._face_type == FACE_CARTOON:
            if status.mouth in MOUTHS:
                self._mouth_type[MOUTHS.index(status.mouth)].set_active(True)

            self._number_of_eyes_changed_event_cb(
                None, None, NUMBERS[len(status.eyes) - 1], True)
            for name in EYE_DICT.keys():
                if status.eyes[0] == EYE_DICT[name]['widget']:
                    self._eye_type[name].set_icon(name + '-selected')
                    self._eyes_changed_event_cb(None, None, name, True)
                    break

        self._entry.props.text = self._cfg['text'].encode('utf-8', 'ignore')
        if not self._tablet_mode:
            for i in self._cfg['history']:
                self._entrycombo.append_text(i.encode('utf-8', 'ignore'))

        self._new_instance()

    def write_file(self, file_path):
        if self._tablet_mode:
            if 'history' in self._cfg:
                history = self._cfg['history']  # retain old history
            else:
                history = []
        else:
            history = [unicode(i[0], 'utf-8', 'ignore')
                       for i in self._entrycombo.get_model()]
        cfg = {'status': self.face.status.serialize(),
               'face_type': self._face_type,
               'text': unicode(self._entry.props.text, 'utf-8', 'ignore'),
               'history': history, }
        file(file_path, 'w').write(json.dumps(cfg))

    def _cursor_moved_cb(self, entry, *ignored):
        # make the eyes track the motion of the text cursor
        index = entry.props.cursor_position
        layout = entry.get_layout()
        pos = layout.get_cursor_pos(index)
        x = pos[0][0] / pango.SCALE - entry.props.scroll_offset
        y = entry.get_allocation().y
        self.face.look_at(pos=(x, y))

    def _poll_accelerometer(self):
        if _has_accelerometer():
            idle_time = self._test_orientation()
            gobject.timeout_add(idle_time, self._poll_accelerometer)

    def _test_orientation(self):
        if _has_accelerometer():
            fh = open(ACCELEROMETER_DEVICE)
            string = fh.read()
            fh.close()
            xyz = string[1:-2].split(',')
            x = int(xyz[0])
            y = int(xyz[1])
            # DO SOMETHING HERE
            if ((gtk.gdk.screen_width() > gtk.gdk.screen_height() and
                 abs(x) > abs(y)) or
                (gtk.gdk.screen_width() < gtk.gdk.screen_height() and
                 abs(x) < abs(y))):
                sideways_phrase = SIDEWAYS_PHRASES[
                    random.randint(0, len(SIDEWAYS_PHRASES) - 1)]
                self.face.say(SIDEWAYS_PHRASES[sideways_phrase])
                return IDLE_DELAY  # Don't repeat the message for a while
            return 1000  # Test again soon

    def get_mouse(self):
        display = gtk.gdk.display_get_default()
        screen, mouseX, mouseY, modifiers = display.get_pointer()
        return mouseX, mouseY

    def _mouse_moved_cb(self, widget, event):
        # make the eyes track the motion of the mouse cursor
        self.face.look_at()
        self._chat.look_at()

    def _mouse_clicked_cb(self, widget, event):
        pass

    def _make_voice_bar(self):
        voicebar = gtk.Toolbar()

        all_voices = []
        for name in sorted(voice_model.allVoices().keys()):
            if len(name) < 26:
                friendly_name = name
            else:
                friendly_name = name[:26] + '...'
            all_voices.append([voice_model.allVoices()[name], friendly_name])

        # A palette for the voice selection
        logging.error(self.face.status.voice)

        self._voice_evboxes = {}
        self._voice_box = gtk.HBox()
        vboxes = [gtk.VBox(), gtk.VBox(), gtk.VBox()]
        count = len(voice_model.allVoices().keys())
        found_my_voice = False
        for i, voice in enumerate(sorted(all_voices)):
            label = gtk.Label()
            label.set_use_markup(True)
            label.set_justify(gtk.JUSTIFY_LEFT)
            label.set_markup('<span size="large">%s</span>' % voice[1])

            alignment = gtk.Alignment(0, 0, 0, 0)
            alignment.add(label)
            label.show()

            evbox = gtk.EventBox()
            self._voice_evboxes[voice[1]] = [evbox, voice[0]]
            self._voice_evboxes[voice[1]][0].connect(
                'button-press-event', self._voices_changed_event_cb, voice)
            if voice[0] == self.face.status.voice and not found_my_voice:
                self._current_voice = voice
                evbox.modify_bg(
                    0, style.COLOR_BUTTON_GREY.get_gdk_color())
                found_my_voice = True
            evbox.add(alignment)
            alignment.show()
            if i < count / 3:
                vboxes[0].pack_start(evbox)
            elif i < 2 * count / 3:
                vboxes[1].pack_start(evbox)
            else:
                vboxes[2].pack_start(evbox)
        self._voice_box.pack_start(vboxes[0], padding=style.DEFAULT_PADDING)
        self._voice_box.pack_start(vboxes[1], padding=style.DEFAULT_PADDING)
        self._voice_box.pack_start(vboxes[2], padding=style.DEFAULT_PADDING)

        voice_palette_button = ToolButton('module-language')
        voice_palette_button.set_tooltip(_('Choose voice:'))
        self._voice_palette = voice_palette_button.get_palette()
        self._voice_palette.set_content(self._voice_box)
        self._voice_box.show_all()
        voice_palette_button.connect('clicked', self._face_palette_cb)
        voicebar.insert(voice_palette_button, -1)
        voice_palette_button.show()

        brain_voices = []
        for name in sorted(brain.BOTS.keys()):
            brain_voices.append([voice_model.allVoices()[name], name])

        self._brain_evboxes = {}
        self._brain_box = gtk.HBox()
        vboxes = gtk.VBox()
        count = brain.BOTS.keys()
        found_my_voice = False
        for i, voice in enumerate(brain_voices):
            label = gtk.Label()
            label.set_use_markup(True)
            label.set_justify(gtk.JUSTIFY_LEFT)
            label.set_markup('<span size="large">%s</span>' % voice[1])

            alignment = gtk.Alignment(0, 0, 0, 0)
            alignment.add(label)
            label.show()

            evbox = gtk.EventBox()
            self._brain_evboxes[voice[1]] = [evbox, voice[0]]
            self._brain_evboxes[voice[1]][0].connect(
                'button-press-event', self._voices_changed_event_cb, voice)
            if voice[0] == self.face.status.voice and not found_my_voice:
                evbox.modify_bg(
                    0, style.COLOR_BUTTON_GREY.get_gdk_color())
                found_my_voice = True
            evbox.add(alignment)
            alignment.show()
            vboxes.pack_start(evbox)
        self._brain_box.pack_start(vboxes, padding=style.DEFAULT_PADDING)
        self._brain_box.show_all()

        separator = gtk.SeparatorToolItem()
        separator.set_draw(True)
        separator.set_expand(False)
        voicebar.insert(separator, -1)

        self.pitchadj = gtk.Adjustment(self.face.status.pitch, 0,
                                       espeak.PITCH_MAX, 1,
                                       espeak.PITCH_MAX/10, 0)
        pitchbar = gtk.HScale(self.pitchadj)
        pitchbar.set_draw_value(False)
        # pitchbar.set_inverted(True)
        pitchbar.set_update_policy(gtk.UPDATE_DISCONTINUOUS)
        pitchbar.set_size_request(240, 15)

        pitchbar_toolitem = ToolWidget(widget=pitchbar, label_text=_('Pitch:'))
        voicebar.insert(pitchbar_toolitem, -1)

        self.rateadj = gtk.Adjustment(self.face.status.rate, 0,
                                      espeak.RATE_MAX,
                                      1, espeak.RATE_MAX / 10, 0)
        ratebar = gtk.HScale(self.rateadj)
        ratebar.set_draw_value(False)
        # ratebar.set_inverted(True)
        ratebar.set_update_policy(gtk.UPDATE_DISCONTINUOUS)
        ratebar.set_size_request(240, 15)

        ratebar_toolitem = ToolWidget(widget=ratebar, label_text=_('Rate:'))
        voicebar.insert(ratebar_toolitem, -1)

        voicebar.show_all()
        return voicebar

    def _pitch_adjusted_cb(self, get, data=None):
        self.face.status.pitch = get.value
        self.face.say_notification(_('pitch adjusted'))

    def _rate_adjusted_cb(self, get, data=None):
        self.face.status.rate = get.value
        self.face.say_notification(_('rate adjusted'))

    def _make_face_bar(self):
        facebar = gtk.Toolbar()

        self._photo_face = ToolButton('photoface')
        self._photo_face.set_tooltip(_('Set face from photo'))
        self._photo_face.connect('clicked', self._photo_face_cb)
        facebar.insert(self._photo_face, -1)
        self._photo_face.show()

        self._clear = ToolButton('face')
        self._clear.set_tooltip(_('Clear photo face'))
        self._clear.set_sensitive(False)
        self._clear.connect('clicked', self._clear_photo_cb)
        facebar.insert(self._clear, -1)
        self._clear.show()

        separator = gtk.SeparatorToolItem()
        separator.set_draw(True)
        separator.set_expand(False)
        facebar.insert(separator, -1)

        self._mouth_type = []
        self._mouth_type.append(RadioToolButton(
            named_icon='mouth',
            group=None,
            tooltip=_('Simple')))
        self._mouth_type[-1].connect('clicked', self._mouth_changed_cb, False)
        facebar.insert(self._mouth_type[-1], -1)

        self._mouth_type.append(RadioToolButton(
            named_icon='waveform',
            group=self._mouth_type[0],
            tooltip=_('Waveform')))
        self._mouth_type[-1].connect('clicked', self._mouth_changed_cb, False)
        facebar.insert(self._mouth_type[-1], -1)

        self._mouth_type.append(RadioToolButton(
            named_icon='frequency',
            group=self._mouth_type[0],
            tooltip=_('Frequency')))
        self._mouth_type[-1].connect('clicked', self._mouth_changed_cb, False)
        facebar.insert(self._mouth_type[-1], -1)

        separator = gtk.SeparatorToolItem()
        separator.set_draw(True)
        separator.set_expand(False)
        facebar.insert(separator, -1)

        eye_box = gtk.VBox()
        self._eye_type = {}
        for name in EYE_DICT.keys():
            self._eye_type[name] = ToolButton(name)
            self._eye_type[name].connect('clicked',
                                         self._eyes_changed_event_cb,
                                         None, name, False)
            label = gtk.Label(EYE_DICT[name]['label'])
            hbox = gtk.HBox()
            hbox.pack_start(self._eye_type[name])
            self._eye_type[name].show()
            hbox.pack_start(label)
            label.show()
            evbox = gtk.EventBox()
            evbox.connect('button-press-event', self._eyes_changed_event_cb,
                          name, False)
            evbox.add(hbox)
            hbox.show()
            eye_box.pack_start(evbox)

        eye_palette_button = ToolButton('eyes')
        eye_palette_button.set_tooltip(_('Choose eyes:'))
        palette = eye_palette_button.get_palette()
        palette.set_content(eye_box)
        eye_box.show_all()
        eye_palette_button.connect('clicked', self._face_palette_cb)
        facebar.insert(eye_palette_button, -1)
        eye_palette_button.show()

        number_of_eyes_box = gtk.VBox()
        self._number_of_eyes_type = {}
        for name in NUMBERS:
            self._number_of_eyes_type[name] = ToolButton(name)
            self._number_of_eyes_type[name].connect(
                'clicked', self._number_of_eyes_changed_event_cb,
                None, name, False)
            label = gtk.Label(name)
            hbox = gtk.HBox()
            hbox.pack_start(self._number_of_eyes_type[name])
            self._number_of_eyes_type[name].show()
            hbox.pack_start(label)
            label.show()
            evbox = gtk.EventBox()
            evbox.connect('button-press-event',
                          self._number_of_eyes_changed_event_cb,
                          name, False)
            evbox.add(hbox)
            hbox.show()
            number_of_eyes_box.pack_start(evbox)

        number_of_eyes_palette_button = ToolButton('number')
        number_of_eyes_palette_button.set_tooltip(_('Eyes number:'))
        palette = number_of_eyes_palette_button.get_palette()
        palette.set_content(number_of_eyes_box)
        number_of_eyes_box.show_all()
        number_of_eyes_palette_button.connect('clicked', self._face_palette_cb)
        facebar.insert(number_of_eyes_palette_button, -1)
        number_of_eyes_palette_button.show()

        self._cartoon_face_buttons = self._mouth_type + \
            [eye_palette_button, number_of_eyes_palette_button]

        facebar.show_all()
        return facebar

    def _photo_face_cb(self, widget):
        chooser = ObjectChooser(parent=self,
                                what_filter=mime.GENERIC_TYPE_IMAGE)

        result = chooser.run()
        if result == gtk.RESPONSE_ACCEPT:
            jobject = chooser.get_selected_object()
            if jobject and jobject.file_path:
                selector = FaceSelector(jobject.file_path)
                selector.connect('face-processed',
                                 self._photo_face_processed_cb)
                selector.connect('cancel', self._photo_face_cancel_cb)
                self._notebook.append_page(selector)
                selector.show()

                num = self._notebook.page_num(selector)
                self._notebook.set_current_page(num)
        chooser.destroy()
                
    def _photo_face_processed_cb(self, widget, *face_data):
        lighter = style.Color(self._colors[_lighter_color(self._colors)])
        self._set_face(photoface.View(*face_data, fill_color=lighter),
                       FACE_PHOTO)

    def _photo_face_cancel_cb(self, widget):
        self._notebook.set_current_page(0)

    def _set_face(self, view, type_):
        self._face_type = type_
        cartoon = type_ == FACE_CARTOON

        self.face.shut_up()
        self._box.remove(self.face)
        self._box.remove(self._entry_box)

        self.face = view
        self.face.set_size_request(
            -1, gtk.gdk.screen_height() - 2 * style.GRID_CELL_SIZE)

        if self._tablet_mode:
            self._box.pack_start(self._entry_box, expand=False)
            self._box.pack_start(self.face)
        else:
            self._box.pack_start(self.face, expand=True)
            self._box.pack_start(self._entry_box)
        self.face.show()

        if not cartoon and self._mode == MODE_CHAT:
            self._mode = MODE_TYPE
            self._mode_type.set_active(True)
            self._mode_chat.set_active(False)

            self._chat.shut_up()
            self._voice_palette.set_content(self._voice_box)
            self._set_voice()
        self._notebook.set_current_page(0)

        self._photo_face.set_sensitive(cartoon)
        self._clear.set_sensitive(not cartoon)
        for bnt in self._cartoon_face_buttons:
            bnt.set_sensitive(cartoon)
        self._mode_chat.set_sensitive(cartoon)


    def _clear_photo_cb(self, widget):
        lighter = style.Color(self._colors[_lighter_color(self._colors)])
        self._set_face(self._cartoon_face, FACE_CARTOON)

    def _face_palette_cb(self, button):
        palette = button.get_palette()
        if palette:
            if not palette.is_up():
                palette.popup(immediate=True, state=palette.SECONDARY)
            else:
                palette.popdown(immediate=True)

    def _get_active_mouth(self):
        for i, button in enumerate(self._mouth_type):
            if button.get_active():
                return MOUTHS[i]

    def _mouth_changed_cb(self, ignored, quiet):
        if self._face_type == FACE_PHOTO:
            return

        value = self._get_active_mouth()
        if value is None:
            return

        self.face.status.mouth = value
        self._update_face()

        # this SegFaults: self.face.say(combo.get_active_text())
        if not quiet:
            self.face.say_notification(_('mouth changed'))

    def _voices_changed_event_cb(self, widget, event, voice):
        logging.error('voices_changed_event_cb %r %s' % (voice[0], voice[1]))
        if self._mode == MODE_BOT:
            evboxes = self._brain_evboxes
        else:
            evboxes = self._voice_evboxes
        for old_voice in evboxes.keys():
            if evboxes[old_voice][1] == self.face.status.voice:
                evboxes[old_voice][0].modify_bg(
                    0, style.COLOR_BLACK.get_gdk_color())
                break

        evboxes[voice[1]][0].modify_bg(
            0, style.COLOR_BUTTON_GREY.get_gdk_color())

        self.face.set_voice(voice[0])
        if self._mode == MODE_BOT:
            brain.load(self, voice[0])
        else:
            self._current_voice = voice

    def _get_active_eyes(self):
        for name in EYE_DICT.keys():
            if EYE_DICT[name]['index'] == self._active_eyes:
                return EYE_DICT[name]['widget']
        return None

    def _eyes_changed_event_cb(self, widget, event, name, quiet):
        if self._face_type == FACE_PHOTO:
            return

        if self._active_eyes is not None:
            for old_name in EYE_DICT.keys():
                if EYE_DICT[old_name]['index'] == self._active_eyes:
                    self._eye_type[old_name].set_icon(old_name)
                    break

        if self._active_number_of_eyes is None:
            self._active_number_of_eyes = 2

        if name is not None:
            self._active_eyes = EYE_DICT[name]['index']
            self._eye_type[name].set_icon(name + '-selected')
            value = EYE_DICT[name]['widget']
            self.face.status.eyes = [value] * self._active_number_of_eyes
            self._update_face()
            if not quiet:
                self.face.say_notification(_('eyes changed'))

    def _number_of_eyes_changed_event_cb(self, widget, event, name, quiet):
        if self._face_type == FACE_PHOTO:
            return

        if self._active_number_of_eyes is not None:
            old_name = NUMBERS[self._active_number_of_eyes - 1]
            self._number_of_eyes_type[old_name].set_icon(old_name)

        if name in NUMBERS:
            self._active_number_of_eyes = NUMBERS.index(name) + 1
            self._number_of_eyes_type[name].set_icon(name + '-selected')
            if self._active_eyes is not None:
                for eye_name in EYE_DICT.keys():
                    if EYE_DICT[eye_name]['index'] == self._active_eyes:
                        value = EYE_DICT[eye_name]['widget']
                        self.face.status.eyes = \
                            [value] * self._active_number_of_eyes
                        self._update_face()
                        if not quiet:
                            self.face.say_notification(_('eyes changed'))
                        break

    def _update_face(self):
        self.face.update()
        self._chat.update(self.face.status)

    def _combo_changed_cb(self, combo):
        # when a new item is chosen, make sure the text is selected
        if not self._entry.is_focus():
            if not self._tablet_mode:
                self._entry.grab_focus()
            self._entry.select_region(0, -1)

    def _entry_key_press_cb(self, combo, event):
        # make the up/down arrows navigate through our history
        if self._tablet_mode:
            return
        keyname = gtk.gdk.keyval_name(event.keyval)
        if keyname == 'Up':
            index = self._entrycombo.get_active()
            if index > 0:
                index -= 1
            self._entrycombo.set_active(index)
            self._entry.select_region(0, -1)
            return True
        elif keyname == 'Down':
            index = self._entrycombo.get_active()
            if index < len(self._entrycombo.get_model()) - 1:
                index += 1
            self._entrycombo.set_active(index)
            self._entry.select_region(0, -1)
            return True
        return False

    def _entry_activate_cb(self, entry):
        # the user pressed Return, say the text and clear it out
        text = entry.props.text
        if self._tablet_mode:
            self._dismiss_OSK(entry)
            timeout = DELAY_BEFORE_SPEAKING
        else:
            timeout = 100
        gobject.timeout_add(timeout, self._speak_the_text, entry, text)

    def _dismiss_OSK(self, entry):
        entry.hide()
        entry.show()

    def _talk_cb(self, button):
        text = self._entry.props.text
        self._speak_the_text(self._entry, text)

    def _speak_the_text(self, entry, text):
        self._remove_idle()

        if text:
            self.face.look_ahead()

            # speak the text
            if self._mode == MODE_BOT:
                self.face.say(brain.respond(text))
            else:
                self.face.say(text)

        if text and not self._tablet_mode:
            # add this text to our history unless it is the same as
            # the last item
            history = self._entrycombo.get_model()
            if len(history) == 0 or history[-1][0] != text:
                self._entrycombo.append_text(text)
                # don't let the history get too big
                while len(history) > 20:
                    self._entrycombo.remove_text(0)
                # select the new item
                self._entrycombo.set_active(len(history) - 1)
        if text:
            # select the whole text
            entry.select_region(0, -1)

        # Launch an robot idle phase after 2 minutes
        self._robot_idle_id = gobject.timeout_add(IDLE_DELAY,
                                                  self._set_idle_phrase)

    def _load_sleeping_face(self):
        if self._face_type == FACE_PHOTO:
            return
        current_eyes = self.face.status.eyes
        self.face.status.eyes = [SLEEPY_EYES] * self._active_number_of_eyes
        self._update_face()
        self.face.status.eyes = current_eyes

    def _set_idle_phrase(self, speak=True):
        if speak:
            self._load_sleeping_face()
            idle_phrase = IDLE_PHRASES[random.randint(
                0, len(IDLE_PHRASES) - 1)]
            if self.props.active:
                self.face.say(idle_phrase)

        self._robot_idle_id = gobject.timeout_add(IDLE_DELAY,
                                                  self._set_idle_phrase)

    def _active_cb(self, widget, pspec):
        # only generate sound when this activity is active
        if not self.props.active:
            self._load_sleeping_face()
            self.face.shut_up()
            self._chat.shut_up()

    def _set_voice(self, new_voice=None):
        if new_voice is not None:
            logging.error('set_voice %r' % new_voice)
            self.face.status.voice = new_voice
        else:
            logging.error('set_voice to current voice %s' %
                          self._current_voice[1])
            self.face.status.voice = self._current_voice[0]

    def __toggled_mode_type_cb(self, button):
        if not button.props.active:
            return

        self._mode = MODE_TYPE
        self._chat.shut_up()
        self.face.shut_up()
        self._notebook.set_current_page(0)

        self._voice_palette.set_content(self._voice_box)
        self._set_voice()

    def __toggled_mode_robot_cb(self, button):
        if not button.props.active:
            return

        self._remove_idle()

        self._mode = MODE_BOT
        self._chat.shut_up()
        self.face.shut_up()
        self._notebook.set_current_page(0)

        self._voice_palette.set_content(self._brain_box)

        new_voice = None
        for name in brain.BOTS.keys():
            if self._current_voice[0].short_name == name:
                new_voice == self._current_voice[0]
                break
        if new_voice is None:
            new_voice = brain.get_default_voice()
            if new_voice.friendlyname in self._current_voice[0].friendlyname:
                logging.debug('skipping sorry message for %s %s' %
                              (new_voice.friendlyname,
                               self._current_voice[0].friendlyname))
                sorry = None
            else:
                sorry = _("Sorry, I can't speak %(old_voice)s, "
                          "let's talk %(new_voice)s instead.") % {
                              'old_voice': self._current_voice[0].friendlyname,
                              'new_voice': new_voice.friendlyname}
        else:
            new_voice = new_voice[0]
            sorry = None

        self._set_voice(new_voice)

        evboxes = self._brain_evboxes
        for old_voice in evboxes.keys():
            evboxes[old_voice][0].modify_bg(
                0, style.COLOR_BLACK.get_gdk_color())

        if new_voice.short_name in evboxes:
            evboxes[new_voice.short_name][0].modify_bg(
                0, style.COLOR_BUTTON_GREY.get_gdk_color())

        if not brain.load(self, new_voice, sorry):
            if sorry:
                self.face.say_notification(sorry)

    def __toggled_mode_chat_cb(self, button):
        if not button.props.active:
            return

        self._remove_idle()

        is_first_session = not self.shared_activity

        self._setup_chat_mode()

        if is_first_session:
            self._chat.me.say_notification(
                _('You are in off-line mode, share and invite someone.'))

    def _remove_idle(self):
        if self._robot_idle_id is not None:
            gobject.source_remove(self._robot_idle_id)

            if self._face_type == FACE_PHOTO:
                return

            value = self._get_active_eyes()
            if value is not None:
                self.face.status.eyes = [value] * self._active_number_of_eyes
                self._update_face()

    def _setup_chat_mode(self):
        self._mode = MODE_CHAT
        self._remove_idle()
        self.face.shut_up()
        self._notebook.set_current_page(1)

        self._voice_palette.set_content(self._voice_box)
        self._set_voice()

    def _shared_cb(self, sender):
        logging.error('SHARED A CHAT')
        self._setup_text_channel()

    def _joined_cb(self, sender):
        '''Joined a shared activity.'''
        if not self.shared_activity:
            return
        logger.error('JOINED A SHARED CHAT')
        for buddy in self.shared_activity.get_joined_buddies():
            self._buddy_already_exists(buddy)
        self._setup_text_channel()

    def _one_to_one_connection(self, tp_channel):
        '''Handle a private invite from a non-sugar3 XMPP client.'''
        if self.shared_activity or self.text_channel:
            return
        bus_name, connection, channel = json.loads(tp_channel)
        logger.debug('GOT XMPP: %s %s %s', bus_name, connection, channel)
        Connection(bus_name, connection, ready_handler=lambda conn:
                   self._one_to_one_connection_ready_cb(
                       bus_name, channel, conn))

    def _one_to_one_connection_ready_cb(self, bus_name, channel, conn):
        '''Callback for Connection for one to one connection'''
        text_channel = Channel(bus_name, channel)
        self.text_channel = TextChannelWrapper(text_channel, conn)
        self.text_channel.set_received_callback(self._received_cb)
        self.text_channel.handle_pending_messages()
        self.text_channel.set_closed_callback(
            self._one_to_one_connection_closed_cb)

        # XXX How do we detect the sender going offline?
        self._chat.chat_post.set_sensitive(True)
        # self._chat.chat_post.props.placeholder_text = None
        self._chat.chat_post.grab_focus()

    def _one_to_one_connection_closed_cb(self):
        '''Callback for when the text channel closes.'''
        pass

    def _setup_text_channel(self):
        logging.error('_SETUP_TEXTCHANNEL')
        self.text_channel = TextChannelWrapper(
            self.shared_activity.telepathy_text_chan,
            self.shared_activity.telepathy_conn)
        self.text_channel.set_received_callback(self._received_cb)
        self.shared_activity.connect('buddy-joined', self._buddy_joined_cb)
        self.shared_activity.connect('buddy-left', self._buddy_left_cb)
        self._chat.messenger = self.text_channel
        self._chat.chat_post.set_sensitive(True)
        self._chat.chat_post.grab_focus()

    def _buddy_joined_cb(self, sender, buddy):
        '''Show a buddy who joined'''
        if buddy == self.owner:
            return
        logging.error('%s joined the chat (%r)' % (buddy.props.nick, buddy))
        self._chat.post(
            buddy, _('%s joined the chat') % buddy.props.nick,
            status_message=True)

    def _buddy_left_cb(self, sender, buddy):
        '''Show a buddy who joined'''
        if buddy == self.owner:
            return
        logging.error('%s left the chat (%r)' % (buddy.props.nick, buddy))
        self._chat.post(
            buddy, _('%s left the chat') % buddy.props.nick,
            status_message=True)
        self._chat.farewell(buddy)

    def _buddy_already_exists(self, buddy):
        '''Show a buddy already in the chat.'''
        if buddy == self.owner:
            return
        logging.error('%s is here (%r)' % (buddy.props.nick, buddy))
        self._chat.post(
            buddy, _('%s is here') % buddy.props.nick,
            status_message=True)

    def _received_cb(self, buddy, text):
        '''Show message that was received.'''
        if buddy:
            if type(buddy) is dict:
                nick = buddy['nick']
            else:
                nick = buddy.props.nick
        else:
            nick = '???'
        logger.debug('Received message from %s: %s', nick, text)
        self._chat.post(buddy, text)


class TextChannelWrapper(object):
    '''Wrap a telepathy Text Channfel to make usage simpler.'''

    def __init__(self, text_chan, conn):
        '''Connect to the text channel'''
        self._activity_cb = None
        self._activity_close_cb = None
        self._text_chan = text_chan
        self._conn = conn
        self._logger = logging.getLogger(
            'chat-activity.TextChannelWrapper')
        self._signal_matches = []
        m = self._text_chan[CHANNEL_INTERFACE].connect_to_signal(
            'Closed', self._closed_cb)
        self._signal_matches.append(m)

    def post(self, text):
        if text is not None:
            self.send(text)

    def send(self, text):
        '''Send text over the Telepathy text channel.'''
        # XXX Implement CHANNEL_TEXT_MESSAGE_TYPE_ACTION
        logging.debug('sending %s' % text)

        text = text.replace('/', SLASH)

        if self._text_chan is not None:
            self._text_chan[CHANNEL_TYPE_TEXT].Send(
                CHANNEL_TEXT_MESSAGE_TYPE_NORMAL, text)

    def close(self):
        '''Close the text channel.'''
        self._logger.debug('Closing text channel')
        try:
            self._text_chan[CHANNEL_INTERFACE].Close()
        except Exception:
            self._logger.debug('Channel disappeared!')
            self._closed_cb()

    def _closed_cb(self):
        '''Clean up text channel.'''
        self._logger.debug('Text channel closed.')
        for match in self._signal_matches:
            match.remove()
        self._signal_matches = []
        self._text_chan = None
        if self._activity_close_cb is not None:
            self._activity_close_cb()

    def set_received_callback(self, callback):
        '''Connect the function callback to the signal.

        callback -- callback function taking buddy and text args
        '''
        if self._text_chan is None:
            return
        self._activity_cb = callback
        m = self._text_chan[CHANNEL_TYPE_TEXT].connect_to_signal(
            'Received', self._received_cb)
        self._signal_matches.append(m)

    def handle_pending_messages(self):
        '''Get pending messages and show them as received.'''
        for identity, timestamp, sender, type_, flags, text in \
            self._text_chan[
                CHANNEL_TYPE_TEXT].ListPendingMessages(False):
            self._received_cb(identity, timestamp, sender, type_, flags, text)

    def _received_cb(self, identity, timestamp, sender, type_, flags, text):
        '''Handle received text from the text channel.

        Converts sender to a Buddy.
        Calls self._activity_cb which is a callback to the activity.
        '''
        logging.debug('received_cb %r %s' % (type_, text))
        if type_ != 0:
            # Exclude any auxiliary messages
            return

        text = text.replace(SLASH, '/')

        if self._activity_cb:
            try:
                self._text_chan[CHANNEL_INTERFACE_GROUP]
            except Exception:
                # One to one XMPP chat
                nick = self._conn[
                    CONN_INTERFACE_ALIASING].RequestAliases([sender])[0]
                buddy = {'nick': nick, 'color': '#000000,#808080'}
                logging.error('Exception: recieved from sender %r buddy %r' %
                              (sender, buddy))
            else:
                # Normal sugar MUC chat
                # XXX: cache these
                buddy = self._get_buddy(sender)
                logging.error('Else: recieved from sender %r buddy %r' %
                              (sender, buddy))
            self._activity_cb(buddy, text)
            self._text_chan[
                CHANNEL_TYPE_TEXT].AcknowledgePendingMessages([identity])
        else:
            self._logger.debug('Throwing received message on the floor'
                               ' since there is no callback connected. See'
                               ' set_received_callback')

    def set_closed_callback(self, callback):
        '''Connect a callback for when the text channel is closed.

        callback -- callback function taking no args

        '''
        self._activity_close_cb = callback

    def _get_buddy(self, cs_handle):
        '''Get a Buddy from a (possibly channel-specific) handle.'''
        # XXX This will be made redundant once Presence Service
        # provides buddy resolution
        # Get the Presence Service
        pservice = presenceservice.get_instance()
        # Get the Telepathy Connection
        tp_name, tp_path = pservice.get_preferred_connection()
        conn = Connection(tp_name, tp_path)
        group = self._text_chan[CHANNEL_INTERFACE_GROUP]
        my_csh = group.GetSelfHandle()
        if my_csh == cs_handle:
            handle = conn.GetSelfHandle()
        elif group.GetGroupFlags() & \
             CHANNEL_GROUP_FLAG_CHANNEL_SPECIFIC_HANDLES:
            handle = group.GetHandleOwners([cs_handle])[0]
        else:
            handle = cs_handle

            # XXX: deal with failure to get the handle owner
            assert handle != 0

        return pservice.get_buddy_by_telepathy_handle(
            tp_name, tp_path, handle)


class ToolWidget(gtk.ToolItem):

    def __init__(self, **kwargs):
        self._widget = None
        self._label = None
        self._label_text = None
        self._box = gtk.HBox(False, style.DEFAULT_SPACING)

        gobject.GObject.__init__(self, **kwargs)
        self.props.border_width = style.DEFAULT_PADDING

        self._box.show()
        self.add(self._box)

        if self.label is None:
            self.label = gtk.Label()

    def get_label_text(self):
        return self._label_text

    def set_label_text(self, value):
        self._label_text = value
        if self.label is not None and value:
            self.label.set_text(self._label_text)

    label_text = gobject.property(getter=get_label_text, setter=set_label_text)

    def get_label(self):
        return self._label

    def set_label(self, label):
        if self._label is not None:
            self._box.remove(self._label)
        self._label = label
        self._box.pack_start(label, False)
        self._box.reorder_child(label, 0)
        label.show()
        self.set_label_text(self._label_text)

    label = gobject.property(getter=get_label, setter=set_label)

    def get_widget(self):
        return self._widget

    def set_widget(self, widget):
        if self._widget is not None:
            self._box.remove(self._widget)
        self._widget = widget
        self._box.pack_end(widget)
        widget.show()

    widget = gobject.property(getter=get_widget, setter=set_widget)


# activate gtk threads when this module loads
gtk.gdk.threads_init()
