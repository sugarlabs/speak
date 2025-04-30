# Copyright (C) 2009, Aleksey Lim, Simon Schampijer
# Copyright (C) 2012, Walter Bender
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import re
import random
import logging
import urllib.request
import json
import threading
from gettext import gettext as _

# Import for Gen-AI support
# We're using a separate thread for API calls to avoid blocking the UI
# We'll add error handling for when the API is unavailable

# Configuration for Gen-AI
GENAI_ENABLED = True  # Set to False to use the original chatbot
GENAI_API_KEY = ""  # Set your API key here
GENAI_API_URL = "https://api.openai.com/v1/chat/completions"
GENAI_MODEL = "gpt-3.5-turbo"
GENAI_TEMPERATURE = 0.7
GENAI_MAX_TOKENS = 100
GENAI_SYSTEM_PROMPT = """You are a friendly assistant for children. 
Keep answers simple, educational, and positive. 
Limit responses to 1-2 short sentences.
Never use inappropriate language or discuss mature topics."""


def get_genai_response(text, callback=None):
    """Get a response from the Gen-AI API"""
    try:
        if not GENAI_API_KEY:
            logging.warning("Gen-AI API key not set, falling back to original brain")
            if callback:
                callback(_("I'm not connected to AI right now. Let's chat the old way!"))
            return

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {GENAI_API_KEY}"
        }
        data = {
            "model": GENAI_MODEL,
            "messages": [
                {"role": "system", "content": GENAI_SYSTEM_PROMPT},
                {"role": "user", "content": text}
            ],
            "temperature": GENAI_TEMPERATURE,
            "max_tokens": GENAI_MAX_TOKENS
        }
        
        req = urllib.request.Request(
            GENAI_API_URL,
            data=json.dumps(data).encode('utf-8'),
            headers=headers,
            method="POST"
        )
        
        with urllib.request.urlopen(req, timeout=10) as response:
            response_data = json.loads(response.read().decode('utf-8'))
            if 'choices' in response_data and len(response_data['choices']) > 0:
                ai_response = response_data['choices'][0]['message']['content'].strip()
                if callback:
                    callback(ai_response)
                return ai_response
            else:
                logging.warning("Invalid response from Gen-AI API")
                if callback:
                    callback(_("I'm having trouble thinking right now."))
    except Exception as e:
        logging.error(f"Error calling Gen-AI API: {str(e)}")
        if callback:
            callback(_("I can't connect to my AI brain right now. Let's chat the old way!"))


class Brain:
    def __init__(self, activity):
        self.activity = activity
        self.context = ''

    def load_brain(self, file_path):
        pass  # We don't need to load patterns if using Gen-AI

    def get_response(self, text):
        """Generate a response to the user input text."""
        if GENAI_ENABLED and GENAI_API_KEY:
            # Start a new thread to avoid blocking the UI
            threading.Thread(
                target=get_genai_response,
                args=(text, self.activity.face.say),
                daemon=True
            ).start()
            return _("Thinking...")  # Return immediately while API call runs
        else:
            # Fall back to original brain logic
            return self._get_legacy_response(text)

    def _get_legacy_response(self, text):
        """The original pattern-matching chatbot logic"""
        # Clean the input text
        text = text.lower()
        text = re.sub(r'[^\w\s]', ' ', text)
        text = text.replace('  ', ' ')
        
        # Simple pattern matching for responses
        if text.strip() == '':
            return _("Please type something.")
        
        if 'hello' in text or 'hi' in text:
            return random.choice([
                _("Hello!"),
                _("Hi there!"),
                _("Hey!")
            ])
        
        if 'how are you' in text:
            return random.choice([
                _("I'm doing well, thank you!"),
                _("I'm fine, how are you?"),
                _("I'm great!")
            ])
        
        if 'name' in text:
            return _("My name is Speak!")
        
        if 'weather' in text:
            return _("I don't know about the weather, I'm indoors.")
        
        if 'bye' in text or 'goodbye' in text:
            return random.choice([
                _("Goodbye!"),
                _("See you later!"),
                _("Bye bye!")
            ])
        
        # Default responses
        return random.choice([
            _("That's interesting. Tell me more."),
            _("I'm not sure I understand."),
            _("Can you explain that differently?"),
            _("Let's talk about something else."),
            _("That's cool!")
        ])