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

import gtk
import pango
import hippo
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

logger = logging.getLogger('speak')

BUDDY_SIZE = min(100, min(gtk.gdk.screen_width(),
        gtk.gdk.screen_height() - style.LARGE_ICON_SIZE) / 5)
BUDDY_XPAD = 0
BUDDY_YPAD = 5

BUDDIES_WIDTH = int(BUDDY_SIZE * 2.5)
BUDDIES_COLOR = style.COLOR_SELECTION_GREY

ENTRY_COLOR = style.COLOR_PANEL_GREY
ENTRY_XPAD = 0
ENTRY_YPAD = 7

class Toolbar(gtk.Toolbar):
    def __init__(self, chat):
        gtk.Toolbar.__init__(self)
        self.chat = chat

        mute = ToggleToolButton('stock_volume-mute')
        mute.set_tooltip(_('Mute'))
        mute.connect('toggled', self._toggled_cb)
        mute.show()
        self.insert(mute, -1)

    def _toggled_cb(self, widget):
        if widget.get_active():
            self.chat.quiet = True
            self.chat.shut_up()
        else:
            self.chat.quiet = False

class View(hippo.Canvas):
    def __init__(self):
        hippo.Canvas.__init__(self)

        self.messenger = None
        self.me = None
        self.quiet = False

        self._buddies = {}
        self.connect('motion_notify_event', self._motion_notify_cb)

        # buddies box

        self._buddies_list = hippo.CanvasBox(
                background_color = BUDDIES_COLOR.get_int(),
                box_width = BUDDIES_WIDTH,
                padding = ENTRY_YPAD,
                spacing = ENTRY_YPAD
                )

        self._buddies_box = hippo.CanvasScrollbars()
        self._buddies_box.set_policy(hippo.ORIENTATION_HORIZONTAL,
                hippo.SCROLLBAR_NEVER)
        self._buddies_box.set_root(self._buddies_list)

        # chat entry

        self._chat = ChatBox()
        self.me, my_face_widget = self._new_face(self._chat.owner,
                ENTRY_COLOR)

        chat_post = gtk.TextView()
        chat_post.modify_bg(gtk.STATE_INSENSITIVE,
                style.COLOR_WHITE.get_gdk_color())
        chat_post.modify_base(gtk.STATE_INSENSITIVE,
                style.COLOR_WHITE.get_gdk_color())
        chat_post.connect('key-press-event', self._key_press_cb)
        chat_post.props.wrap_mode = gtk.WRAP_WORD_CHAR
        chat_post.set_size_request(-1, BUDDY_SIZE - ENTRY_YPAD*2)

        chat_post_box = CanvasRoundBox(
                background_color = style.COLOR_WHITE.get_int(),
                padding_left = ENTRY_XPAD,
                padding_right = ENTRY_XPAD,
                padding_top = ENTRY_YPAD,
                padding_bottom = ENTRY_YPAD
                )
        chat_post_box.props.border_color = ENTRY_COLOR.get_int()
        chat_post_box.append(hippo.CanvasWidget(widget=chat_post),
                hippo.PACK_EXPAND)

        chat_entry = CanvasRoundBox(
                background_color = ENTRY_COLOR.get_int(),
                padding_left = ENTRY_XPAD,
                padding_right = ENTRY_XPAD,
                padding_top = ENTRY_YPAD,
                padding_bottom = ENTRY_YPAD,
                spacing = ENTRY_YPAD
                )
        chat_entry.props.orientation = hippo.ORIENTATION_HORIZONTAL
        chat_entry.props.border_color = style.COLOR_WHITE.get_int()
        chat_entry.append(my_face_widget)
        chat_entry.append(chat_post_box, hippo.PACK_EXPAND)

        chat_box = hippo.CanvasBox(
                orientation = hippo.ORIENTATION_VERTICAL,
                background_color = style.COLOR_WHITE.get_int(),
                )
        chat_box.append(self._chat, hippo.PACK_EXPAND)
        chat_box.append(chat_entry)

        # desk

        self._desk = hippo.CanvasBox()
        self._desk.props.orientation=hippo.ORIENTATION_HORIZONTAL
        self._desk.append(chat_box, hippo.PACK_EXPAND)

        self.set_root(self._desk)

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
            if not self.quiet and self.props.window \
                    and self.props.window.is_visible():
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
            i['face'].shut_up();
        self.me.shut_up();

    def _add_buddy(self, buddy):
        box = hippo.CanvasBox(
                orientation = hippo.ORIENTATION_HORIZONTAL,
                background_color = BUDDIES_COLOR.get_int(),
                spacing = ENTRY_YPAD
                )

        buddy_face, buddy_widget = self._new_face(buddy, BUDDIES_COLOR)
        
        char_box = hippo.CanvasBox(
                orientation = hippo.ORIENTATION_VERTICAL,
                )
        nick = hippo.CanvasText(
                text = buddy.props.nick,
                xalign = hippo.ALIGNMENT_START,
                yalign = hippo.ALIGNMENT_START
                )
        lang = hippo.CanvasText(
                text = '',
                xalign = hippo.ALIGNMENT_START,
                yalign = hippo.ALIGNMENT_START
                )
        char_box.append(nick)
        char_box.append(lang)

        box.append(buddy_widget)
        box.append(char_box, hippo.PACK_EXPAND)

        self._buddies[buddy] = {
                'box'   : box,
                'face'  : buddy_face,
                'lang'  : lang
                }
        self._buddies_list.append(box)

        if len(self._buddies) == 1:
            self._desk.append(self._buddies_box)

    def _key_press_cb(self, widget, event):
        if event.keyval == gtk.keysyms.Return:
            if not (event.state & gtk.gdk.CONTROL_MASK):
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

        inner = CanvasRoundBox(
                background_color = fill_color.get_int(),
                padding_top = BUDDY_YPAD,
                padding_bottom = BUDDY_YPAD,
                padding_left = BUDDY_XPAD,
                padding_right = BUDDY_XPAD,
                )
        inner.props.border_color = fill_color.get_int()
        inner.append(hippo.CanvasWidget(widget=buddy_face), hippo.PACK_EXPAND)

        outer = CanvasRoundBox(
                background_color = stroke_color.get_int(),
                box_width = BUDDY_SIZE,
                box_height = BUDDY_SIZE,
                padding_top = BUDDY_YPAD,
                padding_bottom = BUDDY_YPAD,
                padding_left = BUDDY_XPAD,
                padding_right = BUDDY_XPAD
                )
        outer.props.border_color = stroke_color.get_int()
        outer.append(inner, hippo.PACK_EXPAND)

        return (buddy_face, outer)

    def _look_at(self, x, y):
        self.me.look_at(x, y)
        for i in self._buddies.values():
            i['face'].look_at(x, y)

    def _motion_notify_cb(self, widget, event):
        display = gtk.gdk.display_get_default()
        screen, x, y, modifiers = display.get_pointer()
        self._look_at(x,y)
