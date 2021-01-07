#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Jan 30 15:07:27 2019

https://github.com/julienGautier77/visu.git

@author: juliengautier(LOA)
for dark style :
pip install qdarkstyle (https://github.com/ColinDuquesnoy/QDarkStyleSheet.git)
pip install pyqtgraph (https://github.com/pyqtgraph/pyqtgraph.git)

modified 2020/03/23 :add save tiff and save in graphCut, scale px to um
"""


__author__='julien Gautier'

from PyQt5.QtWidgets import QApplication,QVBoxLayout,QHBoxLayout,QWidget,QPushButton,QGridLayout
from PyQt5.QtWidgets import QSlider,QCheckBox,QLabel,QSizePolicy,QMessageBox
from PyQt5.QtWidgets import QShortcut
from pyqtgraph.Qt import QtCore,QtGui 
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon
import pylab
import sys,time,os
import pyqtgraph as pg # pip install pyqtgraph (https://github.com/pyqtgraph/pyqtgraph.git)
import numpy as np
import qdarkstyle # pip install qdarkstyle https://github.com/ColinDuquesnoy/QDarkStyleSheet  sur conda
from scipy.interpolate import splrep, sproot #
from scipy.ndimage.filters import gaussian_filter
from PIL import Image
from visu.winspec import SpeFile


from visu.winMeas import MEAS

from visu.andor import SifFile

import pathlib


__version__='2020.05'

__all__=['SEELIGHTTHREAD']

class SEELIGHTTHREAD(QWidget) :
    '''open and plot file : 
        SEE(file='nameFile,path=pathFileName,confpath,confMot)
        Make plot profile ands differents measurements(max,min mean...)
        Can open .spe .SPE .sif .TIFF files
        confpath :usefull if more than 2 SEE object used
        confMot usefull if RSAI motors is read
    '''
    
    newMesurment=QtCore.pyqtSignal(object)
    def __init__(self,parent=None,file=None,path=None,**kwds):
        
        print('LightThread')
        super(SEELIGHTTHREAD, self).__init__()
        self.setStyleSheet(qdarkstyle.load_stylesheet_pyqt5()) # dark style
        self.parent=parent
        version=__version__
        p = pathlib.Path(__file__)
        sepa=os.sep
        self.icon=str(p.parent) + sepa+'icons' +sepa
         ## kwds definition:
        if "confpath"in kwds :
            self.confpath=kwds["confpath"]
            self.conf=QtCore.QSettings(self.confpath, QtCore.QSettings.IniFormat)
        else:
            self.conf=QtCore.QSettings(str(p.parent / 'confVisu.ini'), QtCore.QSettings.IniFormat)
        if "name" in kwds:
            self.name=kwds["name"]
        else:
            self.name="VISU"
        
        if "meas" in kwds:
            self.meas=kwds["meas"]
        else:
           self.meas="on" 
        
        if "confMot" in kwds:
            print('motor accepted')
            if self.meas=="on":
                self.confMot=kwds["confoMot"]
                self.winM=MEAS(confMot=self.confMot,conf=self.conf,name=self.name)
        else :
            if self.meas=="on":
                self.winM=MEAS(self,conf=self.conf,name=self.name)
           
        
        if "aff" in kwds:
            self.aff=kwds["aff"]
        else:
            self.aff="left"
        
        
        if "saveTiff" in kwds:
            self.tiff=kwds["saveTiff"]
        else:       
            self.tiff=True
            
            
        self.nomFichier=''
        self.ite=None
        self.path=path
        self.setWindowTitle('Visualization'+'       v.'+ version)
        self.bloqKeyboard=bool((self.conf.value(self.name+"/bloqKeyboard"))  )  # block cross by keyboard
        self.bloqq=1 # block the cross by click on mouse
        self.setup()
        self.shortcut()
        self.actionButton()
        self.activateWindow()
        self.raise_()
        self.showNormal()
       
        self.setWindowIcon(QIcon(self.icon+'LOA.png'))
        
        def twoD_Gaussian(x,y, amplitude, xo, yo, sigma_x, sigma_y, theta, offset):
           xo = float(xo)
           yo = float(yo)    
           a = (np.cos(theta)**2)/(2*sigma_x**2) + (np.sin(theta)**2)/(2*sigma_y**2)
           b = -(np.sin(2*theta))/(4*sigma_x**2) + (np.sin(2*theta))/(4*sigma_y**2)
           c = (np.sin(theta)**2)/(2*sigma_x**2) + (np.cos(theta)**2)/(2*sigma_y**2)
           return offset + amplitude*np.exp( - (a*((x-xo)**2) + 2*b*(x-xo)*(y-yo) + c*((y-yo)**2)))

        
        if file==None:
            # to have a gaussian picture when we start
            self.dimy=960
            self.dimx=1240
            # Create x and y index
            self.x = np.arange(0,self.dimx)
            self.y = np.arange(0,self.dimy)
            self.y,self.x = np.meshgrid(self.y, self.x)
            
            self.data=twoD_Gaussian(self.x, self.y,450, 800, 600, 40, 40, 0, 10)+(50*np.random.rand(self.dimx,self.dimy)).round() 
        
            #self.data=(50*np.random.rand(self.dimx,self.dimy)).round() + 150
        else:
            if path==None:
                self.path=self.conf.value(self.name+"/path")
            
            self.data=self.OpenF(fileOpen=self.path+'/'+file)
        
        
        self.Display(self.data)
       
        
        
        
        
    def setup(self):
        # definition of all button 
        
        TogOff=self.icon+'Toggle_Off.png' 
        TogOn=self.icon+'Toggle_On.png'
        TogOff=pathlib.Path(TogOff)
        TogOff=pathlib.PurePosixPath(TogOff)
        TogOn=pathlib.Path(TogOn)
        TogOn=pathlib.PurePosixPath(TogOn)
        
        self.setStyleSheet("QCheckBox::indicator{width: 30px;height: 30px;}""QCheckBox::indicator:unchecked { image : url(%s);}""QCheckBox::indicator:checked { image:  url(%s);}""QCheckBox{font :10pt;}" % (TogOff,TogOn) )
        
        vbox1=QVBoxLayout() 
        self.hbox0=QHBoxLayout()
        vbox1.addLayout(self.hbox0)
                
        hbox1=QHBoxLayout()
        self.checkBoxPlot=QCheckBox('CROSS',self)
        self.checkBoxPlot.setChecked(False)
        self.label_CrossValue=QLabel()
        self.label_CrossValue.setStyleSheet("font:13pt")
        hbox1.addWidget(self.checkBoxPlot)
        hbox1.addWidget(self.label_CrossValue)
        
        hbox2=QHBoxLayout()
        self.label_Cross=QLabel()
        #self.label_Cross.setMaximumHeight(20)
        self.label_Cross.setMaximumWidth(170)
        self.label_Cross. setStyleSheet("font:12pt")
        hbox2.addWidget(self.label_Cross)
        
        vbox1.addLayout(hbox1)
        vbox1.addLayout(hbox2)
        
        self.ZoomLabel=QLabel('Zoom')
        vbox1.addWidget(self.ZoomLabel)
        self.checkBoxZoom=QSlider(Qt.Horizontal)
        self.checkBoxZoom.setMaximumWidth(250)
        self.checkBoxZoom.setMinimum(0)
        self.checkBoxZoom.setMaximum(200)
        self.checkBoxZoom.setValue(0)
        vbox1.addWidget(self.checkBoxZoom)
        
        self.checkBoxScale=QCheckBox('Auto Scale',self)
        self.checkBoxScale.setChecked(True)
        self.checkBoxScale.setMaximumWidth(100)
        
        self.checkBoxColor=QCheckBox('Color',self)
        self.checkBoxColor.setChecked(True)
    
        self.checkBoxHist=QCheckBox('Hist',self)
        self.checkBoxHist.setChecked(False)
        self.maxGraphBox=QCheckBox('Max',self)
        hbox3=QHBoxLayout()
        grid_layout = QGridLayout()
        grid_layout.setVerticalSpacing(0)
        grid_layout.setHorizontalSpacing(10)
        grid_layout.addWidget(self.checkBoxScale, 0, 0)
        grid_layout.addWidget(self.checkBoxColor,1,0)
        grid_layout.addWidget(self.checkBoxHist, 0, 1)
        #grid_layout.addWidget(self.checkBoxZoom, 1, 0)
        grid_layout.addWidget(self.maxGraphBox, 1,1)
        
        hbox3.addLayout(grid_layout)
        
        vbox1.addLayout(hbox3)
        
        hbox4=QHBoxLayout()
        
        if self.meas=='on':
            self.MeasButton=QPushButton('Meas.')
            hbox4.addWidget(self.MeasButton)
        
        
        vbox1.addLayout(hbox4)
        
        vbox1.addStretch(1)
        
        self.winImage = pg.GraphicsLayoutWidget()
        #self.winImage.setContentsMargins(1,1,1,1)
        self.winImage.setAspectLocked(True)
        self.winImage.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        #self.winImage.ci.setContentsMargins(1,1,1,1)
        
        vbox2=QVBoxLayout()
        # self.dockImage=QDockWidget(self)
        
        # self.dockImage.setWidget(self.winImage)
        # self.dockImage.setFeatures(QDockWidget.DockWidgetFloatable)
        #vbox2.addWidget(self.dockImage)
        vbox2.addWidget(self.winImage)
        vbox2.setContentsMargins(0,0,0,0)
        
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
        self.p1.showAxis('left',show=True)
        self.p1.showAxis('bottom',show=True)
        
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
        if self.aff=='right':
            hMainLayout.addLayout(vbox2)
            hMainLayout.addLayout(vbox1)
        else :
            hMainLayout.addLayout(vbox1)
            hMainLayout.addLayout(vbox2)
            
        hMainLayout.setContentsMargins(1,1,1,1)
        hMainLayout.setSpacing(1)
        hMainLayout.setStretch(10,1)
        
        self.setLayout(hMainLayout)
        self.setContentsMargins(1,1,1,1)
        
        
    def actionButton(self):
        # action of button
        
        
        self.checkBoxColor.stateChanged.connect(self.Color)
        self.checkBoxPlot.stateChanged.connect(self.PlotXY)
        self.ro1.sigRegionChangeFinished.connect(self.roiChanged)
        self.checkBoxZoom.valueChanged.connect(self.Zoom)
        #self.checkBoxZoom.stateChanged.connect(self.Zoom)
       
        self.checkBoxHist.stateChanged.connect(self.HIST)
        self.maxGraphBox.stateChanged.connect(self.Coupe)  
        if self.meas=='on':
            self.MeasButton.clicked.connect(self.Measurement,QtCore.Qt.DirectConnection) # send data to widget measurement
        
        if self.parent is not None : # reveceive data display it
            self.parent.dataSignal.connect(self.Display)#,QtCore.Qt.DirectConnection)  
        
        
    def shortcut(self):
        # keyboard shortcut
        
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
        
        self.shortcutSave=QtGui.QShortcut(QtGui.QKeySequence("Ctrl+s"),self)
        self.shortcutSave.activated.connect(self.SaveF)
        self.shortcutSave.setContext(Qt.ShortcutContext(3))
        
        
        if self.meas=='on':
            self.shortcutMeas=QtGui.QShortcut(QtGui.QKeySequence('Ctrl+m'),self)
            self.shortcutMeas.activated.connect(self.Measurement)
            self.shortcutMeas.setContext(Qt.ShortcutContext(3))
        
        
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
        
        # if self.ite=='line':
        #     self.LigneChanged()
        #     self.winM.setFile(self.nomFichier)
        #     self.open_widget(self.winM)
        #     self.winM.Display(self.cut)
        if self.meas=="on":
            if self.ite==None:
                self.winM.setFile(self.nomFichier)
                self.open_widget(self.winM)
                self.winM.Display(self.data)
    

        
        
    def Display(self,data):
        #  display the data and refresh all the calculated things and plots
        self.data=data
        self.dimy=np.shape(self.data)[1]
        self.dimx=np.shape(self.data)[0]
        self.p1.setXRange(0,self.dimx)
        self.p1.setYRange(0,self.dimy)
        self.p1.setAspectLocked(True,ratio=1)
        
            
        
        if self.checkBoxScale.isChecked()==1: # autoscale on
           self.imh.setImage(self.data.astype(float),autoLevels=True,autoDownsample=True)
        else :
            self.imh.setImage(self.data.astype(float),autoLevels=False,autoDownsample=True)
        
         

        if self.meas=="on" :       
            
            if self.winM.isWinOpen==True:
                self.newMesurment.emit(self.data)#  measurement update
                
                
                #self.Measurement()
                
        
        
    
        self.Zoom() # update zoom
    
    def mouseClick(self): # block the cross if mousse button clicked
        
        if self.bloqq==1:
            self.bloqq=0
            
        else :
            self.bloqq=1
            self.conf.setValue(self.name+"/xc",int(self.xc)) # save cross postion in ini file
            self.conf.setValue(self.name+"/yc",int(self.yc))
            
            
    def mouseMoved(self,evt):

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
        # make  plot profile on cross
        
        
        if self.maxGraphBox.isChecked()==True and self.bloqKeyboard==False: # find and fix the cross on the maximum of the image
            
            dataF=gaussian_filter(self.data,5)
            (self.xc,self.yc)=pylab.unravel_index(dataF.argmax(),self.data.shape) #take the max ndimage.measurements.center_of_mass(dataF)#
            self.vLine.setPos(self.xc)
            self.hLine.setPos(self.yc)
        
            
        dataCross=self.data[int(self.xc),int(self.yc)] 
        coupeX=self.data[int(self.xc),:]
        coupeY=self.data[:,int(self.yc)]
        xxx=np.arange(0,int(self.dimx),1)#
        yyy=np.arange(0,int(self.dimy),1)#
        coupeXMax=np.max(coupeX)
        coupeYMax=np.max(coupeY)
        
        
        if coupeXMax==0: # avoid zero
            coupeXMax=1
        
        if coupeYMax==0:
            coupeYMax=1
            
        
        self.label_Cross.setText('x='+ str(int(self.xc)) + ' y=' + str(int(self.yc)) )
            
        dataCross=round(dataCross,3) # take data  value  on the cross
        self.label_CrossValue.setText(' v.=' + str(dataCross))
        
        
        coupeXnorm=(self.data.shape[0]/10)*(coupeX/coupeXMax) # normalize the curves
        self.curve2.setData(20+self.xminR+coupeXnorm,yyy,clear=True)

          
        coupeYnorm=(self.data.shape[1]/10)*(coupeY/coupeYMax)
        self.curve3.setData(xxx,20+self.yminR+coupeYnorm,clear=True)
        
    
 
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
            self.p1.removeItem(self.textX)
            self.p1.removeItem(self.textY)
            
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
    
    def Color(self):
        """ image in colour/n&b
        """
        if self.checkBoxColor.isChecked()==1:
            self.hist.gradient.loadPreset('flame')
        else:
            self.hist.gradient.loadPreset('grey')
            
    def Zoom(self):
        
        """Zoom function
        """
        self.zo=self.checkBoxZoom.value()
        
        # if self.checkBoxPlot.isChecked()==0:
        #     self.xc=self.dimx/2
        #     self.yc=self.dimy/2
        
       
        if self.zo<=2:
            self.zo=0
            self.p1.setXRange(0,self.dimx)
            self.p1.setYRange(0,self.dimy)
            self.xminR=0
            self.yminR=0
            self.xmaxR=self.dimx
            self.ymaxR=self.dimy
        
        else:
            
            self.xminR=self.xc-(self.dimx-self.xc)*(1-self.zo/200)
            self.xmaxR=self.xc+(self.dimx-self.xc)*(1-self.zo/200)
            
            
            self.yminR=self.yc-(self.dimy-self.yc)*(1-self.zo/200)
            self.ymaxR=self.yc+(self.dimy-self.yc)*(1-self.zo/200)
            
        
            if self.xminR<0:
                self.xminR=0
            if self.xmaxR>self.dimx:
                self.xmaxR=self.dimx   
                
            if self.yminR<0:
                self.yminR=0
            if self.ymaxR>self.dimy:
                self.ymaxR=self.dimy 
            
            
            self.p1.setXRange(self.xminR,self.xmaxR)
            self.p1.setYRange(self.yminR,self.ymaxR)
            
        self.Coupe()
            
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
        
    def debloquer(self): # unblock the cross
        
        self.bloqKeyboard=bool(False)
        self.vLine.setPen('y')
        self.hLine.setPen('y')
        self.conf.setValue(self.name+"/bloqKeyboard",bool(self.bloqKeyboard))
        
        
        
    def HIST(self):
        #show histogramm
        if self.checkBoxHist.isChecked()==1:
            self.winImage.addItem(self.hist)
        else:
            self.winImage.removeItem(self.hist)
    
        
    def OpenF(self,fileOpen=False):
        #open file in txt spe TIFF sif  format
        fileOpen=fileOpen
        print(fileOpen)
        print('open')
        if fileOpen==False:
            print('ici')
            chemin=self.conf.value(self.name+"/path")
            fname=QtGui.QFileDialog.getOpenFileName(self,"Open File",chemin,"Images (*.txt *.spe *.TIFF *.sif *.tif);;Text File(*.txt);;Ropper File (*.SPE);;Andor File(*.sif);; TIFF file(*.TIFF)")
            fichier=fname[0]
        else:
            fichier=str(fileOpen)
            
        ext=os.path.splitext(fichier)[1]
        
        if ext=='.txt': # text file
            data=np.loadtxt(str(fichier))
        elif ext=='.spe' or ext=='.SPE': # SPE file
            dataSPE=SpeFile(fichier)
            data1=dataSPE.data[0]#.transpose() # first frame
            data=data1#np.flipud(data1)
        elif ext=='.TIFF' or ext=='.tif':# tiff File
            dat=Image.open(fichier)
            data=np.array(dat)
        elif ext=='.sif': 
            sifop=SifFile()
            im=sifop.openA(fichier)
            data=np.rot90(im,3)
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
    
        self.newDataReceived(data)
    

    def SaveF (self):
        # save data  in TIFF 
        
        if self.tiff==True: 
            fname=QtGui.QFileDialog.getSaveFileName(self,"Save data as TIFF",self.path)
            self.path=os.path.dirname(str(fname[0]))
            fichier=fname[0]
        
            ext=os.path.splitext(fichier)[1]
            #print(ext)
            print(fichier,' is saved')
            self.conf.setValue(self.name+"/path",self.path)
            time.sleep(0.1)
            img_PIL = Image.fromarray(self.data)

            img_PIL.save(str(fname[0])+'.TIFF',format='TIFF')
            
            
        else :
            fname=QtGui.QFileDialog.getSaveFileName(self,"Save data as txt",self.path)
            self.path=os.path.dirname(str(fname[0]))
            fichier=fname[0]
        
            ext=os.path.splitext(fichier)[1]
            #print(ext)
            print(fichier,' is saved')
            self.conf.setValue(self.name+"/path",self.path)
            time.sleep(0.1)
            np.savetxt(str(fichier)+'.txt',self.data)
            

  
    def newDataReceived(self,data):
        # Do display and save origin data when new data is  sent to  visu
        self.data=data
        self.dimy=np.shape(self.data)[1]
        self.dimx=np.shape(self.data)[0]
        #self.Display(self.data)
        self.dataSignal.emit(self.data)
       
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
        # when the window is closed
       
        if self.winM.isWinOpen==True:
            self.winM.close()
        
        

   
if __name__ == "__main__":
    
    appli = QApplication(sys.argv) 
    appli.setStyleSheet(qdarkstyle.load_stylesheet_pyqt5())
    e = SEELIGHT()#confpath='C:/Users/LOA/Desktop/python/Camera/confCamera.ini',name='camDefault')
    e.show()
    appli.exec_() 