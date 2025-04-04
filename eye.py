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
        self._shared_target = None  # Store shared target coordinates

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
                # Get our allocation and parent allocation
                our_alloc = self.get_allocation()
                parent_alloc = parent.get_allocation()
                
                # Calculate center point between eyes
                center_x = parent_alloc.width / 2
                
                # Determine if cursor is closer to left or right eye
                is_left_side = (x < center_x)
                
                # Find the reference eye (the one cursor is closer to)
                ref_eye = None
                for eye in eyes:
                    eye_alloc = eye.get_allocation()
                    if (is_left_side and eye_alloc.x < center_x) or \
                       (not is_left_side and eye_alloc.x > center_x):
                        ref_eye = eye
                        break
                
                if ref_eye:
                    # Convert cursor position to reference eye's coordinates
                    ref_x, ref_y = ref_eye.translate_coordinates(
                        ref_eye.get_toplevel(), x, y)
                    # Share these coordinates with all eyes
                    for eye in eyes:
                        eye._shared_target = (ref_x, ref_y)
        
        self.queue_draw()

    def look_ahead(self):
        self.x = None
        self.y = None
        self._shared_target = None
        self.queue_draw()

    # Thanks to xeyes :)
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

        # Use shared target if available, otherwise use direct coordinates
        if self._shared_target:
            target_x, target_y = self._shared_target
            dx = target_x - EYE_X
            dy = target_y - EYE_Y
        else:
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
        
        # Return the pupil position relative to eye center
        return a.width // 2 + dx, a.height // 2 + dy

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
