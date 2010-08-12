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

import gtk
import hippo
import logging
import pango
import re
from datetime import datetime
from gobject import SIGNAL_RUN_FIRST, TYPE_PYOBJECT
from gettext import gettext as _

import sugar.graphics.style as style
from sugar.graphics.roundbox import CanvasRoundBox
from sugar.graphics.palette import Palette, CanvasInvoker
from sugar.presence import presenceservice
from sugar.graphics.style import (Color, COLOR_BLACK, COLOR_WHITE)
from sugar.graphics.menuitem import MenuItem
from sugar.activity.activity import get_activity_root

logger = logging.getLogger('speak')

URL_REGEXP = re.compile('((http|ftp)s?://)?'
    '(([-a-zA-Z0-9]+[.])+[-a-zA-Z0-9]{2,}|([0-9]{1,3}[.]){3}[0-9]{1,3})'
    '(:[1-9][0-9]{0,4})?(/[-a-zA-Z0-9/%~@&_+=;:,.?#]*[a-zA-Z0-9/])?')

class ChatBox(hippo.CanvasScrollbars):
    def __init__(self):
        hippo.CanvasScrollbars.__init__(self)

        self.owner = presenceservice.get_instance().get_owner()

        # Auto vs manual scrolling:
        self._scroll_auto = True
        self._scroll_value = 0.0
        self._last_msg_sender = None
        # Track last message, to combine several messages:
        self._last_msg = None
        self._chat_log = ''

        self._conversation = hippo.CanvasBox(
                spacing=0,
                background_color=COLOR_WHITE.get_int())

        self.set_policy(hippo.ORIENTATION_HORIZONTAL,
                hippo.SCROLLBAR_NEVER)
        self.set_root(self._conversation)

        vadj = self.props.widget.get_vadjustment()
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

        hippo layout:
        .------------- rb ---------------.
        | +name_vbox+ +----msg_vbox----+ |
        | |         | |                | |
        | | nick:   | | +--msg_hbox--+ | |
        | |         | | | text       | | |
        | +---------+ | +------------+ | |
        |             |                | |
        |             | +--msg_hbox--+ | |
        |             | | text | url | | |
        |             | +------------+ | |
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
        color_fill_rgba = Color(color_fill_html).get_rgba()
        color_fill_gray = (color_fill_rgba[0] + color_fill_rgba[1] +
                           color_fill_rgba[2])/3
        color_stroke = Color(color_stroke_html).get_int()
        color_fill = Color(color_fill_html).get_int()

        if color_fill_gray < 0.5:
            text_color = COLOR_WHITE.get_int()
        else:
            text_color = COLOR_BLACK.get_int()

        self._add_log(nick, color, text, status_message)

        # Check for Right-To-Left languages:
        if pango.find_base_dir(nick, -1) == pango.DIRECTION_RTL:
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
            msg_vbox = rb.get_children()[1]
            msg_hbox = hippo.CanvasBox(
                orientation=hippo.ORIENTATION_HORIZONTAL)
            msg_vbox.append(msg_hbox)
        else:
            rb = CanvasRoundBox(background_color=color_fill,
                                border_color=color_stroke,
                                padding=4)
            rb.props.border_color = color_stroke  # Bug #3742
            self._last_msg = rb
            self._last_msg_sender = buddy
            if not status_message:
                name = hippo.CanvasText(text=nick+':   ',
                    color=text_color)
                name_vbox = hippo.CanvasBox(
                    orientation=hippo.ORIENTATION_VERTICAL)
                name_vbox.append(name)
                rb.append(name_vbox)
            msg_vbox = hippo.CanvasBox(
                orientation=hippo.ORIENTATION_VERTICAL)
            rb.append(msg_vbox)
            msg_hbox = hippo.CanvasBox(
                orientation=hippo.ORIENTATION_HORIZONTAL)
            msg_vbox.append(msg_hbox)

        if status_message:
            self._last_msg_sender = None

        match = URL_REGEXP.search(text)
        while match:
            # there is a URL in the text
            starttext = text[:match.start()]
            if starttext:
                message = hippo.CanvasText(
                    text=starttext,
                    size_mode=hippo.CANVAS_SIZE_WRAP_WORD,
                    color=text_color,
                    xalign=hippo.ALIGNMENT_START)
                msg_hbox.append(message)
            url = text[match.start():match.end()]

            message = CanvasLink(
                text=url,
                color=text_color)
            attrs = pango.AttrList()
            attrs.insert(pango.AttrUnderline(pango.UNDERLINE_SINGLE, 0, 32767))
            message.set_property("attributes", attrs)
            message.connect('activated', self._link_activated_cb)

            # call interior magic which should mean just:
            # CanvasInvoker().parent = message
            CanvasInvoker(message)

            msg_hbox.append(message)
            text = text[match.end():]
            match = URL_REGEXP.search(text)

        if text:
            message = hippo.CanvasText(
                text=text,
                size_mode=hippo.CANVAS_SIZE_WRAP_WORD,
                color=text_color,
                xalign=hippo.ALIGNMENT_START)
            msg_hbox.append(message)

        # Order of boxes for RTL languages:
        if lang_rtl:
            msg_hbox.reverse()
            if new_msg:
                rb.reverse()

        if new_msg:
            box = hippo.CanvasBox(padding=2)
            box.append(rb)
            self._conversation.append(box)

    def _scroll_value_changed_cb(self, adj, scroll=None):
        """Turn auto scrolling on or off.
        
        If the user scrolled up, turn it off.
        If the user scrolled to the bottom, turn it back on.
        """
        if adj.get_value() < self._scroll_value:
            self._scroll_auto = False
        elif adj.get_value() == adj.upper-adj.page_size:
            self._scroll_auto = True

    def _scroll_changed_cb(self, adj, scroll=None):
        """Scroll the chat window to the bottom"""
        if self._scroll_auto:
            adj.set_value(adj.upper-adj.page_size)
            self._scroll_value = adj.get_value()

    def _link_activated_cb(self, link):
        url = url_check_protocol(link.props.text)
        self._show_via_journal(url)

    def _show_via_journal(self, url):
        """Ask the journal to display a URL"""
        import os
        import time
        from sugar import profile
        from sugar.activity.activity import show_object_in_journal
        from sugar.datastore import datastore
        logger.debug('Create journal entry for URL: %s', url)
        jobject = datastore.create()
        metadata = {
            'title': "%s: %s" % (_('URL from Chat'), url),
            'title_set_by_user': '1',
            'icon-color': profile.get_color().to_string(),
            'mime_type': 'text/uri-list',
            }
        for k,v in metadata.items():
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

class CanvasLink(hippo.CanvasLink):
    def __init__(self, **kwargs):
        hippo.CanvasLink.__init__(self, **kwargs)

    def create_palette(self):
        return URLMenu(self.props.text)

class URLMenu(Palette):
    def __init__(self, url):
        Palette.__init__(self, url)

        self.url = url_check_protocol(url)

        menu_item = MenuItem(_('Copy to Clipboard'), 'edit-copy')
        menu_item.connect('activate', self._copy_to_clipboard_cb)
        self.menu.append(menu_item)
        menu_item.show()

    def create_palette(self):
        pass

    def _copy_to_clipboard_cb(self, menuitem):
        logger.debug('Copy %s to clipboard', self.url)
        clipboard = gtk.clipboard_get()
        targets = [("text/uri-list", 0, 0),
                   ("UTF8_STRING", 0, 1)]

        if not clipboard.set_with_data(targets,
                                       self._clipboard_data_get_cb,
                                       self._clipboard_clear_cb,
                                       (self.url)):
            logger.error('GtkClipboard.set_with_data failed!')
        else:
            self.owns_clipboard = True

    def _clipboard_data_get_cb(self, clipboard, selection, info, data):
        logger.debug('_clipboard_data_get_cb data=%s target=%s', data,
                     selection.target)        
        if selection.target in ['text/uri-list']:
            if not selection.set_uris([data]):
                logger.debug('failed to set_uris')
        else:
            logger.debug('not uri')
            if not selection.set_text(data):
                logger.debug('failed to set_text')

    def _clipboard_clear_cb(self, clipboard, data):
        logger.debug('clipboard_clear_cb')
        self.owns_clipboard = False

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

