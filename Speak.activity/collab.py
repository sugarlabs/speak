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
import telepathy

from sugar.activity.activity import Activity
from sugar.presence.sugartubeconn import SugarTubeConnection

logger = logging.getLogger('speak')

class CollabActivity(Activity):
    def __init__(self, service, *args):
        Activity.__init__(self, *args)
        self.service = service

        self.connect('shared', self._shared_cb)

        # Owner.props.key
        if self._shared_activity:
            # We are joining the activity
            self.connect('joined', self._joined_cb)
            if self.get_shared():
                # We've already joined
                self._joined_cb()

    def on_tube(self, tube_conn, initiating):
        pass

    def _shared_cb(self, activity):
        logger.debug('My activity was shared')
        self._initiating = True
        self._sharing_setup()

        logger.debug('This is my activity: making a tube...')
        id = self._tubes_chan[telepathy.CHANNEL_TYPE_TUBES].OfferDBusTube(
            self.service, {})

    def _joined_cb(self, activity):
        if not self._shared_activity:
            return

        logger.debug('Joined an existing shared activity')

        self._initiating = False
        self._sharing_setup()
        
        logger.debug('This is not my activity: waiting for a tube...')
        self._tubes_chan[telepathy.CHANNEL_TYPE_TUBES].ListTubes(
            reply_handler=self._list_tubes_reply_cb, 
            error_handler=self._list_tubes_error_cb)

    def _sharing_setup(self):
        if self._shared_activity is None:
            logger.error('Failed to share or join activity')
            return
        self._conn = self._shared_activity.telepathy_conn
        self._tubes_chan = self._shared_activity.telepathy_tubes_chan
        self._text_chan = self._shared_activity.telepathy_text_chan
        
        self._tubes_chan[telepathy.CHANNEL_TYPE_TUBES].connect_to_signal('NewTube', self._new_tube_cb)
        
    def _list_tubes_reply_cb(self, tubes):
        for tube_info in tubes:
            self._new_tube_cb(*tube_info)

    def _list_tubes_error_cb(self, e):
        logger.error('ListTubes() failed: %s', e)

    def _new_tube_cb(self, id, initiator, type, service, params, state):
        logger.debug('New tube: ID=%d initator=%d type=%d service=%s '
                     'params=%r state=%d', id, initiator, type, service, 
                     params, state)

        if (type == telepathy.TUBE_TYPE_DBUS and
                service == self.service):
            if state == telepathy.TUBE_STATE_LOCAL_PENDING:
                self._tubes_chan[telepathy.CHANNEL_TYPE_TUBES].AcceptDBusTube(id)

            tube_conn = SugarTubeConnection(self._conn, 
                self._tubes_chan[telepathy.CHANNEL_TYPE_TUBES], 
                id, group_iface=self._text_chan[telepathy.CHANNEL_INTERFACE_GROUP])
            
            self.on_tube(tube_conn, self._initiating)
