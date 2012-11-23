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

from eye import *


class Glasses(Eye):
    def __init__(self, fill_color):
        Eye.__init__(self, fill_color)

    def expose(self, widget, event):
        bounds = self.get_allocation()

        eyeSize = min(bounds.width, bounds.height)
        outlineWidth = eyeSize / 20.0
        pupilSize = eyeSize / 10.0
        pupilX, pupilY = self.computePupil()
        dX = pupilX - bounds.width / 2.
        dY = pupilY - bounds.height / 2.
        distance = math.sqrt(dX * dX + dY * dY)
        limit = eyeSize / 2 - outlineWidth * 2 - pupilSize
        if distance > limit:
            pupilX = bounds.width / 2 + dX * limit / distance
            pupilY = bounds.height / 2 + dY * limit / distance

        self.context = widget.window.cairo_create()
        #self.context.set_antialias(cairo.ANTIALIAS_NONE)

        #set a clip region for the expose event. This reduces redrawing work (and time)
        self.context.rectangle(event.area.x, event.area.y, event.area.width, event.area.height)
        self.context.clip()

        # background
        self.context.set_source_rgba(*self.fill_color.get_rgba())
        self.context.rectangle(0, 0, bounds.width, bounds.height)
        self.context.fill()

        def roundrect(x1, y1, x2, y2):
            self.context.move_to(x1, (y1 + y2) / 2.)
            self.context.curve_to(x1, y1, x1, y1, (x1 + x2) / 2., y1)
            self.context.curve_to(x2, y1, x2, y1, x2, (y1 + y2) / 2.)
            self.context.curve_to(x2, y2, x2, y2, (x1 + x2) / 2., y2)
            self.context.curve_to(x1, y2, x1, y2, x1, (y1 + y2) / 2.)

        # eye ball
        roundrect(outlineWidth, outlineWidth, bounds.width - outlineWidth, bounds.height - outlineWidth)
        self.context.set_source_rgb(1, 1, 1)
        self.context.fill()

        # outline
        self.context.set_line_width(outlineWidth)
        roundrect(outlineWidth, outlineWidth, bounds.width - outlineWidth, bounds.height - outlineWidth)
        #roundrect(0,0, bounds.width,bounds.height)
        self.context.set_source_rgb(0, 0, 0)
        self.context.stroke()

        # pupil
        self.context.arc(pupilX, pupilY, pupilSize, 0, 2*math.pi)
        self.context.set_source_rgb(0, 0, 0)
        self.context.fill()

        return True
