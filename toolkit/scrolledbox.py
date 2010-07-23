# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA

import gtk

from sugar.graphics.icon import Icon

class ScrollButton(gtk.ToolButton):
    def __init__(self, icon_name):
        gtk.ToolButton.__init__(self)

        icon = Icon(icon_name = icon_name,
                icon_size=gtk.ICON_SIZE_SMALL_TOOLBAR)
        # The alignment is a hack to work around gtk.ToolButton code
        # that sets the icon_size when the icon_widget is a gtk.Image
        alignment = gtk.Alignment(0.5, 0.5)
        alignment.add(icon)
        self.set_icon_widget(alignment)

class ScrolledBox(gtk.EventBox):
    def __init__(self, orientation,
            arrows_policy=gtk.POLICY_AUTOMATIC,
            scroll_policy=gtk.POLICY_AUTOMATIC):

        gtk.EventBox.__init__(self)
        self.orientation = orientation
        self._viewport = None
        self._abox = None
        self._aviewport = None
        self._aviewport_sig = None
        self._arrows_policy = arrows_policy
        self._scroll_policy = scroll_policy
        self._left = None
        self._right = None

        if orientation == gtk.ORIENTATION_HORIZONTAL:
            box = gtk.HBox()
        else:
            box = gtk.VBox()
        if self._arrows_policy == gtk.POLICY_AUTOMATIC:
            box.connect("size-allocate", self._box_allocate_cb)
        self.add(box)

        if self._arrows_policy != gtk.POLICY_NEVER:
            if orientation == gtk.ORIENTATION_HORIZONTAL:
                self._left = ScrollButton('go-left')
            else:
                self._left = ScrollButton('go-up')
            self._left.connect('clicked', self._scroll_cb,
                    gtk.gdk.SCROLL_LEFT)
            box.pack_start(self._left, False, False, 0)

        self._scrolled = gtk.ScrolledWindow()
        if orientation == gtk.ORIENTATION_HORIZONTAL:
            self._scrolled.set_policy(scroll_policy, gtk.POLICY_NEVER)
        else:
            self._scrolled.set_policy(gtk.POLICY_NEVER, scroll_policy)
        self._scrolled.connect('scroll-event', self._scroll_event_cb)
        box.pack_start(self._scrolled, True, True, 0)

        if orientation == gtk.ORIENTATION_HORIZONTAL:
            self._adj = self._scrolled.get_hadjustment()
        else:
            self._adj = self._scrolled.get_vadjustment()
        self._adj.connect('changed', self._scroll_changed_cb)
        self._adj.connect('value-changed', self._scroll_changed_cb)

        if self._arrows_policy != gtk.POLICY_NEVER:
            if orientation == gtk.ORIENTATION_HORIZONTAL:
                self._right = ScrollButton('go-right')
            else:
                self._right = ScrollButton('go-down')
            self._right.connect('clicked', self._scroll_cb,
                    gtk.gdk.SCROLL_RIGHT)
            box.pack_start(self._right, False, False, 0)

    def modify_fg(self, state, bg):
        gtk.EventBox.modify_fg(self, state, bg)
        self._viewport.get_parent().modify_fg(state, bg)

    def modify_bg(self, state, bg):
        gtk.EventBox.modify_bg(self, state, bg)
        self._viewport.get_parent().modify_bg(state, bg)

    def set_viewport(self, widget):
        if widget == self._viewport: return
        if self._viewport and self._aviewport_sig:
            self._viewport.disconnect(self._aviewport_sig)
        self._viewport = widget

        if self._arrows_policy == gtk.POLICY_AUTOMATIC:
            self._aviewport_sig = self._viewport.connect('size-allocate',
                    self._viewport_allocate_cb)

        self._scrolled.add_with_viewport(widget)

    def get_viewport_allocation(self):
        alloc = self._scrolled.get_allocation()
        alloc.x -= self._adj.get_value()
        return alloc

    def get_adjustment(self):
        return self._adj

    def _box_allocate_cb(self, w, a):
        self._abox = a
        self._update_arrows()

    def _viewport_allocate_cb(self, w, a):
        self._aviewport = a
        self._update_arrows()

    def _update_arrows(self):
        if not self._abox or not self._aviewport: return

        if self.orientation == gtk.ORIENTATION_HORIZONTAL:
            show_flag = self._abox.width < self._aviewport.width
        else:
            show_flag = self._abox.height < self._aviewport.height

        if show_flag:
            self._left.show()
            self._right.show()
        else:
            self._left.hide()
            self._right.hide()

    def _scroll_event_cb(self, widget, event):
        if self.orientation == gtk.ORIENTATION_HORIZONTAL:
            if event.direction == gtk.gdk.SCROLL_UP:
                event.direction = gtk.gdk.SCROLL_LEFT
            if event.direction == gtk.gdk.SCROLL_DOWN:
                event.direction = gtk.gdk.SCROLL_RIGHT
        else:
            if event.direction == gtk.gdk.SCROLL_LEFT:
                event.direction = gtk.gdk.SCROLL_UP
            if event.direction == gtk.gdk.SCROLL_RIGHT:
                event.direction = gtk.gdk.SCROLL_DOWN

        if self._scroll_policy == gtk.POLICY_NEVER:
            self._scroll_cb(None, event.direction)

        return False

    def _scroll_cb(self, widget, direction):
        if direction in (gtk.gdk.SCROLL_LEFT, gtk.gdk.SCROLL_UP):
            val = max(self._adj.get_property('lower'), self._adj.get_value()
                    - self._adj.get_property('page_increment'))
        else:
            val = min(self._adj.get_property('upper')
                    - self._adj.get_property('page_size'),
                    self._adj.get_value()
                    + self._adj.get_property('page_increment'))

        self._adj.set_value(val)

    def _scroll_changed_cb(self, widget):
        val = self._adj.get_value()
        if self._left:
            if val == 0:
                self._left.set_sensitive(False)
            else:
                self._left.set_sensitive(True)

        if self._right:
            if val >= self._adj.get_property('upper') - \
                    self._adj.get_property('page_size'):
                self._right.set_sensitive(False)
            else:
                self._right.set_sensitive(True)

class HScrolledBox(ScrolledBox):
    def __init__(self, **kwargs):
        ScrolledBox.__init__(self, gtk.ORIENTATION_HORIZONTAL, **kwargs)

class VScrolledBox(ScrolledBox):
    def __init__(self, **kwargs):
        ScrolledBox.__init__(self, gtk.ORIENTATION_VERTICAL, **kwargs)
