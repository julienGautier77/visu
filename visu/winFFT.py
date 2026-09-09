#!/usr/bin/env python3
# -*- coding: utf-8 -*-


"""
Created on Mon May  6 11:24:23 2019
Windows for display FFT
@author: juliengautier

Interface refaite en 2026 sur le modèle de visualLight.py (SEELIGHT) :
QMainWindow avec menuBar (File/Image/Analyse/Zoom), toolBar d'icônes et
statusBar (position/valeur sous la croix, nom de fichier), au lieu d'une
sidebar de boutons empilés.
"""

import sys
import os
import time
import numpy as np
import qdarkstyle  # pip install qdakstyle https://github.com/ColinDuquesnoy/QDarkStyleSheet  sur conda
import pathlib

from PyQt6.QtWidgets import (QApplication, QVBoxLayout, QWidget,
                              QLabel, QSizePolicy, QMenu, QMessageBox,
                              QMainWindow, QStatusBar, QInputDialog, QFileDialog)
from PyQt6.QtGui import QShortcut, QAction, QIcon
from PyQt6 import QtCore, QtGui
from PyQt6.QtCore import Qt

import pyqtgraph as pg  # pip install pyqtgraph (https://github.com/pyqtgraph/pyqtgraph.git)

from scipy.interpolate import splrep, sproot
from scipy.ndimage.filters import gaussian_filter, median_filter
from PIL import Image
from visu.winspec import SpeFile
from visu.winSuppE import WINENCERCLED
from visu.WinCut import GRAPHCUT
from visu.winMeas import MEAS
from visu.WinOption import OPTION
from visu.andor import SifFile


class WINFFT(QMainWindow):
    '''
    Fenêtre d'affichage FFT :
        WINFFT(conf=conf, name='VISU')

    Utilisée par visual.py comme fenêtre de FFT 2D "live" (Display(data)
    calcule et affiche la FFT du tableau reçu), et utilisable seule pour
    ouvrir/analyser un fichier (.spe .SPE .sif .TIFF .txt) : max/min/mean,
    profils de coupe (ligne/rectangle/cercle), mesures, énergie encerclée...
    '''

    def __init__(self, parent=None, file=None, path=None, conf=None, name='VISU'):

        super().__init__()
        self.parent = parent
        self.name = name
        p = pathlib.Path(__file__)
        if conf is None:
            self.conf = QtCore.QSettings(str(p.parent / 'confVisu.ini'), QtCore.QSettings.Format.IniFormat)
        else:
            self.conf = conf
        sepa = os.sep
        self.icon = str(p.parent) + sepa + 'icons' + sepa
        self.isWinOpen = False
        self.nomFichier = ''
        self.path = path
        self.colorBar = 'flame'
        self.filter = 'origin'
        self.ite = None
        self.bloqq = 1
        self.plotRectZoomEtat = 'Zoom'

        self.setWindowTitle('FFT')
        self.setWindowIcon(QIcon(self.icon + 'LOA.png'))
        self.setStyleSheet(qdarkstyle.load_stylesheet(qt_api='pyqt6'))

        self.winEncercled = WINENCERCLED(conf=self.conf, name=self.name)
        self.winCoupe = GRAPHCUT(symbol=False, conf=self.conf, name=self.name)
        self.winM = MEAS(conf=self.conf, name=self.name)
        self.winOpt = OPTION(conf=self.conf, name=self.name)

        if file is None:
            self.dimy = 960
            self.dimx = 1240
            self.data = (50 * np.random.rand(self.dimx, self.dimy)).round() + 150
        else:
            if path is None:
                self.path = self.conf.value(self.name + "/path")
            self.OpenF(fileOpen=self.path + '/' + file)

        self.dataOrg = self.data

        self.setup()
        self.shortcut()
        self.actionButton()
        self.activateWindow()
        self.raise_()

    # ------------------------------------------------------------------
    # UI

    def setup(self):

        menubar = self.menuBar()
        menubar.setNativeMenuBar(False)
        self.fileMenu = menubar.addMenu('&File')
        self.ImageMenu = menubar.addMenu('&Image')
        self.AnalyseMenu = menubar.addMenu('&Analyse')
        self.ZoomMenu = menubar.addMenu('&Zoom')

        self.statusBarFFT = QStatusBar()
        self.setContentsMargins(0, 0, 0, 0)
        self.setStatusBar(self.statusBarFFT)

        # ===== File =====
        self.openAct = QAction(QIcon(self.icon + "Open.png"), 'Open File', self)
        self.openAct.setShortcut('Ctrl+o')
        self.openAct.triggered.connect(self.OpenF)
        self.fileMenu.addAction(self.openAct)

        self.saveAct = QAction(QIcon(self.icon + "disketteSave.png"), 'Save file', self)
        self.saveAct.setShortcut('Ctrl+s')
        self.saveAct.triggered.connect(self.SaveF)
        self.fileMenu.addAction(self.saveAct)

        self.checkBoxAutoSave = QAction(QIcon(self.icon + "diskette.png"), 'AutoSave off', self)
        self.checkBoxAutoSave.setCheckable(True)
        self.checkBoxAutoSave.setChecked(False)
        self.checkBoxAutoSave.triggered.connect(self.autoSaveColor)
        self.fileMenu.addAction(self.checkBoxAutoSave)

        self.optionAutoSaveAct = QAction(QIcon(self.icon + "Settings.png"), 'Options', self)
        self.optionAutoSaveAct.triggered.connect(lambda: self.open_widget(self.winOpt))
        self.fileMenu.addAction(self.optionAutoSaveAct)

        # ===== Image =====
        self.checkBoxScale = QAction(QIcon(self.icon + "expand.png"), 'Auto Scale on', self)
        self.checkBoxScale.setCheckable(True)
        self.checkBoxScale.setChecked(True)
        self.checkBoxScale.triggered.connect(self.checkBoxScaleImage)
        self.ImageMenu.addAction(self.checkBoxScale)

        self.checkBoxColor = QAction(QIcon(self.icon + "colors-icon.png"), 'Color on', self)
        self.checkBoxColor.setCheckable(True)
        self.checkBoxColor.setChecked(True)
        self.checkBoxColor.triggered.connect(self.Color)
        self.ImageMenu.addAction(self.checkBoxColor)

        self.checkBoxHist = QAction(QIcon(self.icon + "colourBar.png"), 'Show colour Bar', self)
        self.checkBoxHist.setCheckable(True)
        self.checkBoxHist.setChecked(False)
        self.checkBoxHist.triggered.connect(self.HIST)
        self.ImageMenu.addAction(self.checkBoxHist)

        menuColor = QMenu('&LookUp Table', self)
        for lut in ('thermal', 'flame', 'yellowy', 'bipolar', 'spectrum',
                    'cyclic', 'viridis', 'inferno', 'plasma', 'magma'):
            menuColor.addAction(lut, self.Setcolor)
        self.ImageMenu.addMenu(menuColor)

        self.checkBoxBg = QAction('Background Substraction On', self)
        self.checkBoxBg.setCheckable(True)
        self.checkBoxBg.setChecked(False)
        self.ImageMenu.addAction(self.checkBoxBg)

        self.ImageMenu.addSeparator()
        filterMenu = QMenu('&Filters', self)
        filterMenu.addAction('&Gaussian', self.Gauss)
        filterMenu.addAction('&Median', self.Median)
        filterMenu.addAction('&Origin', self.Orig)
        self.ImageMenu.addMenu(filterMenu)

        # ===== Analyse =====
        self.checkBoxPlot = QAction(QIcon(self.icon + "target.png"), 'Cross On', self)
        self.checkBoxPlot.setCheckable(True)
        self.checkBoxPlot.setChecked(False)
        self.checkBoxPlot.triggered.connect(self.PlotXY)
        self.AnalyseMenu.addAction(self.checkBoxPlot)

        self.maxGraphBox = QAction('Show Max Position', self)
        self.maxGraphBox.setCheckable(True)
        self.maxGraphBox.setChecked(False)
        self.maxGraphBox.triggered.connect(self.Coupe)
        self.AnalyseMenu.addAction(self.maxGraphBox)

        self.AnalyseMenu.addSeparator()

        # Line/Rect/Circle : uniquement dans la toolBar (icônes), pas dans
        # le menu Analyse.
        self.ligneAct = QAction(QIcon(self.icon + "line.png"), 'Line', self)
        self.ligneAct.setCheckable(True)
        self.ligneAct.triggered.connect(self.LIGNE)

        self.rectangleAct = QAction(QIcon(self.icon + "rectangle.png"), 'Rect', self)
        self.rectangleAct.setCheckable(True)
        self.rectangleAct.triggered.connect(self.Rectangle)

        self.circleAct = QAction(QIcon(self.icon + "Red_circle.png"), 'Circle', self)
        self.circleAct.setCheckable(True)
        self.circleAct.triggered.connect(self.CERCLE)

        self.PlotButton = QAction('Plot Profile', self)
        self.PlotButton.setShortcut('Ctrl+k')
        self.PlotButton.triggered.connect(self.CUT)
        self.AnalyseMenu.addAction(self.PlotButton)

        self.MeasButton = QAction(QIcon(self.icon + "laptop.png"), 'Measure', self)
        self.MeasButton.setShortcut('Ctrl+m')
        self.MeasButton.triggered.connect(self.Measurement)
        self.AnalyseMenu.addAction(self.MeasButton)

        self.energyBox = QAction('Encercled', self)
        self.energyBox.setShortcut('Ctrl+e')
        self.energyBox.triggered.connect(self.Energ)
        self.AnalyseMenu.addAction(self.energyBox)

        # ===== statusBar =====
        self.label_CrossValue = QLabel()
        self.label_CrossValue.setStyleSheet("font:13pt")
        self.label_Cross = QLabel()
        self.label_Cross.setMaximumWidth(220)
        self.label_Cross.setStyleSheet("font:12pt")
        self.statusBarFFT.addPermanentWidget(self.label_Cross)
        self.statusBarFFT.addPermanentWidget(self.label_CrossValue)

        self.labelFilter = QLabel('Filter: origin')
        self.labelFilter.setStyleSheet("font:8pt")
        self.statusBarFFT.addPermanentWidget(self.labelFilter)

        self.labelFileName = QLabel("File :")
        self.labelFileName.setStyleSheet("font:8pt;")
        self.labelFileName.setMaximumWidth(40)
        self.fileName = QLabel()
        self.fileName.setStyleSheet("font:8pt")
        self.fileName.setAlignment(Qt.AlignmentFlag.AlignVCenter)
        self.statusBarFFT.addWidget(self.labelFileName)
        self.statusBarFFT.addWidget(self.fileName)

        # ===== toolBar =====
        self.toolBar = self.addToolBar('tools')
        self.toolBar.addAction(self.checkBoxPlot)
        self.toolBar.addAction(self.checkBoxScale)
        self.toolBar.addAction(self.checkBoxColor)
        self.toolBar.addSeparator()
        self.toolBar.addAction(self.ligneAct)
        self.toolBar.addAction(self.rectangleAct)
        self.toolBar.addAction(self.circleAct)
        self.toolBar.addSeparator()

        self.ZoomRectButton = QAction(QIcon(self.icon + "loupe.png"), 'Zoom Selection', self)
        self.ZoomRectButton.triggered.connect(self.zoomRectAct)
        self.toolBar.addAction(self.ZoomRectButton)
        self.ZoomMenu.addAction(self.ZoomRectButton)
        self.toolBar.setMovable(False)

        # ===== image centrale =====
        self.winImage = pg.GraphicsLayoutWidget()
        self.winImage.setContentsMargins(0, 0, 0, 0)
        self.winImage.setAspectLocked(True)
        self.winImage.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.winImage.ci.setContentsMargins(0, 0, 0, 0)

        centralLayout = QVBoxLayout()
        centralLayout.setContentsMargins(0, 0, 0, 0)
        centralLayout.addWidget(self.winImage)
        centralWidget = QWidget()
        centralWidget.setLayout(centralLayout)
        self.setCentralWidget(centralWidget)

        self.p1 = self.winImage.addPlot()
        self.imh = pg.ImageItem()
        self.p1.addItem(self.imh)
        self.p1.setMouseEnabled(x=False, y=False)
        self.p1.setContentsMargins(0, 0, 0, 0)
        self.p1.setAspectLocked(True, ratio=1)
        self.p1.showAxis('right', show=False)
        self.p1.showAxis('top', show=False)
        self.p1.showAxis('left', show=False)
        self.p1.showAxis('bottom', show=False)

        self.vLine = pg.InfiniteLine(angle=90, movable=False, pen='y')
        self.hLine = pg.InfiniteLine(angle=0, movable=False, pen='y')

        self.xc = 10
        self.yc = 10
        self.rx = 50
        self.ry = 50
        self.vLine.setPos(self.xc)
        self.hLine.setPos(self.yc)

        self.ro1 = pg.EllipseROI([self.xc, self.yc], [self.rx, self.ry], pen='y',
                                  movable=False, maxBounds=QtCore.QRectF(0, 0, self.rx, self.ry))
        self.ro1.setPos([self.xc - (self.rx / 2), self.yc - (self.ry / 2)])

        # text for fwhm on p1
        self.textX = pg.TextItem(angle=-90)
        self.textY = pg.TextItem()

        # histogram
        self.hist = pg.HistogramLUTItem()
        self.hist.setImageItem(self.imh)
        self.hist.autoHistogramRange()
        self.hist.gradient.loadPreset('flame')

        # XY graph (profils au niveau de la croix)
        self.curve2 = pg.PlotCurveItem()
        self.curve3 = pg.PlotCurveItem()

        self.plotLine = pg.LineSegmentROI(positions=((0, 200), (200, 200)), movable=True, angle=0, pen='w')
        self.plotRect = pg.RectROI([self.xc, self.yc], [4 * self.rx, self.ry], pen='g')
        self.plotCercle = pg.CircleROI([self.xc, self.yc], [80, 80], pen='g')

        # Rectangle de sélection pour le zoom (bouton loupe, voir zoomRectAct)
        self.plotRectZoom = pg.RectROI([self.xc / 2, self.yc / 2], [2 * self.rx, 2 * self.ry], pen='w')
        self.plotRectZoom.addScaleHandle((0, 0), center=(1, 1))

    def actionButton(self):
        self.ro1.sigRegionChangeFinished.connect(self.roiChanged)
        self.plotLine.sigRegionChangeFinished.connect(self.LigneChanged)
        self.plotRect.sigRegionChangeFinished.connect(self.RectChanged)
        self.plotCercle.sigRegionChangeFinished.connect(self.CercChanged)

    def shortcut(self):
        self.shortcutPu = QShortcut(QtGui.QKeySequence("+"), self)
        self.shortcutPu.activated.connect(self.paletteup)
        self.shortcutPu.setContext(Qt.ShortcutContext(3))
        self.shortcutPd = QShortcut(QtGui.QKeySequence("-"), self)
        self.shortcutPd.activated.connect(self.palettedown)
        self.shortcutPd.setContext(Qt.ShortcutContext(3))

        # mouse move / click
        self.proxy = pg.SignalProxy(self.p1.scene().sigMouseMoved, rateLimit=60, slot=self.mouseMoved)
        self.p1.scene().sigMouseClicked.connect(self.mouseClick)
        self.vb = self.p1.vb

    # ------------------------------------------------------------------
    # Sélection ROI (ligne / rectangle / cercle) : un seul actif à la fois

    def _updateSelectionActionsChecked(self):
        self.ligneAct.setChecked(self.ite == 'line')
        self.rectangleAct.setChecked(self.ite == 'rect')
        self.circleAct.setChecked(self.ite == 'cercle')

    def LIGNE(self):
        try:
            self.p1.removeItem(self.plotRect)
            self.p1.removeItem(self.plotCercle)
        except Exception:
            pass

        if self.ite == 'line':
            self.p1.removeItem(self.plotLine)
            self.ite = None
        else:
            self.ite = 'line'
            # Recentre la ligne sur l'image courante (comme Rectangle()/CERCLE()
            # le font pour leur ROI) : sans ça elle restait à sa position de
            # construction (0,200)-(200,200), invisible/hors de l'image pour
            # une FFT plus grande, ce qui donnait l'impression que le bouton
            # ne faisait rien.
            self.plotLine.setPos([self.dimx / 2 - 100, self.dimy / 2])
            self.p1.addItem(self.plotLine)
            self.LigneChanged()
        self._updateSelectionActionsChecked()

    def LigneChanged(self):
        self.cut = self.plotLine.getArrayRegion(self.data, self.imh)

    def Rectangle(self):
        try:
            self.p1.removeItem(self.plotLine)
            self.p1.removeItem(self.plotCercle)
        except Exception:
            pass

        if self.ite == 'rect':
            self.p1.removeItem(self.plotRect)
            self.ite = None
        else:
            self.p1.addItem(self.plotRect)
            self.plotRect.setPos([self.dimx / 2, self.dimy / 2])
            self.ite = 'rect'
            self.RectChanged()
        self._updateSelectionActionsChecked()

    def RectChanged(self):
        self.cut = (self.plotRect.getArrayRegion(self.data, self.imh))
        self.cut1 = self.cut.mean(axis=1)

    def CERCLE(self):
        try:
            self.p1.removeItem(self.plotRect)
            self.p1.removeItem(self.plotLine)
        except Exception:
            pass

        if self.ite == 'cercle':
            self.p1.removeItem(self.plotCercle)
            self.ite = None
        else:
            self.p1.addItem(self.plotCercle)
            self.plotCercle.setPos([self.dimx / 2, self.dimy / 2])
            self.ite = 'cercle'
        self._updateSelectionActionsChecked()

    def CercChanged(self):
        self.cut = (self.plotCercle.getArrayRegion(self.data, self.imh))
        self.cut1 = self.cut.mean(axis=1)

    # ------------------------------------------------------------------
    # Actions Analyse

    def CUT(self):
        if self.ite == 'line':
            self.open_widget(self.winCoupe)
            self.winCoupe.PLOT(self.cut)
        if self.ite == 'rect':
            self.open_widget(self.winCoupe)
            self.winCoupe.PLOT(self.cut1)

    def Measurement(self):
        # winMeas.MEAS.Display() attend [data, transx, transy, scalex,
        # scaley] (voir visual.py Measurement()), pas le tableau brut : sans
        # ça data[0] ne récupère que la première ligne de l'image (1D) au
        # lieu de l'image/la coupe entière.
        if self.ite == 'rect':
            self.RectChanged()
            self.winM.setFile(self.nomFichier)
            self.open_widget(self.winM)
            self.winM.Display([self.cut, 0, 0, 1, 1])
        if self.ite == 'cercle':
            self.CercChanged()
            self.winM.setFile(self.nomFichier)
            self.open_widget(self.winM)
            self.winM.Display([self.cut, 0, 0, 1, 1])
        if self.ite is None:
            self.winM.setFile(self.nomFichier)
            self.open_widget(self.winM)
            self.winM.Display([self.data, 0, 0, 1, 1])

    def Energ(self):
        self.open_widget(self.winEncercled)
        self.winEncercled.Display(self.data)

    # ------------------------------------------------------------------
    # Affichage

    def Display(self, data):
        """
        Point d'entrée externe (utilisé par visual.py) : calcule la FFT 2D
        du tableau reçu (image brute) puis l'affiche.
        """
        data = np.asarray(data)
        if data.ndim == 2:
            datafft = np.fft.fft2(data)
            norm = abs(np.fft.fftshift(datafft))
            norm = np.log10(1 + norm)
            self.newDataReceived(norm)

    def newDataReceived(self, data):
        """Affiche directement le tableau reçu (déjà transformé ou non)."""
        self.data = data
        self.dataOrg = self.data
        self._render(self.data)

    def _render(self, data):
        self.data = data

        if self.checkBoxBg.isChecked() and self.winOpt.dataBgExist is True:
            try:
                self.data = self.data.astype(np.int32) - self.winOpt.dataBg.astype(np.int32)
            except Exception:
                msg = QMessageBox()
                msg.setIcon(QMessageBox.Icon.Critical)
                msg.setText("Background not soustracted !")
                msg.setInformativeText("Background file error")
                msg.setWindowTitle("Warning ...")
                msg.setWindowFlags(QtCore.Qt.WindowType.WindowStaysOnTopHint)
                msg.exec()
        elif self.checkBoxBg.isChecked() and self.winOpt.dataBgExist is False:
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Icon.Critical)
            msg.setText("Background not soustracted !")
            msg.setInformativeText("Background file not selected in options menu")
            msg.setWindowTitle("Warning ...")
            msg.setWindowFlags(QtCore.Qt.WindowType.WindowStaysOnTopHint)
            msg.exec()

        self.dimy = np.shape(self.data)[1]
        self.dimx = np.shape(self.data)[0]
        self.p1.setXRange(0, self.dimx)
        self.p1.setYRange(0, self.dimy)

        if self.filter == 'gauss':
            self.data = gaussian_filter(self.data, self.sigma)
        if self.filter == 'median':
            self.data = median_filter(self.data, size=self.sigma)

        if self.checkBoxScale.isChecked():
            self.imh.setImage(self.data.astype(float), autoLevels=True, autoDownsample=True)
        else:
            self.imh.setImage(self.data.astype(float), autoLevels=False, autoDownsample=True)

        self.PlotXY()

        if self.winEncercled.isWinOpen:
            self.winEncercled.Display(self.data)

        if self.winCoupe.isWinOpen:
            if self.ite == 'line':
                self.LigneChanged()
                self.CUT()
            if self.ite == 'rect':
                self.RectChanged()
                self.CUT()
            if self.ite == 'cercle':
                self.CercChanged()

        if self.winM.isWinOpen:
            if self.ite == 'rect':
                self.RectChanged()
                self.Measurement()
            elif self.ite == 'cercle':
                self.CercChanged()
                self.Measurement()
            elif self.ite is None:
                # Sans sélection rect/cercle (mesure sur l'image entière) :
                # sans ce cas, Measurement() n'était rafraîchi qu'une fois
                # (au clic manuel) et ne se remettait plus à jour au tir
                # suivant.
                self.Measurement()

        if self.checkBoxAutoSave.isChecked():
            self.pathAutoSave = str(self.conf.value(self.name + '/pathAutoSave'))
            self.fileNameSave = str(self.conf.value(self.name + '/nameFile'))
            date = time.strftime("%Y_%m_%d_%H_%M_%S")
            self.numTir = int(self.conf.value(self.name + '/tirNumber'))
            if self.numTir < 10:
                num = "00" + str(self.numTir)
            elif 9 < self.numTir < 100:
                num = "0" + str(self.numTir)
            else:
                num = str(self.numTir)
            if self.winOpt.checkBoxDate.isChecked():
                nomFichier = str(str(self.pathAutoSave) + '/' + self.fileNameSave + '_' + num + '_' + date)
            else:
                nomFichier = str(str(self.pathAutoSave) + '/' + self.fileNameSave + '_' + num)
            np.savetxt(str(nomFichier) + '.txt', self.data)
            self.numTir += 1
            self.winOpt.setTirNumber(self.numTir)
            self.conf.setValue(self.name + "/tirNumber", self.numTir)
            self.fileName.setText(nomFichier)

        self.zoomRectupdate()

    # ------------------------------------------------------------------
    # Souris / croix

    def mouseClick(self):
        if self.bloqq == 1:
            self.debloquer()
        else:
            self.bloquer()

    def mouseMoved(self, evt):
        if self.bloqq == 0:
            pos = evt[0]
            if self.p1.sceneBoundingRect().contains(pos):
                mousePoint = self.vb.mapSceneToView(pos)
                self.xMouse = (mousePoint.x())
                self.yMouse = (mousePoint.y())
                if ((self.xMouse > 0 and self.xMouse < self.data.shape[0] - 1) and
                        (self.yMouse > 0 and self.yMouse < self.data.shape[1] - 1)):
                    self.xc = self.xMouse
                    self.yc = self.yMouse
                    self.vLine.setPos(self.xc)
                    self.hLine.setPos(self.yc)
                    self.PlotXY()

    def bloquer(self):  # block the cross
        self.bloqq = 1
        self.conf.setValue(self.name + "/xc", int(self.xc))
        self.conf.setValue(self.name + "/yc", int(self.yc))

    def debloquer(self):  # unblock the cross
        self.bloqq = 0

    def fwhm(self, x, y, order=3):
        """Determine full-width-half-maximum of a peaked set of points."""
        y = gaussian_filter(y, 5)
        half_max = np.amax(y) / 2.0
        s = splrep(x, y - half_max, k=order)
        roots = sproot(s)
        if len(roots) == 2:
            return np.around(abs(roots[1] - roots[0]), decimals=2)
        return None

    def Coupe(self):
        if self.maxGraphBox.isChecked():
            dataF = gaussian_filter(self.data, 5)
            (self.xc, self.yc) = np.unravel_index(dataF.argmax(), self.data.shape)
            self.vLine.setPos(self.xc)
            self.hLine.setPos(self.yc)

        xxx = np.arange(0, int(self.dimx), 1)
        yyy = np.arange(0, int(self.dimy), 1)
        coupeX = self.data[int(self.xc), :]
        coupeXMax = np.max(coupeX)
        dataCross = self.data[int(self.xc), int(self.yc)]
        self.label_Cross.setText('x=' + str(int(self.xc)) + ' y=' + str(int(self.yc)))
        self.label_CrossValue.setText(' v.=' + str(dataCross))

        if coupeXMax == 0:
            coupeXMax = 1
        coupeXnorm = (self.data.shape[0] / 10) * (coupeX / coupeXMax)
        self.curve2.setData(30 + coupeXnorm, yyy, clear=True)

        coupeY = self.data[:, int(self.yc)]
        coupeYMax = np.max(coupeY)
        if coupeYMax == 0:
            coupeYMax = 1
        coupeYnorm = (self.data.shape[1] / 10) * (coupeY / coupeYMax)
        self.curve3.setData(xxx, 20 + coupeYnorm, clear=True)

        xCXmax = np.amax(coupeXnorm)
        if xCXmax > 20:
            fwhmX = self.fwhm(yyy, coupeXnorm, order=3)
            self.textX.setText('' if fwhmX is None else 'fwhm=' + str(fwhmX))

        yCYmax = np.amax(coupeYnorm)
        if yCYmax > 20:
            fwhmY = self.fwhm(xxx, coupeYnorm, order=3)
            if fwhmY is None:
                self.textY.setText('', color='w')
            else:
                self.textY.setText('fwhm=' + str(fwhmY), color='w')

    def PlotXY(self):
        # addItem()/removeItem() préviennent (warning pyqtgraph "Item already
        # added to PlotItem, ignoring") si l'item est déjà présent/absent :
        # PlotXY() étant appelé à chaque tir (_render()) et à chaque
        # déplacement de la croix (mouseMoved()), pas seulement au bascule
        # de la case Cross, on ne (re)touche les items que si nécessaire.
        if self.checkBoxPlot.isChecked():
            if self.vLine not in self.p1.items:
                self.p1.addItem(self.vLine, ignoreBounds=False)
            if self.hLine not in self.p1.items:
                self.p1.addItem(self.hLine, ignoreBounds=False)
            if self.curve2 not in self.p1.items:
                self.p1.addItem(self.curve2)
            if self.curve3 not in self.p1.items:
                self.p1.addItem(self.curve3)
            self.p1.showAxis('left', show=True)
            self.p1.showAxis('bottom', show=True)
            self.Coupe()
        else:
            if self.vLine in self.p1.items:
                self.p1.removeItem(self.vLine)
            if self.hLine in self.p1.items:
                self.p1.removeItem(self.hLine)
            if self.curve2 in self.p1.items:
                self.p1.removeItem(self.curve2)
            if self.curve3 in self.p1.items:
                self.p1.removeItem(self.curve3)
            if self.textX in self.p1.items:
                self.p1.removeItem(self.textX)
            if self.textY in self.p1.items:
                self.p1.removeItem(self.textY)
            self.p1.showAxis('left', show=False)
            self.p1.showAxis('bottom', show=False)

    def roiChanged(self):
        self.rx = self.ro1.size()[0]
        self.ry = self.ro1.size()[1]
        self.conf.setValue(self.name + "/rx", int(self.rx))
        self.conf.setValue(self.name + "/ry", int(self.ry))

    # ------------------------------------------------------------------
    # Palette / couleur / zoom

    def paletteup(self):
        levels = self.imh.getLevels()
        if levels[0] is None:
            xmax, xmin = self.data.max(), self.data.min()
        else:
            xmin, xmax = levels[0], levels[1]
        self.imh.setLevels([xmin, xmax - (xmax - xmin) / 10])
        self.hist.setHistogramRange(xmin, xmax)

    def palettedown(self):
        levels = self.imh.getLevels()
        if levels[0] is None:
            xmax, xmin = self.data.max(), self.data.min()
        else:
            xmin, xmax = levels[0], levels[1]
        self.imh.setLevels([xmin, xmax + (xmax - xmin) / 10])
        self.hist.setHistogramRange(xmin, xmax)

    def Setcolor(self):
        action = self.sender()
        self.colorBar = str(action.text())
        self.hist.gradient.loadPreset(self.colorBar)

    def Color(self):
        if self.checkBoxColor.isChecked():
            self.checkBoxColor.setIcon(QIcon(self.icon + "colors-icon.png"))
            self.hist.gradient.loadPreset(self.colorBar)
            self.checkBoxColor.setText('Color on')
        else:
            self.hist.gradient.loadPreset('grey')
            self.checkBoxColor.setText('Grey')
            self.checkBoxColor.setIcon(QIcon(self.icon + "circleGray.png"))

    def checkBoxScaleImage(self):
        if self.checkBoxScale.isChecked():
            self.checkBoxScale.setIcon(QIcon(self.icon + "expand.png"))
            self.checkBoxScale.setText('Auto Scale On')
        else:
            self.checkBoxScale.setIcon(QIcon(self.icon + "minimize.png"))
            self.checkBoxScale.setText('Auto Scale Off')

    def autoSaveColor(self):
        if self.checkBoxAutoSave.isChecked():
            self.checkBoxAutoSave.setIcon(QIcon(self.icon + "saveAutoOn.png"))
            self.checkBoxAutoSave.setText('Auto Save On')
        else:
            self.checkBoxAutoSave.setIcon(QIcon(self.icon + "diskette.png"))
            self.checkBoxAutoSave.setText('Auto Save Off')

    def zoomRectAct(self):
        """
        Zoom par sélection rectangulaire (bouton loupe), sur le modèle de
        visualLight.py : 3 états cyclés à chaque clic.
        - "Zoom"    : affiche un rectangle déplaçable/redimensionnable
                      autour de la croix -> état "ZoomIn"
        - "ZoomIn"  : zoome la vue sur le rectangle choisi -> état "ZoomOut"
        - "ZoomOut" : revient à la vue complète -> état "Zoom"
        """
        if self.plotRectZoomEtat == "Zoom":
            self.p1.addItem(self.plotRectZoom)
            self.plotRectZoom.setSize(size=(2 * self.rx, 2 * self.ry), center=None)
            self.plotRectZoom.setPos([self.xc - self.rx, self.yc - self.ry])
            self.ZoomRectButton.setIcon(QIcon(self.icon + "zoom-in.png"))
            self.ZoomRectButton.setText('Zoom In')
            self.plotRectZoomEtat = "ZoomIn"

        elif self.plotRectZoomEtat == "ZoomIn":
            self.ZoomRectButton.setIcon(QIcon(self.icon + "zoom-out.png"))
            self.xZoomMin = self.plotRectZoom.pos()[0]
            self.yZoomMin = self.plotRectZoom.pos()[1]
            self.xZoomMax = self.plotRectZoom.pos()[0] + self.plotRectZoom.size()[0]
            self.yZoomMax = self.plotRectZoom.pos()[1] + self.plotRectZoom.size()[1]
            self.p1.setXRange(self.xZoomMin, self.xZoomMax)
            self.p1.setYRange(self.yZoomMin, self.yZoomMax)
            self.p1.setAspectLocked(False)
            self.p1.removeItem(self.plotRectZoom)
            self.ZoomRectButton.setText('Zoom Out')
            self.plotRectZoomEtat = "ZoomOut"

        elif self.plotRectZoomEtat == "ZoomOut":
            self.p1.setXRange(0, self.dimx)
            self.p1.setYRange(0, self.dimy)
            self.ZoomRectButton.setIcon(QIcon(self.icon + "loupe.png"))
            self.ZoomRectButton.setText('Zoom Selection')
            self.plotRectZoomEtat = "Zoom"
            self.p1.setAspectLocked(True)

    def zoomRectupdate(self):
        """Conserve la vue zoomée d'un tir à l'autre (appelé depuis _render())."""
        if self.plotRectZoomEtat == "ZoomOut":
            self.p1.setXRange(self.xZoomMin, self.xZoomMax)
            self.p1.setYRange(self.yZoomMin, self.yZoomMax)
            self.p1.setAspectLocked(True)

    def HIST(self):
        if self.checkBoxHist.isChecked():
            self.winImage.addItem(self.hist)
        else:
            self.winImage.removeItem(self.hist)

    # ------------------------------------------------------------------
    # Filtres

    def Gauss(self):
        self.filter = 'gauss'
        sigma, ok = QInputDialog.getInt(self, 'Gaussian Filter', 'Enter sigma value (radius)')
        if ok:
            self.sigma = sigma
            self.labelFilter.setText('Filter: Gaussian')
            self._render(self.data)

    def Median(self):
        self.filter = 'median'
        sigma, ok = QInputDialog.getInt(self, 'Median Filter', 'Enter sigma value (radius)')
        if ok:
            self.sigma = sigma
            self.labelFilter.setText('Filter: Median')
            self._render(self.data)

    def Orig(self):
        self.data = self.dataOrg
        self.filter = 'origin'
        self._render(self.data)
        self.labelFilter.setText('Filter: origin')

    # ------------------------------------------------------------------
    # Fichiers

    def OpenF(self, fileOpen=None):

        if not fileOpen:
            chemin = self.conf.value(self.name + "/path")
            fname = QFileDialog.getOpenFileName(self, "Open File", chemin, "Images (*.txt *.spe *.TIFF *.sif *.tif);;Text File(*.txt);;Ropper File (*.SPE);;Andor File(*.sif);; TIFF file(*.TIFF)")
            fichier = fname[0]
            if not fichier:
                return
        else:
            fichier = str(fileOpen)

        ext = os.path.splitext(fichier)[1]

        if ext == '.txt':
            data = np.loadtxt(str(fichier))
        elif ext == '.spe' or ext == '.SPE':
            dataSPE = SpeFile(fichier)
            data = dataSPE.data[0]
        elif ext in ('.TIFF', '.tif'):
            dat = Image.open(fichier)
            data = np.array(dat)
        elif ext == '.sif':
            sifop = SifFile()
            im = sifop.openA(fichier)
            data = np.rot90(im, 3)
        else:
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Icon.Critical)
            msg.setText("Wrong file format !")
            msg.setInformativeText("The format of the file must be : .SPE  .TIFF .sif or .txt")
            msg.setWindowTitle("Warning ...")
            msg.setWindowFlags(QtCore.Qt.WindowType.WindowStaysOnTopHint)
            msg.exec()
            return

        chemin = os.path.dirname(fichier)
        self.conf.setValue(self.name + "/path", chemin)
        self.conf.setValue(self.name + "/lastFichier", os.path.split(fichier)[1])
        self.fileName.setText(os.path.split(fichier)[1])
        self.nomFichier = os.path.split(fichier)[1]
        self.dataOrg = data
        self._render(data)

    def SaveF(self):
        fname = QFileDialog.getSaveFileName(self, "Save data as txt", self.path)
        self.path = os.path.dirname(str(fname[0]))
        fichier = fname[0]
        if not fichier:
            return
        self.conf.setValue(self.name + "/path", self.path)
        time.sleep(0.1)
        np.savetxt(str(fichier) + '.txt', self.data)
        self.fileName.setText(fname[0] + '.txt')

    # ------------------------------------------------------------------

    def open_widget(self, fene):
        """open new widget"""
        if fene.isWinOpen is False:
            fene.isWinOpen = True
            fene.show()
        else:
            fene.raise_()
            fene.showNormal()

    def closeEvent(self, event):
        self.isWinOpen = False
        if self.winEncercled.isWinOpen:
            self.winEncercled.close()
        if self.winCoupe.isWinOpen:
            self.winCoupe.close()
        if self.winM.isWinOpen:
            self.winM.close()
        if self.winOpt.isWinOpen:
            self.winOpt.close()
        event.accept()


if __name__ == "__main__":
    appli = QApplication(sys.argv)
    appli.setStyleSheet(qdarkstyle.load_stylesheet(qt_api='pyqt6'))
    e = WINFFT(name='VISU')
    e.show()
    appli.exec()
