#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Feb  8 14:46:20 2019
Windows for plot
@author: juliengautier
"""

import pyqtgraph as pg # pyqtgraph biblio permettent l'affichage 

import qdarkstyle # pip install qdakstyle https://github.com/ColinDuquesnoy/QDarkStyleSheet  sur conda
from PyQt5.QtWidgets import QApplication,QHBoxLayout,QWidget,QCheckBox,QLabel,QVBoxLayout
from PyQt5.QtGui import QIcon
import sys,time

import pathlib,os

class GRAPHCUT(QWidget):
    
    def __init__(self,symbol=True,title='Plot'):
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
        
        
    def mouseMoved(self,evt):

        ## the cross mouve with the mousse mvt
        if self.bloqq==0: # souris non bloquer
            
            pos = evt[0]  ## using signal proxy turns original arguments into a tuple
            if self.pCut.sceneBoundingRect().contains(pos):
                
                mousePoint = self.vb.mapSceneToView(pos)
                self.xMouse = (mousePoint.x())
                self.yMouse= (mousePoint.y())
                if ((self.xMouse>0 and self.xMouse<self.cutData.shape[0]-1)) :
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
            self.pCut.removetem(self.vLine)
            self.pCut.removeItem(self.hLine) 
#    def Display(self,cutData) :
#        pass
        
    def PLOT(self,cutData,axis=None,symbol=True,pen=True,label=None):
        
        self.cutData=cutData
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
        
