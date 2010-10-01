# Copyright (C) 2009, Aleksey Lim
#
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

"""
Unify usage of simplejson in Python 2.5/2.6

In Python 2.5 it imports simplejson module, in 2.6 native json module.

Usage:

    import toolkit.json as json

    # and using regular simplejson interface with module json
    json.dumps([])

"""

try:
    from json import *
    dumps
except (ImportError, NameError):
    from simplejson import *
