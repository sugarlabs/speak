# Speak.activity
# A simple front end to the espeak text-to-speech engine on the XO laptop
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
#     Foobar is distributed in the hope that it will be useful,
#     but WITHOUT ANY WARRANTY; without even the implied warranty of
#     MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#     GNU General Public License for more details.
# 
#     You should have received a copy of the GNU General Public License
#     along with Foobar.  If not, see <http://www.gnu.org/licenses/>.


import subprocess
import re

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
        self.friendlyname = friendlyname

    
def allVoices():
    voices = {}
    result = subprocess.Popen(["espeak", "--voices"], stdout=subprocess.PIPE).communicate()[0]
    for line in result.split('\n'):
        m = re.match(r'\s*\d+\s+([\w-]+)\s+([MF])\s+([\w_-]+)\s+(.+)', line)
        if m:
            language, gender, name, stuff = m.groups()
            if stuff.startswith('mb/') or name in ('en-rhotic','english_rp','english_wmids'):
                # these voices don't produce sound
                continue
            voice = Voice(language, gender, name)
            voices[voice.friendlyname] = voice
    return voices

