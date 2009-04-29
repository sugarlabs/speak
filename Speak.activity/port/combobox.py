# Copyright (C) 2007, One Laptop Per Child
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

"""
STABLE.
"""

import gobject
import gtk

from sugar.graphics import style

class ComboBox(gtk.ComboBox):
    def __init__(self):
        gtk.ComboBox.__init__(self)

        self._text_renderer = None
        self._icon_renderer = None

        self._model = gtk.ListStore(gobject.TYPE_PYOBJECT,
                                    gobject.TYPE_STRING,
                                    gtk.gdk.Pixbuf,
                                    gobject.TYPE_BOOLEAN)
        self.set_model(self._model)

        self.set_row_separator_func(self._is_separator)

    def get_value(self):
        """
        Parameters
        ----------
        None :

        Returns:
        --------
        value :

        """
        row = self.get_active_item()
        if not row:
            return None
        return row[0]

    value = gobject.property(
        type=object, getter=get_value, setter=None)

    def _get_real_name_from_theme(self, name, size):
        icon_theme = gtk.icon_theme_get_default()
        width, height = gtk.icon_size_lookup(size)
        info = icon_theme.lookup_icon(name, max(width, height), 0)
        if not info:
            raise ValueError("Icon '" + name + "' not found.")
        fname = info.get_filename()
        del info
        return fname

    def append_item(self, action_id, text, icon_name=None, file_name=None):
        """
        Parameters
        ----------
        action_id :

        text :

        icon_name=None :

        file_name=None :

        Returns
        -------
        None

        """
        if not self._icon_renderer and (icon_name or file_name):
            self._icon_renderer = gtk.CellRendererPixbuf()

            settings = self.get_settings()
            w, h = gtk.icon_size_lookup_for_settings(
                                            settings, gtk.ICON_SIZE_MENU)
            self._icon_renderer.props.stock_size = max(w, h)

            self.pack_start(self._icon_renderer, False)
            self.add_attribute(self._icon_renderer, 'pixbuf', 2)

        if not self._text_renderer and text:
            self._text_renderer = gtk.CellRendererText()
            self.pack_end(self._text_renderer, True)
            self.add_attribute(self._text_renderer, 'text', 1)

        if icon_name or file_name:
            if text:
                size = gtk.ICON_SIZE_MENU
            else:
                size = gtk.ICON_SIZE_LARGE_TOOLBAR
            width, height = gtk.icon_size_lookup(size)

            if icon_name:
                file_name = self._get_real_name_from_theme(icon_name, size)

            pixbuf = gtk.gdk.pixbuf_new_from_file_at_size(
                                                file_name, width, height)
        else:
            pixbuf = None

        self._model.append([action_id, text, pixbuf, False])

    def append_separator(self):
        """
        Parameters
        ----------
        None

        Returns
        -------
        None

        """
        self._model.append([0, None, None, True])    

    def get_active_item(self):
        """
        Parameters
        ----------
        None

        Returns
        -------
        Active_item :

        """
        index = self.get_active()
        if index == -1:
            index = 0

        row = self._model.iter_nth_child(None, index)
        if not row:
            return None
        return self._model[row]

    def remove_all(self):
        """
        Parameters
        ----------
        None

        Returns
        -------
        None

        """
        self._model.clear()

    def _is_separator(self, model, row):
        return model[row][3]

    def select(self, value, column=0, silent_cb=None):
        for i, item in enumerate(self.get_model()):
            if item[column] != value:
                continue
            try:
                if silent_cb:
                    try:
                        self.handler_block_by_func(silent_cb)
                    except Exception, e:
                        print e
                        silent_cb = None
                self.set_active(i)
            finally:
                if silent_cb:
                    self.handler_unblock_by_func(silent_cb)
            break

class ToolComboBox(gtk.ToolItem):
    __gproperties__ = {
        'label-text' : (str, None, None, None,
                        gobject.PARAM_WRITABLE),
    }

    def __init__(self, combo=None, **kwargs):
        self.label = None
        self._label_text = ''

        gobject.GObject.__init__(self, **kwargs)

        self.set_border_width(style.DEFAULT_PADDING)

        hbox = gtk.HBox(False, style.DEFAULT_SPACING)

        self.label = gtk.Label(self._label_text)
        hbox.pack_start(self.label, False)
        self.label.show()

        if combo:
            self.combo = combo
        else:
            self.combo = ComboBox()

        hbox.pack_start(self.combo)
        self.combo.show()

        self.add(hbox)
        hbox.show()

    def do_set_property(self, pspec, value):
        if pspec.name == 'label-text':
            self._label_text = value
            if self.label:
                self.label.set_text(self._label_text)
