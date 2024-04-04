#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import numpy as np 
import pathlib
import sys
from PyQt6.QtWidgets import QApplication, QWidget, QLineEdit
from PyQt6.QtWidgets import QVBoxLayout, QHBoxLayout
from PyQt6.QtWidgets import QLabel, QSizePolicy, QCheckBox, QPushButton
from PyQt6.QtWidgets import QFileDialog, QProgressBar, QDoubleSpinBox
from PyQt6.QtWidgets import QMainWindow, QStatusBar, QSpacerItem
from PyQt6.QtGui import QAction
from PyQt6 import QtCore, QtGui
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon

import time
import os
import qdarkstyle
from scipy.integrate import solve_ivp
from scipy.interpolate import interp1d, RectBivariateSpline
import matplotlib.pyplot as plt
import pyqtgraph as pg
from scipy.constants import c, m_e, e
from visu import WinCut

# La coordonnee y decrit l'axe de l'aimant et x decrit la coordonnee transverse
# (0,0) correspond au centre de l'aimant.
# y>0: vers le lanex.
# Oxyz repere oriente dans le sens trigonometrique. Le champ magnetique B est suivant z.


class WINRESULT(QWidget):
    
    def __init__(self, parent=None):
        super().__init__()
        self.parent = parent
        self.isWinOpen = False
        self.setup()
        self.actionButton()
    
    def setup(self):
        vbox = QHBoxLayout()
        lablePos = QLabel('Position on lanex')
        self.posBox = QDoubleSpinBox()
        self.posBox.setSuffix(' mm')
        self.posBox.setRange(-10000, 100000)
        lableE = QLabel('E')
        self.EBox = QDoubleSpinBox()
        self.EBox.setSuffix(' Mev')
        self.EBox.setRange(0, 1000000)
        vbox.addWidget(lablePos)
        vbox.addWidget(self.posBox)
        vbox.addWidget(lableE)
        vbox.addWidget(self.EBox)
        self.setWindowTitle('Energy calculation')
        self.setLayout(vbox)
    
    def actionButton(self):
        self.posBox.editingFinished.connect(self.calculE)

    def calculE(self):
        # Find the Enrgy for a postion on the lanex
        f_E = interp1d(self.parent.threadCalcul.s, self.parent.threadCalcul.E)
        if self.posBox.value() < self.parent.threadCalcul.s.max():
            self.EBox.setValue(f_E(self.posBox.value()))
        
    def closeEvent(self, event):
        """ when closing the window
        """
        self.isWinOpen = False

class WINTRAJECTOIRE(QMainWindow):
    signalPlot = QtCore.pyqtSignal(object)

    def __init__(self, parent=None, **kwds):

        super().__init__()
        self.parent = parent
        self.isWinOpen = False
        self.p = pathlib.Path(__file__)
        sepa = os.sep
        self.icon = str(self.p.parent) + sepa+'icons' + sepa
        self.paraFile = QtCore.QSettings(str(self.p.parent / 'defaultTrajectory.ini'), QtCore.QSettings.Format.IniFormat)
        self.winresult = WINRESULT(parent=self)
        self.setup()
        self.iniValue()
        self.threadCalcul = CALCULTHREAD(parent=self)
        self.actionButton()
        self.CheckChangeB()
        
    def setup(self):
        # define button
        self.setWindowTitle('Electron Trajectory ')
        self.setWindowIcon(QIcon(self.icon+'LOA.png'))
        menubar = self.menuBar()
        menubar.setNativeMenuBar(False)
        self.fileMenu = menubar.addMenu('&File')
        self.ResultMenu = menubar.addMenu('&Results')
        self.statusBar = QStatusBar()
        self.setContentsMargins(0, 0, 0, 0)

        self.setStatusBar(self.statusBar)
        self.openAct = QAction(QtGui.QIcon(self.icon+"Open.png"),
                               'Open parameter File', self)

        self.openAct.setShortcut('Ctrl+o')
        self.openAct.triggered.connect(self.openF)
        self.fileMenu.addAction(self.openAct)

        self.saveAct = QAction(QtGui.QIcon(self.icon+"Saving.png"),
                               'Save Parameter', self)

        self.saveAct.setShortcut('Ctrl+s')
        self.saveAct.triggered.connect(self.saveF)
        self.fileMenu.addAction(self.saveAct)

        self.exportAct = QAction(QtGui.QIcon(self.icon+"Settings.png"),
                                 'Export dispersion', self)
        self.exportAct.triggered.connect(self.exportF)
        self.fileMenu.addAction(self.exportAct)

        self.resAct = QAction('Energy cal', self)
        self.resAct.triggered.connect(lambda: self.open_widget(self.winresult))
        self.ResultMenu.addAction(self.resAct)

        self.winDisp = WinCut.GRAPHCUT(self, title='Plot Dispersion' )
        self.DispAct = QAction('Plot  Dispersion', self)
        self.DispAct.triggered.connect(lambda: self.open_widget(self.winDisp))
        self.DispAct.triggered.connect(self.DispDisplay)
        self.ResultMenu.addAction(self.DispAct)

        self.winDist = WinCut.GRAPHCUT(self, title='Plot Electron length path' )
        self.DistAct = QAction('Plot  Distance Electron length path', self)
        self.DistAct.triggered.connect(lambda: self.open_widget(self.winDist))
        self.DistAct.triggered.connect(self.DistDisplay)
        self.ResultMenu.addAction(self.DistAct)

        self.winDsDE = WinCut.GRAPHCUT(self, title='Plot Ds/DE')
        self.DsDEAct = QAction('Plot  ds/dE', self)
        self.DsDEAct.triggered.connect(lambda: self.open_widget(self.winDsDE))
        self.DsDEAct.triggered.connect(self.DsDEDisplay)
        self.ResultMenu.addAction(self.DsDEAct)

        self.winResol = WinCut.GRAPHCUT(self, title='Resolution')
        self.ResolAct = QAction('Plot  Resolution', self)
        self.ResolAct.triggered.connect(lambda: self.open_widget(self.winResol))
        self.ResolAct.triggered.connect(self.ResolDisplay)
        self.ResultMenu.addAction(self.ResolAct)

        vbox1 = QVBoxLayout()

        Hbox1 = QHBoxLayout()
        labelSource = QLabel('Position Source ')
        labelSource.setAlignment(Qt.AlignmentFlag.AlignCenter)
        labelSourceX = QLabel('X')
        self.sourceX = QDoubleSpinBox()
        self.sourceX.setSuffix('mm')
        self.sourceX.setRange(-100000, 10000)
        labelSourceY = QLabel('Y')
        self.sourceY = QDoubleSpinBox()
        self.sourceY.setSuffix('mm')
        self.sourceY.setRange(-100000, 10000)
        Hbox1.addWidget(labelSource)
        Hbox1.addWidget(labelSourceX)
        Hbox1.addWidget(self.sourceX)
        Hbox1.addWidget(labelSourceY)
        Hbox1.addWidget(self.sourceY)
        divLabel = QLabel('div')
        Hbox1.addWidget(divLabel)
        self.divBox = QDoubleSpinBox()
        self.divBox.setSuffix(' mrad')
        Hbox1.addWidget(self.divBox)
        labelAngle = QLabel('Angle Faisceau/oy')
        self.angle = QDoubleSpinBox()
        self.angle.setSuffix(' °')
        self.angle.setRange(-180, 180)
        Hbox1.addWidget(labelAngle)
        Hbox1.addWidget(self.angle)
        Spacer1 = QSpacerItem(1, 1, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        Hbox1.addItem(Spacer1)
        vbox1.addLayout(Hbox1)

        Hbox3 = QHBoxLayout()
        labelLanex = QLabel('Position Lanex')
        labelLanexX = QLabel('X')
        self.lanexX = QDoubleSpinBox()
        self.lanexX.setSuffix(' mm')
        self.lanexX.setRange(-10000, 10000)
        Hbox3.addWidget(labelLanex)
        Hbox3.addWidget(labelLanexX)
        Hbox3.addWidget(self.lanexX)
        labelLanexY = QLabel('Y')
        self.lanexY = QDoubleSpinBox()
        self.lanexY.setSuffix(' mm')
        self.lanexY.setRange(-10000, 10000)
        Hbox3.addWidget(labelLanexY)
        Hbox3.addWidget(self.lanexY)

        labelLanexAngle = QLabel('Angle(°)/ox')
        self.lanexAngle = QDoubleSpinBox()
        self.lanexAngle.setSuffix(' °')
        self.lanexAngle.setRange(-360, 360)
        Hbox3.addWidget(labelLanexAngle)
        Hbox3.addWidget(self.lanexAngle)
        Spacer3 = QSpacerItem(1, 1, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        Hbox3.addItem(Spacer3)
        vbox1.addLayout(Hbox3)

        Hbox4 = QHBoxLayout()
        labelB = QLabel('B')
        self.Bbox = QDoubleSpinBox()
        self.Bbox.setSuffix(' T')
        labelSens = QLabel('B sens')
        self.BSensBox = QDoubleSpinBox()
        self.BSensBox.setRange(-1, 1)
        self.checkB = QCheckBox('B constant')

        self.checkB.setChecked(True)
        self.labelAimantLength = QLabel('Magnet length')
        self.AimantLength = QDoubleSpinBox()
        self.AimantLength.setSuffix(" mm")
        self.AimantLength.setRange(0, 10000)
        self.labelAimantWidth = QLabel('Magnet width')
        self.AimantWidth = QDoubleSpinBox()
        self.AimantWidth.setSuffix(" mm")
        self.AimantWidth.setRange(0, 10000)

        Hbox4.addWidget(labelB)
        Hbox4.addWidget(self.Bbox)
        Hbox4.addWidget(labelSens)
        Hbox4.addWidget(self.BSensBox)
        Hbox4.addWidget(self.checkB)
        Hbox4.addWidget(self.labelAimantLength)
        Hbox4.addWidget(self.AimantLength)
        Hbox4.addWidget(self.labelAimantWidth)
        Hbox4.addWidget(self.AimantWidth)
        Spacer4 = QSpacerItem(1, 1, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        Hbox4.addItem(Spacer4)
        vbox1.addLayout(Hbox4)
        Hbox4b = QHBoxLayout()
        self.BButton = QPushButton('Select B file', self)
        Hbox4b.addWidget(self.BButton)
        self.pathBLine = QLineEdit(self)
        Hbox4b.addWidget(self.pathBLine)
        vbox1.addLayout(Hbox4b)

        Hbox5 = QHBoxLayout()
        paraLabel = QLabel('Parameters')
        Hbox5.addWidget(paraLabel)
        vbox1.addLayout(Hbox5)

        Hbox6 = QHBoxLayout()
        EminLabel = QLabel('Emin')
        Hbox6.addWidget(EminLabel)
        self.EminBox = QDoubleSpinBox()
        self.EminBox.setSuffix(' Mev')
        self.EminBox.setRange(0, 10000)
        Hbox6.addWidget(self.EminBox)

        EmaxLabel = QLabel('Emax')
        Hbox6.addWidget(EmaxLabel)
        self.EmaxBox = QDoubleSpinBox()
        self.EmaxBox.setRange(self.EminBox.value(), 100000)
        self.EmaxBox.setSuffix(' Mev')
        Hbox6.addWidget(self.EmaxBox)
        
        NLabel = QLabel('Number traj')
        Hbox6.addWidget(NLabel)
        self.NBox = QDoubleSpinBox()
        self.NBox.setRange(1, 10000)
        Hbox6.addWidget(self.NBox)

        lanexLabel = QLabel('Lanex length')
        Hbox6.addWidget(lanexLabel)
        self.lanexBox = QDoubleSpinBox()
        self.lanexBox.setSuffix(' mm')
        self.lanexBox.setRange(0, 10000)
        Hbox6.addWidget(self.lanexBox)
        Spacer6 = QSpacerItem(1, 1, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        Hbox6.addItem(Spacer6)
        vbox1.addLayout(Hbox6)
        
        Hbox7 = QHBoxLayout()
        self.calculButton = QPushButton('Start Calcul', self)
        Hbox7.addWidget(self.calculButton)
        self.stopButton = QPushButton('STOP', self)
        Hbox7.addWidget(self.stopButton)
        self.progressBar = QProgressBar()
        Hbox7.addWidget(self.progressBar)
        self.EcalLabel = QLabel('')
        Hbox7.addWidget(self.EcalLabel)
        vbox1.addLayout(Hbox7)

        self.winImage = pg.GraphicsLayoutWidget()
        self.winImage.setContentsMargins(0, 0, 0, 0)
        self.winImage.setAspectLocked(False)
        self.winImage.ci.setContentsMargins(0, 0, 0, 0)
        vbox1.addWidget(self.winImage)
        vbox1.setContentsMargins(0, 0, 0, 0)
        
        self.p1 = self.winImage.addPlot()
        self.imh = pg.ImageItem()
        self.axeX = self.p1.getAxis('bottom')
        self.axeY = self.p1.getAxis('left')
        self.p1.addItem(self.imh)
        self.p1.setMouseEnabled(x=False, y=False)
        self.p1.setContentsMargins(0, 0, 0, 10)
        
        self.winImage2 = pg.GraphicsLayoutWidget()
        self.winImage2.setAspectLocked(True)
        # vbox1.addWidget(self.winImage2) # affiche le plot de la dispersion sous les trejectoires
        self.p2 = self.winImage2.addPlot()

        self.p1.showAxis('right', show=False)
        self.p1.showAxis('top', show=False)
        self.p1.showAxis('left', show=True)
        self.p1.setLabel('left', " Y Axis (mm)")
        self.p1.setLabel('bottom', "X Axis(mm)")
        self.p2.setLabel('left', "Lanex (mm)")
        self.p2.setLabel('bottom', "Energy (Mev) ")
        self.p2.setTitle('Dispersion on lanex ')

        self.label_Cross = QLabel()
        self.label_Cross.setStyleSheet("font:12pt")
        self.statusBar.addPermanentWidget(self.label_Cross)

        MainWidget = QWidget()
        MainWidget.setLayout(vbox1)
        self.setCentralWidget(MainWidget)

    def actionButton(self):

        self.proxy = pg.SignalProxy(self.p1.scene().sigMouseMoved, rateLimit=60, slot=self.mouseMoved)
        self.vb = self.p1.vb
        self.sourceX.editingFinished.connect(self.set_default)
        self.sourceY.editingFinished.connect(self.set_default)
        self.angle.editingFinished.connect(self.set_default)
        self.lanexX.editingFinished.connect(self.set_default)
        self.lanexY.editingFinished.connect(self.set_default)
        self.lanexAngle.editingFinished.connect(self.set_default)
        self.Bbox.editingFinished.connect(self.set_default)
        self.BSensBox.editingFinished.connect(self.set_default)
        self.EminBox.editingFinished.connect(self.set_default)
        self.EmaxBox.editingFinished.connect(self.set_default)
        self.NBox.editingFinished.connect(self.set_default)
        self.divBox.editingFinished.connect(self.set_default)
        self.lanexBox.editingFinished.connect(self.set_default)
        self.AimantLength.editingFinished.connect(self.set_default)
        self.AimantWidth.editingFinished.connect(self.set_default)
        self.BButton.clicked.connect(self.BLoad)
        self.calculButton.clicked.connect(self.startCalcul)
        self.stopButton.clicked.connect(self.stopCalcul)
        self.threadCalcul.remain.connect(self.progress)
        self.checkB.stateChanged.connect(self.CheckChangeB)

    def iniValue(self):
        # set value from ini file 
        self.sourceX.setValue(float(self.paraFile.value("/"+"/x_j")))
        self.sourceY.setValue(float(self.paraFile.value("/"+"/y_j")))
        self.angle.setValue(float(self.paraFile.value("/"+"/theta_e")))
        self.lanexAngle.setValue(float(self.paraFile.value("/"+"/theta_la")))
        self.Bbox.setValue(float(self.paraFile.value("/"+"/B")))
        self.lanexX.setValue(float(self.paraFile.value("/"+"/x_d")))
        self.lanexY.setValue(float(self.paraFile.value("/"+"/y_d")))
        self.EminBox.setValue(float(self.paraFile.value("/"+"/Emin")))
        self.EmaxBox.setValue(float(self.paraFile.value("/"+"/Emax", )))
        self.NBox.setValue(float(self.paraFile.value("/"+"/N")))
        self.divBox.setValue(float(self.paraFile.value("/"+"/div")))
        self.lanexBox.setValue(float(self.paraFile.value("/"+"/long_lanex")))
        self.BSensBox.setValue(float(self.paraFile.value("/"+"/sens_B")))
        self.pathBLine.setText(self.paraFile.value("/"+"/Bpath"))
        self.BFileName = self.paraFile.value("/"+"/Bpath")
        self.AimantLength.setValue(float(self.paraFile.value("/"+"/LM")))
        self.AimantWidth.setValue(float(self.paraFile.value("/"+"/LaM")))
        self.set_default()

    def set_default(self):
        # save values in the default ini file and read value 
        self.paraFile.setValue("/"+"/x_j", self.sourceX.value())
        self.paraFile.setValue("/"+"/y_j", self.sourceY.value())
        self.paraFile.setValue("/"+"/theta_e", self.angle.value())
        self.paraFile.setValue("/"+"/theta_la", self.lanexAngle.value())
        self.paraFile.setValue("/"+"/B", self.Bbox.value())
        self.paraFile.setValue("/"+"/x_d", self.lanexX.value())
        self.paraFile.setValue("/"+"/y_d", self.lanexY.value())
        self.paraFile.setValue("/"+"/Emin", self.EminBox.value())
        self.paraFile.setValue("/"+"/Emax", self.EmaxBox.value())
        self.paraFile.setValue("/"+"/N", self.NBox.value())
        self.paraFile.setValue("/"+"/div", self.divBox.value())
        self.paraFile.setValue("/"+"/long_lanex", self.lanexBox.value())
        self.paraFile.setValue("/"+"/sens_B", self.BSensBox.value())
        self.paraFile.setValue("/"+"/LM", self.AimantLength.value())
        self.paraFile.setValue("/"+"/LaM", self.AimantWidth.value())
        
        # # Position du jet par rapport ? (0,0):
        self.x_j = self.sourceX.value()  # 0  # en mm
        self.y_j = self.sourceY.value()  # -1200  # en mm
        
        # # Angle du faisceau par rapport a l'axe y
        self.theta_e = self.angle.value()*np.pi/180  # 0

        # # Position Lanex
        self.x_d = self.lanexX.value()  # 250
        self.y_d = self.lanexY.value()  # 675
        self.theta_la = self.lanexAngle.value()  # -90  #
        self.theta_l = self.theta_la*np.pi/180

        # # Champ
        self.B = self.Bbox.value()  # 1.4  # Tesla
        self.L = self.AimantLength.value()
        self.La = self.AimantWidth.value()

        # # Parametres de Calcul
        self.Emin = int(self.EminBox.value())  # 20  # en Mev
        self.Emax = int(self.EmaxBox.value())  # 4000
        self.Nt = int(self.NBox.value())  # 100  # nombre de trjectoire
        self.progressBar.setMaximum(int(self.Nt)-1)
        self.div = self.divBox.value() * 1e-3  # 1e-3  # divergence FWHM du faisceau en radian (calcul resolution) 
        self.long_lanex = self.lanexBox.value()  # 870  # mm
        self.sens_B = self.BSensBox.value()  # -1  # =1 si le fichier contenant Bz(x,y) donne le bon signe, =-1 inverse le signe de B(x,y) 

    def BLoad(self):
        dialog = QFileDialog()
        self.BFileName, _ = dialog.getOpenFileName()
        # Update the label text to display the selected file name
        if self.BFileName:
            self.pathBLine.setText(str(self.BFileName))
            self.paraFile.setValue("/"+"/Bpath", self.BFileName)

    def startCalcul(self):
        self.threadCalcul.start()

    def progress(self, rem):
        self.progressBar.setValue(int(rem[0]))
        self.EcalLabel.setText(str(round(rem[1],2)) + ' Mev')
        self.EcalLabel.setStyleSheet("QLabel {color:rgb(%f,%f,%f)}" % (rem[2][0], rem[2][1], rem[2][2]))

    def stopCalcul(self):
        self.threadCalcul.stop = True

    def openF(self):
        # open ini saved file
        fname = QFileDialog.getOpenFileNames(self, "Open File")
        self.openedFiles = fname[0]
        self.openedFiles = fname[0]
        fichier = self.openedFiles[0]
        ext = os.path.splitext(fichier)[1]
        print('fichier to load', fichier)
        if ext == '.ini':  # ini fi
            self.paraFile = QtCore.QSettings(fichier, QtCore.QSettings.Format.IniFormat)
            self.iniValue()

    def saveF(self):
        # save ini saved file
        print(open)
        fname = QFileDialog.getSaveFileName(self, "Save parameter file ")
        self.path = os.path.dirname(str(fname[0]))
        fichier = fname[0]+'.ini'
        print(fichier, ' is saved')
        fichierS = str(self.p.parent / 'defaultTrajectory.ini')
        with open(fichierS, 'r') as f:
            dataS = f.read()
        with open(fichier, 'w') as f:
            f.write(dataS)

    def exportF(self):
        # open ini saved file
        # 1ere colonne = energie electron en MeV
        # 2eme colonne = derivee de s par l'energie E (ds/dE) en mm/MeV
        # 3eme colonne = position s sur le lanex en mm
        # 4eme colonne = angle des electrons par rapport ? Ox (sens)
        # 5eme colone = distance parcourue par les electrons
        fname = QFileDialog.getSaveFileName(self, "export dispersion file ")
        fichier = fname[0]+'.txt'
        dat = np.array([self.threadCalcul.EInter, self.threadCalcul.ds_dE, self.threadCalcul.sInter, self.threadCalcul.thetaInter, self.threadCalcul.DsourceInter])
        dat = dat.T
        np.savetxt(str(fichier), dat)
        if self.parent is not None:
            self.parent.confSpectro.setValue("/"+"/dsde_name",str(fichier))
    
    def mouseMoved(self, evt):
        # to print position of the mouse on the second graph   
        pos = evt[0]  # using signal proxy turns original arguments into a tuple
        
        if self.threadCalcul.E is not None:
            if self.p1.sceneBoundingRect().contains(pos):
                mousePoint = self.vb.mapSceneToView(pos)
                mx = np.array([abs(i-mousePoint.x()) for i in self.threadCalcul.E])
                index = mx.argmin()
                #if index >= 0 and index < len(self.threadCalcul.E):
                self.xMouse = (mousePoint.x())
                self.yMouse = (mousePoint.y())
                    # self.xMc = self.threadCalcul.E[index]
                    # self.yMc = self.threadCalcul.s[index]
                self.label_Cross.setText(str(round((self.xMouse), 2)) + '    ,    '+ str(round(self.yMouse, 2)))
                    
    def CheckChangeB(self):
        if self.checkB.isChecked() is True:
            self.AimantLength.setEnabled(True)
            self.AimantWidth.setEnabled(True)
            self.labelAimantLength.setEnabled(True)
            self.labelAimantWidth.setEnabled(True)
            self.BButton.setEnabled(False)
            self.pathBLine.setEnabled(False)
        else:
            self.AimantLength.setEnabled(False)
            self.AimantWidth.setEnabled(False)
            self.labelAimantLength.setEnabled(False)
            self.labelAimantWidth.setEnabled(False)
            self.BButton.setEnabled(True)
            self.pathBLine.setEnabled(True)

    def DispDisplay(self):
        self.winDisp.PLOT(self.threadCalcul.sInter, axis=self.threadCalcul.EInter, label='E (Mev)', labelY='Lanex Screen (mm)')

    def DistDisplay(self):
        self.winDist.PLOT(self.threadCalcul.DsourceInter, axis=self.threadCalcul.EInter, label='E (Mev)', labelY='D (mm)')
    
    def DsDEDisplay(self):
        self.winDsDE.PLOT(self.threadCalcul.ds_dE, axis=self.threadCalcul.EInter, label='E (Mev)', labelY='Ds/DE (mm/Mev)')

    def ResolDisplay(self):
        self.winResol.PLOT(self.threadCalcul.resolInter, axis=self.threadCalcul.EInter, label='E (Mev)', labelY='Resolution(%)')

    def open_widget(self, fene):
        """ open new widget
        """
        
        if fene.isWinOpen is False:
            fene.setup
            fene.isWinOpen = True
            fene.show()
        else:
            # fene.activateWindow()
            # fene.raise_()
            fene.showNormal()
    
    def closeEvent(self, event):
        """ when closing the window
        """
        self.isWinOpen = False

class CALCULTHREAD(QtCore.QThread):
    '''
    Secon thread  to calcul the trajectory
    '''
    remain = QtCore.pyqtSignal(object)
    

    def __init__(self, parent=None):
        super(CALCULTHREAD, self).__init__()
        self.parent = parent
        self.E = None
        self.aa = 0
        

    def wc_interp(self, x, y):
        #  return wc interpollated x,y in mm =0 if x,y  out of the file
        #  f  = interp2d(self.xmap, self.ymap, self.wcmap)  # depreciated
        f = RectBivariateSpline(self.xmap, self.ymap, self.wcmap.T)
        if x < self.xmap.min() or x > self.xmap.max() or y < self.ymap.min() or y > self.ymap.max():
            # x,y not in the B file wc=0
            return 0
        else:
            return f(x, y)[0][0]

    def odefun(self, t, y):
        # differential equation
        # v=Y[0]ex+y[1]ey x=Y[2]ex+Y[3]ey
        dydt = np.zeros(4)  
        if self.parent.checkB.isChecked() is False:  # b from file with interpolation

            dydt[0] = - self.wc_interp(y[2]*1e3, y[3]*1e3) * y[1] / np.sqrt(1 + y[0]**2 + y[1]**2)
            dydt[1] = self.wc_interp(y[2]*1e3, y[3]*1e3) * y[0] / np.sqrt(1 + y[0]**2 + y[1]**2)
            dydt[2] = c * y[0] / np.sqrt(1 + y[0]**2 + y[1]**2)
            dydt[3] = c * y[1] / np.sqrt(1 + y[0]**2 + y[1]**2)

        else:  # B constant
            
            if (-1*self.parent.L/2  < y[3]*1e3 < self.parent.L/2 ) and (-self.parent.La/2 < y[2]*1e3  < self.parent.La/2):
                #print('dans aimant')
                dydt[0] = -self.wc * y[1] / np.sqrt(1 + y[0]**2 + y[1]**2)
                dydt[1] = self.wc * y[0] / np.sqrt(1 + y[0]**2 + y[1]**2)
                dydt[2] = c * y[0] / np.sqrt(1 + y[0]**2 + y[1]**2)
                dydt[3] = c * y[1] / np.sqrt(1 + y[0]**2 + y[1]**2)
            else:
                # print('hors aimant')resol
                dydt[0] = 0  # B=0
                dydt[1] = 0
                dydt[2] = c * y[0] / np.sqrt(1 + y[0]**2 + y[1]**2)
                dydt[3] = c * y[1] / np.sqrt(1 + y[0]**2 + y[1]**2)
        return dydt

    def run(self):
        # when start button is pressed start the calculation 
        print('calcul ...')
        self.parent.p1.clear()
        self.parent.p2.clear()
        self.stop = False
        self.parent.p1.addItem(self.parent.imh)
        time.sleep(0.1)
        E = []
        sol = []

        def event(t, x):
            # to stop the calculation when electron arrive on the lanex 
            D = (x[2] * 1e3 - self.parent.x_d)  * np.tan(self.parent.theta_l) - (x[3] * 1e3 - self.parent.y_d)  # intersection dans le plan du lanex
            #D = (x[2] * 1e3 - self.parent.x_d)
            return D

        event.terminal = True

        # # Energie de electrons :resol
        E = np.linspace(self.parent.Emin, self.parent.Emax, self.parent.Nt)
        dE = abs(E[2]-E[1])

        # Gamma
        gamma = E * (e/(m_e * c**2) * 1e6) + 1  # E est en MeV  
        beta = np.sqrt((gamma**2)-1)/gamma

        self.wc = self.parent.sens_B*e * self.parent.B/m_e  # wc est la fréquence cyclotron

        # Positions initiales 
        x0 = np.zeros(self.parent.Nt) + self.parent.x_j*1e-3
        y0 = np.zeros(self.parent.Nt) + self.parent.y_j*1e-3

        # Impulsions initiales (ici u=gamma*beta=p/mc)
        ux0 = -np.ones(self.parent.Nt) * gamma * beta * np.sin(self.parent.theta_e)
        uy0 = np.ones(self.parent.Nt) * gamma * beta * np.cos(self.parent.theta_e)

        if self.parent.checkB.isChecked() is False:
            data_B = np.loadtxt(str(self.parent.BFileName))
            self.xmap = data_B[0, 1:]
            print('bMax',max(self.xmap))
            self.xmap = data_B[0, 1:] 
            self.xmax = max(self.xmap)
            self.xmin = min(self.xmap)
            self.ymap = data_B[1:, 0]
            self.ymax = max(self.ymap)
            self.ymin = min(self.ymap)
            self.Bmap = data_B[1:, 1:]
            print('B Max',self.Bmap.max())
            if self.xmap[0]>self.xmap[1] :
                self.xmap = np.flip(self.xmap)
            if self.ymap[0]>self.ymap[1] :
                self.ymap = np.flip(self.ymap)    
            self.wcmap = self.parent.sens_B*e*self.Bmap/m_e
            print('calul avec B file',self.xmax,self.xmin,self.ymax,self.ymin)
            print(self.xmap)
            #  Translation and scaling the image
            tr = QtGui.QTransform()  # prepare ImageItem transformation:
            self.scaleX = self.xmap[1] - self.xmap[2]       
            self.scaleY = self.ymap[1] - self.ymap[2]
            tr.scale(self.scaleX, self.scaleY)  # scale horizontal and vertical axes
            self.transX = (self.xmax-self.xmin)/2
            self.transY = (self.ymax-self.ymin)/2
            tr.translate(self.transX/self.scaleX, self.transY/self.scaleY)  # to locate maximum at axis origin      
            self.parent.imh.setImage(self.Bmap.T)
            self.parent.imh.setTransform(tr)  # assign transform
            # plt.imshow(self.Bmap)
            # plt.show()
        else:
            #  plot rectangle to show  the magnet
            self.parent.p1.plot([-self.parent.La/2, self.parent.La/2], [-self.parent.L/2, -self.parent.L/2], pen='b')
            self.parent.p1.plot([-self.parent.La/2, self.parent.La/2], [self.parent.L/2, self.parent.L/2], pen='b')
            self.parent.p1.plot([-self.parent.La/2, -self.parent.La/2], [-self.parent.L/2, self.parent.L/2], pen='b')
            self.parent.p1.plot([self.parent.La/2, self.parent.La/2], [-self.parent.L/2, self.parent.L/2], pen='b')
        
        #  =============================================================================
        #  Projection sur le lanex
        #  =============================================================================

        x_lanex_end = self.parent.x_d - self.parent.long_lanex * np.cos(self.parent.theta_l)
        y_lanex_end = self.parent.y_d - self.parent.long_lanex * np.sin(self.parent.theta_l)
        #  plot line to show the lanex
        self.parent.p1.plot([self.parent.x_d, x_lanex_end], [self.parent.y_d, y_lanex_end], pen='red')
        
        Dsource = np.zeros(self.parent.Nt)
        x_P = np.zeros(self.parent.Nt)
        y_P = np.zeros(self.parent.Nt)
        theta = np.zeros(self.parent.Nt)
        #calcul trajectoire
        for i in range(0, self.parent.Nt):
            if self.stop is True:
                break
            # print('trajectoire nb : ', i, E[i], 'Mev')
            #input('appuyer pour continuer...')
        
            # Résolution de l'équation différentielle
            
            sol = solve_ivp(self.odefun, [0, abs(3000*np.pi/self.wc)], 
                            np.array([ux0[i], uy0[i], x0[i], y0[i]]),
                            method='LSODA', events=event,rtol=3e-14) #'LSODA' RK45 atol=3e-14, 
            
            # Représentation graphique des trajectoires
            # define random color
            col = (255*np.random.random(), 255*np.random.random(), 255*np.random.random())
            prog = [i, E[i], col] # send to mainGui i, E,color for the progress bar and show Energy 
            self.remain.emit(prog) 
            if i % 5 ==0 :  # too slow with a lot of trejectory :plot only the 5th and then only one
                self.winplot = self.parent.p1.plot(sol.y[2] * 1e3, sol.y[3] * 1e3, pen=col, clear=False)
            else:
                self.winplot.setData(sol.y[2] * 1e3, sol.y[3] * 1e3, pen=col)
            # a=[sol.y[2], sol.y[3]]
            # self.plotData.emit(a)

            # Calcul de la distance parcourue par les électrons
            for j in range(0, (sol.y[1]).shape[0]-1):
                Dsource[i] = Dsource[i] + np.sqrt((sol.y[2, j+1] * 1e3 - sol.y[2, j] * 1e3)**2 + (sol.y[3, j+1] * 1e3 - sol.y[3,j] * 1e3)**2)
            
            # Résultats
            x_P[i] = sol.y[2, -1] * 1e3
            y_P[i] = sol.y[3, -1] * 1e3    # Point P l'arrivée sur le lanex (coordonnées en mm)
            theta[i] = np.arctan2(sol.y[1, -1], sol.y[0, -1])       # angle de sortie de l'électron par rapport à l'axe Ox (sens trigonométrique)
            #print(E[i], 'Mev pos lanex : ', x_P[i], y_P[i], theta[i],'rad')
        
        # Coordonnée s le long du détecteur
        if np.cos(self.parent.theta_l) < 0.1:
            s = -(y_P - self.parent.y_d) / np.sin(self.parent.theta_l)
        else:
            s = -(x_P - self.parent.x_d) / np.cos(self.parent.theta_l)

        #print('Coordonees le long lanex', s)

        # Calcul de ds_dE 
        self.E = E
        self.EInter = E[1:] - dE / 2
        self.s = s  # position sur le dectecteur
        self.theta = theta
        self.ds_dE = np.diff(self.s) / np.diff(E)
        
        self.Dsource = Dsource  # distance parcouru
        
        f_s3 = interp1d(E, s) # fct for  interpol 
        self.sInter = f_s3(self.EInter) # intef pol de s vs E
        f_theta3 = interp1d(E, theta)
        self.thetaInter = f_theta3(self.EInter)

        f_d = interp1d(E, Dsource) # fct for  interpol 
        self.DsourceInter = f_d(self.EInter)
        # plot dispersion en fct E 
        #self.parent.p2.plot(E, self.s, symbol='+', name='no interp', symbolBrush='w', symbolSize= 3)
        #self.parent.p2.plot(self.EInter, self.sInter, pen='r', name="interpolation")
        
        self.resolInter = 2*self.DsourceInter*np.tan(self.parent.div/2)

        self.resolInter= 100*(self.resolInter/self.ds_dE )/ self.EInter

        # self.parent.p2.plot(self.E, self.ds_dE3)
        # self.parent.p2.plot(self.E, self.ds_dE, pen='r')

        # self.parent.p2.plot(self.E, self.Dsource, symbol='t')
        # self.parent.p2.plot(self.EInter, self.DsourceInter, pen='b')


if __name__ == "__main__":

    appli = QApplication(sys.argv)
    appli.setStyleSheet(qdarkstyle.load_stylesheet(qt_api='pyqt6'))
    w = WINTRAJECTOIRE()
    w.show()
    appli.exec()
