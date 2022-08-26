#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Feb 13 16:02:40 2019

@author: juliengautier
"""

import qdarkstyle
from PyQt6.QtCore import pyqtSignal as Signal
from PyQt6 import QtCore,QtGui 
from PyQt6.QtWidgets import QApplication,QCheckBox,QVBoxLayout,QHBoxLayout,QPushButton
from  PyQt6.QtWidgets import QWidget,QLabel,QSpinBox,QLineEdit,QMessageBox,QFileDialog
from PyQt6.QtGui import QIcon 
import sys,os
import numpy as np
import socket as _socket
import pathlib
import time

class OPTION(QWidget):
    
    closeEventVar=QtCore.pyqtSignal(bool) 
    emitChangeScale=QtCore.pyqtSignal(bool) 
    emitChangeRot=QtCore.pyqtSignal(bool)
    def __init__(self,conf=None,name='VISU'):
        
        
        
        super().__init__()
        
        p = pathlib.Path(__file__)
        
        if conf==None:
            self.conf=QtCore.QSettings(str(p.parent / 'confVisu.ini'), QtCore.QSettings.Format.IniFormat)
        else :
            self.conf=conf
        self.name=name
        sepa=os.sep
        self.icon=str(p.parent) + sepa+'icons' +sepa
        self.isWinOpen=False
        self.setStyleSheet(qdarkstyle.load_stylesheet(qt_api='pyqt6'))
       
        self.setWindowTitle('Options Auto Save & visualisation')
        self.setWindowIcon(QIcon(self.icon+'LOA.png'))
        
        # self.stepX=float(self.conf.value(self.name+"/stepX"))
        # self.stepY=float(self.conf.value(self.name+"/stepY"))
        self.shoot=int(self.conf.value(self.name+"/tirNumber"))
        self.setup()
        self.pathAutoSave=self.conf.value(self.name+"/path")
        self.pathBg=self.conf.value(self.name+"/pathBg")
        self.actionButton()
        self.dataBgExist=False
        self.rotateValue=0

        
        
        
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
        self.pathBox=QLineEdit(str(self.conf.value(self.name+"/pathAutoSave")))
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
        self.checkBoxTiff.setChecked(True)
        hbox2.addWidget(self.checkBoxTiff)
        
        self.checkBoxDate=QCheckBox('add date',self)
        self.checkBoxDate.setChecked(False)
        hbox2.addWidget(self.checkBoxDate)
        vbox1.addLayout(hbox3)
        
        hbox4=QHBoxLayout()
        labelTirNumber=QLabel('Next number : ')
        self.checkBoxServer=QCheckBox('Auto',self)
        self.checkBoxServer.setChecked(False)
        hbox4.addWidget(self.checkBoxServer)
        
        self.tirNumberBox=QSpinBox()
        self.tirNumberBox.setMaximum(100000)
        self.tirNumberBox.setValue(self.shoot)
        hbox4.addWidget(labelTirNumber)
        hbox4.addWidget(self.tirNumberBox)
        
        vbox1.addLayout(hbox4)
        
        hbox5=QHBoxLayout()
        self.buttonFileBg=QPushButton('Select Background File : ')
        self.fileBgBox=QLineEdit('bgfile not selected')
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
        self.pathBox.textChanged.connect(self.pathTextChanged)
        self.nameBox.textChanged.connect(self.nameFileChanged)
        self.tirNumberBox.valueChanged.connect(self.TirNumberChange)
        self.buttonFileBg.clicked.connect(self.selectBg)
        #self.fileBgBox.textChanged.connect(self.bgTextChanged)
        self.checkBoxServer.stateChanged.connect(self.checkBoxServerChange)

    def pathTextChanged(self):
        self.pathAutoSave=self.pathBox.text()
        self.conf.setValue(self.name+"/pathAutoSave",str(self.pathAutoSave))
        
    def PathChanged(self) :
       
        self.pathAutoSave=str(QFileDialog.getExistingDirectory(self,"Select Directory",self.pathAutoSave))
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
        
    
    # def rotateChange(self):
    #     self.rotateValue=int(self.rotate.value())
        
    
    
    def selectBg(self):
        
        fname=QFileDialog.getOpenFileName(self,"Select a background file",self.pathBg,"Images (*.txt *.spe *.TIFF *.sif);;Text File(*.txt);;Ropper File (*.SPE);;Andor File(*.sif);; TIFF file(*.TIFF)")
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
            msg.setIcon(QMessageBox.Icon.Critical)
            msg.setText("Wrong file format !")
            msg.setInformativeText("The format of the file must be : .SPE  .TIFF .sif or .txt ")
            msg.setWindowTitle("Warning ...")
            msg.setWindowFlags(QtCore.Qt.WindowType.WindowStaysOnTopHint)
            msg.exec_()
            self.dataBgExist=False
    
        
    def checkBoxServerChange(self):
        
        if self. checkBoxServer.isChecked()==True:
            # print('start number of shot Client')
            self.threadClient=THREADCLIENT(self)
            self.threadClient.start()
            self.threadClient.newShotnumber.connect(self.receiveNewNumber)
        else:
            # print('close client')
            self.threadClient.stopClientThread()
    
    def receiveNewNumber (self,nbShot):
        self.tirNumberBox.setValue(nbShot)
        #print(nbShot)
    
    def closeEvent(self, event):
        """ when closing the window
        """
        self.isWinOpen=False   
        self.closeEventVar.emit(True)
        
class THREADCLIENT(QtCore.QThread):
    
    '''Second thread for controling one acquisition independtly
    '''
    newShotnumber=Signal(int)#QtCore.Signal(int) # signal to send 
    
    def __init__(self, parent):
        
        super(THREADCLIENT,self).__init__(parent)
        self.parent=parent
        self.conf=self.parent.conf
        self.name=self.parent.name
        self.serverHost = str(self.conf.value(self.name+"/server"))
        self.serverPort = str(self.conf.value(self.name+"/serverPort"))
        self.clientSocket= _socket.socket(_socket.AF_INET, _socket.SOCK_STREAM) 
        
        
    def run(self):
        try :
            self.serverHost = str(self.conf.value(self.name+"/server"))
            self.serverPort = str(self.conf.value(self.name+"/serverPort"))
            print(self.serverHost,self.serverPort)
            self.clientSocket.connect((self.serverHost,int(self.serverPort)))
            
            self.ClientIsConnected = True
            print('client connected to server',self.serverHost)
        except:
            self.isConnected = False
            print('Do you start the server?')
            self.ClientIsConnected = False
            self.parent.checkBoxServer.setChecked(False)
            
        
       
        while self.ClientIsConnected == True:
            cmd='numberShoot?'
            self.clientSocket.send(cmd.encode())
            try:
                receiv=self.clientSocket.recv(64500)
                nbshot=int(receiv.decode())
            except:
                self.parent.checkBoxServer.setChecked(False)
            if int(self.parent.tirNumberBox.value()) is not nbshot: # sent signal only when different
                   self.newShotnumber.emit(nbshot)
            time.sleep(0.1)
     
    def stopClientThread(self):
            self.ClientIsConnected=False
            self.clientSocket.close()
     
if __name__ == "__main__":
    appli = QApplication(sys.argv) 
    appli.setStyleSheet(qdarkstyle.load_stylesheet(qt_api='pyqt6'))
    e = OPTION() 
    e.show()
    appli.exec_() 