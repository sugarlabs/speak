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
# Speak.activity is free software: you can redistribute it and/or modify
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

from gi.repository import Gtk
import math

class Eye(Gtk.DrawingArea):
    """Eye."""
    
    def __init__(self, fill_color):
        Gtk.DrawingArea.__init__(self)
        
        self.x, self.y = 0, 0
        self.fill_color = fill_color
        
        self.show_all()

    def look_at(self, x, y):
        """ Look. . ."""
        
        self.x = x
        self.y = y
        self.queue_draw()

    def look_ahead(self):
        """ Look. . ."""
        
        self.x = None
        self.y = None
        self.queue_draw()

    # Thanks to xeyes :)
    def computePupil(self):
        """pupil."""
        
        rect = self.get_allocation()

        if self.x is None or self.y is None:
            # look ahead, but not *directly* in the middle
            if rect.x + rect.width / 2 < rect.width / 2:
                cx = rect.width * 0.6
            else:
                cx = rect.width * 0.4
            return cx, rect.height * 0.6

        EYE_X, EYE_Y = self.translate_coordinates(
                self.get_toplevel(), rect.width / 2, rect.height / 2)
        EYE_HWIDTH = rect.width
        EYE_HHEIGHT = rect.height
        BALL_DIST = EYE_HWIDTH / 4

        dx = self.x - EYE_X
        dy = self.y - EYE_Y

        if dx or dy:
            angle = math.atan2(dy, dx)
            cosa = math.cos(angle)
            sina = math.sin(angle)
            h = math.hypot(EYE_HHEIGHT * cosa, EYE_HWIDTH * sina)
            x = (EYE_HWIDTH * EYE_HHEIGHT) * cosa / h
            y = (EYE_HWIDTH * EYE_HHEIGHT) * sina / h
            dist = BALL_DIST * math.hypot(x, y)

            if dist < math.hypot(dx, dy):
                dx = dist * cosa
                dy = dist * sina

        return rect.width / 2 + dx, rect.height / 2 + dy

    def do_draw(self, context):
        rect = self.get_allocation()
        
        eyeSize = min(rect.width, rect.height)
        
        outlineWidth = eyeSize / 20.0
        pupilSize = eyeSize / 10.0
        pupilX, pupilY = self.computePupil()
        dX = pupilX - rect.width / 2.
        dY = pupilY - rect.height / 2.
        distance = math.sqrt(dX * dX + dY * dY)
        limit = eyeSize / 2 - outlineWidth * 2 - pupilSize
        if distance > limit:
            pupilX = rect.width / 2 + dX * limit / distance
            pupilY = rect.height / 2 + dY * limit / distance
            
        context.set_source_rgba(*self.fill_color.get_rgba())
        context.rectangle(0, 0, rect.width, rect.height)
        context.fill()
        
        # eye ball
        context.set_source_rgb(1, 1, 1)
        context.arc(rect.width / 2,
            rect.height / 2,
            eyeSize / 2 - outlineWidth / 2,
            0, 360)
        context.fill()
        
        # outline
        context.set_source_rgb(0, 0, 0)
        context.set_line_width(outlineWidth)
        context.arc(rect.width / 2,
            rect.height / 2,
            eyeSize / 2 - outlineWidth / 2,
            0, 360)
        context.stroke()
        
        # pupil
        context.set_source_rgb(0, 0, 0)
        context.arc(pupilX, pupilY, pupilSize, 0, 360)
        context.fill()
        
        return True

class Glasses(Eye):
    def __init__(self, fill_color):
        Eye.__init__(self, fill_color)
        
        self.show_all()
        self.connect('draw', self.draw_glass)

    def draw_glass(self, widget, context):
        rect = widget.get_allocation()

        eyeSize = min(rect.width, rect.height)
        outlineWidth = eyeSize / 20.0
        pupilSize = eyeSize / 10.0
        pupilX, pupilY = self.computePupil()
        dX = pupilX - rect.width / 2.
        dY = pupilY - rect.height / 2.
        distance = math.sqrt(dX * dX + dY * dY)
        limit = eyeSize / 2 - outlineWidth * 2 - pupilSize
        if distance > limit:
            pupilX = rect.width / 2 + dX * limit / distance
            pupilY = rect.height / 2 + dY * limit / distance

        # background
        context.set_source_rgba(*self.fill_color.get_rgba())
        context.paint()

        def roundrect(x1, y1, x2, y2):
            context.move_to(x1, (y1 + y2) / 2.)
            context.curve_to(x1, y1, x1, y1, (x1 + x2) / 2., y1)
            context.curve_to(x2, y1, x2, y1, x2, (y1 + y2) / 2.)
            context.curve_to(x2, y2, x2, y2, (x1 + x2) / 2., y2)
            context.curve_to(x1, y2, x1, y2, x1, (y1 + y2) / 2.)

        # eye ball
        context.set_source_rgb(1, 1, 1)
        roundrect(outlineWidth,
                  outlineWidth,
                  rect.width - outlineWidth,
                  rect.height - outlineWidth)
        context.fill()

        # outline
        context.set_source_rgb(0, 0, 0)
        context.set_line_width(outlineWidth)
        roundrect(outlineWidth,
                  outlineWidth,
                  rect.width - outlineWidth,
                  rect.height - outlineWidth)
        #roundrect(0,0, rect.width,rect.height)
        context.stroke()

        # pupil
        context.arc(pupilX, pupilY, pupilSize, 0, 360)
        context.set_source_rgb(0, 0, 0)
        context.fill()

        return True
