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
        # Add smooth movement
        self.current_x = 0
        self.current_y = 0
        self.movement_speed = 0.3

    def has_padding(self):
        return True

    def has_left_center_right(self):
        return False

    def look_at(self, x, y):
        parent = self.get_parent()
        if not parent:
            return

        # Get allocations
        our_alloc = self.get_allocation()
        parent_alloc = parent.get_allocation()

        # Convert cursor to our coordinate space
        cursor_x, cursor_y = self.translate_coordinates(
            self.get_toplevel(), x, y)

        # Calculate center points
        parent_center_x = parent_alloc.width / 2
        our_center_x = our_alloc.x + our_alloc.width / 2
        eye_width = our_alloc.width

        # Determine if we're the left or right eye
        is_left_eye = our_center_x < parent_center_x

        # Check if cursor is inside eye circumference
        eye_radius = min(our_alloc.width, our_alloc.height) / 2
        dx = x - (our_alloc.x + our_alloc.width/2)
        dy = y - (our_alloc.y + our_alloc.height/2)
        cursor_in_eye = (dx*dx + dy*dy) < (eye_radius * eye_radius)

        # Calculate relative cursor position from face center
        relative_x = (x - parent_center_x) / (parent_alloc.width / 2)
        
        # Calculate convergence factor (0 to 1)
        convergence = max(0, 1 - abs(relative_x))
        
        if cursor_in_eye:
            # If cursor is in this eye, look directly at it
            target_x = cursor_x
        elif abs(relative_x) < 0.4:
            # Cursor is between eyes - converge both eyes
            target_x = cursor_x
        else:
            # Cursor is outside - maintain parallel gaze with slight convergence
            base_offset = eye_width * 0.2  # Base parallel offset
            convergence_factor = 0.7  # How much to maintain parallel gaze vs converge
            
            if is_left_eye:
                if x < parent_center_x:
                    # Left eye looking left - slight convergence
                    target_x = cursor_x + (base_offset * convergence_factor)
                else:
                    # Left eye looking right - maintain more parallel
                    target_x = cursor_x - (base_offset * (1 - convergence_factor))
            else:  # Right eye
                if x > parent_center_x:
                    # Right eye looking right - slight convergence
                    target_x = cursor_x - (base_offset * convergence_factor)
                else:
                    # Right eye looking left - maintain more parallel
                    target_x = cursor_x + (base_offset * (1 - convergence_factor))

        self.x = target_x
        self.y = cursor_y
        self.queue_draw()

    def look_ahead(self):
        self.x = None
        self.y = None
        self.current_x = self.get_allocation().width / 2
        self.current_y = self.get_allocation().height / 2
        self.queue_draw()

    def computePupil(self):
        a = self.get_allocation()

        if self.x is None or self.y is None:
            # look ahead, but not *directly* in the middle
            pw = self.get_parent().get_allocation().width
            if a.x + a.width // 2 < pw // 2:
                cx = a.width * 0.6
            else:
                cx = a.width * 0.4
            return cx, a.height * 0.6

        # Get eye center
        center_x = a.width / 2
        center_y = a.height / 2

        # Calculate movement vector
        dx = self.x - center_x
        dy = self.y - center_y

        # Limit maximum movement
        max_radius = min(a.width, a.height) / 4
        distance = math.hypot(dx, dy)
        
        if distance > max_radius:
            scale = max_radius / distance
            dx *= scale
            dy *= scale

        # Calculate target position
        target_x = center_x + dx
        target_y = center_y + dy

        # Apply smooth movement
        self.current_x += (target_x - self.current_x) * self.movement_speed
        self.current_y += (target_y - self.current_y) * self.movement_speed

        return self.current_x, self.current_y

    def draw(self, widget, cr):
        bounds = self.get_allocation()

        eyeSize = min(bounds.width, bounds.height)
        outlineWidth = eyeSize / 20.0
        pupilSize = eyeSize / 10.0
        pupilX, pupilY = self.computePupil()
        dX = pupilX - bounds.width / 2.
        dY = pupilY - bounds.height / 2.
        distance = math.sqrt(dX * dX + dY * dY)
        limit = eyeSize // 2 - outlineWidth * 2 - pupilSize
        if distance > limit:
            pupilX = bounds.width // 2 + dX * limit // distance
            pupilY = bounds.height // 2 + dY * limit // distance

        # background
        cr.set_source_rgba(*self.fill_color.get_rgba())
        cr.rectangle(0, 0, bounds.width, bounds.height)
        cr.fill()

        # eye ball
        cr.arc(bounds.width // 2, bounds.height // 2,
               eyeSize // 2 - outlineWidth // 2, 0, 2 * math.pi)
        cr.set_source_rgb(1, 1, 1)
        cr.fill()

        # outline
        cr.set_line_width(outlineWidth)
        cr.arc(bounds.width // 2, bounds.height // 2,
               eyeSize // 2 - outlineWidth // 2, 0, 2 * math.pi)
        cr.set_source_rgb(0, 0, 0)
        cr.stroke()

        # pupil
        cr.arc(pupilX, pupilY, pupilSize, 0, 2 * math.pi)
        cr.set_source_rgb(0, 0, 0)
        cr.fill()

        return True
