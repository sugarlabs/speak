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


class Sunglasses(Eye):
    def __init__(self, fill_color):
        Eye.__init__(self, fill_color)

        self._pixbufs = []
        self._pixbufs.append(svg_str_to_pixbuf(lefteye_svg()))
        self._pixbufs.append(svg_str_to_pixbuf(centereye_svg()))
        self._pixbufs.append(svg_str_to_pixbuf(righteye_svg()))
        self._which_eye = 2

    def has_padding(self):
        return False

    def has_left_center_right(self):
        return True

    def set_eye(self, which_eye):
        if which_eye < 0 or which_eye > len(self._pixbufs) - 1:
            which_eye = 1
        self._which_eye = which_eye

    def draw(self, widget, cr):
        bounds = self.get_allocation()

        eyeSize = min(bounds.width, bounds.height)
        outlineWidth = eyeSize / 20.0
        pupilSize = eyeSize / 10.0
        pupilX, pupilY = self.computePupil()
        dX = pupilX - bounds.width / 2.
        dY = pupilY - bounds.height / 2.
        distance = math.sqrt(dX * dX + dY * dY)
        limit = eyeSize // 2 - outlineWidth * 2 - pupilSize * 2
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
        pixbuf = self._pixbufs[self._which_eye].scale_simple(
            w, h, GdkPixbuf.InterpType.BILINEAR)
        cr.translate(x + w / 2., y + h / 2.)
        cr.translate(-x - w / 2., -y - h / 2.)

        if self._which_eye == 0:
            x = bounds.width - w
            dx = x - int((bounds.width - w) // 2)
            Gdk.cairo_set_source_pixbuf(cr, pixbuf, x, y)
            cr.rectangle(x, y, w, h)
        elif self._which_eye == 2:
            dx = -x
            Gdk.cairo_set_source_pixbuf(cr, pixbuf, 0, y)
            cr.rectangle(0, y, w, h)
        else:
            dx = 0
            Gdk.cairo_set_source_pixbuf(cr, pixbuf, x, y)
            cr.rectangle(x, y, w, h)

        cr.fill()

        # pupil
        cr.arc(pupilX + dx, pupilY, pupilSize, 0, 2 * math.pi)
        cr.set_source_rgb(255, 255, 255)
        cr.fill()

        return True


def lefteye_svg():
    return \
        '<?xml version="1.0" encoding="UTF-8" standalone="no"?>\n' + \
        '<svg\n' + \
        'xmlns:svg="http://www.w3.org/2000/svg"\n' + \
        'xmlns="http://www.w3.org/2000/svg"\n' + \
        'version="1.1"\n' + \
        'width="300"\n' + \
        'height="300"\n' + \
        '>\n' + \
        '<g\n' + \
        'transform="translate(0,-752.36218)"\n' + \
        '>\n' + \
        '<path\n' + \
        'd="m 4.221987,818.14744 0,32.50132 c 0,0 15.43321,6.07134 20.074349,12.42698 20.144546,27.58623 2.706611,73.4101 24.853957,99.41583 20.454142,24.01754 55.509537,35.21531 86.988847,37.28094 29.39338,1.92879 60.82856,-7.17372 85.07701,-23.89804 16.31556,-11.25294 30.13344,-28.68026 35.36909,-47.79607 6.39204,-23.33787 6.57785,-45.81419 22.94211,-59.26713 C 283.77642,865.31816 295,865.86218 295,865.86218 l 0,-30.50816 c 0,0 -27.60771,-6.26 -41.28253,-9.55921 -21.71145,-5.23814 -42.9884,-12.48265 -65.00265,-16.25067 -16.71978,-2.8618 -33.70419,-4.44612 -50.66384,-4.7796 -23.29114,-0.45798 -46.606389,1.46439 -69.782259,3.82368 -21.474409,2.18608 -64.046734,9.55922 -64.046734,9.55922 z"\n' + \
        'style="fill:#000000;fill-opacity:1;stroke:#000000;stroke-width:8.44397259;stroke-linecap:butt;stroke-linejoin:miter;stroke-miterlimit:4;stroke-opacity:1;stroke-dasharray:none" />\n' + \
        '<path\n' + \
        'd="m 55.471701,108.67924 a 20.377359,3.3962264 0 1 1 -40.754719,0 20.377359,3.3962264 0 1 1 40.754719,0 z"\n' + \
        'transform="matrix(0.84273125,-0.05301633,0.05301633,0.84273125,4.2542086,746.58312)"\n' + \
        'style="fill:#ffffff;fill-opacity:1;fill-rule:nonzero;stroke:#ffffff;stroke-width:10;stroke-linecap:round;stroke-linejoin:round;stroke-miterlimit:4;stroke-opacity:1;stroke-dasharray:none;stroke-dashoffset:0" />\n' + \
        '</g>\n' + \
        '</svg>\n'


def righteye_svg():
    return \
        '<?xml version="1.0" encoding="UTF-8" standalone="no"?>\n' + \
        '<svg\n' + \
        'xmlns:svg="http://www.w3.org/2000/svg"\n' + \
        'xmlns="http://www.w3.org/2000/svg"\n' + \
        'version="1.1"\n' + \
        'width="300"\n' + \
        'height="300"\n' + \
        '>\n' + \
        '<g\n' + \
        'transform="matrix(-1,0,0,1,299.22199,0)"\n' + \
        'id="g2985">\n' + \
        '<g\n' + \
        'transform="translate(0,-752.36218)"\n' + \
        'id="layer1">\n' + \
        '<path\n' + \
        'd="m 4.221987,818.14744 0,32.50132 c 0,0 15.43321,6.07134 20.07435,12.42698 20.14454,27.58623 2.70661,73.4101 24.85396,99.41583 20.45414,24.01754 55.509533,35.21531 86.988843,37.28094 29.39338,1.92879 60.82856,-7.17372 85.07701,-23.89804 16.31556,-11.25294 30.13344,-28.68026 35.36909,-47.79607 6.39204,-23.33787 6.57785,-45.81419 22.94211,-59.26713 C 283.77642,865.31816 295,865.86218 295,865.86218 l 0,-30.50816 c 0,0 -27.60771,-6.26 -41.28253,-9.55921 -21.71145,-5.23814 -42.9884,-12.48265 -65.00265,-16.25067 -16.71978,-2.8618 -33.70419,-4.44612 -50.66384,-4.7796 -23.29114,-0.45798 -46.606393,1.46439 -69.782263,3.82368 -21.47441,2.18608 -64.04673,9.55922 -64.04673,9.55922 z"\n' + \
        'id="path3050"\n' + \
        'style="fill:#000000;fill-opacity:1;stroke:#000000;stroke-width:8.44397259;stroke-linecap:butt;stroke-linejoin:miter;stroke-miterlimit:4;stroke-opacity:1;stroke-dasharray:none" />\n' + \
        '<path\n' + \
        'd="m 55.471701,108.67924 a 20.377359,3.3962266 0 1 1 -40.754719,0 20.377359,3.3962266 0 1 1 40.754719,0 z"\n' + \
        'transform="matrix(0.84273125,-0.05301633,0.05301633,0.84273125,4.2542086,746.58312)"\n' + \
        'id="path3820"\n' + \
        'style="fill:#ffffff;fill-opacity:1;fill-rule:nonzero;stroke:#ffffff;stroke-width:10;stroke-linecap:round;stroke-linejoin:round;stroke-miterlimit:4;stroke-opacity:1;stroke-dasharray:none;stroke-dashoffset:0" />\n' + \
        '</g>\n' + \
        '</g>\n' + \
        '</svg>\n'


def centereye_svg():
    return \
        '<?xml version="1.0" encoding="UTF-8" standalone="no"?>\n' + \
        '<svg\n' + \
        'xmlns:svg="http://www.w3.org/2000/svg"\n' + \
        'xmlns="http://www.w3.org/2000/svg"\n' + \
        'version="1.1"\n' + \
        'width="300"\n' + \
        'height="300"\n' + \
        '>\n' + \
        '<g\n' + \
        'transform="translate(0,-752.36218)"\n' + \
        '>\n' + \
        '<path\n' + \
        'd="m 295,835.36218 0,30.5 c 0,0 -8.3514,-1.23619 -15,2.97454 -17.45316,11.05354 -15.40761,40.17057 -22,60.07644 -5.83383,17.61538 -15.94855,33.62104 -30.8515,47.36654 C 203.05917,998.49811 172.18203,999.82963 150,999.77251 127.81797,999.71541 101.933,993.00402 77.684545,976.2797 61.368985,965.02676 47.551105,948.02897 42.315455,928.91316 35.923415,905.57529 36.36426,882.28967 20,868.83672 15.75093,865.34361 4.221987,865.86218 4.221987,865.86218 l 0,-30.50816 c 0,0 27.60771,-6.25963 41.28253,-9.55884 C 81.607471,816.37471 122.81158,805.35132 150,804.76454 c 27.18842,-0.58678 69.23269,9.92537 105,21.03064 15.27366,4.74226 40,9.567 40,9.567 z"\n' + \
        'style="fill:#000000;fill-opacity:1;stroke:#000000;stroke-width:8.44397259;stroke-linecap:butt;stroke-linejoin:miter;stroke-miterlimit:4;stroke-opacity:1;stroke-dasharray:none" />\n' + \
        '</g>\n' + \
        '</svg>\n'
