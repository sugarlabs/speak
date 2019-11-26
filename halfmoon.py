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

import math

from gi.repository import Gdk
from gi.repository import GdkPixbuf

from eye import Eye
from utils import svg_str_to_pixbuf


class Halfmoon(Eye):
    def __init__(self, fill_color):
        Eye.__init__(self, fill_color)

        self._pixbuf = svg_str_to_pixbuf(eye_svg())

    def draw(self, widget, cr):
        bounds = self.get_allocation()

        eyeSize = min(bounds.width, bounds.height)
        outlineWidth = eyeSize / 20.0
        pupilSize = eyeSize / 10.0
        pupilX, pupilY = self.computePupil()
        dX = pupilX - bounds.width / 2.
        dY = pupilY - bounds.height / 2.
        distance = math.sqrt(dX * dX + dY * dY)
        limit = eyeSize // 2 - outlineWidth * 2 - pupilSize * 2.5
        if distance > limit:
            pupilX = bounds.width // 2 + dX * limit // distance
            pupilY = bounds.height // 2 + dY * limit // distance

        # background
        cr.set_source_rgba(*self.fill_color.get_rgba())
        cr.rectangle(0, 0, bounds.width, bounds.height)
        cr.fill()

        w = h = min(bounds.width, bounds.height)
        x = int((bounds.width - w) // 2)
        y = int((bounds.height - h) // 2)
        pixbuf = self._pixbuf.scale_simple(w, h, GdkPixbuf.InterpType.BILINEAR)
        cr.translate(x + w / 2., y + h / 2.)
        cr.translate(-x - w / 2., -y - h / 2.)
        Gdk.cairo_set_source_pixbuf(cr, pixbuf, x, y)
        cr.rectangle(x, y, w, h)
        cr.fill()

        # pupil
        cr.arc(pupilX, pupilY, pupilSize, 0, 2 * math.pi)
        cr.set_source_rgb(0, 0, 0)
        cr.fill()

        return True


def eye_svg():
    return \
        '<?xml version="1.0" encoding="UTF-8" standalone="no"?>\n' + \
        '<svg\n' + \
        'xmlns:svg="http://www.w3.org/2000/svg"\n' + \
        'xmlns="http://www.w3.org/2000/svg"\n' + \
        'version="1.1"\n' + \
        'width="300"\n' + \
        'height="300"\n' + \
        'id="svg2">\n' + \
        '<path\n' + \
        'd="m 292.26189,79.390293 c -0.006,18.487519 -3.71201,36.966707 -10.84078,54.045417 -7.12874,17.07871 -17.67397,32.74352 -30.84121,45.81427 -13.16726,13.07078 -28.94619,23.53721 -46.14807,30.61084 -17.20189,7.07363 -35.8132,10.74889 -54.43183,10.74889 -18.61864,0 -37.22996,-3.67526 -54.431839,-10.74889 C 78.366281,202.78719 62.58735,192.32076 49.420097,179.24998 36.252844,166.17923 25.707625,150.51442 18.578877,133.43571 11.45013,116.357 7.7434585,97.877812 7.7381095,79.390293 z"\n' + \
        'style="fill:#ffffff;fill-opacity:1;fill-rule:nonzero;stroke:#000000;stroke-width:15.47621632;stroke-linecap:round;stroke-miterlimit:4;stroke-opacity:1;stroke-dasharray:none" />\n' + \
        '</svg>\n'
