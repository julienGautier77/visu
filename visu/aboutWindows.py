#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Apr 12 21:39:01 2021

@author: juliengautier
"""


from PyQt6.QtWidgets import QApplication,QVBoxLayout,QWidget
from PyQt6.QtWidgets import QLabel
from PyQt6.QtGui import QIcon

from PyQt6.QtCore import Qt
from pyqtgraph.Qt.QtGui import QIcon
import visu
import pathlib,os,sys
import qdarkstyle
__version__=visu.__version__
__author__=visu.__author__


class ABOUT(QWidget):
    
    def __init__(self,file=None,path=None,**kwds):
        
        super().__init__()
        self.version=__version__
        p = pathlib.Path(__file__)
        sepa=os.sep
        self.title="About Visualization"
        self.icon=str(p.parent) + sepa+'icons' +sepa
        self.isWinOpen=False
        self.setWindowTitle(self.title)
        self.setWindowIcon(QIcon(self.icon+'LOA.png'))
        self.setStyleSheet(qdarkstyle.load_stylesheet_pyqt5())
        self.setup()
        
    def setup(self):
        hMainLayout=QVBoxLayout()
        img=self.icon+'LOA.png'
        
        text1=QLabel('Visualization  Version :  '+self.version)
        text1.setStyleSheet("font:22pt")
        text1.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        text2=QLabel("<a href=\"https://loa.ensta-paris.fr/fr/accueil/\">Laboratoire d'optique Appliquée</a>")
        text2.setAlignment(Qt.AlignCenter)
        
        text2.setOpenExternalLinks(True)
        text2.setTextFormat(Qt.RichText)
        
        text3=QLabel(__author__)
        text3.setAlignment(Qt.AlignCenter)
        text31=QLabel("<a href=\"https://github.com/julienGautier77/visu/wiki/How--to-use-Visu\">visit on GitHub</a>")
        text31.setOpenExternalLinks(True)
        text31.setTextFormat(Qt.RichText)
        
        
        text4=QLabel()
        text4.setStyleSheet("QLabel:!pressed{border-image: url(%s);background-color: transparent ;border-color: green;}""QLabel:pressed{image: url(%s);background-color: gray ;border-color: gray}"% (img,img))           
        text4.setMaximumWidth(60)
        text4.setMaximumHeight(60)
        text4.setAlignment(Qt.AlignCenter)
        
        hMainLayout.addWidget(text1)
        hMainLayout.addWidget(text2)
        hMainLayout.addWidget(text3)
        hMainLayout.addWidget(text31)
        hMainLayout.addWidget(text4)
        self.setLayout(hMainLayout)
        
   
    def closeEvent(self, event):
        """ when closing the window
        """
        self.isWinOpen=False
        
        event.accept()
        
if __name__ == "__main__":
    appli = QApplication(sys.argv) 
    appli.setStyleSheet(qdarkstyle.load_stylesheet(qt_api='pyqt6'))
    e = ABOUT()  
    e.show()
    appli.exec_()     
    