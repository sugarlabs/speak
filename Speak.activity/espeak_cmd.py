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

import re
import subprocess

import logging
logger = logging.getLogger('speak')

import espeak

PITCH_MAX = 99
RATE_MAX = 99
PITCH_DEFAULT = PITCH_MAX/2
RATE_DEFAULT = RATE_MAX/3

class AudioGrabCmd(espeak.BaseAudioGrab):
    def speak(self, status, text):
        self.make_pipeline('filesrc name=file-source')

        # espeak uses 80 to 370
        rate = 80 + (370-80) * int(status.rate) / 100
        wavpath = "/tmp/speak.wav"

        subprocess.call(["espeak", "-w", wavpath, "-p", str(status.pitch),
                "-s", str(rate), "-v", status.voice.name, text],
                stdout=subprocess.PIPE)

        self.stop_sound_device()

        # set the source file
        self.pipeline.get_by_name("file-source").props.location = wavpath

        # play
        self.restart_sound_device()

def voices():
    out = []
    result = subprocess.Popen(["espeak", "--voices"], stdout=subprocess.PIPE) \
            .communicate()[0]

    for line in result.split('\n'):
        m = re.match(r'\s*\d+\s+([\w-]+)\s+([MF])\s+([\w_-]+)\s+(.+)', line)
        if not m:
            continue
        language, gender, name, stuff = m.groups()
        if stuff.startswith('mb/') or \
                name in ('en-rhotic','english_rp','english_wmids'):
            # these voices don't produce sound
            continue
        out.append((language, name))

    return out
