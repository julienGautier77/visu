#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on 2023/07/01
@author: juliengautier & leopold Rousseau
window image
"""

from PyQt6.QtWidgets import QApplication, QVBoxLayout, QWidget
from PyQt6.QtWidgets import QLabel, QMainWindow, QFileDialog,QStatusBar
from PyQt6 import QtCore, QtGui
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QAction
from PyQt6.QtGui import QIcon, QShortcut
from PIL import Image
import sys
import time
import pyqtgraph as pg  # pyqtgraph biblio permettent l'affichage
import numpy as np
import qdarkstyle  # pip install qdakstyle https://github.com/ColinDuquesnoy/QDarkStyleSheet  sur conda
import os
import pathlib
from scipy.ndimage import median_filter
#from winCrop import WINCROP
from visu.WinCut import GRAPHCUT
from visu.winMeas import MEAS
from visu.InputElectrons import InputE
from visu.CalculTraj import WINTRAJECTOIRE

class WINSPECTRO(QMainWindow):
    signalMeas = QtCore.pyqtSignal(object)
    def __init__(self, parent=None, file=None, conf=None, name='VISU',**kwds):
        
        super().__init__()
        self.name = name
        self.parent = parent
        p = pathlib.Path(__file__)
        if conf is None:
            self.conf = QtCore.QSettings(str(p.parent / 'confVisu.ini'), QtCore.QSettings.Format.IniFormat)
        else:
            self.conf = conf
        self.confSpectro = QtCore.QSettings(str(p.parent / 'default_values.ini'), QtCore.QSettings.Format.IniFormat)
        sepa = os.sep
        self.icon = str(p.parent) + sepa+'icons' + sepa
        self.path = self.conf.value(self.name+"/path")
        self.isWinOpen = False
        self.setWindowTitle('Electrons spectrometer')
        self.setWindowIcon(QIcon(self.icon+'LOA.png'))
        self.setStyleSheet(qdarkstyle.load_stylesheet(qt_api='pyqt6'))
        self.left = 100
        self.top = 30
        self.width = 800
        self.height = 800
        self.setGeometry(self.left, self.top, self.width, self.height)
        
        self.nomFichier = ''
        self.ite = None
        if "confMot" in kwds:
            self.confMot = kwds["confMot"]  # le Qsetting des moteurs
            self.winM = MEAS(parent=self, confMot=self.confMot, conf=self.conf, name=self.name)
        else:
            self.winM = MEAS(parent=self, conf=self.conf, name=self.name)
        self.winM .setWindowTitle('SPECTRO MEASUREMENTS')
        self.setWindowIcon(QIcon('./icons/LOA.png'))
        self.winInputE=InputE(parent=self)
        self.winTrajectory = WINTRAJECTOIRE(parent=self)
        # self.win2=WINCROP()
        # self.win3=WINCROP()
        self.winplot=GRAPHCUT()
        self.setup()
        self.shortcut()
        self.actionButton()

        if file is not None:
            self.dataOrg = Image.open(file)
            self.dataOrg = np.array(self.dataOrg)
            self.dataOrg = np.rot90(self.dataOrg, 3)
        
            self.SpectroChanged()
        else :
            self.spectroInputValue()

    def setup(self):
        
        self.toolBar = self.addToolBar('tools')
        self.toolBar.setMovable(False)

        menubar = self.menuBar()
        menubar.setNativeMenuBar(False)
        self.statusBar = QStatusBar()
        self.setContentsMargins(0, 0, 0, 0)
        
        self.setStatusBar(self.statusBar)
        self.fileMenu = menubar.addMenu('&File')
        self.ImageMenu = menubar.addMenu('&Image')
        self.optionMenu = menubar.addMenu('&Options')
        self.AnalyseMenu = menubar.addMenu('&Analyse')
        self.openAct = QAction(QtGui.QIcon(self.icon+"Open.png"), 'Open File', self)
        self.openAct.setShortcut('Ctrl+o')
        self.toolBar.addAction(self.openAct)
        self.openAct.triggered.connect(self.OpenF)
        
        self.fileMenu.addAction(self.openAct)
        
        self.saveAct = QAction(QtGui.QIcon(self.icon+"disketteSave.png"), 'Save file', self)
        self.saveAct.setShortcut('Ctrl+s')
        self.toolBar.addAction(self.saveAct)
        self.saveAct.triggered.connect(self.SaveF)
        
        self.fileMenu.addAction(self.saveAct)

        self.InputEAct=QAction(QtGui.QIcon(self.icon+"pref.png"),
                                     'Input Electrons', self)
        self.InputEAct.triggered.connect(
                lambda: self.open_widget(self.winInputE))
        self.fileMenu.addAction(self.InputEAct)

        self.CalibEAct=QAction(QtGui.QIcon(self.icon+"pref.png"),
                                     'Trajectory', self)
        self.CalibEAct.triggered.connect(
                lambda: self.open_widget(self.winTrajectory))
        self.fileMenu.addAction(self.CalibEAct)


        self.checkBoxScale = QAction(QtGui.QIcon(self.icon+"expand.png"), ' Auto Scale on', self)
        self.checkBoxScale.setCheckable(True)
        self.checkBoxScale.setChecked(True)
        self.toolBar.addAction(self.checkBoxScale)
        self.ImageMenu.addAction(self.checkBoxScale)
        self.checkBoxScale.triggered.connect(self.checkBoxScaleImage)
        self.MeasButton = QAction(QtGui.QIcon(self.icon+"laptop.png"),
                                      'Measure', self)
        self.MeasButton.setShortcut('ctrl+m')
        self.MeasButton.triggered.connect(self.Measurement)
        self.AnalyseMenu.addAction(self.MeasButton)
        
        self.rectangleButton = QAction(QtGui.QIcon(self.icon+"rectangle.png"),
                                       'Add Rectangle', self)
        self.toolBar.addAction(self.rectangleButton)
        self.rectangleButton.triggered.connect(self.Rectangle)
        # rectangle for measurement
        self.plotRect = pg.RectROI([0, 0], [50,50],
                                   pen='g')
        self.plotRect.sigRegionChangeFinished.connect(self.RectChanged)

        self.label_CrossValue = QLabel()
        self.label_CrossValue.setStyleSheet("font:13pt")
        
        self.label_Cross = QLabel()
        # self.label_Cross.setMaximumHeight(20)
        self.label_Cross.setMaximumWidth(210)
        self.label_Cross.setStyleSheet("font:12pt")
        self.statusBar.addPermanentWidget(self.label_Cross)
        self.statusBar.addPermanentWidget(self.label_CrossValue)

        self.checkBoxBg = QAction('Background Substraction On', self)
        self.checkBoxBg.setCheckable(True)
        self.checkBoxBg.setChecked(False)
        self.checkBoxBg.triggered.connect(self.SpectroChanged)
        self.ImageMenu.addAction(self.checkBoxBg)

        self.vbox2 = QVBoxLayout()
        self.winImage = pg.GraphicsLayoutWidget()
        self.winImage.setContentsMargins(0, 0, 0, 0)
        self.winImage.setAspectLocked(False)
        # self.winImage.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.winImage.ci.setContentsMargins(0, 0, 0, 0)
        self.vbox2.addWidget(self.winImage)
        self.vbox2.setContentsMargins(0, 0, 0, 0)
        
        self.p1 = self.winImage.addPlot()
        self.imh = pg.ImageItem()
        self.axeX = self.p1.getAxis('bottom')
        self.axeY = self.p1.getAxis('left')
        self.p1.addItem(self.imh)
        self.p1.setMouseEnabled(x=False, y=False)
        self.p1.setContentsMargins(0, 0, 0, 10)
    
        #self.p1.setAspectLocked(True, ratio=1)
        self.p1.showAxis('right', show=False)
        self.p1.showAxis('top', show=False)
        self.p1.showAxis('left', show=True)
    
        self.axeX = self.p1.getAxis('bottom')
        self.axeY = self.p1.getAxis('left')
        self.axeX.setLabel(' Energy (Mev) ')
        self.axeY.setLabel( ' mrad ')

        self.winImage2 = pg.GraphicsLayoutWidget()
        self.winPLOT = self.winImage2.addPlot()
        self.vbox2.addWidget(self.winImage2)
        self.pCut = self.winPLOT.plot()
        self.winPLOT.setLabel('bottom', 'Energy (Mev)')
        self.winPLOT.showAxis('right', show=False)
        self.winPLOT.showAxis('top', show=False)
        self.winPLOT.showAxis('left', show=True)
        self.winPLOT.showAxis('bottom', show=True)
        self.axeX = self.winPLOT.getAxis('bottom')
        self.p1.setAxis=self.axeX

        MainWidget = QWidget()
        MainWidget.setLayout(self.vbox2)
        self.setCentralWidget(MainWidget)

        # histogramvalue()
        self.hist = pg.HistogramLUTItem()
        self.hist.setImageItem(self.imh)
        self.hist.autoHistogramRange()
        self.hist.gradient.loadPreset('flame')
        # rectangle Selection ROI spectro
        self.rectSelectSpectro = pg.RectROI([50, 50], [4*10, 20],
                                            pen='w')
        self.rectSelectSpectro.setPos([self.winInputE.wmin.value(),self.winInputE.hmin.value()])
        self.rectSelectSpectro.setSize([self.winInputE.wmax.value() - self.winInputE.wmin.value(),
                                        self.winInputE.hmax.value() - self.winInputE.hmin.value()])

        if self.parent is not None:
            # if signal emit in another thread (see visual)
            self.parent.signalSpectro.connect(self.Display)

    def checkBoxScaleImage(self):

        if self.checkBoxScale.isChecked():
            self.checkBoxScale.setIcon(QtGui.QIcon(self.icon+"expand.png"))
            self.checkBoxScale.setText('Auto Scale On')
        else:
            self.checkBoxScale.setIcon(QtGui.QIcon(self.icon+"minimize.png"))
            self.checkBoxScale.setText('Auto Scale Off')
    
    def Display(self, data):

        # self.open_widget(self.win2)
        # self.open_widget(self.winplot)
        # self.open_widget(self.win3)
        # self.win2.setWindowTitle('win Background crop )')
        
        self.dataOrg=data
        self.data = data[self.wmin:self.wmax+1,self.hmin:self.hmax+1]
        self.dimx = self.data.shape[0]
        self.dimy = self.data.shape[1]
        
        if self.checkBoxBg.isChecked() is True:
            # print('hmin hmax',self.winInputE.hminBg,self.winInputE.hmaxBg)
            #self.bg = self.winInputE.rectSelectBack.getArrayRegion(spectrum_2D.T, self.imh)
            self.bg =self.data[:, self.winInputE.hminBg:self.winInputE.hmaxBg ] # 

            # self.win3.Display(self.bg)
            # self.win3.setWindowTitle('win bg crop')
            if self.filterMed >0:
                self.data = np.array(median_filter(self.data , self.filterMed))
                self.bg = median_filter(self.bg , self.filterMed)
            self.bg = self.bg.mean(axis=1)
            
            # print('shape bg ligne',self.bg.shape)
            # print('data size' ,self.data.shape)
            # self.winplot.PLOT(self.bg)
            
            self.bg2 = np.tile(self.bg,self.data.shape[1])
            # print('shape bg tile',self.bg.shape)
            #self.bg = np.reshape(self.bg2,[self.data.shape[1],self.data.shape[0]])
            self.bg = np.reshape(self.bg2,[self.data.shape[0],self.data.shape[1]],order='F')
            # print('data shape' ,self.data.shape)
            # print('bg size 2' ,self.bg.shape)
            # self.win2.Display(self.bg)
            # self.win2.setWindowTitle('win bg reconstitué )')
            self.data=self.data - self.bg
        else:
            if self.filterMed >0:
                self.data = np.array(median_filter(self.data , self.filterMed))

        self.data[self.data<0] = 0 #change all negative values to 0
        # to be changed no need to be interpolate at each display
        #self.energy_max = int(np.interp((self.s0-self.dimx+1)/self.ppmm, self.slist[::-1], self.elist[::-1]))
        self.energy_max=(np.interp((self.wmax-self.s0)/self.ppmm, self.slist, self.elist))
        self.energy_min =(np.interp((self.wmin-self.s0)/self.ppmm, self.slist,self.elist))
        print('Emin:', self.energy_min,'Emax:', self.energy_max,self.ppmm)
        print('Xmin', (self.wmin-self.s0)/self.ppmm,'Xmax', (self.wmax-self.s0)/self.ppmm)
        self.E = np.linspace(self.energy_min,self.energy_max,self.npoints) 
        ds_dE = abs(np.interp(self.E, self.elist, self.dsdelist))
        
        #  Calculate angle range:
        
        p_y0 = np.unravel_index(np.argmax(self.data), self.data.shape)[1]
        self.theta_max = (self.dimy-1 - p_y0) / self.ppmm / self.ssd  # minimum angle [mrad] 
        self.theta_min = (- p_y0) / self.ppmm / self.ssd  # maximum angle [mrad] 
        deltaTheta = self.theta_max - self.theta_min
        self.scaleY = deltaTheta/self.dimy
        self.scaleX = (self.energy_max-self.energy_min)/self.npoints

        #  Create and fill a new array for the 2D spectrum
        spectrum_2D = np.empty((self.dimy, 0))
        
        for i in range(self.npoints-1):
            # self.s0 position pixel 0 lanex
            # position in px of E in the filtered image = mm/0 lanex * ppm +px_zerolanex -pixel fenetre
            px_float = round(self.ppmm * np.interp(self.E[i], self.elist, self.slist)) - self.wmin + self.s0
            #p rint('pixel dans data win',px_float,self.E[i],round(self.ppmm * np.interp(self.E[i], self.elist, self.slist)))
            # print('pixel dans data org',self.ppmm*np.interp(self.E[i], self.elist, self.slist),self.E[i])
            px0 = int(np.trunc( px_float)) #floor
            # print(i,px0,self.data.shape)
            px1 = px0 +1
            if px1 > self.data.shape[0]-1 :
                px1 = px1 - 1 
            row = np.array([(px1-px_float) * self.data[px0,:] + (px_float-px0) * self.data[px1,:]]).T
            spectrum_2D = np.hstack([ spectrum_2D , row * ds_dE[i] ]) 
                
        spectrum_2D = np.hstack([ spectrum_2D , np.array([self.data[-1,:]]).T* ds_dE[i] ])
        self.theta=np.linspace(self.theta_min,self.theta_max,self.data.shape[1])
    
            #  Translation and scaling the image
        tr = QtGui.QTransform()  # prepare ImageItem transformation:
        tr.scale(self.scaleX, self.scaleY)       # scale horizontal and vertical axes
        self.transX=self.energy_min/self.scaleX
        self.transY=-p_y0
        tr.translate(self.energy_min/self.scaleX, self.transY) #  to locate maximum at axis origin
        self.imh.setTransform(tr) # assign transform

        if self.checkBoxScale.isChecked():
            self.imh.setImage(spectrum_2D.T, autoLevels=True, autoDownsample=True) 
        else:
            self.imh.setImage(spectrum_2D.T, autoLevels=False, autoDownsample=True) 

        self.p1.setXRange(self.energy_min,self.energy_max)
        self.pCut.setData(self.E,spectrum_2D.sum(axis=0))
        self.winPLOT.setXRange(self.energy_min,self.energy_max)
        self.data = spectrum_2D.T
        self.dimx = self.data.shape[0]
        self.dimy = self.data.shape[1]

        if self.winM.isWinOpen is True:  # measurement update
            if self.ite == 'rect': # rest selection is selected
                self.RectChanged()
                self.Measurement()
            else:
                self.Measurement()
        # except:
        #     self.errorDisplay = True
        #     print('error Display: Calibrate')


    def shortcut(self):
        # keyboard shortcut
        self.shortcutPu = QShortcut(QtGui.QKeySequence("+"), self)
        self.shortcutPu.activated.connect(self.paletteup)
        self.shortcutPu.setContext(Qt.ShortcutContext(3))
        # 3: The shortcut is active when its parent widget, or any of its children has focus. default O The shortcut is active when its parent widget has focus.
        self.shortcutPd = QtGui.QShortcut(QtGui.QKeySequence("-"), self)
        self.shortcutPd.activated.connect(self.palettedown)
        self.shortcutPd.setContext(Qt.ShortcutContext(3))
        # mousse action:
        self.proxy = pg.SignalProxy(self.p1.scene().sigMouseMoved, rateLimit=60, slot=self.mouseMoved)
        # self.p1.scene().sigMouseClicked.connect(self.mouseClick)
        # self.vb=self.p1.vb

    def actionButton (self):
        self.winInputE.selectButton.clicked.connect(self.selectDimSpectro)
        self.rectSelectSpectro.sigRegionChangeFinished.connect(self.changeDimSpectro)
        self.winInputE.wmin.editingFinished.connect(self.SpectroChanged)
        self.winInputE.wmax.editingFinished.connect(self.SpectroChanged)
        self.winInputE.hmin.editingFinished.connect(self.SpectroChanged)
        self.winInputE.hmax.editingFinished.connect(self.SpectroChanged)    
        self.winInputE.medfilt.editingFinished.connect(self.SpectroChanged)
        self.winInputE.npoints.editingFinished.connect(self.SpectroChanged)
        self.winInputE.ppmm.editingFinished.connect(self.SpectroChanged)
        self.winInputE.pps0.editingFinished.connect(self.SpectroChanged)
        self.winInputE.ssd.editingFinished.connect(self.SpectroChanged)
        self.winInputE.count.editingFinished.connect(self.SpectroChanged)
        self.winInputE.selected_dsde_label.textChanged.connect(self.SpectroChanged)

    def paletteup(self):
        # change the color scale
        levels = self.imh.getLevels()
        if levels[0] is None:
            xmax = self.data.max()
            xmin = self.data.min()
        else:
            xmax = levels[1]
            xmin = levels[0]
        self.imh.setLevels([xmin, xmax-(xmax - xmin) / 10])
        self.hist.setHistogramRange(xmin, xmax)

    def palettedown(self):
        levels = self.imh.getLevels()
        if levels[0] is None:
            xmax = self.data.max()
            xmin = self.data.min()
        else:
            xmax = levels[1]
            xmin = levels[0]
        self.imh.setLevels([xmin, xmax + (xmax - xmin) / 10])
        self.hist.setHistogramRange(xmin, xmax)

    def OpenF(self, fileOpen=False):

        fname = QFileDialog.getOpenFileNames(self, "Open File")
        self.openedFiles = fname[0]
        fichier = self.openedFiles[0]
        ext = os.path.splitext(fichier)[1]
        
        if ext == '.txt':  # text file
            data = np.loadtxt(str(fichier))
        elif ext == '.TIFF' or ext == '.tif' or ext == '.Tiff' or ext == '.jpg' or ext == '.JPEG' or ext == '.png':  # tiff File
            dat = Image.open(fichier)
            data = np.array(dat)
            data = np.rot90(data, 3)
        
        self.Display(data)
        

    def SaveF(self):
        # save as tiff
        fname = QFileDialog.getSaveFileName(self, "Save data as TIFF", self.path)
        self.path = os.path.dirname(str(fname[0]))
        fichier = fname[0]
        print(fichier, ' is saved')
        self.conf.setValue(self.name+"/path", self.path)
        time.sleep(0.1)
        self.dataS = np.rot90(self.data, 1)
        img_PIL = Image.fromarray(self.dataS)
        img_PIL.save(str(fname[0])+'.TIFF', format='TIFF')
        
    def mouseMoved(self, evt):
        pos = evt[0]  # using signal proxy turns original arguments into a tuple
        if self.p1.sceneBoundingRect().contains(pos):
            mousePoint = self.p1.vb.mapSceneToView(pos)
            self.xMouse = (mousePoint.x())
            self.yMouse = (mousePoint.y())
            if ((self.xMouse > self.energy_min and self.xMouse < self.energy_max ) and (self.yMouse > self.theta_min and self.yMouse < self.theta_max)):
                self.xc = self.xMouse
                self.yc = self.yMouse
                try:
                    dataCross = (self.data[int(self.xc), int(self.yc)] ) * self.countPerPixel
                except:
                    dataCross = 0  # evoid to have an error if cross if out of the image
                    self.xc = 0
                    self.yc = 0
                
                self.label_Cross.setText('x=' + str(round(self.xc,1)) + ' Mev  '+ ' y=' + str(round(self.yc,1)) + ' mrad  ' )
                
                dataCross = round(dataCross, 3)  # take data  value  on the cross
                self.label_CrossValue.setText(' v.=' + str(dataCross)+ ' C/Mev')

    def Rectangle(self):
        if self.ite == 'rect':
            self.p1.removeItem(self.plotRect)
            self.ite = None
        else:
            self.ite = 'rect'
            self.p1.addItem(self.plotRect)
            self.plotRect.setPos([100, 0])

    def RectChanged(self):
        '''Take ROIself.s0 = self.winInputE.pps0.value() # pixel position of high energy
        self.wmin = int(self.winInputE.wmin.value()) # dimension
        self.wmax = int(self.winInputE.wmax.value())
        self.hmin = int(self.winInputE.hmin.value())
        self.hmax = int(self.winInputE.hmax.value())
        self.ppmm = self.winInputE.ppmm.value() # pixel per millimeter
        self.npoints = int(self.winInputE.npoints.value()) # nombre de point
        self.ssd= self.winInputE.ssd.value()  # source screen distance
        self.slist = self.winInputE.slist
        self.elist = self.winInputE.elist
        self.dsdelist = self.winInputE.dsdelist
        self.filterMed = int(self.winInputE.medfilt.value())
        self.countPerPixel = self.winInputE.count.value()
        '''
        self.cut = (self.plotRect.getArrayRegion(self.data, self.imh))
        self.xini=self.plotRect.pos()[0]
        self.yini=self.plotRect.pos()[1]
        
        # # Rectangle stay inside view
        # if self.plotRect.pos()[0] < 0:
        #     self.plotRect.setPos([0, self.plotRect.pos()[1]])

        # if self.plotRect.pos()[0]+self.plotRect.size()[0] > self.dimx:
        #     x = self.plotRect.pos()[0]
        #     y = self.plotRect.pos()[1]
        #     sizex = self.dimx-self.plotRect.pos()[0]
        #     sizey = self.plotRect.size()[1]
        #     self.plotRect.setSize([sizex, sizey], update=False)
        #     self.plotRect.setPos([x, y])

        # if self.plotRect.pos()[1]+self.plotRect.size()[1] > self.dimy:
        #     x = self.plotRect.pos()[0]
        #     y = self.plotRect.pos()[1]
        #     sizex = self.plotRect.size()[0]
        #     sizey = self.dimy-self.plotRect.pos()[1]
        #     self.plotRect.setSize([sizex, sizey], update=False)
        #     self.plotRect.setPos([x, y])

        # if self.plotRect.pos()[1] < 0:
        #     self.plotRect.setPos([self.plotRect.pos()[0], 0])

    def spectroFunct(self):
        self.open_widget(self.winSpectro)
        self.SpectroChanged()

    def spectroInputValue(self):
        self.s0 = self.winInputE.pps0.value() # pixel position of lanex origin
        self.wmin = int(self.winInputE.wmin.value()) # dimension
        self.wmax = int(self.winInputE.wmax.value())
        self.hmin = int(self.winInputE.hmin.value())
        self.hmax = int(self.winInputE.hmax.value())
        self.ppmm = self.winInputE.ppmm.value() # pixel per millimeter
        self.npoints = int(self.winInputE.npoints.value()) # nombre de point
        self.ssd= self.winInputE.ssd.value()  # source screen distance
        self.slist = self.winInputE.slist
        self.elist = self.winInputE.elist
        self.dsdelist = self.winInputE.dsdelist
        self.filterMed = int(self.winInputE.medfilt.value())
        self.countPerPixel = self.winInputE.count.value()

    def SpectroChanged(self):
        # print('specto changeged')
        self.spectroInputValue()
        #self.signalSpectro.emit(self.data)
        self.Display(self.dataOrg)
    
    def selectDimSpectro(self):
        
        if self.winInputE.buttonSelected is False :
            self.rectSelectSpectro.setPos([self.winInputE.wmin.value(),self.winInputE.hmin.value()])

            self.rectSelectSpectro.setSize([self.winInputE.wmax.value() - self.winInputE.wmin.value(),
                                        self.winInputE.hmax.value() - self.winInputE.hmin.value()])
            if self.parent is not None:
                self.parent.p1.addItem(self.rectSelectSpectro)
                self.winInputE.buttonSelected = True
        else:
            self.winInputE.buttonSelected = False
            if self.parent is not None:
                self.parent.p1.removeItem(self.rectSelectSpectro)
        
    
    def changeDimSpectro(self):
        self.winInputE.wmin.setValue(int(self.rectSelectSpectro.pos()[0]))
        self.winInputE.wmax.setValue(int(self.rectSelectSpectro.pos()[0] + self.rectSelectSpectro.size()[0] ))
        self.winInputE.hmin.setValue(int(self.rectSelectSpectro.pos()[1]))
        self.winInputE.hmax.setValue(int(self.rectSelectSpectro.pos()[1] + self.rectSelectSpectro.size()[1] ))
        self.SpectroChanged()

    def Measurement(self):
        '''widget for measurement on all image or ROI  (max, min mean ...)
        '''
        if self.ite == 'rect':
            self.RectChanged()
            self.winM.setFile(self.nomFichier)
            self.open_widget(self.winM)
            MeasData=[self.cut*self.countPerPixel,self.xini+self.transX,self.yini+self.transY,self.scaleX,self.scaleY]
            self.signalMeas.emit(MeasData)
      
        if self.ite is None:
            self.winM.setFile(self.nomFichier)
            self.open_widget(self.winM)
            MeasData=[self.data* self.countPerPixel,self.transX,self.transY, self.scaleX, self.scaleY]
            self.signalMeas.emit(MeasData)

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
        
        if self.winInputE.isWinOpen is True:
            self.winInputE.close()
        if self.winM.isWinOpen is True:
            self.winM.close()
        time.sleep(0.1)

        event.accept()
    
        
if __name__ == "__main__":
    appli = QApplication(sys.argv)
    appli.setStyleSheet(qdarkstyle.load_stylesheet(qt_api='pyqt6'))
    file= str(pathlib.Path(__file__).parents[0])+'/tir_025.TIFF'
    e =WINSPECTRO(name='VISU', file=file)
    e.show()
    appli.exec_()
