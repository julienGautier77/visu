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
    
    def __init__(self,symbol=True,title='Plot',conf=None,name='VISU',meas=True):
        
        super().__init__()
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
        self.meas=meas
        self.cutData=np.zeros(self.dimx)
        self.path=None
        self.axisOn=False
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
        self.symbol=symbol
        
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
        if self.meas==True : #display mean variance pv
        
            self.label_Mean=QLabel('Mean :')
            hLayout1.addWidget(self.label_Mean)
            self.label_MeanValue=QLabel('...')
            hLayout1.addWidget(self.label_MeanValue)
            self.label_PV=QLabel('PV :')
            hLayout1.addWidget(self.label_PV)
            self.label_PVValue=QLabel('...')
            hLayout1.addWidget(self.label_PVValue)
            self.label_Variance=QLabel('variance :')
            hLayout1.addWidget(self.label_Variance)
            self.label_VarianceValue=QLabel('...')
            hLayout1.addWidget(self.label_VarianceValue)
        
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
            #self.cutData=np.loadtxt(str(fichier))
            self.cutData=np.genfromtxt(fichier, delimiter=" ")
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
        if self.axis==None:
            np.savetxt(str(fichier)+'.txt',self.cutData)
        else :
            saveData=np.array([self.axis,self.cutData])
            saveData=saveData.T
            np.savetxt(str(fichier)+'.txt',saveData)
        

        
    def mouseMoved(self,evt):

        ## the cross mouve with the mousse mvt
        if self.checkBoxPlot.isChecked()==1 and self.bloqq==0:
            pos = evt[0]  ## using signal proxy turns original arguments into a tuple
            if self.pCut.sceneBoundingRect().contains(pos):
                
                mousePoint = self.vb.mapSceneToView(pos)
                self.xMouse = (mousePoint.x())
                self.yMouse= (mousePoint.y())
                if self.axisOn==True:
                
                    if (self.xMouse>self.axis.min()-10 and self.xMouse<self.axis.max()+10):  # the cross move only in the graph
                            self.xc =int(self.xMouse)

                            self.yc= self.yMouse#self.cutData[self.xc]
                            
                            self.vLine.setPos(self.xc)
                            self.hLine.setPos(self.yc)     
                            self.affiCross()
                else :     
                    if (self.xMouse>-1 and self.xMouse<self.dimx-1): # the cross move only in the graph
                            self.xc = int(self.xMouse)
                            self.yc= self.cutData[self.xc]
                            self.vLine.setPos(self.xc)
                            self.hLine.setPos(self.yc)     
                            self.affiCross()
    
    def affiCross(self):
        
        if self.checkBoxPlot.isChecked()==1 :
            if self.axisOn==True:
                #print(self.xc,self.yc)
                self.label_Cross.setText('x='+ str(round((self.xc),2)) + ' y=' + str(round(self.yc,2)))
            else:
                self.label_Cross.setText('x='+ str(round((self.xc),2)) + ' y=' + str(round(self.cutData[self.xc],2)))
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
    
        
    def PLOT(self,cutData,axis=[],pen=True,symbol=True,label=None,labelY=None):
        """
        

        Parameters
        ----------
        cutData : TYPE 1D array
            DESCRIPTION. array to plot
        
        axis : TYPE 1D array , optional
            DESCRIPTION. absissee array 
            The default is None.
        symbol : TYPE bool, optional
            DESCRIPTION. True add symbol
            The default is True.
        pen : TYPE, optional
            DESCRIPTION. The default is True.
        label : TYPE, optional
            DESCRIPTION. The default is None.
        labelY : TYPE, optional
            DESCRIPTION. The default is None.

        Returns
        -------
        None.

        """
        
        self.cutData=cutData
        self.dimx=np.shape(self.cutData)[0]
        self.pen=pen
        self.axis=np.array(axis)
        
        if symbol==True:
            self.symbol=self.symbol
        else:
            self.symbol=symbol
        if self.pen ==None:
            
            if self.axis.any()==False:
                if self.symbol==True:
                    self.pCut.plot(cutData,clear=True,symbol='t',pen=self.pen)
                else:
                    
                    self.pCut.plot(cutData,clear=True,pen=self.pen)
            else:
                self.axisOn=True
                if self.symbol==True:
                    self.pCut.plot(axis,cutData,clear=True,symbol='t',pen=self.pen)
                else:
                    self.pCut.plot(axis,cutData,clear=True,pen=self.pen)
        else:
            
            if self.axis.any()==False:
                if self.symbol==True:
                    self.pCut.plot(cutData,clear=True,symbol='t')
                else:
                    self.pCut.plot(cutData,clear=True)
            else:
                self.axisOn=True
                if self.symbol==True:
                    self.pCut.plot(axis,cutData,clear=True,symbol='t')
                else:
                    self.pCut.plot(axis,cutData,clear=True)
            
        if label!=None:
            self.pCut.setLabel('bottom',label)
        if labelY!=None:
            self.pCut.setLabel('left',labelY)
        
        self.PlotXY()
        self.affiCross()
        
        if self.meas==True:
            self.label_MeanValue.setText(str(round(np.mean(cutData),3)))
            self.label_PVValue.setText(str(round(np.ptp(cutData),3)))
            
            self.label_VarianceValue.setText(str(round(np.var(cutData),3)))
       
    def SetTITLE(self,title):
        self.setWindowTitle(title)
    
    def dragEnterEvent(self, e):
        e.accept()

        
    def dropEvent(self, e):
        l = []
        for url in e.mimeData().urls():
            l.append(str(url.toLocalFile()))
        e.accept()
        self.OpenF(fileOpen=l[0])
    
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
        
