#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Feb  8 14:46:20 2019
Windows for plot
@author: juliengautier
"""

import pyqtgraph as pg # pyqtgraph biblio permettent l'affichage 

import qdarkstyle # pip install qdakstyle https://github.com/ColinDuquesnoy/QDarkStyleSheet  sur conda
from PyQt5.QtWidgets import QApplication,QHBoxLayout,QAction,QWidget,QStatusBar,QMainWindow,QVBoxLayout,QCheckBox,QLabel,QPushButton,QMessageBox
from PyQt5.QtGui import QIcon,QColorDialog
import sys,time
from PyQt5.QtCore import Qt
from pyqtgraph.Qt import QtCore,QtGui 
import numpy as np
import pathlib,os

class GRAPHCUT(QMainWindow):
    
    def __init__(self,symbol=None,title='Plot',conf=None,name='VISU',meas=False,pen='w',symbolPen='w'):
        
        super().__init__()
        p = pathlib.Path(__file__)
        sepa=os.sep
        self.title=title
        self.icon=str(p.parent) + sepa+'icons' +sepa
        
        self.isWinOpen=False
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
        
        self.setWindowTitle(self.title)
        self.setWindowIcon(QIcon(self.icon+'LOA.png'))
        self.setStyleSheet(qdarkstyle.load_stylesheet_pyqt5())
        
        self.symbol=symbol
        self.axis=None
        self.label=None
        self.labelY=None
        self.symbolPen=symbolPen
        self.symbolBrush='w'
        self.pen=pen
        self.setup()
        self.actionButton()
    def setup(self):
        
        TogOff=self.icon+'Toggle_Off.png'
        TogOn=self.icon+'Toggle_On.png'
        TogOff=pathlib.Path(TogOff)
        TogOff=pathlib.PurePosixPath(TogOff)
        TogOn=pathlib.Path(TogOn)
        TogOn=pathlib.PurePosixPath(TogOn)
        
        self.setStyleSheet("QCheckBox::indicator{width: 30px;height: 30px;}""QCheckBox::indicator:unchecked { image : url(%s);}""QCheckBox::indicator:checked { image:  url(%s);}""QCheckBox{font :10pt;}" % (TogOff,TogOn) )
        
        self.toolBar =self.addToolBar('tools')
        menubar = self.menuBar()
        menubar.setNativeMenuBar(False)
        self.fileMenu = menubar.addMenu('&File')
        self.ImageMenu = menubar.addMenu('&Plot option')
        
        self.AnalyseMenu = menubar.addMenu('&Analyse')
        self.Aboutenu = menubar.addMenu('&About')
        self.statusBar = QStatusBar()
        self.setContentsMargins(0, 0, 0, 0)
        
        self.setStatusBar(self.statusBar)
        
        self.openAct = QAction(QtGui.QIcon(self.icon+"Open.png"), 'Open File', self)
        self.openAct.setShortcut('Ctrl+o')
        self.openAct.triggered.connect(self.OpenF)
        self.toolBar.addAction(self.openAct)
        self.fileMenu.addAction(self.openAct)
        
        self.saveAct=QAction(QtGui.QIcon(self.icon+"disketteSave.png"), 'Save file', self)
        self.saveAct.setShortcut('Ctrl+s')
        self.saveAct.triggered.connect(self.SaveF)
        self.toolBar.addAction(self.saveAct)
        self.fileMenu.addAction(self.saveAct)
        
        
        vLayout=QVBoxLayout() 
        hLayout1=QHBoxLayout() 
        self.checkBoxPlot=QAction(QtGui.QIcon(self.icon+"target.png"),'Cross On (ctrl+b to block ctrl+d to deblock)',self)
        self.checkBoxPlot.setCheckable(True)
        self.checkBoxPlot.setChecked(False)
        self.checkBoxPlot.triggered.connect(self.PlotXY)
        self.toolBar.addAction(self.checkBoxPlot)
        self.AnalyseMenu.addAction(self.checkBoxPlot)
        
        # self.maxGraphBox=QAction('Set Cross on the max',self)
        # self.maxGraphBox.setCheckable(True)
        # self.maxGraphBox.setChecked(False)
        # self.maxGraphBox.triggered.connect(self.Coupe)
        # self.AnalyseMenu.addAction(self.maxGraphBox)
        
        self.actionColor=QAction('Choose line color',self)
        self.actionColor.triggered.connect(self.setColorLine)
        self.ImageMenu.addAction(self.actionColor)
        
        
        
        self.label_CrossValue=QLabel()
        self.label_CrossValue.setStyleSheet("font:13pt")
        
        self.label_Cross=QLabel()
        #self.label_Cross.setMaximumHeight(20)
        self.label_Cross.setMaximumWidth(170)
        self.label_Cross.setStyleSheet("font:12pt")
        self.statusBar.addPermanentWidget(self.label_Cross)
        self.statusBar.addPermanentWidget(self.label_CrossValue)
        
        
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
        
        
        
        self.checkBoxSymbol=QAction('Set Symbol on',self)
        self.checkBoxSymbol.setCheckable(True)
        self.checkBoxSymbol.setChecked(False)
        self.ImageMenu.addAction(self.checkBoxSymbol)
        self.checkBoxSymbol.triggered.connect(self.setSymbol)
        
        self.checkBoxSymbolColor=QAction('Choose Symbol color',self)
        self.ImageMenu.addAction(self.checkBoxSymbolColor)
        self.checkBoxSymbolColor.triggered.connect(self.setColorSymbol)
        
        
        self.vLine = pg.InfiniteLine(angle=90, movable=False,pen='y')
        self.hLine = pg.InfiniteLine(angle=0, movable=False,pen='y')
    
        self.vLine.setPos(0)
        self.hLine.setPos(0)
        
        vLayout.addLayout(hLayout1)
        
        hLayout2=QHBoxLayout()
        
        self.winImage = pg.GraphicsLayoutWidget()
        self.winPLOT = self.winImage.addPlot()
        
        hLayout2.addWidget(self.winImage)
        vLayout.addLayout(hLayout2)
        
        #self.setLayout(vLayout)
        
        MainWidget=QWidget()
        
        MainWidget.setLayout(vLayout)
        
        self.setCentralWidget(MainWidget)
        
        
        self.pCut=self.winPLOT.plot(symbol=self.symbol,symbolPen=self.symbolPen,symbolBrush=self.symbolBrush,pen=self.pen)
        
#    def Display(self,cutData) :
#        pass
        
    def actionButton(self):
        
         # mousse mvt
        self.proxy=pg.SignalProxy(self.winPLOT.scene().sigMouseMoved, rateLimit=60, slot=self.mouseMoved)
        self.vb=self.winPLOT.vb
        self.winPLOT.scene().sigMouseClicked.connect(self.mouseClick)
        
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
            if self.winPLOT.sceneBoundingRect().contains(pos):
                
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
            
            self.winPLOT.addItem(self.vLine, ignoreBounds=False)
            self.winPLOT.addItem(self.hLine, ignoreBounds=False)
            self.vLine.setPos(self.xc)
            self.hLine.setPos(self.cutData[self.xc]) # the cross move only in the graph    
            
            
        else:
            self.winPLOT.removeItem(self.vLine)
            self.winPLOT.removeItem(self.hLine)
    
     
    def PLOT(self,cutData,axis=[],label=None,labelY=None):
        
        
        self.cutData=cutData
        self.dimx=np.shape(self.cutData)[0]
        
        self.axis=np.array(axis)
        if axis==[]:
            self.data=self.cutData
            self.pCut.setData(self.data)
        else:
            self.pCut.setData(y=self.cutData,x=axis)
    
    
    def CHANGEPLOT(self,cutData,axis=[],label=None,labelY=None):
        """
        

        """
        
        
        self.dimx=np.shape(self.cutData)[0]
        
        self.axis=np.array(axis)
        self.label=label
        self.labelY=labelY
       
       
        
        
        if self.axis.any()==False:
            self.pCut=self.winPLOT.plot(self.cutData,clear=True,symbol=self.symbol,symbolPen=self.symbolPen,symbolBrush=self.symbolBrush,pen=self.pen)
        else:
            self.axisOn=True
           
            self.pCut=self.winPLOT.plot(self.cutData,axis,clear=True,symbol=self.symbol,symbolPen=self.symbolPen,symbolBrush=self.symbolBrush,pen=self.pen)
            
        
        
        if label!=None:
            self.winPLOT.setLabel('bottom',label)
        if labelY!=None:
            self.winPLOT.setLabel('left',labelY)
        
        self.PlotXY()
        self.affiCross()
        
        if self.meas==True:
            self.label_MeanValue.setText(str(round(np.mean(self.cutData),3)))
            self.label_PVValue.setText(str(round(np.ptp(self.cutData),3)))
            
            self.label_VarianceValue.setText(str(round(np.var(self.cutData),3)))
       
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
    
    def setColorLine(self):
        color=QColorDialog.getColor()
        self.color=str(color.name())
        self.pen=pg.mkPen({'color': self.color})
        self.CHANGEPLOT(self.cutData,axis=self.axis,label=self.label,labelY=self.labelY)
    
    def setColorSymbol(self):
        color=QColorDialog.getColor()
        self.colorSymbol=str(color.name())
        self.symbolPen=pg.mkPen({'color': self.colorSymbol})
        self.symbolBrush=pg.mkBrush(self.colorSymbol)
        self.CHANGEPLOT(self.cutData,axis=self.axis,label=self.label,labelY=self.labelY)
    
    
    def setSymbol(self):
        if self.checkBoxSymbol.isChecked()==1:
            self.symbol='t'
        else :
            self.symbol=None
        
        self.CHANGEPLOT(self.cutData,axis=self.axis,label=self.label,labelY=self.labelY)
       
        
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
    a=[2,3,7,-5]
    b=[-2,4,5,7]
    e.PLOT(a,b)
    e.show()
    appli.exec_()     
        
