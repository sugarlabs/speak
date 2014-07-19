# Speak.activity
# A simple front end to the espeak text-to-speech engine on the XO laptop
# http://wiki.laptop.org/go/Speak
#
# Copyright (C) 2008  Joshua Minor
# Copyright (C) 2014  Walter Bender
# This file is part of Speak.activity
#
# Parts of Speak.activity are based on code from Measure.activity
# Copyright (C) 2007  Arjun Sarwal - arjun@laptop.org
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

from eye import *


class Sleepy(Eye):
    def __init__(self, fill_color):
        Eye.__init__(self, fill_color)

        self._pixbuf = svg_str_to_pixbuf(eye_svg())

    def expose(self, widget, event):
        bounds = self.get_allocation()

        self.context = widget.window.cairo_create()

        #set a clip region for the expose event. This reduces
        #redrawing work (and time)
        self.context.rectangle(event.area.x, event.area.y,
                               event.area.width, event.area.height)
        self.context.clip()

        # background
        self.context.set_source_rgba(*self.fill_color.get_rgba())
        self.context.rectangle(0, 0, bounds.width, bounds.height)
        self.context.fill()

        w = h = min(bounds.width, bounds.height)
        x = int((bounds.width - w) / 2)
        y = int((bounds.height - h) / 2)
        pixbuf = self._pixbuf.scale_simple(w, h, gtk.gdk.INTERP_BILINEAR)
        self.context.translate(x + w / 2., y + h / 2.)
        self.context.translate(-x - w / 2., -y - h / 2.)
        self.context.set_source_pixbuf(pixbuf, x, y)
        self.context.rectangle(x, y, w, h)
        self.context.fill()

        return True


def svg_str_to_pixbuf(svg_string):
    """ Load pixbuf from SVG string """
    pl = gtk.gdk.PixbufLoader('svg')
    pl.write(svg_string)
    pl.close()
    pixbuf = pl.get_pixbuf()
    return pixbuf


def eye_svg():
    return \
        '<?xml version="1.0" encoding="UTF-8" standalone="no"?>\n' + \
        '<svg\n' + \
        '   xmlns:svg="http://www.w3.org/2000/svg"\n' + \
        '   xmlns="http://www.w3.org/2000/svg"\n' + \
        '   version="1.1"\n' + \
        '   width="300"\n' + \
        '   height="300">\n' + \
        '  <path\n' + \
        '          d="m 260.26893,151.09803 c -6.07398,14.55176 -15.05894,27.89881 -26.27797,39.03563 -11.21904,11.13683 -24.66333,20.05466 -39.32004,26.08168 -14.65671,6.02702 -30.51431,9.15849 -46.37814,9.15849 -15.86384,0 -31.72144,-3.13147 -46.37815,-9.15849 C 87.257925,210.18832 73.813631,201.27049 62.594594,190.13366 51.375557,178.99684 42.3906,165.64979 36.316616,151.09803"\n' + \
        '     style="fill:none;fill-opacity:1;fill-rule:nonzero;stroke:#000000;stroke-width:13.18636799;stroke-linecap:round;stroke-miterlimit:4;stroke-opacity:1;stroke-dasharray:none" />\n' + \
        '</svg>\n'
