#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Dec 19 11:43:05 2018
@author: juliengautier

"""

from PyQt5.QtWidgets import QApplication,QVBoxLayout,QHBoxLayout,QWidget,QGridLayout
from PyQt5.QtWidgets import QCheckBox,QLabel,QSizePolicy,QSpinBox,QPushButton,QMainWindow,QMessageBox
from pyqtgraph.Qt import QtCore,QtGui 
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QShortcut,QAction
from PyQt5.QtGui import QIcon
import sys,time
import pyqtgraph as pg # pyqtgraph biblio permettent l'affichage 
import numpy as np
import qdarkstyle # pip install qdakstyle https://github.com/ColinDuquesnoy/QDarkStyleSheet  sur conda
import pylab,os
from scipy.ndimage.filters import gaussian_filter # pour la reduction du bruit
from scipy.interpolate import splrep, sproot # pour calcul fwhm et fit 
import pathlib

class WINPOINTING(QMainWindow):
    
    def __init__(self,conf=None,name='VISU'):
        
        super().__init__()
        self.name=name
        p = pathlib.Path(__file__)
        if conf==None:
            self.conf=QtCore.QSettings(str(p.parent / 'confVisu.ini'), QtCore.QSettings.IniFormat)
        else :
            self.conf=conf
        
        sepa=os.sep
        self.icon=str(p.parent) + sepa+'icons' +sepa
        self.path=self.conf.value(self.name+"/path")
        self.isWinOpen=False
        self.setWindowTitle('Pointing')
        self.setWindowIcon(QIcon(self.icon+'LOA.png'))
        self.setStyleSheet(qdarkstyle.load_stylesheet_pyqt5())
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
        
        # self.Display(self.data)
        
    def setup(self):
        
        
        menubar = self.menuBar()
        menubar.setNativeMenuBar(False)
        self.fileMenu = menubar.addMenu('&File')
        
        self.openAct = QAction(QtGui.QIcon(self.icon+"Open.png"), 'Open File', self)
        self.openAct.setShortcut('Ctrl+o')
        self.openAct.triggered.connect(self.OpenF)
        
        self.fileMenu.addAction(self.openAct)
        
        self.saveAct=QAction(QtGui.QIcon(self.icon+"disketteSave.png"), 'Save file', self)
        self.saveAct.setShortcut('Ctrl+s')
        self.saveAct.triggered.connect(self.SaveF)
        
        self.fileMenu.addAction(self.saveAct)
        
        # vbox1=QVBoxLayout()
        XYHLayout=QHBoxLayout()
        
        self.resetButton=QAction('Reset',self)
        self.resetButton.triggered.connect(self.Reset)
        self.fileMenu.addAction(self.resetButton)
        # vbox1.addLayout(hbox)
        
        
        
        self.win1=pg.PlotWidget()
        self.p1=self.win1.plot(pen='w',symbol='t',symboleSize=2,clear=True,symbolPen='w',symbolBrush='w',name="XY")
        self.win1.setContentsMargins(0,0,0,0)
        self.win1.setLabel('bottom','X')#,units='pixel')
        self.win1.setLabel('left','Y')#,units='pixel')
        
        XYHLayout.addWidget(self.win1)
        
        
        
        self.win3=pg.PlotWidget()
        self.p3=self.win3.plot(pen='r',symbol='t',symboleSize=2,clear=True,symbolPen='r',symbolBrush='r',name="x")
        self.win3.setContentsMargins(0,0,0,0)
        self.win3.setLabel('left','X')#,units='pixel')
        self.hLineMeanX = pg.InfiniteLine(angle=0, movable=False,pen=pg.mkPen('r', width=3, style=QtCore.Qt.DashLine))
        self.win3.addItem(self.hLineMeanX, ignoreBounds=True)
        
        
      
        
        
        
        labelMeanX=QLabel('<X>')
        self.meanXAff=QLabel()
        labelMeanX.setStyleSheet("color:red;font:14pt")
        
        labelStdX=QLabel('std X')
        labelStdX.setStyleSheet("color:red;font:14pt")
        self.stdXAff=QLabel()
        
        labelPVX=QLabel('PV X')
        labelPVX.setStyleSheet("color:red;font:14pt")
        self.PVXAff=QLabel()
        
        
        grid_layoutX=QGridLayout()
        grid_layoutX.addWidget(labelMeanX, 0, 0)
        grid_layoutX.addWidget(self.meanXAff,0, 1)
        grid_layoutX.addWidget(labelStdX, 1, 0)
        grid_layoutX.addWidget(self.stdXAff, 1,1)
        grid_layoutX.addWidget(labelPVX,2,0)
        grid_layoutX.addWidget(self.PVXAff, 2,1)
        
        
        
        
        XHLayout=QHBoxLayout()
        XHLayout.addWidget(self.win3)
        
        
        
        
        
        dataxVLayout=QVBoxLayout()
        dataxVLayout.addStretch(2)
        dataxVLayout.addLayout(grid_layoutX)
        dataxVLayout.addStretch(2)
        XHLayout.addLayout(dataxVLayout)
        
        
        
        self.win4=pg.PlotWidget()
        self.p4=self.win4.plot(pen='g',symbol='t',symboleSize=2,clear=True,symbolPen='g',symbolBrush='g',name="y")
        self.win4.setLabel('left','Y')#,units='pixel')
        self.win4.setLabel('bottom',"Shoot number")
        self.hLineMeanY = pg.InfiniteLine(angle=0, movable=False,pen=pg.mkPen('g', width=3, style=QtCore.Qt.DashLine))
        self.win4.addItem(self.hLineMeanY, ignoreBounds=True)
        
        
        labelMeanY=QLabel('<Y>')
        self.meanYAff=QLabel()
        labelMeanY.setStyleSheet("color:green;font:14pt")
        
        labelStdY=QLabel('std Y')
        labelStdY.setStyleSheet("color:green;font:14pt")
        self.stdYAff=QLabel()
        labelPVY=QLabel('PV Y')
        labelPVY.setStyleSheet("color:green;font:14pt")
        self.PVYAff=QLabel()
        
        grid_layoutY=QGridLayout()
        grid_layoutY.addWidget(labelMeanY, 0, 0)
        grid_layoutY.addWidget(self.meanYAff,0, 1)
        grid_layoutY.addWidget(labelStdY, 1, 0)
        grid_layoutY.addWidget(self.stdYAff, 1,1)
        grid_layoutY.addWidget(labelPVY,2,0)
        grid_layoutY.addWidget(self.PVYAff, 2,1)
        
        
        
        YHLayout=QHBoxLayout()
        YHLayout.addWidget(self.win4)
        
        datayVLayout=QVBoxLayout()
        datayVLayout.addStretch(2)
        datayVLayout.addLayout(grid_layoutY)
        datayVLayout.addStretch(2)
        YHLayout.addLayout(datayVLayout)
        
        
        vMainLayout=QVBoxLayout()
        
        # vMainLayout.addLayout(vbox1)
        vMainLayout.addLayout(XYHLayout)
        vMainLayout.addLayout(XHLayout)
        vMainLayout.addLayout(YHLayout)
        
        
        MainWidget=QWidget()
        
        MainWidget.setLayout(vMainLayout)
      
        self.setCentralWidget(MainWidget)
        self.setContentsMargins(1,1,1,1)
        
        self.axeX1=self.win1.getAxis('bottom')
        self.axeY1=self.win1.getAxis('left')
        
        self.axeY3=self.win3.getAxis('left')
        self.axeY4=self.win4.getAxis('left')
        
 
        
    def Display(self,data,stepX=1,stepY=1):
        self.data=data
        self.dimx=self.data.shape[0]
        self.dimy=self.data.shape[1]
        self.stepX=stepX
        self.stepY=stepY
        dataF=gaussian_filter(self.data,5)
        (self.xec,self.yec)=pylab.unravel_index(dataF.argmax(),self.data.shape) 
        
        self.xec=self.xec*stepX
        self.yec=self.yec*stepX
        
        self.Xec.append(self.xec)
        self.Yec.append(self.yec)
        
        Xmean=np.mean(self.Xec)
        self.meanXAff.setText('%.2f' % Xmean)
        stdX=np.std(self.Xec)
        self.stdXAff.setText('%.2f' % stdX)
        self.hLineMeanX.setPos(Xmean)
        Ymean=np.mean(self.Yec)
        self.meanYAff.setText('%.2f' % Ymean)
        stdV=np.std(self.Yec)
        self.stdYAff.setText('%.2f' % stdV)
        self.hLineMeanY.setPos(Ymean)
        
        XPV=max(self.Xec)-min(self.Xec)
        self.PVXAff.setText('%.2f' % XPV)
        
        YPV=max(self.Yec)-min(self.Yec)
        self.PVYAff.setText('%.2f' % YPV)
        
        
        
        self.p1.setData(y=self.Yec,x=self.Xec)
        self.p3.setData(self.Xec)#,pen='r',symbol='t',symboleSize=2,clear=True,symbolPen='r',symbolBrush='r',name="x")
        #self.p3.addItem(self.hLineMeanX, ignoreBounds=True)
        self.p4.setData(self.Yec)#,pen='g',symbol='t',symboleSize=2,clear=True,symbolPen='g',symbolBrush='g',name="y")
        #self.p4.addItem(self.hLineMeanY, ignoreBounds=True)
        
        if self.stepX!=1:
            self.axeX1.setLabel("um")
            
        else:
            self.axeX1.showLabel(False)
            
        if self.stepY!=1: 
            self.axeY1.setLabel("um")
            self.axeY3.setLabel("um")
            self.axeY4.setLabel("um")
        else:
            self.axeY1.showLabel(False)
            self.axeY3.showLabel(False)
            self.axeY4.showLabel(False)
            
    
        
    
    
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
            aa=np.loadtxt(fichier, delimiter=" ",comments='#')
            
            self.Xec=aa[:,0]
            self.Yec=aa[:,1]
            
            
            self.p1.setData(y=self.Yec,x=self.Xec)
            self.p3.setData(self.Xec)
            self.p4.setData(self.Yec)
            Xmean=np.mean(self.Xec)
            self.meanXAff.setText('%.2f' % Xmean)
            stdX=np.std(self.Xec)
            self.stdXAff.setText('%.2f' % stdX)
            self.hLineMeanX.setPos(Xmean)
            Ymean=np.mean(self.Yec)
            self.meanYAff.setText('%.2f' % Ymean)
            stdV=np.std(self.Yec)
            self.stdYAff.setText('%.2f' % stdV)
            self.hLineMeanY.setPos(Ymean)
        
            XPV=max(self.Xec)-min(self.Xec)
            self.PVXAff.setText('%.2f' % XPV)
        
            YPV=max(self.Yec)-min(self.Yec)
            self.PVYAff.setText('%.2f' % YPV)
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
        
        np.savetxt(str(fichier)+'.txt',np.array(self.Xec, self.Yec).T,header="StepX:"+str(self.stepX)+"StepY:"+str(self.stepY))
        
    
    
    
    def Reset(self):
        print('reset)')
        self.Xec=[]
        self.Yec=[]
        
        
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
    appli.setStyleSheet(qdarkstyle.load_stylesheet_pyqt5())
    e = WINPOINTING(name='VISU')  
    e.show()
    appli.exec_()         