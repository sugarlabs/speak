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

# Widget was copy&pasted from TamTam activities

import gtk
import rsvg
import cairo

from sugar.graphics import style

class TempoSlider(gtk.HBox):
    def __init__(self, min_value, max_value):
        gtk.HBox.__init__(self)

        self._pixbuf = [None] * 8
        self._image = gtk.Image()
        self._image.show()

        # used to store tempo updates while the slider is active
        self._delayed = 0
        self._active = False

        self.adjustment = gtk.Adjustment(min_value, min_value, max_value,
                (max_value - min_value) / 8, (max_value - min_value) / 8, 0)
        self._adjustment_h = self.adjustment.connect('value-changed',
                self._changed_cb)

        slider = gtk.HScale(adjustment = self.adjustment)
        slider.show()
        slider.set_draw_value(False)
        slider.connect("button-press-event", self._press_cb)
        slider.connect("button-release-event", self._release_cb)

        self.pack_start(slider, True, True)
        self.pack_end(self._image, False, False)

    def set_value(self, tempo, quiet = False):
        if self._active:
            self._delayed = tempo
        elif quiet:
            self.adjustment.handler_block(self._adjustment_h)
            self.adjustment.set_value(tempo)
            self._update(tempo)
            self.adjustment.handler_unblock(self._adjustment_h)
        else:
            self.adjustment.set_value(tempo)

    def _changed_cb(self, widget):
        self._update(widget.get_value())

    def _update(self, tempo):
        def map_range(value, ilower, iupper, olower, oupper):
            if value == iupper:
                return oupper
            return olower + int((oupper-olower+1) * (value-ilower) /
                    float(iupper-ilower))

        img = map_range(tempo, self.adjustment.lower,
                            self.adjustment.upper, 0, 7)

        if not self._pixbuf[img]:
            svg = rsvg.Handle(data=IMAGE[img])
            self._pixbuf[img] = _from_svg_at_size(handle=svg,
                    width=style.STANDARD_ICON_SIZE,
                    height=style.STANDARD_ICON_SIZE)

        self._image.set_from_pixbuf(self._pixbuf[img])

    def _press_cb(self, widget, event):
        self._active = True

    def _release_cb(self, widget, event):
        self._active = False
        if self._delayed != 0:
            self.set_value(self._delayed, True)
            self._delayed = 0

def _from_svg_at_size(filename=None, width=None, height=None, handle=None,
        keep_ratio=True):
    """ import from pixbuf.py """

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

IMAGE = [None] * 8

IMAGE[0] = """<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE svg PUBLIC "-//W3C//DTD SVG 1.1//EN" "http://www.w3.org/Graphics/SVG/1.1/DTD/svg11.dtd">
<svg version="1.1" id="Layer_1" xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" x="0px" y="0px"
     width="50px" height="50px" viewBox="0 0 50 50" enable-background="new 0 0 50 50" xml:space="preserve">
<path fill-rule="evenodd" clip-rule="evenodd" fill="#FFFFFF" d="M23.5,6.5c3,3,7,7,9,11c-7,5-4,6-3,26c-1,1-8,1-9,0c0,0,2,1,2-1
    c0-3-2-7-2-11c0-2,1-4,1-6c0-3-2-1-2-3c0-3,3-8,3-11c0-2-1-1-2-2v-3H23.5z"/>
</svg>
"""

IMAGE[1] = """<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE svg PUBLIC "-//W3C//DTD SVG 1.1//EN" "http://www.w3.org/Graphics/SVG/1.1/DTD/svg11.dtd">
<svg version="1.1" id="Layer_1" xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" x="0px" y="0px"
     width="50px" height="50px" viewBox="0 0 50 50" enable-background="new 0 0 50 50" xml:space="preserve">
<path fill-rule="evenodd" clip-rule="evenodd" fill="#FFFFFF" d="M27.5,44.5v-3C28.5,42.5,28.5,43.5,27.5,44.5z M26.5,10.5
    c2,2,2,6,2,8c0,4-3,11-3,13s4,7,7,10c-2,2-4,3-5,5h-6c1-1,2-3,2-5c0-3-2-9-3-14c0,0,0-1-1,0v-6c0-3,3-8,3-11c0-1-2-2-2-6h3
    C23.5,5.5,26.5,9.5,26.5,10.5z"/>
</svg>
"""

IMAGE[2] = """<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE svg PUBLIC "-//W3C//DTD SVG 1.1//EN" "http://www.w3.org/Graphics/SVG/1.1/DTD/svg11.dtd">
<svg version="1.1" id="Layer_1" xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" x="0px" y="0px"
     width="50px" height="50px" viewBox="0 0 50 50" enable-background="new 0 0 50 50" xml:space="preserve">
<path fill-rule="evenodd" clip-rule="evenodd" fill="#FFFFFF" d="M30.5,17.5c0,3-2,2-2,4c0,3,4,14,7,21c-1,0-3,1-5,1c1-1,2,0,2-3
    c0-2-4-7-6-10c-3,3-5,8-7,13c-1,0-3-1-4-1c3-3,7-14,7-18s-1-3-4-4c3-2,4-8,4-14h3C23.5,9.5,30.5,14.5,30.5,17.5z"/>
</svg>
"""

IMAGE[3] = """<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE svg PUBLIC "-//W3C//DTD SVG 1.1//EN" "http://www.w3.org/Graphics/SVG/1.1/DTD/svg11.dtd">
<svg version="1.1" id="Layer_1" xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" x="0px" y="0px"
     width="50px" height="50px" viewBox="0 0 50 50" enable-background="new 0 0 50 50" xml:space="preserve">
<path fill-rule="evenodd" clip-rule="evenodd" fill="#FFFFFF" d="M34.5,22.5c-1-1-2-4-5-6c-1,2,0,3,0,6c0,2-3,4-3,7c0,2,4,2,4,4
    c0,3-1,4-2,5c0-1,0-3-1-4c-1,3-2,7-3,10c-4-3,0-6,0-9s-3-11-4-17l-4,4c1-5,8.25-11.12,7.25-16.12c0.68,0.68,3.029,0,2.87,2.12
    C26.5,10.25,33.62,17.75,34.5,22.5z"/>
</svg>
"""

IMAGE[4] = """<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE svg PUBLIC "-//W3C//DTD SVG 1.1//EN" "http://www.w3.org/Graphics/SVG/1.1/DTD/svg11.dtd">
<svg version="1.1" id="Layer_1" xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" x="0px" y="0px"
     width="50px" height="50px" viewBox="0 0 50 50" enable-background="new 0 0 50 50" xml:space="preserve">
<path fill-rule="evenodd" clip-rule="evenodd" fill="#FFFFFF" d="M24.5,13.5c2,1,5,3,5,6c0,2-2,3-2,5c0,9,11,4,11,13c-1,0-3-2-4-3
    c-3-1-9,1-10-3c-2,3-5,7-7,11c-3,0-3-1-4-1c0-2,3-3,4-6s4-8,4-10c0-3-1-3-2-5c-1,0-2,1-3,2c0-1,2-3,2-4c1-2,3-5,2-8c0,0,1-1,4-2
    C25.5,9.5,25.5,11.5,24.5,13.5z"/>
</svg>
"""

IMAGE[5] = """<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE svg PUBLIC "-//W3C//DTD SVG 1.1//EN" "http://www.w3.org/Graphics/SVG/1.1/DTD/svg11.dtd">
<svg version="1.1" id="Layer_1" xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" x="0px" y="0px"
     width="50px" height="50px" viewBox="0 0 50 50" enable-background="new 0 0 50 50" xml:space="preserve">
<path fill-rule="evenodd" clip-rule="evenodd" fill="#FFFFFF" d="M22.5,10.5c3,2,7,5,7,7c0,3-4,8-4,10c0,3,1,3,1,5h5l2-2l2,2v4
    c-1,0-3-2-5-2c-3,0-5,1-8,1c-1,3-2,7-2,10h-5c1-1,3-3,3-4c1-5,1-11,1-18l-1-1c-1,1-1.75,2.88-2.75,2.88c0,0-0.25-0.63-0.25-1.63
    c4-4,2-8.25,2-13.25c0-1,0.25-2.5,0.38-5.38L22.5,5.5C23.12,6.5,22.5,8.5,22.5,10.5z"/>
<polygon fill-rule="evenodd" clip-rule="evenodd" fill="#333333" stroke="#333333" stroke-linecap="round" stroke-linejoin="round" points="
    25,20 25.25,16.75 26.5,17.88 "/>
</svg>
"""

IMAGE[6] = """<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE svg PUBLIC "-//W3C//DTD SVG 1.1//EN" "http://www.w3.org/Graphics/SVG/1.1/DTD/svg11.dtd">
<svg version="1.1" id="Layer_1" xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" x="0px" y="0px"
     width="50px" height="50px" viewBox="0 0 50 50" enable-background="new 0 0 50 50" xml:space="preserve">
<path fill-rule="evenodd" clip-rule="evenodd" fill="#FFFFFF" d="M20.5,7.5c1,1,1,3,1,4c10,4,8,6,8,14c0,2,6,9,10,13c-1,2-2,4-4,5
    c1.62-8.88-8.75-13.88-12-15c-1,1-1,0-1,2c0,3,2,5,3,7c-1,1-3,2-6,2c0-1,2-1,2-4c0-2-4-4-4-6c0-3,3-4,5-6c-3-8-8-2-11-6h6
    c0-1,1,0,1-3c0-2-1-1-2-2l1-5H20.5z"/>
</svg>
"""

IMAGE[7] = """<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE svg PUBLIC "-//W3C//DTD SVG 1.1//EN" "http://www.w3.org/Graphics/SVG/1.1/DTD/svg11.dtd">
<svg version="1.1" id="Layer_1" xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" x="0px" y="0px"
     width="50px" height="50px" viewBox="0 0 50 50" enable-background="new 0 0 50 50" xml:space="preserve">
<path fill-rule="evenodd" clip-rule="evenodd" fill="#FFFFFF" d="M20.5,12.5c0.67,0.4,0.4,1.9,1.75,2.25s1.05-0.38,1.5-0.37
    c4.971,0,10.95-0.88,11.75,7.12c-1-2-3-4-5-5l-4,1c1,2,4,4,5,7c1,1,1,4,1,6c3,3,8-1,11,6c-2.88-0.82-4.25-2.62-12.75-2.75
    c-1.561-0.02-2.34-1.561-3.75-1.87c-3.42-0.76-4.67-0.38-5.5-0.38c-3,0-8,7-11,7c-2,0-3-1-3-2c4,2,8-4,9-7c2-1,5-1,8-3c-2-4-6-5-8-3
    l-6-6l2-2c1,1,1,2,1,4c1,0,4.12,0.38,6.12-0.62L16.5,17.5v-5H20.5z"/>
</svg>
"""
