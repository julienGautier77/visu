#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Feb 13 16:02:40 2019

@author: juliengautier
"""

import qdarkstyle 
from pyqtgraph.Qt import QtCore,QtGui 
from PyQt5.QtWidgets import QApplication,QCheckBox,QVBoxLayout,QHBoxLayout,QPushButton,QDoubleSpinBox
from PyQt5.QtWidgets import QWidget,QLabel,QTextEdit,QSpinBox,QLineEdit,QMessageBox
from PyQt5.QtGui import QIcon
import sys,os
import numpy as np

import pathlib

class OPTION(QWidget):
    
    closeEventVar=QtCore.pyqtSignal(bool) 
    
    def __init__(self,conf=None,name='VISU'):
        
        
        
        super(OPTION, self).__init__()
        
        p = pathlib.Path(__file__)
        
        if conf==None:
            self.conf=QtCore.QSettings(str(p.parent / 'confVisu.ini'), QtCore.QSettings.IniFormat)
        else :
            self.conf=conf
        self.name=name
        sepa=os.sep
        self.icon=str(p.parent) + sepa+'icons' +sepa
        self.isWinOpen=False
        self.setStyleSheet(qdarkstyle.load_stylesheet_pyqt5())
       
        self.setWindowTitle('Options Auto Save & visualisation')
        self.setWindowIcon(QIcon(self.icon+'LOA.png'))
        
        self.stepX=float(self.conf.value(self.name+"/stepX"))
        self.stepY=float(self.conf.value(self.name+"/stepY"))
        self.shoot=int(self.conf.value(self.name+"/tirNumber"))
        self.setup()
        self.pathAutoSave=self.conf.value(self.name+"/path")
        self.pathBg=self.conf.value(self.name+"/pathBg")
        self.actionButton()
        self.dataBgExist=False
        

        
        
        
    def setFile(self,file) :
        
        self.nomFichier=file

    def setup(self):
        
        TogOff=self.icon+'Toggle_Off.png'
        TogOn=self.icon+'Toggle_On.png'
        
        
        TogOff=pathlib.Path(TogOff)
        TogOff=pathlib.PurePosixPath(TogOff)
        TogOn=pathlib.Path(TogOn)
        TogOn=pathlib.PurePosixPath(TogOn)
        self.setStyleSheet("QCheckBox::indicator{width: 30px;height: 30px;}""QCheckBox::indicator:unchecked { image : url(%s);}""QCheckBox::indicator:checked { image:  url(%s);}""QCheckBox{font :10pt;}" % (TogOff,TogOn) )
        
        vbox1=QVBoxLayout()
        self.buttonPath=QPushButton('Path : ')
        self.pathBox=QTextEdit(str(self.conf.value(self.name+"/pathAutoSave")))
        self.pathBox.setMaximumHeight(60)
        hbox1=QHBoxLayout()
        hbox1.addWidget(self.buttonPath)
        hbox1.addWidget(self.pathBox)
        
        vbox1.addLayout(hbox1)
        
        hbox2=QHBoxLayout()
        labelName=QLabel('Name : ')
        self.nameBox=QLineEdit(str(self.conf.value(self.name+"/nameFile")))
        self.nameBox.setMaximumHeight(30)
        hbox2.addWidget(labelName)
        hbox2.addWidget(self.nameBox)
       
        vbox1.addLayout(hbox2)
        
        hbox3=QHBoxLayout()
        
         
        self.checkBoxTiff=QCheckBox('Save as TIFF',self)
        self.checkBoxTiff.setChecked(False)
        hbox2.addWidget(self.checkBoxTiff)
        
        self.checkBoxDate=QCheckBox('add date',self)
        self.checkBoxDate.setChecked(False)
        hbox2.addWidget(self.checkBoxDate)
        vbox1.addLayout(hbox3)
        
        hbox4=QHBoxLayout()
        labelTirNumber=QLabel('Next number : ')
        self.tirNumberBox=QSpinBox()
        self.tirNumberBox.setMaximum(10000)
        self.tirNumberBox.setValue(self.shoot)
        hbox4.addWidget(labelTirNumber)
        hbox4.addWidget(self.tirNumberBox)
        
        vbox1.addLayout(hbox4)
        
        hbox5=QHBoxLayout()
        self.buttonFileBg=QPushButton('Select Background File : ')
        self.fileBgBox=QTextEdit('bgfile not selected')
        self.fileBgBox.setMaximumHeight(60)
        hbox5=QHBoxLayout()
        hbox5.addWidget(self.buttonFileBg)
        hbox5.addWidget(self.fileBgBox)
        
        vbox1.addLayout(hbox5)
        
        hbox6=QHBoxLayout()
        self.checkBoxAxeScale=QCheckBox('Scale Factor : ',self)
        
        self.checkBoxAxeScale.setChecked(False)
        hbox6.addWidget(self.checkBoxAxeScale)
        
        
        self.checkBoxStepX=QLabel('X axe (Pixel/um) : ')
        self.stepXBox=QDoubleSpinBox()
        self.stepXBox.setMaximum(10000)
        self.stepXBox.setValue(self.stepX)
        hbox6.addWidget(self.checkBoxStepX)
        hbox6.addWidget(self.stepXBox)
        
        self.checkBoxStepY=QLabel('Y axe (Pixel/um) : ')
        self.stepYBox=QDoubleSpinBox()
        self.stepYBox.setMaximum(10000)
        self.stepYBox.setValue(self.stepY)
        hbox6.addWidget(self.checkBoxStepY)
        hbox6.addWidget(self.stepYBox)
        
        vbox1.addLayout(hbox6)
        
        hbox7=QHBoxLayout()
        self.checkBoxFwhm=QCheckBox('FWHM ',self)
        
        self.checkBoxFwhm.setChecked(False)
        hbox7.addWidget(self.checkBoxFwhm)
        vbox1.addLayout(hbox7)
        
        hMainLayout=QHBoxLayout()
        hMainLayout.addLayout(vbox1)
        self.setLayout(hMainLayout)
        
    
    def actionButton(self):
        self.buttonPath.clicked.connect(self.PathChanged)
        self.nameBox.textChanged.connect(self.nameFileChanged)
        self.tirNumberBox.valueChanged.connect(self.TirNumberChange)
        self.buttonFileBg.clicked.connect(self.selectBg)
        self.stepXBox.valueChanged.connect(self.stepXChange)
        self.stepYBox.valueChanged.connect(self.stepYChange)
        
    def stepXChange(self) :
        self.stepX=self.stepXBox.value()
        self.conf.setValue(self.name+"/stepX",self.stepX)
        
        
    def stepYChange(self) :
        self.stepY=self.stepYBox.value()
        self.conf.setValue(self.name+"/stepY",self.stepY)

        
    def PathChanged(self) :
       
        self.pathAutoSave=str(QtGui.QFileDialog.getExistingDirectory(self,"Select Directory",self.pathAutoSave))
        self.pathBox.setText(self.pathAutoSave)
        self.conf.setValue(self.name+"/pathAutoSave",str(self.pathAutoSave))
        
    def nameFileChanged(self):
        self.fileName=self.nameBox.text()
        self.conf.setValue(self.name+"/nameFile",str(self.fileName))
            
    def TirNumberChange(self):
        self.tirNumber=self.tirNumberBox.value()
        self.conf.setValue(self.name+"/tirNumber",self.tirNumber)
        self.conf.sync()
        
    def setTirNumber(self,tirNumber) :
        self.tirNumber=tirNumber
        self.tirNumberBox.setValue(self.tirNumber)
        
    
    
    def selectBg(self):
        
        fname=QtGui.QFileDialog.getOpenFileName(self,"Select a background file",self.pathBg,"Images (*.txt *.spe *.TIFF *.sif);;Text File(*.txt);;Ropper File (*.SPE);;Andor File(*.sif);; TIFF file(*.TIFF)")
        fichier=fname[0]
        ext=os.path.splitext(fichier)[1]
        self.fileBgBox.setText(fichier)
        
        self.conf.setValue(self.name+"/pathBg",os.path.dirname(fichier))
        
        self.dataBgExist=True
        
        if ext=='.txt': # text file
            self.dataBg=np.loadtxt(str(fichier))
        elif ext=='.spe' or ext=='.SPE': # SPE file
            from winspec import SpeFile
            dataSPE=SpeFile(fichier)
            data1=dataSPE.data[0]#.transpose() # first frame
            self.dataBg=data1#np.flipud(data1)
        elif ext=='.TIFF':# tiff File
            from PIL import Image
            dat=Image.open(fichier)
            self.dataBg=np.array(dat)
        elif ext=='.sif': 
            from andor import SifFile
            sifop=SifFile()
            im=sifop.openA(fichier)
            self.dataBg=np.rot90(im,3)
            
        else :
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Critical)
            msg.setText("Wrong file format !")
            msg.setInformativeText("The format of the file must be : .SPE  .TIFF .sif or .txt ")
            msg.setWindowTitle("Warning ...")
            msg.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint)
            msg.exec_()
            self.dataBgExist=False
        
    def closeEvent(self, event):
        """ when closing the window
        """
        self.isWinOpen=False   
        self.closeEventVar.emit(True)
        


if __name__ == "__main__":
    appli = QApplication(sys.argv) 
    appli.setStyleSheet(qdarkstyle.load_stylesheet_pyqt5())
    e = OPTION() 
    e.show()
    appli.exec_() 