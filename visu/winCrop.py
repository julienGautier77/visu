#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on 2023/07/01
@author: juliengautier
window for crop image
"""

from PyQt6.QtWidgets import QApplication,QVBoxLayout,QWidget
from PyQt6.QtWidgets import QLabel,QMainWindow,QFileDialog,QSizePolicy,QStatusBar
from PyQt6 import QtCore,QtGui 
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QAction
from PyQt6.QtGui import QIcon,QShortcut
from PIL import Image
import sys,time
import pyqtgraph as pg # pyqtgraph biblio permettent l'affichage 
import numpy as np
import qdarkstyle # pip install qdakstyle https://github.com/ColinDuquesnoy/QDarkStyleSheet  sur conda
import os
import pathlib


class WINCROP(QMainWindow):
    
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
        self.path=self.conf.value(self.name+"/path")
        self.isWinOpen=False
        self.setWindowTitle('CropWindows')
        self.setWindowIcon(QIcon(self.icon+'LOA.png'))
        self.setStyleSheet(qdarkstyle.load_stylesheet(qt_api='pyqt6'))
        self.left=100
        self.top=30
        self.width=800
        self.height=800
        self.setGeometry(self.left,self.top,self.width,self.height)
        self.dimx=1200
        self.dimy=900
        
        self.setWindowIcon(QIcon('./icons/LOA.png'))
        
        self.data=(40*np.random.rand(self.dimx,self.dimy)).round()
        self.setup()
        self.shortcut()
        
        
    def setup(self):
        
        self.toolBar =self.addToolBar('tools')
        self.toolBar.setMovable(False)

        menubar = self.menuBar()
        menubar.setNativeMenuBar(False)
        self.statusBar = QStatusBar()
        self.setContentsMargins(0, 0, 0, 0)
        
        self.setStatusBar(self.statusBar)
        self.fileMenu = menubar.addMenu('&File')
        self.ImageMenu = menubar.addMenu('&Image')
        self.optionMenu = menubar.addMenu('&Options')
        self.openAct = QAction(QtGui.QIcon(self.icon+"Open.png"), 'Open File', self)
        self.openAct.setShortcut('Ctrl+o')
        self.toolBar.addAction(self.openAct)
        self.openAct.triggered.connect(self.OpenF)
        
        self.fileMenu.addAction(self.openAct)
        
        self.saveAct=QAction(QtGui.QIcon(self.icon+"disketteSave.png"), 'Save file', self)
        self.saveAct.setShortcut('Ctrl+s')
        self.toolBar.addAction(self.saveAct)
        self.saveAct.triggered.connect(self.SaveF)
        
        self.fileMenu.addAction(self.saveAct)
        

        self.checkBoxScale=QAction(QtGui.QIcon(self.icon+"expand.png"),' Auto Scale on',self)
        self.checkBoxScale.setCheckable(True)
        self.checkBoxScale.setChecked(True)
        self.toolBar.addAction(self.checkBoxScale)
        self.ImageMenu.addAction(self.checkBoxScale)
        self.checkBoxScale.triggered.connect(self.checkBoxScaleImage)

        self.label_CrossValue=QLabel()
        self.label_CrossValue.setStyleSheet("font:13pt")
        
        self.label_Cross=QLabel()
        #self.label_Cross.setMaximumHeight(20)
        self.label_Cross.setMaximumWidth(170)
        self.label_Cross.setStyleSheet("font:12pt")
        self.statusBar.addPermanentWidget(self.label_Cross)
        self.statusBar.addPermanentWidget(self.label_CrossValue)

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

        MainWidget=QWidget()
        MainWidget.setLayout(self.vbox2)
        self.setCentralWidget(MainWidget)

        #histogram
        self.hist = pg.HistogramLUTItem() 
        self.hist.setImageItem(self.imh)
        self.hist.autoHistogramRange()
        self.hist.gradient.loadPreset('flame')

        if self.parent is not None:
            #if signal emit in another thread (see visual)
            
            self.parent.signalCrop.connect(self.Display)


    def checkBoxScaleImage(self):

        if self.checkBoxScale.isChecked()==True:
            self.checkBoxScale.setIcon(QtGui.QIcon(self.icon+"expand.png"))
            self.checkBoxScale.setText('Auto Scale On')
        else :
             self.checkBoxScale.setIcon(QtGui.QIcon(self.icon+"minimize.png"))
             self.checkBoxScale.setText('Auto Scale Off')

    def Display(self,data,stepX=1,stepY=1):
        
        self.data=data
        self.dimx=self.data.shape[0]
        self.dimy=self.data.shape[1]
        self.stepX=stepX
        self.stepY=stepY
        if self.checkBoxScale.isChecked()==1:
            self.imh.setImage(self.data,autoLevels=True,autoDownsample=True)
        else :
            self.imh.setImage(self.data,autoLevels=False,autoDownsample=True)

    def shortcut(self):
        # keyboard shortcut
        
        self.shortcutPu=QShortcut(QtGui.QKeySequence("+"),self)
        self.shortcutPu.activated.connect(self.paletteup)
        self.shortcutPu.setContext(Qt.ShortcutContext(3))
        #3: The shortcut is active when its parent widget, or any of its children has focus. default O The shortcut is active when its parent widget has focus.
        self.shortcutPd=QtGui.QShortcut(QtGui.QKeySequence("-"),self)
        self.shortcutPd.activated.connect(self.palettedown)
        self.shortcutPd.setContext(Qt.ShortcutContext(3))
        # mousse action:
        self.proxy=pg.SignalProxy(self.p1.scene().sigMouseMoved, rateLimit=60, slot=self.mouseMoved)
        #self.p1.scene().sigMouseClicked.connect(self.mouseClick)
        #self.vb=self.p1.vb

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

    def OpenF(self,fileOpen=False):

        fname=QFileDialog.getOpenFileNames(self,"Open File")
        self.openedFiles=fname[0]
        fichier=self.openedFiles[0]
        ext=os.path.splitext(fichier)[1]
        
        if ext=='.txt': # text file
            data=np.loadtxt(str(fichier))
        elif ext=='.TIFF' or ext=='.tif' or ext=='.Tiff' or ext=='.jpg' or ext=='.JPEG' or ext=='.png': # tiff File
            dat=Image.open(fichier)
            data=np.array(dat)
            data=np.rot90(data,3) 

        self.Display(self.data)

    def SaveF (self):
        # save as tiff
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
        
    def mouseMoved(self,evt):
        pos = evt[0]  ## using signal proxy turns original arguments into a tuple
        if self.p1.sceneBoundingRect().contains(pos):
            mousePoint = self.p1.vb.mapSceneToView(pos)
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
                self.label_Cross.setText('x='+ str(int(self.xc)) + ' y=' + str(int(self.yc)) )     
                dataCross=round(dataCross,3) # take data  value  on the cross
                self.label_CrossValue.setText(' v.=' + str(dataCross))
        
        
    def closeEvent(self, event):
        """ when closing the window
        """
        self.isWinOpen=False
        time.sleep(0.1)
        event.accept()
    

        
  
        
if __name__ == "__main__":
    appli = QApplication(sys.argv) 
    appli.setStyleSheet(qdarkstyle.load_stylesheet(qt_api='pyqt6'))
    e = WINCROP(name='VISU')  
    e.show()
    appli.exec_()         
