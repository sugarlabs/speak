# Copyright 2007-2008 One Laptop Per Child
# Copyright 2009, Aleksey Lim
# Copyright 2010, Mukesh Gupta
# Copyright 2014, Walter Bender
# Copyright 2014, Gonzalo Odiard
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

import re
import time
import logging
from datetime import datetime
from gettext import gettext as _

import gobject
import gtk
import pango

from sugar.graphics import style
'''
from sugar.graphics.palette import Palette, Invoker
from sugar.graphics.palettemenu import PaletteMenuItem
from sugar.graphics.palette import MouseSpeedDetector
'''
from sugar.util import timestamp_to_elapsed_string
from sugar import profile

from roundbox import RoundBox


_URL_REGEXP = re.compile(
    '((http|ftp)s?://)?'
    '(([-a-zA-Z0-9]+[.])+[-a-zA-Z0-9]{2,}|([0-9]{1,3}[.]){3}[0-9]{1,3})'
    '(:[1-9][0-9]{0,4})?(/[-a-zA-Z0-9/%~@&_+=;:,.?#]*[a-zA-Z0-9/])?')


def _luminance(color):
    ''' Calculate luminance value '''
    return int(color[1:3], 16) * 0.3 + int(color[3:5], 16) * 0.6 + \
        int(color[5:7], 16) * 0.1


def is_low_contrast(colors):
    ''' We require lots of luminance contrast to make color text legible. '''
    # To turn off color on color, always return False
    return _luminance(colors[0]) - _luminance(colors[1]) < 96


def is_dark_too_light(color):
    return _luminance(color) > 96


def lighter_color(colors):
    ''' Which color is lighter? Use that one for the text nick color '''
    if _luminance(colors[0]) > _luminance(colors[1]):
        return 0
    return 1


def darker_color(colors):
    ''' Which color is darker? Use that one for the text background '''
    return 1 - lighter_color(colors)


class TextBox(gtk.EventBox):

    '''
    __gsignals__ = {
        'open-on-journal': (gobject.SignalFlags.RUN_FIRST, None, ([str])), }

    # hand_cursor = gtk.gdk.Cursor.new(Gdk.CursorType.HAND2)
    '''

    def __init__(self, parent,
                 name_color, text_color, bg_color, highlight_color,
                 lang_rtl, nick_name=None, text=None):
        gtk.EventBox.__init__(self)

        self.textview = gtk.TextView()

        self.set_size_request(-1, style.GRID_CELL_SIZE)
        self.add(self.textview)
        self.textview.show()

        self._parent = parent
        self._buffer = gtk.TextBuffer()
        self._empty_buffer = gtk.TextBuffer()
        self._empty_buffer.set_text('')
        self._empty = True
        self._name_tag = self._buffer.create_tag(
            'name', foreground=name_color.get_html(), weight=pango.WEIGHT_BOLD,
            background=bg_color.get_html())
        self._fg_tag = self._buffer.create_tag(
            'foreground_color', foreground=text_color.get_html(),
            background=bg_color.get_html())
        self._subscript_tag = self.textview.get_buffer().create_tag(
            'subscript', foreground=text_color.get_html(),
            background=bg_color.get_html(),
            rise=-7 * pango.SCALE)  # in pixels

        if nick_name:
            self._add_name(nick_name)
            self.add_text(text, newline=False)
        elif text:
            self.add_text(text)

        self.resize_box()

        self._lang_rtl = lang_rtl
        self.textview.set_editable(False)
        self.textview.set_cursor_visible(False)
        self.textview.set_wrap_mode(gtk.WRAP_WORD)

        self.textview.modify_base(gtk.STATE_NORMAL, bg_color.get_gdk_color())

        self.connect('size-allocate', self.__size_allocate_cb)

    def __size_allocate_cb(self, widget, allocation):
        ''' Load buffer after resize to circumvent race condition '''
        self.textview.set_buffer(self._buffer)
        self._parent.resize_rb()

    def resize_box(self):
        self.textview.set_buffer(self._empty_buffer)
        self.set_size_request(gtk.gdk.screen_width() - style.GRID_CELL_SIZE
                              - 2 * style.DEFAULT_SPACING, -1)

    def _add_name(self, name):
        buf = self._buffer
        self.iter_text = self._buffer.get_iter_at_offset(0)
        words = name.split()
        for word in words:
            buf.insert_with_tags(self.iter_text, word, self._name_tag)
            buf.insert_with_tags(self.iter_text, ' ', self._fg_tag)

        self._empty = False

    def add_text(self, text, newline=True):
        buf = self._buffer
        self.iter_text = self._buffer.get_end_iter()

        if not self._empty:
            if newline:
                buf.insert(self.iter_text, '\n')
            else:
                buf.insert(self.iter_text, ' ')

        words = text.split()
        for word in words:
            buf.insert_with_tags(self.iter_text, word, self._fg_tag)
            buf.insert_with_tags(self.iter_text, ' ', self._fg_tag)

        self._empty = False


class ChatBox(gtk.ScrolledWindow):

    def __init__(self, owner, tablet_mode):
        gtk.ScrolledWindow.__init__(self)

        if owner is None:
            self._owner = {'nick': profile.get_nick_name(),
                           'color': profile.get_color().to_string()}
        else:
            self._owner = owner

        self._tablet_mode = tablet_mode

        # Auto vs manual scrolling:
        self._scroll_auto = True
        self._scroll_value = 0.0
        self._last_msg_sender = None
        # Track last message, to combine several messages:
        self._last_msg = None
        self._chat_log = ''
        self._row_counter = 0

        # We need access to individual messages for resizing
        # TODO: use a signal for this
        self._rb_list = []
        self._grid_list = []
        self._message_list = []

        self._conversation = gtk.VBox()
        # self._conversation.set_row_spacing(style.DEFAULT_PADDING)
        # self._conversation.set_border_width(0)
        self._conversation.set_size_request(
            gtk.gdk.screen_width() - style.GRID_CELL_SIZE, -1)

        # OSK padding for conversation
        self._dy = 0

        evbox = gtk.EventBox()
        evbox.modify_bg(
            gtk.STATE_NORMAL, style.COLOR_WHITE.get_gdk_color())
        evbox.add(self._conversation)
        self._conversation.show()

        self.set_policy(gtk.POLICY_NEVER, gtk.POLICY_ALWAYS)
        self.add_with_viewport(evbox)
        evbox.show()

        vadj = self.get_vadjustment()
        vadj.connect('changed', self._scroll_changed_cb)
        vadj.connect('value-changed', self._scroll_value_changed_cb)

    def get_log(self):
        return self._chat_log

    def add_text(self, buddy, text, status_message=False):
        '''Display text on screen, with name and colors.
        buddy -- buddy object or dict {nick: string, color: string}
        (The dict is for loading the chat log from the journal,
        when we don't have the buddy object any more.)
        text -- string, what the buddy said
        status_message -- boolean
        False: show what buddy said
        True: show what buddy did

        .----- rb ------------.
        |  +----align-------+ |
        |  | +--message---+ | |
        |  | | nick:      | | |
        |  | | text 1     | | |
        |  | | text 2     | | |
        |  | +------------+ | |
        |  +----------------+ |
        `----------------- +--'
                          \|

        The color scheme for owner messages is:
        nick in darker of stroke and fill colors
        background in lighter of stroke and fill colors
        text in black

        The color scheme for buddy messages is:
        nick in darker of stroke and fill colors
        background in light gray
        text in black

        rb has a tail on the right for owner messages and the left for
        buddy messages.
        '''
        if not buddy:
            buddy = self._owner

        if type(buddy) is dict:
            # dict required for loading chat log from journal
            nick = buddy['nick']
            color = buddy['color']
        elif buddy is None:
            nick = 'unknown'
            color = '#000000,#808080'
        else:
            nick = buddy.props.nick
            color = buddy.props.color
        try:
            color_stroke_html, color_fill_html = color.split(',')
        except ValueError:
            color_stroke_html, color_fill_html = ('#000000', '#888888')

        lighter = lighter_color(color.split(','))
        darker = 1 - lighter

        if len(text) > 3 and text[0:4] == '/me ':
            me_message = True
        else:
            me_message = False

        if status_message or me_message:
            text_color = style.COLOR_WHITE
            nick_color = style.COLOR_WHITE
            color_fill = style.Color('#808080')
            highlight_fill = style.COLOR_WHITE
            tail = None
        else:
            highlight_fill = style.COLOR_BUTTON_GREY
            text_color = style.COLOR_BLACK
            if darker == 1:
                color_fill = style.Color(color_stroke_html)
                if is_low_contrast(color.split(',')):
                    nick_color = text_color
                else:
                    nick_color = style.Color(color_fill_html)
            else:
                color_fill = style.Color(color_fill_html)
                if is_low_contrast(color.split(',')):
                    nick_color = text_color
                else:
                    nick_color = style.Color(color_stroke_html)
            if nick == profile.get_nick_name():
                tail = 'right'
            else:
                tail = 'left'

        color_stroke = None

        self._add_log(nick, color, text, status_message)

        # Check for Right-To-Left languages:
        if pango.find_base_dir(nick, -1) == pango.DIRECTION_RTL:
            lang_rtl = True
        else:
            lang_rtl = False

        # Check if new message box or add text to previous:
        new_msg = True
        if self._last_msg_sender and buddy == self._last_msg_sender:
            # Add text to previous message
            if not (me_message or status_message):
                new_msg = False

        if not new_msg:
            message = self._last_msg
            message.add_text(text)
        else:
            rb = RoundBox()
            rb.background_color = color_fill
            rb.border_color = color_stroke
            rb.tail = tail
            self._rb_list.append(rb)

            grid_internal = gtk.VBox()
            grid_internal.set_size_request(
                gtk.gdk.screen_width() - style.GRID_CELL_SIZE,
                style.GRID_CELL_SIZE)  # -1)
            self._grid_list.append(grid_internal)

            row = 0

            if status_message:
                nick = None
            elif me_message:
                text = text[4:]

            message = TextBox(self, nick_color, text_color, color_fill,
                              highlight_fill, lang_rtl, nick, text)
            self._message_list.append(message)

            self._last_msg_sender = buddy
            self._last_msg = message

            grid_internal.pack_start(message, expand=False, padding=0)
            row += 1

            align = gtk.Alignment(0.0, 0.0, 1.0, 1.0)
            if rb.tail is None:
                bottom_padding = style.zoom(7)
            else:
                bottom_padding = style.zoom(40)
            align.set_padding(style.zoom(7), bottom_padding, style.zoom(30),
                              style.zoom(30))

            align.add(grid_internal)
            grid_internal.show()

            rb.pack_start(align, True, True, 0)
            align.show()

            self._conversation.pack_start(rb, expand=False,
                                          padding=style.DEFAULT_PADDING)
            rb.show()
            self._row_counter += 1
            message.show()

        if status_message:
            self._last_msg_sender = None

    def add_separator(self, timestamp):
        '''Add whitespace and timestamp between chat sessions.'''
        time_with_current_year = \
            (time.localtime(time.time())[0], ) + \
            time.strptime(timestamp, '%b %d %H:%M:%S')[1:]

        timestamp_seconds = time.mktime(time_with_current_year)
        if timestamp_seconds > time.time():
            time_with_previous_year = \
                (time.localtime(time.time())[0] - 1, ) + \
                time.strptime(timestamp, '%b %d %H:%M:%S')[1:]
            timestamp_seconds = time.mktime(time_with_previous_year)

        message = TextBox(self,
                          style.COLOR_BUTTON_GREY, style.COLOR_BUTTON_GREY,
                          style.COLOR_WHITE, style.COLOR_BUTTON_GREY, False,
                          None, timestamp_to_elapsed_string(timestamp_seconds))
        self._message_list.append(message)
        box = gtk.HBox()
        align = gtk.Alignment(0.5, 0.0, 0.0, 0.0)
        box.pack_start(align, True, True, 0)
        align.show()
        align.add(message)
        message.show()
        self._conversation.pack_start(box)
        box.show()
        self._row_counter += 1
        self.add_log_timestamp(timestamp)
        self._last_msg_sender = None

    def add_log_timestamp(self, existing_timestamp=None):
        '''Add a timestamp entry to the chat log.'''
        if existing_timestamp is not None:
            self._chat_log += '%s\t\t\n' % existing_timestamp
        else:
            self._chat_log += '%s\t\t\n' % (
                datetime.strftime(datetime.now(), '%b %d %H:%M:%S'))

    def _add_log(self, nick, color, text, status_message):
        '''Add the text to the chat log.
        nick -- string, buddy nickname
        color -- string, buddy.props.color
        text -- string, body of message
        status_message -- boolean
        '''
        if not nick:
            nick = '???'
        if not color:
            color = '#000000,#FFFFFF'
        if not text:
            text = '-'
        if not status_message:
            status_message = False
        self._chat_log += '%s\t%s\t%s\t%d\t%s\n' % (
            datetime.strftime(datetime.now(), '%b %d %H:%M:%S'),
            nick, color, status_message, text)

    def _scroll_value_changed_cb(self, adj, scroll=None):
        '''Turn auto scrolling on or off.
        If the user scrolled up, turn it off.
        If the user scrolled to the bottom, turn it back on.
        '''
        if adj.get_value() < self._scroll_value:
            self._scroll_auto = False
        elif adj.get_value() == adj.get_upper() - adj.get_page_size():
            self._scroll_auto = True

    def _scroll_changed_cb(self, adj, scroll=None):
        '''Scroll the chat window to the bottom'''
        if self._scroll_auto:
            adj.set_value(adj.get_upper() - adj.get_page_size())
            self._scroll_value = adj.get_value()

    def resize_all(self):
        for message in self._message_list:
            message.resize_box()
        self.resize_rb()

    def resize_rb(self):
        for grid in self._grid_list:
            grid.set_size_request(
                gtk.gdk.screen_width() - style.GRID_CELL_SIZE, -1)
        for rb in self._rb_list:
            rb.set_size_request(
                gtk.gdk.screen_width() - style.GRID_CELL_SIZE, -1)
        self.resize_conversation()

    def resize_conversation(self, dy=None):
        ''' Take into account OSK (dy) '''
        if dy is None:
            dy = self._dy
        else:
            self._dy = dy

        self._conversation.set_size_request(
            gtk.gdk.screen_width() - style.GRID_CELL_SIZE,
            int(gtk.gdk.screen_height() - 2.5 * style.GRID_CELL_SIZE) - dy)
