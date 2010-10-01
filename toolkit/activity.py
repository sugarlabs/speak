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

"""Extend sugar-toolkit activity class"""

import gtk
import logging
import telepathy
import gobject

from sugar.activity import activity
from sugar.presence.sugartubeconn import SugarTubeConnection
from sugar.graphics.alert import ConfirmationAlert, NotifyAlert


_NEW_INSTANCE   = 0
_NEW_INSTANCE   = 1
_PRE_INSTANCE   = 2
_POST_INSTANCE  = 3


class CursorFactory:

    __shared_state = {"cursors": {}}

    def __init__(self):
        self.__dict__ = self.__shared_state

    def get_cursor(self, cur_type):
        if not self.cursors.has_key(cur_type):
            cur = gtk.gdk.Cursor(cur_type)
            self.cursors[cur_type] = cur
        return self.cursors[cur_type]


class Activity(activity.Activity):

    """Basic activity class"""

    def new_instance(self):
        """
        New instance was created.

        Will be invoked after __init__() instead of resume_instance().
        Subclass should implement this method to catch creation stage.
        """
        pass

    def resume_instance(self, filepath):
        """
        Instance was resumed.

        Will be invoked after __init__() instead of new_instance().
        Subclass should implement this method to catch resuming stage.

        """
        pass

    def save_instance(self, filepath):
        """
        Save activity instance.

        Subclass should implement this method to save activity data.
        """
        raise NotImplementedError

    def on_save_instance(self, cb, *args):
        """ Register callback which will be invoked before save_instance """
        self.__on_save_instance.append((cb, args))

    def share_instance(self, connection, is_initiator):
        """
        Activity was shared/joined.

        connection -- SugarTubeConnection object
            wich represents telepathy connection

        is_initiator -- boolean
            if True activity was shared and
            (current activity is an initiator of sharing)
            otherwise activity was joined(to existed sharing session)

        Will be invoked after __init__() and {new,resume}_instance().
        Subclass should implement this method to catch sharing stage.
        """
        pass

    def set_toolbar_box(self, toolbox):
        if hasattr(activity.Activity, 'set_toolbar_box'):
            activity.Activity.set_toolbar_box(self, toolbox)
        else:
            self.set_toolbox(toolbox)

    def get_toolbar_box(self):
        if hasattr(activity.Activity, 'get_toolbar_box'):
            return activity.Activity.get_toolbar_box(self)
        else:
            return self.get_toolbox()

    toolbar_box = property(get_toolbar_box, set_toolbar_box)

    def get_shared_activity(self):
        if hasattr(activity.Activity, 'get_shared_activity'):
            return activity.Activity.get_shared_activity(self)
        else:
            return self._shared_activity

    def notify_alert(self, title, msg):
        """Raise standard notify alert"""
        alert = NotifyAlert(title=title, msg=msg)

        def response(alert, response_id, self):
            self.remove_alert(alert)

        alert.connect('response', response, self)
        alert.show_all()
        self.add_alert(alert)

    def confirmation_alert(self, title, msg, cb, *cb_args):
        """Raise standard confirmation alert"""
        alert = ConfirmationAlert(title=title, msg=msg)

        def response(alert, response_id, self, cb, *cb_args):
            self.remove_alert(alert)
            if response_id is gtk.RESPONSE_OK:
                cb(*cb_args)

        alert.connect('response', response, self, cb, *cb_args)
        alert.show_all()
        self.add_alert(alert)

    def get_cursor(self):
        return self._cursor

    def set_cursor(self, cursor):
        if not isinstance(cursor, gtk.gdk.Cursor):
            cursor = CursorFactory().get_cursor(cursor)

        if self._cursor != cursor:
            self._cursor = cursor
            self.window.set_cursor(self._cursor)

    def __init__(self, canvas, handle):
        """
        Initialise the Activity.

        canvas -- gtk.Widget
            root widget for activity content

        handle -- sugar.activity.activityhandle.ActivityHandle
            instance providing the activity id and access to the

        """
        activity.Activity.__init__(self, handle)

        if handle.object_id:
            self.__state = _NEW_INSTANCE
        else:
            self.__state = _NEW_INSTANCE

        self.__resume_filename = None
        self.__postponed_share = []
        self.__on_save_instance = []

        self._cursor = None
        self.set_cursor(gtk.gdk.LEFT_PTR)

        # XXX do it after(possible) read_file() invoking
        # have to rely on calling read_file() from map_cb in sugar-toolkit
        canvas.connect_after('map', self.__map_canvasactivity_cb)
        self.set_canvas(canvas)

    def __instance(self):
        logging.debug('Activity.__instance')

        if self.__resume_filename:
            self.resume_instance(self.__resume_filename)
        else:
            self.new_instance()

        for i in self.__postponed_share:
            self.share_instance(*i)
        self.__postponed_share = []

        self.__state = _POST_INSTANCE

    def read_file(self, filepath):
        """Subclass should not override this method"""
        logging.debug('Activity.read_file state=%s' % self.__state)

        self.__resume_filename = filepath

        if self.__state == _NEW_INSTANCE:
            self.__state = _PRE_INSTANCE
        elif self.__state == _PRE_INSTANCE:
            self.__instance();

    def write_file(self, filepath):
        """Subclass should not override this method"""
        for cb, args in self.__on_save_instance:
            cb(*args)
        self.save_instance(filepath)

    def __map_canvasactivity_cb(self, widget):
        logging.debug('Activity.__map_canvasactivity_cb state=%s' % \
                self.__state)

        if self.__state == _NEW_INSTANCE:
            self.__instance()
        elif self.__state == _NEW_INSTANCE:
            self.__state = _PRE_INSTANCE
        elif self.__state == _PRE_INSTANCE:
            self.__instance();

        return False

    def _share(self, tube_conn, initiator):
        logging.debug('Activity._share state=%s' % self.__state)

        if self.__state == _NEW_INSTANCE:
            self.__postponed_share.append((tube_conn, initiator))
            self.__state = _PRE_INSTANCE
        elif self.__state == _PRE_INSTANCE:
            self.__postponed_share.append((tube_conn, initiator))
            self.__instance();
        elif self.__state == _POST_INSTANCE:
            self.share_instance(tube_conn, initiator)


class SharedActivity(Activity):
    """Basic activity class with sharing features"""

    def __init__(self, canvas, service, handle):
        """
        Initialise the Activity.

        canvas -- gtk.Widget
            root widget for activity content

        service -- string
            dbus service for activity

        handle -- sugar.activity.activityhandle.ActivityHandle
            instance providing the activity id and access to the
            presence service which *may* provide sharing for this
            application

        """
        Activity.__init__(self, canvas, handle)
        self.service = service

        self.connect('shared', self._shared_cb)

        # Owner.props.key
        if self._shared_activity:
            # We are joining the activity
            self.connect('joined', self._joined_cb)
            if self.get_shared():
                # We've already joined
                self._joined_cb()

    def _shared_cb(self, activity):
        logging.debug('My activity was shared')
        self.__initiator = True
        self._sharing_setup()

        logging.debug('This is my activity: making a tube...')
        id = self._tubes_chan[telepathy.CHANNEL_TYPE_TUBES].OfferDBusTube(
            self.service, {})

    def _joined_cb(self, activity):
        if not self._shared_activity:
            return

        logging.debug('Joined an existing shared activity')

        self.__initiator = False
        self._sharing_setup()

        logging.debug('This is not my activity: waiting for a tube...')
        self._tubes_chan[telepathy.CHANNEL_TYPE_TUBES].ListTubes(
            reply_handler=self._list_tubes_reply_cb,
            error_handler=self._list_tubes_error_cb)

    def _sharing_setup(self):
        if self._shared_activity is None:
            logging.error('Failed to share or join activity')
            return
        self._conn = self._shared_activity.telepathy_conn
        self._tubes_chan = self._shared_activity.telepathy_tubes_chan
        self._text_chan = self._shared_activity.telepathy_text_chan

        self._tubes_chan[telepathy.CHANNEL_TYPE_TUBES].connect_to_signal(
                'NewTube', self._new_tube_cb)

    def _list_tubes_reply_cb(self, tubes):
        for tube_info in tubes:
            self._new_tube_cb(*tube_info)

    def _list_tubes_error_cb(self, e):
        logging.error('ListTubes() failed: %s', e)

    def _new_tube_cb(self, id, initiator, type, service, params, state):
        logging.debug('New tube: ID=%d initator=%d type=%d service=%s '
                     'params=%r state=%d', id, initiator, type, service,
                     params, state)

        if (type == telepathy.TUBE_TYPE_DBUS and
                service == self.service):
            if state == telepathy.TUBE_STATE_LOCAL_PENDING:
                self._tubes_chan[telepathy.CHANNEL_TYPE_TUBES] \
                        .AcceptDBusTube(id)

            tube_conn = SugarTubeConnection(self._conn,
                self._tubes_chan[telepathy.CHANNEL_TYPE_TUBES], id,
                group_iface=self._text_chan[telepathy.CHANNEL_INTERFACE_GROUP])

            self._share(tube_conn, self.__initiator)
