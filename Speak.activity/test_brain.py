#!/usr/bin/env python
#coding=utf-8

import aiml
import os.path

k = aiml.Kernel()
k.loadBrain("sara.brn")

while True: print k.respond(raw_input("Pregunta > ")) 
