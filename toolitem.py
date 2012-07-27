# Copyright (C) 2009, Aleksey Lim
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2 of the License, or (at your option) any later version.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this library; if not, write to the
# Free Software Foundation, Inc., 59 Temple Place - Suite 330,
# Boston, MA 02111-1307, USA.

"""A set of toolitem widets"""

from gi.repository import Gtk

class ToolWidget(Gtk.ToolItem):

    def __init__(self, widget=None, label_text=""):
        Gtk.ToolItem.__init__(self)
        
        self.wid = widget
        self.label = Gtk.Label(label_text)
        self._box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        
        if self.label:
                self._box.pack_start(self.label, True, True, 5)
        if self.wid:
                self._box.pack_start(self.wid, True, True, 5)
        
        self.add(self._box)
        self.show_all()
