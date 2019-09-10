#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Feb  8 14:46:20 2019
Windows for plot
@author: juliengautier
"""

import pyqtgraph as pg # pyqtgraph biblio permettent l'affichage 

import qdarkstyle # pip install qdakstyle https://github.com/ColinDuquesnoy/QDarkStyleSheet  sur conda
from PyQt5.QtWidgets import QApplication,QHBoxLayout,QWidget,QCheckBox,QLabel,QVBoxLayout,QPushButton,QMessageBox
from pyqtgraph.Qt import QtCore,QtGui
import sys,time
import numpy as np
import pathlib,os
from PyQt5.QtGui import QIcon



class GRAPHCUT(QWidget):
    
    def __init__(self,symbol=True,title='Plot',conf=None):
        super(GRAPHCUT, self).__init__()
        
        p = pathlib.Path(__file__)
        sepa=os.sep
        
        self.title=title
        self.icon=str(p.parent) + sepa+'icons' +sepa
        self.winPLOT = pg.GraphicsLayoutWidget()
        self.isWinOpen=False
        self.symbol=symbol
        self.setup()
        self.setWindowTitle(self.title)
        self.setWindowIcon(QIcon(self.icon+'LOA.png'))
        self.setStyleSheet(qdarkstyle.load_stylesheet_pyqt5())
        self.vLine = pg.InfiniteLine(angle=90, movable=False,pen='y')
        self.hLine = pg.InfiniteLine(angle=0, movable=False,pen='y')
        self.cutData=[]
        self.actionButton()
        self.bloqq=1
        if conf==None:
            self.conf=QtCore.QSettings(str(p.parent / 'confVisu.ini'), QtCore.QSettings.IniFormat)
        else :
            self.conf=conf
       
    def setup(self):
        
        TogOff=self.icon+'Toggle_Off.svg'
        TogOn=self.icon+'Toggle_On.svg'
        TogOff=pathlib.Path(TogOff)
        TogOff=pathlib.PurePosixPath(TogOff)
        TogOn=pathlib.Path(TogOn)
        TogOn=pathlib.PurePosixPath(TogOn)
        self.setStyleSheet("QCheckBox::indicator{width: 30px;height: 30px;}""QCheckBox::indicator:unchecked { image : url(%s);}""QCheckBox::indicator:checked { image:  url(%s);}""QCheckBox{font :10pt;}" % (TogOff,TogOn) )
        
        
        hLayout1=QHBoxLayout()
        self.checkBoxPlot=QCheckBox('CROSS',self)
        self.checkBoxPlot.setChecked(False)
        self.label_CrossValue=QLabel()
        self.label_CrossValue.setStyleSheet("font:15pt")
        hLayout1.addWidget(self.checkBoxPlot)
        hLayout1.addWidget(self.label_CrossValue)
        
        self.openButton=QPushButton('Open',self)
        self.openButton.setIcon(QtGui.QIcon(self.icon+"Open.svg"))
        self.openButton.setIconSize(QtCore.QSize(50,50))
        self.openButton.setMaximumWidth(200)
        self.openButton.setMaximumHeight(100)
        self.openButton.setShortcut(QtGui.QKeySequence("Ctrl+O"))
        hLayout1.addWidget(self.openButton)
        self.openButtonhbox4=QHBoxLayout()
        self.openButton.setStyleSheet("background-color: rgb(0, 0, 0,0) ;border-color: rgb(0, 0, 0,0)")
        
        self.saveButton=QPushButton('Save',self)
        self.saveButton.setMaximumWidth(100)
        self.saveButton.setMinimumHeight(100)
        self.saveButton.setIconSize(QtCore.QSize(50,50))
        hLayout1.addWidget(self.saveButton)
        self.saveButton.setIcon(QtGui.QIcon(self.icon+"Saving.svg"))
        self.saveButton.setStyleSheet("background-color: rgb(0, 0, 0,0) ;border-color: rgb(0, 0, 0,0)")
        
        
        hLayout2=QHBoxLayout()
        hLayout2.addWidget(self.winPLOT)
        VLayout=QVBoxLayout()
        VLayout.addLayout(hLayout1)
        VLayout.addLayout(hLayout2)
        self.setLayout(VLayout)
        self.pCut=self.winPLOT.addPlot(1,0)
        
        
        
    def mouseClick(self): # block the cross if mousse button clicked
        if self.bloqq==1:
            self.bloqq=0
        else :
            self.bloqq=1
            
    def actionButton(self)  :
        self.vb=self.pCut.vb
        # mousse mvt
        self.proxy=pg.SignalProxy(self.pCut.scene().sigMouseMoved, rateLimit=60, slot=self.mouseMoved)
        self.pCut.scene().sigMouseClicked.connect(self.mouseClick)
        self.checkBoxPlot.stateChanged.connect(self.plotCross)
        self.openButton.clicked.connect(self.OpenF)
        self.saveButton.clicked.connect(self.SaveF)
        
    def mouseMoved(self,evt):

        ## the cross mouve with the mousse mvt
        if self.checkBoxPlot.isChecked()==1: # 
            
            pos = evt[0]  ## using signal proxy turns original arguments into a tuple
            if self.pCut.sceneBoundingRect().contains(pos):
                
                mousePoint = self.vb.mapSceneToView(pos)
                self.xMouse = (mousePoint.x())
                self.yMouse= (mousePoint.y())
                if ((self.xMouse>-1 and self.xMouse<self.cutData.shape[0])) :
                        self.xc = self.xMouse
                        self.yc= self.cutData[int(self.xc)]
                        self.vLine.setPos(self.xc)
                        self.hLine.setPos(self.yc)
                        self.label_CrossValue.setText('x='+ str(int(self.xc)) + ' y=' + str(int(self.yc)) )
                        
    def plotCross(self):
        
        if self.checkBoxPlot.isChecked()==1:
            
            self.pCut.addItem(self.vLine, ignoreBounds=False)
            self.pCut.addItem(self.hLine, ignoreBounds=False)    
        else:
            self.pCut.removeItem(self.vLine)
            self.pCut.removeItem(self.hLine) 
            self.label_CrossValue.setText(" ")
            
    def SaveF (self):
        
            self.path=self.conf.value('VISU'+"/path")
            fname=QtGui.QFileDialog.getSaveFileName(self,"Save data as txt ",self.path)
            self.path=os.path.dirname(str(fname[0]))
            fichier=fname[0]
            print(fichier,' is saved')
            self.conf.setValue("VISU"+"/path",self.path)
            time.sleep(0.1)
#        img_PIL = PIL.Image.fromarray(self.data)
#        img_PIL.save(str(fname[0])+'.TIFF',format='TIFF') 
            np.savetxt(str(fichier)+'.txt',self.cutData)
        
    
    def OpenF(self,fileOpen=None):

        if fileOpen==False:
            chemin=self.conf.value('VISU'+"/path")
            fname=QtGui.QFileDialog.getOpenFileName(self,"Open File",chemin,"Images (*.txt *.spe *.TIFF *.sif *.tif);;Text File(*.txt);;Ropper File (*.SPE);;Andor File(*.sif);; TIFF file(*.TIFF)")
            fichier=fname[0]
        else:
            fichier=str(fileOpen)
            
        ext=os.path.splitext(fichier)[1]
        
        if ext=='.txt': # text file
            self.data=np.loadtxt(str(fichier))
            self.PLOT(self.data,symbol=False)
        else :
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Critical)
            msg.setText("Wrong file format !")
            msg.setInformativeText("The format of the file must be : .txt ")
            msg.setWindowTitle("Warning ...")
            msg.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint)
            msg.exec_()
    
    
    def PLOT(self,cutData,axis=None,symbol=True,pen=True,label=None):
        
        self.cutData=np.array(cutData)
        self.symbol=symbol
        self.pen=pen
        if self.pen ==None:
            self.symbol=symbol
            if axis==None:
                if self.symbol==True:
                    self.pCut.plot(cutData,clear=True,symbol='t',pen=self.pen)
                else:
                    self.pCut.plot(cutData,clear=True,pen=self.pen)
            else:
                if self.symbol==True:
                    self.pCut.plot(axis,cutData,clear=True,symbol='t',pen=self.pen)
                else:
                    self.pCut.plot(axis,cutData,clear=True,pen=self.pen)
        else:
            self.symbol=symbol
            if axis==None:
                if self.symbol==True:
                    self.pCut.plot(cutData,clear=True,symbol='t')
                else:
                    self.pCut.plot(cutData,clear=True)
            else:
                if self.symbol==True:
                    self.pCut.plot(axis,cutData,clear=True,symbol='t')
                else:
                    self.pCut.plot(axis,cutData,clear=True)
            
        if label!=None:
            self.pCut.setLabel('bottom',label)
              
            
    def SetTITLE(self,title):
        self.setWindowTitle(title)
    
    def closeEvent(self, event):
        """ when closing the window
        """
        self.isWinOpen=False
        time.sleep(0.1)
        event.accept()
    
    
if __name__ == "__main__":
    appli = QApplication(sys.argv) 
    appli.setStyleSheet(qdarkstyle.load_stylesheet_pyqt5())
    e = GRAPHCUT()  
    e.show()
    appli.exec_()     
        
