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
from math import ceil
from numpy.fft import *


class FFTMouth(Mouth):
    def __init__(self, audioSource, fill_color):

        Mouth.__init__(self, audioSource, fill_color)
        
        self.peaks = []

        self.y_mag = 1.7
        self.freq_range=70
        self.draw_interval = 1
        self.num_of_points = 105

        self.stop=False

        self.y_mag_bias_multiplier = 1  #constant to multiply with self.param2 while scaling values

        self.fftx = []

        self.scaleX = "10"
        self.scaleY = "10"


    def processBuffer(self, bounds):
        self.param1 = bounds.height/65536.0
        self.param2 = bounds.height/2.0

        if(self.stop==False):

            Fs = 48000
            nfft= 65536
            self.newest_buffer=self.newest_buffer[0:256]
            self.fftx = fft(self.newest_buffer, 256,-1)

            self.fftx=self.fftx[0:self.freq_range*2]
            self.draw_interval=bounds.width/(self.freq_range*2.)

            NumUniquePts = ceil((nfft+1)/2)
            self.buffers=abs(self.fftx)*0.02
            self.y_mag_bias_multiplier=0.1
            self.scaleX = "hz"
            self.scaleY = ""

        if(len(self.buffers)==0):
            return False

        # Scaling the values
        val = []
        for i in self.buffers:
            temp_val_float = float(self.param1*i*self.y_mag) + self.y_mag_bias_multiplier * self.param2

            if(temp_val_float >= bounds.height):
                temp_val_float = bounds.height-25
            if(temp_val_float <= 0):
                temp_val_float = 25
            val.append( temp_val_float )

        self.peaks = val

    def expose(self, widget, event):
        """This function is the "expose" event handler and does all the drawing."""

        bounds = self.get_allocation()

        self.processBuffer(bounds)

        #Create context, disable antialiasing
        self.context = widget.window.cairo_create()
        self.context.set_antialias(cairo.ANTIALIAS_NONE)

        #set a clip region for the expose event. This reduces redrawing work (and time)
        self.context.rectangle(event.area.x, event.area.y,event.area.width, event.area.height)
        self.context.clip()

        # background
        self.context.set_source_rgba(*self.fill_color.get_rgba())
        self.context.rectangle(0,0, bounds.width,bounds.height)
        self.context.fill()

        # Draw the waveform
        self.context.set_line_width(min(bounds.height/10.0, 10))
        self.context.set_source_rgb(0,0,0)
        count = 0
        for peak in self.peaks:
            self.context.line_to(bounds.width/2 + count,bounds.height/2 - peak)
            count += self.draw_interval
        self.context.stroke()
        count = 0
        for peak in self.peaks:
            self.context.line_to(bounds.width/2 - count,bounds.height/2 - peak)
            count += self.draw_interval
        self.context.stroke()

        return True
