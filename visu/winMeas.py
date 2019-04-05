#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Feb 10 09:44:07 2019
Window for Measurement
@author: juliengautier
"""


import qdarkstyle 
from pyqtgraph.Qt import QtCore,QtGui 
from PyQt5.QtWidgets import QApplication,QVBoxLayout,QHBoxLayout,QPushButton
from PyQt5.QtWidgets import QMenu,QWidget,QTableWidget,QTableWidgetItem,QAbstractItemView
import sys,time,os
import numpy as np
import pylab
from PyQt5.QtGui import QIcon
from scipy import ndimage
from visu.WinCut import GRAPHCUT
import pathlib


class MEAS(QWidget):
    
    def __init__(self):
        
        super(MEAS, self).__init__()
        p = pathlib.Path(__file__)
        conf=QtCore.QSettings(str(p.parent / 'confVisu.ini'), QtCore.QSettings.IniFormat)
        sepa=os.sep
        
        self.icon=str(p.parent) + sepa+'icons' +sepa
        self.isWinOpen=False
        self.setup()
        self.setWindowTitle('MEASUREMENTS')
        self.shoot=0
        self.nomFichier=''
        self.TableSauv=['file,Max,Min,x Max,y max,Sum,Mean,Size,x c.mass,y c.mass']
        self.conf =conf
        self.path=self.conf.value('VISU'+"/path")
        self.winCoupeMax=GRAPHCUT()
        self.winCoupeMin=GRAPHCUT()
        self.winCoupeXmax=GRAPHCUT()
        self.winCoupeYmax=GRAPHCUT()
        self.winCoupeSum=GRAPHCUT()
        self.winCoupeMean=GRAPHCUT()
        self.winCoupeXcmass=GRAPHCUT()
        self.winCoupeYcmass=GRAPHCUT()
        self.setStyleSheet(qdarkstyle.load_stylesheet_pyqt5())
        self.Maxx=[]
        self.Minn=[]
        self.Summ=[]
        self.Mean=[]
        self.Xmax=[]
        self.Ymax=[]
        self.Xcmass=[]
        self.Ycmass=[]
        self.labelsVert=[]
        self.setWindowIcon(QIcon(self.icon+'LOA.png'))
        
    def setFile(self,file) :
        self.nomFichier=file
        
    def setup(self):
        
        vLayout=QVBoxLayout()
        
        hLayout1=QHBoxLayout()
        
        self.FileMenu=QPushButton('File')
        self.FileMenu2=QPushButton('Plot')
        hLayout1.addWidget(self.FileMenu)
        hLayout1.addWidget(self.FileMenu2)
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
        
        
        
        hLayout2=QHBoxLayout()
        self.table=QTableWidget()
        hLayout2.addWidget(self.table)
        
        self.table.setColumnCount(10)
        #self.table.setRowCount(10)
       
        self.table.setHorizontalHeaderLabels(('File','Max','Min','x max','y max','Sum','Mean','Size','x c.mass','y c.mass'))
        self.table.horizontalHeader().setVisible(True)
        self.table.setAlternatingRowColors(True)
        self.table.resizeColumnsToContents()
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)# no modifiable
        
        vLayout.addLayout(hLayout1)
        vLayout.addLayout(hLayout2)
        self.setLayout(vLayout)
         
    def saveF(self):
       
        fname=QtGui.QFileDialog.getSaveFileName(self,"Save Measurements as txt file",self.path)
        
        self.path=os.path.dirname(str(fname[0]))
        #mat=np.array(self.TableSauv)
        #print('mat=',mat)
#        with open('myfile','w',)as f:
#            json.dump(self.TableSauv,f)
        f=open(str(fname[0])+'.txt','w')
        f.write("\n".join(self.TableSauv))
        f.close()
        
    def openF(self) :
        print ('open not done')
    

    def PlotMAX(self):
        self.open_widget(self.winCoupeMax)
        self.winCoupeMax.SetTITLE('Plot Max')
        self.winCoupeMax.PLOT(self.Maxx)
           
    def PlotMIN (self):
        self.open_widget(self.winCoupeMin)
        self.winCoupeMin.SetTITLE('Plot Min')
        self.winCoupeMin.PLOT(self.Minn)
        
    
    def PlotXMAX(self):
        self.open_widget(self.winCoupeXmax)
        self.winCoupeXmax.SetTITLE('Plot  X MAX')
        self.winCoupeXmax.PLOT(self.Xmax)
    
    def PlotYMAX(self):
        self.open_widget(self.winCoupeYmax)
        self.winCoupeYmax.SetTITLE('Plot  Y MAX')
        self.winCoupeYmax.PLOT(self.Ymax)
     
        
    def PlotSUM(self):
        self.open_widget(self.winCoupeSum)
        self.winCoupeSum.SetTITLE('Plot Sum')
        self.winCoupeSum.PLOT(self.Summ)
    
    def PlotMEAN (self):
        self.open_widget(self.winCoupeMean)
        print('plot mean')
        self.winCoupeMean.SetTITLE('Plot Mean')
        print('pppp')
        self.winCoupeMean.PLOT(self.Mean)
        print('ppeeeepp')
        
    def PlotXCMASS (self):
        self.open_widget(self.winCoupeXcmass)
        self.winCoupeXcmass.SetTITLE('Plot x center of mass')
        self.winCoupeXcmass.PLOT(self.Xcmass)
    
    def PlotYCMASS (self):
        self.open_widget(self.winCoupeYcmass)
        self.winCoupeYcmass.SetTITLE('Plot Y center of mass')
        self.winCoupeYcmass.PLOT(self.Xcmass)    
        
        
    def Display(self,data):
        
        maxx=round(data.max(),3)
        minn=round(data.min(),3)
        summ=round(data.sum(),3)
        moy=round(data.mean(),3)
        
        (xmax,ymax)=pylab.unravel_index(data.argmax(),data.shape)
        (xcmass,ycmass)=ndimage.center_of_mass(data)
        xcmass=round(xcmass,3)
        ycmass=round(ycmass,3)
        xs=data.shape[0]
        ys=data.shape[1]
        self.table.setRowCount(self.shoot+1)
        self.table.setItem(self.shoot, 0, QTableWidgetItem(str(self.nomFichier)))
        self.table.setItem(self.shoot, 1, QTableWidgetItem(str(maxx)))
        self.table.setItem(self.shoot, 2, QTableWidgetItem(str(minn)))
        self.table.setItem(self.shoot, 3, QTableWidgetItem(str(xmax)))
        self.table.setItem(self.shoot, 4, QTableWidgetItem(str(ymax)))
        self.table.setItem(self.shoot, 5, QTableWidgetItem(str(summ)))
        self.table.setItem(self.shoot, 6, QTableWidgetItem(str(moy)))
        self.table.setItem(self.shoot, 7, QTableWidgetItem(  (str(xs) +'*'+ str(ys) ) ))
        self.table.setItem(self.shoot, 8, QTableWidgetItem( str(xcmass) ) )
        self.table.setItem(self.shoot, 9, QTableWidgetItem( str(ycmass) ) )
        
        self.table.resizeColumnsToContents()
        self.labelsVert.append('%s'% self.shoot)
        self.TableSauv.append( '%s,%.1f,%.1f,%i,%i,%.1f,%.3f,%.2f,%.2f,%.2f,%.2f' % (self.nomFichier,maxx,minn,xmax,ymax,summ,moy,xs,ys,xcmass,ycmass) )
        self.Maxx.append(maxx)
        self.Minn.append(minn)
        self.Summ.append(summ)
        self.Mean.append(moy)
        self.Xmax.append(xmax)
        self.Ymax.append(ymax)
        
        self.Xcmass.append(xcmass)
        self.Ycmass.append(ycmass)
        
        
        self.table.setVerticalHeaderLabels(self.labelsVert)



        #  plot Update 
        if self.winCoupeMax.isWinOpen==True:
            self.winCoupeMax.PLOT(self.Maxx)
        if self.winCoupeMin.isWinOpen==True:
            self.winCoupeMin.PLOT(self.Minn)
            
        if self.winCoupeXmax.isWinOpen==True:
            self.winCoupeXmax.PLOT(self.Xmax)
        if self.winCoupeYmax.isWinOpen==True:
            self.winCoupeYmax.PLOT(self.Ymax)   
        if self.winCoupeSum.isWinOpen==True:
            self.winCoupeSum.PLOT(self.Summ)
            
        if self.winCoupeMean.isWinOpen==True:
            self.winCoupeMean.PLOT(self.Mean)
        
        if self.winCoupeXcmass.isWinOpen==True:
            self.winCoupeXcmass.PLOT(self.Xcmass)
        if self.winCoupeYcmass.isWinOpen==True:
            self.winCoupeYcmass.PLOT(self.Ycmass)
            
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
            A=self.geometry()
            fene.setGeometry(A.left()+A.width(),A.top(),500,A.height())
            fene.show()
        else:
            fene.activateWindow()
            fene.raise_()
            fene.showNormal()
    
    
    
if __name__ == "__main__":
    appli = QApplication(sys.argv) 
    appli.setStyleSheet(qdarkstyle.load_stylesheet_pyqt5())
    e = MEAS() 
    e.show()
    appli.exec_()         