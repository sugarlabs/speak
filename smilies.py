# -*- coding: utf-8 -*-
# Copyright 2010, Mukesh Gupta
# Copyright 2010, Aleksey Lim
# Copyright 2014, Walter Bender
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

import os
from gettext import gettext as _
from gi.repository import GdkPixbuf
from sugar3.graphics import style
from sugar3.activity.activity import get_bundle_path

THEME = [
    # TRANS: A smiley (http://en.wikipedia.org/wiki/Smiley) explanation
    # TRANS: ASCII-art equivalents are :-) and :)
    ('smile', _('Smile'), [':-)', ':)']),
    # TRANS: A smiley (http://en.wikipedia.org/wiki/Smiley) explanation
    # TRANS: ASCII-art equivalents are ;-) and ;)
    ('wink', _('Winking'), [';-)', ';)']),
    # TRANS: A smiley (http://en.wikipedia.org/wiki/Smiley) explanation
    # TRANS: ASCII-art equivalents are :-/ and :/
    ('confused', _('Confused'), [':-/', ':/']),
    # TRANS: A smiley (http://en.wikipedia.org/wiki/Smiley) explanation
    # TRANS: ASCII-art equivalents are :-( and :(
    ('sad', _('Sad'), [':-(', ':(']),
    # TRANS: A smiley (http://en.wikipedia.org/wiki/Smiley) explanation
    # TRANS: ASCII-art equivalents are :-D and :D
    ('grin', _('Grin'), [':-D', ':D']),
    # TRANS: A smiley (http://en.wikipedia.org/wiki/Smiley) explanation
    # TRANS: ASCII-art equivalents are :-| and :|
    ('neutral', _('Neutral'), (':-|', ':|')),
    # TRANS: A smiley (http://en.wikipedia.org/wiki/Smiley) explanation
    # TRANS: ASCII-art equivalents are :-O, :O, =-O and =O
    ('shock', _('Shock'), [':-O', ':O', '=-O', '=O']),
    # TRANS: A smiley (http://en.wikipedia.org/wiki/Smiley) explanation
    # TRANS: ASCII-art equivalents are B-), B), 8-) and 8)
    ('cool', _('Cool'), ['B-)', 'B)', '8-)', '8)']),
    # TRANS: A smiley (http://en.wikipedia.org/wiki/Smiley) explanation
    # TRANS: ASCII-art equivalents are :-P and :P
    ('tongue', _('Tongue'), [':-P', ':P']),
    # TRANS: A smiley (http://en.wikipedia.org/wiki/Smiley) explanation
    # TRANS: ASCII-art equivalents are :">
    ('blush', _('Blushing'), [':">']),
    # TRANS: A smiley (http://en.wikipedia.org/wiki/Smiley) explanation
    # TRANS: ASCII-art equivalents are :'-( and :'(
    ('weep', _('Weeping'), [":'-(", ":'("]),
    # TRANS: A smiley (http://en.wikipedia.org/wiki/Smiley) explanation
    # TRANS: ASCII-art equivalents are O-), O), O:-) and O:)
    ('angel', _('Angel'), ['O-)', 'O)', 'O:-)', 'O:)']),
    # TRANS: A smiley (http://en.wikipedia.org/wiki/Smiley) explanation
    # TRANS: ASCII-art equivalents are :-$ and :-$
    ('shutup', _("Don't tell anyone"), (':-$', ':-$')),
    # TRANS: A smiley (http://en.wikipedia.org/wiki/Smiley) explanation
    # TRANS: ASCII-art equivalents are x-(, x(, X-( and x-(
    ('angry', _('Angry'), ('x-(', 'x(', 'X-(', 'x-(')),
    # TRANS: A smiley (http://en.wikipedia.org/wiki/Smiley) explanation
    # TRANS: ASCII-art equivalents are >:> and >:)
    ('devil', _('Devil'), ('>:>', '>:)')),
    # TRANS: A smiley (http://en.wikipedia.org/wiki/Smiley) explanation
    # TRANS: ASCII-art equivalents are :-B, :B
    ('nerd', _('Nerd'), (':-B', ':B')),
    # TRANS: A smiley (http://en.wikipedia.org/wiki/Smiley) explanation
    # TRANS: ASCII-art equivalents are :-*, :*
    ('kiss', _('Kiss'), (':-*', ':*')),
    # TRANS: A smiley (http://en.wikipedia.org/wiki/Smiley) explanation
    # TRANS: ASCII-art equivalents are :))
    ('laugh', _('Laughing'), [':))']),
    # TRANS: A smiley (http://en.wikipedia.org/wiki/Smiley) explanation
    # TRANS: ASCII-art equivalents are I-)
    ('sleep', _('Sleepy'), ['I-)']),
    # TRANS: A smiley (http://en.wikipedia.org/wiki/Smiley) explanation
    # TRANS: ASCII-art equivalents are :-&
    ('sick', _('Sick'), [':-&']),
    # TRANS: A smiley (http://en.wikipedia.org/wiki/Smiley) explanation
    # TRANS: ASCII-art equivalents are /:)
    ('eyebrow', _('Raised eyebrows'), ['/:)']),
    ('unicode-1', _('Heart'), ['♥']),
    ('unicode-2', _('Airplane'), ['✈']),
    ('unicode-3', _('Music'), ['♬']),
    ('unicode-4', _('Check box'), ['☑']),
    ('unicode-5', _('Spade'), ['♠']),
    ('unicode-6', _('Telephone'), ['☎']),
    ('unicode-7', _('X box'), ['☒']),
    ('unicode-8', _('Cadusis'), ['☤']),
    ('unicode-9', _('Female'), ['♀']),
    ('unicode-10', _('Star'), ['✩']),
    ('unicode-11', _('Letter'), ['✉']),
    ('unicode-12', _('Poison'), ['☠']),
    ('unicode-13', _('Check mark'), ['✔']),
    ('unicode-14', _('Male'), ['♂']),
    ('unicode-15', _('Star'), ['★']),
    ('unicode-16', _('Shamrock'), ['☘']),
    ('unicode-17', _('Recycle'), ['♺']),
    ('unicode-18', _('X'), ['✖']),
    ('unicode-19', _('Fire'), ['♨']),
    ('unicode-20', _('Leaf'), ['❦']),
    ('unicode-21', _('Cloud'), ['☁']),
    ('unicode-22', _('V'), ['✌']),
    ('unicode-23', _('Crown'), ['♛']),
    ('unicode-24', _('Floret'), ['❁']),
    ('unicode-25', _('Star and crescent'), ['☪']),
    ('unicode-26', _('Umbrella'), ['☂']),
    ('unicode-27', _('Pencil'), ['✏']),
    ('unicode-28', _('Floret'), ['❀']),
    ('unicode-29', _('Snowman'), ['☃']),
    ('unicode-30', _('Point right'), ['☛']),
    ('unicode-31', _('Horse'), ['♞']),
    ('unicode-32', _('Floret'), ['✿']),
    ('unicode-33', _('Peace sign'), ['☮']),
    ('unicode-34', _('Sun'), ['☼']),
    ('unicode-35', _('Point left'), ['☚']),
    ('unicode-36', _('Floret'), ['✾']),
    ('unicode-37', _('Yin yang'), ['☯']),
    ('unicode-38', _('Moon'), ['☾']),
    ('unicode-39', _('Point up'), ['☝']),
    ('unicode-40', _('Floret'), ['✽']),
    ('unicode-41', _('Meteor'), ['☄']),
    ('unicode-42', _('Point down'), ['☟']),
    ('unicode-43', _('Floret'), ['✺']),
    ('unicode-44', _('Scissors'), ['✂']),
    ('unicode-45', _('Pen'), ['✍']),
    ('unicode-46', _('Floret'), ['✵']),
    ('unicode-47', _('Stars'), ['⁂']),
    ('unicode-48', _('Place'), ['⌘']),
    ('unicode-49', _('High voltage'), ['⚡']),
    ]

SMILIES_SIZE = int(style.STANDARD_ICON_SIZE * 0.75)
_catalog = {}


def _smiley_to_theme_name(smiley):
    for theme in THEME:
        if smiley in theme[2]:
            return theme[0]
    return None


def parse(text):
    '''Parse text and find smiles.
    :param text:
    string to parse for smilies
    :returns:
    array of string parts and pixbufs
    '''

    result = [text]

    for smiley in sorted(_catalog.keys(), lambda x, y: cmp(len(y), len(x))):
        new_result = []
        for word in result:
            if isinstance(word, GdkPixbuf.Pixbuf):
                new_result.append(word)
            else:
                parts = word.split(smiley)
                for i in parts[:-1]:
                    name = _smiley_to_theme_name(smiley)
                    new_result.append(i)
                    if name is not None and 'unicode' in name:
                        new_result.append(smiley)
                    else:
                        new_result.append(_catalog[smiley])
                new_result.append(parts[-1])
        result = new_result

    return result


def init():
    if _catalog:
        return

    svg_dir = os.path.join(get_bundle_path(), 'icons', 'smilies')

    for index, (name, hint, codes) in enumerate(THEME):
        archivo = os.path.join(svg_dir, '%s.svg' % (name))
        if name[0:7] == 'unicode':
            # Create the icon from unicode character on the fly
            pl = GdkPixbuf.PixbufLoader.new_with_type('svg')
            pl.write(_generate_svg(codes[0]))
            pl.close()
            pixbuf = pl.get_pixbuf()
            if not os.path.exists(archivo):
                try:
                    fd = open(archivo, 'w')
                    fd.write(_generate_svg(codes[0]))
                    fd.close()
                except IOError as e:
                    pass
        else:
            pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_size(
                archivo, SMILIES_SIZE, SMILIES_SIZE)
        for i in codes:
            _catalog[i] = pixbuf
            THEME[index] = (archivo, hint, codes)


def _generate_svg(letter):
    # TODO: Adjust font size and character positioning
    return '<?xml version="1.0" encoding="UTF-8" standalone="no"?>\n' + \
        '<svg\n' + \
        ' xmlns:dc="http://purl.org/dc/elements/1.1/"\n' + \
        ' xmlns:cc="http://creativecommons.org/ns#"\n' + \
        ' xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#"\n' + \
        ' xmlns:svg="http://www.w3.org/2000/svg"\n' + \
        ' xmlns="http://www.w3.org/2000/svg"\n' + \
        ' version="1.0"\n' + \
        ' width="55"\n' + \
        ' height="55"\n' + \
        '>\n' + \
        '<text\n' + \
        ' x="0"\n' + \
        ' y="42"\n' + \
        'style="font-size:40px;font-style:normal;font-weight:normal;\n' + \
        'fill:#ffffff;fill-opacity:1;stroke:none;' + \
        'font-family:Bitstream Vera Sans">\n' + \
        '<tspan\n' + \
        ' x="0"\n' + \
        ' y="42">\n' + \
        letter + \
        '</tspan></text>\n' + \
        '</svg>\n'
