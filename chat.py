# Copyright (C) 2009, Aleksey Lim
# Copyright (C) 2014, Walter Bender (remove hippo)
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

import os
import gtk
import pango
import subprocess
import logging
from gettext import gettext as _

import sugar.graphics.style as style
from sugar.graphics.roundbox import CanvasRoundBox
from sugar.graphics.toggletoolbutton import ToggleToolButton

import eye
import glasses
import mouth
import face
import messenger
from chatbox import ChatBox
from sugar.presence import presenceservice

logger = logging.getLogger('speak')

BUDDY_SIZE = int(style.GRID_CELL_SIZE * 1.5)
BUDDY_PAD = 5

BUDDIES_WIDTH = int(BUDDY_SIZE * 5)
BUDDIES_COLOR = style.COLOR_SELECTION_GREY

ENTRY_COLOR = style.COLOR_PANEL_GREY
ENTRY_XPAD = 0
ENTRY_YPAD = 7


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


class View(gtk.EventBox):
    def __init__(self):
        gtk.EventBox.__init__(self)

        self.messenger = None
        self.me = None
        self.quiet = False

        self._buddies = {}

        # buddies box

        self._buddies_box = gtk.ScrolledWindow()
        self._buddies_box.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_NEVER)
        self._buddies_box.set_size_request(BUDDY_SIZE, BUDDY_SIZE)

        self._buddies_list = gtk.HBox()
        self._buddies_list.set_size_request(BUDDY_SIZE, BUDDY_SIZE)
        self._buddies_box.add_with_viewport(self._buddies_list)
        self._buddies_list.show()

        # chat entry

        self.owner = presenceservice.get_instance().get_owner()
        self._chat = ChatBox(self.owner, _is_tablet_mode())
        self._chat.set_size_request(
            -1, gtk.gdk.screen_height() - style.GRID_CELL_SIZE - BUDDY_SIZE)
        self.me, my_face_widget = self._new_face(self.owner, # self._chat.owner,
                ENTRY_COLOR)
        my_face_widget.set_size_request(BUDDY_SIZE, BUDDY_SIZE)

        self.chat_post = gtk.Entry()
        entry_height = int(BUDDY_SIZE)
        entry_width = gtk.gdk.screen_width() - \
                      max(1, min(5, len(self._buddies_list))) * BUDDY_SIZE
        self.chat_post.set_size_request(entry_width, entry_height)
        self.chat_post.modify_bg(gtk.STATE_NORMAL,
                                 style.COLOR_WHITE.get_gdk_color())
        self.chat_post.modify_base(gtk.STATE_NORMAL,
                                   style.COLOR_WHITE.get_gdk_color())
        self.chat_post.modify_font(pango.FontDescription(str='sans bold 24'))
        self.chat_post.connect('activate', self._activate_cb)
        self.chat_post.connect('key-press-event', self._key_press_cb)

        chat_post_box = gtk.VBox()
        chat_post_box.pack_start(self.chat_post, padding=ENTRY_XPAD)
        self.chat_post.show()

        chat_entry = gtk.HBox()
        self._buddies_list.pack_start(my_face_widget)
        chat_entry.pack_start(self._buddies_box)
        my_face_widget.show()
        chat_entry.pack_start(chat_post_box)
        chat_post_box.show()

        chat_box = gtk.VBox()
        chat_box.pack_start(self._chat, expand=True)
        self._chat.show()
        chat_box.pack_start(chat_entry)
        chat_entry.show()

        # desk
        self._desk = gtk.HBox()
        self._desk.pack_start(chat_box)
        self.add(self._desk)
        self._desk.show()

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

    def _resize_buddy_list(self):
        self._buddies_list.set_size_request(
            len(self._buddies_list) * BUDDY_SIZE, -1)
        self._buddies_box.set_size_request(
            min(5, len(self._buddies_list)) * BUDDY_SIZE, -1)
        self.chat_post.set_size_request(
            gtk.gdk.screen_width() -
            min(5, len(self._buddies_list)) * BUDDY_SIZE, -1)

    def farewell(self, buddy):
        i = self._buddies.get(buddy)
        if not i:
            logger.debug('farewell: cannot find buddy %s' % buddy.props.nick)
            return

        self._buddies_list.remove(i['box'])
        del self._buddies[buddy]
        self._resize_buddy_list()

        if len(self._buddies) == 0:
            self._desk.remove(self._buddies_box)

    def shut_up(self):
        for i in self._buddies.values():
            i['face'].shut_up();
        self.me.shut_up();

    def _add_buddy(self, buddy):
        box = gtk.VBox()
        buddy_face, buddy_widget = self._new_face(buddy, BUDDIES_COLOR)
        box.pack_start(buddy_widget)
        buddy_widget.show()
        self._buddies[buddy] = {
                'box': box,
                'face': buddy_face,
                'lang': lang
                }
        self._buddies_list.append(box)
        box.show()
        self._resize_buddy_list()

        if len(self._buddies) == 1:
            self._desk.append(self._buddies_box)

    def _activate_cb(self, widget, event):
        text = widget.get_buffer().props.text
        if text:
            self._chat.add_text(None, text)
            widget.get_buffer().props.text = ''
            if not self.quiet:
                self.me.say(text)
            if self.messenger:
                self.messenger.post(text)
        return True

    def _key_press_cb(self, widget, event):
        if event.keyval == gtk.keysyms.Return:
            if not (event.state & gtk.gdk.CONTROL_MASK):
                return self._activate_cb(widget, event)
        return False

    def _new_face(self, buddy, color):
        stroke_color, fill_color = buddy.props.color.split(',')
        stroke_color = style.Color(stroke_color)
        fill_color = style.Color(fill_color)

        buddy_face = face.View(fill_color)
        buddy_face.set_border_state(False)
        buddy_face.set_size_request(BUDDY_SIZE - style.DEFAULT_PADDING,
                                    BUDDY_SIZE - style.DEFAULT_PADDING)

        outer = gtk.VBox()
        outer.set_size_request(BUDDY_SIZE, BUDDY_SIZE)
        outer.pack_start(buddy_face)
        buddy_face.show_all()

        return (buddy_face, outer)

    def look_at(self):
        self.me.look_at()
        for i in self._buddies.values():
            i['face'].look_at()
