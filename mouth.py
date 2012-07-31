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

# This code is a super-stripped down version of the waveform view from Measure

from gi.repository import Gtk
from gi.repository import Gdk
from struct import unpack
import numpy.core


class Mouth(Gtk.DrawingArea):
    
    def __init__(self, audioSource, fill_color):
        Gtk.DrawingArea.__init__(self)
        
        self.buffers = []
        self.buffer_size = 256
        self.main_buffers = []
        self.newest_buffer = []
        self.fill_color = fill_color
        
        self.show_all()
        
        audioSource.connect("new-buffer", self._new_buffer)

    def _new_buffer(self, obj, buf):
        if len(buf) < 28:
            self.newest_buffer = []
        else:
            self.newest_buffer = list(unpack(str(int(len(buf)) / 2) + 'h',
                                      buf))
            self.main_buffers += self.newest_buffer
            if(len(self.main_buffers) > self.buffer_size):
                del self.main_buffers[0:(len(self.main_buffers) - \
                        self.buffer_size)]

        self.queue_draw()
        return True

    def processBuffer(self):
        if len(self.main_buffers) == 0 or len(self.newest_buffer) == 0:
            self.volume = 0
        else:
            self.volume = numpy.core.max(self.main_buffers)  # -\
            # numpy.core.min(self.main_buffers)

    def do_draw(self, context):
        rect = self.get_allocation()
        
        self.processBuffer()
        
        # background
        context.set_source_rgba(*self.fill_color.get_rgba())
        context.paint()

        # Draw the mouth
        volume = self.volume / 30000.
        mouthH = volume * rect.height
        mouthW = volume ** 2 * (rect.width / 2.) + rect.width / 2.
        #        T
        #  L          R
        #        B
        Lx, Ly = rect.width / 2 - mouthW / 2, rect.height / 2
        Tx, Ty = rect.width / 2, rect.height / 2 - mouthH / 2
        Rx, Ry = rect.width / 2 + mouthW / 2, rect.height / 2
        Bx, By = rect.width / 2, rect.height / 2 + mouthH / 2
        context.set_line_width(min(rect.height / 10.0, 10))
        context.move_to(Lx, Ly)
        context.curve_to(Tx, Ty, Tx, Ty, Rx, Ry)
        context.curve_to(Bx, By, Bx, By, Lx, Ly)
        context.set_source_rgb(0, 0, 0)
        context.close_path()
        context.stroke()
        
        return True
