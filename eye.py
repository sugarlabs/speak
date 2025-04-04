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

import math

from gi.repository import Gtk


class Eye(Gtk.DrawingArea):
    def __init__(self, fill_color):
        Gtk.DrawingArea.__init__(self)
        self.connect("draw", self.draw)
        self.x, self.y = 0, 0
        self.fill_color = fill_color
        # Add smoothing variables
        self.current_pupil_x = 0
        self.current_pupil_y = 0
        self.smoothing_factor = 0.5  # Lower value = more smoothing

    def has_padding(self):
        return True

    def has_left_center_right(self):
        return False

    def look_at(self, x, y):
        self.x = x
        self.y = y
        self.queue_draw()

    def look_ahead(self):
        self.x = None
        self.y = None
        self.queue_draw()

    def computePupil(self):
        a = self.get_allocation()
        
        # Center of the eye
        center_x = a.width / 2
        center_y = a.height / 2
        
        if self.x is None or self.y is None:
            # Default forward look position
            pw = self.get_parent().get_allocation().width
            if a.x + a.width // 2 < pw // 2:
                return center_x * 1.2, center_y * 1.2
            else:
                return center_x * 0.8, center_y * 1.2

        # Get absolute eye position
        EYE_X, EYE_Y = self.translate_coordinates(self.get_toplevel(), int(center_x), int(center_y))
        
        # Calculate direction vector from eye center to cursor
        dx = self.x - EYE_X
        dy = self.y - EYE_Y
        
        # Calculate the angle and distance
        angle = math.atan2(dy, dx)
        distance = math.hypot(dx, dy)
        
        # Calculate the eye's usable radius (accounting for pupil size and outline)
        eye_size = min(a.width, a.height)
        outline_width = eye_size / 20.0
        pupil_size = eye_size / 10.0
        max_travel_radius = (eye_size / 2) - outline_width - pupil_size
        
        # Calculate target position with proper boundary constraints
        if distance == 0:
            # If cursor is exactly at center, keep pupil at center
            target_x = center_x
            target_y = center_y
        else:
            # Convert cursor position to eye-relative coordinates
            relative_x = dx * (a.width / eye_size)
            relative_y = dy * (a.height / eye_size)
            
            # Calculate the target position
            target_x = center_x + relative_x
            target_y = center_y + relative_y
            
            # Check if target position exceeds maximum travel radius
            dx_target = target_x - center_x
            dy_target = target_y - center_y
            dist_target = math.hypot(dx_target, dy_target)
            
            if dist_target > max_travel_radius:
                # If beyond max radius, scale back to the boundary
                scale = max_travel_radius / dist_target
                target_x = center_x + dx_target * scale
                target_y = center_y + dy_target * scale
        
        # Apply smoothing
        self.current_pupil_x += (target_x - self.current_pupil_x) * self.smoothing_factor
        self.current_pupil_y += (target_y - self.current_pupil_y) * self.smoothing_factor
        
        return self.current_pupil_x, self.current_pupil_y

    def draw(self, widget, cr):
        bounds = self.get_allocation()
        eyeSize = min(bounds.width, bounds.height)
        outlineWidth = eyeSize / 20.0
        pupilSize = eyeSize / 10.0
        pupilX, pupilY = self.computePupil()

        # background
        cr.set_source_rgba(*self.fill_color.get_rgba())
        cr.rectangle(0, 0, bounds.width, bounds.height)
        cr.fill()

        # eye ball
        cr.arc(bounds.width / 2, bounds.height / 2,
               eyeSize / 2 - outlineWidth / 2, 0, 2 * math.pi)
        cr.set_source_rgb(1, 1, 1)
        cr.fill()

        # outline
        cr.set_line_width(outlineWidth)
        cr.arc(bounds.width / 2, bounds.height / 2,
               eyeSize / 2 - outlineWidth / 2, 0, 2 * math.pi)
        cr.set_source_rgb(0, 0, 0)
        cr.stroke()

        # pupil
        cr.arc(pupilX, pupilY, pupilSize, 0, 2 * math.pi)
        cr.set_source_rgb(0, 0, 0)
        cr.fill()

        return True
