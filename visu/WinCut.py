#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Feb  8 14:46:20 2019
Windows for plot
@author: juliengautier
"""

import pyqtgraph as pg # pyqtgraph biblio permettent l'affichage 

import qdarkstyle # pip install qdakstyle https://github.com/ColinDuquesnoy/QDarkStyleSheet  sur conda
from PyQt5.QtWidgets import QApplication,QHBoxLayout,QWidget,QVBoxLayout,QCheckBox,QLabel,QPushButton,QMessageBox
from PyQt5.QtGui import QIcon
import sys,time
from PyQt5.QtCore import Qt
from pyqtgraph.Qt import QtCore,QtGui 
import numpy as np
import pathlib,os

class GRAPHCUT(QWidget):
    
    def __init__(self,symbol=True,title='Plot',conf=None,name='VISU'):
        super(GRAPHCUT, self).__init__()
        p = pathlib.Path(__file__)
        sepa=os.sep
        self.title=title
        self.icon=str(p.parent) + sepa+'icons' +sepa
        self.winPLOT = pg.GraphicsLayoutWidget()
        self.isWinOpen=False
        self.symbol=symbol
        self.dimx=10
        self.bloqq=0
        self.xc=0
        self.cutData=np.zeros(self.dimx)
        self.path=None
        if conf==None:
            self.conf=QtCore.QSettings(str(p.parent / 'confVisu.ini'), QtCore.QSettings.IniFormat)
        else :
            self.conf=conf
        self.name=name
        self.setup()
        self.setWindowTitle(self.title)
        self.setWindowIcon(QIcon(self.icon+'LOA.png'))
        self.setStyleSheet(qdarkstyle.load_stylesheet_pyqt5())
        self.actionButton()
        
        
    def setup(self):
        
        TogOff=self.icon+'Toggle_Off.png'
        TogOn=self.icon+'Toggle_On.png'
        TogOff=pathlib.Path(TogOff)
        TogOff=pathlib.PurePosixPath(TogOff)
        TogOn=pathlib.Path(TogOn)
        TogOn=pathlib.PurePosixPath(TogOn)
        
        self.setStyleSheet("QCheckBox::indicator{width: 30px;height: 30px;}""QCheckBox::indicator:unchecked { image : url(%s);}""QCheckBox::indicator:checked { image:  url(%s);}""QCheckBox{font :10pt;}" % (TogOff,TogOn) )
        
        vLayout=QVBoxLayout() 
        
        hLayout1=QHBoxLayout()
        self.checkBoxPlot=QCheckBox('CROSS',self)
        self.checkBoxPlot.setChecked(False)
        
        hLayout1.addWidget(self.checkBoxPlot)
        
        self.label_Cross=QLabel()
        #self.label_Cross.setMaximumHeight(20)
        self.label_Cross.setMaximumWidth(150)
        self.label_Cross. setStyleSheet("font:12pt")
        hLayout1.addWidget(self.label_Cross)
        
        self.openButton=QPushButton('Open',self)
        self.openButton.setIcon(QtGui.QIcon(self.icon+"Open.png"))
        self.openButton.setIconSize(QtCore.QSize(30,30))
        self.openButton.setStyleSheet("background-color: rgb(0, 0, 0,0) ;border-color: rgb(0, 0, 0,0)")
        
        self.openButton.setMaximumWidth(80)
        self.openButton.setMaximumHeight(30)
        self.shortcutOpen=QtGui.QShortcut(QtGui.QKeySequence("Ctrl+o"),self)
        self.shortcutOpen.activated.connect(self.OpenF)
        self.shortcutOpen.setContext(Qt.ShortcutContext(3))
        
        
        hLayout1.addWidget(self.openButton)
        
        self.saveButton=QPushButton('Save',self)
        self.shortcutSave=QtGui.QShortcut(QtGui.QKeySequence("Ctrl+s"),self)
        self.shortcutSave.activated.connect(self.SaveF)
        self.shortcutSave.setContext(Qt.ShortcutContext(3))
        self.openButton.setShortcut(QtGui.QKeySequence("Ctrl+s"))
        self.saveButton.setMaximumWidth(80)
        self.saveButton.setMinimumHeight(30)
        self.saveButton.setIconSize(QtCore.QSize(30,30))
        hLayout1.addWidget(self.saveButton)
        self.saveButton.setIcon(QtGui.QIcon(self.icon+"Saving.png"))
        self.saveButton.setStyleSheet("background-color: rgb(0, 0, 0,0) ;border-color: rgb(0, 0, 0,0)")
       
        
        self.vLine = pg.InfiniteLine(angle=90, movable=False,pen='y')
        self.hLine = pg.InfiniteLine(angle=0, movable=False,pen='y')
    
        self.vLine.setPos(0)
        self.hLine.setPos(0)
        
        vLayout.addLayout(hLayout1)
        
        hLayout2=QHBoxLayout()
        hLayout2.addWidget(self.winPLOT)
        vLayout.addLayout(hLayout2)
        
        self.setLayout(vLayout)
        self.pCut=self.winPLOT.addPlot(1,0)
        
#    def Display(self,cutData) :
#        pass
        
    def actionButton(self):
        self.checkBoxPlot.stateChanged.connect(self.PlotXY)
         # mousse mvt
        self.proxy=pg.SignalProxy(self.pCut.scene().sigMouseMoved, rateLimit=60, slot=self.mouseMoved)
        self.vb=self.pCut.vb
        self.pCut.scene().sigMouseClicked.connect(self.mouseClick)
        
        self.openButton.clicked.connect(self.OpenF)
        self.saveButton.clicked.connect(self.SaveF)
        
    def OpenF(self,fileOpen=False):

        if fileOpen==False:
            chemin=self.conf.value(self.name+"/path")
            fname=QtGui.QFileDialog.getOpenFileName(self,"Open File",chemin," 1D data (*.txt )")
            fichier=fname[0]
        else:
            fichier=str(fileOpen)
            
        ext=os.path.splitext(fichier)[1]
        
        if ext=='.txt': # text file
            self.cutData=np.loadtxt(str(fichier))
            self.PLOT(self.cutData,symbol=False)
            
        else :
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Critical)
            msg.setText("Wrong file format !")
            msg.setInformativeText("The format of the file must be : .txt ")
            msg.setWindowTitle("Warning ...")
            msg.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint)
            msg.exec_()
    

    def SaveF (self):
        
        fname=QtGui.QFileDialog.getSaveFileName(self,"Save data as txt",self.path)
        self.path=os.path.dirname(str(fname[0]))
        fichier=fname[0]
        
        #ext=os.path.splitext(fichier)[1]
        #print(ext)
        print(fichier,' is saved')
        self.conf.setValue(self.name+"/path",self.path)
        time.sleep(0.1)
        
        np.savetxt(str(fichier)+'.txt',self.cutData)
        

        
    def mouseMoved(self,evt):

        ## the cross mouve with the mousse mvt
        if self.checkBoxPlot.isChecked()==1 and self.bloqq==0:
            pos = evt[0]  ## using signal proxy turns original arguments into a tuple
            if self.pCut.sceneBoundingRect().contains(pos):
                
                mousePoint = self.vb.mapSceneToView(pos)
                self.xMouse = (mousePoint.x())
                self.yMouse= (mousePoint.y())
                if (self.xMouse>0 and self.xMouse<self.dimx-1):
                        self.xc = int(self.xMouse)
                        self.yc= self.cutData[self.xc]
                        self.vLine.setPos(self.xc)
                        self.hLine.setPos(self.yc) # the cross move only in the graph    
                        self.affiCross()
    
    def affiCross(self):
        if self.checkBoxPlot.isChecked()==1 :
            self.label_Cross.setText('x='+ str(int(self.xc)) + ' y=' + str(round(self.cutData[self.xc],3)))
        else : 
            self.label_Cross.setText('')
                
    def mouseClick(self): # block the cross if mousse button clicked
        if self.bloqq==1:
            self.bloqq=0
        else :
            self.bloqq=1 
            
            
    def PlotXY(self): # plot cross on the  graph
        
        if self.checkBoxPlot.isChecked()==1:
            
            self.pCut.addItem(self.vLine, ignoreBounds=False)
            self.pCut.addItem(self.hLine, ignoreBounds=False)
            self.vLine.setPos(self.xc)
            self.hLine.setPos(self.cutData[self.xc]) # the cross move only in the graph    
            
            
        else:
            self.pCut.removeItem(self.vLine)
            self.pCut.removeItem(self.hLine)
    
    
        
    def PLOT(self,cutData,axis=None,symbol=True,pen=True,label=None):
        
        self.cutData=cutData
        self.dimx=np.shape(self.cutData)[0]
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
        
        
        self.PlotXY()
        self.affiCross()  
            
 
       
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
        
