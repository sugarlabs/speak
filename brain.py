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
import gconf
import time
from gettext import gettext as _

import logging
logger = logging.getLogger('speak')

from sugar import profile

import aiml
import voice

BOTS = {
    _('Spanish'): { 'name': 'Sara',
                    'brain': 'bot/sara.brn',
                    'predicates': { 'nombre_bot': 'Sara',
                                    'botmaster': 'La comunidad Azucar' } },
    _('English'): { 'name': 'Alice',
                    'brain': 'bot/alice.brn',
                    'predicates': { 'name': 'Alice',
                                    'master': 'The Sugar Community' } } }


def get_mem_info(tag):
    meminfo = file('/proc/meminfo').readlines()
    return int([i for i in meminfo if i.startswith(tag)][0].split()[1])


# load Standard AIML set for restricted systems
if get_mem_info('MemTotal:') < 524288:
    mem_free = get_mem_info('MemFree:') + get_mem_info('Cached:')
    if mem_free < 102400:
        BOTS[_('English')]['brain'] = None
    else:
        BOTS[_('English')]['brain'] = 'bot/alisochka.brn'


_kernel = None
_kernel_voice = None


def _get_age():
    client = gconf.client_get_default()
    birth_timestamp = client.get_int('/desktop/sugar/user/birth_timestamp')
    if birth_timestamp == None or birth_timestamp == 0:
        return 8
    else:
        current_timestamp = time.time()
        age = (current_timestamp - birth_timestamp) / (365. * 24 * 60 * 60)
        if age < 5 or age > 16:
            age = 8
        return int(age)


def get_default_voice():
    default_voice = voice.defaultVoice()
    if default_voice.friendlyname not in BOTS:
        return voice.allVoices()[_('English')]
    else:
        return default_voice


def respond(text):
    if _kernel is not None:
        text = _kernel.respond(text)
    if _kernel is None or not text:
        text = _("Sorry, I can't understand what you are asking about.")
    return text


def load(activity, voice, sorry=None):
    if voice == _kernel_voice:
        return False

    old_cursor = activity.get_window().get_cursor()
    activity.get_window().set_cursor(gtk.gdk.Cursor(gtk.gdk.WATCH))

    def load_brain():
        global _kernel
        global _kernel_voice

        is_first_session = _kernel is None

        try:
            if voice.friendlyname in BOTS:
                brain = BOTS[voice.friendlyname]
                brain_name = BOTS[voice.friendlyname]['name']
            else:
                brain = BOTS[_('English')]
                brain_name = BOTS[_('English')]['name']
            logger.debug('Load bot: %s' % brain)

            kernel = aiml.Kernel()

            if brain['brain'] is None:
                warning = _("Sorry, there is no free memory to load my " \
                        "brain. Close other activities and try once more.")
                activity.face.say_notification(warning)
                return

            kernel.loadBrain(brain['brain'])
            for name, value in brain['predicates'].items():
                kernel.setBotPredicate(name, value)

            if _kernel is not None:
                del _kernel
                _kernel = None
                import gc
                gc.collect()

            _kernel = kernel
            _kernel_voice = voice
        finally:
            activity.get_window().set_cursor(old_cursor)

        if is_first_session:
            _kernel.respond(_('my name is %s') % (profile.get_nick_name()))
            _kernel.respond(_('I am %d years old') % (_get_age()))
            hello = \
                _("Hello, I'm a robot \"%s\". Please ask me any question.") \
                % brain_name
            if sorry:
                hello += ' ' + sorry
            activity.face.say_notification(hello)
        elif sorry:
            activity.face.say_notification(sorry)

    gobject.idle_add(load_brain)
    return True
