#!/usr/bin/env python
#coding=utf-8

import aiml

k = aiml.Kernel()
import glob
laiml = glob.glob("sara/*.aiml") #devuelve lista con ficheros *.aiml
for fichero in laiml:
    k.learn(str(fichero))
k.saveBrain("sara.brn")

laiml = glob.glob("alice/*.aiml") #devuelve lista con ficheros *.aiml
for fichero in laiml:
    k.learn(str(fichero))
k.saveBrain("alice.brn")
