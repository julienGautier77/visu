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



from ctypes import alignment
import pyqtgraph as pg # pip install pyqtgraph (https://github.com/pyqtgraph/pyqtgraph.git)
from PyQt6 import QtCore,QtGui
from PyQt6.QtWidgets import QApplication,QVBoxLayout,QHBoxLayout,QWidget
from PyQt6.QtWidgets import QCheckBox,QLabel,QSizePolicy,QMenu,QMessageBox,QFileDialog
from PyQt6.QtWidgets import QMainWindow,QStatusBar
from PyQt6.QtGui import QShortcut,QAction
from PyQt6.QtCore import pyqtSlot,Qt
from PyQt6.QtGui import QIcon
import sys,time,os

import numpy as np
import qdarkstyle # pip install qdarkstyle https://github.com/ColinDuquesnoy/QDarkStyleSheet  sur conda
from scipy.interpolate import splrep, sproot #
from scipy.ndimage import gaussian_filter,median_filter
from PIL import Image
from visu.winspec import SpeFile
from visu.winMeas import MEAS
from visu.WinOption import OPTION
from visu.WinPreference import PREFERENCES
from visu.andor import SifFile
from visu.winPointing import WINPOINTING

    
import pathlib
import visu

__version__=visu.__version__
__author__=visu.__author__


__all__=['SEELIGHT','runVisu']

class SEELIGHT(QMainWindow) :
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
    
    def __init__(self,parent=None,file=None,path=None,**kwds):
        
        super().__init__()
        version=__version__
        print("data visualisation :  ",version)
        p = pathlib.Path(__file__)
        self.parent=parent
        self.fullscreen=False
        self.setAcceptDrops(True)
        sepa=os.sep
        self.icon=str(p.parent) + sepa+'icons' +sepa
        self.colorBar='flame'
        
        self.nomFichier=''
        
        
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
    
        if "name" in kwds:
            self.name=kwds["name"]
        else:
            self.name="VISU"
        
        if "crossON" in kwds:
            # print('ROICROSS on')
            self.crossON=kwds["crossON"]
        else :
            self.crossON=True
        
        if "roiCross" in kwds:
            # print('ROICROSS on')
            self.roiCross=kwds["roiCross"]
        else :
            self.roiCross=True
            # print('no roicross')
       
        if "aff" in kwds:
            self.aff=kwds["aff"]
        else :
            self.aff="right"
        
        
        
        if "meas" in kwds:
            self.meas=kwds["meas"]
        else:
           self.meas="on" 
           
        if "toolBar" in kwds:
            self.toolBarOn=kwds["toolBar"]
        else:
            self.toolBarOn=True
            
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
        
        
            
        self.winPointing=WINPOINTING(parent=self)
        
        self.path=path
        self.setWindowTitle('Visualization'+'       v.'+ version)
        self.bloqKeyboard=1#=bool((self.conf.value(self.name+"/bloqKeyboard"))  )  # block cross by keyboard
        self.bloqq=1 # block the cross by click on mouse
        
        # initialize variable : 
        self.filter='origin' # filter initial value
        self.ite=None
        self.setWindowIcon(QIcon(self.icon+'LOA.png'))
        self.zo=1 # zoom initial value
        self.scaleAxis="off"
        self.plotRectZoomEtat='Zoom'
        self.angleImage=0
        
        
        
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
        
        self.setup()
        self.shortcut()
        self.actionButton()
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
        
        
        
        #self.toolBar.setOrientation(Qt.Vertical)
        #self.setStyleSheet("{background-color: black}")
        menubar = self.menuBar()
        menubar.setNativeMenuBar(False)
        self.fileMenu = menubar.addMenu('&File')
        self.ImageMenu = menubar.addMenu('&Image')
        #self.ProcessMenu = menubar.addMenu('&Process')
        self.AnalyseMenu = menubar.addMenu('&Analyse')
        
        self.ZoomMenu = menubar.addMenu('&Zoom')
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
        #self.toolBar.addAction(self.openAct)
        self.fileMenu.addAction(self.openAct)
        
        self.saveAct=QAction(QtGui.QIcon(self.icon+"disketteSave.png"), 'Save file', self)
        self.saveAct.setShortcut('Ctrl+s')
        self.saveAct.triggered.connect(self.SaveF)
        #self.toolBar.addAction(self.saveAct)
        self.fileMenu.addAction(self.saveAct)

        
        self.checkBoxAutoSave=QAction(QtGui.QIcon(self.icon+"diskette.png"),'AutoSave off',self)
        self.checkBoxAutoSave.setCheckable(True)
        self.checkBoxAutoSave.setChecked(False)
        
        self.checkBoxAutoSave.triggered.connect(self.autoSaveColor)
        #self.toolBar.addAction(self.checkBoxAutoSave)
        self.fileMenu.addAction(self.checkBoxAutoSave)
        
        
        self.optionAutoSaveAct=QAction(QtGui.QIcon(self.icon+"Settings.png"),'Option',self) #
        self.optionAutoSaveAct.triggered.connect(lambda:self.open_widget(self.winOpt))
        #self.toolBar.addAction(self.optionAutoSaveAct)
        self.fileMenu.addAction(self.optionAutoSaveAct)
        
        self.preferenceAct=QAction('Preferences',self) #
        self.preferenceAct.triggered.connect(lambda:self.open_widget(self.winPref))
        
        self.fileMenu.addAction(self.preferenceAct)
        
        self.checkBoxPlot=QAction(QtGui.QIcon(self.icon+"target.png"),'Cross On (ctrl+b to block ctrl+d to unblock)',self)
        self.checkBoxPlot.setCheckable(True)
        
        self.checkBoxPlot.setChecked(self.crossON)
        self.checkBoxPlot.triggered.connect(self.PlotXY)
        
        self.AnalyseMenu.addAction(self.checkBoxPlot)
        
        
        
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
        self.fileName.setStyleSheet("font:8pt")
        self.fileName.setMaximumHeight(30)
        self.fileName.setMaximumWidth(200000)
        self.fileName.setAlignment(Qt.AlignmentFlag.AlignVCenter)
        self.statusBar.addWidget(self.labelFileName)
        self.statusBar.addWidget(self.fileName)
         
        self.checkBoxScale=QAction(QtGui.QIcon(self.icon+"expand.png"),' Auto Scale on',self)
        self.checkBoxScale.setCheckable(True)
        self.checkBoxScale.setChecked(True)
        
        self.ImageMenu.addAction(self.checkBoxScale)
        self.checkBoxScale.triggered.connect(self.checkBoxScaleImage)
        
        self.checkBoxColor=QAction(QtGui.QIcon(self.icon+"colors-icon.png"),'Color on',self)
        self.checkBoxColor.triggered.connect(self.Color)
        self.checkBoxColor.setCheckable(True) 
        self.checkBoxColor.setChecked(True)
        
        self.ImageMenu.addAction(self.checkBoxColor)
        
    
        self.checkBoxHist=QAction(QtGui.QIcon(self.icon+"colourBar.png"),'Show colour Bar',self)
        self.checkBoxHist.setCheckable(True)
        self.checkBoxHist.setChecked(False)
        self.checkBoxHist.triggered.connect(self.HIST)
        self.ImageMenu.addAction(self.checkBoxHist)
        
        #self.ColorBox=QAction('&LookUp Table',self)
        menuColor=QMenu('&LookUp Table',self)
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
        
        
        
        
        
        if self.meas=='on':
            self.MeasButton=QAction(QtGui.QIcon(self.icon+"laptop.png"),'Measure',self)
            self.MeasButton.setShortcut('ctrl+m')
            self.MeasButton.triggered.connect(self.Measurement)
            self.AnalyseMenu.addAction(self.MeasButton)
            
        
        
        self.PointingButton=QAction(QtGui.QIcon(self.icon+"recycle.png"),'Pointing',self)
        self.PointingButton.triggered.connect(self.Pointing)
        self.AnalyseMenu.addAction(self.PointingButton)       
            
        self.ZoomRectButton=QAction(QtGui.QIcon(self.icon+"loupe.png"),'Zoom',self)
        self.ZoomRectButton.triggered.connect(self.zoomRectAct)
        
        self.ZoomMenu.addAction(self.ZoomRectButton)
        
        
        if self.toolBarOn==True:
            self.toolBar =self.addToolBar('tools')
            
            self.toolBar.addAction(self.checkBoxPlot)
            self.toolBar.addAction(self.checkBoxScale)
            self.toolBar.addAction(self.checkBoxColor)
            self.toolBar.addAction(self.ZoomRectButton)
            self.checkBoxZoom=QCheckBox('Zoom',self)
            self.checkBoxZoom.setChecked(False)
            self.checkBoxZoom.setStyleSheet("QCheckBox { background-color: transparent }""QCheckBox::indicator{width: 30px;height: 30px;}""QCheckBox::indicator:unchecked { image : url(./icons/Toggle_Off.png);background-color: transparent;}""QCheckBox::indicator:checked { image:  url(./icons/Toggle_On.png);background-color: transparent;}")
            
            self.toolBar.addWidget(self.checkBoxZoom)
            self.checkBoxZoom.stateChanged.connect(self.ZoomBut)
            self.toolBar.setMovable(False)
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
        
       
        self.PlotXY()
        #histogram
        self.hist = pg.HistogramLUTItem() 
        self.hist.setImageItem(self.imh)
        self.hist.autoHistogramRange()
        self.hist.gradient.loadPreset('flame')
        
        
        hMainLayout=QHBoxLayout()
       
        
        if self.aff=='right':
            hMainLayout.addLayout(self.vbox2)
            hMainLayout.addLayout(self.vbox1)
        if self.aff=='left':
            hMainLayout.addLayout(self.vbox1)
            hMainLayout.addLayout(self.vbox2)
        
        
        hMainLayout.setContentsMargins(1,1,1,1)
        #hMainLayout.setSpacing(1)
        #hMainLayout.setStretch(10,1)
        MainWidget=QWidget()
        
        MainWidget.setLayout(hMainLayout)
        self.setCentralWidget(MainWidget)
        self.plotRectZoom=pg.RectROI([self.xc/2,self.yc/2],[2*self.rx,2*self.ry],pen='w')
        self.plotRectZoom.addScaleHandle((0,0),center=(1,1))
        #self.setStyleSheet(qdarkstyle.load_stylesheet(qt_api='pyqt6')) # dark style
        
        
        self.Display(self.data)
        
    def actionButton(self):
        # action of button
        
        self.ro1.sigRegionChangeFinished.connect(self.roiChanged)
        self.winPref.closeEventVar.connect(self.ScaleImg)
        if self.parent is not None:
            self.parent.signalData.connect(self.newDataReceived)
        
        
    def shortcut(self):
        # keyboard shortcut
        
        self.shortcutPu=QShortcut(QtGui.QKeySequence("+"),self)
        self.shortcutPu.activated.connect(self.paletteup)
        self.shortcutPu.setContext(Qt.ShortcutContext(3))
        #3: The shortcut is active when its parent widget, or any of its children has focus. default O The shortcut is active when its parent widget has focus.
        self.shortcutPd=QtGui.QShortcut(QtGui.QKeySequence("-"),self)
        self.shortcutPd.activated.connect(self.palettedown)
        self.shortcutPd.setContext(Qt.ShortcutContext(3))
        
        # self.shortcutOpen=QtGui.QShortcut(QtGui.QKeySequence("Ctrl+o"),self)
        # self.shortcutOpen.activated.connect(self.OpenF)
        # self.shortcutOpen.setContext(Qt.ShortcutContext(3))
        
        # self.shortcutSave=QtGui.QShortcut(QtGui.QKeySequence("Ctrl+s"),self)
        # self.shortcutSave.activated.connect(self.SaveF)
        # self.shortcutSave.setContext(Qt.ShortcutContext(3))
        
        # self.shortcutMeas=QtGui.QShortcut(QtGui.QKeySequence('Ctrl+m'),self)
        # self.shortcutMeas.activated.connect(self.Measurement)
        # self.shortcutMeas.setContext(Qt.ShortcutContext(3))
        
        # self.shortcutCut=QtGui.QShortcut(QtGui.QKeySequence('Ctrl+k'),self)
        # self.shortcutCut.activated.connect(self.CUT)
        # self.shortcutCut.setContext(Qt.ShortcutContext(3))
        
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
        
        
        
        
    def Measurement(self) :
        # show widget for measurement on all image or ROI  (max, min mean ...)
        
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
                self.winPointing.Display(pData,self.winPref.stepX,self.winPref.stepX)
        else:
                self.winPointing.Display(pData)

    
        
    @pyqtSlot (object)   
    def Display(self,data):
        #  display the data and refresh all the calculated things and plots
        self.data=data
        
        
        if self.checkBoxBg.isChecked()==True and self.winOpt.dataBgExist==True:
            try :
                self.data=self.data-self.winOpt.dataBg
            except :
                msg = QMessageBox()
                msg.setIcon(QMessageBox.Critical)
                msg.setText("Background not soustracred !")
                msg.setInformativeText("Background file error  ")
                msg.setWindowTitle("Warning ...")
                msg.setWindowFlags(QtCore.Qt.WindowType.WindowStaysOnTopHint)
                msg.exec_()
                
        if self.checkBoxBg.isChecked()==True and self.winOpt.dataBgExist==False:
                msg = QMessageBox()
                msg.setIcon(QMessageBox.Critical)
                msg.setText("Background not soustracted !")
                msg.setInformativeText("Background file not selected in options menu ")
                msg.setWindowTitle("Warning ...")
                msg.setWindowFlags(QtCore.Qt.WindowType.WindowStaysOnTopHint)
                msg.exec_()
            
        
        
        # self.p1.setAspectLocked(True,ratio=1)
        
        ### color  and sacle 
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
        
        if self.winPointing.isWinOpen==True:
            self.Pointing()
        ### autosave
        if self.checkBoxAutoSave.isChecked()==True: ## autosave data
            self.pathAutoSave=str(self.conf.value(self.name+'/pathAutoSave'))
            self.fileNameSave=str(self.conf.value(self.name+'/nameFile'))
            date=time.strftime("%Y_%m_%d_%H_%M_%S")
            self.numTir=int(self.conf.value(self.name+'/tirNumber'))
            if self.numTir<10:
                num="00"+str(self.numTir)
            elif 9<self.numTir<100:
                num="0"+str(self.numTir)
            else:
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

            self.numTir+=1
            self.winOpt.setTirNumber(self.numTir)
            self.conf.setValue(self.name+"/tirNumber",self.numTir)
            self.fileName.setText(nomFichier)
    
        
        self.zoomRectupdate() # update rect
        
    def mouseClick(self,evt): # block the cross if mousse button clicked
        
    
        if self.bloqq==1:
            self.bloqq=0
            
        else :
            self.bloqq=1
            self.conf.setValue(self.name+"/xc",int(self.xc)) # save cross postion in ini file
            self.conf.setValue(self.name+"/yc",int(self.yc))
            
            
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
                        self.label_CrossValue.setText(' v.=' + str(dataCross))
        
        
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
        
       
    # def Coupe(self):
        # # make  plot profile on cross
        
        # if self.checkBoxPlot.isChecked()==True:
            

                
        #     try :
        #         dataCross=self.data[int(self.xc),int(self.yc)] 
        #     except :dataCross=0  # evoid to have an error if cross if out of the image
            
    
                
        #     if self.winPref.checkBoxAxeScale.isChecked()==1: # scale axe on 
        #         self.label_Cross.setText('x='+ str(round(int(self.xc)*self.winPref.stepX,2)) + '  um'+' y=' + str(round(int(self.yc)*self.winPref.stepY,2)) +' um')
        #     else : 
        #         self.label_Cross.setText('x='+ str(int(self.xc)) + ' y=' + str(int(self.yc)) )
                
        #     dataCross=round(dataCross,3) # take data  value  on the cross
        #     self.label_CrossValue.setText(' v.=' + str(dataCross))
            
            
 
    def PlotXY(self): # plot curves on the  graph
        
        if self.checkBoxPlot.isChecked()==1:
            
            self.p1.addItem(self.vLine, ignoreBounds=False)
            self.p1.addItem(self.hLine, ignoreBounds=False)
           
            # self.p1.showAxis('left',show=True)
            # self.p1.showAxis('bottom',show=True)
           
            if self.roiCross==True:
                self.p1.addItem(self.ro1)
            # self.Coupe()
        else:
            self.p1.removeItem(self.vLine)
            self.p1.removeItem(self.hLine)
            
            self.p1.showAxis('left',show=False)
            self.p1.showAxis('bottom',show=False)
            # self.label_Cross.setText('')
            # self.label_CrossValue.setText('')
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
            self.checkBoxColor.setText('Color on')
        else:
            self.hist.gradient.loadPreset('grey')
            self.checkBoxColor.setText('Grey')
            self.checkBoxColor.setIcon(QtGui.QIcon(self.icon+"circleGray.png"))
            
    def roiChanged(self):
        
        self.rx=self.ro1.size()[0]
        self.ry=self.ro1.size()[1]
        self.conf.setValue(self.name+"/rx",int(self.rx))
        self.conf.setValue(self.name+"/ry",int(self.ry))
      
        
    def bloquer(self): # block the cross
        
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
    
    
        
    def OpenF(self,fileOpen=False):
        #open file in txt spe TIFF sif jpeg png  format
        fileOpen=fileOpen
        
        if fileOpen==False:
            
            chemin=self.conf.value(self.name+"/path")
            fname=QFileDialog.getOpenFileNames(self,"Open File",chemin,"Images (*.txt *.spe *.TIFF *.sif *.tif);;Text File(*.txt);;Ropper File (*.SPE);;Andor File(*.sif);; TIFF file(*.TIFF)")
            
            fichier=fname[0]
            self.openedFiles=fichier

            self.nbOpenedImage=len(fichier)
            if self.nbOpenedImage==1:
                fichier=fichier[0]
                self.sliderImage.setEnabled(False)
            if self.nbOpenedImage>1:
                fichier=fichier[0]
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
            msg.setIcon(QMessageBox.Icon.Critical)
            msg.setText("Wrong file format !")
            msg.setInformativeText("The format of the file must be : .SPE  .TIFF .sif  png jpeg or .txt ")
            msg.setWindowTitle("Warning ...")
            msg.setWindowFlags(QtCore.Qt.WindowType.WindowStaysOnTopHint)
            msg.exec_()
            
        chemin=os.path.dirname(fichier)
        self.conf.setValue(self.name+"/path",chemin)
        self.conf.setValue(self.name+"/lastFichier",os.path.split(fichier)[1])
        print('open',fichier)
        
        self.fileName.setText(str(fichier))
        self.nomFichier=os.path.split(fichier)[1]
    
        self.newDataReceived(data)
        
        
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
       
        self.dimy=np.shape(self.data)[1]
        self.dimx=np.shape(self.data)[0]
        self.dataOrgScale=self.data
        self.dataOrg=self.data
        
        self.Display(self.data)
        
    

    
    def ScaleImg(self):
        #scale Axis px to um
        if self.winPref.checkBoxAxeScale.isChecked()==1:
            self.scaleAxis="on"
            self.LigneChanged()
        else :
            self.scaleAxis="off"
        self.data=self.dataOrg
        self.Display(self.data)
    
    
    def zoomRectAct(self):
        
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
            self.p1.setYRange(0,self.dimy)
            self.p1.setXRange(0,self.dimx)
            self.ZoomRectButton.setIcon(QtGui.QIcon(self.icon+"loupe.png"))
            self.plotRectZoomEtat="Zoom"
            self.ZoomRectButton.setText('Zoom Selection')
            self.p1.setAspectLocked(True)
        
        # self.Coupe()  
        
    def zoomRectupdate(self):
        if self.plotRectZoomEtat=="ZoomOut":
            self.p1.setXRange(self.xZoomMin,self.xZoomMax)
            self.p1.setYRange(self.yZoomMin,self.yZoomMax)
            self.p1.setAspectLocked(True)
        # else:
        #     self.p1.setYRange(0,self.dimy)
        #     self.p1.setXRange(0,self.dimx)
        #     print('ra')
    def ZoomBut(self):
        if self.checkBoxZoom.isChecked()==1:
            self.p1.setXRange(self.xc-200,self.xc+200)
            self.p1.setYRange(self.yc-200,self.yc+200)
        else:
            self.p1.setXRange(0,self.dimx)
            self.p1.setYRange(0,self.dimy)           
        
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
            #fene.raise_()
            fene.showNormal()
    
    
    def dragEnterEvent(self, e):
        e.accept()

        
    def dropEvent(self, e):
        l = []
        for url in e.mimeData().urls():
            l.append(str(url.toLocalFile()))
        e.accept()
        self.OpenF(fileOpen=l[0])
    
    def checkBoxScaleImage(self):
        if self.checkBoxScale.isChecked()==True:
            self.checkBoxScale.setIcon(QtGui.QIcon(self.icon+"expand.png"))
            self.checkBoxScale.setText('Àuto Scale  On')
        else :
             self.checkBoxScale.setIcon(QtGui.QIcon(self.icon+"minimize.png"))
             self.checkBoxScale.setText('Àuto Scale  Off')
    
    def autoSaveColor(self):
        
        if self.checkBoxAutoSave.isChecked()==True:
            self.checkBoxAutoSave.setIcon(QtGui.QIcon(self.icon+"saveAutoOn.png"))
            self.checkBoxAutoSave.setText('Auto Save On')
        else :
             self.checkBoxAutoSave.setIcon(QtGui.QIcon(self.icon+"diskette.png"))
             self.checkBoxAutoSave.setText('Auto Save Off')
    def closeEvent(self,event):
        # when the window is closed
        
        if self.meas=="on":
            if self.winM.isWinOpen==True:
                self.winM.close()
        if self.winOpt.isWinOpen==True:
            self.winOpt.close() 
        if self.winPref.isWinOpen==True:
            self.winPref.close() 
        
       
        
def runVisu() :
        
    from pyqtgraph.Qt.QtWidgets import QApplication
    import sys
    import qdarkstyle
    import visu
    
    appli = QApplication(sys.argv)   
    appli.setStyleSheet(qdarkstyle.load_stylesheet(qt_api='pyqt6'))
    e = visu.visual2.SEE2()
    e.show()
    appli.exec_() 

   
if __name__ == "__main__":
    
    appli = QApplication(sys.argv) 
    appli.setStyleSheet(qdarkstyle.load_stylesheet(qt_api='pyqt6'))
    e = SEELIGHT(aff='left',roiCross=True,crossON=True,toolBar=False)
    e.show()
    appli.exec_() 





