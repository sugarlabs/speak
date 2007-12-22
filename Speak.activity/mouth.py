#! /usr/bin/python

import pygst
pygst.require("0.10")
import pygtk
import gtk
import cairo
import gobject
from time import *
from struct import *
import pango
import os
import audioop
from Numeric import *
from FFT import *

class Mouth(gtk.DrawingArea):
    def __init__(self, audioSource):
        
        gtk.DrawingArea.__init__(self)
        self.connect("expose_event",self.expose)
        self.buffers = []
        self.str_buffer=''
        self.integer_buffer=[]  

        audioSource.connect("new-buffer", self._new_buffer)

        self.peaks = []
        self.main_buffers = []      
    
        self.y_mag = 0.7
        self.freq_range=70
        self.draw_interval = 1
        self.num_of_points = 105
        
        self.details_show = False
        self.logging_status=False
        self.f=None

        self.stop=False

        self.fft_show = False
        self.fftx = []

        self.y_mag_bias_multiplier = 1  #constant to multiply with self.param2 while scaling values 
        
        self.scaleX = "10"
        self.scaleY = "10"

            
    def _new_buffer(self, obj, buf, status, f):
        self.str_buffer = buf
        self.integer_buffer = list(unpack( str(int(len(buf))/2)+'h' , buf))     
        if(len(self.main_buffers)>6301):
            del self.main_buffers[0:(len(self.main_buffers)-6301)]
        self.main_buffers += self.integer_buffer
        self.logging_status=status
        self.f=f
        return True


    def processBuffer(self, bounds):
        self.param1 = bounds.height/65536.0
        self.param2 = bounds.height/2.0 

        if(self.stop==False):       
            
            if(self.fft_show==False):               
                
                ######################filtering####################
                weights = [1,2,3,4,3,2,1] 
                weights_sum = 16.0
                
                for i in range(3,len(self.integer_buffer)-3):
                    self.integer_buffer[i] = (self.integer_buffer[(i-3)]+2*self.integer_buffer[(i-2)] + 3*self.integer_buffer[(i-1)] + 4*self.integer_buffer[(i)]+3*self.integer_buffer[(i+1)] + 2*self.integer_buffer[(i+2)]  + self.integer_buffer[(i+3)]) / weights_sum                  
                ###################################################
            
                self.y_mag_bias_multiplier=1                    
                self.draw_interval=10                   
                
                #100hz
                if(self.freq_range==30):
                    self.spacing = 60
                    self.num_of_points=6300
                        
                #1khz
                if(self.freq_range==50):
                    self.spacing = 6
                    self.num_of_points=630
                        
                #4khz
                if(self.freq_range==70):
                    self.spacing = 1
                    self.num_of_points = 105
                
                self.scaleX = str(self.spacing*.104) + " msec"  #.104 = 5/48; 5 points per division and 48 khz sampling             
                
                if(len(self.main_buffers)>=self.num_of_points):
                    del self.main_buffers[0:len(self.main_buffers)-(self.num_of_points+1)]
                    self.buffers=[]
                    i=0
                    while i<self.num_of_points:
                        self.buffers.append(self.main_buffers[i])                       
                        i+=self.spacing
            
                self.scaleY=" "
            
            else:
                ###############fft################      
                Fs = 48000
                nfft= 65536
                self.integer_buffer=self.integer_buffer[0:256]
                self.fftx = fft(self.integer_buffer, 256,-1)
                
                self.fftx=self.fftx[0:self.freq_range*2]
                self.draw_interval=bounds.width/(self.freq_range*2)
                
                NumUniquePts = ceil((nfft+1)/2)
                self.buffers=abs(self.fftx)*0.02
                self.y_mag_bias_multiplier=0.1
                self.scaleX = "hz"
                self.scaleY = ""
                ##################################
                    
        if(len(self.buffers)==0):
            return False
        
        ###############Scaling the values################       
        val = []
        for i in self.buffers:
            temp_val_float = float(self.param1*i*self.y_mag) + self.y_mag_bias_multiplier * self.param2
            
            if(temp_val_float >= bounds.height):
                temp_val_float = bounds.height-25
            if(temp_val_float <= 0):
                temp_val_float = 25
            val.append( temp_val_float )
        
        self.peaks = val
        #################################################
            
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
        self.context.set_source_rgb(.5,.5,.5)
        self.context.rectangle(0,0, bounds.width,bounds.height)     
        self.context.fill()

        # Draw the waveform
        self.context.set_line_width(10.0)        
        count = 0
        for peak in self.peaks:
            self.context.line_to(count,bounds.height - peak)
            count += self.draw_interval
        self.context.set_source_rgb(0,0,0)
        self.context.stroke()

        return True
