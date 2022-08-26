#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Dec 19 11:43:05 2018
@author: juliengautier

"""

from PyQt6.QtWidgets import QApplication,QVBoxLayout,QHBoxLayout,QWidget,QGridLayout
from PyQt6.QtWidgets import QCheckBox,QLabel,QSizePolicy,QSpinBox,QSizePolicy
from PyQt6 import QtCore,QtGui 
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QShortcut
from PyQt6.QtGui import QIcon
import sys,time
import pyqtgraph as pg # pyqtgraph biblio permettent l'affichage 
import numpy as np
import qdarkstyle # pip install qdakstyle https://github.com/ColinDuquesnoy/QDarkStyleSheet  sur conda
import pylab,os
from scipy.ndimage.filters import gaussian_filter # pour la reduction du bruit
from scipy.interpolate import splrep, sproot # pour calcul fwhm et fit 
import pathlib

class WINENCERCLED(QWidget):
    
    def __init__(self,parent=None,conf=None,name='VISU'):
        
        super().__init__()
        self.name=name
        self.parent=parent
        p = pathlib.Path(__file__)
        if conf==None:
            self.conf=QtCore.QSettings(str(p.parent / 'confVisu.ini'), QtCore.QSettings.Format.IniFormat)
        else :
            self.conf=conf
        
        sepa=os.sep
        self.icon=str(p.parent) + sepa+'icons' +sepa

        self.isWinOpen=False
        self.setWindowTitle('Encercled')
        self.setWindowIcon(QIcon(self.icon+'LOA.png'))
        self.setStyleSheet(qdarkstyle.load_stylesheet(qt_api='pyqt6'))
        self.left=100
        self.top=30
        self.width=800
        self.height=800
        self.setGeometry(self.left,self.top,self.width,self.height)
        self.dimx=1200
        self.dimy=900
        self.bloqq=1
        self.xec=int(self.conf.value(self.name+"/xec"))
        self.yec=int(self.conf.value(self.name+"/yec"))
        self.r1x=int(self.conf.value(self.name+"/r1x"))
        self.r1y=int(self.conf.value(self.name+"/r1y"))
        self.r2=int(self.conf.value(self.name+"/r2x"))
        self.r2=int(self.conf.value(self.name+"/r2y"))
        
        self.kE=0 # variable pour la courbe E fct du nb shoot
        
        self.Xec=[]
        self.Yec=[]
        self.fwhmX=100
        self.fwhmY=100
        self.setWindowIcon(QIcon('./icons/LOA.png'))
        self.E = []
        
        #self.E=np.array([2,3,5])
        self.Xec=[]
        self.Yec=[]
        
        # Create x and y indices
        x = np.arange(0,self.dimx)
        y = np.arange(0,self.dimy)
        y,x = np.meshgrid(y, x)
    
        self.data=(40*np.random.rand(self.dimx,self.dimy)).round()
        
        self.setup()
        self.ActionButton()
        self.Display(self.data)
        
    def setup(self):
        
        TogOff=self.icon+'Toggle_Off.png'
        TogOn=self.icon+'Toggle_On.png'
        
        
        TogOff=pathlib.Path(TogOff)
        TogOff=pathlib.PurePosixPath(TogOff)
        TogOn=pathlib.Path(TogOn)
        TogOn=pathlib.PurePosixPath(TogOn)
        self.setStyleSheet("QCheckBox::indicator{width: 30px;height: 30px;}""QCheckBox::indicator:unchecked { image : url(%s);}""QCheckBox::indicator:checked { image:  url(%s);}""QCheckBox{font :10pt;}" % (TogOff,TogOn) )
        
        vbox1=QVBoxLayout()
        hbox=QHBoxLayout()
        self.checkBoxAuto=QCheckBox('Auto',self)
        self.checkBoxAuto.setChecked(True)
        hbox.addWidget(self.checkBoxAuto)
        self.bckButton=QCheckBox('Soustract Bg',self)
        hbox.addWidget(self.bckButton)
        vbox1.addLayout(hbox)
        hbox0=QHBoxLayout()
        self.energieRes=QLabel('?')
        self.energieRes.setMaximumHeight(30)
        self.energieRes.setMaximumWidth(140)
        self.energieRes.setStyleSheet("color:blue;font:20pt")
        self.lEnergie=QLabel('s(E1)/s(E2) :')
        self.lEnergie.setStyleSheet("color:blue;font:18pt")
        self.lEnergie.setMaximumWidth(160)
        hbox0.addWidget(self.lEnergie)
        hbox0.addWidget(self.energieRes)
        #vbox1.addStretch(1)
        vbox1.addLayout(hbox0)
        
        
        LabelR1x=QLabel("fwhm X/0.85")
        LabelR1x.setStyleSheet("color:red;font:14pt")
        self.r1xBox=QSpinBox()
        #self.r1Box.setMaximumWidth(60)
        self.r1xBox.setMaximum(2000)
        LabelR1y=QLabel('fwhm Y/0.85')
        LabelR1y.setStyleSheet("color:green;font:14pt")
        self.r1yBox=QSpinBox()
        self.r1yBox.setMaximum(2000)
        #self.r2Box.setMaximumWidth(60)
        LabelR2=QLabel('R2')
        LabelR2.setStyleSheet("color:yellow;font:14pt")
        self.r2Box=QSpinBox()
        self.r2Box.setMaximum(2000)
        
        LabelE1=QLabel("E1 Sum ")
        LabelE1.setStyleSheet("color:red;font:14pt")
        self.LabelE1Sum=QLabel("? ")
        self.LabelE1Sum.setStyleSheet("color:red;font:14pt")
        LabelE1M=QLabel("E1 mean ")
        LabelE1M.setStyleSheet("color:red;font:14pt")
        self.LabelE1Mean=QLabel("? ")
        self.LabelE1Mean.setStyleSheet("color:red;font:14pt")
        
        
        LabelE2=QLabel("E2 Sum ")
        LabelE2.setStyleSheet("color:yellow;font:14pt")
        self.LabelE2Sum=QLabel("? ")
        self.LabelE2Sum.setStyleSheet("color:yellow;font:14pt")
        LabelE2M=QLabel("E2 mean ")
        LabelE2M.setStyleSheet("color:yellow ;font:14pt")
        self.LabelE2Mean=QLabel("? ")
        self.LabelE2Mean.setStyleSheet("color:yellow;font:14pt")
        
        grid_layout1 = QGridLayout()
        grid_layout1.addWidget(LabelR1x, 0, 0)
        grid_layout1.addWidget(self.r1xBox, 0, 1)
        grid_layout1.addWidget(LabelR1y, 1, 0)
        grid_layout1.addWidget(self.r1yBox, 1,1)
        grid_layout1.addWidget(LabelR2, 2, 0)
        grid_layout1.addWidget(self.r2Box, 2,1)
        grid_layout1.addWidget(LabelE1,3,0)
        grid_layout1.addWidget(self.LabelE1Sum,3,1)
        grid_layout1.addWidget(LabelE1M,4,0)
        grid_layout1.addWidget(self.LabelE1Mean,4,1)
        
        grid_layout1.addWidget(LabelE2,5,0)
        grid_layout1.addWidget(self.LabelE2Sum,5,1)
        grid_layout1.addWidget(LabelE2M,6,0)
        grid_layout1.addWidget(self.LabelE2Mean,6,1)
        
        
        vbox1.addLayout(grid_layout1)
        
        vbox1.addStretch(1)
        
        self.winImage = pg.GraphicsLayoutWidget()
        self.winImage.setContentsMargins(0,0,0,0)
        self.winImage.setAspectLocked(True)
        self.winImage.setSizePolicy(QSizePolicy.Policy.MinimumExpanding, QSizePolicy.Policy.MinimumExpanding)
        #self.winImage.ci.setContentsMargins(0,0,0,0)
        
        vbox2=QVBoxLayout()
        hbox2=QHBoxLayout()
        
        
        hbox2.addWidget(self.winImage)
        vbox2.addLayout(hbox2)
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
        self.vLine = pg.InfiniteLine(angle=90, movable=False,pen='w')
        self.hLine = pg.InfiniteLine(angle=0, movable=False,pen='w')
        self.p1.addItem(self.vLine)
        self.p1.addItem(self.hLine)
        
        self.vLine.setPos(self.xec)
        self.hLine.setPos(self.yec)
        
        self.roi1=pg.CircleROI([self.xec,self.yec],[2*self.r1x,2*self.r1y],pen='r',movable=False)
        self.roi1.setPos([self.xec-(self.r1x),self.yec-(self.r1y)])
        self.p1.addItem(self.roi1)
       
        self.roi2=pg.CircleROI([self.xec,self.yec],[2*self.r2,2*self.r2],pen='y',movable=False)
        self.roi2.setPos([self.xec-(self.r2),self.yec-(self.r2)])
        self.p1.addItem(self.roi2)
        
        #histogramme
        self.hist = pg.HistogramLUTItem() 
        self.hist.setImageItem(self.imh)
        self.hist.autoHistogramRange()
        self.hist.gradient.loadPreset('flame')
        
        self.curve2=pg.PlotCurveItem()
        self.curve3=pg.PlotCurveItem()
        # text pour afficher fwhm sur p1
        self.textX = pg.TextItem(angle=-90) 
        self.textY = pg.TextItem()
        self.p1.addItem(self.curve2)
        self.p1.addItem(self.curve3)
        self.p1.addItem(self.textX)
        self.p1.addItem(self.textY)
        
        
        self.ROIRect=pg.RectROI([self.xec,self.yec],[4*self.r1x,4*self.r1y],pen='m',)
        
        hLayout1=QHBoxLayout()
        
        hLayout1.addLayout(vbox2)
        hLayout1.addLayout(vbox1)
        
        
        hLayout1.setContentsMargins(1,1,1,1)
#        hLayout1.setSpacing(1)
#        hLayout1.setStretch(10,1)
        
        vMainLayout=QVBoxLayout()
        vMainLayout.addLayout(hLayout1)
        
        
        
        
        
        hMainLayout=QHBoxLayout()
        hMainLayout.addLayout(vMainLayout)
        self.setLayout(hMainLayout)
        self.setContentsMargins(1,1,1,1)
        
        
        
    def ActionButton(self):   
        # Blocage de la souris
        self.roi1.sigRegionChangeFinished.connect(self.energSouris) # signal si changement à la souris de la taille des cercles
        self.roi2.sigRegionChangeFinished.connect(self.energSouris)
#
        self.r1xBox.editingFinished.connect(self.Rayon) #w.r1Box.returnPressed.connect(Rayon)# rayon change a la main
        self.r1yBox.editingFinished.connect(self.Rayon)
        self.r2Box.editingFinished.connect(self.Rayon)
       
        self.shortcutb=QtGui.QShortcut(QtGui.QKeySequence("Ctrl+b"),self)
        self.shortcutb.activated.connect(self.bloquer)
        self.shortcutd=QtGui.QShortcut(QtGui.QKeySequence("Ctrl+d"),self)
        self.shortcutd.activated.connect(self.debloquer)
         
        self.shortcutPu=QShortcut(QtGui.QKeySequence("+"),self)
        self.shortcutPu.activated.connect(self.paletteup)
        self.shortcutPu.setContext(Qt.ShortcutContext(3))
        #3: The shortcut is active when its parent widget, or any of its children has focus. default O The shortcut is active when its parent widget has focus.
        self.shortcutPd=QtGui.QShortcut(QtGui.QKeySequence("-"),self)
        self.shortcutPd.activated.connect(self.palettedown)
        self.shortcutPd.setContext(Qt.ShortcutContext(3))
        
        self.checkBoxAuto.stateChanged.connect(lambda:self.Display(self.data))
        # mvt de la souris
        self.proxy=pg.SignalProxy(self.p1.scene().sigMouseMoved, rateLimit=60, slot=self.mouseMoved)
        self.p1.scene().sigMouseClicked.connect(self.mouseClick)
        
        self.vb=self.p1.vb
        
        self.checkBoxAuto.stateChanged.connect(self.AutoE)
        self.bckButton.stateChanged.connect(self.Back)
        self.ROIRect.sigRegionChangeFinished.connect(self.roiBackChanged)
        
        
        if self.parent is not None:
            self.parent.signalEng.connect(self.Display)
        
    def mouseClick(self):
        # bloque ou debloque la souris si click su le graph
        
        if self.bloqq==1:
            self.debloquer()
        else :
            self.bloquer()  
            
    def bloquer(self): # bloque la croix 
        self.bloqq=1
        self.conf.setValue(self.name+"/xec",int(self.xec)) # save cross postion in ini file
        self.conf.setValue(self.name+"/yec",int(self.yec))
        self.CalculE()
        
    def debloquer(self): # deblaoque la croix : elle bouge avec la souris
        self.bloqq=0
    
    # mvt de la souris
    
    def mouseMoved(self,evt):
        ## pour que la cross suive le mvt de la souris
        if self.checkBoxAuto.isChecked()==False:

            if self.bloqq==0: # souris non bloquer
                pos = evt[0]  ## using signal proxy turns original arguments into a tuple
                if self.p1.sceneBoundingRect().contains(pos):
                    mousePoint = self.vb.mapSceneToView(pos)
                    self.xec =int (mousePoint.x())
                    self.yec= int(mousePoint.y())
                    if ((self.xec>0 and self.xec<self.data.shape[0]) and (self.yec>0 and self.yec<self.data.shape[1]) ):
                            self.vLine.setPos(self.xec)
                            self.hLine.setPos(self.yec) # la croix ne bouge que dans le graph  
                            
                            self.roi1.setPos([self.xec-(self.r1x),self.yec-(self.r1y)])
                            self.roi2.setPos([self.xec-(self.r2),self.yec-(self.r2)])
                            
    
    def AutoE(self):
        if self.checkBoxAuto.isChecked()==False:
            self.energSouris()
            self.roi1.setSize([2*self.r1x,2*self.r1y])
            self.roi2.setSize([2*self.r2,2*self.r2])
            
            
    def energSouris(self): # changement des rayons à la souris 
        if self.checkBoxAuto.isChecked()==False:
            s1=self.roi1.size()
            s2=self.roi2.size()
            self.r1xBox.setValue((int(s1[0]/2)))
            self.r1yBox.setValue((int(s1[1]/2)))
            self.r2Box.setValue((int(s2[0]/2)))
            self.r1x=int(s1[0]/2)
            self.r1y=int(s1[1]/2)
            self.r2=int(s2[0]/2)
            if self.bloqq==1:
                self.CalculE()
     
        
    def Rayon(self): 
        """changement rayon dans les box
        """
        if self.checkBoxAuto.isChecked()==False:
            if self.r1xBox.hasFocus() :
                self.r1x=(float(self.r1xBox.text()))
                self.roi1.setSize([2*self.r1x,2*self.r1y])
            if self.r1yBox.hasFocus() :
                self.r1y=(float(self.r1yBox.text()))
                self.roi1.setSize([2*self.r1x,2*self.r1y])
            
            if self.r2Box.hasFocus():
                self.r2=(float(self.r2Box.text()))
                self.roi2.setSize([2*self.r2,2*self.r2])
            
            self.roi1.setPos([self.xec-(self.r1x),self.yec-(self.r1y)])
            self.roi2.setPos([self.xec-(self.r2),self.yec-(self.r2)])
            if self.bloqq==1:
                self.CalculE()
    
    
    def CalculE(self):
        
        if self.fwhmX==None or self.fwhmY==None:
            self.fwhmX=100
            self.fwhmY=100
        
        if self.checkBoxAuto.isChecked()==True:
            self.r1x=self.fwhmX/0.849
            self.r1y=self.fwhmY/0.849
            self.r1xBox.setValue(int(self.r1x))
            self.r1yBox.setValue(int(self.r1y))
            nbG=2 # ré= 2 fois r1 pour le grand cercle
            self.roi2.setSize([2*nbG*self.r1x,2*nbG*self.r1y])
            self.roi2.setPos([self.xec-nbG*self.r1x,self.yec-nbG*self.r1y])
            self.r2Box.setValue(int(2*nbG*self.r1x))
            self.roi1.setSize([2*self.r1x,2*self.r1y])
            self.roi1.setPos([self.xec-self.r1x,self.yec-self.r1y])
            
        else:
            self.r1x=self.r1x
            self.r1y=self.r1y
           
        E1=self.roi1.getArrayRegion(self.data,self.imh).sum()
        E2=self.roi2.getArrayRegion(self.data,self.imh).sum()
        self.rap=100*E1/E2
        self.energieRes.setText('%.2f %%' % self.rap)
        # self.E=np.append(self.E,self.rap)
        # #self.E.append(self.rap)
        # Emean=np.mean(self.E)
        # self.meanAff.setText('%.2f' % Emean)
        # EPV=np.std(self.E)
        # self.PVAff.setText('%.2f' % EPV)
        # self.hLineMeanE.setPos(Emean)
        self.textX.setText('fwhm='+str(self.fwhmY))
        self.textY.setText('fwhm='+str(self.fwhmX),color='w')
        self.LabelE1Sum.setText('%.2f' %E1)
        self.LabelE1Mean.setText('%.2f' % (self.roi1.getArrayRegion(self.data,self.imh).mean()))
        self.LabelE2Sum.setText('%.2f' %E2)
        self.LabelE2Mean.setText('%.2f' % (self.roi2.getArrayRegion(self.data,self.imh).mean()))
        
    def Display(self,data):
        self.dataOrg=data
        self.data=data
        
        self.dimx=self.data.shape[0]
        self.dimy=self.data.shape[1]
        self.p1.setXRange(0,self.dimx)
        self.p1.setYRange(0,self.dimy)
        self.p1.setAspectLocked(True,ratio=1)
        self.imh.setImage(data.astype(float),autoLevels=True,autoDownsample=True)
        self.CalculCentroid()
        self.Coupe()
        self.Back()
        # self.CalculE() 
        
    #     self.Xec.append(self.xec)
    #     self.Yec.append(self.yec)
        
    #     Xmean=np.mean(self.Xec)
    #     self.meanXAff.setText('%.2f' % Xmean)
    #     XPV=np.std(self.Xec)
    #     self.stdXAff.setText('%.2f' % XPV)
    #     self.hLineMeanX.setPos(Xmean)
    #     Ymean=np.mean(self.Yec)
    #     self.meanYAff.setText('%.2f' % Ymean)
    #     YPV=np.std(self.Yec)
    #     self.stdYAff.setText('%.2f' % YPV)
    #     self.hLineMeanY.setPos(Ymean)
    #     self.plotGraph()
       
        
    
    # def plotGraph(self):
        
        
        
    #     self.p2.setData(self.E)#,pen='b',symbol='t',symboleSize=2,clear=True,symbolPen='b',symbolBrush='b',name="rapport")
    #     #self.p2.addItem(self.hLineMeanE, ignoreBounds=True)
    #     self.p3.setData(self.Xec)#,pen='r',symbol='t',symboleSize=2,clear=True,symbolPen='r',symbolBrush='r',name="x")
    #     #self.p3.addItem(self.hLineMeanX, ignoreBounds=True)
    #     self.p4.setData(self.Yec)#,pen='g',symbol='t',symboleSize=2,clear=True,symbolPen='g',symbolBrush='g',name="y")
    #     #self.p4.addItem(self.hLineMeanY, ignoreBounds=True)
    
    
    
    def CalculCentroid(self):
        
        if self.checkBoxAuto.isChecked()==True:
            dataF=gaussian_filter(self.data,5)
            (self.xec,self.yec)=pylab.unravel_index(dataF.argmax(),self.data.shape) #prend le max 
            self.vLine.setPos(self.xec)
            self.hLine.setPos(self.yec)       
            self.roi1.setPos([self.xec-(self.r1x),self.yec-(self.r1y)])
            self.roi2.setPos([self.xec-(self.r2),self.yec-(self.r2)])
        
        
    def fwhm(self,x, y, order=3):
        
        """
            Determine full-with-half-maximum of a peaked set of points, x and y.
            Assumes that there is only one peak present in the datasset.  The function
            uses a spline interpolation of order k.
        """
        y=gaussian_filter(y,5) # filtre pour reduire le bruit
        half_max = np.amax(y)/2
        try:
            s = splrep(x, y - half_max,k=order) # Find the B-spline representation of 1-D curve.
            roots = sproot(s) # Given the knots (>=8) and coefficients of a cubic B-spline return the roots of the spline.
        except:
           roots=0
           
        if len(roots) > 2:
            pass
            #print( "The dataset appears to have multiple peaks, and ","thus the FWHM can't be determined.")
        elif len(roots) < 2:
            pass
           # print( "No proper peaks were found in the data set; likely ","the dataset is flat (e.g. all zeros).")
        else:
            return np.around(abs(roots[1] - roots[0]),decimals=2)
         
    def Coupe(self):
        
        xxx=np.arange(0,int(self.dimx),1)#
        yyy=np.arange(0,int(self.dimy),1)#
        coupeX=self.data[int(self.xec),:]
        coupeXMax=np.max(coupeX)
        
        if coupeXMax==0: # evite la div par zero
            coupeXMax=1
            
        coupeXnorm=(self.data.shape[0]/10)*(coupeX/coupeXMax) # normalise les coupes pour pas prendre tout l ecran
        self.curve2.setData(30+coupeXnorm,yyy,clear=True)
        
        coupeY=self.data[:,int(self.yec)]
        coupeYMax=np.max(coupeY)
        if coupeYMax==0:
            coupeYMax=1
            
        coupeYnorm=(self.data.shape[1]/10)*(coupeY/coupeYMax)
        self.curve3.setData(xxx,20+coupeYnorm,clear=True)
        
        ### affichage de fwhm sur les coupes X et Y que si le max est >20 counts
        xCXmax=np.amax(coupeXnorm) # max
        if xCXmax>20:
            self.fwhmY=self.fwhm(yyy, coupeXnorm, order=3)
            
            
            yCXmax=yyy[coupeXnorm.argmax()]
            self.textX.setPos(xCXmax-3,yCXmax+3)
            
        yCYmax=np.amax(coupeYnorm) # max
        if yCYmax>20:
            self.fwhmX=self.fwhm(xxx, coupeYnorm, order=3)
            xCYmax=xxx[coupeYnorm.argmax()]            
            
            self.textY.setPos(xCYmax-3,yCYmax-3) 

    def paletteup(self):
        levels=self.imh.getLevels()
        if levels[0]==None:
            xmax =self.data.max()
            xmin=self.data.min()
        else :
            xmax=levels[1]
            xmin=levels[0]
            
        self.imh.setLevels([xmin, xmax+(xmax- xmin) / 10])
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
            
        self.imh.setLevels([xmin, xmax- (xmax- xmin) / 10])
        #hist.setImageItem(imh,clear=True)
        self.hist.setHistogramRange(xmin,xmax)
        
    # def Reset(self):
    #     self.E = []
    #     self.Xec=[]
    #     self.Yec=[]
        
    
        
    def roiBackChanged(self):
        bg=self.ROIRect.getArrayRegion(self.dataOrg,self.imh).mean()
        print(bg)
        self.data=self.dataOrg-bg
        self.CalculE()
    
    def Back(self):
        if self.bckButton.isChecked()==True:
            self.p1.addItem(self.ROIRect)
            bg=self.ROIRect.getArrayRegion(self.dataOrg,self.imh).mean()
            self.data=self.dataOrg-bg
            self.CalculE()
        else:
            self.p1.removeItem(self.ROIRect)
            
            self.data=self.dataOrg
            
            self.CalculE()
            
            
            
    def closeEvent(self, event):
        """ when closing the window
        """
        self.isWinOpen=False
        self.E=[]
        self.Xec=[]
        self.Yec=[]
        time.sleep(0.1)
        event.accept()
     
        
  
        
if __name__ == "__main__":
    appli = QApplication(sys.argv) 
    appli.setStyleSheet(qdarkstyle.load_stylesheet(qt_api='pyqt6'))
    e = WINENCERCLED(name='VISU')  
    e.show()
    appli.exec_()         