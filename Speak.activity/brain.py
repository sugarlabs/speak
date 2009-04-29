# HablarConSara.activity
# A simple hack to attach a chatterbot to speak activity
# Copyright (C) 2008 Sebastian Silva Fundacion FuenteLibre sebastian@fuentelibre.org
#
# Style and structure taken from Speak.activity Copyright (C) Joshua Minor
#
#     HablarConSara.activity is free software: you can redistribute it and/or modify
#     it under the terms of the GNU General Public License as published by
#     the Free Software Foundation, either version 3 of the License, or
#     (at your option) any later version.
# 
#     HablarConSara.activity is distributed in the hope that it will be useful,
#     but WITHOUT ANY WARRANTY; without even the implied warranty of
#     MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#     GNU General Public License for more details.
# 
#     You should have received a copy of the GNU General Public License
#     along with HablarConSara.activity.  If not, see <http://www.gnu.org/licenses/>.

import gtk
import gobject
from gettext import gettext as _

import logging
logger = logging.getLogger('speak')

from port.combobox import ToolComboBox

import bot.aiml
import voice

BOTS = {
    _('Spanish'): { 'name': 'Sara',
                    'brain': 'bot/sara.brn',
                    'predicates': { 'nombre_bot': 'Sara',
                                    'botmaster': 'la comunidad Azucar' } },
    _('English'): { 'name': 'Alice',
                    'brain': 'bot/alice.brn',
                    'predicates': { 'name': 'Alice',
                                    'master': 'the Sugar Community' } } }

DEFAULT = voice.defaultVoice()
if not BOTS.has_key(DEFAULT):
    DEFAULT = _('English')

class Toolbar(gtk.Toolbar):
    def __init__(self, activity):
        gtk.Toolbar.__init__(self)
        self.activity = activity
        self._kernels = {}

        self.voices = ToolComboBox()

        for lang in sorted(BOTS.keys()):
            self.voices.combo.append_item(lang, lang)

        self.voices.combo.set_active(0)
        self.voices.combo.connect('changed', self._changed_cb)
        self.voices.show()

        self.insert(self.voices, -1)

    def _load_brain(self, voice, sorry=''):
        def load_brain(old_cursor):
            is_first_session = (len(self._kernels) == 0)

            try:
                brain = BOTS[voice]
                logger.debug('Load bot: %s' % brain)

                kernel = bot.aiml.Kernel()
                kernel.loadBrain(brain['brain'])
                for name, value in brain['predicates'].items():
                    kernel.setBotPredicate(name, value)
                self._kernels[voice] = kernel
            finally:
                self.activity.set_cursor(old_cursor)

            if is_first_session:
                hello = _("Hello, I'am a robot \"%s\". Ask me any question.") \
                        % BOTS[voice]['name']
                hello += ' ' + sorry
                self.activity.face.say(hello)
            elif sorry:
                self.activity.face.say(sorry)

        old_cursor = self.activity.get_cursor()
        self.activity.set_cursor(gtk.gdk.WATCH)
        gobject.idle_add(load_brain, old_cursor)

    def _changed_cb(self, combo):
        voice = combo.props.value
        self.activity.change_voice(voice, False)
        if not self._kernels.has_key(voice):
            self._load_brain(voice)

    def update_voice(self):
        voice = self.activity.voice_combo.props.value.friendlyname
        new_voice = BOTS.has_key(voice) and voice or DEFAULT

        if voice != new_voice:
            self.activity.change_voice(new_voice, True)
        self.voices.combo.select(new_voice, silent_cb=self._changed_cb)

        sorry = _("Sorry, I can speak %s, let's speak %s instead.") \
                % (voice, new_voice)

        if not self._kernels.has_key(new_voice):
            self._load_brain(new_voice, (voice != new_voice) and sorry or '')
        elif voice != new_voice:
            self.activity.face.say(sorry)

    def respond(self, text):
        voice = self.voices.combo.props.value
        return self._kernels[voice].respond(text)
