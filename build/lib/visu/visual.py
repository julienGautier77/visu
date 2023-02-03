#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Jan 30 15:07:27 2019

https://github.com/julienGautier77/visu.git

@author: juliengautier(LOA)
for dark style :
pip install qdarkstyle (https://github.com/ColinDuquesnoy/QDarkStyleSheet.git)

pip install pyqtgraph (https://github.com/pyqtgraph/pyqtgraph.git)
conda install pyopengl 3D plot

created 2021/11/02 : new design
"""



import pyqtgraph as pg  #pip install pyqtgraph (https://github.com/pyqtgraph/pyqtgraph.git)

from PyQt6.QtWidgets import QApplication, QVBoxLayout,QHBoxLayout,QPushButton
from PyQt6.QtWidgets import QInputDialog,QSlider,QLabel,QSizePolicy,QMenu,QMessageBox,QFileDialog
from PyQt6.QtWidgets import QMainWindow,QToolButton,QStatusBar,QFrame
from PyQt6.QtGui import QShortcut,QAction
from PyQt6 import QtCore,QtGui
from PyQt6.QtCore import pyqtSlot,Qt
from PyQt6.QtGui import QIcon

import sys,time,os

import numpy as np
import qdarkstyle # pip install qdarkstyle https://github.com/ColinDuquesnoy/QDarkStyleSheet  sur conda
from scipy.interpolate import splrep, sproot #
from scipy.ndimage import gaussian_filter,median_filter
from PIL import Image
from visu.winspec import SpeFile
from visu.visualLight import SEELIGHT
from visu.winSuppE import WINENCERCLED
from visu.WinCut import GRAPHCUT
from visu.winMeas import MEAS
from visu.WinOption import OPTION
from visu.WinPreference import PREFERENCES
from visu.andor import SifFile
from visu.winFFT import WINFFT
from visu.winMath import WINMATH
from visu.winPointing import WINPOINTING
from visu.winHist import HISTORY
from visu import aboutWindows
from visu.winZoom import ZOOM
# try :
#     from visu.Win3D import GRAPH3D #conda install pyopengl
# except :
#     print ('')
    
import pathlib
import visu

__version__=visu.__version__
__author__=visu.__author__


__all__=['SEE','runVisu']

class SEE(QMainWindow) :
    '''open and plot file : 
        SEE(file='nameFile,path=pathFileName,confpath,confMot,name,aff)
        Make plot profile ands differents measurements(max,min mean...)
        Can open .spe .SPE .sif .TIFF files
        
        
        file = name of the file to open
        path=path of the file to open
        confpath=path  and  file name of the ini file if =None ini file will be the one in visu folder
        confMot usefull if RSAI motors is read
        name= name of the item  in the ini file could be usfull if there is more than two visu widget open in the  same   time
            default is  VISU
        
        kwds :
            aff = "right" or "left" display button on the  right or on the left
            fft="on" or "off" display 1d and 2D fft 
            plot3D 
    '''
    
    signalMeas= QtCore.pyqtSignal(object)
    signalEng=QtCore.pyqtSignal(object)
    signalPointing=QtCore.pyqtSignal(object)
    signalPlot=QtCore.pyqtSignal(object)
    
    def __init__(self,file=None,path=None,parent=None,**kwds):
        
        super().__init__()
        version=__version__
        self.parent=parent
        print("data visualisation version :  ",version)
        p = pathlib.Path(__file__)
        self.fullscreen=False
        self.setAcceptDrops(True)
        sepa=os.sep
        self.icon=str(p.parent) + sepa+'icons' +sepa
        self.colorBar='flame'
        self.setWindowIcon(QIcon(self.icon+'LOA.png'))
        self.nomFichier=''
        self.labelValue=''
        self.aboutWidget=aboutWindows.ABOUT()
        self.signalTrans=dict() #dict to emit multivariable
        self.frameNumber=0
        ### kwds definition  : 
        
        if "confpath"in kwds :   #confpath path.file pour le fichier ini.
            self.confpath=kwds["confpath"]
            if self.confpath==None:
                self.conf=QtCore.QSettings(str(p.parent / 'confVisu.ini'), QtCore.QSettings.Format.IniFormat)
            else:
                self.conf=QtCore.QSettings(self.confpath, QtCore.QSettings.Format.IniFormat)
            print ('configuration path of visu : ',self.confpath)
            
            # print ('conf path visu',self.confpath,self.conf)
        else:
            self.conf=QtCore.QSettings(str(p.parent / 'confVisu.ini'), QtCore.QSettings.Format.IniFormat)
        
        if "conf"in kwds:               #conf : le QSetting
            self.conf=kwds["conf"]
        
        if "color" in kwds:
            self.color=kwds["color"]
        else:
            self.color=None
        
        if "name" in kwds:
            self.name=kwds["name"]
        else:
            self.name="VISU"
        
        print('name :' ,self.name)
        
        if "roiCross" in kwds:
            # print('ROICROSS on')
            self.roiCross=kwds["roiCross"]
        else :
            self.roiCross=False
            # print('no roicross')
        if "aff" in kwds:
            self.aff=kwds["aff"]
        else :
            self.aff="right"
        
        if "fft" in kwds:
            self.fft=kwds["fft"]
        else:
            self.fft="off"
        
        if "meas" in kwds:
            self.meas=kwds["meas"]
        else:
           self.meas="on" 
           
        if "encercled" in kwds:
            self.encercled=kwds["encercled"]
        else:
            self.encercled="on"
        
        
        if self.fft=='on'  :  
            self.winFFT=WINFFT(conf=self.conf,name=self.name)
            self.winFFT1D=GRAPHCUT(symbol=False,title='FFT 1D',conf=self.conf,name=self.name)
          
        if "filter" in kwds:
            self.winFilter=kwds['filter']
        else :
            self.winFilter='on'
            
        if "confMot" in kwds:
            print('motor accepted')
            if self.meas=="on":
                self.confMot=kwds["confMot"]
                # print(self.confMot)
                self.winM=MEAS(parent=self,confMot=self.confMot,conf=self.conf,name=self.name)
        else :
            if self.meas=="on":
                self.winM=MEAS(parent=self,conf=self.conf,name=self.name)
            
        self.winOpt=OPTION(conf=self.conf,name=self.name)
        self.winPref=PREFERENCES(conf=self.conf,name=self.name)
        self.winHistory=HISTORY(self,conf=self.conf,name=self.name)
        
        if self.encercled=="on":
            self.winEncercled=WINENCERCLED(parent=self,conf=self.conf,name=self.name)
        
        if "plot3d" in kwds :
            self.plot3D=kwds["plot3d"]
        else:
            self.plot3D="off"
            
        # if self.plot3D=="on":
            
        #     self.Widget3D=GRAPH3D(self.conf,name=self.name)
        
        
        if "math" in kwds:
            self.math=kwds["math"]
        else :
            self.math="on"
        
        if self.math=="on":
            self.winMath=WINMATH()
            
            
            
        self.winPointing=WINPOINTING(parent=self)
        self.winCoupe=GRAPHCUT(parent=self,symbol=None,conf=self.conf,name=self.name)
        self.path=path
        self.setWindowTitle('Visualization'+'       v.'+ version)
        self.bloqKeyboard=1#bool((self.conf.value(self.name+"/bloqKeyboard"))  )  # block cross by keyboard
        self.bloqq=1 # block the cross by click on mouse
        
        # initialize variable : 
        self.filter='origin' # filter initial value
        self.ite=None
        self.setWindowIcon(QIcon(self.icon+'LOA.png'))
        self.zo=1 # zoom initial value
        self.scaleAxis="off"
        self.plotRectZoomEtat='Zoom'
        self.angleImage=0
        
        self.setup()
        
        def twoD_Gaussian(x,y, amplitude, xo, yo, sigma_x, sigma_y, theta, offset):
           xo = float(xo)
           yo = float(yo)    
           a = (np.cos(theta)**2)/(2*sigma_x**2) + (np.sin(theta)**2)/(2*sigma_y**2)
           b = -(np.sin(2*theta))/(4*sigma_x**2) + (np.sin(2*theta))/(4*sigma_y**2)
           c = (np.sin(theta)**2)/(2*sigma_x**2) + (np.cos(theta)**2)/(2*sigma_y**2)
           return offset + amplitude*np.exp( - (a*((x-xo)**2) + 2*b*(x-xo)*(y-yo) + c*((y-yo)**2)))

        
        if file==None:
            # to have a gaussian picture when we start
            self.dimy=800
            self.dimx=800
            # Create x and y index
            self.x = np.arange(0,self.dimx)
            self.y = np.arange(0,self.dimy)
            self.y,self.x = np.meshgrid(self.y, self.x)
            
            self.data=twoD_Gaussian(self.x, self.y,200, 200, 600, 40, 40, 0, 10)+(50*np.random.rand(self.dimx,self.dimy)).round() 
        
            #self.data=(50*np.random.rand(self.dimx,self.dimy)).round() + 150
        else:
            if path==None:
                self.path=self.conf.value(self.name+"/path")
            
            self.data=self.OpenF(fileOpen=self.path+'/'+file)
        
        
        self.dataOrg=self.data
        self.dataOrgScale=self.data
        
        self.xminR=0
        self.xmaxR=self.dimx
        self.yminR=0
        self.ymaxR=self.dimy
        
        
        self.shortcut()
        self.actionButton()
        self.Display(self.data)
        self.activateWindow()
        self.raise_()
        self.showNormal()
        
        
        
    def setup(self):
        # definition of all button 
        
        TogOff=self.icon+'Toggle_Off.png' 
        TogOn=self.icon+'Toggle_On.png'
        TogOff=pathlib.Path(TogOff)
        TogOff=pathlib.PurePosixPath(TogOff)
        TogOn=pathlib.Path(TogOn)
        TogOn=pathlib.PurePosixPath(TogOn)
        self.hboxBar=QHBoxLayout() 
        
        #self.setStyleSheet("QCheckBox::indicator{width: 30px;height: 30px;}""QCheckBox::indicator:unchecked { image : url(%s);}""QCheckBox::indicator:checked { image:  url(%s);}""QCheckBox{font :10pt;QCheckBox{background-color :red}" % (TogOff,TogOn) )
        
        
        self.toolBar =self.addToolBar('tools')
        self.toolBar.setMovable(False)
        #self.setStyleSheet("{background-color: black}")
        menubar = self.menuBar()
        menubar.setNativeMenuBar(False)
        self.fileMenu = menubar.addMenu('&File')
        self.ImageMenu = menubar.addMenu('&Image')
        self.ProcessMenu = menubar.addMenu('&Process')
        self.AnalyseMenu = menubar.addMenu('&Analyse')
        self.AboutMenu = menubar.addMenu('&About')
        
        self.aboutAction=QAction(QtGui.QIcon(self.icon+"LOA.png'"), 'About', self)
        self.AboutMenu.addAction(self.aboutAction)
        self.aboutAction.triggered.connect(lambda:self.open_widget(self.aboutWidget) )     
        self.statusBar = QStatusBar()
        self.setContentsMargins(0, 0, 0, 0)
        
        self.setStatusBar(self.statusBar)
       
        
        self.vbox1=QVBoxLayout() 
        self.vbox1.setContentsMargins(0, 0, 0, 0)
        
        self.hbox0=QHBoxLayout()
        self.hbox0.setContentsMargins(0, 0, 0, 0)
        self.vbox1.addLayout(self.hbox0)
        
         
        self.openAct = QAction(QtGui.QIcon(self.icon+"Open.png"), 'Open File', self)
        self.openAct.setShortcut('Ctrl+o')
        self.openAct.triggered.connect(self.OpenF)
        self.toolBar.addAction(self.openAct)
        self.fileMenu.addAction(self.openAct)
        
        
        self.openActNewWin = QAction(QtGui.QIcon(self.icon+"Open.png"), 'Open in new window', self)
        #self.openActNewWin.setShortcut('Ctrl+o')
        self.openActNewWin.triggered.connect(self.OpenFNewWin)
        #self.toolBar.addAction(self.openActNewWin)
        self.fileMenu.addAction(self.openActNewWin)
        
        
        self.saveAct=QAction(QtGui.QIcon(self.icon+"disketteSave.png"), 'Save file', self)
        self.saveAct.setShortcut('Ctrl+s')
        self.saveAct.triggered.connect(self.SaveF)
        self.toolBar.addAction(self.saveAct)
        self.fileMenu.addAction(self.saveAct)

        
        self.checkBoxAutoSave=QAction(QtGui.QIcon(self.icon+"diskette.png"),'AutoSave Off',self)
        self.checkBoxAutoSave.setCheckable(True)
        self.checkBoxAutoSave.setChecked(False)
        
        self.checkBoxAutoSave.triggered.connect(self.autoSaveColor)
        self.toolBar.addAction(self.checkBoxAutoSave)
        self.fileMenu.addAction(self.checkBoxAutoSave)
        
        
        self.optionAutoSaveAct=QAction(QtGui.QIcon(self.icon+"Settings.png"),'Options',self) #
        self.optionAutoSaveAct.triggered.connect(lambda:self.open_widget(self.winOpt))
        self.toolBar.addAction(self.optionAutoSaveAct)
        self.fileMenu.addAction(self.optionAutoSaveAct)
        
        self.preferenceAct=QAction(QtGui.QIcon(self.icon+"pref.png"),'Preferences',self) #
        self.preferenceAct.triggered.connect(lambda:self.open_widget(self.winPref))
        
        self.fileMenu.addAction(self.preferenceAct)
        
        self.historyAct=QAction(QtGui.QIcon(self.icon+"time.png"),'&History',self) #
        self.historyAct.triggered.connect(lambda:self.open_widget(self.winHistory))
        self.fileMenu.addAction(self.historyAct)
        
        
        self.checkBoxPlot=QAction(QtGui.QIcon(self.icon+"target.png"),'Cross On (ctrl+b to block ctrl+d to unblock)',self)
        self.checkBoxPlot.setCheckable(True)
        self.checkBoxPlot.setChecked(False)
        self.checkBoxPlot.triggered.connect(self.PlotXY)
        self.toolBar.addAction(self.checkBoxPlot)
        self.AnalyseMenu.addAction(self.checkBoxPlot)
        
        self.maxGraphBox=QAction('Set Cross on the max',self)
        self.maxGraphBox.setCheckable(True)
        self.maxGraphBox.setChecked(False)
        self.maxGraphBox.triggered.connect(self.Coupe)
        self.AnalyseMenu.addAction(self.maxGraphBox)
        
        
        
        self.label_CrossValue=QLabel()
        self.label_CrossValue.setStyleSheet("font:13pt")
        
        self.label_Cross=QLabel()
        #self.label_Cross.setMaximumHeight(20)
        self.label_Cross.setMaximumWidth(170)
        self.label_Cross.setStyleSheet("font:12pt")
        self.statusBar.addPermanentWidget(self.label_Cross)
        self.statusBar.addPermanentWidget(self.label_CrossValue)
        
        self.labelFileName=QLabel("File :")
        self.labelFileName.setStyleSheet("font:8pt;")
        self.labelFileName.setMinimumHeight(30)
        self.labelFileName.setMaximumWidth(40)
        
        self.fileName=QLabel()
        self.fileName.setStyleSheet("font:10pt")
        self.fileName.setMaximumHeight(30)
        self.fileName.setMaximumWidth(200000)
        self.fileName.setAlignment(Qt.AlignmentFlag.AlignVCenter)
        self.statusBar.addWidget(self.labelFileName)
        self.statusBar.addWidget(self.fileName)
        
        self.labelFrameName=QLabel("Frame :")
        self.labelFrameName.setStyleSheet("font:8pt;")
        self.labelFrameName.setMinimumHeight(30)
        self.labelFrameName.setMaximumWidth(70)
        self.labelFrameName.setAlignment(Qt.AlignmentFlag.AlignVCenter)
        self.frameName=QLabel()
        self.frameName.setStyleSheet("font:8pt")
        self.frameName.setMaximumHeight(30)
        self.frameName.setMaximumWidth(100)
        self.frameName.setAlignment(Qt.AlignmentFlag.AlignVCenter)
        self.statusBar.addPermanentWidget(self.labelFrameName)
        self.statusBar.addPermanentWidget(self.frameName)
        
        self.ImgFrame=QToolButton()
        self.ImgFrame.setStyleSheet("QToolButton:!pressed{border-image: url(./icons/data1.png);background-color: transparent;border-color: green;}""QToolButton:pressed{image: url(./icons/data2.png) ;background-color: transparent;border-color: blue}")
        self.statusBar.addPermanentWidget(self.ImgFrame)
        
        self.checkBoxScale=QAction(QtGui.QIcon(self.icon+"expand.png"),' Auto Scale on',self)
        self.checkBoxScale.setCheckable(True)
        self.checkBoxScale.setChecked(True)
        self.toolBar.addAction(self.checkBoxScale)
        self.ImageMenu.addAction(self.checkBoxScale)
        self.checkBoxScale.triggered.connect(self.checkBoxScaleImage)
        
        self.checkBoxColor=QAction(QtGui.QIcon(self.icon+"colors-icon.png"),'Color on',self)
        self.checkBoxColor.triggered.connect(self.Color)
        self.checkBoxColor.setCheckable(True) 
        self.checkBoxColor.setChecked(True)
        self.toolBar.addAction(self.checkBoxColor)
        self.ImageMenu.addAction(self.checkBoxColor)
        
    
        self.checkBoxHist=QAction(QtGui.QIcon(self.icon+"colourBar.png"),'Show colour Bar',self)
        self.checkBoxHist.setCheckable(True)
        self.checkBoxHist.setChecked(False)
        self.checkBoxHist.triggered.connect(self.HIST)
        self.ImageMenu.addAction(self.checkBoxHist)
        
        #self.ColorBox=QMenu('&LookUp Table',self) #
        menuColor=QMenu('LookUp Table',self)
        menuColor.addAction('thermal',self.Setcolor)
        menuColor.addAction('flame',self.Setcolor)
        menuColor.addAction('yellowy',self.Setcolor)
        menuColor.addAction('bipolar',self.Setcolor)
        menuColor.addAction('spectrum',self.Setcolor)
        menuColor.addAction('cyclic',self.Setcolor)
        menuColor.addAction('viridis',self.Setcolor) 
        menuColor.addAction('inferno',self.Setcolor)
        menuColor.addAction('plasma',self.Setcolor)      
        menuColor.addAction('magma',self.Setcolor)            
        
        #self.ColorBox.setMenu(menuColor)
        self.ImageMenu.addMenu(menuColor)
        
        
        self.checkBoxBg=QAction('Background Substraction On',self)
        self.checkBoxBg.setCheckable(True)
        self.checkBoxBg.setChecked(False)
        self.ImageMenu.addAction(self.checkBoxBg)
        
        
        
        if self.encercled=="on":
            self.energyBox=QAction(QtGui.QIcon(self.icon+"coin.png"),'Energy Encercled',self)
            self.energyBox.setShortcut('Ctrl+e')
            self.AnalyseMenu.addAction(self.energyBox)
            self.energyBox.triggered.connect(self.Energ)
        
            
        if self.math=="on":
            self.mathButton=QAction(QtGui.QIcon(self.icon+"math.png"),'Math',self)
            self.mathButton.triggered.connect(lambda:self.open_widget(self.winMath))
            self.ProcessMenu.addAction(self.mathButton)
            self.winMath.emitApply.connect(self.newDataReceived)
        
        self.paletteupButton=QAction(QtGui.QIcon(self.icon+"user.png"),'Brightness +',self)
        #self.paletteupButton.setShortcut('+')
        self.ProcessMenu.addAction(self.paletteupButton)
        self.paletteupButton.triggered.connect(self.paletteup)
        
        self.palettedownButton=QAction(QtGui.QIcon(self.icon+"userM.png"),'Brightness -',self)
        #self.palettedownButton.setShortcut('-')
        self.ProcessMenu.addAction(self.palettedownButton)
        self.palettedownButton.triggered.connect(self.palettedown)
        
        self.paletteautoButton=QAction(QtGui.QIcon(self.icon+"robotics.png"),'Brightness auto ',self)
        #self.palettedautoButton.setShortcut('-')
        self.ProcessMenu.addAction(self.paletteautoButton)
        self.paletteautoButton.triggered.connect(self.paletteauto)
        
        self.contrastButton=QAction(QtGui.QIcon(self.icon+"ying-yang.png"),'Contrast 5%-95%',self)
        #self.palettedautoButton.setShortcut('-')
        self.ProcessMenu.addAction(self.contrastButton)
        self.contrastButton.triggered.connect(self.contrast)
        
        
        
        if self.winFilter=='on':
            #self.filtreBox=QAction('&Filters',self)
            self.menuFilter=QMenu('&Filters',self)
            self.menuFilter.addAction('&Gaussian',self.Gauss)
            self.menuFilter.addAction('&Median',self.Median)
            self.menuFilter.addAction('&Threshold',self.Threshold)
            self.menuFilter.addAction('&Origin',self.Orig)
            
            #self.filtreBox.setMenu(menu)
            self.ProcessMenu.addMenu(self.menuFilter)
        
        if self.plot3D=="on":
            self.box3d=QPushButton('3D', self)
            self.toolBar.addWidget(self.box3d)
        
        if self.meas=='on':
            self.MeasButton=QAction(QtGui.QIcon(self.icon+"laptop.png"),'Measure',self)
            self.MeasButton.setShortcut('ctrl+m')
            self.MeasButton.triggered.connect(self.Measurement)
            self.AnalyseMenu.addAction(self.MeasButton)
            
        if self.fft=='on':
            self.fftButton=QAction('FFT')
            self.AnalyseMenu.addAction(self.fftButton)
            self.fftButton.triggered.connect(self.fftTransform)
        
        self.PointingButton=QAction(QtGui.QIcon(self.icon+"recycle.png"),'Pointing',self)
        self.PointingButton.triggered.connect(self.Pointing)
        self.AnalyseMenu.addAction(self.PointingButton)       
        
        
        
        
        
        
        self.ZoomRectButton=QAction(QtGui.QIcon(self.icon+"loupe.png"),'Zoom',self)
        self.ZoomRectButton.triggered.connect(self.zoomRectAct)
        self.toolBar.addAction(self.ZoomRectButton)
        
        
        self.ligneButton=QAction(QtGui.QIcon(self.icon+"line.png"),'add  Line',self)
        self.toolBar.addAction(self.ligneButton)
        
        self.rectangleButton=QAction(QtGui.QIcon(self.icon+"rectangle.png"),'Add Rectangle',self)
        self.toolBar.addAction(self.rectangleButton)
        
        self.circleButton=QAction(QtGui.QIcon(self.icon+"Red_circle.png"),'add  Cercle',self)
        self.toolBar.addAction(self.circleButton)
        
        self.PlotButton=QAction(QtGui.QIcon(self.icon+"analytics.png"),'Plot Profile',self)
        self.PlotButton.triggered.connect(self.CUT)
        self.PlotButton.setShortcut("ctrl+k")
        self.AnalyseMenu.addAction(self.PlotButton)
        
        
        self.showMaxButton=QAction('Show max',self)
        self.showMaxButton.triggered.connect(self.ZoomMAX)
        self.winZoomMax=ZOOM()
        self.AnalyseMenu.addAction(self.showMaxButton)
        
        
        
        self.flipButton=QAction(QtGui.QIcon(self.icon+"fliphorizontal.png"),'Flip Horizontally',self)
        self.flipButton.setCheckable(True)
        self.flipButton.setChecked(False)
        self.flipButton.triggered.connect(self.flipAct)
        self.ImageMenu.addAction(self.flipButton)
        
        
        self.flipButtonVert=QAction(QtGui.QIcon(self.icon+"flipvertical.png"),'Flip Horizontally',self)
        self.flipButtonVert.setCheckable(True)
        self.flipButtonVert.setChecked(False)
        self.ImageMenu.addAction(self.flipButtonVert)
        self.flipButtonVert.triggered.connect(self.flipVertAct)
        
        
        self.vbox2=QVBoxLayout()
        
        self.winImage = pg.GraphicsLayoutWidget()
        self.winImage.setContentsMargins(0,0,0,0)
        self.winImage.setAspectLocked(True)
        self.winImage.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.winImage.ci.setContentsMargins(0,0,0,0)
        self.vbox2.addWidget(self.winImage)
        self.vbox2.setContentsMargins(0,0,0,0)
        
        self.p1=self.winImage.addPlot()
        self.imh=pg.ImageItem()
        self.axeX=self.p1.getAxis('bottom')
        self.axeY=self.p1.getAxis('left')
        self.p1.addItem(self.imh)
        self.p1.setMouseEnabled(x=False,y=False)
        self.p1.setContentsMargins(0,0,0,0)
   
        self.p1.setAspectLocked(True,ratio=1)
        self.p1.showAxis('right',show=False)
        self.p1.showAxis('top',show=False)
        self.p1.showAxis('left',show=False)
        self.p1.showAxis('bottom',show=False)
        
        if self.bloqKeyboard==True:
            self.vLine = pg.InfiniteLine(angle=90, movable=False,pen='r')
            self.hLine = pg.InfiniteLine(angle=0, movable=False,pen='r')
        else:
            self.vLine = pg.InfiniteLine(angle=90, movable=False,pen='y')
            self.hLine = pg.InfiniteLine(angle=0, movable=False,pen='y')

        self.xc=int(self.conf.value(self.name+"/xc"))
        self.yc=int(self.conf.value(self.name+"/yc"))
        self.rx=int(self.conf.value(self.name+"/rx"))
        self.ry=int(self.conf.value(self.name+"/ry"))
        self.vLine.setPos(self.xc)
        self.hLine.setPos(self.yc)
       
        
        self.ro1=pg.EllipseROI([self.xc,self.yc],[self.rx,self.ry],pen='r',movable=False)
        self.ro1.setPos([self.xc-(self.rx/2),self.yc-(self.ry/2)])
        
       
        self.roiFluence=pg.EllipseROI([self.xc,self.yc],[self.rx,self.ry],pen='b',movable=True)
        self.roiFluence.setPos([self.xc-(self.rx/2),self.yc-(self.ry/2)])
       
        
        # text for fwhm on p1
        self.textX = pg.TextItem(angle=-90) 
        self.textY = pg.TextItem()
        
        #histogram
        self.hist = pg.HistogramLUTItem() 
        self.hist.setImageItem(self.imh)
        self.hist.autoHistogramRange()
        self.hist.gradient.loadPreset('flame')
        
        ##  XY  graph
        self.curve2=pg.PlotCurveItem()
        self.curve3=pg.PlotCurveItem()
        
        ## slider to open multi file
        self.sliderImage=QSlider(Qt.Horizontal)
        self.sliderImage.setEnabled(False)
        self.vbox2.addWidget(self.sliderImage)
        
        ## main layout
        
        # vMainLayout=QVBoxLayout()
        
        hMainLayout=QHBoxLayout()
        # vMainLayout.addLayout(self.hboxBar)
        #vMainLayout.addLayout(hMainLayout)
        
        if self.aff=='right':
            hMainLayout.addLayout(self.vbox2)
            hMainLayout.addLayout(self.vbox1)
        if self.aff=='left':
            hMainLayout.addLayout(self.vbox1)
            hMainLayout.addLayout(self.vbox2)
            
        
        
        hMainLayout.setContentsMargins(1,1,1,1)
        #hMainLayout.setSpacing(1)
        #hMainLayo.setStretch(10,1)
        MainWidget=QFrame()#
        
        if self.color is not None :
            
            self.winImage.setStyleSheet("border : 3px solid  %s" % self.color);
        
        MainWidget.setLayout(hMainLayout)
        
        self.setCentralWidget(MainWidget)
        #self.setContentsMargins(1,1,1,1)
        #self.plotLine=pg.LineSegmentROI(positions=((self.dimx/2-100,self.dimy/2),(self.dimx/2+100,self.dimy/2)), movable=True,angle=0,pen='b')
        self.plotLine=pg.LineSegmentROI(positions=((0,200),(200,200)), movable=True,angle=0,pen='w')
        #self.plotLine=pg.PolyLineROI(positions=((0,200),(200,200),(300,200)), movable=True,angle=0,pen='w')
        self.plotRect=pg.RectROI([self.xc,self.yc],[4*self.rx,self.ry],pen='g')
        self.plotCercle=pg.CircleROI([self.xc,self.yc],[80,80],pen='g')
        self.plotRectZoom=pg.RectROI([self.xc,self.yc],[4*self.rx,self.ry],pen='w')
        self.plotRectZoom.addScaleHandle((0,0),center=(1,1))
        self.setStyleSheet(qdarkstyle.load_stylesheet(qt_api='pyqt6')) # dark style
        
        
        
    def actionButton(self):
        # action of button
        
       
        self.ro1.sigRegionChangeFinished.connect(self.roiChanged)
        self.ligneButton.triggered.connect(self.LIGNE)
        self.rectangleButton.triggered.connect(self.Rectangle)
        self.circleButton.triggered.connect(self.CERCLE)
        
        self.plotLine.sigRegionChangeFinished.connect(self.LigneChanged)
        self.plotRect.sigRegionChangeFinished.connect(self.RectChanged)
        self.plotCercle.sigRegionChangeFinished.connect(self.CercChanged)
        
        # if self.plot3D=="on":
        #     self.box3d.clicked.connect(self.Graph3D)
            
        self.winPref.closeEventVar.connect(self.ScaleImg)
        
        
        self.sliderImage.valueChanged.connect(self.SliderImgFct)
        # self.dockImage.topLevelChanged.connect(self.fullScreen)
        self.roiFluence.sigRegionChangeFinished.connect(self.fluenceFct)
        
        if self.parent is not None:
            self.parent.signalData.connect(self.newDataReceived)
        
    def fullScreen(self):
        if  self.fullscreen==False:
            self.fullscreen=True
            self.dockImage.showMaximized()
        else :
            self.fullscreen=False
            self.dockImage.showNormal()
        
    def shortcut(self):
        # keyboard shortcut
        
        self.shortcutPu=QShortcut(QtGui.QKeySequence("+"),self)
        self.shortcutPu.activated.connect(self.paletteup)
        self.shortcutPu.setContext(Qt.ShortcutContext(3))
        #3: The shortcut is active when its parent widget, or any of its children has focus. default O The shortcut is active when its parent widget has focus.
        self.shortcutPd=QtGui.QShortcut(QtGui.QKeySequence("-"),self)
        self.shortcutPd.activated.connect(self.palettedown)
        self.shortcutPd.setContext(Qt.ShortcutContext(3))
        
        
        self.shortcutBloq=QtGui.QShortcut(QtGui.QKeySequence("Ctrl+b"),self)
        self.shortcutBloq.activated.connect(self.bloquer)
        self.shortcutBloq.setContext(Qt.ShortcutContext(3))
        
        self.shortcutDebloq=QtGui.QShortcut(QtGui.QKeySequence("Ctrl+d"),self)
        self.shortcutDebloq.activated.connect(self.debloquer)
        self.shortcutDebloq.setContext(Qt.ShortcutContext(3))
        
        
        
        # mousse action:
        self.proxy=pg.SignalProxy(self.p1.scene().sigMouseMoved, rateLimit=60, slot=self.mouseMoved)
        self.p1.scene().sigMouseClicked.connect(self.mouseClick)
        self.vb=self.p1.vb
        
        
    def Energ(self):
        # open windget for calculated encercled energy and plot it vs shoot number
        self.open_widget(self.winEncercled)
        self.winEncercled.Display(self.data)
        
    def LIGNE(self) : 
        #plot a line
        try :
            self.p1.removeItem(self.plotRect)
            self.p1.removeItem(self.plotCercle)
        except:pass
    
        if self.ite=='line':
            self.p1.removeItem(self.plotLine)
            self.ite=None
        else: 
            self.ite='line'
            self.p1.addItem(self.plotLine)
            self.LigneChanged()
        
      
    def LigneChanged(self):
        # take ROI 
        self.cut=self.plotLine.getArrayRegion(self.data,self.imh)
        
        if self.winPref.checkBoxAxeScale.isChecked()==1:
            self.linePoints=self.plotLine.listPoints()
            self.lineXo=self.linePoints[0][0]
            self.lineYo=self.linePoints[0][1]
            self.lineXf=self.linePoints[1][0]
            self.lineYf=self.linePoints[1][1]
            #self.plotLineAngle=np.arctan((self.lineYf-self.lineYo)/(self.lineXf-self.lineXo))
            # print('angle',self.plotLineAngle*360/(2*3.14),self.cut.size)
            
            step=(self.winPref.stepX**2*(self.lineXo-self.lineXf)**2+self.winPref.stepY**2*(self.lineYo-self.lineYf)**2)
            step=step**0.5/self.cut.size
            self.absiLine=np.arange(0,(self.cut.size)*step,step)
            
            #print(self.absiLine)
        
    def Rectangle(self)  :
        
        try :
            self.p1.removeItem(self.plotLine)
            self.p1.removeItem(self.plotCercle)
        except:pass
        
        if self.ite=='rect':
            self.p1.removeItem(self.plotRect)
            self.ite=None
        else :
            self.p1.addItem(self.plotRect)
            self.plotRect.setPos([self.dimx/2,self.dimy/2])
            self.ite='rect'
            self.RectChanged()
        
    def RectChanged(self):
        # take ROI
        self.cut=(self.plotRect.getArrayRegion(self.data,self.imh))
        if self.winPref.plotRectOpt.currentIndex()==0:
            self.cut1=self.cut.mean(axis=1)
        else:
            self.cut1=self.cut.sum(axis=1)
        
    def CERCLE(self) : 
        try :
            self.p1.removeItem(self.plotRect)
            self.p1.removeItem(self.plotLine)
        except:pass
        #self.p1.clear()
        if self.ite=='cercle':
            self.p1.removeItem(self.plotCercle)
            self.ite=None
        else:
            self.p1.addItem(self.plotCercle) 
            self.plotCercle.setPos([self.dimx/2,self.dimy/2])
            self.ite='cercle'
        
    def CercChanged(self):
        # take ROI
        self.cut=(self.plotCercle.getArrayRegion(self.data,self.imh))
        self.cut1=self.cut.mean(axis=1)
    
    def CUT(self): 
        # plot on a separated widget the ROI plot profile
        if self.ite=='line':
            self.signalTrans['data']=self.cut
            self.open_widget(self.winCoupe)
            if self.winPref.checkBoxAxeScale.isChecked()==1:
                
                self.signalTrans['axis']=self.absiLine
                self.signalPlot.emit(self.signalTrans)
                # self.winCoupe.PLOT(self.cut,axis=self.absiLine)
            else:
                # self.winCoupe.PLOT(self.cut)#,symbol=False)
                self.signalPlot.emit(self.signalTrans)
        if self.ite=='rect':
            self.signalTrans['data']=self.cut1
            self.open_widget(self.winCoupe)
            # self.winCoupe.PLOT(self.cut1)#,symbol=False)
            self.signalPlot.emit(self.signalTrans)
   
    # def Graph3D (self):
        
    #     self.open_widget(self.Widget3D)
    #     self.Widget3D.Plot3D(self.data)
        
        
    def Measurement(self) :
        # show widget for measurement on all image or ROI  (max, min mean ...)
        if self.ite=='rect':
            self.RectChanged()
            if self.meas=="on":
                self.winM.setFile(self.nomFichier)
                self.open_widget(self.winM)
                self.signalMeas.emit(self.cut)
                # self.winM.Display(self.cut)
            
        if self.ite=='cercle':
            self.CercChanged()
            if self.meas=="on":
                self.winM.setFile(self.nomFichier)
                self.open_widget(self.winM)
                self.signalMeas.emit(self.cut)
                # self.winM.Display(self.cut)
        
        # if self.ite=='line':
        #     self.LigneChanged()
        #     self.winM.setFile(self.nomFichier)
        #     self.open_widget(self.winM)
        #     self.winM.Display(self.cut)
        
        if self.ite==None:
            if self.meas=="on":
                self.winM.setFile(self.nomFichier)
                self.open_widget(self.winM)
                
                self.signalMeas.emit(self.data)
                
                # self.winM.Display(self.data)
                
    def Pointing(self) :

        self.open_widget(self.winPointing)

        if self.ite=='rect':
            self.RectChanged()
            pData=self.cut
        elif self.ite=='cercle':
            self.CercChanged() 
            pData=self.cut
        elif self.ite==None:
            pData=self.data
        else :pData=self.data


        if self.winPref.checkBoxAxeScale.isChecked()==1:
            self.signalPointing.emit(pData,self.winPref.stepX,self.winPref.stepX)
                #self.winPointing.Display(pData,self.winPref.stepX,self.winPref.stepX)
        else:
            self.signalPointing.emit(pData)
            # self.winPointing.Display(pData)

    def fftTransform(self):
        # show on a new widget fft 
        if self.ite=='rect':
            self.RectChanged()
            self.open_widget(self.winFFT)
            self.winFFT.Display(self.cut)   
        if self.ite=='cercle':
            self.CercChanged()
            self.open_widget(self.winFFT)
            self.winFFT.Display(self.cut)
        if self.ite=='line':
            self.LigneChanged()
            self.open_widget(self.winFFT1D)
            if self.cut.ndim==1:
                datafft=np.fft.fft(np.array(self.cut))
                self.norm=abs(np.fft.fftshift(datafft))
                self.norm=np.log10(1+self.norm)
                self.winFFT1D.PLOT(self.norm)
            
        if self.ite==None:
            self.open_widget(self.winFFT)
            self.winFFT.Display(self.data) 
        

        
    @pyqtSlot (object)   
    def Display(self,data):
        #  display the data and refresh all the calculated things and plots
        self.data=data
        
        
        if self.checkBoxBg.isChecked()==True and self.winOpt.dataBgExist==True:
            try :
                self.data=self.data-self.winOpt.dataBg
            except :
                msg = QMessageBox()
                msg.setIcon(QMessageBox.Icon.Critical)
                msg.setText("Background not soustracred !")
                msg.setInformativeText("Background file error  ")
                msg.setWindowTitle("Warning ...")
                msg.setWindowFlags(QtCore.Qt.WindowType.WindowStaysOnTopHint)
                msg.exec_()
                
        if self.checkBoxBg.isChecked()==True and self.winOpt.dataBgExist==False:
                msg = QMessageBox()
                msg.setIcon(QMessageBox.Icon.Critical)
                msg.setText("Background not soustracted !")
                msg.setInformativeText("Background file not selected in options menu ")
                msg.setWindowTitle("Warning ...")
                msg.setWindowFlags(QtCore.Qt.WindowType.WindowStaysOnTopHint)
                
                msg.exec_()
                
        
        #### filtre
        if self.filter=='gauss':
            self.data=gaussian_filter(self.data,self.sigma)
            #print('gauss filter')
            
        if self.filter=='median':
            self.data=median_filter(self.data,size=self.sigma)
            #print('median filter')
        if self.filter=='threshold':
            self.data=np.where( self.data<self.threshold,0,self.data)
        #### fluence 
        if self.winPref.checkBoxFluence.isChecked()==1: # fluence on 
           energy=self.winPref.energy.value()
           #print('energy',energy)
           if self.winPref.checkBoxAxeScale.isChecked()==0:  # en pixel
               size=1#self.sizeFluenceX*self.sizeFluenceY
               self.labelValue=' mJ/pixel2'
           if self.winPref.checkBoxAxeScale.isChecked()==1: #en micron
               size=1E-8*self.winPref.stepX*self.winPref.stepY
               self.labelValue=' mJ/cm2'
               
           enrgTot=self.roiFluence.getArrayRegion(self.data,self.imh).sum()
           
           self.data=1000*(self.data*energy/enrgTot)/size #(microJ/cm2)
        # self.p1.setAspectLocked(True,ratio=1)
        else :
            self.labelValue=''
            
        #### color  and sacle 
        if self.checkBoxScale.isChecked()==1: # color autoscale on
            
            if self.winPref.checkBoxAxeScale.isChecked()==1:
                self.axeX.setScale(self.winPref.stepX)
                self.axeY.setScale(self.winPref.stepY)
                self.axeX.setLabel('um')
                self.axeY.setLabel('um')
                self.axeX.showLabel(True)
            if self.winPref.checkBoxAxeScale.isChecked()==0:
                self.scaleAxis="off"
                self.axeX.setScale(1)
                self.axeY.setScale(1)  
                self.axeX.showLabel(False)
            self.imh.setImage(self.data,autoLevels=True,autoDownsample=True) #.astype(float)
        else :
            self.imh.setImage(self.data,autoLevels=False,autoDownsample=True)
        
        
        ####update    
        self.Coupe()#self.PlotXY() # graph update
        self.zoomRectupdate() # update rect  
        
        if self.encercled=="on":
            if self.winEncercled.isWinOpen==True:
                self.signalEng.emit(self.data)
                # self.winEncercled.Display(self.data) ## energy update
        
        if self.winCoupe.isWinOpen==True:
            if self.ite=='line':
                self.LigneChanged()
                self.CUT()
            if self.ite=='rect':
                self.RectChanged()
                self.CUT()
            if self.ite=='cercle':
                self.CercChanged()
        if self.meas=="on":       
            if self.winM.isWinOpen==True: #  measurement update
                if self.ite=='rect':
                    self.RectChanged()
                    self.Measurement()
                elif self.ite=='cercle':
                    self.CercChanged()
                    self.Measurement()
                else :
                    self.Measurement()
        if self.fft=='on':        
            if self.winFFT.isWinOpen==True: # fft update
                self.winFFT.Display(self.data)
                
        # if self.plot3D=="on":
        #     if self.Widget3D.isWinOpen==True:
        #         self.Graph3D()
        if self.winPointing.isWinOpen==True:
            self.Pointing()
        if self.winZoomMax.isWinOpen==True:
            self.ZoomMAX()   
            
        #### autosave
        if self.checkBoxAutoSave.isChecked()==True: ## autosave data
            self.pathAutoSave=str(self.conf.value(self.name+'/pathAutoSave'))
            self.fileNameSave=str(self.conf.value(self.name+'/nameFile'))
            date=time.strftime("%Y_%m_%d_%H_%M_%S")
            self.numTir=int(self.conf.value(self.name+'/tirNumber'))
            # if self.numTir<10:
            #     num="00"+str(self.numTir)
            # elif 9<self.numTir<100:
            #     num="0"+str(self.numTir)
            # else:
            num=str(self.numTir)
            if self.winOpt.checkBoxDate.isChecked()==True: # add the date
                nomFichier=str(str(self.pathAutoSave)+'/'+self.fileNameSave+'_'+num+'_'+date)
            else :
                nomFichier=str(str(self.pathAutoSave)+'/'+self.fileNameSave+'_'+num)

            print( nomFichier, 'saved')
            if self.winOpt.checkBoxTiff.isChecked()==True: #save as tiff 
                self.dataS=self.dataS=np.rot90(self.data,1)
                img_PIL = Image.fromarray(self.dataS)
                img_PIL.save(str(nomFichier)+'.TIFF',format='TIFF') 
            else :
                
                np.savetxt(str(nomFichier)+'.txt',self.data)
                
            if self.winOpt.checkBoxServer.isChecked()==False: # if not connected to server we had +1
                self.numTir+=1
                self.winOpt.setTirNumber(self.numTir)
            self.conf.setValue(self.name+"/tirNumber",self.numTir)
                
            self.fileName.setText(nomFichier)
    
        
        
        
    def mouseClick(self,evt): # block the cross if mousse button clicked
        
#            
#            
#        else:
        if self.bloqq==1:
            self.bloqq=0
            
        else :
            self.bloqq=1
#            self.conf.setValue(self.name+"/xc",int(self.xc)) # save cross postion in ini file
#            self.conf.setValue(self.name+"/yc",int(self.yc))
        
            
    def mouseMoved(self,evt):
        if self.checkBoxPlot.isChecked()==False or self.bloqKeyboard==True :  # if not  cross or crossblocked by  keyboard: 
            
            if self.bloqq==0:
                
                pos = evt[0]  ## using signal proxy turns original arguments into a tuple
                if self.p1.sceneBoundingRect().contains(pos):
                    
                    mousePoint = self.vb.mapSceneToView(pos)
                    self.xMouse = (mousePoint.x())
                    self.yMouse= (mousePoint.y())
                    if ((self.xMouse>0 and self.xMouse<self.dimx-1) and (self.yMouse>0 and self.yMouse<self.dimy-1) ):
                        self.xc = self.xMouse
                        self.yc= self.yMouse  
                        
                        try :
                            dataCross=self.data[int(self.xc),int(self.yc)]
                    
                        except :
                            dataCross=0  # evoid to have an error if cross if out of the image
                            self.xc=0
                            self.yc=0
                        if self.winPref.checkBoxAxeScale.isChecked()==1: # scale axe on 
                            self.label_Cross.setText('x='+ str(round(int(self.xc)*self.winPref.stepX,2)) + '  um'+' y=' + str(round(int(self.yc)*self.winPref.stepY,2)) +' um')
                        else : 
                            
                            self.label_Cross.setText('x='+ str(int(self.xc)) + ' y=' + str(int(self.yc)) )
                        
                        dataCross=round(dataCross,3) # take data  value  on the cross
                        self.label_CrossValue.setText(' v.=' + str(dataCross)+self.labelValue)
        ## the cross mouve with the mousse mvt
        if self.bloqKeyboard==False :  #mouse not  blocked by  keyboard
            if self.bloqq==0: # mouse not  blocked by mouse  click
                
                pos = evt[0]  ## using signal proxy turns original arguments into a tuple
                if self.p1.sceneBoundingRect().contains(pos):
                    
                    mousePoint = self.vb.mapSceneToView(pos)
                    self.xMouse = (mousePoint.x())
                    self.yMouse= (mousePoint.y())
                    if ((self.xMouse>0 and self.xMouse<self.dimx-1) and (self.yMouse>0 and self.yMouse<self.dimy-1) ):
                            self.xc = self.xMouse
                            self.yc= self.yMouse  
                            self.vLine.setPos(self.xc)
                            self.hLine.setPos(self.yc) # the cross move only in the graph    
                            if self.roiCross==True :
                                self.ro1.setPos([self.xc-(self.rx/2),self.yc-(self.ry/2)])
                            self.PlotXY()
                
    def fwhm(self,x, y, order=3):
        """
            Determine full-with-half-maximum of a peaked set of points, x and y.
    
        """
        y=gaussian_filter(y,5) # filtre for reducing noise
        half_max = np.amax(y)/2.0
        s = splrep(x, y - half_max,k=order) # F
        roots = sproot(s) # Given the knots .
        if len(roots) > 2:
            pass
           
        elif len(roots) < 2:
            pass
        else:
            return np.around(abs(roots[1] - roots[0]),decimals=2)
        
       
    def Coupe(self):
        # make  plot profile on cross
        
        if self.checkBoxPlot.isChecked()==True:
            
            if self.maxGraphBox.isChecked()==True  and self.bloqKeyboard==False  : # find and fix the cross on the maximum of the image
                
                #dataF=gaussian_filter(self.data,3)
                # dataF=self.data
                (self.xc,self.yc)=np.unravel_index(self.data.argmax(),self.data.shape) #take the max ndimage.measurements.center_of_mass(dataF)#
                self.vLine.setPos(self.xc)
                self.hLine.setPos(self.yc)
                if self.roiCross==True:
                    self.ro1.setPos([self.xc-(self.rx/2),self.yc-(self.ry/2)])
            
                
            try :
                dataCross=self.data[int(self.xc),int(self.yc)]
                
            except :
                dataCross=0  # evoid to have an error if cross if out of the image
                self.xc=0
                self.yc=0
               
            coupeX=self.data[int(self.xc),:]
            coupeY=self.data[:,int(self.yc)]
            xxx=np.arange(0,int(self.dimx),1)
            yyy=np.arange(0,int(self.dimy),1)
            coupeXMax=np.max(coupeX)
            coupeYMax=np.max(coupeY)
            
            
            if coupeXMax==0: # avoid zero
                coupeXMax=1
            
            if coupeYMax==0:
                coupeYMax=1
                
            if self.winPref.checkBoxAxeScale.isChecked()==1: # scale axe on 
                self.label_Cross.setText('x='+ str(round(int(self.xc)*self.winPref.stepX,2)) + '  um'+' y=' + str(round(int(self.yc)*self.winPref.stepY,2)) +' um')
            else : 
                self.label_Cross.setText('x='+ str(int(self.xc)) + ' y=' + str(int(self.yc)) )
                
            dataCross=round(dataCross,3) # take data  value  on the cross
            
            self.label_CrossValue.setText(' v.=' + str(dataCross))
            
            coupeXnorm=(self.data.shape[0]/10)*(coupeX/coupeXMax)
            coupeYnorm=(self.data.shape[1]/10)*(coupeY/coupeYMax)
            
            if self.plotRectZoomEtat=="ZoomOut": # the cut line follow the zoom
               
                self.curve2.setData(20+self.xZoomMin+coupeXnorm,yyy,clear=True)
                self.curve3.setData(xxx,20+self.yZoomMin+coupeYnorm,clear=True)
            
            else :
                 # normalize the curves
                self.curve2.setData(20+self.xminR+coupeXnorm,yyy,clear=True)
                self.curve3.setData(xxx,20+self.yminR+coupeYnorm,clear=True)
                
            
            
            ###  fwhm on the  X et Y curves if max  >20 counts if checked in winOpt
            
            
            if self.winPref.checkBoxFwhm.isChecked()==1: # show fwhm values on graph
                xCXmax=np.amax(coupeXnorm) # max
                if xCXmax>20:
                    try :
                        fwhmX=self.fwhm(yyy, coupeXnorm, order=3)
                    except : fwhmX=None
                    if fwhmX==None:
                        self.textX.setText('')
                    else:
                        if self.winPref.checkBoxAxeScale.isChecked()==1:
                            self.textX.setText('fwhm='+str(round(fwhmX*self.winPref.stepX,2))+' um',color='w')
                        else :
                           self.textX.setText('fwhm='+str(round(fwhmX,2)),color='w')
                    yCXmax=yyy[coupeXnorm.argmax()]
                    
                    self.textX.setPos(xCXmax+70,yCXmax+60)
                
                yCYmax=np.amax(coupeYnorm) # max
                
                if yCYmax>20:
                    try:
                        fwhmY=self.fwhm(xxx, coupeYnorm, order=3)
                    except :fwhmY=None
                    xCYmax=xxx[coupeYnorm.argmax()]
                    if fwhmY==None:
                        self.textY.setText('',color='w')
                    else:
                        if self.winPref.checkBoxAxeScale.isChecked()==1:
                            self.textY.setText('fwhm='+str(round(fwhmY*self.winPref.stepY,2))+' um',color='w')
                        else:
                            self.textY.setText('fwhm='+str(round(fwhmY,2)),color='w')
                            
                    self.textY.setPos(xCYmax-60,yCYmax+70)   
        
        if self.checkBoxPlot.isChecked()==False: ## write mouse value and not cross  value
            
            try :
                dataCross=self.data[int(self.xc),int(self.yc)]
                
            except :
                dataCross=0  # evoid to have an error if mousse is out of the image
                self.xc=0
                self.yc=0
                
            if self.winPref.checkBoxAxeScale.isChecked()==1: # scale axe on 
                self.label_Cross.setText('x='+ str(round(int(self.xc)*self.winPref.stepX,2)) + '  um'+' y=' + str(round(int(self.yc)*self.winPref.stepY,2)) +' um')
            else : 
                        
                self.label_Cross.setText('x='+ str(int(self.xc)) + ' y=' + str(int(self.yc)) )
                        
            dataCross=round(dataCross,3) # take data  value  on the mousse
            self.label_CrossValue.setText(' v.=' + str(dataCross)+self.labelValue)
 
    def PlotXY(self): # plot curves on the  graph
        
        if self.checkBoxPlot.isChecked()==1:
            
            self.p1.addItem(self.vLine, ignoreBounds=False)
            self.p1.addItem(self.hLine, ignoreBounds=False)
            self.p1.addItem(self.curve2)
            self.p1.addItem(self.curve3)
            self.p1.showAxis('left',show=True)
            self.p1.showAxis('bottom',show=True)
            self.p1.addItem(self.textX)
            self.p1.addItem(self.textY)
            if self.roiCross==True:
                self.p1.addItem(self.ro1)
            self.Coupe()
        else:
            self.p1.removeItem(self.vLine)
            self.p1.removeItem(self.hLine)
            self.p1.removeItem(self.curve2)
            self.p1.removeItem(self.curve3)
            self.p1.removeItem(self.textX)
            self.p1.removeItem(self.textY)
            self.p1.showAxis('left',show=False)
            self.p1.showAxis('bottom',show=False)
            #self.label_Cross.setText('')
            #self.label_CrossValue.setText('')
            if self.roiCross==True:
                self.p1.removeItem(self.ro1)

            
    def paletteup(self):
        # change the color scale
        levels=self.imh.getLevels()
        if levels[0]==None:
            xmax =self.data.max()
            xmin=self.data.min()
        else :
            xmax=levels[1]
            xmin=levels[0]
            
        self.imh.setLevels([xmin, xmax-(xmax- xmin) / 10])
        #hist.setImageItem(imh,clear=True)
        self.hist.setHistogramRange(xmin,xmax)

    def palettedown(self):
        
        levels=self.imh.getLevels()
        if levels[0]==None:
            xmax=self.data.max()
            xmin=self.data.min()
        else :
            xmax=levels[1]
            xmin=levels[0]
            
        self.imh.setLevels([xmin, xmax+ (xmax- xmin) / 10])
        #hist.setImageItem(imh,clear=True)
        self.hist.setHistogramRange(xmin,xmax)
    
    def paletteauto(self):
        
        xmax=self.data.max()
        xmin=self.data.min()
        if xmax==xmin:
            xmax=xmin+1
 
        self.imh.setLevels([xmin, xmax])
        self.hist.setHistogramRange(xmin,xmax)
    
    def contrast(self):
        if self.ite=='rect':
            self.cont=(self.plotRect.getArrayRegion(self.data,self.imh))
            xmax=self.cont.max()
            xmin=self.cont.min()
            
        else:
             xmax=self.data.max()
             xmin=self.data.min()
        xmin=0.05*xmax
        xmax=0.95*xmax
        self.imh.setLevels([xmin, xmax])
        self.hist.setHistogramRange(xmin,xmax)
  
     
    
    def Setcolor(self):
        action = self.sender()
        self.colorBar=str(action.text())
        
        self.hist.gradient.loadPreset(self.colorBar)
    
    def Color(self):
        """ image in colour/n&b
        """
        
        
        if self.checkBoxColor.isChecked()==1:
            self.checkBoxColor.setIcon(QtGui.QIcon(self.icon+"colors-icon.png"))
            self.hist.gradient.loadPreset(self.colorBar)
            self.checkBoxColor.setText('Color On')
        else:
            self.hist.gradient.loadPreset('grey')
            self.checkBoxColor.setIcon(QtGui.QIcon(self.icon+"circleGray.png"))
            self.checkBoxColor.setText('Gray')
            
    def roiChanged(self):
        
        self.rx=self.ro1.size()[0]
        self.ry=self.ro1.size()[1]
        self.conf.setValue(self.name+"/rx",int(self.rx))
        self.conf.setValue(self.name+"/ry",int(self.ry))
      
        
    def bloquer(self): # block the cross by keyboard
        
        self.bloqKeyboard=bool(True)
        self.conf.setValue(self.name+"/xc",int(self.xc))# save cross postion in ini file
        self.conf.setValue(self.name+"/yc",int(self.yc))
        self.conf.setValue(self.name+"/bloqKeyboard",bool(self.bloqKeyboard))
        self.vLine.setPen('r')
        self.hLine.setPen('r')
        self.ro1.setPen('r')
        
    def debloquer(self): # unblock the cross
        self.bloqKeyboard=bool(False)
        self.vLine.setPen('y')
        self.hLine.setPen('y')
        self.ro1.setPen('y')
        self.conf.setValue(self.name+"/bloqKeyboard",bool(self.bloqKeyboard))
        
        
        
    def HIST(self):
        #show histogramm
        if self.checkBoxHist.isChecked()==1:
            self.winImage.addItem(self.hist)
        else:
            self.winImage.removeItem(self.hist)
    
    
    def Gauss(self):
        # gauss filter
        self.filter='gauss'
        sigma, ok=QInputDialog.getInt(self,'Gaussian Filter ','Enter sigma value (radius)')
        if ok:
            self.sigma=sigma
            self.menuFilter.setTitle('F: Gaussian')
            self.Display(self.data)
        
        
    def Median(self):
        #median  filter
        self.filter='median'
        sigma, ok=QInputDialog.getInt(self,'Median Filter ','Enter sigma value (radius)')
        if ok:
            self.sigma=sigma
            self.menuFilter.setTitle('F: Median')
            self.Display(self.data)
        
    def Threshold(self):
        self.filter='threshold'
        threshold, ok=QInputDialog.getInt(self,'Threshold Filter ','Enter thresold value')
        if ok:
            self.threshold=threshold
            self.menuFilter.setTitle('F: Thresold')
            self.Display(self.data)
    def Orig(self):
        """
        return data without filter
        """
        self.data=self.dataOrg
        self.filter='origin'
        self.Display(self.data)
        self.menuFilter.setTitle('Filters')
        #print('original data')
        
    def OpenF(self,fileOpen=False):
        #open file in txt spe TIFF sif jpeg png  format
        fileOpen=fileOpen
        
        if fileOpen==False:
            
            chemin=self.conf.value(self.name+"/path")
            fname=QFileDialog.getOpenFileNames(self,"Open File",chemin,"Images (*.txt *.spe *.TIFF *.sif *.tif);;Text File(*.txt);;Ropper File (*.SPE);;Andor File(*.sif);; TIFF file(*.TIFF)")
           
            self.openedFiles=fname[0]
            
            self.nbOpenedImage=len(self.openedFiles)
            
            if self.nbOpenedImage==1:
                fichier=self.openedFiles[0]
                self.sliderImage.setEnabled(False)
                
            if self.nbOpenedImage>1:
                fichier=self.openedFiles[0]
                self.sliderImage.setMinimum(0)
                self.sliderImage.setMaximum(self.nbOpenedImage - 1)
                self.sliderImage.setValue(0)
                self.sliderImage.setEnabled(True)
                
                
        else:
            fichier=str(fileOpen)
                
        ext=os.path.splitext(fichier)[1]
        
        if ext=='.txt': # text file
            data=np.loadtxt(str(fichier))
        elif ext=='.spe' or ext=='.SPE': # SPE file
            dataSPE=SpeFile(fichier)
            data1=dataSPE.data[0]#.transpose() # first frame
            data=data1#np.flipud(data1)
        elif ext=='.TIFF' or ext=='.tif' or ext=='.Tiff' or ext=='.jpg' or ext=='.JPEG' or ext=='.png': # tiff File
            dat=Image.open(fichier)
            data=np.array(dat)
            data=np.rot90(data,3)
        elif ext=='.sif': 
            sifop=SifFile()
            im=sifop.openA(fichier)
            data=np.rot90(im,3)
#            self.data=self.data[250:495,:]
        else :
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Critical)
            msg.setText("Wrong file format !")
            msg.setInformativeText("The format of the file must be : .SPE  .TIFF .sif  png jpeg or .txt ")
            msg.setWindowTitle("Warning ...")
            msg.setWindowFlags(QtCore.Qt.WindowType.WindowStaysOnTopHint)
            msg.exec_()
            
        chemin=os.path.dirname(fichier)
        self.conf.setValue(self.name+"/path",chemin)
        self.conf.setValue(self.name+"/lastFichier",os.path.split(fichier)[1])
        print('Open file  :  ',fichier)
        
        self.fileName.setText(str(fichier))
        self.nomFichier=os.path.split(fichier)[1]
        
        self.winHistory.Display(fichier)
        
        self.newDataReceived(data)
        
    
    def OpenFNewWin(self):
        
        chemin=self.conf.value(self.name+"/path")
        fname=QFileDialog.getOpenFileNames(self,"Open File",chemin,"Images (*.txt *.spe *.TIFF *.sif *.tif);;Text File(*.txt);;Ropper File (*.SPE);;Andor File(*.sif);; TIFF file(*.TIFF)")
           
            
        self.openedFiles=fname[0]
            
            
        fichier=self.openedFiles[0]
                
       
                
        ext=os.path.splitext(fichier)[1]
        
        if ext=='.txt': # text file
            data=np.loadtxt(str(fichier))
        elif ext=='.spe' or ext=='.SPE': # SPE file
            dataSPE=SpeFile(fichier)
            data1=dataSPE.data[0]#.transpose() # first frame
            data=data1#np.flipud(data1)
        elif ext=='.TIFF' or ext=='.tif' or ext=='.Tiff' or ext=='.jpg' or ext=='.JPEG' or ext=='.png': # tiff File
            dat=Image.open(fichier)
            data=np.array(dat)
            data=np.rot90(data,3)
        elif ext=='.sif': 
            sifop=SifFile()
            im=sifop.openA(fichier)
            data=np.rot90(im,3)
#            self.data=self.data[250:495,:]
        else :
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Critical)
            msg.setText("Wrong file format !")
            msg.setInformativeText("The format of the file must be : .SPE  .TIFF .sif  png jpeg or .txt ")
            msg.setWindowTitle("Warning ...")
            msg.setWindowFlags(QtCore.Qt.WindowType.WindowStaysOnTopHint)
            msg.exec_()
            
        chemin=os.path.dirname(fichier)
        self.conf.setValue(self.name+"/path",chemin)
        self.conf.setValue(self.name+"/lastFichier",os.path.split(fichier)[1])
        print('Open file  :  ',fichier)
        
        
        self.newWindow=SEELIGHT(conf=self.conf,name=self.name)
        self.newWindow.setWindowTitle(fichier)
        self.newWindow.newDataReceived(data)
    
    
    def SliderImgFct(self):# open multiimage
        nbImgToOpen=int(self.sliderImage.value())

        self.OpenF(fileOpen=self.openedFiles[nbImgToOpen])
        
    def SaveF (self):
        # save data  in TIFF or Text  files
        
        if self.winOpt.checkBoxTiff.isChecked()==True: 
            fname=QFileDialog.getSaveFileName(self,"Save data as TIFF",self.path)
            self.path=os.path.dirname(str(fname[0]))
            fichier=fname[0]
        
            ext=os.path.splitext(fichier)[1]
            #print(ext)
            print(fichier,' is saved')
            self.conf.setValue(self.name+"/path",self.path)
            time.sleep(0.1)
            self.dataS=np.rot90(self.data,1)
            img_PIL = Image.fromarray(self.dataS)

            img_PIL.save(str(fname[0])+'.TIFF',format='TIFF')
            self.fileName.setText(fname[0]+'.TIFF') 
            
        else :
            fname=QFileDialog.getSaveFileName(self,"Save data as txt",self.path)
            self.path=os.path.dirname(str(fname[0]))
            fichier=fname[0]
            self.dataS=np.rot90(self.data,1)
            ext=os.path.splitext(fichier)[1]
            #print(ext)
            print(fichier,' is saved')
            self.conf.setValue(self.name+"/path",self.path)
            time.sleep(0.1)
            np.savetxt(str(fichier)+'.txt',self.dataS)
            self.fileName.setText(fname[0]+str(ext))

    @pyqtSlot (object) 
    def newDataReceived(self,data):
        
        # Do display and save origin data when new data is  sent to  visu
        
        self.data=data
        self.ImgFrame.animateClick() # change icon data when receive image
        if self.flipButton.isChecked()==1 and self.flipButtonVert.isChecked()==1 :
            self.data=np.flipud(self.data)
            self.data=np.fliplr(self.data)
        elif self.flipButton.isChecked()==1:
            self.data=np.flipud(self.data)
        elif self.flipButtonVert.isChecked()==1 :
            self.data=np.fliplr(self.data)
        else:
            self.data=data
            
        self.data=np.rot90(self.data,self.winPref.rotateValue)
        self.dimy=np.shape(self.data)[1]
        self.dimx=np.shape(self.data)[0]
        self.dataOrgScale=self.data
        self.dataOrg=self.data
        
        self.Display(self.data)
        self.frameName.setText(str(self.frameNumber))
        self.frameNumber=self.frameNumber+1

    
    
    def ScaleImg(self):
        #scale Axis px to um
        if self.winPref.checkBoxAxeScale.isChecked()==1:
            self.scaleAxis="on"
            self.LigneChanged()
        else :
            self.scaleAxis="off"
        self.data=self.dataOrg
        if self.winPref.checkBoxFluence.isChecked()==1: 
            # fluence on 
            self.p1.addItem(self.roiFluence)
            self.fluenceFct()
        else:
            try :
                self.p1.removeItem(self.roiFluence)
            except:
                pass
        self.Display(self.data)
    
    
    def zoomRectAct(self): #zoom fonction Display data on a range difined by a rectangular  roi
        
        if self.plotRectZoomEtat=="Zoom": 
            
            self.p1.addItem(self.plotRectZoom)
            self.plotRectZoom.setSize(size=(2*self.rx,2*self.ry),center=None)
            self.plotRectZoom.setPos([self.xc-1*self.rx,self.yc-1*self.ry])
            
            self.ZoomRectButton.setIcon(QtGui.QIcon(self.icon+"zoom-in.png"))
            self.plotRectZoomEtat="ZoomIn"
            self.ZoomRectButton.setText('Zoom In')
            
        elif self.plotRectZoomEtat=="ZoomIn":
            self.ZoomRectButton.setIcon(QtGui.QIcon(self.icon+"zoom-out.png"))
            self.xZoomMin=(self.plotRectZoom.pos()[0])
            self.yZoomMin=(self.plotRectZoom.pos()[1])
            self.xZoomMax=(self.plotRectZoom.pos()[0])+self.plotRectZoom.size()[0]
            self.yZoomMax=(self.plotRectZoom.pos()[1])+self.plotRectZoom.size()[1]
            self.p1.setXRange(self.xZoomMin,self.xZoomMax)
            
            self.p1.setYRange(self.yZoomMin,self.yZoomMax)
            self.p1.setAspectLocked(False)
            self.p1.removeItem(self.plotRectZoom)
            self.ZoomRectButton.setText('Zoom Out')
            self.plotRectZoomEtat="ZoomOut"
            
        elif self.plotRectZoomEtat=="ZoomOut": 
            self.p1.setYRange(0,self.dimy,update=True)
            self.p1.setXRange(0,self.dimx,update=True)
            #self.p1.setLimits(minXRange=0,maxXRange=self.dimx,minYRange=0,maxYRange=self.dimy,xMin=0,yMin=0,xMax=self.dimx,yMax=self.dimy)
            self.ZoomRectButton.setIcon(QtGui.QIcon(self.icon+"loupe.png"))
            self.ZoomRectButton.setText('Zoom rect')
            self.plotRectZoomEtat="Zoom"
            self.p1.setAspectLocked(True)
            #print(self.p1.viewRange(),self.p1.viewRect())
            
        
        self.Coupe()  #update profile line
        
    def zoomRectupdate(self):
        if self.plotRectZoomEtat=="ZoomOut":
            self.p1.setXRange(self.xZoomMin,self.xZoomMax)
            self.p1.setYRange(self.yZoomMin,self.yZoomMax)
            self.p1.setAspectLocked(True)
        # else:
        #     self.p1.setYRange(0,self.dimy)
        #     self.p1.setXRange(0,self.dimx)
        #     print('ra')
            
    def flipAct (self):
        ##flip the image up/down
        self.data=np.flipud(self.data)
        self.Display(self.data)
    
    def flipVertAct (self):
        #flip the image left/right
        self.data=np.fliplr(self.data)
        self.Display(self.data)
    
    
    def open_widget(self,fene):
        """ open new widget 
        """

        if fene.isWinOpen==False:
            fene.setup
            fene.isWinOpen=True
            
            #fene.Display(self.data)
            fene.show()
        else:
            #fene.activateWindow()
            # fene.raise_()
            fene.showNormal()
    
    
    def dragEnterEvent(self, e):
        e.accept()

        
    def dropEvent(self, e):
        #allow to drop image in visu and open it
        l = []
        for url in e.mimeData().urls():
            l.append(str(url.toLocalFile()))
        e.accept()
        
        if len(l)>1: #open multi file in drag process
                self.openedFiles=l
                self.sliderImage.setMinimum(0)
                self.sliderImage.setMaximum(len(l) - 1)
                self.sliderImage.setValue(0)
                self.sliderImage.setEnabled(True)
                
        
        self.OpenF(fileOpen=l[0])
    
    def checkBoxScaleImage(self):
        if self.checkBoxScale.isChecked()==True:
            self.checkBoxScale.setIcon(QtGui.QIcon(self.icon+"expand.png"))
            self.checkBoxScale.setText('Auto Scale On')
        else :
             self.checkBoxScale.setIcon(QtGui.QIcon(self.icon+"minimize.png"))
             self.checkBoxScale.setText('Auto Scale Off')
    
    def autoSaveColor(self):
        
        if self.checkBoxAutoSave.isChecked()==True:
            self.checkBoxAutoSave.setIcon(QtGui.QIcon(self.icon+"saveAutoOn.png"))
            self.checkBoxAutoSave.setText('Auto Save on')
        else :
             self.checkBoxAutoSave.setIcon(QtGui.QIcon(self.icon+"diskette.png"))
             self.checkBoxAutoSave.setText('Auto Save off')
    
             
    def fluenceFct(self):
        self.sizeFluenceX=self.roiFluence.size()[0]
        self.sizeFluenceY=self.roiFluence.size()[1]
        self.Display(self.data)
    
    
    def ZoomMAX(self):
        self.open_widget(self.winZoomMax)
        self.winZoomMax.SetTITLE('MAX')
        self.maxx=round(self.data.max(),3)
        self.winZoomMax.setZoom(self.maxx)
    
    def closeEvent(self,event):
        self.close()
    def close(self):
        
        # when the window is closed
        if self.encercled=="on":
            if self.winEncercled.isWinOpen==True:
                self.winEncercled.close()
        if self.winCoupe.isWinOpen==True:
            self.winCoupe.close()
        if self.meas=="on":
            if self.winM.isWinOpen==True:
                self.winM.close()
        if self.winOpt.isWinOpen==True:
            self.winOpt.close() 
        if self.winPref.isWinOpen==True:
            self.winPref.close() 
        if self.fft=='on':
            if self.winFFT.isWinOpen==True:
                self.winFFT.close()
            if self.winFFT1D.isWinOpen==True:
                self.winFFT1D.close()
        
       
        
def runVisu(file=None,path=None) :
        
    from pyqtgraph.Qt.QtWidgets import QApplication
    import sys
    import qdarkstyle
    import visu
    
    appli = QApplication(sys.argv)   
    appli.setStyleSheet(qdarkstyle.load_stylesheet(qt_api='pyqt6'))
    e = visu.visual2.SEE2(file=file,path=path)
    e.show()
    appli.exec_() 

   
if __name__ == "__main__":
    
    appli = QApplication(sys.argv) 
    appli.setStyleSheet(qdarkstyle.load_stylesheet(qt_api='pyqt6'))
    pathVisu="/Users/juliengautier/Desktop/confTest.ini"
    
    name="testVisu"
    conf=QtCore.QSettings(pathVisu, QtCore.QSettings.Format.IniFormat)
    
    #file='FP__2201_2019_01_17_13_17_59.TIFF'
    #path='/Users/juliengautier/Dropbox (LOA)/Data_Analysis_LOA/Laser X/Manip Janvier 2019/FP/2019-01-16'
    e = SEE(aff='left',roiCross=True)#,color="red")#,conf=conf,name=name)
    e.show()
    appli.exec_() 





