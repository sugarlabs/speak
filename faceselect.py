# Speak.activity
# A simple front end to the espeak text-to-speech engine on the XO laptop
# http://wiki.laptop.org/go/Speak
#
# Copyright (C) 2008  Joshua Minor
# This file is part of Speak.activity
#
# Parts of Speak.activity are based on code from Measure.activity
# Copyright (C) 2007  Arjun Sarwal - arjun@laptop.org
#
# New face features
# Copyright (C) 2014  Walter Bender
# Copyright (C) 2014  Sam Parkinson
#
#     Speak.activity is free software: you can redistribute it and/or modify
#     it under the terms of the GNU General Public License as published by
#     the Free Software Foundation, either version 3 of the License, or
#     (at your option) any later version.
#
#     Speak.activity is distributed in the hope that it will be useful,
#     but WITHOUT ANY WARRANTY; without even the implied warranty of
#     MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#     GNU General Public License for more details.
#
#     You should have received a copy of the GNU General Public License
#     along with Speak.activity.  If not, see <http://www.gnu.org/licenses/>.


import math

from gettext import gettext as _

from gi.repository import Gtk
from gi.repository import Gdk
from gi.repository import GObject
from gi.repository import GdkPixbuf

from sugar3.graphics.icon import Icon

_POINT_CIRCUMFERENCE = 5

_LIMIT_VERTICAL = 1
_LIMIT_HORIZONTAL = 2

_STEPS = [_("Draw a line from the center to the edge of the left eye's iris"),
          _("Draw a line from the center to the edge of the right eye's iris"),
          _("Draw a line across the mouth")]


def _scale(iw, ih, aw, ah):
    factor = min(aw * 1.0 // iw, ah * 1.0 // ih)
    return int(iw * factor), int(ih * factor)


def _circumference(a, b):
    return math.sqrt((a[0] - b[0])**2 + (a[1] - b[1])**2)


class Eye(object):

    def __init__(self, center, circ):
        self.center = center
        self.circ = circ


class Mouth(object):

    def from_values(self, x, y, w, h, pixbuf):
        self.x = x
        self.y = y
        self.w = w
        self.h = h
        self.pixbuf = pixbuf

    def create(self, y, left_x, right_x, pixbuf):
        self.y = y
        self.x = left_x
        self.w = right_x - left_x
        self.h = pixbuf.get_height() - y
        self.pixbuf = pixbuf.new_subpixbuf(int(self.x), int(self.y),
                                           int(self.w), int(self.h))
        return self


class FaceSelector(Gtk.VBox):

    __gsignals__ = {
        'face-processed': (GObject.SIGNAL_RUN_FIRST, None,
                           [GObject.TYPE_OBJECT, GObject.TYPE_PYOBJECT,
                            GObject.TYPE_PYOBJECT, GObject.TYPE_PYOBJECT]),
        'cancel': (GObject.SIGNAL_RUN_FIRST, None, [])
    }

    def __init__(self, file_):
        Gtk.VBox.__init__(self)
        self._step = 0
        self._step_lines = []

        self._drawing = FaceSelectorDrawing(file_)
        self.pack_start(self._drawing, True, True, 0)
        self._drawing.show()

        self._toolbar = Gtk.Toolbar()
        self.pack_start(self._toolbar, False, True, 0)
        self._toolbar.show()

        self._label = Gtk.Label()
        self._label.set_alignment(0.5, 0.5)
        self._add_widget(self._label)

        sep = Gtk.SeparatorToolItem()
        sep.set_draw(False)
        sep.set_expand(True)
        self._toolbar.insert(sep, -1)
        sep.show()

        Gtk.Settings.get_default().props.gtk_button_images = True

        bnt = Gtk.Button()
        bnt.set_label(_('Cancel'))
        bnt.connect('clicked', self.__cancel_clicked_cb)
        self._add_widget(bnt)

        bnt = Gtk.Button()
        bnt.set_label(_('Next'))
        bnt.set_image(Icon(icon_name='go-next'))
        bnt.set_image_position(Gtk.PositionType.RIGHT)
        bnt.connect('clicked', self.__next_clicked_cb)
        self._add_widget(bnt)

        self._show_step(0)

    def _show_step(self, num):
        self._label.set_text(_STEPS[num])
        self._drawing.clear_line()

    def __cancel_clicked_cb(self, widget):
        self.emit('cancel')

    def __next_clicked_cb(self, widget):
        sp, ep = self._drawing.get_line()
        if not (sp and ep):
            return

        self._step_lines.append((sp, ep))
        self._step += 1

        if self._step == 2:
            self._drawing.limit_axis = _LIMIT_VERTICAL

        if self._step == len(_STEPS):
            self._process_data()
        else:
            self._show_step(self._step)

    def _process_data(self):
        left_eye = self._step_lines[0]
        left_eye_center = left_eye[0]
        left_eye_circ = _circumference(*left_eye)

        right_eye = self._step_lines[1]
        right_eye_center = right_eye[0]
        right_eye_circ = _circumference(*right_eye)

        mouth = self._step_lines[2]
        mouth_y = mouth[0][1]
        mouth_x_left = min(mouth[0][0], mouth[1][0])
        mouth_x_right = max(mouth[0][0], mouth[1][0])

        self.emit('face-processed', self._drawing.get_pixbuf(),
                  Eye(left_eye_center, left_eye_circ),
                  Eye(right_eye_center, right_eye_circ),
                  Mouth().create(mouth_y, mouth_x_left, mouth_x_right,
                                 self._drawing.get_pixbuf()))

    def _add_widget(self, widget):
        t = Gtk.ToolItem()
        t.set_expand(True)
        t.add(widget)
        widget.show()
        self._toolbar.insert(t, -1)
        t.show()


class FaceSelectorDrawing(Gtk.DrawingArea):

    def __init__(self, file_):
        Gtk.DrawingArea.__init__(self)
        self.limit_axis = None
        self._start_point = None
        self._end_point = None
        self._mouse_point = None

        self._full_pixbuf = GdkPixbuf.Pixbuf.new_from_file(file_)
        self._pixbuf = None
        self._offset_x = None
        self._offset_y = None

        self.set_events(Gdk.EventMask.BUTTON_PRESS_MASK
                        | Gdk.EventMask.BUTTON_RELEASE_MASK
                        | Gdk.EventMask.POINTER_MOTION_MASK)
        self.connect('draw', self.__draw_cb)
        self.connect('button-press-event', self.__button_press_cb)
        self.connect('button-release-event', self.__button_release_cb)
        self.connect('motion-notify-event', self.__motion_cb)

    def __draw_cb(self, widget, cr):
        alloc = widget.get_allocation()

        if not self._pixbuf:
            sw, sh = _scale(self._full_pixbuf.get_width(),
                            self._full_pixbuf.get_height(),
                            alloc.width,
                            alloc.height)
            self._pixbuf = self._full_pixbuf.scale_simple(
                sw, sh, GdkPixbuf.InterpType.BILINEAR)

            self._offset_x = (alloc.width - sw) // 2
            self._offset_y = (alloc.height - sh) // 2

        cr.rectangle(self._offset_x, self._offset_y, alloc.width, alloc.height)
        Gdk.cairo_set_source_pixbuf(cr, self._pixbuf,
                                    self._offset_x, self._offset_y)
        cr.fill()

        if self._start_point and (self._mouse_point or self._end_point):
            sx, sy = self._start_point
            mx, my = self._end_point if self._end_point else self._mouse_point
            cr.move_to(sx, sy)
            cr.line_to(mx, my)
            cr.close_path()

            cr.set_source_rgb(1.0, 1.0, 0.0)
            cr.set_line_width(1)
            cr.stroke()

        if self._start_point:
            x, y = self._start_point
            cr.arc(x, y, _POINT_CIRCUMFERENCE, 0, 2 * math.pi)
            cr.set_source_rgb(1.0, 1.0, 0.0)
            cr.fill()

        if self._end_point:
            x, y = self._end_point
            cr.arc(x, y, _POINT_CIRCUMFERENCE, 0, 2 * math.pi)
            cr.set_source_rgb(1.0, 1.0, 0.0)
            cr.fill()

        return False

    def _redraw(self):
        alloc = self.get_allocation()
        self.queue_draw_area(0, 0, alloc.width, alloc.height)

    def __button_press_cb(self, widget, event):
        self._start_point = (event.x, event.y)
        self._end_point = None
        self._redraw()

    def __button_release_cb(self, widget, event):
        sx, sy = self._start_point
        self._end_point = \
            (sx if self.limit_axis == _LIMIT_HORIZONTAL else event.x,
             sy if self.limit_axis == _LIMIT_VERTICAL else event.y)
        self._redraw()

    def __motion_cb(self, widget, event):
        if self._start_point:
            sx, sy = self._start_point
            self._mouse_point = \
                (sx if self.limit_axis == _LIMIT_HORIZONTAL else event.x,
                 sy if self.limit_axis == _LIMIT_VERTICAL else event.y)
            self._redraw()

    def get_line(self):
        return (self._start_point[0] - self._offset_x,
                self._start_point[1] - self._offset_y), \
               (self._end_point[0] - self._offset_x,
                self._end_point[1] - self._offset_y)

    def clear_line(self):
        self._start_point = None
        self._end_point = None
        self._mouse_point = None
        self._redraw()

    def get_pixbuf(self):
        return self._pixbuf
