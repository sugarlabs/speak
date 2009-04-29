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

from port.toolcombobox import ToolComboBox

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
        self._first_session = True

        self.voices = ToolComboBox()

        for lang in sorted(BOTS.keys()):
            self.voices.combo.append_item(lang, lang)

        self.voices.combo.set_active(0)
        self.voices.combo.connect('changed', self._changed_cb)
        self.voices.show()

        self.insert(self.voices, -1)

    def _changed_cb(self, combo):
        self.activity.change_voice(combo.props.value, False)

    def update_voice(self):
        voice = self.activity.voice_combo.props.value.friendlyname
        new_voice = BOTS.has_key(voice) and voice or DEFAULT

        if voice != new_voice:
            self.activity.change_voice(new_voice, True)
            self.voices.combo.select(new_voice)
        else:
            self.voices.combo.select(voice)

        if not self._kernels.has_key(new_voice):
            def load_brain(old_cursor, is_first_session):
                try:
                    brain = BOTS[new_voice]
                    logger.debug('Load bot: %s' % brain)

                    kernel = bot.aiml.Kernel()
                    kernel.loadBrain(brain['brain'])
                    for name, value in brain['predicates'].items():
                        kernel.setBotPredicate(name, value)
                    self._kernels[new_voice] = kernel
                finally:
                    self.activity.set_cursor(old_cursor)

                if is_first_session:
                    self.activity.face.say(
                            _("Hello, I'am a robot \"%s\". " \
                              "Ask me any question.") % BOTS[new_voice]['name'])

            old_cursor = self.activity.get_cursor()
            self.activity.set_cursor(gtk.gdk.WATCH)
            gobject.idle_add(load_brain, old_cursor, self._first_session)

        elif voice != new_voice:
            self.activity.face.say(
                    _("Sorry, I can speak %s, let's speak %s instead.") \
                            % (voice, new_voice))

        self._first_session = False

    def respond(self, text):
        voice = self.voices.combo.props.value
        return self._kernels[voice].respond(text)
