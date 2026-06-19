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
from gettext import gettext as _

from gi.repository import Gdk
from gi.repository import GLib
from gi.repository import Gio

from sugar3 import profile

# Replaced Kernel with our new AI Manager
from ai_manager import AIManager
import voice

import logging
logger = logging.getLogger('speak')

# Compatibility: Keep this dictionary so activity.py doesn't crash when building the menu.
# We map 'English' to our generic Robot.
BOTS = {
    _('English'): {'name': 'Robot',
                   'brain': None,
                   'predicates': {'name': 'Robot'}}
}

_ai_brain = None

# Compatibility: activity.py calls this.
def get_default_voice():
    return voice.defaultVoice()

def respond(text, callback_func):
    """
    Non-blocking respond.
    text: User input
    callback_func: Function to call when answer is ready (must handle UI update)
    """
    if _ai_brain:
        # 1. Define the callback that runs on the UI thread
        def safe_ui_callback(response_text):
            callback_func(response_text)
            return False # Stop GLib.idle_add

        # 2. Define the callback that the background thread calls
        def thread_bridge(response_text):
            GLib.idle_add(safe_ui_callback, response_text)

        # 3. Actually ask the AI
        _ai_brain.generate_response(text, thread_bridge)
    else:
        # Fallback if brain isn't loaded
        callback_func(_("I am not ready yet."))


def load(activity, voice, sorry=None):
    """
    Initialize the AI Manager in a background thread.
    """
    # 1. Set "Watch" cursor immediately to show loading
    window = activity.get_window()
    old_cursor = window.get_cursor() if window else None
    if window:
        window.set_cursor(Gdk.Cursor(Gdk.CursorType.WATCH))

    # Callback when the model finishes loading
    def on_brain_loaded(success, message):
        def _update_ui():
            if window:
                window.set_cursor(old_cursor)
            
            if success:
                # Enable the button and speak
                if hasattr(activity, 'mode_robot'):
                    activity.mode_robot.set_sensitive(True)
                if hasattr(activity, 'face'):
                    activity.face.say(_("I am ready."))
            else:
                print(f"DEBUG: Load failed: {message}")
                if hasattr(activity, 'face'):
                    activity.face.say(_("I failed to load."))
            return False
        
        # Ensure UI updates happen on the main thread
        GLib.idle_add(_update_ui)

    # 2. Start the Threaded Loader IMMEDIATELY
    global _ai_brain
    if _ai_brain is None:
        print(" brain.py: Initializing AIManager...")
        _ai_brain = AIManager()
        _ai_brain.load_model(callback=on_brain_loaded)
    else:
        # Already loaded
        if window:
            window.set_cursor(old_cursor)
        if hasattr(activity, 'mode_robot'):
            activity.mode_robot.set_sensitive(True)

    return True