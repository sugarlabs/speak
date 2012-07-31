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

# This code is a stripped down version of the Chat

from gi.repository import Gtk
from gi.repository import Gdk
import logging
from gi.repository import Pango
import re
from datetime import datetime
from gettext import gettext as _

from sugar3.graphics import style
from sugar3.graphics.palette import Palette
#from sugar3.graphics.palette import CanvasInvoker
from sugar3.graphics.palette import MouseSpeedDetector
from sugar3.presence import presenceservice
from sugar3.graphics.menuitem import MenuItem
from sugar3.activity.activity import get_activity_root
from roundbox import RoundBox

logger = logging.getLogger('speak')

URL_REGEXP = re.compile('((http|ftp)s?://)?'
    '(([-a-zA-Z0-9]+[.])+[-a-zA-Z0-9]{2,}|([0-9]{1,3}[.]){3}[0-9]{1,3})'
    '(:[1-9][0-9]{0,4})?(/[-a-zA-Z0-9/%~@&_+=;:,.?#]*[a-zA-Z0-9/])?')


class TextBox(Gtk.TextView):

    hand_cursor = Gdk.Cursor.new(Gdk.CursorType.HAND2)

    def __init__(self, color, bg_color, lang_rtl):
        self._lang_rtl = lang_rtl
        Gtk.TextView.__init__(self)
        self.set_editable(False)
        self.set_cursor_visible(False)
        self.set_wrap_mode(Gtk.WrapMode.WORD_CHAR)
        self.get_buffer().set_text("", 0)
        self.iter_text = self.get_buffer().get_iter_at_offset(0)
        self.fg_tag = self.get_buffer().create_tag("foreground_color",
            foreground=color.get_html())
        self._subscript_tag = self.get_buffer().create_tag('subscript',
                    rise=-7 * Pango.SCALE)  # in pixels
        self._empty = True
        self.palette = None
        self._mouse_detector = MouseSpeedDetector(200, 5)
        self._mouse_detector.connect('motion-slow', self.__mouse_slow_cb)
        self.modify_base(Gtk.StateType.NORMAL, bg_color.get_gdk_color())

        self.add_events(Gdk.EventMask.POINTER_MOTION_MASK | \
                        Gdk.EventMask.BUTTON_PRESS_MASK | \
                        Gdk.EventMask.BUTTON_RELEASE_MASK | \
                        Gdk.EventMask.LEAVE_NOTIFY_MASK)

        self.connect('event-after', self.__event_after_cb)
        self.connect('button-press-event', self.__button_press_cb)
        self.motion_notify_id = self.connect('motion-notify-event', \
                self.__motion_notify_cb)
        self.connect('visibility-notify-event', self.__visibility_notify_cb)
        self.connect('leave-notify-event', self.__leave_notify_event_cb)

    def __leave_notify_event_cb(self, widget, event):
        self._mouse_detector.stop()

    def __button_press_cb(self, widget, event):
        if event.type == Gdk.EventType.BUTTON_PRESS and event.button == 3:
            # To disable the standard textview popup
            return True

    # Links can be activated by clicking.
    def __event_after_cb(self, widget, event):
        if event.type != Gdk.EventType.BUTTON_RELEASE:
            return False

        x, y = self.window_to_buffer_coords(Gtk.TextWindowType.WIDGET,
            int(event.x), int(event.y))
        iter_tags = self.get_iter_at_location(x, y)

        for tag in iter_tags.get_tags():
            url = tag.get_data('url')
            if url is not None:
                if event.button == 3:
                    palette = tag.get_data('palette')
                    xw, yw = self.get_toplevel().get_pointer()
                    palette.move(int(xw), int(yw))
                    palette.popup()
                else:
                    self._show_via_journal(url)
                break

        return False

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

        tags = iter_tags.get_tags()
        for tag in tags:
            url = tag.get_data('url')
            self.palette = tag.get_data('palette')
            if url is not None:
                hovering = True
                break
        return hovering

    def set_cursor_if_appropriate(self, x, y):
        # Looks at all tags covering the position (x, y) in the text view,
        # and if one of them is a link, change the cursor to the "hands" cursor

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
                self.palette.move(xw, yw)
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
        return False

    def __visibility_notify_cb(self, widget, event):
        # Also update the cursor image if the window becomes visible
        # (e.g. when a window covering it got iconified).

        wx, wy = self.get_pointer()
        bx, by = self.window_to_buffer_coords(Gtk.TextWindowType.WIDGET, wx, wy)
        self.set_cursor_if_appropriate(bx, by)
        return False

    def __palette_mouse_enter_cb(self, widget, event):
        self.handler_block(self.motion_notify_id)

    def __palette_mouse_leave_cb(self, widget, event):
        self.handler_unblock(self.motion_notify_id)

    def add_text(self, text):
        buf = self.get_buffer()

        if not self._empty:
            buf.insert(self.iter_text, '\n')

        words = text.split()
        for word in words:
            buf.insert(self.iter_text, word)
            buf.insert(self.iter_text, ' ')

        self._empty = False


class ColorLabel(Gtk.Label):

    def __init__(self, text, color=None):
        self._color = color
        if self._color is not None:
            text = '<span foreground="%s">' % self._color.get_html() +\
                    text + '</span>'
        Gtk.Label.__init__(self)
        self.set_use_markup(True)
        self.set_markup(text)
        self.props.selectable = True


class ChatBox(Gtk.ScrolledWindow):

    def __init__(self):
        Gtk.ScrolledWindow.__init__(self)

        self.owner = presenceservice.get_instance().get_owner()

        # Auto vs manual scrolling:
        self._scroll_auto = True
        self._scroll_value = 0.0
        self._last_msg_sender = None
        # Track last message, to combine several messages:
        self._last_msg = None
        self._chat_log = ''

        self._conversation = Gtk.VBox()
        self._conversation.set_homogeneous(False)
        self._conversation.props.spacing = style.LINE_WIDTH
        self._conversation.props.border_width = style.LINE_WIDTH
        
        evbox = Gtk.EventBox()
        evbox.modify_bg(Gtk.StateType.NORMAL, style.COLOR_WHITE.get_gdk_color())
        evbox.add(self._conversation)

        self.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.ALWAYS)
        self.add_with_viewport(evbox)
        
        vadj = self.get_vadjustment()
        vadj.connect('changed', self._scroll_changed_cb)
        vadj.connect('value-changed', self._scroll_value_changed_cb)

    def get_log(self):
        return self._chat_log

    def add_text(self, buddy, text, status_message=False):
        """Display text on screen, with name and colors.

        buddy -- buddy object or dict {nick: string, color: string}
                 (The dict is for loading the chat log from the journal,
                 when we don't have the buddy object any more.)
        text -- string, what the buddy said
        status_message -- boolean
            False: show what buddy said
            True: show what buddy did

        .------------- rb ---------------.
        | +name_vbox+ +----align-----+ |
        | |         | |                | |
        | | nick:   | | +--message---+ | |
        | |         | | |  text      | | |
        | +---------+ | +------------+ | |
        |             +----------------+ |
        `--------------------------------'
        """
        if not buddy:
            buddy = self.owner

        if type(buddy) is dict:
            # dict required for loading chat log from journal
            nick = buddy['nick']
            color = buddy['color']
        else:
            nick = buddy.props.nick
            color = buddy.props.color
        try:
            color_stroke_html, color_fill_html = color.split(',')
        except ValueError:
            color_stroke_html, color_fill_html = ('#000000', '#888888')

        # Select text color based on fill color:
        color_fill_rgba = style.Color(color_fill_html).get_rgba()
        color_fill_gray = (color_fill_rgba[0] + color_fill_rgba[1] +
            color_fill_rgba[2]) / 3
        color_stroke = style.Color(color_stroke_html)
        color_fill = style.Color(color_fill_html)
        if color_fill_gray < 0.5:
            text_color = style.COLOR_WHITE
        else:
            text_color = style.COLOR_BLACK

        self._add_log(nick, color, text, status_message)

        # Check for Right-To-Left languages:
        if Pango.find_base_dir(nick, -1) == Pango.Direction.RTL:
            lang_rtl = True
        else:
            lang_rtl = False

        # Check if new message box or add text to previous:
        new_msg = True
        if self._last_msg_sender:
            if not status_message:
                if buddy == self._last_msg_sender:
                    # Add text to previous message
                    new_msg = False

        if not new_msg:
            rb = self._last_msg
            self._last_msg.add_text(text)
        else:
            rb = RoundBox()
            screen_width = Gdk.Screen.width()
            # keep space to the scrollbar
            rb.set_size_request(screen_width - 50, -1)
            rb.props.border_width = style.DEFAULT_PADDING
            rb.props.spacing = style.DEFAULT_SPACING
            rb.background_color = color_fill
            rb.border_color = color_stroke
            self._last_msg_sender = buddy
            self._last_msg = rb
            if not status_message:
                name = ColorLabel(text=nick + ':', color=text_color)
                name_vbox = Gtk.VBox()
                name_vbox.pack_start(name, False, False, 0)
                rb.pack_start(name_vbox, False, False, 0)
            message = TextBox(text_color, color_fill, lang_rtl)
            vbox = Gtk.VBox()
            vbox.pack_start(message, True, True, 0)
            rb.pack_start(vbox, True, True, 0)
            self._last_msg = message
            self._conversation.pack_start(rb, False, False, 0)
            message.add_text(text)
            self._conversation.show_all()

        if status_message:
            self._last_msg_sender = None

    def _scroll_value_changed_cb(self, adj, scroll=None):
        """Turn auto scrolling on or off.
        If the user scrolled up, turn it off.
        If the user scrolled to the bottom, turn it back on.
        """
        if adj.get_value() < self._scroll_value:
            self._scroll_auto = False
        elif adj.get_value() == adj.get_upper() - adj.get_page_size():
            self._scroll_auto = True

    def _scroll_changed_cb(self, adj, scroll=None):
        """Scroll the chat window to the bottom"""
        if self._scroll_auto:
            adj.set_value(adj.get_upper() - adj.get_page_size())
            self._scroll_value = adj.get_value()

    def _link_activated_cb(self, link):
        url = url_check_protocol(link.props.text)
        self._show_via_journal(url)

    def _show_via_journal(self, url):
        """Ask the journal to display a URL"""
        import os
        import time
        from sugar3 import profile
        from sugar3.activity.activity import show_object_in_journal
        from sugar3.datastore import datastore
        logger.debug('Create journal entry for URL: %s', url)
        jobject = datastore.create()
        metadata = {
            'title': "%s: %s" % (_('URL from Chat'), url),
            'title_set_by_user': '1',
            'icon-color': profile.get_color().to_string(),
            'mime_type': 'text/uri-list',
            }
        for k, v in metadata.items():
            jobject.metadata[k] = v
        file_path = os.path.join(get_activity_root(), 'instance',
                                 '%i_' % time.time())
        open(file_path, 'w').write(url + '\r\n')
        os.chmod(file_path, 0755)
        jobject.set_file_path(file_path)
        datastore.write(jobject)
        show_object_in_journal(jobject.object_id)
        jobject.destroy()
        os.unlink(file_path)

    def _add_log(self, nick, color, text, status_message):
        """Add the text to the chat log.
        nick -- string, buddy nickname
        color -- string, buddy.props.color
        text -- string, body of message
        status_message -- boolean
        """
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


def url_check_protocol(url):
    """Check that the url has a protocol, otherwise prepend https://

    url -- string

    Returns url -- string
    """
    protocols = ['http://', 'https://', 'ftp://', 'ftps://']
    no_protocol = True
    for protocol in protocols:
        if url.startswith(protocol):
            no_protocol = False
    if no_protocol:
        url = 'http://' + url
    return url
