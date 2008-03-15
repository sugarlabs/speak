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


import subprocess
import re, os
from gettext import gettext as _

# Lets trick gettext into generating entries for the voice names we expect espeak to have
# If espeak actually has new or different names then they won't get translated, but they
# should still show up in the interface.
expectedVoiceNames = [
    _("Brazil"),
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
    _("Vietnam"),
    _("English"),
    _("Lancashire"),
    _("Italian"),
    _("Portugal"),
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

class Voice:
    def __init__(self, language, gender, name):
        self.language = language
        self.gender = gender
        self.name = name

        friendlyname = name
        friendlyname = friendlyname.replace('-test','')
        friendlyname = friendlyname.replace('_test','')
        friendlyname = friendlyname.replace('en-','')
        friendlyname = friendlyname.replace('english-wisper','whisper')
        friendlyname = friendlyname.capitalize()
        self.friendlyname = _(friendlyname)
    
def allVoices():
    if len(_allVoices) == 0:
        result = subprocess.Popen(["espeak", "--voices"], stdout=subprocess.PIPE).communicate()[0]
        for line in result.split('\n'):
            m = re.match(r'\s*\d+\s+([\w-]+)\s+([MF])\s+([\w_-]+)\s+(.+)', line)
            if m:
                language, gender, name, stuff = m.groups()
                if stuff.startswith('mb/') or name in ('en-rhotic','english_rp','english_wmids'):
                    # these voices don't produce sound
                    continue
                voice = Voice(language, gender, name)
                _allVoices[voice.friendlyname] = voice
    return _allVoices

def defaultVoice():
    """Try to figure out the default voice, from the current locale ($LANG).
       Fall back to espeak's voice called Default."""

    def fit(a,b):
        "Compare two language ids to see if they are similar."
	as = re.split(r'[^a-z]+', a.lower())
	bs = re.split(r'[^a-z]+', b.lower())
	for count in range(0, min(len(as),len(bs))):
            if as[count] != bs[count]:
                count -= 1
                break
        return count
    try:
        lang = os.environ["LANG"]
    except:
        lang = ""
    
    best = _allVoices[_("Default")]
    for voice in _allVoices.values():
        voiceMetric = fit(voice.language, lang)
        bestMetric  = fit(best.language, lang)
        if voiceMetric > bestMetric:
            best = voice

    print "Best voice for LANG %s seems to be %s %s" % (lang, best.language, best.friendlyname)
    return best
