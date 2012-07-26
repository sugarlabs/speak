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

# This code is a stripped down version of the waveform view from Measure

from mouth import *


class WaveformMouth(Mouth):
    def __init__(self, audioSource, fill_color):

        Mouth.__init__(self, audioSource, fill_color)

        self.buffer_size = 100
        self.peaks = []

        self.stop = False

        self.y_mag_bias_multiplier = 1
        self.y_mag = 0.7

    def do_draw(self, context):
        """This function is the "expose"
        event handler and does all the drawing."""

        bounds = self.get_allocation()
        self.param1 = bounds.height / 65536.0
        self.param2 = bounds.height / 2.0

        #Create context, disable antialiasing
        self.context = context
        #self.context.set_antialias(cairo.ANTIALIAS_NONE)

        #set a clip region for the expose event.
        #This reduces redrawing work (and time)
        self.context.rectangle(bounds.x,
                               bounds.y,
                               bounds.width,
                               bounds.height)
        self.context.clip()

        # background
        self.context.set_source_rgba(*self.fill_color.get_rgba())
        self.context.rectangle(0, 0, bounds.width, bounds.height)
        self.context.fill()

        # Draw the waveform
        self.context.set_line_width(min(bounds.height / 10.0, 10))
        count = 0
        buflen = float(len(self.main_buffers))
        for value in self.main_buffers:
            peak = float(self.param1 * value * self.y_mag) +\
                   self.y_mag_bias_multiplier * self.param2

            if peak >= bounds.height:
                peak = bounds.height
            if peak <= 0:
                peak = 0

            x = count / buflen * bounds.width
            self.context.line_to(x, bounds.height - peak)

            count += 1
        self.context.set_source_rgb(0, 0, 0)
        self.context.stroke()

        return True
