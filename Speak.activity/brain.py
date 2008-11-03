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

import aiml
from gettext import gettext as _

class defaultBrain:
    def __init__(self, voice):
        self.language = voice.language 
	self.kernel = aiml.Kernel()

	if self.language=="es":
            self.kernel.loadBrain("sara.brn")
	    self.kernel.setBotPredicate("nombre_bot","Sara")
	    self.kernel.setBotPredicate("botmaster","la comunidad Azucar")
	elif self.language=="en-uk":
            self.kernel.loadBrain("alice.brn")
	    self.kernel.setBotPredicate("name","Alice")
	    self.kernel.setBotPredicate("master","the Sugar Community")
	else:
            self.kernel.respond = lambda x: x

    def respond(self, text):
        return self.kernel.respond(text)
