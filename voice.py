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
#     Speak.activity is free software: you can redistribute it and/or modify
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

import re
import os
from gettext import gettext as _

import speech
import logging
logger = logging.getLogger('speak')

# Lets trick gettext into generating entries for the voice names we
# expect espeak to have. If espeak actually has new or different names
# then they won't get translated, but they should still show up in the
# interface.
expectedVoiceNames = [
    _("Portuguese (Brazil)"),
    _("Swedish"),
    _("Icelandic"),
    _("Romanian"),
    _("Swahili"),
    _("Hindi"),
    _("Dutch"),
    _("Latin"),
    _("Hungarian"),
    _("Macedonian"),
    _("Welsh"),
    _("French"),
    _("Norwegian"),
    _("Russian"),
    _("Afrikaans"),
    _("Finnish"),
    _("Default"),
    _("Cantonese"),
    _("Scottish"),
    _("Greek"),
    _("Vietnamese"),
    _("English"),
    _("Lancashire"),
    _("Italian"),
    _("Portuguese"),
    _("German"),
    _("Whisper"),
    _("Croatian"),
    _("Czech"),
    _("Slovak"),
    _("Spanish"),
    _("Polish"),
    _("Esperanto")
]

_allVoices = {}
_defaultVoice = None


def _friendly_name(full_name):
    parts = re.split('[ _-]', full_name)
    short_name = _(parts[0].capitalize())
    return ' '.join([short_name] + parts[1:])


class Voice:
    def __init__(self, language, name):
        self.language = language
        self.name = name
        friendlyname = name
        friendlyname = friendlyname.replace('-test', '')
        friendlyname = friendlyname.replace('_test', '')
        friendlyname = friendlyname.replace('en-', '')
        friendlyname = friendlyname.replace('english-wisper', 'whisper')
        friendlyname = friendlyname.replace('english-us', 'us')

        friendlynameRP = name  # friendlyname for RP
        friendlynameRP = friendlynameRP.replace('english_rp', 'rp')
        friendlynameRP = friendlynameRP.replace('english_wmids', 'wmids')

        parts = re.split('[ _-]', friendlyname)
        self.short_name = _(parts[0].capitalize())
        self.friendlyname = ' '.join([self.short_name] + parts[1:])

        if friendlynameRP == 'rp':
            self.friendlyname = 'English (Received Pronunciation)'

        if friendlyname == 'us':
            self.friendlyname = 'English (USA)'

        if friendlynameRP == 'wmids':
            self.friendlyname = 'English (West Midlands)'

    def __lt__(self, other):
        return self.friendlyname < other.friendlyname


def allVoices():
    if _allVoices:
        return _allVoices

    voice_list = speech.get_speech().get_all_voices()

    for language, name in voice_list.items():
        voice = Voice(language, name)
        _allVoices[voice.friendlyname] = voice

    en_name = _friendly_name('English')
    if en_name not in _allVoices:
        _allVoices[en_name] = _allVoices[_friendly_name('English (America)')]
        _allVoices[en_name].friendlyname = en_name

    es_name = _friendly_name('Spanish')
    if es_name not in _allVoices:
        _allVoices[es_name] = _allVoices[_friendly_name('Spanish (Latin America)')]
        _allVoices[es_name].friendlyname = es_name

    return _allVoices


def by_name(name):
    return allVoices().get(name, defaultVoice())


def defaultVoice():
    """Try to figure out the default voice, from the current locale ($LANG).
    """

    global _defaultVoice

    if _defaultVoice:
        return _defaultVoice

    voices = allVoices()

    def fit(a, b):
        "Compare two language ids to see if they are similar."
        as_ = re.split(r'[^a-z]+', a.lower())
        bs = re.split(r'[^a-z]+', b.lower())
        for count in range(0, min(len(as_), len(bs))):
            if as_[count] != bs[count]:
                count -= 1
                break
        return count
    try:
        lang = os.environ["LANG"]
    except KeyError:
        lang = ""

    voice_names = [
        _friendly_name("English (America)"),  # espeak-ng 1.49.2
        _friendly_name("English"),  # espeak-ng 1.49.1
        _friendly_name("Default"),  # espeak 1.48
    ]

    best = None
    for voice_name in voice_names:
        if voice_name in voices:
            best = voices[voice_name]
            break

    es_name = _friendly_name('Spanish')
    es_la_name = _friendly_name('Spanish (Latin America)')
    en_au_name = _friendly_name('English (Received Pronunciation)')

    for voice in list(voices.values()):
        voiceMetric = fit(voice.language, lang)
        bestMetric = fit(best.language, lang)
        if lang == 'en_AU.UTF-8':
            if voice.friendlyname == en_au_name:
                best = voice
                break
        if lang[0:2] == 'es':
            if voice.friendlyname in [es_name, es_la_name]:
                best = voice
                break
        if voiceMetric > bestMetric:
            best = voice

    _defaultVoice = best
    return best
