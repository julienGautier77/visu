#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Feb  8 14:46:20 2019
Windows for plot
@author: juliengautier
"""

import pyqtgraph as pg  # pyqtgraph biblio permettent l'affichage 

import qdarkstyle  # pip install qdakstyle https://github.com/ColinDuquesnoy/QDarkStyleSheet  sur conda
from PyQt6.QtWidgets import QApplication, QVBoxLayout, QMainWindow
from PyQt6.QtGui import QIcon
from PyQt6 import QtCore
import os
import sys
import time
from PyQt6.QtCore import pyqtSlot
import numpy as np
import pathlib
import pyqtgraph.opengl as gl


class GRAPH3D(QMainWindow):

    def __init__(self, symbol=True, title='Plot3D', conf=None, name='VISU'):
        super(GRAPH3D, self).__init__()
        p = pathlib.Path(__file__)
        sepa = os.sep
        self.title = title
        self.icon = str(p.parent) + sepa + 'icons' + sepa
        self.left = 100
        self.top = 30
        self.width = 800
        self.height = 800
        self.setGeometry(self.left, self.top, self.width, self.height)
        self.isWinOpen = False
        self.symbol = symbol
        self.name = name
        self.path = None
        self.axisOn = False
        if conf is None:
            self.conf = QtCore.QSettings(str(p.parent / 'confVisu.ini'), QtCore.QSettings.IniFormat)
        else:
            self.conf = conf

        self.setup()
        self.setWindowTitle(self.title)
        self.setWindowIcon(QIcon(self.icon+'LOA.png'))
        self.setStyleSheet(qdarkstyle.load_stylesheet_pyqt5())
        
    def setup(self):
        vLayout = QVBoxLayout()

        #  Add a grid to the view
        self.w = gl.GLViewWidget()
        # g = gl.GLGridItem()
        # g.scale(20,20,1)
        # g.setDepthValue(220)  # draw grid after surfaces since they may be translucent
        # self.w.addItem(g)
        vLayout.addWidget(self.w)
        self.w.setCameraPosition(distance=1000)
        self.setCentralWidget(self.w)
        # self.w.show()
        
    def Plot3D(self, data, axisX=None, axisY=None, symbol=True, pen=True, label=None):
        print('ici plot 3d')
        self.data = data
        self.dimx = np.shape(self.data)[0]
        self.dimy = np.shape(self.data)[1]
        self.pen = pen
        self.axisX = axisX
        self.axisY = axisY
        
        if self.axisX is None or self.axisY is None:
            
            z = self.data  # [:self.dimx,:self.dimy]
            zmax = z.max()
            # zmin = z.min()
            if zmax == 0:
                zmax = 1
            z = z/((zmax))
            
            p1 = gl.GLSurfacePlotItem(z=z, shader='heightColor', computeNormals=False, smooth=False)  # .reshape(50*50,4))
            # p1.shader()['colorMap'] = np.array([0.2, 2, 0.5, 0.2, 1, 1, 0.2, 0, 2])
            p1.scale(1, 1, zmax)
              
            self.w.addItem(p1)
        else:
            print('')
            # create 3D array to pass it to plotting function
# 		vetrs3D = np.zeros([nbv,3])
# 		if vertexes.shape == (nbv,3): vetrs3D = vertexes
# 		else: 
# 			print 'Converting 2D to 3D'
# 			vetrs3D[:,:2] = vertexes
# 		# compute distance to set initial camera pozition
# 		dst = max(vertexes[:,0].max() - vertexes[:,0].min(), vertexes[:,1].max() - vertexes[:,1].min())
# 		view.setCameraPosition(distance=dst)

# 		plt = gl.GLMeshItem(vertexes=vetrs3D, faces=faces, faceColors=colors, drawEdges=drawEdges, smooth=smooth)
            
        # p1.scale(16./49., 16./49., 1.0)
        # p1.translate(-18, 2, 0)
       
    def SetTITLE(self, title):
        self.setWindowTitle(title)
    
    def closeEvent(self, event):
        """ when closing the window
        """
        self.isWinOpen = False
        time.sleep(0.1)
        event.accept()


if __name__ == "__main__":
    z = pg.gaussianFilter(np.random.normal(size=(50, 50)), (1, 1))
    appli = QApplication(sys.argv) 
    appli.setStyleSheet(qdarkstyle.load_stylesheet(qt_api='pyqt6'))
    e = GRAPH3D()
    e.Plot3D(data=z)
    e.show()
    appli.exec_()
