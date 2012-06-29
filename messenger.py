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

import logging
from dbus.gobject_service import ExportedGObject
from dbus.service import method, signal

from sugar.presence import presenceservice

import face

logger = logging.getLogger('speak')

SERVICE = 'org.sugarlabs.Speak'
IFACE = SERVICE
PATH = '/org/sugarlabs/Speak'


class Messenger(ExportedGObject):
    def __init__(self, tube, is_initiator, chat):
        ExportedGObject.__init__(self, tube, PATH)

        self.is_initiator = is_initiator
        self.chat = chat

        self._tube = tube
        self._entered = False
        self._buddies = {}

        self._tube.watch_participants(self._participant_change_cb)

    def post(self, text):
        if text == None:
            text = ''
        self._post(self.chat.me.status.serialize(), text)

    def _participant_change_cb(self, added, removed):
        if removed:
            for i in removed:
                buddy = self._buddies.get(i)
                if buddy:
                    logger.debug('buddy %s left chat'
                            % self._buddies[i].props.nick)
                    self.chat.farewell(self._buddies[i])
                    del self._buddies[i]
                else:
                    logger.warning('_participant_change_cb: cannot find buddy')
        else:
            if not self._entered:
                self.me = self._tube.get_unique_name()

                self._tube.add_signal_receiver(self._ping_cb,
                                               '_ping',
                                               IFACE,
                                               path=PATH,
                                               sender_keyword='sender')
                self._tube.add_signal_receiver(self._post_cb,
                                               '_post',
                                               IFACE,
                                               path=PATH,
                                               sender_keyword='sender')

                if not self.is_initiator:
                    self._ping(self.chat.me.status.serialize())
            self._entered = True

    @signal(IFACE, signature='s')
    def _ping(self, status):
        logger.debug('send ping')
        pass

    @signal(IFACE, signature='ss')
    def _post(self, status, text):
        logger.debug('send message: %s' % text)
        pass

    @method(dbus_interface=IFACE, in_signature='s', out_signature='',
            sender_keyword='sender')
    def _pong(self, sender_status, sender=None):
        tp_handle = self._tube.bus_name_to_handle[sender]
        buddy = self._buddies[tp_handle] = self._tube.get_buddy(tp_handle)

        logger.debug('pong received from %s(%s) status=%s' \
                % (sender, buddy.props.nick, sender_status))

        self.chat.post(buddy, face.Status().deserialize(sender_status), None)

    def _ping_cb(self, sender_status, sender=None):
        if sender == self.me:
            return

        tp_handle = self._tube.bus_name_to_handle[sender]
        buddy = self._tube.get_buddy(tp_handle)
        if not buddy:
            return
        self._buddies[tp_handle] = buddy

        logger.debug('ping received from %s(%s) status=%s' \
                % (sender, buddy.props.nick, sender_status))

        self.chat.post(buddy, face.Status().deserialize(sender_status), None)
        remote_object = self._tube.get_object(sender, PATH)
        remote_object._pong(self.chat.me.status.serialize())

    def _post_cb(self, sender_status, text, sender=None):
        if sender == self.me:
            return
        if not text:
            text = None

        tp_handle = self._tube.bus_name_to_handle[sender]
        buddy = self._buddies[tp_handle]

        logger.debug('message received from %s(%s): %s'
                % (sender, buddy.props.nick, text))

        self.chat.post(buddy, face.Status().deserialize(sender_status), text)
