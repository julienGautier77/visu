#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Wavelength calibration of the X axis : two reference wavelengths and
their position in pixel give a linear law  lambda = offset + slope * pixel

@author: juliengautier
"""

import qdarkstyle
import pyqtgraph as pg
from math import ceil
import numpy as np
from PyQt6 import QtCore
from PyQt6.QtWidgets import QApplication, QGridLayout, QLabel, QDoubleSpinBox, QWidget
from PyQt6.QtGui import QIcon
import sys
import os
import pathlib


class CalibAxisItem(pg.AxisItem):
    ''' AxisItem with an offset : tick value displayed = offset + scale * value
    (pg.AxisItem.setScale only allows a multiplicative factor)
    with offset = 0 it behaves exactly like pg.AxisItem
    '''

    def __init__(self, *args, **kwds):
        super().__init__(*args, **kwds)
        self.offset = 0

    def setOffset(self, offset=0):
        if offset != self.offset:
            self.offset = offset
            self.picture = None
            self.update()

    def tickValues(self, minVal, maxVal, size):
        if self.offset == 0 or self.logMode or self.scale == 0:
            return super().tickValues(minVal, maxVal, size)
        # ticks computed in displayed unit then converted back in view coordinate
        uMin, uMax = sorted((self.offset + self.scale * minVal, self.offset + self.scale * maxVal))
        ticks = []
        allValues = np.array([])
        for spacing, off in self.tickSpacing(uMin, uMax, size):
            start = (ceil((uMin - off) / spacing) * spacing) + off
            num = int((uMax - start) / spacing) + 1
            values = np.arange(num) * spacing + start
            close = np.any(np.isclose(allValues, values[:, np.newaxis], rtol=0, atol=spacing*0.01), axis=-1)
            values = values[~close]
            allValues = np.concatenate([allValues, values])
            ticks.append((spacing / abs(self.scale), ((values - self.offset) / self.scale).tolist()))
        return ticks

    def tickStrings(self, values, scale, spacing):
        if self.offset == 0 or self.logMode or scale == 0:
            return super().tickStrings(values, scale, spacing)
        return super().tickStrings([v + self.offset / scale for v in values], scale, spacing)


class WINLAMBDA(QWidget):
    ''' widget to enter two wavelengths (nm) and their position (pixel)
    '''

    signalChange = QtCore.pyqtSignal(bool)

    def __init__(self, conf=None, name='VISU'):

        super().__init__()

        p = pathlib.Path(__file__)
        if conf is None:
            self.conf = QtCore.QSettings(str(p.parent / 'confVisu.ini'), QtCore.QSettings.Format.IniFormat)
        else:
            self.conf = conf
        self.name = name
        sepa = os.sep
        self.icon = str(p.parent) + sepa + 'icons' + sepa
        self.isWinOpen = False
        self.setStyleSheet(qdarkstyle.load_stylesheet(qt_api='pyqt6'))
        self.setWindowTitle('Wavelength calibration')
        self.setWindowIcon(QIcon(self.icon + 'LOA.png'))

        self.lambda1 = float(self.conf.value(self.name + "/lambda1", 400))
        self.pixel1 = float(self.conf.value(self.name + "/lambdaPixel1", 0))
        self.lambda2 = float(self.conf.value(self.name + "/lambda2", 800))
        self.pixel2 = float(self.conf.value(self.name + "/lambdaPixel2", 1000))
        self.calcCoef()
        self.setup()
        self.actionButton()

    def setup(self):

        grid = QGridLayout()
        grid.addWidget(QLabel('Wavelength (nm)'), 0, 1)
        grid.addWidget(QLabel('Position (pixel)'), 0, 2)

        self.lambda1Box = self.spinBox(self.lambda1)
        self.pixel1Box = self.spinBox(self.pixel1)
        self.lambda2Box = self.spinBox(self.lambda2)
        self.pixel2Box = self.spinBox(self.pixel2)

        grid.addWidget(QLabel('Point 1 :'), 1, 0)
        grid.addWidget(self.lambda1Box, 1, 1)
        grid.addWidget(self.pixel1Box, 1, 2)
        grid.addWidget(QLabel('Point 2 :'), 2, 0)
        grid.addWidget(self.lambda2Box, 2, 1)
        grid.addWidget(self.pixel2Box, 2, 2)

        self.labelCoef = QLabel()
        grid.addWidget(self.labelCoef, 3, 0, 1, 3)
        self.updateLabel()
        self.setLayout(grid)

    def spinBox(self, value):
        box = QDoubleSpinBox()
        box.setDecimals(3)
        box.setRange(-100000, 100000)
        box.setValue(value)
        return box

    def actionButton(self):
        for box in (self.lambda1Box, self.pixel1Box, self.lambda2Box, self.pixel2Box):
            box.valueChanged.connect(self.valueChange)

    def valueChange(self):
        self.lambda1 = self.lambda1Box.value()
        self.pixel1 = self.pixel1Box.value()
        self.lambda2 = self.lambda2Box.value()
        self.pixel2 = self.pixel2Box.value()
        self.conf.setValue(self.name + "/lambda1", self.lambda1)
        self.conf.setValue(self.name + "/lambdaPixel1", self.pixel1)
        self.conf.setValue(self.name + "/lambda2", self.lambda2)
        self.conf.setValue(self.name + "/lambdaPixel2", self.pixel2)
        self.calcCoef()
        self.updateLabel()
        self.signalChange.emit(True)

    def calcCoef(self):
        # lambda = offset + slope * pixel
        if self.pixel2 != self.pixel1:
            self.slope = (self.lambda2 - self.lambda1) / (self.pixel2 - self.pixel1)
        else:
            self.slope = 1  # the two pixels must be different
        self.offset = self.lambda1 - self.slope * self.pixel1

    def updateLabel(self):
        if self.pixel2 == self.pixel1:
            self.labelCoef.setText('the two positions must be different !')
        else:
            self.labelCoef.setText(f'dispersion = {round(self.slope, 5)} nm/pixel   lambda(0) = {round(self.offset, 3)} nm')

    def toLambda(self, pixel):
        lam = self.offset + self.slope * np.asarray(pixel, dtype=float)
        return float(lam) if lam.ndim == 0 else lam

    def closeEvent(self, event):
        """ when closing the window
        """
        self.isWinOpen = False


if __name__ == "__main__":
    appli = QApplication(sys.argv)
    e = WINLAMBDA()
    e.show()
    appli.exec()
