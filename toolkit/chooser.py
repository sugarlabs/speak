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

"""Object chooser method"""

import gtk
import logging

from sugar import mime
from sugar.graphics.objectchooser import ObjectChooser

TEXT  = hasattr(mime, 'GENERIC_TYPE_TEXT') and mime.GENERIC_TYPE_TEXT or None
IMAGE = hasattr(mime, 'GENERIC_TYPE_IMAGE') and mime.GENERIC_TYPE_IMAGE or None
AUDIO = hasattr(mime, 'GENERIC_TYPE_AUDIO') and mime.GENERIC_TYPE_AUDIO or None
VIDEO = hasattr(mime, 'GENERIC_TYPE_VIDEO') and mime.GENERIC_TYPE_VIDEO or None
LINK  = hasattr(mime, 'GENERIC_TYPE_LINK') and mime.GENERIC_TYPE_LINK or None


def pick(cb=None, default=None, parent=None, what=None):
    """
    Opens object chooser.

    Method returns:

        * cb(jobject), if object was choosen and cb is not None
        * jobject, if object was choosen and cb is None
        * default, otherwise

    NOTE: 'what' makes sense only for sugar >= 0.84
    """
    what = what and {'what_filter': what} or {}
    chooser = ObjectChooser(parent=parent, **what)

    jobject = None
    out = None

    try:
        if chooser.run() == gtk.RESPONSE_ACCEPT:
            jobject = chooser.get_selected_object()
            logging.debug('ObjectChooser: %r' % jobject)

            if jobject and jobject.file_path:
                if cb:
                    out = cb(jobject)
                else:
                    out = jobject
    finally:
        if jobject and id(jobject) != id(out):
            jobject.destroy()
        chooser.destroy()
        del chooser

    if out:
        return out
    else:
        return default
