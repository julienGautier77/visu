#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Feb 10 09:44:07 2019
Window for Measurement
@author: juliengautier
modified 2019/08/13 : add motors RSAI position and zoom windows
"""


import qdarkstyle 
from PyQt6 import QtCore,QtGui 
from PyQt6.QtWidgets import QApplication,QVBoxLayout,QHBoxLayout,QMainWindow
from PyQt6.QtWidgets import QWidget,QTableWidget,QTableWidgetItem,QAbstractItemView,QComboBox,QInputDialog
from PyQt6.QtGui import QAction
from PyQt6.QtGui import QIcon

from scipy import ndimage
from visu.WinCut import GRAPHCUT
from visu.winZoom import ZOOM
import pathlib
import numpy as np
import sys,time,os


class MEAS(QMainWindow):
    
    signalPlot=QtCore.pyqtSignal(object)
    
    def __init__(self,parent=None,conf=None,name='VISU',confMot=None,**kwds):
        
        super().__init__()
        self.parent=parent
        self.setStyleSheet(qdarkstyle.load_stylesheet(qt_api='pyqt6'))
        p = pathlib.Path(__file__)
        sepa=os.sep
        if conf==None:
            print('tt')
            self.conf=QtCore.QSettings(str(p.parent / 'confVisu.ini'), QtCore.QSettings.IniFormat)
        else :
            self.conf=conf
        self.confMot=confMot   
        self.name=name
        
        self.ThresholdState=False
        self.symbol=False
        if self.confMot!=None:    
            self.groups=self.confMot.childGroups()
            #print('groups',self.groups,self.confMotPath)
            try :
                import moteurRSAI as RSAI
            except: 
                import  visu.moteurRSAI as RSAI
            self.motorType=RSAI
            self.nbMotors=int(np.size(self.groups))
           
        self.unitChange=1
        self.unitName='step'
        self.icon=str(p.parent) + sepa+'icons' +sepa
        self.isWinOpen=False
        self.setup()
        self.setWindowTitle('MEASUREMENTS')
        self.shoot=0
        self.nomFichier=''
        self.TableSauv=['file,Max,Min,x Max,y max,Sum,Mean,Size,x c.mass,y c.mass']
        
        self.path=self.conf.value(self.name+"/path")
        self.winCoupeMax=GRAPHCUT(parent=self,conf=self.conf,name=self.name,symbol='t',pen=None)
        self.winCoupeMin=GRAPHCUT(parent=self,conf=self.conf,name=self.name,symbol='t',pen=None)
        self.winCoupeXmax=GRAPHCUT(parent=self,conf=self.conf,name=self.name,symbol='t',pen=None)
        self.winCoupeYmax=GRAPHCUT(parent=self,conf=self.conf,name=self.name,symbol='t',pen=None)
        self.winCoupeSum=GRAPHCUT(parent=self,conf=self.conf,name=self.name,symbol='t',pen=None)
        self.winCoupeMean=GRAPHCUT(parent=self,conf=self.conf,name=self.name,symbol='t',pen=None)
        self.winCoupeXcmass=GRAPHCUT(parent=self,conf=self.conf,name=self.name,symbol='t',pen=None)
        self.winCoupeYcmass=GRAPHCUT(parent=self,conf=self.conf,name=self.name,symbol='t',pen=None)
        self.winCoupeSumThreshold=GRAPHCUT(parent=self,conf=self.conf,name=self.name,symbol='t',pen=None)
        self.signalTrans=dict()
        
        self.Maxx=[]
        self.Minn=[]
        self.Summ=[]
        self.Mean=[]
        self.Xmax=[]
        self.Ymax=[]
        self.Xcmass=[]
        self.Ycmass=[]
        self.labelsVert=[]
        self.posMotor=[]
        self.SummThre=[]
        self.winZoomMax=ZOOM()
        self.winZoomSum=ZOOM()
        self.winZoomMean=ZOOM()
        self.winZoomXmax=ZOOM()
        self.winZoomYmax=ZOOM()
        self.winZoomCxmax=ZOOM()
        self.winZoomCymax=ZOOM()
        self.winZoomSumThreshold=ZOOM()
        self.maxx=0
        self.summ=0
        self.moy=0
        self.label='Shoot'
        self.setWindowIcon(QIcon(self.icon+'LOA.png'))
        self.setGeometry(100, 300, 700, 300)
        
    def setFile(self,file) :
        self.nomFichier=file
        
    def setup(self):
        
            
        vLayout=QVBoxLayout()
        
        hLayout1=QHBoxLayout()
        # self.toolBar =self.addToolBar('tools')
        #self.setStyleSheet("{background-color: black}")
        menubar = self.menuBar()
        menubar.setNativeMenuBar(False)
        self.fileMenu = menubar.addMenu('&File')
        self.PlotMenu = menubar.addMenu('&Plot')
        self.ZoomMenu = menubar.addMenu('&Zoom')
        
        self.ThresholdAct=QAction('Threshold',self)
        self.ThresholdMenu = menubar.addAction(self.ThresholdAct)
        self.ThresholdAct.triggered.connect(self.Threshold)
        
        self.setContentsMargins(0, 0, 0, 0)
       
        
        self.openAct = QAction(QtGui.QIcon(self.icon+"Open.png"), 'Open File', self)
        self.openAct.setShortcut('Ctrl+o')
        self.openAct.triggered.connect(self.openF)
        
        self.fileMenu.addAction(self.openAct)
        
        self.saveAct=QAction(QtGui.QIcon(self.icon+"disketteSave.png"), 'Save file', self)
        self.saveAct.setShortcut('Ctrl+s')
        self.saveAct.triggered.connect(self.saveF)
        
        self.fileMenu.addAction(self.saveAct)
        
        
        
        
        
        self.PlotMenu.addAction('max',self.PlotMAX)
        self.PlotMenu.addAction('min',self.PlotMIN)
        self.PlotMenu.addAction('x max',self.PlotXMAX)
        self.PlotMenu.addAction('y max',self.PlotYMAX)
        self.PlotMenu.addAction('Sum',self.PlotSUM)
        self.PlotMenu.addAction('Mean',self.PlotMEAN)
        self.PlotMenu.addAction('x center mass',self.PlotXCMASS)
        self.PlotMenu.addAction('y center mass',self.PlotYCMASS)
        
        
        
       
        
        
        self.ZoomMenu.addAction('max',self.ZoomMAX)
        self.ZoomMenu.addAction('Sum',self.ZoomSUM)
        self.ZoomMenu.addAction('Mean',self.ZoomMEAN)
        self.ZoomMenu.addAction('X max',self.ZoomXmax) 
        self.ZoomMenu.addAction('Y max',self.ZoomYmax)
        self.ZoomMenu.addAction(' X c.of.m',self.ZoomCxmax)
        self.ZoomMenu.addAction(' Y c.of.m',self.ZoomCymax)
        
        
        
        
        
        self.But_reset=QAction('Reset',self)
        # self.PlotMenu.addAction(self.But_reset)
        menubar.addAction(self.But_reset)
        
        
        
        hLayout2=QHBoxLayout()
        self.table=QTableWidget()
        hLayout2.addWidget(self.table)
        
        self.table.setColumnCount(10)
        #self.table.setRowCount(10)
       
        self.table.setHorizontalHeaderLabels(('File','Max','Min','x max','y max','Sum','Mean','Size','x c.mass','y c.mass'))
        
        if self.confMot!=None:
            self.motorNameBox=QComboBox()
            self.motorNameBox.addItem('Motors')
            hLayout1.addWidget(self.motorNameBox)
            self.unitBouton=QComboBox()
            self.unitBouton.addItem('Step')
            self.unitBouton.addItem('um')
            self.unitBouton.addItem('mm')
            self.unitBouton.addItem('ps')
            self.unitBouton.addItem('°')
            self.unitBouton.setMaximumWidth(100)
            self.unitBouton.setMinimumWidth(100)
            hLayout1.addWidget(self.unitBouton)
            self.unitBouton.currentIndexChanged.connect(self.unit) 
            for mo in range (0,self.nbMotors):
                self.motorNameBox.addItem(self.groups[mo])
            self.table.setColumnCount(11)   
            self.table.setHorizontalHeaderLabels(('File','Max','Min','x max','y max','Sum','Mean','Size','x c.mass','y c.mass','Motor'))
            self.motorNameBox.currentIndexChanged.connect(self.motorChange)
            self.motor=str(self.motorNameBox.currentText())
            
            
        self.table.horizontalHeader().setVisible(True)
        self.table.setAlternatingRowColors(True)
        self.table.resizeColumnsToContents()
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)# no modifiableEditTriggers=QAbstractItemView.editTriggers(QAbstractItemView.NoEditTriggers)
        
        vLayout.addLayout(hLayout1)
        vLayout.addLayout(hLayout2)
        
        MainWidget=QWidget()
        
        MainWidget.setLayout(vLayout)
      
        self.setCentralWidget(MainWidget)
        self.setContentsMargins(1,1,1,1)
        
        if self.parent is not None:
            self.parent.signalMeas.connect(self.Display)
            
        # if self.parent is not None:
        #     self.parent.newMesurment.connect(self.Display)
        self.But_reset.triggered.connect(self.Reset)
        
    def Reset(self):
        self.shoot=0
        self.table.setRowCount(0)
        self.Maxx=[]
        self.Minn=[]
        self.Summ=[]
        self.Mean=[]
        self.Xmax=[]
        self.Ymax=[]
        self.Xcmass=[]
        self.Ycmass=[]
        self.labelsVert=[]
        self.posMotor=[]
        self.SummThre=[]
    def saveF(self):
       
        fname=QtGui.QFileDialog.getSaveFileName(self,"Save Measurements as txt file",self.path)
        self.path=os.path.dirname(str(fname[0]))
        f=open(str(fname[0])+'.txt','w')
        f.write("\n".join(self.TableSauv))
        f.close()
        
    def openF(self) :
        '''
        to do
        '''
        print ('open not done yet')
    
    def ZoomMAX(self):
        self.open_widget(self.winZoomMax)
        self.winZoomMax.SetTITLE('MAX')
        self.winZoomMax.setZoom(self.maxx)
        
    def ZoomSUM(self):
        self.open_widget(self.winZoomSum)
        self.winZoomSum.SetTITLE('Sum')
        self.winZoomSum.setZoom(self.summ)
        
    def ZoomMEAN(self):
        self.open_widget(self.winZoomMean)
        self.winZoomMean.SetTITLE('Mean')
        self.winZoomMean.setZoom(self.moy)    
   
    def ZoomXmax(self):
        self.open_widget(self.winZoomXmax)
        self.winZoomXmax.SetTITLE('x max')
        self.winZoomXmax.setZoom(self.xmax)
        
    def ZoomYmax(self):
        self.open_widget(self.winZoomYmax)
        self.winZoomYmax.SetTITLE('y max')
        self.winZoomYmax.setZoom(self.ymax) 
    
    def ZoomCxmax(self):
        self.open_widget(self.winZoomCymax)
        self.winZoomCxmax.SetTITLE('x center of mass')
        self.winZoomCxmax.setZoom(self.xcmass)   
    
    
    def ZoomCymax(self):
        self.open_widget(self.winZoomCxmax)
        self.winZoomCymax.SetTITLE('y center of mass')
        self.winZoomCymax.setZoom(self.ycmass)
        
    def ZoomSUMThreshold(self):
        self.open_widget(self.winZoomSumThreshold)
        
        self.winZoomSumThreshold.SetTITLE('Sum threshold')
        self.winZoomSumThreshold.setZoom(self.summThre)  
    
    
    def PlotMAX(self):
        self.open_widget(self.winCoupeMax)
        self.winCoupeMax.SetTITLE('Plot Max')
        self.signalTrans['data']=self.Maxx
        self.signalTrans['axis']=self.posMotor
        self.signalTrans['label']=self.label
        
        self.signalPlot.emit(self.signalTrans)
        # self.winCoupeMax.PLOT(self.Maxx,axis=self.posMotor, label=self.label)
    
    def PlotMIN (self):
        self.open_widget(self.winCoupeMin)
        self.winCoupeMin.SetTITLE('Plot Min')
        self.signalTrans['data']=self.Minn
        self.signalTrans['axis']=self.posMotor
        self.signalTrans['label']=self.label
        
        self.signalPlot.emit(self.signalTrans)
        # self.winCoupeMin.PLOT(self.Minn,axis=self.posMotor,label=self.label)
        
    
    def PlotXMAX(self):
        self.open_widget(self.winCoupeXmax)
        self.winCoupeXmax.SetTITLE('Plot  X MAX')
        self.signalTrans['data']=self.Xmax
        self.signalTrans['axis']=self.posMotor
        self.signalTrans['label']=self.label
        
        self.signalPlot.emit(self.signalTrans)
        
        # self.winCoupeXmax.PLOT(self.Xmax,axis=self.posMotor,label=self.label)
    
    def PlotYMAX(self):
        self.open_widget(self.winCoupeYmax)
        self.winCoupeYmax.SetTITLE('Plot  Y MAX')
        self.signalTrans['data']=self.Ymax
        self.signalTrans['axis']=self.posMotor
        self.signalTrans['label']=self.label
        
        self.signalPlot.emit(self.signalTrans)
        # self.winCoupeYmax.PLOT(self.Ymax,axis=self.posMotor,label=self.label)
     
        
    def PlotSUM(self):
        self.open_widget(self.winCoupeSum)
        self.winCoupeSum.SetTITLE('Plot Sum')
        self.signalTrans['data']=self.Summ
        self.signalTrans['axis']=self.posMotor
        self.signalTrans['label']=self.label
        
        self.signalPlot.emit(self.signalTrans)
        # self.winCoupeSum.PLOT(self.Summ,axis=self.posMotor,label=self.label)
    
    def PlotMEAN (self):
        self.open_widget(self.winCoupeMean)
        self.winCoupeMean.SetTITLE('Plot Mean')
        self.signalTrans['data']=self.Mean
        self.signalTrans['axis']=self.posMotor
        self.signalTrans['label']=self.label
        
        self.signalPlot.emit(self.signalTrans)
        # self.winCoupeMean.PLOT(self.Mean,axis=self.posMotor,label=self.label)
        
    def PlotXCMASS (self):
        self.open_widget(self.winCoupeXcmass)
        self.winCoupeXcmass.SetTITLE('Plot x center of mass')
        self.signalTrans['data']=self.Xcmass
        self.signalTrans['axis']=self.posMotor
        self.signalTrans['label']=self.label
        
        self.signalPlot.emit(self.signalTrans)
        # self.winCoupeXcmass.PLOT(self.Xcmass,axis=self.posMotor,label=self.label)
    
    def PlotYCMASS (self):
        self.open_widget(self.winCoupeYcmass)
        self.winCoupeYcmass.SetTITLE('Plot Y center of mass')
        self.signalTrans['data']=self.Ycmass
        self.signalTrans['axis']=self.posMotor
        self.signalTrans['label']=self.label
        
        self.signalPlot.emit(self.signalTrans)
        # self.winCoupeYcmass.PLOT(self.Xcmass,axis=self.posMotor,label=self.label)    
    
    
    def PlotSUMTHRESHOLD (self) :
        self.open_widget(self.winCoupeSumThreshold)
        self.winCoupeSumThreshold.SetTITLE('Plot Sum with Threshold')
        # print('fct',self.SummThre,self.posMotor)
        self.signalTrans['data']=self.SummThre
        self.signalTrans['axis']=self.posMotor
        self.signalTrans['label']=self.label
       
        self.signalPlot.emit(self.signalTrans)
    
    
    def Threshold(self):
        
        threshold, ok=QInputDialog.getInt(self,'Threshold Filter ','Enter thresold value')
        if ok:
            self.ThresholdState=True
            self.threshold=threshold
            self.Reset()
            self.PlotMenu.addAction('Sum Threshold',self.PlotSUMTHRESHOLD)
            self.ZoomMenu.addAction(' Sum  with Threshold',self.ZoomSUMThreshold)
            self.Display(self.data)
        else:
            self.ThresholdState=False
            self.PlotMenu.removeAction('Sum Threshold',self.PlotSUMTHRESHOLD)
            self.ZoomMenu.removeAction(' Sum  with Threshold',self.ZoomSUMThreshold)
            
    def Display(self,data):
        
        self.data=data
        self.maxx=round(data.max(),3)
        self.minn=round(data.min(),3)
        self.summ=round(data.sum(),3)#)
        self.moy=round(data.mean(),3)
        
        (self.xmax,self.ymax)=np.unravel_index(data.argmax(),data.shape)
        #print(self.maxx,data[int(self.xmax),int(self.ymax)])
        (self.xcmass,self.ycmass)=ndimage.center_of_mass(data)
        self.xcmass=round(self.xcmass,3)
        self.ycmass=round(self.ycmass,3)
        self.xs=data.shape[0]
        self.ys=data.shape[1]
        self.table.setRowCount(self.shoot+1)
        self.table.setItem(self.shoot, 0, QTableWidgetItem(str(self.nomFichier)))
        self.table.setItem(self.shoot, 1, QTableWidgetItem(str(self.maxx)))
        self.table.setItem(self.shoot, 2, QTableWidgetItem(str(self.minn)))
        self.table.setItem(self.shoot, 3, QTableWidgetItem(str(self.xmax)))
        self.table.setItem(self.shoot, 4, QTableWidgetItem(str(self.ymax)))
        self.table.setItem(self.shoot, 5, QTableWidgetItem("{:.3e}".format(self.summ)))
        self.table.setItem(self.shoot, 6, QTableWidgetItem(str(self.moy)))
        self.table.setItem(self.shoot, 7, QTableWidgetItem(  (str(self.xs) +'*'+ str(self.ys) ) ))
        self.table.setItem(self.shoot, 8, QTableWidgetItem( str(self.xcmass) ) )
        self.table.setItem(self.shoot, 9, QTableWidgetItem( str(self.ycmass) ) )
        
        
        
        if self.confMot!=None:
            if self.motor=='Motors':
                Posi=self.shoot
                self.label='Shoot'
            else:
                Posi=(self.MOT.position())/self.unitChange
                self.label=self.motor+'('+self.unitName+')'
            # self.table.setItem(self.shoot, 10, QTableWidgetItem( str(Posi ) ) )
            
        else :
            Posi=self.shoot
            self.label='Shoot'
            
        
        
        self.posMotor.append(Posi)    
        self.table.resizeColumnsToContents()
        self.labelsVert.append('%s'% self.shoot)
        
        if self.ThresholdState==True:
            dataCor=np.where(data<self.threshold,0,data)
            self.summThre=round(dataCor.sum(),3)
            self.SummThre.append(self.summThre)
            self.TableSauv.append( '%s,%.1f,%.1f,%i,%i,%.1f,%.3f,%.2f,%.2f,%.2f,%.2f,%.2f,%.2f' % (self.nomFichier,self.maxx,self.minn,self.xmax,self.ymax,self.summ,self.moy,self.xs,self.ys,self.xcmass,self.ycmass,Posi,self.summThre) )
            
            if self.confMot!=None:
                self.table.setColumnCount(12)
                self.table.setHorizontalHeaderLabels(('File','Max','Min','x max','y max','Sum','Mean','Size','x c.mass','y c.mass','Sum Thr','Motor'))
                self.table.setItem(self.shoot, 11, QTableWidgetItem( str(Posi ) ) )
            else :
                self.table.setColumnCount(11)
                self.table.setHorizontalHeaderLabels(('File','Max','Min','x max','y max','Sum','Mean','Size','x c.mass','y c.mass','Sum Thr'))
                self.TableSauv=['file,Max,Min,x Max,y max,Sum,Mean,Size,x c.mass,y c.mass,SumCorr']
            self.table.setItem(self.shoot, 10, QTableWidgetItem( "{:.3e}".format(self.summThre ) ) )
            
            
        else:
            self.TableSauv.append( '%s,%.1f,%.1f,%i,%i,%.1f,%.3f,%.2f,%.2f,%.2f,%.2f,%.2f'% (self.nomFichier,self.maxx,self.minn,self.xmax,self.ymax,self.summ,self.moy,self.xs,self.ys,self.xcmass,self.ycmass,Posi) )
            self.table.setItem(self.shoot, 10, QTableWidgetItem( str(Posi ) ) )
            if self.confMot!=None:
                self.table.setColumnCount(11)
            else :
                self.table.setColumnCount(10)
        
        
        self.table.selectRow(self.shoot)
        self.Maxx.append(self.maxx)
        self.Minn.append(self.minn)
        self.Summ.append(self.summ)
        self.Mean.append(self.moy)
        self.Xmax.append(self.xmax)
        self.Ymax.append(self.ymax)
        self.Xcmass.append(self.xcmass)
        self.Ycmass.append(self.ycmass)
        
        
        self.table.setVerticalHeaderLabels(self.labelsVert)


        #  plot Update plot
        if self.winCoupeMax.isWinOpen==True:
            self.PlotMAX()#(self.Maxx,axis=self.posMotor,symbol=self.symbol,pen=None,label=self.motor)
        if self.winCoupeMin.isWinOpen==True:
            self.PlotMIN()
        if self.winCoupeXmax.isWinOpen==True:
            self.PlotXMAX()
        if self.winCoupeYmax.isWinOpen==True:
            self.PlotYMAX()
        if self.winCoupeSum.isWinOpen==True:
            self.PlotSUM()
        if self.winCoupeMean.isWinOpen==True:
            self.PlotMEAN()
        if self.winCoupeXcmass.isWinOpen==True:
            self.PlotXCMASS()
        if self.winCoupeYcmass.isWinOpen==True:
            self.PlotYCMASS()
        if self.winCoupeSumThreshold.isWinOpen==True:
            self.PlotSUMTHRESHOLD()   
        # update zoom windows  
        
        if self.winZoomMax.isWinOpen==True:
            self.ZoomMAX()
        if self.winZoomSum.isWinOpen==True:
            self.ZoomSUM()
        if self.winZoomMean.isWinOpen==True:
            self.ZoomMEAN()    
            
        if self.winZoomXmax.isWinOpen==True:
            self.ZoomXmaX()
        if self.winZoomYmax.isWinOpen==True:
            self.ZoomYmAX()
        if self.winZoomCxmax.isWinOpen==True:
            self.ZoomCxmaX()
        if self.winZoomCymax.isWinOpen==True:
            self.ZoomCymAX()   
        if self.winZoomSumThreshold.isWinOpen==True:
            self.ZoomSUMThreshold()
             
        self.shoot+=1
      
    def closeEvent(self, event):
        """ when closing the window
        """
        self.isWinOpen=False
        self.shoot=0
        self.TableSauv=['file,Max,Min,x Max,y max,Sum,Mean,Size,x c.mass,y c.mass']
        
        if self.winCoupeMax.isWinOpen==True:
            self.winCoupeMax.close()
        if self.winCoupeMin.isWinOpen==True:
            self.winCoupeMin.close()
        if self.winCoupeXmax.isWinOpen==True:
            self.winCoupeXmax.close()
        if self.winCoupeYmax.isWinOpen==True:
            self.winCoupeYmax.close()
        if self.winCoupeSum.isWinOpen==True:
            self.winCoupeSum.close()
        if self.winCoupeMean.isWinOpen==True:
            self.winCoupeMean.close() 
        if self.winCoupeXcmass.isWinOpen==True:
            self.winCoupeXcmass.close()
        if self.winCoupeYcmass.isWinOpen==True:
            self.winCoupeYcmass.close()
        if self.winCoupeSumThreshold.isWinOpen==True:
            self.winCoupeSumThreshold.close()
        time.sleep(0.1)
        event.accept()  

    def open_widget(self,fene):
        """ ouverture widget suplementaire 
        """

        if fene.isWinOpen==False:
            fene.setup
            fene.isWinOpen=True
            #A=self.geometry()
            #fene.setGeometry(A.left()+A.width(),A.top(),500,A.height())
            fene.show()
        else:
            # fene.activateWindow()
            #fene.raise_()
            fene.showNormal()
            
    def motorChange(self):
        
        self.motor=str(self.motorNameBox.currentText())
        self.stepmotor=float(self.confMot.value(self.motor+"/stepmotor")) 
        if self.motor!='Motors':
            self.MOT=self.motorType.MOTORRSAI(self.motor)

    def unit(self):
        '''
        unit change mot foc
        '''
        self.indexUnit=self.unitBouton.currentIndex()
        
        
        if self.indexUnit==0: #  step
            self.unitChange=1
            self.unitName='step'
            
        if self.indexUnit==1: # micron
            self.unitChange=float((1*self.stepmotor)) 
            self.unitName='um'
        if self.indexUnit==2: #  mm 
            self.unitChange=float((1000*self.stepmotor))
            self.unitName='mm'
        if self.indexUnit==3: #  ps  double passage : 1 microns=6fs
            self.unitChange=float(1*self.stepmotor/0.0066666666) 
            self.unitName='ps'
        if self.indexUnit==4: #  en degres
            self.unitChange=1 *self.stepmotor
            self.unitName='°'    
            
        if self.unitChange==0:
            self.unitChange=1 #avoid /0 
    
if __name__ == "__main__":
    appli = QApplication(sys.argv) 
    appli.setStyleSheet(qdarkstyle.load_stylesheet(qt_api='pyqt6'))
    e = MEAS() 
    e.show()
    appli.exec_()         