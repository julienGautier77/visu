#!/usr/bin/env python3
# -*- coding: utf-8 -*-


"""
Created on Mon May  6 11:24:23 2019
Windows for display FFT
@author: juliengautier


"""

from PyQt5.QtWidgets import QApplication,QVBoxLayout,QHBoxLayout,QWidget
from pyqtgraph.Qt import QtCore
from PyQt5.QtGui import QIcon
import sys,os
import numpy as np
import qdarkstyle # pip install qdakstyle https://github.com/ColinDuquesnoy/QDarkStyleSheet  sur conda
import pathlib
from visu import SEE



class WINFFT(QWidget):
    
    def __init__(self,nbcam):
        
        super(WINFFT, self).__init__()
        self.nbcam=nbcam
        p = pathlib.Path(__file__)
        conf=QtCore.QSettings(str(p.parent / 'confVisu.ini'), QtCore.QSettings.IniFormat)
        sepa=os.sep
        self.icon=str(p.parent) + sepa+'icons' +sepa
        self.confCCD = conf
        self.isWinOpen=False
        self.setWindowTitle('FFT')
        self.setWindowIcon(QIcon(self.icon+'LOA.png'))
        self.setStyleSheet(qdarkstyle.load_stylesheet_pyqt5())
        self.setup()      
        
    
    def setup(self):
                
        self.visualisationFFT=SEE()
        vbox3=QVBoxLayout() 
        vbox3.addWidget(self.visualisationFFT)
        hMainLayout=QHBoxLayout()
        hMainLayout.addLayout(vbox3)
        self.setLayout(hMainLayout)
    
    
    def Display(self,data):
        self.data=data
        if self.data.ndim==2:
            datafft=np.fft.fft2(np.array(self.data))
            self.norm=abs(np.fft.fftshift(datafft))#datafft*datafft.conj()
            self.norm=np.log10(1+self.norm)
            self.visualisationFFT.newDataReceived(self.norm)
     
           
    def closeEvent(self, event):
        """ when closing the window
        """
        self.isWinOpen=False
        event.accept()
     
       
if __name__ == "__main__":
    appli = QApplication(sys.argv) 
    appli.setStyleSheet(qdarkstyle.load_stylesheet_pyqt5())
    e = WINFFT(nbcam='VISU')  
    e.show()
    appli.exec_()    
        
        