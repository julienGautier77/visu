#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Created on Mon Dec 18 11:23:52 2017

@author: juliengautier
"""
from PyQt5 import uic
import os,sys
from pyqtgraph.Qt import QtGui, QtCore


appli=QtGui.QApplication(sys.argv)
w=uic.loadUi("test.ui")

w.show()

appli.exec_()


if __name__=="__main":
    app.exec_()
    