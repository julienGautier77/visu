#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Mar 18 10:50:06 2019
Data vizualisation
@author: juliengautier
"""

from visu import visual
from visu import visualLight
from visu.visualLight import SEELIGHT
from visu.visualLightThread import SEELIGHTTHREAD
from visu.visual import SEE
from visu.visual import runVisu
from visu import andor
from visu import WinCut
from visu import winMeas
from visu import winspec
from visu import winSuppE
from visu import winFFT
from visu import winZoom
try:
    from visu import Win3D
except :
    print('no 3D available')
#from visu import moteurRSAI as RSAI
__version__='2020.06'