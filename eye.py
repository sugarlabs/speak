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
        self.current_x = 0  # Current pupil position for smooth movement
        self.current_y = 0
        self.movement_speed = 0.2  # Adjust speed of eye movement (0-1)

    def has_padding(self):
        return True

    def has_left_center_right(self):
        return False

    def look_at(self, x, y):
        self.x = x
        self.y = y
        
        # Get parent widget (face container)
        parent = self.get_parent()
        if parent:
            # Find all eye widgets in the parent
            eyes = [w for w in parent.get_children() if isinstance(w, Eye)]
            if len(eyes) > 1:
                # Get parent allocation for calculations
                parent_alloc = parent.get_allocation()
                center_x = parent_alloc.width / 2
                
                # Get our allocation
                our_alloc = self.get_allocation()
                our_center_x = our_alloc.x + our_alloc.width / 2
                
                # Determine if we're the left or right eye
                is_left_eye = our_center_x < center_x
                
                # Calculate convergence based on cursor position
                cursor_center_ratio = (x - center_x) / (parent_alloc.width / 2)
                # Adjust convergence strength when cursor is between eyes
                convergence = abs(cursor_center_ratio) < 0.5
                
                if convergence:
                    # Both eyes should look towards the cursor position
                    target_x = x
                    target_y = y
                else:
                    # When cursor is outside center area, use parallel gaze
                    if is_left_eye:
                        # Left eye
                        target_x = x + (our_alloc.width / 2 if x < center_x else 0)
                    else:
                        # Right eye
                        target_x = x - (our_alloc.width / 2 if x > center_x else 0)
                    target_y = y
                
                # Convert target position to eye's coordinates
                target_x, target_y = self.translate_coordinates(
                    self.get_toplevel(), target_x, target_y)
                
                # Store target for smooth movement
                self.x = target_x
                self.y = target_y
        
        self.queue_draw()

    def look_ahead(self):
        self.x = None
        self.y = None
        self.current_x = 0
        self.current_y = 0
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

        # Get the eye's center position in window coordinates
        EYE_X, EYE_Y = self.translate_coordinates(
            self.get_toplevel(), a.width // 2, a.height // 2)

        # Calculate target movement
        dx = self.x - EYE_X
        dy = self.y - EYE_Y

        # Calculate the angle and distance
        angle = math.atan2(dy, dx)
        distance = math.hypot(dx, dy)
        
        # Calculate maximum allowed movement radius based on eye size
        max_radius = min(a.width, a.height) / 4
        
        # If the target is too far, limit the movement
        if distance > max_radius:
            dx = max_radius * math.cos(angle)
            dy = max_radius * math.sin(angle)
        
        # Smooth movement interpolation
        target_x = a.width // 2 + dx
        target_y = a.height // 2 + dy
        
        # Update current position with smooth interpolation
        self.current_x += (target_x - self.current_x) * self.movement_speed
        self.current_y += (target_y - self.current_y) * self.movement_speed
        
        # Return interpolated position
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
