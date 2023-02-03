#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Feb 10 09:44:07 2019
Window for Measurement
@author: juliengautier
modified 2019/08/13 : add motors RSAI position and zoom windows
"""


import qdarkstyle 
from PyQt6 import QtCore 
from PyQt6.QtWidgets import QApplication,QVBoxLayout,QHBoxLayout,QMainWindow
from PyQt6.QtWidgets import QWidget,QTableWidget,QTableWidgetItem,QAbstractItemView
import sys,os
from PyQt6.QtGui import QIcon
import pathlib

class HISTORY(QMainWindow):
    
    def __init__(self,parent=None,conf=None,name='VISU',confMot=None,**kwds):
        
        super().__init__()
        self.parent=parent
        self.setStyleSheet(qdarkstyle.load_stylesheet(qt_api='pyqt6'))
        p = pathlib.Path(__file__)
        sepa=os.sep
        if conf==None:
            self.conf=QtCore.QSettings(str(p.parent / 'confVisu.ini'), QtCore.QSettings.Format.IniFormat)
        else :
            self.conf=conf
        self.confMot=confMot   
        self.name=name
        self.shoot=0
        self.nbHistory=20  # maximum file to  be displayed in history log 
        
        self.icon=str(p.parent) + sepa+'icons' +sepa
        self.isWinOpen=False
        self.setup()
        self.setWindowTitle('History')
        
        self.nomFichier=''
        
        self.path=self.conf.value(self.name+"/path")
        
        self.labelsVert=[]
    
        
        self.setWindowIcon(QIcon(self.icon+'LOA.png'))
        

        
    def setup(self):
        
            
        vLayout=QVBoxLayout()
        
      
        hLayout2=QHBoxLayout()
        self.table=QTableWidget()
        hLayout2.addWidget(self.table)
        
        self.table.setColumnCount(1)
        #self.table.setRowCount(10)
        

            
            
        self.table.horizontalHeader().setVisible(True)
        self.table.setHorizontalHeaderLabels(('File',''))
        self.table.setAlternatingRowColors(True)
        self.table.resizeColumnsToContents()
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)# no modifiable
        
        vLayout.addLayout(hLayout2)
        
        MainWidget=QWidget()
        
        MainWidget.setLayout(vLayout)
      
        self.setCentralWidget(MainWidget)
        self.setContentsMargins(1,1,1,1)
        
        
        self.table.cellDoubleClicked.connect(self.openF)
       
          
         
    def Display(self,file):
        
        
        
        self.table.selectRow(self.shoot)
        
        
        
        
        if self.shoot>=self.nbHistory:
            for i in range  (0,self.shoot+1):  
                
                item = self.table.item(i+1, 0)
                
                self.table.setItem(i, 0, QTableWidgetItem(item))
             
            self.table.setItem(self.shoot-1, 0, QTableWidgetItem(str(file)))
            print('shoot',self.shoot)
        else: 
            self.table.setRowCount(self.shoot+1)
            self.table.setVerticalHeaderLabels(self.labelsVert)
            self.table.setItem(self.shoot, 0, QTableWidgetItem(str(file)))
            self.shoot+=1
            
        self.table.resizeColumnsToContents()
        
    
    def openF(self,row,column):
        item = self.table.item(row, column)
        if self.parent is not None:
            print('parent',self.parent)
            self.parent.OpenF(fileOpen=item.text())
        
    
    def closeEvent(self, event):
        """ when closing the window
        """
        self.isWinOpen=False
        
        
    
if __name__ == "__main__":
    appli = QApplication(sys.argv) 
    appli.setStyleSheet(qdarkstyle.load_stylesheet(qt_api='pyqt6'))
    e = HISTORY() 
    e.show()
    appli.exec_()         