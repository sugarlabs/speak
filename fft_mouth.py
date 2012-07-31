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

# This code is a stripped down version of the fft view from Measure

from mouth import *

# Newer OLPC builds (and Fedora) have numpy instead of numeric:
try:
    from numpy.oldnumeric import ceil
    from numpy.fft import *
except:
    from Numeric import ceil
    from FFT import *


class FFTMouth(Mouth):
    def __init__(self, audioSource, fill_color):

        Mouth.__init__(self, audioSource, fill_color)

        self.peaks = []

        self.y_mag = 1.7
        self.freq_range = 70
        self.draw_interval = 1
        self.num_of_points = 105

        self.stop = False

        #constant to multiply with self.param2 while scaling values
        self.y_mag_bias_multiplier = 1

        self.fftx = []

        self.scaleX = "10"
        self.scaleY = "10"

    def processBuffer(self, rect):
        self.param1 = rect.height / 65536.0
        self.param2 = rect.height / 2.0

        if(self.stop == False):

            Fs = 48000
            nfft = 65536
            self.newest_buffer = self.newest_buffer[0:256]
            self.fftx = fft(self.newest_buffer, 256, -1)

            self.fftx = self.fftx[0:self.freq_range * 2]
            self.draw_interval = rect.width / (self.freq_range * 2.)

            NumUniquePts = ceil((nfft + 1) / 2)
            self.buffers = abs(self.fftx) * 0.02
            self.y_mag_bias_multiplier = 0.1
            self.scaleX = "hz"
            self.scaleY = ""

        if(len(self.buffers) == 0):
            return False

        # Scaling the values
        val = []
        for i in self.buffers:
            temp_val_float = float(self.param1 * i * self.y_mag) +\
                             self.y_mag_bias_multiplier * self.param2

            if(temp_val_float >= rect.height):
                temp_val_float = rect.height - 25
            if(temp_val_float <= 0):
                temp_val_float = 25
            val.append(temp_val_float)

        self.peaks = val

    def do_draw(self, context):
        rect = self.get_allocation()
        
        self.processBuffer(rect)
        
        # background
        context.set_source_rgba(*self.fill_color.get_rgba())
        context.paint()
        
        # Draw the waveform
        context.set_line_width(min(rect.height / 10.0, 10))
        context.set_source_rgb(0, 0, 0)
        count = 0
        for peak in self.peaks:
            context.line_to(rect.width / 2 + count,
                                 rect.height / 2 - peak)
            count += self.draw_interval
        context.stroke()
        count = 0
        for peak in self.peaks:
            context.line_to(rect.width / 2 - count,
                rect.height / 2 - peak)
            count += self.draw_interval
        context.stroke()
        
        return True
