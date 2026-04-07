#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Dec 19 11:43:05 2018
@author: juliengautier
@author: SemionTche
"""

from PyQt6.QtWidgets import QApplication, QVBoxLayout, QHBoxLayout, QWidget, QGridLayout
from PyQt6.QtWidgets import QCheckBox, QLabel, QSizePolicy,QDoubleSpinBox, QSlider
from PyQt6 import QtCore, QtGui
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QShortcut
from PyQt6.QtGui import QIcon
import sys
import time
import pyqtgraph as pg  # pyqtgraph biblio permettent l'affichage
import numpy as np
import qdarkstyle  # pip install qdakstyle https://github.com/ColinDuquesnoy/QDarkStyleSheet  sur conda
#import pylab
import os
# from scipy.ndimage import gaussian_filter  # pour la reduction du bruit
from scipy.interpolate import splrep, sproot  # pour calcul fwhm et fit
import pathlib

from PIL import Image

class WINENCERCLED(QWidget):

    def __init__(self, parent=None, conf=None, name='VISU'):
        
        super().__init__() # heritage

        self.name = name
        self.parent = parent
        p = pathlib.Path(__file__)

        # set the config dictionary
        if conf is None:
            self.conf = QtCore.QSettings(str(p.parent / 'confVisu.ini'), QtCore.QSettings.Format.IniFormat)
        else:
            self.conf = conf
        
        sepa = os.sep # separator (depends on the os)
        self.icon = str(p.parent) + sepa + 'icons' + sepa # path to the icon folder

        # bool that indicates if the window is open for visual
        self.isWinOpen = False # keep this false or visual will make computation even if the window is not 'open' but only 'construct'
        
        # window config (geometry, title, ...)
        self.setWindowTitle('Encercled')
        self.setWindowIcon(QIcon(self.icon+'LOA.png'))
        self.setStyleSheet(qdarkstyle.load_stylesheet(qt_api='pyqt6'))
        self.left = 100
        self.top = 30
        self.width = 800
        self.height = 500
        self.setGeometry(self.left, self.top, self.width, self.height)

        # energy center coordinates
        self.xec = int(self.conf.value(self.name + "/xec"))
        self.yec = int(self.conf.value(self.name + "/yec"))
        # radius red circle
        self.rxFixed = int(self.conf.value(self.name + "/r1x"))
        self.ryFixed = int(self.conf.value(self.name + "/r1y"))

        self.isBlock = True # boolean that indicates if the cursors are blocked

        # default FWHM px
        self.fwhmX = 100 # px
        self.fwhmY = 100 # px
        self.FWHM_TO_GAUSS = 1/np.sqrt(2 * np.log(2)) # coefficient to multiply the FWHM to get the 1/e radius 
        
        # default picture
        self.dimx = 1200
        self.dimy = 900
        
        x = np.arange(0, self.dimx)
        y = np.arange(0, self.dimy)
        y, x = np.meshgrid(y, x)
        # self.data = (40*np.random.rand(self.dimx, self.dimy)).round()
        
        # path_focal_spot = "C:/Users/APPLI/Downloads/Focal_spot_laser/TachFocale_0001.TIFF"
        p = pathlib.Path(__file__)
        path_focal_spot = str(p.parent) + sepa + "tmp_TachFocale_0001.TIFF" # "C:/Users/APPLI/Documents/GitHub/camera_dummyClass/tmp_TachFocale_0001.TIFF"
        im = np.array(Image.open(path_focal_spot)).T
        self.data = im + np.random.randint(0, im.max()/10, im.shape)
        
        self.setup()
        self.ActionButton()
        self.AutoE()
        self.Display(self.data)

        # continuous flow of data
        if self.parent is not None:
            self.parent.signalEng.connect(self.Display)
    
    @property
    def rx(self):
        if self.fwhmX is not None:
            return self.fwhmX * self.FWHM_TO_GAUSS # px
        else:
            return 100 * self.FWHM_TO_GAUSS

    @property
    def ry(self):
        if self.fwhmY is not None:
            return self.fwhmY * self.FWHM_TO_GAUSS # px
        else:
            return 100 * self.FWHM_TO_GAUSS

    def setup(self):
        
        # togle design
        TogOff = self.icon+'Toggle_Off.png'
        TogOn = self.icon+'Toggle_On.png'       
        TogOff = pathlib.Path(TogOff)
        TogOff = pathlib.PurePosixPath(TogOff)
        TogOn = pathlib.Path(TogOn)
        TogOn = pathlib.PurePosixPath(TogOn)
        self.setStyleSheet("QCheckBox::indicator{width: 30px;height: 30px;}"
                           "QCheckBox::indicator:unchecked { image : url(%s);}"
                           "QCheckBox::indicator:checked { image:  url(%s);}"
                           "QCheckBox{font :10pt;}" % (TogOff, TogOn))
        
        ### right panel #########################################################
        vbox1 = QVBoxLayout() # vertical box on the right part of the panel
        # auto and bg togle
        hbox = QHBoxLayout()
        self.checkBoxAuto = QCheckBox('Auto max', self)
        self.checkBoxAuto.setChecked(True)
        hbox.addWidget(self.checkBoxAuto)
        self.bckButton = QCheckBox('Soustract Bg', self)
        hbox.addWidget(self.bckButton)
        vbox1.addLayout(hbox)
        # centred togle
        hbox0 = QHBoxLayout()
        self.checkBoxCentred = QCheckBox('Auto scale', self)
        self.checkBoxCentred.setChecked(True)
        hbox0.addWidget(self.checkBoxCentred)
        vbox1.addLayout(hbox0)
        
        # initial laser values
        init_energy_mJ = 60 # float(self.conf.value(self.name + "/init_energy_mJ"))
        init_duration_fs = 28 # float(self.conf.value(self.name + "/init_duration_fs"))
        init_peak_power_TW = init_energy_mJ / init_duration_fs
        # laser energy - label and box
        energyLabel = QLabel ('Energy (mJ)')
        self.energyLaserBox = QDoubleSpinBox() # for the value
        self.energyLaserBox.setValue(init_energy_mJ)
        self.energyLaserBox.setRange(0, 9999)
        # transmission coefficient - label and box
        transmissionLabel = QLabel ('Transmission')
        self.transmissionBox = QDoubleSpinBox() # for the value
        self.transmissionBox.setValue(1)
        self.transmissionBox.setRange(0, 1)
        self.transmissionBox.setSingleStep(0.01)
        # laser duration - label and box
        durationLabel = QLabel ('Duration (fs FWHM)')
        self.durationLaserBox = QDoubleSpinBox() # for the value
        self.durationLaserBox.setValue(init_duration_fs)
        self.durationLaserBox.setMinimum(0.1)
        # peak power - label and box
        peakPowerLabel = QLabel("Peak Power (TW)")
        self.PeakPowerBox = QLabel() # for the value
        self.PeakPowerBox.setText(f"{init_peak_power_TW:.2f}")
        # intensity - main label, in circle and FWHM
        intensityLabel = QLabel("Intensity ( x 10^18 W / cm2 ) :")
        intensityDiskLabel = QLabel("in circle (filtered)") # in circle (filtered)
        self.intensityDisk = QLabel() # for the value
        intensityFWHMLabel = QLabel("Gaussian") # gaussian
        self.intensityFWHM = QLabel() # for the value
        # beam size - x and y FWHM
        sizeXFWHMLabel = QLabel(f" x FWHM (um)")
        self.sizeXFWHM = QLabel() # for the value
        sizeYFWHMLabel = QLabel("y FWHM (um)")
        self.sizeYFWHM = QLabel() # for the value
        # radius circle
        radiusCircleLabel = QLabel("Radius circle (um)")
        self.radiusCircle = QDoubleSpinBox() # for the value
        self.radiusCircle.setRange(0.1, 2000)
        # default calibration
        if self.parent is None : 
            pixelX = pixelY = 1. # px / um
        else :
            pixelX = self.parent.winPref.stepX # um / px
            pixelY = self.parent.winPref.stepY
        # calibration
        self.calibrationXLabel = QLabel("calibration X (um / px)")
        self.calibrationX = QDoubleSpinBox() # for the value
        self.calibrationX.setValue(pixelX)
        self.calibrationX.setMinimum(0.1)
        self.calibrationX.setSingleStep(0.01)
        self.calibrationYLabel = QLabel("calibration Y (um / px)")
        self.calibrationY = QDoubleSpinBox() # for the value
        self.calibrationY.setValue(pixelY)
        self.calibrationY.setMinimum(0.1)
        self.calibrationY.setSingleStep(0.01)
        # threshold circle
        thresholdCircleLabel = QLabel('Threshold circle')
        self.thresholdCircle = QDoubleSpinBox()
        self.thresholdCircle.setValue(0.05)
        self.thresholdCircle.setRange(0., 0.99)
        self.thresholdCircle.setSingleStep(0.01)
        
        # add to window
        grid_layout1 = QGridLayout()
        # laser energy
        grid_layout1.addWidget(energyLabel, 0, 0)
        grid_layout1.addWidget(self.energyLaserBox, 0, 1)
        # transmission coefficient
        grid_layout1.addWidget(transmissionLabel, 1, 0)
        grid_layout1.addWidget(self.transmissionBox, 1, 1)
        # laser duration
        grid_layout1.addWidget(durationLabel, 2, 0)
        grid_layout1.addWidget(self.durationLaserBox, 2, 1)
        # peak power
        grid_layout1.addWidget(peakPowerLabel, 3, 0)
        grid_layout1.addWidget(self.PeakPowerBox, 3, 1)
        # intensity
        grid_layout1.addWidget(QLabel(), 4, 0) # skip a line
        grid_layout1.addWidget(intensityLabel, 5, 0)
        grid_layout1.addWidget(intensityDiskLabel, 6, 0)
        grid_layout1.addWidget(self.intensityDisk, 6, 1)
        grid_layout1.addWidget(intensityFWHMLabel, 7, 0)
        grid_layout1.addWidget(self.intensityFWHM, 7, 1)
        # beam size x and y FWHM
        grid_layout1.addWidget(QLabel(), 8, 0) # skip a line
        grid_layout1.addWidget(sizeXFWHMLabel, 9, 0)
        grid_layout1.addWidget(self.sizeXFWHM, 9, 1)
        grid_layout1.addWidget(sizeYFWHMLabel, 10, 0)
        grid_layout1.addWidget(self.sizeYFWHM, 10, 1)
        # radius circle
        grid_layout1.addWidget(radiusCircleLabel, 11, 0)
        grid_layout1.addWidget(self.radiusCircle, 11, 1)
        # calibration
        grid_layout1.addWidget(QLabel(), 12, 0)
        grid_layout1.addWidget(self.calibrationXLabel, 13, 0)
        grid_layout1.addWidget(self.calibrationX, 13, 1)
        grid_layout1.addWidget(self.calibrationYLabel, 14, 0)
        grid_layout1.addWidget(self.calibrationY, 14, 1)
        # threshold circle
        grid_layout1.addWidget(thresholdCircleLabel, 15, 0)
        grid_layout1.addWidget(self.thresholdCircle, 15, 1)
        
        vbox1.addLayout(grid_layout1) # add the grid in the right panel
        vbox1.addStretch(1)

        # brightness
        grid_layout_brightness = QGridLayout()
        grid_layout_brightness.addWidget(QLabel(), 0, 0) # skip a line
        brightnessLabel = QLabel("Brightness:")
        grid_layout_brightness.addWidget(brightnessLabel, 1, 0)
        self.brightnessSlider = QSlider(Qt.Orientation.Horizontal)
        self.brightnessSlider.setRange(0, 100)
        self.brightnessSlider.setValue(50)
        grid_layout_brightness.addWidget(self.brightnessSlider, 2, 0)
        self.brightnessBox = QDoubleSpinBox()
        self.brightnessBox.setRange(0, 100)
        self.brightnessBox.setValue(self.brightnessSlider.value()) 
        grid_layout_brightness.addWidget(self.brightnessBox, 2, 1)
        vbox1.addLayout(grid_layout_brightness)
        # vbox1.addWidget(self.brightnessSlider)

        # FWHM
        # self.r1xBox = QSpinBox()
        # self.r1xBox.setMaximum(2000)
        # LabelR1y = QLabel('fwhm Y/0.85')
        # LabelR1y.setStyleSheet("color:green;font:14pt")
        # self.r1yBox = QSpinBox()
        # self.r1yBox.setMaximum(2000)

        # grid_layout1.addWidget(self.r1xBox, 13, 1)
        # grid_layout1.addWidget(LabelR1y, 14, 0)
        # grid_layout1.addWidget(self.r1yBox, 14, 1)

        ### image and curves #########################################################
        vbox2 = QVBoxLayout()

        self.winImage = pg.GraphicsLayoutWidget()    # graphic panel
        self.winImage.setContentsMargins(0, 0, 0, 0) # use all the space
        self.winImage.setAspectLocked(True)          # preserve the aspect ratio (width, height)
        self.winImage.setSizePolicy(QSizePolicy.Policy.MinimumExpanding, 
                                    QSizePolicy.Policy.MinimumExpanding) # size behavior
        
        # horizontal box to add to proced as in the right panel
        # hbox2 = QHBoxLayout()
        # hbox2.addWidget(self.winImage)
        vbox2.addWidget(self.winImage)
        vbox2.setContentsMargins(0, 0, 0, 0) # use all the space for the vertical box
        
        # figure setup
        self.plotItem = self.winImage.addPlot() # figure over which the data and curves will be plot
        self.imh = pg.ImageItem()
        self.plotItem.addItem(self.imh) # add an image on the figure (2D plot)
        self.plotItem.setAspectLocked(True, ratio=1)
        self.plotItem.setMouseEnabled(x=False, y=False)
        self.plotItem.setContentsMargins(0, 0, 0, 0) # use all the space for the figure
        
        # disable axis
        self.plotItem.showAxis('right', show=False)
        self.plotItem.showAxis('top', show=False)
        self.plotItem.showAxis('left', show=False)
        self.plotItem.showAxis('bottom', show=False)

        # add lines to identify the center of the beam
        self.vLine = pg.InfiniteLine(angle=90, movable=False, pen='w')
        self.hLine = pg.InfiniteLine(angle=0, movable=False, pen='w')
        self.plotItem.addItem(self.vLine)
        self.plotItem.addItem(self.hLine)
        self.vLine.setPos(self.xec)
        self.hLine.setPos(self.yec)
        
        # add a circle
        self.circle = pg.CircleROI([self.xec, self.yec], 
                                   [2 * self.rx, 2 * self.ry], 
                                   pen='r', movable=False)
        self.circle.setPos([self.xec - self.rxFixed, 
                            self.yec - self.ryFixed])
        self.plotItem.addItem(self.circle)
               
        # histogramme
        self.hist = pg.HistogramLUTItem() 
        self.hist.setImageItem(self.imh)
        self.hist.autoHistogramRange()
        self.hist.gradient.loadPreset('flame')
        
        # 1D curves
        self.curveAlongX = pg.PlotCurveItem()
        self.curveAlongY = pg.PlotCurveItem()
        self.plotItem.addItem(self.curveAlongX)
        self.plotItem.addItem(self.curveAlongY)
        # text to display FWHM on the plotItem
        self.textY = pg.TextItem(angle=-90)
        self.textX = pg.TextItem()
        self.plotItem.addItem(self.textY)
        self.plotItem.addItem(self.textX)
        
        # ROI for local background substraction
        self.ROIRect = pg.RectROI([self.xec, self.yec], 
                                  [2 * self.rx, 2 * self.ry], pen='m')
        
        # group the two vertical boxes
        hLayout1 = QHBoxLayout()
        hLayout1.addLayout(vbox2)
        hLayout1.addLayout(vbox1)
        # hLayout1.setContentsMargins(0, 0, 0, 0)
        hLayout1.setContentsMargins(1, 1, 1, 1)
        
        # creates the main layout
        vMainLayout = QVBoxLayout()
        vMainLayout.addLayout(hLayout1)

        hMainLayout = QHBoxLayout()
        hMainLayout.addLayout(vMainLayout)
        self.setLayout(hMainLayout)
        self.setContentsMargins(1, 1, 1, 1)
        # self.setContentsMargins(0, 0, 0, 0)

        
    def ActionButton(self):
        # block the mouse
        self.circle.sigRegionChangeFinished.connect(self.energSouris)  # modification of the size of the circle

        # self.r1xBox.editingFinished.connect(self.Rayon)  # w.r1Box.returnPressed.connect(Rayon)# rayon change a la main
        # self.r1yBox.editingFinished.connect(self.Rayon)
        self.radiusCircle.valueChanged.connect(self.Rayon)  # w.r1Box.returnPressed.connect(Rayon)# rayon change a la main

        # shortcut block and unblock
        self.shortcutb = QtGui.QShortcut(QtGui.QKeySequence("Ctrl+b"), self)
        self.shortcutb.activated.connect(self.bloquer)
        self.shortcutd = QtGui.QShortcut(QtGui.QKeySequence("Ctrl+d"), self)
        self.shortcutd.activated.connect(self.debloquer)
        
        # shortcut brightness + and -
        self.shortcutPu = QShortcut(QtGui.QKeySequence("+"), self)
        self.shortcutPu.activated.connect(self.paletteup)
        self.shortcutPu.setContext(Qt.ShortcutContext(3))
        self.shortcutPd = QtGui.QShortcut(QtGui.QKeySequence("-"), self)
        self.shortcutPd.activated.connect(self.palettedown)
        self.shortcutPd.setContext(Qt.ShortcutContext(3)) # The shortcut is active when its parent widget, or any of its children has focus.
        # default 'O' The shortcut is active when its parent widget has focus.

        # input changes
        self.calibrationX.valueChanged.connect(self.changeInputs)
        self.calibrationY.valueChanged.connect(self.changeInputs)
        self.energyLaserBox.valueChanged.connect(self.changeInputs)
        self.transmissionBox.valueChanged.connect(self.changeInputs)
        self.durationLaserBox.valueChanged.connect(self.changeInputs)
        self.thresholdCircle.valueChanged.connect(self.changeInputs)

        # auto button
        self.checkBoxAuto.stateChanged.connect(lambda: self.Display(self.data)) # update display
        self.checkBoxAuto.stateChanged.connect(self.AutoE)
        # self.checkBoxAuto.stateChanged.connect(self.radiusFixed)
        
        # centred button
        self.checkBoxCentred.stateChanged.connect(lambda: self.Display(self.data)) # update display

        # mouse mouvement
        self.proxy = pg.SignalProxy(self.plotItem.scene().sigMouseMoved, rateLimit=60, slot=self.mouseMoved)
        self.plotItem.scene().sigMouseClicked.connect(self.mouseClick)
        self.vb = self.plotItem.vb
        
        # background button
        self.bckButton.stateChanged.connect(self.Back)
        # ROI background change of size
        self.ROIRect.sigRegionChangeFinished.connect(self.roiBackChanged)

        # birghtnessSlider
        self.brightnessSlider.valueChanged.connect(self.updateBrightness)
        self.brightnessBox.valueChanged.connect(self.updateBrightnessBox)

    def mouseClick(self):
        # bloque ou debloque la souris si click su le graph
        if self.isBlock is True:
            self.debloquer()
        else:
            self.bloquer() 
            
    def bloquer(self):  # bloque la croix 
        self.isBlock = True
        self.computeIntensity()
        
    def debloquer(self):  # debloque la croix : elle bouge avec la souris
        self.isBlock = False
    
    # mvt de la souris
    
    def mouseMoved(self, evt):
        # pour que la cross suive le mvt de la souris
        if self.checkBoxAuto.isChecked() is False:

            if self.isBlock is False:  # souris non bloquer
                pos = evt[0]  # using signal proxy turns original arguments into a tuple
                if self.plotItem.sceneBoundingRect().contains(pos):
                    mousePoint = self.vb.mapSceneToView(pos)
                    self.xec = int(mousePoint.x())
                    self.yec = int(mousePoint.y())
                    if ((self.xec > 0 and self.xec < self.data.shape[0]) and (self.yec > 0 and self.yec < self.data.shape[1])):
                        self.vLine.setPos(self.xec)
                        self.hLine.setPos(self.yec)  # la croix ne bouge que dans le graph
                        self.circle.setPos([self.xec - self.rxFixed, 
                                            self.yec - self.ryFixed])
                            
    def AutoE(self):
        if self.checkBoxAuto.isChecked() is False:
            self.radiusCircle.setEnabled(True)
            self.energSouris()
            self.circle.setSize([2 * self.rxFixed, 
                                 2 * self.ryFixed])
        else:
            self.radiusCircle.setEnabled(False)
            
    def energSouris(self):  # changement des rayons à la souris 
        sizeX, sizeY = self.circle.size()
        radiusX, radiusY = sizeX/2, sizeY/2
        pixelX = self.calibrationX.value() # um / px
        pixelY = self.calibrationY.value()
        pixel = np.mean([pixelX, pixelY])
        radius = np.mean([radiusX, radiusY]) * pixel # um
        self.radiusCircle.setValue(radius)
        
        if self.checkBoxAuto.isChecked() is False:
            # self.r1xBox.setValue((int(s1[0]/2)))
            # self.r1yBox.setValue((int(s1[1]/2)))
            # self.r1x = int(s1[0]/2)
            # self.r1y = int(s1[1]/2)
            if self.isBlock is True:
                self.computeIntensity()

    # def Rayon(self): 
    #     """changement rayon dans les box
    #     """
    #     if self.checkBoxAuto.isChecked() is False:
    #         if self.r1xBox.hasFocus():
    #             self.r1x = (float(self.r1xBox.text()))
    #             self.circle.setSize([2*self.r1x, 2*self.r1y])
    #         if self.r1yBox.hasFocus():
    #             self.r1y = (float(self.r1yBox.text()))
    #             self.circle.setSize([2*self.r1x, 2*self.r1y])
            
    #         self.circle.setPos([self.xec-(self.r1x), self.yec-(self.r1y)])
    #         if self.isBlock is True:
    #             self.computeIntensity()
    
    def Rayon(self): 
        """changement rayon dans les box
        """
        if self.checkBoxAuto.isChecked() is False:
            pixelX = self.calibrationX.value()
            pixelY = self.calibrationY.value()
            pixel = np.mean([pixelX, pixelY])
            radius = self.radiusCircle.value() / pixel # radius in px
            self.circle.setSize([2 * radius, 2 * radius])
            
            self.circle.setPos([self.xec - radius, 
                                self.yec- radius])
            
            self.computeIntensity()
    
    def changeInputs(self):
        self.Coupe()
        self.computeIntensity()

    def computeIntensity(self):
        
        if self.checkBoxAuto.isChecked():
            # self.r1xBox.setValue(int(self.r1x))
            # self.r1yBox.setValue(int(self.r1y))
            # nbG = 2  # ré= 2 fois r1 pour le grand cercle
            self.rxFixed = self.rx
            self.ryFixed = self.ry

            self.circle.setSize([2 * self.rxFixed, # size = diameter = rx (which is the waist) 
                                 2 * self.rxFixed]) # but it's to small so double the size
            self.circle.setPos([self.xec - self.rxFixed, 
                                self.yec - self.rxFixed]) # center the circle
        # else:
        #     self.rxFixed = self.rxFixed
        #     self.ryFixed = self.ryFixed
        #     self.circle.setSize([2 * self.rxFixed, 
        #                          2 * self.ryFixed]) # size = diameter = 2 * radius
        #     self.circle.setPos([self.xec - self.rxFixed, 
        #                         self.yec - self.ryFixed]) # center the circle
            # self.r1x = self.r1x
            # self.r1y = self.r1y
                # get calibration value
        
        pixelX = 1 / self.calibrationX.value() # px / um
        pixelY = 1 / self.calibrationY.value() # px / um
        
        if self.fwhmX is not None :
            self.textX.setText('fwhm='+f"{self.fwhmX / pixelX:.2f}")
        else:
            self.textX.setText('fwhm='+f"{self.fwhmX}")
        if self.fwhmY is not None:
            self.textY.setText('fwhm='+f"{self.fwhmY / pixelY:.2f}")
        else:
            self.textY.setText('fwhm='+f"{self.fwhmY}")
        
        # compute power
        laserEnergy = self.energyLaserBox.value() * 1e-3 # J
        transmission = self.transmissionBox.value()
        laserEffective = laserEnergy * transmission
        laserDuration = self.durationLaserBox.value() * 1e-15 # fwhm - s 
        peakPowerTW = laserEffective / laserDuration * 1e-12
        self.PeakPowerBox.setText(f"{peakPowerTW:.2f}")
        
        # intensity circled:
        circleSize = self.circle.size() # px - x and y
        radius = circleSize / 2 # px - x and y
        area_px2 = np.pi * radius[0] * radius[1] # circle area in px^2
        area_cm2 = area_px2 / pixelX / pixelY * 1e-8 # circle area in cm^2
        intensity = (laserEffective / area_cm2 / laserDuration) * 1e-18 # intensity in the red circle without filter
        
        # disk filtered
        disk = self.circle.getArrayRegion(self.data, self.imh) # get the data in the circle
        diskNorm = disk / np.max(disk) # normalized it
        threshold = self.thresholdCircle.value() # get the threshold value
        disk_filtered = np.where(diskNorm > threshold, 1, 0) # filter the data
        disk_area_px2 = disk_filtered.sum() # integrate the number of px
        disk_area_cm2 = disk_area_px2 / pixelX / pixelY * 1e-8 # convert it in cm^2
        intensity_disk = (laserEffective / disk_area_cm2 / laserDuration) * 1e-18 # compute the intensity in circle filtered
        # self.intensityDisk.setText(f"{intensity_disk:.2f}") # update the layout

        # disk weighted
        disk = self.circle.getArrayRegion(self.data, self.imh)
        diskNorm = disk / np.max(disk)
        disk_area_px2 = np.where(diskNorm > threshold, diskNorm, 0).sum()
        disk_area_cm2 = disk_area_px2 / pixelX / pixelY * 1e-8
        intensity_disk = peakPowerTW / disk_area_cm2 * 1e-6
        self.intensityDisk.setText(f"{intensity_disk:.2f}")

        # intensity gaussian:
        fwhm_x_cm = (self.fwhmX / pixelX) * 1e-4
        fwhm_y_cm = (self.fwhmY / pixelY) * 1e-4
        area_fwhm_cm2 = fwhm_x_cm * fwhm_y_cm
        wprod_cm2 = area_fwhm_cm2 * (self.FWHM_TO_GAUSS ** 2)
        intensity_gaussian = 2.0 * peakPowerTW / (np.pi * wprod_cm2) * 1e-6 # 10^18 W/cm2
        self.intensityFWHM.setText(f"{intensity_gaussian:.2f}") # update the layout


    def Display(self, data):
        self.dataOrg = data
        self.data = data
        
        self.dimx = self.data.shape[0]
        self.dimy = self.data.shape[1]
        
        self.plotItem.setXRange(0, self.dimx)
        self.plotItem.setYRange(0, self.dimy)
        
        self.plotItem.setAspectLocked(True, ratio=1)
        
        if not self.checkBoxCentred.isChecked():
            self.plotItem.enableAutoRange(False) # prevent the zoom pattern
        self.imh.setImage(data.astype(float), autoLevels=True, autoDownsample=True)
        
        # brightness levels
        levels = self.imh.getLevels()
        if levels[0] is None:
            self.base_xmin = float(self.data.min())
            self.base_xmax = float(self.data.max())
        else:
            self.base_xmin = float(levels[0])
            self.base_xmax = float(levels[1])

        self.computeCentroid()
        self.Coupe()
        self.Back()
        self.updateBrightness(self.brightnessBox.value())
    
    def computeCentroid(self):
        if self.checkBoxAuto.isChecked():
            # dataF = gaussian_filter(self.data, 5) # apply a gaussian filter
            dataF = self.data
            (self.xec, self.yec) = np.unravel_index(dataF.argmax(), self.data.shape) # get the maximum
            self.vLine.setPos(self.xec) # set the cursors
            self.hLine.setPos(self.yec)   
            self.circle.setPos([self.xec - self.rxFixed, 
                                self.yec - self.ryFixed]) # set the circle
        
    def computeFWHM(self, x, y, order=3):
        """
        Determine full-with-half-maximum of a peaked set of points, x and y.
        Assumes that there is only one peak present in the datasset.  
        The function uses a spline interpolation of order k. 
        """
        
        # y = gaussian_filter(y, 5)  # filtre pour reduire le bruit
        half_max = np.amax(y)/2
        try:
            s = splrep(x, y - half_max, k=order)  # Find the B-spline representation of 1-D curve.
            roots = sproot(s)  # Given the knots (>=8) and coefficients of a cubic B-spline return the roots of the spline.
        except:
            roots = 0
           
        if len(roots) > 2:
            pass
            # print( "The dataset appears to have multiple peaks, and ","thus the FWHM can't be determined.")
        elif len(roots) < 2:
            pass
            #  print( "No proper peaks were found in the data set; likely ","the dataset is flat (e.g. all zeros).")
        else:
            return np.around(abs(roots[1] - roots[0]), decimals=2)
    
    def Coupe(self):
        xxx = np.arange(0, int(self.dimx), 1)
        yyy = np.arange(0, int(self.dimy), 1)
        
        coupeX = self.data[int(self.xec),:]
        coupeXMax = np.max(coupeX)
        
        if coupeXMax == 0:  # evite la div par zero
            coupeXMax = 1
            
        coupeXnorm = (self.data.shape[0]/10)*(coupeX/coupeXMax)  # normalise les coupes pour pas prendre tout l ecran
        self.curveAlongX.setData(coupeXnorm, yyy, clear=True)
        
        coupeY = self.data[:, int(self.yec)]
        coupeYMax = np.max(coupeY)
        if coupeYMax == 0:
            coupeYMax = 1
            
        coupeYnorm = (self.data.shape[1]/10)*(coupeY/coupeYMax)
        self.curveAlongY.setData(xxx, 20 + coupeYnorm, clear=True)
        
        # affichage de fwhm sur les coupes X et Y que si le max est > 15 counts
        xCXmax = np.amax(coupeXnorm)  # max
        # if xCXmax > 15:
        pixelY = self.calibrationY.value()  # um / px
        self.fwhmY = self.computeFWHM(yyy, coupeXnorm, order=3)
        if self.fwhmY is not None:
            self.sizeYFWHM.setText(f"{self.fwhmY * pixelY:.2f}")
        else:
            self.sizeYFWHM.setText(f"{self.fwhmY}")
        yCXmax = yyy[coupeXnorm.argmax()]
        self.textY.setPos(xCXmax-3, yCXmax+3)
            
        yCYmax = np.amax(coupeYnorm)  # max
        # if yCYmax > 15:
        pixelX = self.calibrationX.value() # um / px
        self.fwhmX = self.computeFWHM(xxx, coupeYnorm, order=3)
        if self.fwhmX is not None:
            self.sizeXFWHM.setText(f"{self.fwhmX * pixelX:.2f}")
        else:
            self.sizeXFWHM.setText(f"{self.fwhmX}")
        xCYmax = xxx[coupeYnorm.argmax()]            
        self.textX.setPos(xCYmax-3, yCYmax+3)

    def updateBrightnessBox(self):
        self.brightnessSlider.setValue(int(self.brightnessBox.value()))
        self.updateBrightness(self.brightnessBox.value())

    def updateBrightness(self, val):
        self.brightnessBox.setValue(self.brightnessSlider.value())
        xmin = self.base_xmin
        
        span = self.base_xmax - self.base_xmin
        factor = (val - 50) / 50.0
        xmax = self.base_xmax - factor * span 

        if xmax <= xmin:
            xmax = xmin + 1e-9

        self.imh.setLevels([xmin, xmax])
        self.hist.setHistogramRange(xmin, xmax)

    def paletteup(self):
        # levels = self.imh.getLevels()
        # if levels[0] is None:
        #     xmax = self.data.max()
        #     xmin = self.data.min()
        # else:
        #     xmax = levels[1]
        #     xmin = levels[0]
            
        # self.imh.setLevels([xmin, xmax - (xmax - xmin) / 10])
        # # self.hist.setImageItem(self.imh,clear=True)
        # self.hist.setHistogramRange(xmin, xmax)
        self.brightnessSlider.setValue(self.brightnessSlider.value() + 1)

    def palettedown(self):
        # levels = self.imh.getLevels()
        # if levels[0] is None:
        #     xmax = self.data.max()
        #     xmin = self.data.min()
        # else:
        #     xmax = levels[1]
        #     xmin = levels[0]
            
        # self.imh.setLevels([xmin, xmax + (xmax - xmin) / 10])
        # # hist.setImageItem(imh,clear=True)
        # self.hist.setHistogramRange(xmin, xmax)
        self.brightnessSlider.setValue(self.brightnessSlider.value() - 1)

    def roiBackChanged(self):
        bg = self.ROIRect.getArrayRegion(self.dataOrg, self.imh).mean()
        self.data = np.where( self.dataOrg - bg > 0, self.dataOrg - bg, 0 ) # return bg substration except if negative return 0
        self.computeIntensity()
    
    def Back(self):
        if self.bckButton.isChecked():
            if self.ROIRect not in self.plotItem.items:
                self.plotItem.addItem(self.ROIRect)
            self.roiBackChanged()
        else:
            if self.ROIRect in self.plotItem.items:
                self.plotItem.removeItem(self.ROIRect)
                self.data = self.dataOrg
            self.computeIntensity()
              
    def closeEvent(self, event):
        """ 
        when closing the window
        """
        self.isWinOpen = False
        time.sleep(0.1)
        event.accept()
     
        
if __name__ == "__main__":
    appli = QApplication(sys.argv) 
    appli.setStyleSheet(qdarkstyle.load_stylesheet(qt_api='pyqt6'))
    e = WINENCERCLED(name='VISU')
    e.show()
    appli.exec_()
