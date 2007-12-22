#! /usr/bin/python

import pygtk
import gtk
import gtk.gdk
import gobject
import cairo
import math

class Eye(gtk.DrawingArea):
    def __init__(self):
        gtk.DrawingArea.__init__(self)
        self.connect("expose_event",self.expose)
        self.frame = 0
        # instead of listening for mouse move events we poll to see if the mouse has moved
        # this is so we can react to the mouse even when it isn't directly over this widget
        gobject.timeout_add(100, self._timeout_cb)
        self.mousePosition = self.get_mouse()

    def _timeout_cb(self):
        # only redraw if the mouse has moved
        newPosition = self.get_mouse()
        if newPosition != self.mousePosition:
            self.queue_draw()
            self.mousePosition = newPosition
        return True

    def get_mouse(self):
        display = gtk.gdk.display_get_default()
        screen, mouseX, mouseY, modifiers = display.get_pointer()
        return mouseX, mouseY

    def expose(self, widget, event):
        self.frame += 1
        bounds = self.get_allocation()
        
        mouseX, mouseY = self.mousePosition
        
        eyeSize = min(bounds.width, bounds.height)
        outlineWidth = eyeSize/20.0
        pupilSize = eyeSize/10.0
        pupilX = max(min(mouseX - bounds.x, bounds.width), 0)
        pupilY = max(min(mouseY - bounds.y, bounds.height), 0)
        dX = pupilX - bounds.width/2.
        dY = pupilY - bounds.height/2.
        distance = math.sqrt(dX*dX + dY*dY)
        limit = eyeSize/2 - outlineWidth*2 - pupilSize
        if distance > limit:
            pupilX = bounds.width/2 + dX*limit/distance
            pupilY = bounds.height/2 + dY*limit/distance

        self.context = widget.window.cairo_create()
        #self.context.set_antialias(cairo.ANTIALIAS_NONE)

        #set a clip region for the expose event. This reduces redrawing work (and time)
        self.context.rectangle(event.area.x, event.area.y, event.area.width, event.area.height)
        self.context.clip()

        # background
        self.context.set_source_rgb(.5,.5,.5)
        self.context.rectangle(0,0,bounds.width,bounds.height)
        self.context.fill()

        # eye ball
        self.context.arc(bounds.width/2,bounds.height/2, eyeSize/2-outlineWidth/2, 0,360)
        self.context.set_source_rgb(1,1,1)
        self.context.fill()

        # outline
        self.context.set_line_width(outlineWidth)
        self.context.arc(bounds.width/2,bounds.height/2, eyeSize/2-outlineWidth/2, 0,360)
        self.context.set_source_rgb(0,0,0)
        self.context.stroke()

        # pupil
        self.context.arc(pupilX,pupilY,pupilSize,0,360)
        self.context.set_source_rgb(0,0,0)
        self.context.fill()

        return True
