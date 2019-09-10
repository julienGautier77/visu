# -*- coding: utf-8 -*-
"""
Created on Tue Aug 13 15:27:31 2019
windows for see max ,mean ,sum in a bigger windows
@author: Salle-Jaune
"""



import qdarkstyle # pip install qdakstyle https://github.com/ColinDuquesnoy/QDarkStyleSheet  sur conda
from PyQt5.QtWidgets import QApplication,QHBoxLayout,QWidget,QLabel
from PyQt5.QtGui import QIcon
import sys,time

import pathlib,os

class ZOOM(QWidget):
    
    def __init__(self,symbol=True,title='Zoom'):
        super(ZOOM, self).__init__()
        p = pathlib.Path(__file__)
        sepa=os.sep
        self.title=title
        self.icon=str(p.parent) + sepa+'icons' +sepa
        self.isWinOpen=False
        self.symbol=symbol
        self.setup()
        self.setWindowTitle(self.title)
        self.setWindowIcon(QIcon(self.icon+'LOA.png'))
        self.setStyleSheet(qdarkstyle.load_stylesheet_pyqt5())
    
    def setup(self):
        hLayout2=QHBoxLayout()
        self.label=QLabel('?')
        self.label.setMinimumHeight(100)
        self.label.setMinimumWidth(400)
        self.label.setMaximumHeight(200)
        self.label.setMaximumWidth(500)
        self.label.setStyleSheet('font :bold  60pt;color: white')
        hLayout2.addWidget(self.label)
        self.setLayout(hLayout2)
        
    def setZoom(self,dat):
        if self.title=='Sum':
            self.label.setText('%.3e' % dat)
        else :
            self.label.setText('%.0f' % dat)
        
        
    def SetTITLE(self,title):
        self.title=title
        self.setWindowTitle(title)
        
        
        
        
    def closeEvent(self, event):
        """ when closing the window
        """
        self.isWinOpen=False
        time.sleep(0.1)
        event.accept()
    
    
if __name__ == "__main__":
    appli = QApplication(sys.argv) 
    appli.setStyleSheet(qdarkstyle.load_stylesheet_pyqt5())
    e = ZOOM()  
    e.show()
    appli.exec_()     