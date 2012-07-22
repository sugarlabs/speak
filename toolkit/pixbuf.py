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

"""gtk.gdk.Pixbuf extensions"""

import re
import cStringIO
import gtk
import rsvg
import cairo
import logging

from sugar.graphics import style
from sugar.graphics.xocolor import XoColor, is_valid
from sugar.util import LRU


def to_file(pixbuf):
    """Convert pixbuf object to file object"""

    def push(pixbuf, buffer):
        buffer.write(pixbuf)

    buffer = cStringIO.StringIO()
    pixbuf.save_to_callback(push, 'png', user_data=buffer)
    buffer.seek(0)

    return buffer

def to_str(pixbuf):
    """Convert pixbuf object to string"""
    return to_file(pixbuf).getvalue()

def from_str(str):
    """Convert string to pixbuf object"""

    loader = gtk.gdk.pixbuf_loader_new_with_mime_type('image/png')

    try:
        loader.write(str)
    except Exception, e:
        logging.error('pixbuf.from_str: %s' % e)
        return None
    finally:
        loader.close()

    return loader.get_pixbuf()


def at_size_with_ratio(pixbuf, width, height, type=gtk.gdk.INTERP_BILINEAR):
    image_width = pixbuf.get_width()
    image_height = pixbuf.get_height()

    ratio_width = float(width) / image_width
    ratio_height = float(height) / image_height
    ratio = min(ratio_width, ratio_height)

    if ratio_width != ratio:
        ratio_width = ratio
        width = int(image_width * ratio)
    elif ratio_height != ratio:
        ratio_height = ratio
        height = int(image_height * ratio)

    return pixbuf.scale_simple(width, height, type)

def from_svg_at_size(filename=None, width=None, height=None, handle=None,
        keep_ratio=True):
    """Scale and load SVG into pixbuf"""

    if not handle:
        handle = rsvg.Handle(filename)

    dimensions = handle.get_dimension_data()
    icon_width = dimensions[0]
    icon_height = dimensions[1]

    if icon_width != width or icon_height != height:
        ratio_width = float(width) / icon_width
        ratio_height = float(height) / icon_height

        if keep_ratio:
            ratio = min(ratio_width, ratio_height)
            if ratio_width != ratio:
                ratio_width = ratio
                width = int(icon_width * ratio)
            elif ratio_height != ratio:
                ratio_height = ratio
                height = int(icon_height * ratio)
    else:
        ratio_width = 1
        ratio_height = 1

    surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, width, height)
    context = cairo.Context(surface)
    context.scale(ratio_width, ratio_height)
    handle.render_cairo(context)

    loader = gtk.gdk.pixbuf_loader_new_with_mime_type('image/png')
    surface.write_to_png(loader)
    loader.close()

    return loader.get_pixbuf()
