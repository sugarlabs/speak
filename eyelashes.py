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


class Eyelashes(Eye):
    def __init__(self, fill_color):
        Eye.__init__(self, fill_color)

        self._pixbuf = svg_str_to_pixbuf(eyelashes_svg())

    def expose(self, widget, event):
        bounds = self.get_allocation()

        eyeSize = min(bounds.width, bounds.height)
        outlineWidth = eyeSize / 20.0
        pupilSize = eyeSize / 10.0
        pupilX, pupilY = self.computePupil()
        dX = pupilX - bounds.width / 2.
        dY = pupilY - bounds.height / 2.
        distance = math.sqrt(dX * dX + dY * dY)
        limit = eyeSize / 2 - outlineWidth * 2 - pupilSize
        if distance > limit:
            pupilX = bounds.width / 2 + dX * limit / distance
            pupilY = bounds.height / 2 + dY * limit / distance + \
                     int(bounds.height * 0.1)

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

        # pupil
        self.context.arc(pupilX, pupilY, pupilSize, 0, 2*math.pi)
        self.context.set_source_rgb(0, 0, 0)
        self.context.fill()

        return True


def svg_str_to_pixbuf(svg_string):
    """ Load pixbuf from SVG string """
    pl = gtk.gdk.PixbufLoader('svg')
    pl.write(svg_string)
    pl.close()
    pixbuf = pl.get_pixbuf()
    return pixbuf


def eyelashes_svg():
    return '<?xml version="1.0" encoding="UTF-8" standalone="no"?>\n' + \
        '<svg\n' + \
        'xmlns:svg="http://www.w3.org/2000/svg"\n' + \
        'xmlns="http://www.w3.org/2000/svg"\n' + \
        'version="1.1"\n' + \
        'width="300"\n' + \
        'height="300"\n' + \
        '>\n' + \
        '<g\n' + \
        'transform="matrix(5.4545455,0,0,5.4545455,-1.239,-5440.1557)"\n' + \
        '>\n' + \
        '<g\n' + \
        'transform="matrix(0.96700035,0,0,0.96700035,0.75256628,31.994388)"\n' + \
        '>\n' + \
        '<path\n' + \
        'd="m 702.85715,-306.42856 a 202.85715,201.42857 0 1 1 -405.7143,0 202.85715,201.42857 0 1 1 405.7143,0 z"\n' + \
        'transform="matrix(0.11328527,0,0,0.11328527,-29.306097,1065.8336)"\n' + \
        'style="fill:#ffffff;fill-opacity:1;fill-rule:nonzero;stroke:#000000;stroke-width:22.06818199;stroke-linecap:round;stroke-miterlimit:4;stroke-opacity:1;stroke-dasharray:none" />\n' + \
        '<path\n' + \
        'd="M 9.2108952,1016.3927 2.413779,1011.5376"\n' + \
        'style="fill:none;stroke:#000000;stroke-width:2.5;stroke-linecap:round;stroke-linejoin:miter;stroke-miterlimit:4;stroke-opacity:1;stroke-dasharray:none" />\n' + \
        '<path\n' + \
        'd="m 13.418634,1012.8323 -5.5024274,-7.1208"\n' + \
        'style="fill:none;stroke:#000000;stroke-width:2.5;stroke-linecap:round;stroke-linejoin:miter;stroke-miterlimit:4;stroke-opacity:1;stroke-dasharray:none" />\n' + \
        '<path\n' + \
        'd="m 17.626373,1010.2429 -3.884067,-8.0918"\n' + \
        'style="fill:none;stroke:#000000;stroke-width:2.5;stroke-linecap:round;stroke-linejoin:miter;stroke-miterlimit:4;stroke-opacity:1;stroke-dasharray:none" />\n' + \
        '<path\n' + \
        'd="m 22.805128,1008.5085 -2.406446,-8.51932"\n' + \
        'style="fill:none;stroke:#000000;stroke-width:2.5;stroke-linecap:round;stroke-linejoin:miter;stroke-miterlimit:4;stroke-opacity:1;stroke-dasharray:none" />\n' + \
        '<path\n' + \
        'd="m 27.452641,1007.6535 -0.116103,-8.09177"\n' + \
        'style="fill:none;stroke:#000000;stroke-width:2.5;stroke-linecap:round;stroke-linejoin:miter;stroke-miterlimit:4;stroke-opacity:1;stroke-dasharray:none" />\n' + \
        '<path\n' + \
        'd="m 32.39919,1008.4838 2.38181,-7.9511"\n' + \
        'style="fill:none;stroke:#000000;stroke-width:2.5;stroke-linecap:round;stroke-linejoin:miter;stroke-miterlimit:4;stroke-opacity:1;stroke-dasharray:none" />\n' + \
        '<path\n' + \
        'd="m 37.694049,1009.9192 3.884067,-8.0918"\n' + \
        'style="fill:none;stroke:#000000;stroke-width:2.5;stroke-linecap:round;stroke-linejoin:miter;stroke-miterlimit:4;stroke-opacity:1;stroke-dasharray:none" />\n' + \
        '<path\n' + \
        'd="m 41.901788,1013.156 4.855082,-7.4445"\n' + \
        'style="fill:none;stroke:#000000;stroke-width:2.5;stroke-linecap:round;stroke-linejoin:miter;stroke-miterlimit:4;stroke-opacity:1;stroke-dasharray:none" />\n' + \
        '<path\n' + \
        'd="m 45.462182,1017.04 7.444461,-5.1787"\n' + \
        'style="fill:none;stroke:#000000;stroke-width:2.5;stroke-linecap:round;stroke-linejoin:miter;stroke-miterlimit:4;stroke-opacity:1;stroke-dasharray:none" />\n' + \
        '</g>\n' + \
        '</g>\n' + \
        '</svg>'
