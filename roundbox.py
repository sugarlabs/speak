import math
import gtk
from sugar.graphics import style


class RoundBox(gtk.HBox):
    __gtype_name__ = 'RoundBox'

    _BORDER_DEFAULT = style.LINE_WIDTH

    def __init__(self, **kwargs):
        gtk.HBox.__init__(self, **kwargs)

        self._x = None
        self._y = None
        self._width = None
        self._height = None
        self._radius = style.zoom(10)
        self.border = self._BORDER_DEFAULT
        self.border_color = style.COLOR_BLACK
        self.background_color = None
        self.set_reallocate_redraws(True)
        self.set_resize_mode(gtk.RESIZE_PARENT)
        self.connect("expose_event", self.__expose_cb)
        self.connect("add", self.__add_cb)

    def __add_cb(self, child, params):
        child.set_border_width(style.zoom(5))

    def __size_allocate_cb(self, widget, allocation):
        self._x = allocation.x
        self._y = allocation.y
        self._width = allocation.width
        self._height = allocation.height

    def __expose_cb(self, widget, event):
        context = widget.window.cairo_create()

        # set a clip region for the expose event
        context.rectangle(event.area.x, event.area.y,
                               event.area.width, event.area.height)
        context.clip()
        self.draw(context)
        return False

    def draw(self, cr):
        rect = self.get_allocation()
        x = rect.x + self._BORDER_DEFAULT / 2
        y = rect.y + self._BORDER_DEFAULT / 2
        width = rect.width - self._BORDER_DEFAULT
        height = rect.height - self._BORDER_DEFAULT

        cr.move_to(x + self._radius, y)
        cr.arc(x + width - self._radius, y + self._radius,
               self._radius, math.pi * 1.5, math.pi * 2)
        cr.arc(x + width - self._radius, y + height - self._radius,
               self._radius, 0, math.pi * 0.5)
        cr.arc(x + self._radius, y + height - self._radius,
               self._radius, math.pi * 0.5, math.pi)
        cr.arc(x + self._radius, y + self._radius, self._radius,
               math.pi, math.pi * 1.5)
        cr.close_path()

        if self.background_color is not None:
            r, g, b, __ = self.background_color.get_rgba()
            cr.set_source_rgb(r, g, b)
            cr.fill_preserve()

        if self.border_color is not None:
            r, g, b, __ = self.border_color.get_rgba()
            cr.set_source_rgb(r, g, b)
            cr.set_line_width(self.border)
            cr.stroke()

if __name__ == '__main__':

    win = gtk.Window()
    win.connect('destroy', gtk.main_quit)
    win.set_default_size(450, 550)
    vbox = gtk.VBox()

    box1 = RoundBox()
    vbox.add(box1)
    label1 = gtk.Label("Test 1")
    box1.add(label1)

    rbox = RoundBox()
    rbox.background_color = style.Color('#FF0000')
    vbox.add(rbox)
    label2 = gtk.Label("Test 2")
    rbox.add(label2)

    bbox = RoundBox()
    bbox.background_color = style.Color('#aaff33')
    bbox.border_color = style.Color('#ff3300')
    vbox.add(bbox)

    win.add(vbox)
    win.show_all()
    gtk.main()
