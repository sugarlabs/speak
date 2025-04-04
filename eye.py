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

        # Determine if we're the left or right eye
        is_left_eye = our_center_x < parent_center_x

        # Calculate relative cursor position from face center
        relative_x = (x - parent_center_x) / (parent_alloc.width / 2)
        
        # Adjust gaze based on cursor position
        if abs(relative_x) < 0.4:  # Cursor is between eyes
            target_x = cursor_x
        else:  # Cursor is outside central area
            if (is_left_eye and x < parent_center_x) or (not is_left_eye and x > parent_center_x):
                # Cursor is on our side - look directly
                target_x = cursor_x
            else:
                # Cursor is on opposite side - maintain parallel gaze
                gaze_offset = (abs(relative_x) - 0.4) * our_alloc.width * 0.3
                target_x = cursor_x + (-gaze_offset if is_left_eye else gaze_offset)

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
