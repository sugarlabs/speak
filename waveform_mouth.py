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
        rect = self.get_allocation()
        self.param1 = rect.height / 65536.0
        self.param2 = rect.height / 2.0
        
        # background
        context.set_source_rgba(*self.fill_color.get_rgba())
        context.paint()
        
        # Draw the waveform
        context.set_line_width(min(rect.height / 10.0, 10))
        count = 0
        buflen = float(len(self.main_buffers))
        for value in self.main_buffers:
            peak = float(self.param1 * value * self.y_mag) +\
                   self.y_mag_bias_multiplier * self.param2
                
            if peak >= rect.height:
                peak = rect.height
            if peak <= 0:
                peak = 0
                
            x = count / buflen * rect.width
            context.line_to(x, rect.height - peak)
            
            count += 1
        context.set_source_rgb(0, 0, 0)
        context.stroke()
        
        return True
