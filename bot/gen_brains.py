#!/usr/bin/env python

# Copyright (C) 2008 Sebastian Silva Fundacion FuenteLibre sebastian@fuentelibre.org
#
# HablarConSara.activity is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# HablarConSara.activity is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with HablarConSara.activity.  If not, see <http://www.gnu.org/licenses/>.

# A simple hack to attach a chatterbot to speak activity
#coding=utf-8

import aiml
import glob

k = aiml.Kernel()
laiml = glob.glob("sara/*.aiml") #devuelve lista con ficheros *.aiml
for fichero in laiml:
    k.learn(str(fichero))
k.saveBrain("sara.brn")

k = aiml.Kernel()
laiml = glob.glob("alice/*.aiml") #devuelve lista con ficheros *.aiml
for fichero in laiml:
    k.learn(str(fichero))
k.saveBrain("alice.brn")

k = aiml.Kernel()
laiml = glob.glob("alisochka/*.aiml")
for fichero in laiml:
    k.learn(str(fichero))
k.saveBrain("alisochka.brn")
