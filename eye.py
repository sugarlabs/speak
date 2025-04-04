class Eye(Gtk.DrawingArea):
    def __init__(self, fill_color):
        Gtk.DrawingArea.__init__(self)
        self.connect("draw", self.draw)
        self.x, self.y = None, None  # Current look-at position
        self.fill_color = fill_color

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

    def compute_pupil_position(self):
        allocation = self.get_allocation()
        eye_center_x = allocation.width // 2
        eye_center_y = allocation.height // 2
        
        # If not looking at anything specific, look slightly off-center
        if self.x is None or self.y is None:
            # Look ahead but slightly inward (toward nose)
            if allocation.x + allocation.width // 2 < self.get_parent().get_allocation().width // 2:
                return (allocation.width * 0.6, allocation.height * 0.5)
            else:
                return (allocation.width * 0.4, allocation.height * 0.5)
        
        # Convert cursor position to eye coordinates
        cursor_x, cursor_y = self.translate_coordinates(
            self.get_toplevel(), self.x, self.y)
        if cursor_x is None or cursor_y is None:
            return (eye_center_x, eye_center_y)
        
        # Calculate vector from eye center to cursor
        dx = cursor_x - eye_center_x
        dy = cursor_y - eye_center_y
        
        # Calculate distance from center
        distance = math.hypot(dx, dy)
        
        # Eye parameters
        eye_radius = min(allocation.width, allocation.height) // 2
        pupil_radius = eye_radius // 5
        max_pupil_distance = eye_radius - pupil_radius * 1.5
        
        # If cursor is inside eye boundary, look directly at it
        if distance <= max_pupil_distance:
            return (cursor_x, cursor_y)
        
        # Otherwise, look in that direction but constrained to eye boundary
        scale = max_pupil_distance / distance
        pupil_x = eye_center_x + dx * scale
        pupil_y = eye_center_y + dy * scale
        
        return (pupil_x, pupil_y)

    def draw(self, widget, cr):
        bounds = self.get_allocation()
        eye_size = min(bounds.width, bounds.height)
        outline_width = eye_size / 20.0
        pupil_size = eye_size / 10.0
        
        # Get pupil position
        pupil_x, pupil_y = self.compute_pupil_position()

        # Draw background
        cr.set_source_rgba(*self.fill_color.get_rgba())
        cr.rectangle(0, 0, bounds.width, bounds.height)
        cr.fill()

        # Draw eye white
        cr.arc(bounds.width // 2, bounds.height // 2,
               eye_size // 2 - outline_width // 2, 0, 2 * math.pi)
        cr.set_source_rgb(1, 1, 1)
        cr.fill()

        # Draw eye outline
        cr.set_line_width(outline_width)
        cr.arc(bounds.width // 2, bounds.height // 2,
               eye_size // 2 - outline_width // 2, 0, 2 * math.pi)
        cr.set_source_rgb(0, 0, 0)
        cr.stroke()

        # Draw pupil
        cr.arc(pupil_x, pupil_y, pupil_size, 0, 2 * math.pi)
        cr.set_source_rgb(0, 0, 0)
        cr.fill()

        return True