#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Feb 13 16:02:40 2019

@author: juliengautier
"""

import qdarkstyle 
from pyqtgraph.Qt import QtCore,QtGui 
from PyQt5.QtWidgets import QApplication,QCheckBox,QVBoxLayout,QHBoxLayout,QPushButton
from PyQt5.QtWidgets import QWidget,QLabel,QTextEdit,QSpinBox,QLineEdit,QMessageBox
from PyQt5.QtGui import QIcon
import sys,os
import numpy as np

import pathlib
class OPTION(QWidget):
    
    def __init__(self):
        
        super(OPTION, self).__init__()
        p = pathlib.Path(__file__)
        conf=QtCore.QSettings(str(p.parent / 'confVisu.ini'), QtCore.QSettings.IniFormat)
        sepa=os.sep
        self.icon=str(p.parent) + sepa+'icons' +sepa
        self.isWinOpen=False
        self.setStyleSheet(qdarkstyle.load_stylesheet_pyqt5())
       
        self.setWindowTitle('Option Auto Save')
        self.setWindowIcon(QIcon(self.icon+'LOA.png'))
        self.conf =conf

        self.shoot=int(self.conf.value('VISU'+"/tirNumber"))
        self.setup()
        self.pathAutoSave=self.conf.value('VISU'+"/path")
        self.pathBg=self.conf.value('VISU'+"/pathBg")
        self.actionButton()
        self.dataBgExist=False
        
        
        
    def setFile(self,file) :
        
        self.nomFichier=file

    def setup(self):
        
        TogOff=self.icon+'Toggle_Off.svg'
        TogOn=self.icon+'Toggle_On.svg'
        
        
        TogOff=pathlib.Path(TogOff)
        TogOff=pathlib.PurePosixPath(TogOff)
        TogOn=pathlib.Path(TogOn)
        TogOn=pathlib.PurePosixPath(TogOn)
        self.setStyleSheet("QCheckBox::indicator{width: 30px;height: 30px;}""QCheckBox::indicator:unchecked { image : url(%s);}""QCheckBox::indicator:checked { image:  url(%s);}""QCheckBox{font :10pt;}" % (TogOff,TogOn) )
        
        vbox1=QVBoxLayout()
        self.buttonPath=QPushButton('Path : ')
        self.pathBox=QTextEdit(str(self.conf.value('VISU'+"/pathAutoSave")))
        self.pathBox.setMaximumHeight(60)
        hbox1=QHBoxLayout()
        hbox1.addWidget(self.buttonPath)
        hbox1.addWidget(self.pathBox)
        
        vbox1.addLayout(hbox1)
        
        hbox2=QHBoxLayout()
        labelName=QLabel('Name : ')
        self.nameBox=QLineEdit(str(self.conf.value('VISU'+"/nameFile")))
        self.nameBox.setMaximumHeight(30)
        hbox2.addWidget(labelName)
        hbox2.addWidget(self.nameBox)
       
        vbox1.addLayout(hbox2)
        
        hbox3=QHBoxLayout()
        self.checkBoxDate=QCheckBox('add date',self)
        self.checkBoxDate.setChecked(False)
        hbox2.addWidget(self.checkBoxDate)
        vbox1.addLayout(hbox3)
        
        hbox4=QHBoxLayout()
        labelTirNumber=QLabel('Next number : ')
        self.tirNumberBox=QSpinBox()
        self.tirNumberBox.setValue(self.shoot)
        self.tirNumberBox.setMaximum(10000)
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
        
        
        hMainLayout=QHBoxLayout()
        hMainLayout.addLayout(vbox1)
        self.setLayout(hMainLayout)
        
    
    def actionButton(self):
        self.buttonPath.clicked.connect(self.PathChanged)
        self.nameBox.textChanged.connect(self.nameFileChanged)
        self.tirNumberBox.valueChanged.connect(self.TirNumberChange)
        self.buttonFileBg.clicked.connect(self.selectBg)
        
        
    def PathChanged(self) :
       
        self.pathAutoSave=str(QtGui.QFileDialog.getExistingDirectory(self,"Select Directory",self.pathAutoSave))
        self.pathBox.setText(self.pathAutoSave)
        self.conf.setValue("VISU"+"/pathAutoSave",str(self.pathAutoSave))
        
    def nameFileChanged(self):
        self.fileName=self.nameBox.text()
        self.conf.setValue("VISU"+"/nameFile",str(self.fileName))
            
    def TirNumberChange(self):
        self.tirNumber=self.tirNumberBox.value()
        self.conf.setValue("VISU"+"/tirNumber",self.tirNumber)
        self.conf.sync()
    def setTirNumber(self,tirNumber) :
        self.tirNumber=tirNumber
        self.tirNumberBox.setValue(self.tirNumber)
        
    
    
    def selectBg(self):
        
        fname=QtGui.QFileDialog.getOpenFileName(self,"Select a background file",self.pathBg,"Images (*.txt *.spe *.TIFF *.sif);;Text File(*.txt);;Ropper File (*.SPE);;Andor File(*.sif);; TIFF file(*.TIFF)")
        fichier=fname[0]
        ext=os.path.splitext(fichier)[1]
        self.fileBgBox.setText(fichier)
        
        self.conf.setValue("VISU"+"/pathBg",os.path.dirname(fichier))
        
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


if __name__ == "__main__":
    appli = QApplication(sys.argv) 
    appli.setStyleSheet(qdarkstyle.load_stylesheet_pyqt5())
    e = OPTION() 
    e.show()
    appli.exec_() 