# -*- coding: utf-8 -*-
"""
Created on Fri Oct 30 16:21:09 2020

@author: julien Gautier(LOA)
"""

import qdarkstyle 

from PyQt6 import QtCore 
from PyQt6.QtWidgets import QApplication,QVBoxLayout,QHBoxLayout,QPushButton
from PyQt6.QtWidgets import QWidget,QLabel,QMessageBox,QComboBox,QFileDialog
from PyQt6.QtGui import QIcon

import sys,os
import numpy as np
from visu.andor import SifFile
from PIL import Image
from visu.winspec import SpeFile
import pathlib

class WINMATH(QWidget):
    emitApply=QtCore.pyqtSignal(object) # signal emit when aplly
    
    def __init__(self,parent=None,conf=None,name='VISU'):
        
        super().__init__()
        
        p = pathlib.Path(__file__)
        
        self.data1=[]
        self.data2=[]
        self.parent=parent
        if conf==None:
            self.conf=QtCore.QSettings(str(p.parent / 'confVisu.ini'), QtCore.QSettings.Format.IniFormat)
        else :
            self.conf=conf
        self.name=name
        sepa=os.sep
        self.icon=str(p.parent) + sepa+'icons' +sepa
        self.isWinOpen=False
        self.setStyleSheet(qdarkstyle.load_stylesheet(qt_api='pyqt6'))
       
        self.setWindowTitle('Math operations')
        self.setWindowIcon(QIcon(self.icon+'LOA.png'))
        
        
        self.path=self.conf.value(self.name+"/path")
        self.setup()
        self.actionButton()
        
    def setup(self):
        self.vbox1=QVBoxLayout()
        self.hbox1=QHBoxLayout()
        self.label1=QLabel('Image 1 :',self)
        self.labelFile1=QLabel('..............')
        self.browse1=QPushButton('Browse')
        self.hbox1.addWidget(self.label1)
        self.hbox1.addWidget(self.labelFile1)
        self.hbox1.addWidget(self.browse1)
        
        self.vbox1.addLayout(self.hbox1)
        
        self.labelOperand=QLabel('Operation :')
        self.operandButton=QComboBox()
        self.operandButton.addItem('Add')
        self.operandButton.addItem('Substract')
        self.operandButton.addItem('Multiply')
        self.operandButton.addItem('Divise')
        self.hbox2=QHBoxLayout()
        self.hbox2.addWidget(self.labelOperand)
        self.hbox2.addWidget(self.operandButton)
        self.vbox1.addLayout(self.hbox2)
        
        
        self.hbox3=QHBoxLayout()
        self.label2=QLabel('Image 2 : ',self)
        self.labelFile2=QLabel('..............')
        self.browse2=QPushButton('Browse')
        self.hbox3.addWidget(self.label2)
        self.hbox3.addWidget(self.labelFile2)
        self.hbox3.addWidget(self.browse2)
        
        self.vbox1.addLayout(self.hbox3)
        
        
        self.hbox4=QHBoxLayout()
        self.cancelButt=QPushButton('Cancel',self)
        self.applyButt=QPushButton('Apply',self)
        self.hbox4.addWidget(self.cancelButt)
        self.hbox4.addWidget(self.applyButt)
        self.vbox1.addLayout(self.hbox4)
        self.setLayout(self.vbox1)
    
        
    def actionButton(self):
        self.browse1.clicked.connect(self.openFile1)
        #
        self.browse2.clicked.connect(self.openFile2)
        self.applyButt.clicked.connect(self.apply)
        self.cancelButt.clicked.connect(self.cancel)
        
    def cancel(self)   :
        self.isWinOpen=False 
        self.close()
        
        
    def apply(self):
         
        
        if np.shape(self.data1)==0 or np.shape(self.data2) == 0:
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Icon.Critical)
            msg.setText("Select Files !")
            msg.setInformativeText("Select 2 images files  ")
            msg.setWindowTitle("Warning ...")
            msg.setWindowFlags(QtCore.Qt.WindowType.WindowStaysOnTopHint)
            msg.exec_()
            
            
            
            
        elif len (self.data1) != len(self.data2) :
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Icon.Critical)
            msg.setText("Wrong shape!")
            msg.setInformativeText("The files must have have the same shape  ")
            msg.setWindowTitle("Warning ...")
            msg.setWindowFlags(QtCore.Qt.WindowType.WindowStaysOnTopHint)
            msg.exec_()
            
        else :
            
            if self.operandButton.currentIndex()==0:
                 self.data=self.data1 + self.data2
            if self.operandButton.currentIndex()==1:
                 self.data=self.data1 - self.data2
            if self.operandButton.currentIndex()==2:
                 self.data=self.data1 * self.data2
            if self.operandButton.currentIndex()==3:
                 self.data=self.data1 / self.data2
            
            self.emitApply.emit(self.data)
            
            
    def openFile1(self):
        
        (self.data1,file1)=self.OpenF()
        self.labelFile1.setText(file1)
        
    def openFile2(self):
        
        (self.data2,file2)=self.OpenF()
        self.labelFile2.setText(file2)    
        
    def OpenF(self,fileOpen=False):
        #open file in txt spe TIFF sif jpeg png  format
        fileOpen=fileOpen
        
        if fileOpen==False:
            
            chemin=self.conf.value(self.name+"/path")
            fname=QFileDialog.getOpenFileName(self,"Open File",chemin,"Images (*.txt *.spe *.TIFF *.sif *.tif);;Text File(*.txt);;Ropper File (*.SPE);;Andor File(*.sif);; TIFF file(*.TIFF)")
            
            fichier=fname[0]
            self.openedFiles=fichier

          
                
                
        else:
            fichier=str(fileOpen)
            
        ext=os.path.splitext(fichier)[1]
        
        if ext=='.txt': # text file
            data=np.loadtxt(str(fichier))
        elif ext=='.spe' or ext=='.SPE': # SPE file
            dataSPE=SpeFile(fichier)
            data1=dataSPE.data[0]#.transpose() # first frame
            data=data1#np.flipud(data1)
        elif ext=='.TIFF' or ext=='.tif' or ext=='.Tiff' or ext=='.jpg' or ext=='.JPEG' or ext=='.png': # tiff File
            dat=Image.open(fichier)
            data=np.array(dat)
            data=np.rot90(data,3)
        elif ext=='.sif': 
            sifop=SifFile()
            im=sifop.openA(fichier)
            data=np.rot90(im,3)
#            self.data=self.data[250:495,:]
        else :
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Critical)
            msg.setText("Wrong file format !")
            msg.setInformativeText("The format of the file must be : .SPE  .TIFF .sif  png jpeg or .txt ")
            msg.setWindowTitle("Warning ...")
            msg.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint)
            msg.exec_()
            
        chemin=os.path.dirname(fichier)
        self.conf.setValue(self.name+"/path",chemin)
        self.conf.setValue(self.name+"/lastFichier",os.path.split(fichier)[1])
        
        nomFichier=os.path.split(fichier)[1]
        
        return(data,nomFichier)
        
    
    def closeEvent(self, event):
        """ when closing the window
        """
        self.isWinOpen=False   
        event.accept()
          
        
if __name__ == "__main__":
    appli = QApplication(sys.argv) 
    appli.setStyleSheet(qdarkstyle.load_stylesheet(qt_api='pyqt6'))
    e = WINMATH()
    e.show()
    appli.exec_()        
        
        
        
