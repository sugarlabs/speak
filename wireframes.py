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
import logging


class Wireframes(Eye):
    def __init__(self, fill_color):
        Eye.__init__(self, fill_color)

        self._pixbufs = []
        self._pixbufs.append(svg_str_to_pixbuf(lefteye_svg()))
        self._pixbufs.append(svg_str_to_pixbuf(centereye_svg()))
        self._pixbufs.append(svg_str_to_pixbuf(righteye_svg()))
        self._which_eye = 1

    def has_padding(self):
        return False

    def has_left_center_right(self):
        return True

    def set_eye(self, which_eye):
        if which_eye < 0 or which_eye > len(self._pixbufs) - 1:
            which_eye = 1
        self._which_eye = which_eye

    def expose(self, widget, event):
        bounds = self.get_allocation()

        eyeSize = min(bounds.width, bounds.height)
        outlineWidth = eyeSize / 20.0
        pupilSize = eyeSize / 10.0
        pupilX, pupilY = self.computePupil()
        dX = pupilX - bounds.width / 2.
        dY = pupilY - bounds.height / 2.
        distance = math.sqrt(dX * dX + dY * dY)
        limit = eyeSize / 2 - outlineWidth * 2 - pupilSize * 2
        if distance > limit:
            pupilX = bounds.width / 2 + dX * limit / distance
            pupilY = bounds.height / 2 + dY * limit / distance

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
        pixbuf = self._pixbufs[self._which_eye].scale_simple(
            w, h, gtk.gdk.INTERP_BILINEAR)
        self.context.translate(x + w / 2., y + h / 2.)
        self.context.translate(-x - w / 2., -y - h / 2.)

        if self._which_eye == 0:
            x = bounds.width - w
            dx = x - int((bounds.width - w) / 2)
            self.context.set_source_pixbuf(pixbuf, x, y)
            self.context.rectangle(x, y, w, h)
        elif self._which_eye == 2:
            dx = -x
            self.context.set_source_pixbuf(pixbuf, 0, y)
            self.context.rectangle(0, y, w, h)
        else:
            dx = 0
            self.context.set_source_pixbuf(pixbuf, x, y)
            self.context.rectangle(x, y, w, h)

        self.context.fill()

        # pupil
        self.context.arc(pupilX + dx, pupilY, pupilSize, 0, 2*math.pi)
        self.context.set_source_rgb(255, 255, 255)
        self.context.fill()

        return True


def svg_str_to_pixbuf(svg_string):
    """ Load pixbuf from SVG string """
    pl = gtk.gdk.PixbufLoader('svg')
    pl.write(svg_string)
    pl.close()
    pixbuf = pl.get_pixbuf()
    return pixbuf


def lefteye_svg():
    return \
        '<?xml version="1.0" encoding="UTF-8" standalone="no"?>\n' + \
        '<svg\n' + \
        'xmlns:svg="http://www.w3.org/2000/svg"\n' + \
        'xmlns="http://www.w3.org/2000/svg"\n' + \
        'version="1.1"\n' + \
        'width="300"\n' + \
        'height="300"\n' + \
        'id="svg2">\n' + \
        '<g\n' + \
        'transform="translate(0,-752.36218)"\n' + \
        'id="layer1">\n' + \
        '<g\n' + \
        'id="g3836">\n' + \
        '<path\n' + \
        'd="m 189.36512,795.09433 c 22.2049,4.57289 39.65255,13.60803 54.63845,27.79851 5.82185,5.58038 10.86979,12.47939 13.41997,20.12995 3.64313,10.92938 3.72637,23.13088 1.91714,34.5085 -2.90735,18.28333 -10.61556,35.88165 -20.12995,51.76274 -10.59773,17.68938 -23.93941,34.36566 -40.25991,46.96991 -21.37604,16.5086 -46.35091,30.25176 -72.85128,35.46706 -19.47799,3.8333 -41.21539,4.0567 -59.431295,-3.8343 C 47.377417,999.54009 31.513035,982.76427 20.656919,964.7611 10.049414,947.17021 5.1147028,925.85761 4.361243,905.3298 3.6326265,885.4787 5.837951,864.00566 15.86407,846.85707 26.044643,829.4443 44.231979,817.33113 61.875396,807.55573 c 15.822774,-8.76667 33.883599,-13.54784 51.762744,-16.29568 25.55956,-1.29621 52.33526,0.0824 75.72698,3.83428 z"\n' + \
        'id="path3050"\n' + \
        'style="fill:#000000;fill-opacity:1;stroke:#000000;stroke-width:8.4673624;stroke-linecap:butt;stroke-linejoin:miter;stroke-miterlimit:4;stroke-opacity:1;stroke-dasharray:none" />\n' + \
        '<path\n' + \
        'd="m 41.745444,896.70268 c -6.981137,-0.6094 -11.943714,-8.76601 -14.378538,-15.33711 -2.555831,-6.89769 -1.277573,-15.03924 0.958565,-22.0471 3.933538,-12.32733 11.237689,-24.20107 21.088525,-32.59135 6.643865,-5.6588 15.42386,-8.74846 23.964236,-10.54427 6.879072,-1.44648 15.167324,-3.78858 21.088525,0 3.853582,2.46565 6.208913,7.90946 5.751413,12.4614 -0.594366,5.91368 -6.794202,9.76748 -10.544262,14.37854 -5.424615,6.67011 -11.813638,12.51432 -17.254249,19.17139 -6.794,8.31306 -11.602395,18.2672 -19.171387,25.88137 -3.378952,3.39913 -6.728141,9.04392 -11.502828,8.62713 z"\n' + \
        'id="path3820"\n' + \
        'style="fill:#808080;fill-opacity:1;stroke:#000000;stroke-width:0.84673625px;stroke-linecap:butt;stroke-linejoin:miter;stroke-opacity:1" />\n' + \
        '<path\n' + \
        'd="m 218.45365,803.24217 77.31235,0"\n' + \
        'id="path3822"\n' + \
        'style="fill:none;stroke:#000000;stroke-width:8.4673624;stroke-linecap:square;stroke-linejoin:miter;stroke-miterlimit:4;stroke-opacity:1;stroke-dasharray:none" />\n' + \
        '<path\n' + \
        'd="m 257.42354,843.02279 c 0,0 10.4078,-6.86417 16.29568,-8.62712 6.45711,-1.93339 22.04678,-1.91714 22.04678,-1.91714"\n' + \
        'id="path3824"\n' + \
        'style="fill:none;stroke:#000000;stroke-width:8.4673624;stroke-linecap:square;stroke-linejoin:miter;stroke-miterlimit:4;stroke-opacity:1;stroke-dasharray:none" />\n' + \
        '</g>\n' + \
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
        'id="svg2">\n' + \
        '<path\n' + \
        'd="m 110.63456,42.73215 c -22.2049,4.57289 -39.65255,13.60803 -54.63845,27.79851 -5.82185,5.58038 -10.86979,12.47939 -13.41997,20.12995 -3.64313,10.92938 -3.72637,23.13088 -1.91714,34.5085 2.90735,18.28333 10.61556,35.88165 20.12995,51.76274 10.59773,17.68938 23.93941,34.36566 40.25991,46.96991 21.37604,16.5086 46.35091,30.25176 72.85128,35.46706 19.47799,3.8333 41.21539,4.0567 59.43129,-3.8343 19.29083,-8.35661 35.15521,-25.13243 46.01133,-43.1356 10.60751,-17.59089 15.54222,-38.90349 16.29568,-59.4313 0.72861,-19.8511 -1.47671,-41.32414 -11.50283,-58.47273 C 273.95504,77.08212 255.7677,64.96895 238.12428,55.19355 222.30151,46.42688 204.24069,41.64571 186.36154,38.89787 c -25.55956,-1.29621 -52.33526,0.0824 -75.72698,3.83428 z"\n' + \
        'id="path3050"\n' + \
        'style="fill:#000000;fill-opacity:1;stroke:#000000;stroke-width:8.4673624;stroke-linecap:butt;stroke-linejoin:miter;stroke-miterlimit:4;stroke-opacity:1;stroke-dasharray:none" />\n' + \
        '<path\n' + \
        'd="m 81.54603,50.87999 -77.31235,0"\n' + \
        'id="path3822"\n' + \
        'style="fill:none;stroke:#000000;stroke-width:8.4673624;stroke-linecap:square;stroke-linejoin:miter;stroke-miterlimit:4;stroke-opacity:1;stroke-dasharray:none" />\n' + \
        '<path\n' + \
        'd="m 42.57614,90.66061 c 0,0 -10.4078,-6.86417 -16.29568,-8.62712 C 19.82335,80.1001 4.23368,80.11635 4.23368,80.11635"\n' + \
        'id="path3824"\n' + \
        'style="fill:none;stroke:#000000;stroke-width:8.4673624;stroke-linecap:square;stroke-linejoin:miter;stroke-miterlimit:4;stroke-opacity:1;stroke-dasharray:none" />\n' + \
        '<path\n' + \
        'd="m 65.745604,144.15196 c -6.981137,-0.6094 -11.943714,-8.76601 -14.378538,-15.33711 -2.555831,-6.89769 -1.277573,-15.03924 0.958565,-22.0471 3.933538,-12.32733 11.237689,-24.20107 21.088525,-32.59135 6.643865,-5.6588 15.42386,-8.74846 23.964236,-10.54427 6.879068,-1.44648 15.167328,-3.78858 21.088528,0 3.85358,2.46565 6.20891,7.90946 5.75141,12.4614 -0.59437,5.91368 -6.7942,9.76748 -10.54426,14.37854 -5.42462,6.67011 -11.81364,12.51432 -17.254251,19.17139 -6.794,8.31306 -11.602395,18.2672 -19.171387,25.88137 -3.378952,3.39913 -6.728141,9.04392 -11.502828,8.62713 z"\n' + \
        'id="path3820-6"\n' + \
        'style="fill:#808080;fill-opacity:1;stroke:#000000;stroke-width:0.84673625px;stroke-linecap:butt;stroke-linejoin:miter;stroke-opacity:1" />\n' + \
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
        'id="svg2">\n' + \
        '<path\n' + \
        'd="m -48,117.5 a 123,116.5 0 1 1 -246,0 123,116.5 0 1 1 246,0 z"\n' + \
        'transform="matrix(0.9473704,0,0,1.000228,311.50034,34.973213)"\n' + \
        'id="path3001"\n' + \
        'style="fill:#000000;fill-opacity:1;fill-rule:nonzero;stroke:#000000;stroke-width:2;stroke-linecap:square;stroke-linejoin:round;stroke-miterlimit:4;stroke-opacity:1;stroke-dasharray:none;stroke-dashoffset:0" />\n' + \
        '<path\n' + \
        'd="m 97.54603,50.87999 -93.31235,0"\n' + \
        'id="path3822"\n' + \
        'style="fill:none;stroke:#000000;stroke-width:8.4673624;stroke-linecap:square;stroke-linejoin:miter;stroke-miterlimit:4;stroke-opacity:1;stroke-dasharray:none" />\n' + \
        '<path\n' + \
        'd="m 50.57614,90.66061 c 0,0 -10.4078,-6.86417 -16.29568,-8.62712 C 27.82335,80.1001 4.23368,80.11635 4.23368,80.11635"\n' + \
        'id="path3824"\n' + \
        'style="fill:none;stroke:#000000;stroke-width:8.4673624;stroke-linecap:square;stroke-linejoin:miter;stroke-miterlimit:4;stroke-opacity:1;stroke-dasharray:none" />\n' + \
        '<path\n' + \
        'd="m 73.745603,144.15196 c -6.981137,-0.6094 -11.943714,-8.76601 -14.378538,-15.33711 -2.555831,-6.89769 -1.277573,-15.03924 0.958565,-22.0471 3.933538,-12.32733 11.237689,-24.20107 21.088525,-32.59135 6.643865,-5.6588 15.42386,-8.74846 23.964235,-10.54427 6.87907,-1.44648 15.16733,-3.78858 21.08853,0 3.85358,2.46565 6.20891,7.90946 5.75141,12.4614 -0.59437,5.91368 -6.7942,9.76748 -10.54426,14.37854 -5.42462,6.67011 -11.81364,12.51432 -17.25425,19.17139 -6.794002,8.31306 -11.602397,18.2672 -19.171389,25.88137 -3.378952,3.39913 -6.728141,9.04392 -11.502828,8.62713 z"\n' + \
        'id="path3820-3"\n' + \
        'style="fill:#808080;fill-opacity:1;stroke:#000000;stroke-width:0.84673625px;stroke-linecap:butt;stroke-linejoin:miter;stroke-opacity:1" />\n' + \
        '<path\n' + \
        'd="m 200.45381,50.69145 95.31235,0"\n' + \
        'id="path3822-7"\n' + \
        'style="fill:none;stroke:#000000;stroke-width:8.4673624;stroke-linecap:square;stroke-linejoin:miter;stroke-miterlimit:4;stroke-opacity:1;stroke-dasharray:none" />\n' + \
        '<path\n' + \
        'd="m 249.4237,90.47207 c 0,0 10.4078,-6.86417 16.29568,-8.62712 6.45711,-1.93339 30.04678,-1.91714 30.04678,-1.91714"\n' + \
        'id="path3824-7"\n' + \
        'style="fill:none;stroke:#000000;stroke-width:8.4673624;stroke-linecap:square;stroke-linejoin:miter;stroke-miterlimit:4;stroke-opacity:1;stroke-dasharray:none" />\n' + \
        '</svg>\n'
