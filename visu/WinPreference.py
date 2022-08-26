#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Feb 13 16:02:40 2019

@author: juliengautier
"""

import qdarkstyle 
from PyQt6 import QtCore
from PyQt6.QtWidgets import QApplication,QCheckBox,QVBoxLayout,QHBoxLayout,QDoubleSpinBox
from PyQt6.QtWidgets import QWidget,QLabel,QSpinBox,QLineEdit,QComboBox
from PyQt6.QtGui import QIcon
import sys,os

import pathlib

class PREFERENCES(QWidget):
    
    closeEventVar=QtCore.pyqtSignal(bool) 
    emitChangeScale=QtCore.pyqtSignal(bool) 
    emitChangeRot=QtCore.pyqtSignal(bool)
    def __init__(self,conf=None,name='VISU'):
        
        
        
        super().__init__()
        
        p = pathlib.Path(__file__)
        
        if conf==None:
            self.conf=QtCore.QSettings(str(p.parent / 'confVisu.ini'), QtCore.QSettings.Format.IniFormat)
            print(str(p.parent))
        else :
            self.conf=conf
        self.name=name
        sepa=os.sep
        self.icon=str(p.parent) + sepa+'icons' +sepa
        self.isWinOpen=False
        self.setStyleSheet(qdarkstyle.load_stylesheet(qt_api='pyqt6'))
       
        self.setWindowTitle('Preferences visualisation')
        self.setWindowIcon(QIcon(self.icon+'LOA.png'))
        
        self.stepX=float(self.conf.value(self.name+"/stepX"))
        self.stepY=float(self.conf.value(self.name+"/stepY"))
        self.server=str(self.conf.value(self.name+"/server"))
        self.serverPort=str(self.conf.value(self.name+"/serverPort"))
        self.rotateValue=int(self.conf.value(self.name+"/rotation"))

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
        
        vbox1=QVBoxLayout()
        
        hbox1=QHBoxLayout()
        
        
        vbox1.addLayout(hbox1)
        

        
        hbox6=QHBoxLayout()
        self.checkBoxAxeScale=QCheckBox('Scale Factor : ',self)
        
        self.checkBoxAxeScale.setChecked(False)
        hbox6.addWidget(self.checkBoxAxeScale)
        
        
        self.checkBoxStepX=QLabel('X axe (Pixel/um) : ')
        self.stepXBox=QDoubleSpinBox()
        self.stepXBox.setMaximum(10000)
        self.stepXBox.setValue(self.stepX)
        self.stepXBox.setDecimals(4)
        hbox6.addWidget(self.checkBoxStepX)
        hbox6.addWidget(self.stepXBox)
        
        self.checkBoxStepY=QLabel('Y axe (Pixel/um) : ')
        self.stepYBox=QDoubleSpinBox()
        self.stepYBox.setMaximum(10000)
        self.stepYBox.setValue(self.stepY)
        self.stepYBox.setDecimals(4)
        hbox6.addWidget(self.checkBoxStepY)
        hbox6.addWidget(self.stepYBox)
        
        vbox1.addLayout(hbox6)
        
        hbox7=QHBoxLayout()
        self.checkBoxFwhm=QCheckBox('FWHM ',self)
        
        self.checkBoxFwhm.setChecked(False)
        hbox7.addWidget(self.checkBoxFwhm)
        
        labelRotate=QLabel('Img Rotation  90°:')
        
        
        hbox7.addWidget(labelRotate)
        self.rotate=QSpinBox()
        self.rotate.setMaximum(4)
        self.rotate.setValue(self.rotateValue)
        hbox7.addWidget(self.rotate)
        vbox1.addLayout(hbox7)
        
        
        hbox8=QHBoxLayout()
        self.checkBoxFluence=QCheckBox('Fluence ',self)
        
        self.checkBoxFluence.setChecked(False)
        hbox8.addWidget(self.checkBoxFluence)
        
        labelEnergy=QLabel('Energy (mJ):')
        
        
        hbox8.addWidget(labelEnergy)
        self.energy=QDoubleSpinBox()
        self.energy.setDecimals(2)
        self.energy.setMaximum(1000)
        self.energy.setValue(1)
        
        
        hbox8.addWidget(self.energy)
        vbox1.addLayout(hbox8)
        
        
        hbox9=QHBoxLayout()
        
        self.labelPlot=QLabel('Rectangular plot profile')
        
        self.plotRectOpt=QComboBox()
        self.plotRectOpt.setMaximumWidth(80)
        self.plotRectOpt.addItem('Mean')
        self.plotRectOpt.addItem('Sum')
        #self.plotRectOpt.setStyleSheet('font :bold  10pt;color: white')
            # self.labelTrigger=QLabel('Trigger')
            # self.labelTrigger.setMaximumWidth(70)
            # self.labelTrigger.setStyleSheet('font :bold  10pt')
            # self.itrig=self.self.plotRectOpt.currentIndex()
        
        hbox9.addWidget(self.labelPlot)
        hbox9.addWidget(self.plotRectOpt)
        vbox1.addLayout(hbox9)
        
        hbox10=QHBoxLayout()
        self.labelServer=QLabel('IP Server address')
        self.serverIP=QLineEdit(str(self.conf.value(self.name+"/server")))
        hbox10.addWidget(self.labelServer)
        hbox10.addWidget(self.serverIP)
        self.labelPort=QLabel('IP Server port')
        self.serverPortBut=QLineEdit(str(self.conf.value(self.name+"/serverPort")))
        hbox10.addWidget(self.labelPort)
        hbox10.addWidget(self.serverPortBut)
        vbox1.addLayout(hbox10)
        
        hMainLayout=QHBoxLayout()
        hMainLayout.addLayout(vbox1)
        self.setLayout(hMainLayout)
        
    
    def actionButton(self):
       
        self.stepXBox.valueChanged.connect(self.stepXChange)
        self.stepYBox.valueChanged.connect(self.stepYChange)
        self.rotate.valueChanged.connect(self.rotateChange)
        self.serverIP.textChanged.connect(self.serverChange)
        self.serverPortBut.textChanged.connect(self.serverPortChange)
        
    def serverChange(self) :
        self.server=self.serverIP.text()
        self.conf.setValue(self.name+"/server",self.server)
        
    def serverPortChange(self) :
        self.serverPort=self.serverPortBut.text()
        self.conf.setValue(self.name+"/serverPort",self.serverPort)
        
    def stepXChange(self) :
        self.stepX=self.stepXBox.value()
        self.conf.setValue(self.name+"/stepX",self.stepX)
        
        
    def stepYChange(self) :
        self.stepY=self.stepYBox.value()
        self.conf.setValue(self.name+"/stepY",self.stepY)
        
    def checkBoxAxeChange(self):
        self.emitChangeScale.emit(True)
   
        
        
    
    def rotateChange(self):
        self.rotateValue=int(self.rotate.value())
        self.conf.setValue(self.name+"/rotation",self.rotateValue)
        
    def closeEvent(self, event):
        """ when closing the window
        """
        self.isWinOpen=False   
        self.closeEventVar.emit(True)
        


if __name__ == "__main__":
    appli = QApplication(sys.argv) 
    appli.setStyleSheet(qdarkstyle.load_stylesheet(qt_api='pyqt6'))
    e = PREFERENCES() 
    e.show()
    appli.exec_() 