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

import gtk
import gobject

from sugar.graphics import style

from toolkit.combobox import ComboBox


class ToolWidget(gtk.ToolItem):

    def __init__(self, **kwargs):
        self._widget = None
        self._label = None
        self._label_text = None
        self._box = gtk.HBox(False, style.DEFAULT_SPACING)

        gobject.GObject.__init__(self, **kwargs)
        self.props.border_width = style.DEFAULT_PADDING

        self._box.show()
        self.add(self._box)

        if self.label is None:
            self.label = gtk.Label()

    def get_label_text(self):
        return self._label_text

    def set_label_text(self, value):
        self._label_text = value
        if self.label is not None and value:
            self.label.set_text(self._label_text)

    label_text = gobject.property(getter=get_label_text, setter=set_label_text)

    def get_label(self):
        return self._label

    def set_label(self, label):
        if self._label is not None:
            self._box.remove(self._label)
        self._label = label
        self._box.pack_start(label, False)
        self._box.reorder_child(label, 0)
        label.show()
        self.set_label_text(self._label_text)

    label = gobject.property(getter=get_label, setter=set_label)

    def get_widget(self):
        return self._widget

    def set_widget(self, widget):
        if self._widget is not None:
            self._box.remove(self._widget)
        self._widget = widget
        self._box.pack_end(widget)
        widget.show()

    widget = gobject.property(getter=get_widget, setter=set_widget)
