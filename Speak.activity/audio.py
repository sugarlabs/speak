import pygst
pygst.require("0.10")
import gst
import pygtk
import gtk, gobject
import signal, os

import time

import dbus

import audioop

from struct import *



class AudioGrab(gobject.GObject):
    __gsignals__ = {
        'new-buffer': (gobject.SIGNAL_RUN_FIRST, None, [gobject.TYPE_PYOBJECT, gobject.TYPE_BOOLEAN, gobject.TYPE_PYOBJECT])
    }

    def __init__(self, datastore, _jobject):
        gobject.GObject.__init__(self)
        
        self.wave_copy= None
        self.electrical_ui_copy= None

        self.datastore = datastore
        self._jobject = _jobject
        
        self.pipeline = None
        self.fakesink = None

        self.logging_status = False
        self.count1 = 48000/9600
        self.final_count = 0

        self.count_temp = 0
        self.entry_count = 0
        
        self.draw_graph_status = False
        self.f = None
        
        self.temp_buffer = []
        self.snapshot_buffer = []

    def playfile(self, filename):
        p = 'filesrc name=file-source ! decodebin ! tee name=tee tee.! audioconvert ! alsasink tee.! queue ! audioconvert name=conv'
        self.pipeline = gst.parse_launch(p)
        
        self.fakesink = gst.element_factory_make("fakesink", "fakesink")
        self.fakesink.connect("handoff",self.on_buffer)
        self.fakesink.set_property("signal-handoffs",True)
        self.pipeline.add(self.fakesink)

        conv = self.pipeline.get_by_name("conv")
        gst.element_link_many(conv, self.fakesink)
        
        self.pipeline.get_by_name("file-source").set_property('location', filename)
        self.pipeline.set_state(gst.STATE_PLAYING)
        
    def disable_handoff_signal(self):
        self.fakesink.set_property("signal-handoffs",False)
    
    def enable_handoff_signal(self):
        self.fakesink.set_property("signal-handoffs",True)
    
    def on_quit(self):
        self.fakesink.set_property("signal-handoffs",False)     
        self.pipeline.set_state(gst.STATE_NULL)

    def _new_buffer(self, buf):
        # on the main thread

        if(self.logging_status == True):
            
            if(self.final_count==777700):   #777700 is a special value for indicating 'Snapshot'
                #buffer_temp = unpack( str(int(len(self.temp_buffer))/2)+'h' , self.temp_buffer)                
                for val in self.snapshot_buffer:                
                    self.f.write(str(val)+'\n') #Write the latest buffer
                self.f.write("stop")                
                self.f.close()
                self.datastore.write(self._jobject)
                self.logging_status=False
            
            else:
                self.count_temp+=1
    
                if(self.count_temp==self.final_count):
                    self.count_temp=0
                    write_buffer = unpack( str(int(len(buf))/2)+'h' , buf)
                    self.f.write(str(write_buffer[int(len(buf)/4.0)])+'\n') #Writing the middle value of the buffer available at each logging time
                    self.entry_count+=1
                
                        
        self.emit("new-buffer", buf, self.draw_graph_status, self.f)
        return False


    def on_buffer(self,element,buffer,pad):     
        # could be in a different thread
        #print len(str(buffer)) 
        gobject.timeout_add(30, self._new_buffer, str(buffer))      
        #gobject.idle_add(self._new_buffer, str(buffer))
        return True


    def set_logging_status(self, status, f, multiplier):
        self.logging_status = status

        if(status==True):
            self.f = f
            self.final_count = (multiplier*(48000/960)*2)
            self.count_temp=0
            self.entry_count=0      
                    
        if(status==False):
            self.f.write("stop")            
            self.f.close()
            self.datastore.write(self._jobject)
            self.logging_status=False

    
    def start_drawing_graph(self, status, f):
        self.draw_graph_status = status
        if(self.draw_graph_status==True):       
            self.f = f
        return

    def snapshot(self):
        self.snapshot_buffer = self.wave_copy.buffers
        return

    def set_wave_copy(self, wave):
        self.wave_copy = wave       
        return

    def set_reference_electrical(self,electrical_ui):
        self.electrical_ui_copy=electrical_ui

    def stop_sound_device(self):
        self.pipeline.set_state(gst.STATE_NULL)

    def restart_sound_device(self):
        self.pipeline.set_state(gst.STATE_PLAYING)

