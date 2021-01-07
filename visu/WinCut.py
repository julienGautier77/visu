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
from PyQt5.QtGui import QIcon,QColorDialog,QInputDialog,QGridLayout,QDoubleSpinBox
import sys,time
from PyQt5.QtCore import Qt
from pyqtgraph.Qt import QtCore,QtGui 
import numpy as np
import pathlib,os
from scipy.optimize import curve_fit
from scipy.ndimage.filters import gaussian_filter # pour la reduction du bruit
from scipy.interpolate import splrep, sproot # pour calcul fwhm et fit 



class WINDOWRANGE(QWidget):
    """Samll widget to set axis range
    """
    def __init__(self):
        super().__init__()
        self.isWinOpen=False
        self.setup()
        
    def setup(self):
        hRangeBox=QHBoxLayout()
        hRangeGrid=QGridLayout()
        
        labelXmin=QLabel('Xmin:')
        self.xMinBox=QDoubleSpinBox(self)
        self.xMinBox.setMinimum(-100000)
        hRangeGrid.addWidget(labelXmin,0,0)
        hRangeGrid.addWidget(self.xMinBox,0,1)
        labelXmax=QLabel('Xmax:')
        self.xMaxBox=QDoubleSpinBox(self)
        self.xMaxBox.setMaximum(100000)
        hRangeGrid.addWidget(labelXmax,1,0)
        hRangeGrid.addWidget(self.xMaxBox,1,1)
        
        labelYmin=QLabel('Ymin:')
        self.yMinBox=QDoubleSpinBox(self)
        self.yMinBox.setMinimum(-100000)
        hRangeGrid.addWidget(labelYmin,2,0)
        hRangeGrid.addWidget(self.yMinBox,2,1)
        labelYmax=QLabel('Ymax:')
        self.yMaxBox=QDoubleSpinBox(self)
        self.yMaxBox.setMaximum(100000)
        hRangeGrid.addWidget(labelYmax,3,0)
        hRangeGrid.addWidget(self.yMaxBox,3,1)
        self.applyButton=QPushButton('Apply')
        self.ResetButton=QPushButton('Reset')
        hRangeGrid.addWidget(self.applyButton,4,0)
        hRangeGrid.addWidget(self.ResetButton,4,1)
        self.setLayout(hRangeGrid)

        
    def closeEvent(self, event):
        """ when closing the window
        """
        self.isWinOpen=False
        
        time.sleep(0.1)
        event.accept()

class GRAPHCUT(QMainWindow):
    
    def __init__(self,symbol=None,title='Plot',conf=None,name='VISU',meas=False,pen='w',symbolPen='w',label=None,labelY=None,clearPlot=True):
        
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
        self.label=label
        self.labelY=labelY
        self.symbolPen=symbolPen
        self.symbolBrush='w'
        self.ligneWidth=1
        self.color='w'
        self.plotRectZoomEtat="Zoom"
        self.pen=pen
        self.clearPlot=clearPlot
        self.xLog=False
        self.yLog=False
                
        self.widgetRange=WINDOWRANGE()
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
        self.axisMenu=menubar.addMenu('&Axis option')
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
        
        self.actionLigne=QAction('Set line',self)
        self.actionLigne.triggered.connect(self.setLine)
        self.actionLigne.setCheckable(True)
        if self.pen is not None:
            self.actionLigne.setChecked(True)
            
        self.ImageMenu.addAction(self.actionLigne)
        
        self.actionColor=QAction('Set line color',self)
        self.actionColor.triggered.connect(self.setColorLine)
        self.ImageMenu.addAction(self.actionColor)
        
        self.actionLigneWidth=QAction('Set line width',self)
        self.actionLigneWidth.triggered.connect(self.setWidthLine)
        self.ImageMenu.addAction(self.actionLigneWidth)
        
        
        
        
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
        if self.symbol is not None:
            self.checkBoxSymbol.setChecked(True)
        self.ImageMenu.addAction(self.checkBoxSymbol)
        self.checkBoxSymbol.triggered.connect(self.setSymbol)
        
        self.checkBoxSymbolColor=QAction('Set Symbol color',self)
        self.ImageMenu.addAction(self.checkBoxSymbolColor)
        self.checkBoxSymbolColor.triggered.connect(self.setColorSymbol)
        
        self.showGridX=QAction('Show X grid',self)
        self.showGridX.setCheckable(True)
        self.ImageMenu.addAction(self.showGridX)
        self.showGridX.triggered.connect(self.showGrid)
        
        self.showGridY=QAction('Show Y grid',self)
        self.showGridY.setCheckable(True)
        self.ImageMenu.addAction(self.showGridY)
        self.showGridY.triggered.connect(self.showGrid)
        
        
        self.lockGraphAction=QAction('Lock Graph',self)
        self.lockGraphAction.setCheckable(True)
        self.ImageMenu.addAction(self.lockGraphAction)
        self.lockGraphAction.triggered.connect(self.lockGraph)
        
        self.axisRange=QAction('Set Axis Range',self)
        self.axisMenu.addAction(self.axisRange)
        self.axisRange.triggered.connect(self.showRange)
        
        self.logActionX=QAction('Log X',self)
        self.axisMenu.addAction(self.logActionX)
        self.logActionX.setCheckable(True)
        self.logActionX.triggered.connect(self.logMode)
        
        self.logActionY=QAction('Log Y',self)
        self.axisMenu.addAction(self.logActionY)
        self.logActionY.setCheckable(True)
        self.logActionY.triggered.connect(self.logMode)
        
        self.ZoomRectButton=QAction(QtGui.QIcon(self.icon+"loupe.png"),'Zoom',self)
        self.ZoomRectButton.triggered.connect(self.zoomRectAct)
        self.toolBar.addAction(self.ZoomRectButton)
        self.plotRectZoom=pg.RectROI([0,0],[4,4],pen='w')
            
        self.fitAction=QAction('Gaussian Fit',self)
        self.AnalyseMenu.addAction(self.fitAction)
        self.fitAction.setCheckable(True)
        self.fitAction.triggered.connect(self.setFit)
        
        self.vLine = pg.InfiniteLine(angle=90, movable=False,pen='y')
        self.hLine = pg.InfiniteLine(angle=0, movable=False,pen='y')
    
        self.vLine.setPos(0)
        self.hLine.setPos(0)
        
        vLayout.addLayout(hLayout1)
        hLayout2=QHBoxLayout()
        
        self.winImage = pg.GraphicsLayoutWidget()
        self.winPLOT = self.winImage.addPlot()
        if self.label!=None:
            self.winPLOT.setLabel('bottom',self.label)
        if self.labelY!=None:
            self.winPLOT.setLabel('left',self.labelY)
        hLayout2.addWidget(self.winImage)
        vLayout.addLayout(hLayout2)
        
        #self.setLayout(vLayout)
        
        MainWidget=QWidget()
        
        MainWidget.setLayout(vLayout)
        
        self.setCentralWidget(MainWidget)
        
        
        self.pCut=self.winPLOT.plot(symbol=self.symbol,symbolPen=self.symbolPen,symbolBrush=self.symbolBrush,pen=self.pen,clear=self.clearPlot)
        pen=pg.mkPen(color='r',width=3)
        self.pFit=self.winPLOT.plot(pen=pen)
#    def Display(self,cutData) :
#        pass
        
    def actionButton(self):
        
         # mousse mvt
        self.proxy=pg.SignalProxy(self.winPLOT.scene().sigMouseMoved, rateLimit=60, slot=self.mouseMoved)
        self.vb=self.winPLOT.vb
        self.winPLOT.scene().sigMouseClicked.connect(self.mouseClick)
        self.widgetRange.applyButton.clicked.connect(self.setRangeOn)
        self.widgetRange.ResetButton.clicked.connect(self.setRangeReset)
        
        
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
        
        self.label=label
        self.labelY=labelY
        self.cutData=cutData
        self.axis=np.array(axis)
         
        self.dimy=max(cutData)
        self.minY=min(cutData)
        if self.axis.any()==False:
            self.dimx=np.shape(self.cutData)[0]
            self.minX=0
            self.data=self.cutData
            self.pCut.setData(self.data)
        else:
            self.dimx=max(self.axis)
            self.minX=min(self.axis)
            self.pCut.setData(y=self.cutData,x=self.axis)
        self.zoomRectupdate()
        self.setFit()
        
        
    def CHANGEPLOT(self,cutData):
        """
        
        """
        
        if self.axis.any()==False:
            self.pCut=self.winPLOT.plot(self.cutData,clear=self.clearPlot,symbol=self.symbol,symbolPen=self.symbolPen,symbolBrush=self.symbolBrush,pen=self.pen)
        else:
            self.axisOn=True
           
            self.pCut=self.winPLOT.plot(y=self.cutData,x=self.axis,clear=self.clearPlot,symbol=self.symbol,symbolPen=self.symbolPen,symbolBrush=self.symbolBrush,pen=self.pen)
            
        if self.label!=None:
            self.winPLOT.setLabel('bottom',self.label)
        if self.labelY!=None:
            self.winPLOT.setLabel('left',self.labelY)
            
        self.pFit=self.winPLOT.plot(clear=self.clearPlot,pen='r')
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
    
    
    def setLine(self):
        if self.actionLigne.isChecked()==0:
            self.pen=None
        else:
            self.pen=pg.mkPen(color=self.color,width=self.ligneWidth)
            
        self.CHANGEPLOT(self.cutData)
    
    
    def setColorLine(self):
        color=QColorDialog.getColor()
        self.color=str(color.name())
        self.pen=pg.mkPen(color=self.color,width=self.ligneWidth)
        self.CHANGEPLOT(self.cutData)
    
    def setWidthLine(self):
        num,ok = QInputDialog.getInt(self,"Line width","enter a width ")
        if ok:
            self.ligneWidth=float(num)
            self.pen=pg.mkPen(color=self.color,width=self.ligneWidth)
            self.CHANGEPLOT(self.cutData)
            
    def setColorSymbol(self):
        color=QColorDialog.getColor()
        self.colorSymbol=str(color.name())
        self.symbolPen=pg.mkPen({'color': self.colorSymbol})
        self.symbolBrush=pg.mkBrush(self.colorSymbol)
        self.CHANGEPLOT(self.cutData)
    
    def showGrid(self):
        
        self.winPLOT.showGrid(x = self.showGridX.isChecked(), y = self.showGridY.isChecked())
        
    def setSymbol(self):
        
        if self.checkBoxSymbol.isChecked()==1:
            self.symbol='t'
        else :
            self.symbol=None
        
        self.CHANGEPLOT(self.cutData)
       
    
    def zoomRectAct(self):
        
        if self.plotRectZoomEtat=="Zoom": 
            self.winPLOT.addItem(self.plotRectZoom)
            self.plotRectZoom.setPos([self.dimx/2,self.dimy/2])
            self.ZoomRectButton.setIcon(QtGui.QIcon(self.icon+"zoom-in.png"))
            self.plotRectZoomEtat="ZoomIn"
            
        elif self.plotRectZoomEtat=="ZoomIn":
            self.ZoomRectButton.setIcon(QtGui.QIcon(self.icon+"zoom-out.png"))
            self.xZoomMin=(self.plotRectZoom.pos()[0])
            self.yZoomMin=(self.plotRectZoom.pos()[1])
            self.xZoomMax=(self.plotRectZoom.pos()[0])+self.plotRectZoom.size()[0]
            self.yZoomMax=(self.plotRectZoom.pos()[1])+self.plotRectZoom.size()[1]
            self.winPLOT.setXRange(self.xZoomMin,self.xZoomMax)
            self.winPLOT.setYRange(self.yZoomMin,self.yZoomMax)
            #self.winPlot.setAspectLocked(True)
            self.winPLOT.removeItem(self.plotRectZoom)
            
            self.plotRectZoomEtat="ZoomOut"
        
        elif self.plotRectZoomEtat=="ZoomOut": 
            self.winPLOT.setYRange(self.minY,self.dimy)
            
            self.winPLOT.setXRange(self.minX,self.dimx)
            self.ZoomRectButton.setIcon(QtGui.QIcon(self.icon+"loupe.png"))
            self.plotRectZoomEtat="Zoom"
            #self.winPlot.setAspectLocked(True,ratio=1)
            
    def zoomRectupdate(self):
        if self.plotRectZoomEtat=="ZoomOut":
            self.winPLOT.setXRange(self.xZoomMin,self.xZoomMax)
            self.winPlot.setYRange(self.yZoomMin,self.yZoomMax)
            #self.pwinPlot.setAspectLocked(True)   
    
    
    def showRange(self):
        
        self.open_widget(self.widgetRange)
        
        
    def setRangeOn(self) :       
        self.xZoomMin=(self.widgetRange.xMinBox.value())
        self.yZoomMin=(self.widgetRange.yMinBox.value())
        self.xZoomMax=(self.widgetRange.xMaxBox.value())
        self.yZoomMax=(self.widgetRange.yMaxBox.value())
        self.winPLOT.setXRange(self.xZoomMin,self.xZoomMax)
        self.winPLOT.setYRange(self.yZoomMin,self.yZoomMax)
        self.plotRectZoomEtat="Zoom"
        
    def setRangeReset(self) :  
        self.winPLOT.setYRange(self.minY,self.dimy)
        self.winPLOT.setXRange(self.minX,self.dimx)
        self.plotRectZoomEtat="ZoomOut"
     
        
    def lockGraph(self):
        
        if self.lockGraphAction.isChecked():
            self.clearPlot=False
        else:
            self.clearPlot=True
        self.CHANGEPLOT(self.cutData)
    
    def logMode(self):
        if self.logActionY.isChecked():
            self.yLog=True
        else :self.yLog=False
        if self.logActionX.isChecked():
            self.xLog=True
        else : self.xLog=False
        self.winPLOT.setLogMode(x=self.xLog, y=self.yLog)
        self.CHANGEPLOT(self.cutData)
        
        
    def setFit(self):
        
        if self.fitAction.isChecked():
            if self.axis.any()==False:
                xxx=np.arange(0,int(self.dimx),1)
            else :
                xxx=self.axis
                
            try :
                Datafwhm,xDataMax=self.fwhm(xxx,self.cutData)
                ymaxx=self.cutData[int(xDataMax)]
            except:
                Datafwhm,xDataMax=0,0
                
            init_vals = [ymaxx, xDataMax, Datafwhm,0]  # for [A, mu, sigma,B]
            try :
                best_vals, covar = curve_fit(self.gauss, xxx, gaussian_filter(self.cutData,5), p0=init_vals)
        
                y_fit = self.gauss(xxx, best_vals[0], best_vals[1], best_vals[2],best_vals[3])
            except:
                y_fit = []
                
            self.pFit.setData(x=xxx,y=y_fit)
            self.fitA=best_vals[0]
            self.fitMu=best_vals[1]
            self.fitSigma=best_vals[2]
        else :
             self.pFit.setData([])
            
        
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
            return np.around(abs(roots[1] - roots[0]),decimals=2),half_max
    
    def gauss(self,x, A, mu, sigma,B ):
    
        return A*np.exp(-(x-mu)**2/(2.*sigma**2))+B
    
    
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
    a=[2,3,7,100,1000]
    b=[2,4,5,100,2000]
    e.PLOT(a,b)
    e.show()
    appli.exec_()     
        
