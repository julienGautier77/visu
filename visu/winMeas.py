#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Feb 10 09:44:07 2019
Window for Measurement
@author: juliengautier
modified 2019/08/13 : add motors RSAI position and zoom windows
"""


import qdarkstyle 
from pyqtgraph.Qt import QtCore,QtGui 
from PyQt5.QtWidgets import QApplication,QVBoxLayout,QHBoxLayout,QPushButton
from PyQt5.QtWidgets import QMenu,QWidget,QTableWidget,QTableWidgetItem,QAbstractItemView,QComboBox
import sys,time,os
import pylab
from PyQt5.QtGui import QIcon
from scipy import ndimage
from visu.WinCut import GRAPHCUT
from visu.winZoom import ZOOM
import pathlib
import numpy as np

class MEAS(QWidget):
    
    def __init__(self,conf=None,name='VISU',confMot=None):
        
        super(MEAS, self).__init__()
        self.setStyleSheet(qdarkstyle.load_stylesheet_pyqt5())
        p = pathlib.Path(__file__)
        if conf==None:
            
            self.conf=QtCore.QSettings(str(p.parent / 'confVisu.ini'), QtCore.QSettings.IniFormat)
        else :
            self.conf =conf
        self.name=name
        sepa=os.sep
        self.confMotPath=None
        self.symbol=False
        if confMot!=None:    
            self.confMotPath=str(p.parent / "fichiersConfig")+sepa+'configMoteurRSAI.ini'
            self.motorListGui=list()
            self.configMot=QtCore.QSettings(self.confMotPath, QtCore.QSettings.IniFormat)
            self.groups=self.configMot.childGroups()
            #print('groups',self.groups,self.confMotPath)
            import  visu.moteurRSAI as RSAI
            self.motorType=RSAI
            self.nbMotors=int(np.size(self.groups))
        
        
        self.icon=str(p.parent) + sepa+'icons' +sepa
        self.isWinOpen=False
        self.setup()
        self.setWindowTitle('MEASUREMENTS')
        self.shoot=0
        self.nomFichier=''
        self.TableSauv=['file,Max,Min,x Max,y max,Sum,Mean,Size,x c.mass,y c.mass']
        
        self.path=self.conf.value(self.name+"/path")
        self.winCoupeMax=GRAPHCUT(conf=self.conf,name=self.name)
        self.winCoupeMin=GRAPHCUT(conf=self.conf,name=self.name)
        self.winCoupeXmax=GRAPHCUT(conf=self.conf,name=self.name)
        self.winCoupeYmax=GRAPHCUT(conf=self.conf,name=self.name)
        self.winCoupeSum=GRAPHCUT(conf=self.conf,name=self.name)
        self.winCoupeMean=GRAPHCUT(conf=self.conf,name=self.name)
        self.winCoupeXcmass=GRAPHCUT(conf=self.conf,name=self.name)
        self.winCoupeYcmass=GRAPHCUT(conf=self.conf,name=self.name)
        
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
        
        self.winZoomMax=ZOOM()
        self.winZoomSum=ZOOM()
        self.winZoomMean=ZOOM()
        self.winZoomXmax=ZOOM()
        self.winZoomYmax=ZOOM()
        self.winZoomCxmax=ZOOM()
        self.winZoomCymax=ZOOM()
        self.maxx=0
        self.summ=0
        self.moy=0
        self.label='Shoot'
        self.setWindowIcon(QIcon(self.icon+'LOA.png'))
        
    def setFile(self,file) :
        self.nomFichier=file
        
    def setup(self):
        
            
        vLayout=QVBoxLayout()
        
        hLayout1=QHBoxLayout()
        
        self.FileMenu=QPushButton('File')
        self.FileMenu2=QPushButton('Plot')
        self.FileMenu3=QPushButton('ZOOM')
        hLayout1.addWidget(self.FileMenu)
        hLayout1.addWidget(self.FileMenu2)
        hLayout1.addWidget(self.FileMenu3)
        menu=QMenu()
        menu.addAction('&Open',self.openF)
        menu.addAction('&Save',self.saveF)
        self.FileMenu.setMenu(menu)
        menu2=QMenu()
        menu2.addAction('max',self.PlotMAX)
        menu2.addAction('min',self.PlotMIN)
        menu2.addAction('x max',self.PlotXMAX)
        menu2.addAction('y max',self.PlotYMAX)
        menu2.addAction('Sum',self.PlotSUM)
        menu2.addAction('Mean',self.PlotMEAN)
        
        menu2.addAction('x center mass',self.PlotXCMASS)
        menu2.addAction('y center mass',self.PlotYCMASS)
        
        
        
        self.FileMenu2.setMenu(menu2)
        
        menu3=QMenu()
        menu3.addAction('max',self.ZoomMAX)
        menu3.addAction('Sum',self.ZoomSUM)
        menu3.addAction('Mean',self.ZoomMEAN)
        menu3.addAction('X max',self.ZoomXmax) 
        menu3.addAction('Y max',self.ZoomYmax)
        menu3.addAction(' X c.of.m',self.ZoomCxmax)
        menu3.addAction(' Y c.of.m',self.ZoomCymax)
        
        self.FileMenu3.setMenu(menu3)
        
        
        
        self.But_reset=QPushButton('Reset')
        hLayout1.addWidget(self.But_reset)
        
        hLayout2=QHBoxLayout()
        self.table=QTableWidget()
        hLayout2.addWidget(self.table)
        
        self.table.setColumnCount(10)
        #self.table.setRowCount(10)
       
        self.table.setHorizontalHeaderLabels(('File','Max','Min','x max','y max','Sum','Mean','Size','x c.mass','y c.mass'))
        
        if self.confMotPath!=None:
            self.motorNameBox=QComboBox()
            self.motorNameBox.addItem('Motors')
            hLayout1.addWidget(self.motorNameBox)
            for mo in range (0,self.nbMotors):
                self.motorNameBox.addItem(self.groups[mo])
            self.table.setColumnCount(11)   
            self.table.setHorizontalHeaderLabels(('File','Max','Min','x max','y max','Sum','Mean','Size','x c.mass','y c.mass','Motor'))
            self.motorNameBox.currentIndexChanged.connect(self.motorChange)
            self.motor=str(self.motorNameBox.currentText())
            
            
        self.table.horizontalHeader().setVisible(True)
        self.table.setAlternatingRowColors(True)
        self.table.resizeColumnsToContents()
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)# no modifiable
        
        vLayout.addLayout(hLayout1)
        vLayout.addLayout(hLayout2)
        self.setLayout(vLayout)
        self.But_reset.clicked.connect(self.Reset)
    
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
        
    
    
    
        
    
    def PlotMAX(self):
        self.open_widget(self.winCoupeMax)
        self.winCoupeMax.SetTITLE('Plot Max')
        self.winCoupeMax.PLOT(self.Maxx,axis=self.posMotor,pen=None,label=self.label)
           
    def PlotMIN (self):
        self.open_widget(self.winCoupeMin)
        self.winCoupeMin.SetTITLE('Plot Min')
        self.winCoupeMin.PLOT(self.Minn,axis=self.posMotor,pen=None,label=self.label)
        
    
    def PlotXMAX(self):
        self.open_widget(self.winCoupeXmax)
        self.winCoupeXmax.SetTITLE('Plot  X MAX')
        self.winCoupeXmax.PLOT(self.Xmax,axis=self.posMotor,pen=None,label=self.label)
    
    def PlotYMAX(self):
        self.open_widget(self.winCoupeYmax)
        self.winCoupeYmax.SetTITLE('Plot  Y MAX')
        self.winCoupeYmax.PLOT(self.Ymax,axis=self.posMotor,pen=None,label=self.label)
     
        
    def PlotSUM(self):
        self.open_widget(self.winCoupeSum)
        self.winCoupeSum.SetTITLE('Plot Sum')
        self.winCoupeSum.PLOT(self.Summ,axis=self.posMotor,pen=None,label=self.label)
    
    def PlotMEAN (self):
        self.open_widget(self.winCoupeMean)
        self.winCoupeMean.SetTITLE('Plot Mean')
        self.winCoupeMean.PLOT(self.Mean,axis=self.posMotor,pen=None,label=self.label)
        
    def PlotXCMASS (self):
        self.open_widget(self.winCoupeXcmass)
        self.winCoupeXcmass.SetTITLE('Plot x center of mass')
        self.winCoupeXcmass.PLOT(self.Xcmass,axis=self.posMotor,pen=None,label=self.label)
    
    def PlotYCMASS (self):
        self.open_widget(self.winCoupeYcmass)
        self.winCoupeYcmass.SetTITLE('Plot Y center of mass')
        self.winCoupeYcmass.PLOT(self.Xcmass,axis=self.posMotor,pen=None,label=self.label)    
         
    def Display(self,data):
        
        self.maxx=round(data.max(),3)
        self.minn=round(data.min(),3)
        self.summ=round(data.sum(),3)
        self.moy=round(data.mean(),3)
        
        (self.xmax,self.ymax)=pylab.unravel_index(data.argmax(),data.shape)
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
        self.table.setItem(self.shoot, 5, QTableWidgetItem(str(self.summ)))
        self.table.setItem(self.shoot, 6, QTableWidgetItem(str(self.moy)))
        self.table.setItem(self.shoot, 7, QTableWidgetItem(  (str(self.xs) +'*'+ str(self.ys) ) ))
        self.table.setItem(self.shoot, 8, QTableWidgetItem( str(self.xcmass) ) )
        self.table.setItem(self.shoot, 9, QTableWidgetItem( str(self.ycmass) ) )
        
        if self.confMotPath!=None:
            if self.motor=='Motors':
                Posi=self.shoot
                self.label='Shoot'
            else:
                Posi=(self.MOT.position())
                self.label=self.motor
            self.table.setItem(self.shoot, 10, QTableWidgetItem( str(Posi ) ) )
            
        else :
            Posi=self.shoot
            self.label='Shoot'
            
        self.posMotor.append(Posi)    
        self.table.resizeColumnsToContents()
        self.labelsVert.append('%s'% self.shoot)
        self.TableSauv.append( '%s,%.1f,%.1f,%i,%i,%.1f,%.3f,%.2f,%.2f,%.2f,%.2f,%.2f' % (self.nomFichier,self.maxx,self.minn,self.xmax,self.ymax,self.summ,self.moy,self.xs,self.ys,self.xcmass,self.ycmass,Posi) )
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
            fene.activateWindow()
            fene.raise_()
            fene.showNormal()
            
    def motorChange(self):
        
        self.motor=str(self.motorNameBox.currentText())
        if self.motor!='Motors':
            self.MOT=self.motorType.MOTORRSAI(self.motor)

    
    
if __name__ == "__main__":
    appli = QApplication(sys.argv) 
    appli.setStyleSheet(qdarkstyle.load_stylesheet_pyqt5())
    e = MEAS() 
    e.show()
    appli.exec_()         