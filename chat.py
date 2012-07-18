# Copyright (C) 2009, Aleksey Lim
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA

from gi.repository import Gtk
from gi.repository import Gdk
from gi.repository import GObject
from gi.repository import Pango
import logging
from gettext import gettext as _

import sugar3.graphics.style as style
from roundbox import RoundBox
from sugar3.graphics.toggletoolbutton import ToggleToolButton

import eye
import glasses
import mouth
import face
import messenger
from chatbox import ChatBox

logger = logging.getLogger('speak')

BUDDY_SIZE = min(100, min(Gdk.Screen.width(),
        Gdk.Screen.height() - style.LARGE_ICON_SIZE) / 5)
BUDDY_PAD = 5

BUDDIES_WIDTH = int(BUDDY_SIZE * 2.5)
BUDDIES_COLOR = style.COLOR_SELECTION_GREY

ENTRY_COLOR = style.COLOR_PANEL_GREY
ENTRY_XPAD = 0
ENTRY_YPAD = 7


class View(Gtk.EventBox):
    def __init__(self):
        Gtk.EventBox.__init__(self)

        self.messenger = None
        self.me = None
        self.quiet = False

        self._buddies = {}

        # buddies box

        self._buddies_list = Gtk.VBox()
        self._buddies_list.set_homogeneous(False)
        self._buddies_list.props.spacing = ENTRY_YPAD

        self._buddies_box = Gtk.ScrolledWindow()
        self._buddies_box.set_policy(Gtk.PolicyType.ALWAYS,
                                     Gtk.PolicyType.NEVER)
        evbox = Gtk.EventBox()
        evbox.modify_bg(Gtk.StateType.NORMAL, BUDDIES_COLOR.get_gdk_color())
        evbox.add(self._buddies_list)
        evbox.show()
        self._buddies_box.add_with_viewport(evbox)

        # chat entry

        self._chat = ChatBox()
        self.me, my_face_widget = self._new_face(self._chat.owner,
                ENTRY_COLOR)

        chat_post = Gtk.TextView()
        chat_post.modify_bg(Gtk.StateType.INSENSITIVE,
                style.COLOR_WHITE.get_gdk_color())
        chat_post.modify_base(Gtk.StateType.INSENSITIVE,
                style.COLOR_WHITE.get_gdk_color())
        chat_post.connect('key-press-event', self._key_press_cb)
        chat_post.props.wrap_mode = Gtk.WrapMode.WORD_CHAR
        chat_post.set_size_request(-1, BUDDY_SIZE - ENTRY_YPAD * 2)
        chat_post_box = RoundBox()
        chat_post_box.background_color = style.COLOR_WHITE
        chat_post_box.border_color = ENTRY_COLOR
        chat_post_box.pack_start(chat_post, True, True, ENTRY_XPAD)

        chat_entry = RoundBox()
        chat_entry.set_border_width(ENTRY_YPAD)
        chat_entry.background_color = ENTRY_COLOR
        chat_entry.border_color = style.COLOR_WHITE
        chat_entry.pack_start(my_face_widget, False, True, 0)
        separator = Gtk.EventBox()
        separator.modify_bg(Gtk.StateType.NORMAL, ENTRY_COLOR.get_gdk_color())
        separator.set_size_request(ENTRY_YPAD, -1)
        separator.show()
        chat_entry.pack_start(separator, False, False, 0)
        chat_entry.pack_start(chat_post_box, True, True, ENTRY_XPAD)

        evbox = Gtk.EventBox()
        evbox.modify_bg(Gtk.StateType.NORMAL, style.COLOR_WHITE.get_gdk_color())
        chat_box = Gtk.VBox()
        chat_box.pack_start(self._chat, True, True, 0)
        chat_box.pack_start(chat_entry, False, True, 0)
        evbox.add(chat_box)

        # desk

        self._desk = Gtk.HBox()
        self._desk.pack_start(evbox, True, True, 0)
        self._desk.show_all()

        self.add(self._desk)

    def update(self, status):
        self.me.update(status)
        if self.messenger:
            self.messenger.post(None)

    def post(self, buddy, status, text):
        i = self._buddies.get(buddy)
        if not i:
            self._add_buddy(buddy)
            i = self._buddies[buddy]

        face = i['face']
        lang_box = i['lang']

        if status:
            face.update(status)
            if lang_box:
                lang_box.props.text = status.voice.friendlyname
        if text:
            self._chat.add_text(buddy, text)
            if not self.quiet:
                # and self.props.window \
                #    and self.props.window.is_visible():
                face.say(text)

    def farewell(self, buddy):
        i = self._buddies.get(buddy)
        if not i:
            logger.debug('farewell: cannot find buddy %s' % buddy.props.nick)
            return

        self._buddies_list.remove(i['box'])
        del self._buddies[buddy]

        if len(self._buddies) == 0:
            self._desk.remove(self._buddies_box)

    def shut_up(self):
        for i in self._buddies.values():
            i['face'].shut_up()
        self.me.shut_up()

    def _add_buddy(self, buddy):
        evbox = Gtk.EventBox()
        evbox.modify_bg(Gtk.StateType.NORMAL, BUDDIES_COLOR.get_gdk_color())
        box = Gtk.HBox()

        buddy_face, buddy_widget = self._new_face(buddy, BUDDIES_COLOR)

        char_box = Gtk.VBox()
        nick = Gtk.Label(label=buddy.props.nick)
        lang = Gtk.Label()
        char_box.pack_start(nick, True, True, 0)
        char_box.pack_start(lang, True, True, 0)

        box.pack_start(buddy_widget, False, False, ENTRY_YPAD)
        box.pack_start(char_box, True, True, ENTRY_YPAD)

        self._buddies[buddy] = {
                'box': box,
                'face': buddy_face,
                'lang': lang
                }
        self._buddies_list.pack_start(box, True, True, 0)

        if len(self._buddies) == 1:
            self._desk.pack_start(self._buddies_box, True, True, 0)

    def _key_press_cb(self, widget, event):
        if event.keyval == Gdk.KEY_Return:
            if not (event.get_state() & Gdk.ModifierType.CONTROL_MASK):
                text = widget.get_buffer().props.text

                if text:
                    self._chat.add_text(None, text)
                    widget.get_buffer().props.text = ''
                    if not self.quiet:
                        self.me.say(text)
                    if self.messenger:
                        self.messenger.post(text)

                return True
        return False

    def _new_face(self, buddy, color):
        stroke_color, fill_color = buddy.props.color.split(',')
        stroke_color = style.Color(stroke_color)
        fill_color = style.Color(fill_color)

        buddy_face = face.View(fill_color)
        buddy_face.show_all()

        inner = RoundBox()
        inner.set_border_width(BUDDY_PAD)
        inner.background_color = fill_color
        inner.border_color = fill_color
        inner.pack_start(buddy_face, True, True, 0)
        inner.border = BUDDY_PAD

        outer = RoundBox()
        outer.set_border_width(BUDDY_PAD)
        outer.background_color = stroke_color
        outer.set_size_request(BUDDY_SIZE, BUDDY_SIZE)
        outer.border_color = stroke_color
        outer.pack_start(inner, True, True, 0)
        outer.border = BUDDY_PAD

        return (buddy_face, outer)

    def look_at(self):
        self.me.look_at()
        for i in self._buddies.values():
            i['face'].look_at()
