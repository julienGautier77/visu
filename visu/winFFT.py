#!/usr/bin/env python3
# -*- coding: utf-8 -*-


"""
Created on Mon May  6 11:24:23 2019
Windows for display FFT
@author: juliengautier


"""

import sys,os,time
import numpy as np
import qdarkstyle # pip install qdakstyle https://github.com/ColinDuquesnoy/QDarkStyleSheet  sur conda
import pathlib

from PyQt5.QtWidgets import QApplication,QVBoxLayout,QHBoxLayout,QWidget,QPushButton,QGridLayout
from PyQt5.QtWidgets import QInputDialog,QSlider,QCheckBox,QLabel,QSizePolicy,QMenu,QMessageBox
from PyQt5.QtWidgets import QShortcut
from pyqtgraph.Qt import QtCore,QtGui 
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon
import pylab
import pyqtgraph as pg # pip install pyqtgraph (https://github.com/pyqtgraph/pyqtgraph.git)


from scipy.interpolate import splrep, sproot #
from scipy.ndimage.filters import gaussian_filter,median_filter
from PIL import Image
from visu.winspec import SpeFile
from visu.winSuppE import WINENCERCLED
from visu.WinCut import GRAPHCUT
from visu.winMeas import MEAS
from visu.WinOption import OPTION
from visu.andor import SifFile


class WINFFT(QWidget):
    
    def __init__(self,conf=None,name='VISU'):
        
        super(WINFFT, self).__init__()
        self.name=name
        p = pathlib.Path(__file__)
        if conf==None:
            self.conf=QtCore.QSettings(str(p.parent / 'confVisu.ini'), QtCore.QSettings.IniFormat)
        else :
            self.conf=conf
        sepa=os.sep
        self.icon=str(p.parent) + sepa+'icons' +sepa
        self.confCCD = conf
        self.isWinOpen=False
        self.setWindowTitle('FFT')
        self.setWindowIcon(QIcon(self.icon+'LOA.png'))
        self.setStyleSheet(qdarkstyle.load_stylesheet_pyqt5())
        self.setup()      
        
    
    def setup(self):
        
        self.visualisationFFT=SEEFFT(conf=None,name='VISU')
        vbox3=QVBoxLayout() 
        vbox3.addWidget(self.visualisationFFT)
        hMainLayout=QHBoxLayout()
        hMainLayout.addLayout(vbox3)
        self.setLayout(hMainLayout)
    
    
    def Display(self,data):
        self.data=data
        if self.data.ndim==2:
            datafft=np.fft.fft2(np.array(self.data))
            self.norm=abs(np.fft.fftshift(datafft))#datafft*datafft.conj()
            self.norm=np.log10(1+self.norm)
            self.visualisationFFT.newDataReceived(self.norm)
     
           
    def closeEvent(self, event):
        """ when closing the window
        """
        self.isWinOpen=False
        event.accept()




class SEEFFT(QWidget) :
    '''open and plot file : 
        SEE(file='nameFile,path=pathFileName)
        Make plot profile ands differents measurements(max,min mean...)
        Can open .spe .SPE .sif .TIFF files
   
    '''
   
    def __init__(self,file=None,path=None,conf=None,name='VISU'):
        
        super(SEEFFT, self).__init__()
        p = pathlib.Path(__file__)
        self.setStyleSheet(qdarkstyle.load_stylesheet_pyqt5())
        if conf==None:
            conf=QtCore.QSettings(str(p.parent / 'confVisu.ini'), QtCore.QSettings.IniFormat)
        else :self.conf=conf
        self.name=name
        sepa=os.sep
        self.icon=str(p.parent) + sepa+'icons' +sepa
        self.conf = conf
        
        self.winEncercled=WINENCERCLED(conf=self.conf,name=self.name)
        self.winCoupe=GRAPHCUT(symbol=False,conf=self.conf,name=self.name)
    
        self.winM=MEAS(conf=self.conf,name=self.name)
        self.winOpt=OPTION(conf=self.conf,name=self.name)
        
        self.nomFichier=''
        
        self.path=path
        self.setWindowTitle('FTT')
        self.setup()
        self.shortcut()
        self.actionButton()
        self.activateWindow()
        self.raise_()
        self.showNormal()
        self.filter='origin'
        self.ite=None
        self.setWindowIcon(QIcon(self.icon+'LOA.png'))
        
        if file==None:
            
            self.dimy=960
            self.dimx=1240
            # Create x and y index
            self.x = np.arange(0,self.dimx)
            self.y = np.arange(0,self.dimy)
            self.y,self.x = np.meshgrid(self.y, self.x)
    
            self.data=(50*np.random.rand(self.dimx,self.dimy)).round() + 150
        else:
            if path==None:
                self.path=self.conf.value(self.name+"/path")
            
            self.OpenF(fileOpen=self.path+'/'+file)
            
        self.bloqq=1
        
        
    def setup(self):
        
        TogOff=self.icon+'Toggle_Off.png'
        TogOn=self.icon+'Toggle_On.png'
        TogOff=pathlib.Path(TogOff)
        TogOff=pathlib.PurePosixPath(TogOff)
        TogOn=pathlib.Path(TogOn)
        TogOn=pathlib.PurePosixPath(TogOn)
        
        self.setStyleSheet("QCheckBox::indicator{width: 30px;height: 30px;}""QCheckBox::indicator:unchecked { image : url(%s);}""QCheckBox::indicator:checked { image:  url(%s);}""QCheckBox{font :10pt;}" % (TogOff,TogOn) )
        
        vbox1=QVBoxLayout() 
        
        hbox2=QHBoxLayout()
        self.openButton=QPushButton('Open',self)
        self.openButton.setIcon(QtGui.QIcon(self.icon+"Open.png"))
        self.openButton.setIconSize(QtCore.QSize(50,50))
        self.openButton.setMaximumWidth(200)
        self.openButton.setMaximumHeight(100)
        self.openButton.setShortcut(QtGui.QKeySequence("Ctrl+O"))
        hbox2.addWidget(self.openButton)
        self.openButtonhbox4=QHBoxLayout()
        self.openButton.setStyleSheet("background-color: rgb(0, 0, 0,0) ;border-color: rgb(0, 0, 0,0)")
        
        self.saveButton=QPushButton('Save',self)
        self.saveButton.setMaximumWidth(100)
        self.saveButton.setMinimumHeight(100)
        self.saveButton.setIconSize(QtCore.QSize(50,50))
        hbox2.addWidget(self.saveButton)
        self.saveButton.setIcon(QtGui.QIcon(self.icon+"Saving.png"))
        self.saveButton.setStyleSheet("background-color: rgb(0, 0, 0,0) ;border-color: rgb(0, 0, 0,0)")
        vbox1.addLayout(hbox2)
        
        hbox3=QHBoxLayout()
        grid_layout0 = QGridLayout()
        self.checkBoxAutoSave=QCheckBox('AutoSave',self)
        self.checkBoxAutoSave.setChecked(False)
        grid_layout0.addWidget(self.checkBoxAutoSave,0,0)
        self.checkBoxBg=QCheckBox('Bg substraction',self)
        self.checkBoxBg.setChecked(False)
        grid_layout0.addWidget(self.checkBoxBg,1,0)
        self.optionAutoSave=QPushButton('Options',self)
        hbox3.addLayout( grid_layout0)
        self.optionAutoSave.setIcon(QtGui.QIcon(self.icon+"Settings.png"))
        #self.optionAutoSave.setIconSize(QtCore.QSize(20,20))
        hbox3.addWidget(self.optionAutoSave)
        vbox1.addLayout(hbox3)

        hbox8=QHBoxLayout()
        
        hbox4=QHBoxLayout()
        self.labelFileName=QLabel("File :")
        self.labelFileName.setStyleSheet("font:15pt;")
        self.labelFileName.setMinimumHeight(30)
        self.labelFileName.setMaximumWidth(40)
        hbox4.addWidget(self.labelFileName)
        hbox42=QHBoxLayout()
    
        self.fileName=QLabel()
        self.fileName.setStyleSheet("font:10pt")
        self.fileName.setMaximumHeight(30)
        self.fileName.setMaximumWidth(150)
        hbox42.addWidget(self.fileName)
        vbox1.addLayout(hbox4)
        vbox1.addLayout(hbox42)
        
        hbox5=QHBoxLayout()
        self.checkBoxPlot=QCheckBox('CROSS',self)
        self.checkBoxPlot.setChecked(False)

        hbox5.addWidget(self.checkBoxPlot)
        hbox6=QHBoxLayout()
        self.label_Cross=QLabel()
        #self.label_Cross.setMaximumHeight(20)
        self.label_Cross.setMaximumWidth(150)
        self.label_Cross. setStyleSheet("font:10pt")
        hbox6.addWidget(self.label_Cross)
        #hbox6.setSpacing(1)
        vbox1.addLayout(hbox5)
        vbox1.addLayout(hbox6)
        
        self.ZoomLabel=QLabel('Zoom')
        vbox1.addWidget(self.ZoomLabel)
        self.checkBoxZoom=QSlider(Qt.Horizontal)
        self.checkBoxZoom.setMaximumWidth(200)
        self.checkBoxZoom.setMinimum(-5)
        self.checkBoxZoom.setMaximum(100)
        self.checkBoxZoom.setValue(-20)
        vbox1.addWidget(self.checkBoxZoom)
        
        self.checkBoxScale=QCheckBox('Auto Scale',self)
        self.checkBoxScale.setChecked(True)
        self.checkBoxScale.setMaximumWidth(100)
        
        self.checkBoxColor=QCheckBox('Color',self)
        self.checkBoxColor.setChecked(True)
    
        self.checkBoxHist=QCheckBox('Hist',self)
        self.checkBoxHist.setChecked(False)
        self.maxGraphBox=QCheckBox('Max',self)
        grid_layout = QGridLayout()
        grid_layout.setVerticalSpacing(0)
        grid_layout.setHorizontalSpacing(10)
        grid_layout.addWidget(self.checkBoxScale, 0, 0)
        grid_layout.addWidget(self.checkBoxColor,1,0)
        grid_layout.addWidget(self.checkBoxHist, 0, 1)
        #grid_layout.addWidget(self.checkBoxZoom, 1, 0)
        grid_layout.addWidget(self.maxGraphBox, 1,1)
        
        hbox8.addLayout(grid_layout)
        
        vbox1.addLayout(hbox8)
        
        hbox9=QHBoxLayout()
        self.energyBox=QPushButton('&Encercled',self)
        hbox9.addWidget(self.energyBox)
        self.filtreBox=QPushButton('&Filters',self)
        menu=QMenu()
        menu.addAction('&Gaussian',self.Gauss)
        menu.addAction('&Median',self.Median)
        menu.addAction('&Origin',self.Orig)
        self.filtreBox.setMenu(menu)
        hbox9.addWidget(self.filtreBox)
        vbox1.addLayout(hbox9)
        
        hbox11=QHBoxLayout()
        self.PlotButton=QPushButton('Plot')
        hbox11.addWidget(self.PlotButton)
        self.MeasButton=QPushButton('Meas.')
        hbox11.addWidget(self.MeasButton)
        
        hbox10=QHBoxLayout()
        self.ligneButton=QPushButton('Line')
        self.ligneButton.setIcon(QtGui.QIcon(self.icon+"ligne.jpeg")) 

        hbox10.addWidget(self.ligneButton)
        
        self.rectangleButton=QPushButton('Rect')
        self.rectangleButton.setIcon(QtGui.QIcon(self.icon+"rectangle.png")) 
        hbox10.addWidget(self.rectangleButton)
        
        self.circleButton=QPushButton('Circle')
        self.circleButton.setIcon(QtGui.QIcon(self.icon+"Red_circle.png")) 
        hbox10.addWidget(self.circleButton)
        
        vbox1.addLayout(hbox11)
        vbox1.addLayout(hbox10)
        vbox1.addStretch(1)
        
        self.winImage = pg.GraphicsLayoutWidget()
        self.winImage.setContentsMargins(0,0,0,0)
        self.winImage.setAspectLocked(True)
        self.winImage.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.winImage.ci.setContentsMargins(0,0,0,0)
        
        vbox2=QVBoxLayout()
        vbox2.addWidget(self.winImage)
        vbox2.setContentsMargins(0,0,0,0)
        
        self.p1=self.winImage.addPlot()
        self.imh=pg.ImageItem()
        self.p1.addItem(self.imh)
        self.p1.setMouseEnabled(x=False,y=False)
        self.p1.setContentsMargins(0,0,0,0)
   
        self.p1.setAspectLocked(True,ratio=1)
        self.p1.showAxis('right',show=False)
        self.p1.showAxis('top',show=False)
        self.p1.showAxis('left',show=False)
        self.p1.showAxis('bottom',show=False)
        
        self.vLine = pg.InfiniteLine(angle=90, movable=False,pen='y')
        self.hLine = pg.InfiniteLine(angle=0, movable=False,pen='y')

        self.xc=10
        self.yc=10
        self.rx=50
        self.ry=50
        self.vLine.setPos(self.xc)
        self.hLine.setPos(self.yc)
        
        self.ro1=pg.EllipseROI([self.xc,self.yc],[self.rx,self.ry],pen='y',movable=False,maxBounds=QtCore.QRectF(0,0,self.rx,self.ry))
        self.ro1.setPos([self.xc-(self.rx/2),self.yc-(self.ry/2)])
      
       
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
        
        ## main layout
        hMainLayout=QHBoxLayout()
        hMainLayout.addLayout(vbox2)
        hMainLayout.addLayout(vbox1)
        hMainLayout.setContentsMargins(1,1,1,1)
        hMainLayout.setSpacing(1)
        hMainLayout.setStretch(10,1)
        
        self.setLayout(hMainLayout)
        self.setContentsMargins(1,1,1,1)
        #self.plotLine=pg.LineSegmentROI(positions=((self.dimx/2-100,self.dimy/2),(self.dimx/2+100,self.dimy/2)), movable=True,angle=0,pen='b')
        self.plotLine=pg.LineSegmentROI(positions=((0,200),(200,200)), movable=True,angle=0,pen='w')
        #self.plotLine=pg.PolyLineROI(positions=((0,200),(200,200),(300,200)), movable=True,angle=0,pen='w')
        self.plotRect=pg.RectROI([self.xc,self.yc],[4*self.rx,self.ry],pen='g')
        self.plotCercle=pg.CircleROI([self.xc,self.yc],[80,80],pen='g')
        
        #self.plotRect.addScaleRotateHandle([0.5, 1], [0.5, 0.5])
        
        
    def actionButton(self):
        
        self.openButton.clicked.connect(self.OpenF)
        self.saveButton.clicked.connect(self.SaveF)
        
        self.optionAutoSave.clicked.connect(lambda:self.open_widget(self.winOpt))
        self.checkBoxColor.stateChanged.connect(self.Color)
        self.checkBoxPlot.stateChanged.connect(self.PlotXY)
        self.ro1.sigRegionChangeFinished.connect(self.roiChanged)
        self.checkBoxZoom.valueChanged.connect(self.Zoom)
        #self.checkBoxZoom.stateChanged.connect(self.Zoom)
        self.energyBox.clicked.connect(self.Energ)
        self.checkBoxHist.stateChanged.connect(self.HIST)
        self.maxGraphBox.stateChanged.connect(self.Coupe)  
        self.ligneButton.clicked.connect(self.LIGNE)
        self.rectangleButton.clicked.connect(self.Rectangle)
        self.circleButton.clicked.connect(self.CERCLE)
        self.plotLine.sigRegionChangeFinished.connect(self.LigneChanged)
        self.plotRect.sigRegionChangeFinished.connect(self.RectChanged)
        self.plotCercle.sigRegionChangeFinished.connect(self.CercChanged)
        self.PlotButton.clicked.connect(self.CUT)
        self.MeasButton.clicked.connect(self.Measurement)
        

    def Energ(self):
        
        self.open_widget(self.winEncercled)
        self.winEncercled.Display(self.data)
        
    def LIGNE(self) : 
        
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
        
        self.cut=self.plotLine.getArrayRegion(self.data,self.imh)

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
        self.cut=(self.plotRect.getArrayRegion(self.data,self.imh))
        self.cut1=self.cut.mean(axis=1)
        
        
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
        
        self.cut=(self.plotCercle.getArrayRegion(self.data,self.imh))
        self.cut1=self.cut.mean(axis=1)
    
    def CUT(self): 
        
        if self.ite=='line':
            self.open_widget(self.winCoupe)
            self.winCoupe.PLOT(self.cut)
            
        if self.ite=='rect':
            self.open_widget(self.winCoupe)
            self.winCoupe.PLOT(self.cut1)
        
        
    def Measurement(self) :
        
        if self.ite=='rect':
            self.RectChanged()
            self.winM.setFile(self.nomFichier)
            self.open_widget(self.winM)
            self.winM.Display(self.cut)
            
        if self.ite=='cercle':
            self.CercChanged()
            self.winM.setFile(self.nomFichier)
            self.open_widget(self.winM)
            self.winM.Display(self.cut)
            
        if self.ite==None:
            self.winM.setFile(self.nomFichier)
            self.open_widget(self.winM)
            self.winM.Display(self.data)
    
    def shortcut(self):
        
        self.shortcutPu=QShortcut(QtGui.QKeySequence("+"),self)
        self.shortcutPu.activated.connect(self.paletteup)
        self.shortcutPu.setContext(Qt.ShortcutContext(3))
        #3: The shortcut is active when its parent widget, or any of its children has focus. default O The shortcut is active when its parent widget has focus.
        self.shortcutPd=QtGui.QShortcut(QtGui.QKeySequence("-"),self)
        self.shortcutPd.activated.connect(self.palettedown)
        self.shortcutPd.setContext(Qt.ShortcutContext(3))
        
        self.shortcutOpen=QtGui.QShortcut(QtGui.QKeySequence("Ctrl+o"),self)
        self.shortcutOpen.activated.connect(self.OpenF)
        self.shortcutOpen.setContext(Qt.ShortcutContext(3))
        
        #self.shortcutSave=QtGui.QShortcut(QtGui.QKeySequence("Ctrl+s"),self)
        #self.shortcutSave.activated.connect(self.SaveF)
        #self.shortcutSave.setContext(Qt.ShortcutContext(3))
        
        self.shortcutEnerg=QtGui.QShortcut(QtGui.QKeySequence("Ctrl+e"),self)
        self.shortcutEnerg.activated.connect(self.Energ)
        self.shortcutEnerg.setContext(Qt.ShortcutContext(3))
        
        self.shortcutMeas=QtGui.QShortcut(QtGui.QKeySequence('Ctrl+m'),self)
        self.shortcutMeas.activated.connect(self.Measurement)
        self.shortcutMeas.setContext(Qt.ShortcutContext(3))
        
        self.shortcutMeas=QtGui.QShortcut(QtGui.QKeySequence('Ctrl+k'),self)
        self.shortcutMeas.activated.connect(self.CUT)
        self.shortcutMeas.setContext(Qt.ShortcutContext(3))
        
        
        # mousse mvt
        self.proxy=pg.SignalProxy(self.p1.scene().sigMouseMoved, rateLimit=60, slot=self.mouseMoved)
        self.p1.scene().sigMouseClicked.connect(self.mouseClick)
        self.vb=self.p1.vb
           
        
    def Display(self,data):
        
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
                msg.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint)
                msg.exec_()
                
        if self.checkBoxBg.isChecked()==True and self.winOpt.dataBgExist==False:
                msg = QMessageBox()
                msg.setIcon(QMessageBox.Critical)
                msg.setText("Background not soustracred !")
                msg.setInformativeText("Background file not selected in options menu ")
                msg.setWindowTitle("Warning ...")
                msg.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint)
                msg.exec_()
            
            
        self.dimy=np.shape(self.data)[1]
        self.dimx=np.shape(self.data)[0]
        self.p1.setXRange(0,self.dimx)
        self.p1.setYRange(0,self.dimy)
        
        if self.filter=='gauss':
            self.data=gaussian_filter(self.data,self.sigma)
            print ('gauss filter')
            
        if self.filter=='median':
            self.data=median_filter(self.data,size=self.sigma)
            print ('median filter')
         
        if self.checkBoxScale.isChecked()==1: # autoscale on
            self.imh.setImage(self.data.astype(float),autoLevels=True,autoDownsample=True)
        else :
            self.imh.setImage(self.data.astype(float),autoLevels=False,autoDownsample=True)
        
        self.PlotXY() #graph update
                
        
        if self.winEncercled.isWinOpen==True:
            self.winEncercled.Display(self.data) ## energy update
        
        if self.winCoupe.isWinOpen==True:
            if self.ite=='line':
                self.LigneChanged()
                self.CUT()
            if self.ite=='rect':
                self.RectChanged()
                self.CUT()
            if self.ite=='cercle':
                self.CercChanged()
                
        if self.winM.isWinOpen==True: #  measurement update
            if self.ite=='rect':
                self.RectChanged()
                self.Measurement()
            if self.ite=='cercle':
                self.CercChanged()
                self.Measurement()
       
        if self.checkBoxAutoSave.isChecked()==True:
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
            if self.winOpt.checkBoxDate.isChecked()==True: # rajoute la date
                nomFichier=str(str(self.pathAutoSave)+'/'+self.fileNameSave+'_'+num+'_'+date)
            else :
                nomFichier=str(str(self.pathAutoSave)+'/'+self.fileNameSave+'_'+num)

            print( nomFichier, 'saved')
            np.savetxt(str(nomFichier)+'.txt',self.data)

            self.numTir+=1
            self.winOpt.setTirNumber(self.numTir)
            self.conf.setValue(self.name+"/tirNumber",self.numTir)
            self.fileName.setText(nomFichier)
    
        self.Zoom()
    
    def mouseClick(self): # block the cross if mousse button clicked
        if self.bloqq==1:
            self.debloquer()
        else :
            self.bloquer()
            
    def mouseMoved(self,evt):

        ## the cross mouve with the mousse mvt
        if self.bloqq==0: # souris non bloquer
            
            pos = evt[0]  ## using signal proxy turns original arguments into a tuple
            if self.p1.sceneBoundingRect().contains(pos):
                
                mousePoint = self.vb.mapSceneToView(pos)
                self.xMouse = (mousePoint.x())
                self.yMouse= (mousePoint.y())
                if ((self.xMouse>0 and self.xMouse<self.data.shape[0]-1) and (self.yMouse>0 and self.yMouse<self.data.shape[1]-1) ):
                        self.xc = self.xMouse
                        self.yc= self.yMouse  
                        self.vLine.setPos(self.xc)
                        self.hLine.setPos(self.yc) # the cross move only in the graph    
                        #self.ro1.setPos([self.xc-(self.rx/2),self.yc-(self.ry/2)])
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
        
        if self.maxGraphBox.isChecked()==True:
            dataF=gaussian_filter(self.data,5)
            (self.xc,self.yc)=pylab.unravel_index(dataF.argmax(),self.data.shape) #take the max ndimage.measurements.center_of_mass(dataF)#
            self.vLine.setPos(self.xc)
            self.hLine.setPos(self.yc)
            
        xxx=np.arange(0,int(self.dimx),1)#
        yyy=np.arange(0,int(self.dimy),1)#
        coupeX=self.data[int(self.xc),:]
        coupeXMax=np.max(coupeX)
        dataCross=self.data[int(self.xc),int(self.yc)] 
        self.label_Cross.setText('x='+ str(int(self.xc)) + ' y=' + str(int(self.yc)) + ' value=' + str(dataCross))
        
        if coupeXMax==0: # evite la div par zero
            coupeXMax=1
            
        coupeXnorm=(self.data.shape[0]/10)*(coupeX/coupeXMax) # normalize the curves
        self.curve2.setData(30+coupeXnorm,yyy,clear=True)
        
        coupeY=self.data[:,int(self.yc)]
        coupeYMax=np.max(coupeY)
        if coupeYMax==0:
            coupeYMax=1
            
        coupeYnorm=(self.data.shape[1]/10)*(coupeY/coupeYMax)
        self.curve3.setData(xxx,20+coupeYnorm,clear=True)
        
        ### print fwhm on the  X et Y curves if max  >20 counts
        xCXmax=np.amax(coupeXnorm) # max
        if xCXmax>20:
            fwhmX=self.fwhm(yyy, coupeXnorm, order=3)
            if fwhmX==None:
                self.textX.setText('')
            else:
                self.textX.setText('fwhm='+str(fwhmX))
            #yCXmax=yyy[coupeXnorm.argmax()]
            #self.textX.setPos(xCXmax-3,yCXmax+3)
        yCYmax=np.amax(coupeYnorm) # max
        if yCYmax>20:
            fwhmY=self.fwhm(xxx, coupeYnorm, order=3)
            #xCYmax=xxx[coupeYnorm.argmax()]
            if fwhmY==None:
                self.textY.setText('',color='w')
            else:
                self.textY.setText('fwhm='+str(fwhmY),color='w')
            #self.textY.setPos(xCYmax-3,yCYmax-3)   
    
 
    def PlotXY(self): # plot curves on the  graph
        
        if self.checkBoxPlot.isChecked()==1:
            
            self.p1.addItem(self.vLine, ignoreBounds=False)
            self.p1.addItem(self.hLine, ignoreBounds=False)
            self.p1.addItem(self.curve2)
            self.p1.addItem(self.curve3)
            self.p1.showAxis('left',show=True)
            self.p1.showAxis('bottom',show=True)
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
            
    def paletteup(self):
        
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
    
    def Color(self):
        """ image in colour
        """
        if self.checkBoxColor.isChecked()==1:
            self.hist.gradient.loadPreset('flame')
        else:
            self.hist.gradient.loadPreset('grey')
            
    def Zoom(self):
        
        """Zoom function
        """
        self.zo=self.checkBoxZoom.value()
        
        if self.checkBoxPlot.isChecked()==0:
            self.xc=self.dimx/2
            self.yc=self.dimy/2
        
       
        if self.zo<=0:
            self.p1.setXRange(0,self.dimx)
            self.p1.setYRange(0,self.dimy)
        
        else:
            xmin=self.xc-10*(101-self.zo)
            xmax=self.xc+10*(101-self.zo)
            ymin=self.yc-10*(101-self.zo)
            ymax=self.yc+10*(101-self.zo)
            
            if xmin<0:
                xmin=0
            if xmax>self.dimx:
                xmax=self.dimx   
                
            if ymin<0:
                ymin=0
            if ymax>self.dimy:
                ymax=self.dimy 
                
            self.p1.setXRange(xmin,xmax)
            self.p1.setYRange(ymin,ymax)
    
    
    def roiChanged(self):
        self.rx=self.ro1.size()[0]
        self.ry=self.ro1.size()[1]
        self.conf.setValue(self.name+"/rx",int(self.rx))
        self.conf.setValue(self.name+"/ry",int(self.ry))
      
        
    def bloquer(self): # block the cross
        
        self.bloqq=1
        self.conf.setValue(self.name+"/xc",int(self.xc)) # save cross postion in ini file
        self.conf.setValue(self.name+"/yc",int(self.yc))
         
    def debloquer(self): # unblock the cross
        self.bloqq=0
    
    def HIST(self):
        
        if self.checkBoxHist.isChecked()==1:
            self.winImage.addItem(self.hist)
        else:
            self.winImage.removeItem(self.hist)
    
    
    def Gauss(self):
        
        self.filter='gauss'
        sigma, ok=QInputDialog.getInt(self,'Gaussian Filter ','Enter sigma value (radius)')
        if ok:
            self.sigma=sigma
            self.filtreBox.setText('F: Gaussian')
            self.Display(self.data)
        
        
    def Median(self):
        
        self.filter='median'
        sigma, ok=QInputDialog.getInt(self,'Median Filter ','Enter sigma value (radius)')
        if ok:
            self.sigma=sigma
            self.filtreBox.setText('F: Median')
            self.Display(self.data)
        
        
    def Orig(self):
        """
        return data without filter
        """
        self.data=self.dataOrg
        self.filter='origin'
        self.Display(self.data)
        self.filtreBox.setText('Filters')
        print('original')
        
    def OpenF(self,fileOpen=None):

        if fileOpen==False:
            chemin=self.conf.value(self.name+"/path")
            fname=QtGui.QFileDialog.getOpenFileName(self,"Open File",chemin,"Images (*.txt *.spe *.TIFF *.sif *.tif);;Text File(*.txt);;Ropper File (*.SPE);;Andor File(*.sif);; TIFF file(*.TIFF)")
            fichier=fname[0]
        else:
            fichier=str(fileOpen)
            
        ext=os.path.splitext(fichier)[1]
        
        if ext=='.txt': # text file
            self.data=np.loadtxt(str(fichier))
        elif ext=='.spe' or ext=='.SPE': # SPE file
            dataSPE=SpeFile(fichier)
            data1=dataSPE.data[0]#.transpose() # first frame
            self.data=data1#np.flipud(data1)
        elif ext=='.TIFF' or ext=='.tif':# tiff File
            dat=Image.open(fichier)
            self.data=np.array(dat)
        elif ext=='.sif': 
            sifop=SifFile()
            im=sifop.openA(fichier)
            
            self.data=np.rot90(im,3)
#            self.data=self.data[250:495,:]
        else :
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Critical)
            msg.setText("Wrong file format !")
            msg.setInformativeText("The format of the file must be : .SPE  .TIFF .sif or .txt ")
            msg.setWindowTitle("Warning ...")
            msg.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint)
            msg.exec_()
            
        chemin=os.path.dirname(fichier)
        self.conf.setValue(self.name+"/path",chemin)
        self.conf.setValue(self.name+"/lastFichier",os.path.split(fichier)[1])
        self.fileName.setText(os.path.split(fichier)[1])
        self.nomFichier=os.path.split(fichier)[1]
        self.dataOrg=self.data
        self.Display(self.data)
    

    def SaveF (self):
        
        fname=QtGui.QFileDialog.getSaveFileName(self,"Save data as tiff ",self.path)
        self.path=os.path.dirname(str(fname[0]))
        fichier=fname[0]
        print(fichier,' is saved')
        self.conf.setValue(self.name+"/path",self.path)
        time.sleep(0.1)
#        img_PIL = PIL.Image.fromarray(self.data)
#        img_PIL.save(str(fname[0])+'.TIFF',format='TIFF') 
        np.savetxt(str(fichier)+'.txt',self.data)
        self.fileName.setText(fname[0]+'.TIFF') 

  
    def newDataReceived(self,data):
        self.data=data
        self.dataOrg=self.data
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
            fene.raise_()
            fene.showNormal()


    def closeEvent(self,event):
        
        if self.winEncercled.isWinOpen==True:
            self.winEncercled.close()
        if self.winCoupe.isWinOpen==True:
            self.winCoupe.close()
        if self.winM.isWinOpen==True:
            self.winM.close()
        if self.winOpt.isWinOpen==True:
            self.winOpt.close() 
            
        exit  









     
       
if __name__ == "__main__":
    appli = QApplication(sys.argv) 
    appli.setStyleSheet(qdarkstyle.load_stylesheet_pyqt5())
    e = WINFFT(name='VISU')  
    e.show()
    appli.exec_()    
        
        