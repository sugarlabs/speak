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

from gi.repository import GObject
from gi.repository import Gtk
from gi.repository import Gdk
from gi.repository import GdkPixbuf
from gi.repository import Pango

from sugar3.graphics import style
from sugar3.graphics.palette import Palette, Invoker
from sugar3.graphics.palettemenu import PaletteMenuItem
from sugar3.graphics.palette import MouseSpeedDetector
from sugar3.util import timestamp_to_elapsed_string
from sugar3 import profile

import smilies
import roundbox


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


class TextBox(Gtk.TextView):

    __gsignals__ = {
        'open-on-journal': (GObject.SignalFlags.RUN_FIRST, None, ([str])), }

    hand_cursor = Gdk.Cursor.new(Gdk.CursorType.HAND2)

    def __init__(self, parent,
                 name_color, text_color, bg_color, highlight_color,
                 lang_rtl, nick_name=None, text=None):
        Gtk.TextView.__init__(self)
        self._parent = parent
        self._buffer = Gtk.TextBuffer()
        self._empty_buffer = Gtk.TextBuffer()
        self._empty_buffer.set_text('')
        self._empty = True
        self._name_tag = self._buffer.create_tag(
            'name', foreground=name_color.get_html(), weight=Pango.Weight.BOLD)
        self._fg_tag = self._buffer.create_tag(
            'foreground_color', foreground=text_color.get_html())
        self._subscript_tag = self.get_buffer().create_tag(
            'subscript', foreground=text_color.get_html(),
            rise=-7 * Pango.SCALE)  # in pixels

        if nick_name:
            self._add_name(nick_name)
            self.add_text(text, newline=False)
        elif text:
            self.add_text(text)

        self.resize_box()

        self._lang_rtl = lang_rtl
        self.set_editable(False)
        self.set_cursor_visible(False)
        self.set_wrap_mode(Gtk.WrapMode.WORD_CHAR)

        self.palette = None

        self._mouse_detector = MouseSpeedDetector(200, 5)
        self._mouse_detector.connect('motion-slow', self.__mouse_slow_cb)

        self.modify_bg(0, bg_color.get_gdk_color())

        rgba = Gdk.RGBA()
        rgba.red, rgba.green, rgba.blue, rgba.alpha = \
            highlight_color.get_rgba()
        self.override_background_color(Gtk.StateFlags.SELECTED, rgba)

        self.add_events(Gdk.EventMask.POINTER_MOTION_MASK
                        | Gdk.EventMask.BUTTON_PRESS_MASK
                        | Gdk.EventMask.BUTTON_RELEASE_MASK
                        | Gdk.EventMask.LEAVE_NOTIFY_MASK)

        self.connect('event-after', self.__event_after_cb)
        self.connect('button-press-event', self.__button_press_cb)
        self.motion_notify_id = \
            self.connect('motion-notify-event', self.__motion_notify_cb)
        self.connect('visibility-notify-event', self.__visibility_notify_cb)
        self.connect('leave-notify-event', self.__leave_notify_event_cb)
        self.connect('size-allocate', self.__size_allocate_cb)

    def __size_allocate_cb(self, widget, allocation):
        ''' Load buffer after resize to circumvent race condition '''
        self.set_buffer(self._buffer)
        self._parent.resize_rb()

    def resize_box(self):
        self.set_buffer(self._empty_buffer)
        self.set_size_request(Gdk.Screen.width() - style.GRID_CELL_SIZE
                              - 2 * style.DEFAULT_SPACING, -1)

    def __leave_notify_event_cb(self, widget, event):
        self._mouse_detector.stop()

    def __button_press_cb(self, widget, event):
        if event.type == Gdk.EventType.BUTTON_PRESS and event.button == 3:
            # To disable the standard textview popup
            return True

    # Links can be activated by clicking.
    def __event_after_cb(self, widget, event):
        if event.type.value_name != 'GDK_BUTTON_RELEASE':
            return False

        x, y = self.window_to_buffer_coords(Gtk.TextWindowType.WIDGET,
                                            int(event.x), int(event.y))
        iter_tags = self.get_iter_at_location(x, y)

        for tag in iter_tags.get_tags():
            try:
                url = tag.url
            except BaseException:
                url = None
            if url is not None:
                if event.button == 3:
                    palette = tag.palette
                    xw, yw = self.get_toplevel().get_pointer()
                    palette.popup()
                else:
                    self._show_via_journal(url)
                break

        return False

    def _show_via_journal(self, url):
        self.emit('open-on-journal', url)

    def check_url_hovering(self, x, y):
        # Looks at all tags covering the position (x, y) in the text view,
        # and if one of them is a link return True

        hovering = False
        # When check on_slow_mouse event, the position can be out
        # of the widget and return negative values.
        if x < 0 or y < 0:
            return hovering

        self.palette = None
        iter_tags = self.get_iter_at_location(x, y)

        tags = iter_tags[1].get_tags()
        for tag in tags:
            try:
                url = tag.url
                self.palette = tag.palette
            except BaseException:
                url = None
            if url is not None:
                hovering = True
                break
        return hovering

    def set_cursor_if_appropriate(self, x, y):
        # Looks at all tags covering the position (x, y) in the text view,
        # and if one of them is a link, change the cursor to the 'hands' cursor

        hovering_over_link = self.check_url_hovering(x, y)
        win = self.get_window(Gtk.TextWindowType.TEXT)
        if hovering_over_link:
            win.set_cursor(self.hand_cursor)
            self._mouse_detector.start()
        else:
            win.set_cursor(None)
            self._mouse_detector.stop()

    def __mouse_slow_cb(self, widget):
        x, y = self.get_pointer()
        hovering_over_link = self.check_url_hovering(x, y)
        if hovering_over_link:
            if self.palette is not None:
                xw, yw = self.get_toplevel().get_pointer()
                self.palette.popup()
                self._mouse_detector.stop()
        else:
            if self.palette is not None:
                self.palette.popdown()

    # Update the cursor image if the pointer moved.
    def __motion_notify_cb(self, widget, event):
        x, y = self.window_to_buffer_coords(Gtk.TextWindowType.WIDGET,
                                            int(event.x), int(event.y))
        self.set_cursor_if_appropriate(x, y)
        self.get_pointer()
        return False

    def __visibility_notify_cb(self, widget, event):
        # Also update the cursor image if the window becomes visible
        # (e.g. when a window covering it got iconified).
        bx, by = self.window_to_buffer_coords(
            Gtk.TextWindowType.WIDGET, 200, 200)
        self.set_cursor_if_appropriate(bx, by)
        return False

    def __palette_mouse_enter_cb(self, widget, event):
        self.handler_block(self.motion_notify_id)

    def __palette_mouse_leave_cb(self, widget, event):
        self.handler_unblock(self.motion_notify_id)

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
            if _URL_REGEXP.match(word) is not None:
                tag = buf.create_tag(None, underline=Pango.Underline.SINGLE)
                tag.url = word
                palette = _URLMenu(word)
                # FIXME: TypeError: _URLMenu: unknown signal name:
                # enter-notify-event - leave-notify-event
                # palette.connect('enter-notify-event',
                #                 self.__palette_mouse_enter_cb)
                # palette.connect('leave-notify-event',
                #                 self.__palette_mouse_leave_cb)
                tag.palette = palette
                buf.insert_with_tags(self.iter_text, word, tag, self._fg_tag)
            else:
                for i in smilies.parse(word):
                    if isinstance(i, GdkPixbuf.Pixbuf):
                        start = self.iter_text.get_offset()
                        buf.insert_pixbuf(self.iter_text, i)
                        buf.apply_tag(self._subscript_tag,
                                      buf.get_iter_at_offset(start),
                                      self.iter_text)
                    else:
                        buf.insert_with_tags(self.iter_text, i, self._fg_tag)
            buf.insert_with_tags(self.iter_text, ' ', self._fg_tag)

        self._empty = False


class ChatBox(Gtk.ScrolledWindow):

    __gsignals__ = {
        'foo': (GObject.SignalFlags.RUN_FIRST, None, ([])),
        'open-on-journal': (GObject.SignalFlags.RUN_FIRST, None, ([str])), }

    def __init__(self, owner, tablet_mode):
        Gtk.ScrolledWindow.__init__(self)

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

        self._conversation = Gtk.Grid()
        self._conversation.set_row_spacing(style.DEFAULT_PADDING)
        self._conversation.set_border_width(0)
        self._conversation.set_size_request(
            Gdk.Screen.width() - style.GRID_CELL_SIZE, -1)

        # OSK padding for conversation
        self._dy = 0

        evbox = Gtk.EventBox()
        evbox.modify_bg(
            Gtk.StateType.NORMAL, style.COLOR_WHITE.get_gdk_color())
        evbox.add(self._conversation)
        self._conversation.show()

        self.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.ALWAYS)
        self.add_with_viewport(evbox)
        evbox.show()

        vadj = self.get_vadjustment()
        vadj.connect('changed', self._scroll_changed_cb)
        vadj.connect('value-changed', self._scroll_value_changed_cb)

        self.connect('foo', self.resize_rb)

    def __open_on_journal(self, widget, url):
        self.emit('open-on-journal', url)

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
        if Pango.find_base_dir(nick, -1) == Pango.Direction.RTL:
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
            rb = roundbox.RoundBox()
            rb.background_color = color_fill
            rb.border_color = color_stroke
            rb.tail = tail
            self._rb_list.append(rb)

            grid_internal = Gtk.Grid()
            grid_internal.set_row_spacing(0)
            grid_internal.set_border_width(style.DEFAULT_PADDING)
            grid_internal.set_size_request(
                Gdk.Screen.width() - style.GRID_CELL_SIZE, -1)
            self._grid_list.append(grid_internal)

            row = 0

            if status_message:
                nick = None
            elif me_message:
                text = text[4:]

            message = TextBox(self, nick_color, text_color, color_fill,
                              highlight_fill, lang_rtl, nick, text)
            self._message_list.append(message)
            message.connect('open-on-journal', self.__open_on_journal)

            self._last_msg_sender = buddy
            self._last_msg = message

            grid_internal.attach(message, 0, row, 1, 1)
            row += 1

            align = Gtk.Alignment.new(xalign=0.0, yalign=0.0, xscale=1.0,
                                      yscale=1.0)
            if rb.tail is None:
                bottom_padding = style.zoom(7)
            else:
                bottom_padding = style.zoom(35)
            align.set_padding(style.zoom(7), bottom_padding, style.zoom(30),
                              style.zoom(30))

            align.add(grid_internal)
            grid_internal.show()

            rb.pack_start(align, True, True, 0)
            align.show()

            self._conversation.attach(rb, 0, self._row_counter, 1, 1)
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
        box = Gtk.HBox()
        align = Gtk.Alignment.new(
            xalign=0.5, yalign=0.0, xscale=0.0, yscale=0.0)
        box.pack_start(align, True, True, 0)
        align.show()
        align.add(message)
        message.show()
        self._conversation.attach(box, 0, self._row_counter, 1, 1)
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
                Gdk.Screen.width() - style.GRID_CELL_SIZE, -1)
        for rb in self._rb_list:
            rb.set_size_request(
                Gdk.Screen.width() - style.GRID_CELL_SIZE, -1)
        self.resize_conversation()

    def resize_conversation(self, dy=None):
        ''' Take into account OSK (dy) '''
        if dy is None:
            dy = self._dy
        else:
            self._dy = dy

        width = Gdk.Screen.width() - style.GRID_CELL_SIZE
        height = int(Gdk.Screen.height() - 3 * style.GRID_CELL_SIZE) - dy
        self._conversation.set_size_request(width, height)


class ContentInvoker(Invoker):
    def __init__(self):
        Invoker.__init__(self)
        self._position_hint = self.AT_CURSOR

    def get_default_position(self):
        return self.AT_CURSOR

    def get_toplevel(self):
        return None


class _URLMenu(Palette):

    def __init__(self, url):
        Palette.__init__(self, url)
        self.owns_clipboard = False
        self.url = self._url_check_protocol(url)

        menu_box = Gtk.VBox()
        self.set_content(menu_box)
        menu_box.show()
        self._content.set_border_width(1)
        menu_item = PaletteMenuItem(_('Copy to Clipboard'), 'edit-copy')
        menu_item.connect('activate', self._copy_to_clipboard_cb)
        menu_box.pack_start(menu_item, False, False, 0)
        menu_item.show()
        self.props.invoker = ContentInvoker()

    def create_palette(self):
        pass

    def _copy_to_clipboard_cb(self, menuitem):
        logging.debug('Copy %s to clipboard', self.url)
        clipboard = Gtk.clipboard_get()
        targets = [('text/uri-list', 0, 0), ('UTF8_STRING', 0, 1)]

        if not clipboard.set_with_data(targets, self._clipboard_data_get_cb,
                                       self._clipboard_clear_cb, (self.url)):
            logging.debug('GtkClipboard.set_with_data failed!')
        else:
            self.owns_clipboard = True

    def _clipboard_data_get_cb(self, clipboard, selection, info, data):
        logging.debug('_clipboard_data_get_cb data=%s target=%s', data,
                      selection.target)
        if selection.target in ['text/uri-list']:
            if not selection.set_uris([data]):
                logging.debug('failed to set_uris')
        else:
            logging.debug('not uri')
            if not selection.set_text(data):
                logging.debug('failed to set_text')

    def _clipboard_clear_cb(self, clipboard, data):
        logging.debug('clipboard_clear_cb')
        self.owns_clipboard = False

    def _url_check_protocol(self, url):
        '''Check that the url has a protocol, otherwise prepend https://
        url -- string
        Returns url -- string
        '''
        protocols = ['http://', 'https://', 'ftp://', 'ftps://']
        no_protocol = True
        for protocol in protocols:
            if url.startswith(protocol):
                no_protocol = False
        if no_protocol:
            url = 'http://' + url
        return url
