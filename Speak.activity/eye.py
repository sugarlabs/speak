# Speak.activity
# A simple front end to the espeak text-to-speech engine on the XO laptop
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
#     Foobar is distributed in the hope that it will be useful,
#     but WITHOUT ANY WARRANTY; without even the implied warranty of
#     MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#     GNU General Public License for more details.
# 
#     You should have received a copy of the GNU General Public License
#     along with Foobar.  If not, see <http://www.gnu.org/licenses/>.

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
        self.blink = False
        
        # listen for clicks
        self.add_events(gtk.gdk.BUTTON_PRESS_MASK)
        self.add_events(gtk.gdk.BUTTON_RELEASE_MASK)
        self.connect("button_press_event", self._mouse_pressed_cb)
        self.connect("button_release_event", self._mouse_released_cb)
        
        # Instead of listening for mouse move events we could poll to see if the mouse has moved
        # would let us react to the mouse even when it isn't directly over this widget.
        # Unfortunately that would cause a lot of CPU usage.  So instead we rely on our parent to
        # tell us to redraw when the mouse has moved.  We still need to call add_events so that
        # our parent will get mouse motion events, but we don't connect the callback for them ourselves.
        self.add_events(gtk.gdk.POINTER_MOTION_MASK)
        # self.connect("motion_notify_event", self._mouse_moved_cb)

    def _mouse_moved_cb(self, widget, event):
        self.queue_draw()

    def _mouse_pressed_cb(self, widget, event):
        self.blink = True
        self.queue_draw()

    def _mouse_released_cb(self, widget, event):
        self.blink = False
        self.queue_draw()
        
    def get_mouse(self):
        display = gtk.gdk.display_get_default()
        screen, mouseX, mouseY, modifiers = display.get_pointer()
        return mouseX, mouseY

    def expose(self, widget, event):
        self.frame += 1
        bounds = self.get_allocation()
        
        mouseX, mouseY = self.get_mouse()
        
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

        self.blink = False

        return True
