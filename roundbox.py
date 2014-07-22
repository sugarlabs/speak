# Copyright 2014, Sugar Labs
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

import math
import gtk
from sugar.graphics import style

_BORDER_DEFAULT = style.LINE_WIDTH


class RoundBox(gtk.HBox):
    __gtype_name__ = 'RoundBox'

    def __init__(self, **kwargs):
        gtk.HBox.__init__(self, **kwargs)
        self._radius = style.zoom(15)
        self.border_color = style.COLOR_BLACK
        self.tail = None
        self.background_color = None
        self.set_resize_mode(gtk.RESIZE_PARENT)
        self.set_reallocate_redraws(True)
        self.connect('expose-event', self.__expose_cb)
        self.connect('add', self.__add_cb)

    def __add_cb(self, child, params):
        child.set_border_width(style.zoom(5))

    def __expose_cb(self, widget, event):
        cr = widget.window.cairo_create()
        rect = self.get_allocation()
        hmargin = style.zoom(15)
        x = rect.x + hmargin
        y = rect.y
        width = rect.width - _BORDER_DEFAULT * 2. - hmargin * 2
        if self.tail is None:
            height = rect.height - _BORDER_DEFAULT * 2.
        else:
            height = rect.height - _BORDER_DEFAULT * 2. - self._radius

        cr.move_to(x + self._radius, y)
        cr.arc(x + width - self._radius, y + self._radius,
               self._radius, math.pi * 1.5, math.pi * 2)
        tail_height = style.zoom(5)
        if self.tail == 'right':
            cr.arc(x + width - self._radius, y + height - self._radius * 2,
                   self._radius, 0, math.pi * 0.5)
            cr.line_to(x + width - self._radius, y + height)
            cr.line_to(x + width - tail_height * self._radius,
                       y + height - self._radius)
            cr.arc(x + self._radius, y + height - self._radius * 2,
                   self._radius, math.pi * 0.5, math.pi)
        elif self.tail == 'left':
            cr.arc(x + width - self._radius, y + height - self._radius * 2,
                   self._radius, 0, math.pi * 0.5)
            cr.line_to(x + self._radius * tail_height,
                       y + height - self._radius)
            cr.line_to(x + self._radius, y + height)
            cr.line_to(x + self._radius, y + height - self._radius)
            cr.arc(x + self._radius, y + height - self._radius * 2,
                   self._radius, math.pi * 0.5, math.pi)
        else:
            cr.arc(x + width - self._radius, y + height - self._radius,
                   self._radius, 0, math.pi * 0.5)
            cr.arc(x + self._radius, y + height - self._radius,
                   self._radius, math.pi * 0.5, math.pi)
        cr.arc(x + self._radius, y + self._radius, self._radius,
               math.pi, math.pi * 1.5)
        cr.close_path()

        if self.background_color is not None:
            r, g, b, __ = self.background_color.get_rgba()
            cr.set_source_rgb(r, g, b)
            cr.fill_preserve()

        if self.border_color is not None:
            r, g, b, __ = self.border_color.get_rgba()
            cr.set_source_rgb(r, g, b)
            cr.set_line_width(_BORDER_DEFAULT)
            cr.stroke()
        return False


if __name__ == '__main__':

    win = gtk.Window()
    win.connect('destroy', gtk.main_quit)
    win.set_default_size(450, 450)
    vbox = gtk.VBox()

    box1 = RoundBox()
    box1.tail = 'right'
    vbox.add(box1)
    label1 = gtk.Label("Test 1")
    box1.add(label1)

    rbox = RoundBox()
    rbox.tail = 'left'
    rbox.background_color = style.Color('#FF0000')
    vbox.add(rbox)
    label2 = gtk.Label("Test 2")
    rbox.add(label2)

    bbox = RoundBox()
    bbox.background_color = style.Color('#aaff33')
    bbox.border_color = style.Color('#ff3300')
    vbox.add(bbox)

    win.add(vbox)
    win.show_all()
    gtk.main()
