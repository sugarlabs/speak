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
import subprocess
import logging
import time
from gettext import gettext as _

from gi.repository import Gtk
from gi.repository import Gdk
from gi.repository import Pango

from sugar3.graphics import style
from sugar3.presence import presenceservice
from sugar3.activity.activity import get_activity_root
from sugar3.activity.activity import show_object_in_journal
from sugar3.datastore import datastore
from sugar3 import profile

import face
from chatbox import ChatBox

logger = logging.getLogger('speak')

BUDDY_SIZE = int(style.GRID_CELL_SIZE * 1.5)

BUDDIES_WIDTH = int(BUDDY_SIZE * 5)
BUDDIES_COLOR = style.COLOR_SELECTION_GREY

ENTRY_COLOR = style.COLOR_PANEL_GREY
STATUS_MSG = '++STATUS++'


def _luminance(color):
    ''' Calculate luminance value '''
    return int(color[1:3], 16) * 0.3 + int(color[3:5], 16) * 0.6 + \
        int(color[5:7], 16) * 0.1


def _lighter_color(colors):
    ''' Which color is lighter? Use that one for the text nick color '''
    if _luminance(colors[0]) > _luminance(colors[1]):
        return 0
    return 1


def _is_tablet_mode():
    try:
        fp = open('/dev/input/event4', 'rb')
        fp.close()
    except IOError:
        return False

    try:
        output = subprocess.call(
            ['evtest', '--query', '/dev/input/event4', 'EV_SW',
             'SW_TABLET_MODE'])
    except (OSError, subprocess.CalledProcessError):
        return False
    if output == 10:
        return True
    return False


class View(Gtk.VBox):
    def __init__(self):
        Gtk.VBox.__init__(self)

        self.messenger = None
        self.me = None
        self.quiet = False

        self._buddies = {}

        # chat entry

        owner = presenceservice.get_instance().get_owner()
        self._chat = ChatBox(owner, _is_tablet_mode())
        self._chat.connect('open-on-journal', self.__open_on_journal)
        self.me = self._new_face(owner, ENTRY_COLOR)

        # add owner to buddy list
        self._buddies[owner] = self.me

        # buddies box

        self._buddies_box = Gtk.HBox()
        self._buddies_box.pack_end(self.me, True, True, 0)

        self._buddies_sw = Gtk.ScrolledWindow()
        self._buddies_sw.set_policy(Gtk.PolicyType.AUTOMATIC,
                                    Gtk.PolicyType.NEVER)
        self._buddies_sw.add_with_viewport(self._buddies_box)

        self.chat_post = Gtk.Entry()
        self.chat_post.modify_font(Pango.FontDescription('sans bold 24'))
        self.chat_post.connect('activate', self._activate_cb)
        self.chat_post.connect('key-press-event', self._key_press_cb)

        self._entry = Gtk.HBox()
        self._entry.pack_start(self._buddies_sw, False, False, 0)
        self._entry.pack_start(self.chat_post, True, True, 0)

        if _is_tablet_mode():
            self.pack_start(self._entry, False, False, 0)
            self.pack_end(self._chat, True, True, 0)
        else:
            self.pack_start(self._chat, True, True, 0)
            self.pack_end(self._entry, False, False, 0)

        self.resize_chat_box(expanded=False)
        self.show_all()

    def resize_chat_box(self, expanded=False):
        pass

    def update(self, status):
        self.me.update(status)
        if self.messenger:
            self.messenger.post('%s:%s' %
                                (STATUS_MSG, status.serialize()))

    def post(self, buddy, text, status_message=False):
        buddy_face = self._find_buddy(buddy)

        if not text:
            return

        if STATUS_MSG in text:
            try:
                status = face.Status().deserialize(
                    text[len(STATUS_MSG) + 1:])
                buddy_face.update(status)
                self.resize_buddy_list()
            except BaseException:
                logging.error('Could not parse status message %s' %
                              text)
        else:
            self._chat.add_text(buddy, text, status_message)
            if not self.quiet:
                # and self.props.window \
                #    and self.props.window.is_visible():
                buddy_face.say(text)

    def _find_buddy(self, buddy):
        i = self._buddies.get(buddy)
        if not i:
            # Sometimes the same buddy has a different dbus instance,
            # so walk through the list
            nick = buddy.props.nick
            color = buddy.props.color
            for old_buddy in list(self._buddies.keys()):
                if old_buddy.props.nick == nick and \
                   old_buddy.props.color == color:
                    i = self._buddies.get(old_buddy)
            if not i:  # No match, so add a new buddy
                self._add_buddy(buddy)
                i = self._buddies[buddy]
        return i

    def resize_buddy_list(self):
        """ maintain the buddy list width """
        size = min(BUDDIES_WIDTH, len(self._buddies) * BUDDY_SIZE)
        self._buddies_sw.set_size_request(size, BUDDY_SIZE)
        for buddy in list(self._buddies.values()):
            buddy.set_size_request(BUDDY_SIZE, BUDDY_SIZE)

    def farewell(self, buddy):
        i = self._find_buddy(buddy)
        if not i:
            logger.debug('farewell: cannot find buddy %s' % buddy.props.nick)
            return

        self._buddies_box.remove(i)
        del self._buddies[buddy]
        self.resize_buddy_list()

    def shut_up(self):
        for i in list(self._buddies.values()):
            i.shut_up()
        self.me.shut_up()

    def _add_buddy(self, buddy):
        self._buddies[buddy] = self._new_face(buddy, BUDDIES_COLOR)
        self._buddies_box.pack_start(self._buddies[buddy], True, True, 0)
        self.resize_buddy_list()

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
        if event.keyval == Gdk.KEY_Return:
            if not (event.state & Gdk.ModifierType.CONTROL_MASK):
                return self._activate_cb(widget, event)
        return False

    def _new_face(self, buddy, color):
        colors = buddy.props.color.split(',')
        lighter = style.Color(colors[_lighter_color(colors)])

        buddy_face = face.View(lighter)
        # FIXME: omit set_border_state causes main face alignment problems
        buddy_face.set_border_state(False)
        # FIXME: non-me faces have no mouth

        buddy_face.show_all()

        return buddy_face

    def look_at(self):
        self.me.look_at()
        for i in list(self._buddies.values()):
            i.look_at()

    def __open_on_journal(self, widget, url):
        '''Ask the journal to display a URL'''
        jobject = datastore.create()
        metadata = {
            'title': '%s: %s' % (_('URL from Speak'), url),
            'title_set_by_user': '1',
            'icon-color': profile.get_color().to_string(),
            'mime_type': 'text/uri-list',
        }
        for k, v in list(metadata.items()):
            jobject.metadata[k] = v
        file_path = os.path.join(get_activity_root(), 'instance',
                                 '%i_' % time.time())
        open(file_path, 'w').write(url + '\r\n')
        os.chmod(file_path, 0o755)
        jobject.set_file_path(file_path)
        datastore.write(jobject)
        show_object_in_journal(jobject.object_id)
        jobject.destroy()
        os.unlink(file_path)
