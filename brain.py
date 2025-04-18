# HablarConSara.activity
# A simple hack to attach a chatterbot to speak activity
# Copyright (C) 2008 Sebastian Silva Fundacion FuenteLibre
# sebastian@fuentelibre.org
#
# Style and structure taken from Speak.activity Copyright (C) Joshua Minor
#
#     HablarConSara.activity is free software: you can redistribute it
#     and/or modify it under the terms of the GNU General Public
#     License as published by the Free Software Foundation, either
#     version 3 of the License, or (at your option) any later version.
#
#     HablarConSara.activity is distributed in the hope that it will
#     be useful, but WITHOUT ANY WARRANTY; without even the implied
#     warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
#     See the GNU General Public License for more details.
#
#     You should have received a copy of the GNU General Public
#     License along with HablarConSara.activity.  If not, see
#     <http://www.gnu.org/licenses/>.

import time
import os
import json
import logging
from gettext import gettext as _

from gi.repository import Gdk
from gi.repository import GLib
from gi.repository import Gio

from sugar3 import profile

from aiml.Kernel import Kernel
import voice

# Try to import ai_chat, but don't fail if unavailable
try:
    import ai_chat
    _has_ai_chat = True
except ImportError:
    _has_ai_chat = False
    logging.warning("ai_chat module not available - using legacy AIML bot instead")

import logging
logger = logging.getLogger('speak')

BOTS = {
    _('Spanish'): {'name': 'Sara',
                   'brain': 'bot/sara.brn',
                   'predicates': {'nombre_bot': 'Sara',
                                  'botmaster': 'La comunidad Azucar'}},
    _('English'): {'name': 'Alice',
                   'brain': 'bot/alice.brn',
                   'predicates': {'name': 'Alice',
                                  'master': 'The Sugar Community'}}}

# The MS. Robin bot uses the new AI chat system
BOTS[_('Robin')] = {'name': 'Robin', 
                   'brain': None,  # No AIML brain needed
                   'predicates': {'name': 'Robin',
                                  'master': 'The Sugar Community'}}

def get_mem_info(tag):
    '''
    Returns the specified memory information in KB

    tag -- the memory information to return
        MemTotal, MemFree, MemAvailable, etc from /proc/meminfo
    '''
    meminfo = {}
    with open('/proc/meminfo') as f:
        for line in f:
            key, value = line.split(':', 1)
            meminfo[key] = int(value.strip().split()[0])
    return meminfo.get(tag, 0)

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
    birth_timestamp = os.stat(os.path.expanduser('~/.sugar/default/user'))
    birth_time = time.gmtime(birth_timestamp.st_ctime)
    now_time = time.gmtime()
    birth_year = birth_time.tm_year
    birth_month = birth_time.tm_mon
    birth_day = birth_time.tm_mday
    now_year = now_time.tm_year
    now_month = now_time.tm_mon
    now_day = now_time.tm_mday
    age = now_year - birth_year
    if now_month < birth_month or \
            (now_month == birth_month and now_day < birth_day):
        age -= 1
    return age


def get_default_voice():
    if 'es' in _('English'):
        default_language = 'es'
    else:
        default_language = 'en'
    return voice.get_default_voice(default_language)


def respond(text):
    """Generate a response to user input text using LLM or AIML"""
    # If AI chat is available and properly initialized, use it
    if _has_ai_chat and _kernel_voice and _kernel_voice.short_name == "Robin":
        try:
            return ai_chat.get_response(text)
        except Exception as e:
            logger.error(f"Error using AI chatbot: {e}")
            # Fall through to AIML backup
    
    # Otherwise use AIML-based response
    if _kernel is not None:
        text = _kernel.respond(text)
    if _kernel is None or not text:
        text = _("Sorry, I can't understand what you are asking about.")
    return text


def load(activity, voice, sorry=None):
    if voice == _kernel_voice:
        return False

    old_cursor = activity.get_window().get_cursor()
    activity.get_window().set_cursor(Gdk.Cursor(Gdk.CursorType.WATCH))

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
            
            # For "Robin" bot, we don't need to load an AIML brain
            if voice.short_name == "Robin" and _has_ai_chat:
                _kernel_voice = voice
                activity.get_window().set_cursor(old_cursor)
                
                if is_first_session:
                    hello = \
                        _("Hello, I'm Ms. Robin. I'm here to help you learn to read. What would you like to talk about?")
                    if sorry:
                        hello += ' ' + sorry
                    activity.face.say_notification(hello)
                elif sorry:
                    activity.face.say_notification(sorry)
                return
            
            # For other bots, load AIML brain
            kernel = Kernel()

            if brain['brain'] is None:
                warning = _("Sorry, there is no free memory to load my "
                            "brain. Close other activities and try once more.")
                activity.face.say_notification(warning)
                return

            kernel.loadBrain(brain['brain'])
            for name, value in list(brain['predicates'].items()):
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

    GLib.idle_add(load_brain)
    return True
