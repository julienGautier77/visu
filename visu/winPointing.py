#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Dec 19 11:43:05 2018
@author: juliengautier

"""

from PyQt6.QtWidgets import QApplication, QVBoxLayout, QHBoxLayout, QWidget, QGridLayout
from PyQt6.QtWidgets import QLabel, QMainWindow, QMessageBox, QFileDialog, QInputDialog, QFrame, QGroupBox
from PyQt6 import QtCore, QtGui 

from PyQt6.QtGui import QAction
from PyQt6.QtGui import QIcon
from PyQt6.QtCore import QThread, pyqtSignal, QTimer, Qt
import sys
import time
import pyqtgraph as pg
import numpy as np
import qdarkstyle
import pylab
import os
from scipy.ndimage.filters import gaussian_filter
import pathlib
from scipy import ndimage
from collections import deque


class PointingWorker(QThread):
    """Thread worker pour les calculs de pointing"""
    results_ready = pyqtSignal(dict)  # Signal avec les résultats calculés
    
    def __init__(self):
        super().__init__()
        self.data = None
        self.stepX = 1
        self.stepY = 1
        self.xini = 0
        self.yini = 0
        self.use_center_of_mass = False
        self.is_running = False
        
    def set_data(self, obje):
        """Définir les nouvelles données à traiter"""
        if not self.is_running:
            self.data = obje[0]
            self.stepX = obje[1]
            self.stepY = obje[2]
            self.xini = obje[3]
            self.yini = obje[4]
            self.is_running = True
            self.start()
    
    def run(self):
        """Calculs effectués dans le thread séparé"""
        if self.data is None:
            self.is_running = False
            return
            
        try:
            # Filtrage gaussien
            dataF = gaussian_filter(self.data, 5)
            
            # Calcul du centre
            if self.use_center_of_mass:
                (xec, yec) = ndimage.center_of_mass(dataF)
                label = 'com'
            else:
                (xec, yec) = pylab.unravel_index(dataF.argmax(), self.data.shape)
                label = 'max'
            
            # Conversion en coordonnées réelles
            xec = (xec + self.xini) * self.stepX
            yec = (yec + self.yini) * self.stepY
            
            # Émettre les résultats
            results = {
                'xec': xec,
                'yec': yec,
                'label': label,
                'stepX': self.stepX,
                'stepY': self.stepY
            }
            self.results_ready.emit(results)
            
        except Exception as e:
            print(f"Erreur dans PointingWorker: {e}")
        finally:
            self.is_running = False


class StatsCard(QFrame):
    """Widget carte pour afficher une statistique"""
    def __init__(self, title, color='white', parent=None):
        super().__init__(parent)
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setStyleSheet(f"""
            QFrame {{
                background-color: #2b2b2b;
                border: 2px solid {color};
                border-radius: 8px;
                padding: 5px;
            }}
        """)
        
        layout = QVBoxLayout()
        layout.setSpacing(2)
        layout.setContentsMargins(5, 5, 5, 5)
        
        # Titre
        self.titleLabel = QLabel(title)
        self.titleLabel.setStyleSheet(f"color: {color}; font: bold 9pt; border: none;")
        self.titleLabel.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.titleLabel.setWordWrap(False)  # Pas de retour à la ligne
        
        # Valeur
        self.valueLabel = QLabel('--')
        self.valueLabel.setStyleSheet(f"color: {color}; font: bold 11pt; border: none;")  # Réduit de 14pt à 11pt
        self.valueLabel.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.valueLabel.setWordWrap(False)  # Pas de retour à la ligne
        
        layout.addWidget(self.titleLabel)
        layout.addWidget(self.valueLabel)
        self.setLayout(layout)
    
    def setValue(self, value):
        """Mettre à jour la valeur affichée"""
        self.valueLabel.setText(str(value))


class WINPOINTING(QMainWindow):
    
    def __init__(self, parent=None, conf=None, name='VISU'):
        
        super().__init__()

        self.name = name
        self.parent = parent
        p = pathlib.Path(__file__)
        if conf is None:
            self.conf = QtCore.QSettings(str(p.parent / 'confVisu.ini'), QtCore.QSettings.Format.IniFormat)
        else:
            self.conf = conf
        
        sepa = os.sep
        self.icon = str(p.parent) + sepa+'icons' + sepa
        self.path = self.conf.value(self.name+"/path")
        self.isWinOpen = False
        self.setWindowTitle('Pointing Stability Monitor')
        self.setWindowIcon(QIcon(self.icon+'LOA.png'))
        self.setStyleSheet(qdarkstyle.load_stylesheet(qt_api='pyqt6'))
        self.left = 100
        self.top = 30
        self.width = 1400
        self.height = 800
        self.setGeometry(self.left, self.top, self.width, self.height)
        self.dimx = 1200
        self.dimy = 900
        self.bloqq = 1
        self.xec = int(self.conf.value(self.name+"/xec")) if self.conf.value(self.name+"/xec") else 0
        self.yec = int(self.conf.value(self.name+"/yec")) if self.conf.value(self.name+"/yec") else 0
        self.r1x = int(self.conf.value(self.name+"/r1x")) if self.conf.value(self.name+"/r1x") else 0
        self.r1y = int(self.conf.value(self.name+"/r1y")) if self.conf.value(self.name+"/r1y") else 0
        self.r2 = int(self.conf.value(self.name+"/r2x")) if self.conf.value(self.name+"/r2x") else 0
        self.r2 = int(self.conf.value(self.name+"/r2y")) if self.conf.value(self.name+"/r2y") else 0
        
        self.kE = 0
        
        # Charger ou initialiser max_points depuis la config
        max_points_conf = self.conf.value(self.name+"/max_points")
        if max_points_conf is None:
            self._max_points = 1000  # Valeur par défaut
        else:
            self._max_points = int(max_points_conf)
        
        # Utiliser deque au lieu de listes - BEAUCOUP PLUS EFFICACE !
        self.Xec = deque(maxlen=self._max_points)
        self.Yec = deque(maxlen=self._max_points)
        
        self.fwhmX = 100
        self.fwhmY = 100
        self.E = []
        
        # Variables pour la mise à jour des graphiques
        self.current_label = ''
        self.current_stepX = 1
        self.current_stepY = 1
        self.data_updated = False  # Flag pour savoir si de nouvelles données sont disponibles
        
        # Créer le worker thread
        self.worker = PointingWorker()
        self.worker.results_ready.connect(self.update_display)
        
        # Timer pour la mise à jour des graphiques (20 fps par défaut = 50ms)
        self.plot_update_timer = QTimer()
        self.plot_update_timer.timeout.connect(self.updatePlotsFromTimer)
        self.plot_update_interval = 50  # ms
        self.plot_update_timer.start(self.plot_update_interval)
        
        # Create x and y indices
        x = np.arange(0, self.dimx)
        y = np.arange(0, self.dimy)
        y, x = np.meshgrid(y, x)
    
        self.data = (40*np.random.rand(self.dimx, self.dimy)).round()
        
        self.setup()
    
    @property
    def max_points(self):
        """Getter pour max_points"""
        return self._max_points
    
    @max_points.setter
    def max_points(self, value):
        """Setter pour max_points - recrée les deques avec la nouvelle taille"""
        self._max_points = value
        # Recréer les deques avec la nouvelle taille maximale
        old_xec = list(self.Xec)
        old_yec = list(self.Yec)
        self.Xec = deque(old_xec[-value:], maxlen=value)
        self.Yec = deque(old_yec[-value:], maxlen=value)
        
    def setup(self):
        
        menubar = self.menuBar()
        menubar.setNativeMenuBar(False)
        self.fileMenu = menubar.addMenu('&File')
        self.optionMenu = menubar.addMenu('&Options')
        
        self.openAct = QAction(QtGui.QIcon(self.icon+"Open.png"), 'Open File', self)
        self.openAct.setShortcut('Ctrl+o')
        self.openAct.triggered.connect(self.OpenF)
        self.fileMenu.addAction(self.openAct)
        
        self.saveAct = QAction(QtGui.QIcon(self.icon+"disketteSave.png"), 'Save file', self)
        self.saveAct.setShortcut('Ctrl+s')
        self.saveAct.triggered.connect(self.SaveF)
        self.fileMenu.addAction(self.saveAct)
        
        # Options menu
        self.resetButton = QAction('Reset', self)
        self.resetButton.triggered.connect(self.Reset)
        self.optionMenu.addAction(self.resetButton)
        
        self.centerOfMass = QAction('Center of Mass', self)
        self.centerOfMass.setCheckable(True)
        self.centerOfMass.setChecked(False)
        self.optionMenu.addAction(self.centerOfMass)
        
        # Ajouter l'action pour définir le nombre max de points
        self.setMaxPointsAct = QAction('Set Max Points...', self)
        self.setMaxPointsAct.triggered.connect(self.setMaxPointsDialog)
        self.optionMenu.addAction(self.setMaxPointsAct)
        
        # Ajouter l'action pour activer/désactiver les graphiques
        self.enablePlotsAct = QAction('Enable Plots Update', self)
        self.enablePlotsAct.setCheckable(True)
        self.enablePlotsAct.setChecked(True)  # Activé par défaut
        self.enablePlotsAct.triggered.connect(self.togglePlots)
        self.optionMenu.addAction(self.enablePlotsAct)
        
        # Ajouter l'action pour configurer la fréquence de mise à jour
        self.setUpdateRateAct = QAction('Set Update Rate...', self)
        self.setUpdateRateAct.triggered.connect(self.setUpdateRateDialog)
        self.optionMenu.addAction(self.setUpdateRateAct)
        
        # Layout principal
        mainLayout = QVBoxLayout()
        mainLayout.setSpacing(10)
        mainLayout.setContentsMargins(10, 10, 10, 10)
        
        # ===== SECTION X =====
        xGroup = QGroupBox('X Position')
        xGroup.setStyleSheet("""
            QGroupBox {
                font: bold 12pt;
                color: #ff6b6b;
                border: 2px solid #ff6b6b;
                border-radius: 8px;
                margin-top: 8px;
                padding-top: 8px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 12px;
                padding: 0 5px 0 5px;
            }
        """)
        
        xLayout = QHBoxLayout()
        xLayout.setSpacing(8)
        
        # Graphique X (beaucoup plus grand)
        self.win3 = pg.PlotWidget()
        self.win3.setDownsampling(auto=True)
        self.win3.setClipToView(True)
        self.win3.setBackground('#1e1e1e')
        self.win3.setMinimumHeight(300)
        self.p3 = self.win3.plot(pen=pg.mkPen('#ff6b6b', width=2), symbol='o', 
                                 symbolSize=4, symbolPen='#ff6b6b', symbolBrush='#ff6b6b', 
                                 name="x", antialias=True)
        self.win3.setLabel('left', 'X Position', color='#ff6b6b', **{'font-size': '11pt'})
        self.win3.setLabel('bottom', "Shot Number", color='white', **{'font-size': '11pt'})
        self.win3.showGrid(x=True, y=True, alpha=0.3)
        
        self.hLineMeanX = pg.InfiniteLine(angle=0, movable=False, 
                                          pen=pg.mkPen('#ff6b6b', width=2, style=QtCore.Qt.PenStyle.DashLine))
        self.win3.addItem(self.hLineMeanX, ignoreBounds=True)
        
        xLayout.addWidget(self.win3, stretch=5)  # Graph prend 5 parts
        
        # Statistiques X (cartes plus petites, verticales)
        xStatsLayout = QVBoxLayout()
        xStatsLayout.setSpacing(8)
        
        self.meanXCard = StatsCard('Mean', color='#ff6b6b')
        self.meanXCard.setMaximumWidth(100)
        self.stdXCard = StatsCard('Std', color='#ff6b6b')
        self.stdXCard.setMaximumWidth(100)
        self.pvXCard = StatsCard('P-V', color='#ff6b6b')
        self.pvXCard.setMaximumWidth(100)
        
        xStatsLayout.addWidget(self.meanXCard)
        xStatsLayout.addWidget(self.stdXCard)
        xStatsLayout.addWidget(self.pvXCard)
        xStatsLayout.addStretch()
        
        xLayout.addLayout(xStatsLayout, stretch=1)  # Stats prennent 1 part
        xGroup.setLayout(xLayout)
        mainLayout.addWidget(xGroup, stretch=1)
        
        # ===== SECTION Y =====
        yGroup = QGroupBox('Y Position')
        yGroup.setStyleSheet("""
            QGroupBox {
                font: bold 12pt;
                color: #51cf66;
                border: 2px solid #51cf66;
                border-radius: 8px;
                margin-top: 8px;
                padding-top: 8px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 12px;
                padding: 0 5px 0 5px;
            }
        """)
        
        yLayout = QHBoxLayout()
        yLayout.setSpacing(8)
        
        # Graphique Y (beaucoup plus grand)
        self.win4 = pg.PlotWidget()
        self.win4.setDownsampling(auto=True)
        self.win4.setClipToView(True)
        self.win4.setBackground('#1e1e1e')
        self.win4.setMinimumHeight(300)
        self.p4 = self.win4.plot(pen=pg.mkPen('#51cf66', width=2), symbol='o', 
                                 symbolSize=4, symbolPen='#51cf66', symbolBrush='#51cf66', 
                                 name="y", antialias=True)
        self.win4.setLabel('left', 'Y Position', color='#51cf66', **{'font-size': '11pt'})
        self.win4.setLabel('bottom', "Shot Number", color='white', **{'font-size': '11pt'})
        self.win4.showGrid(x=True, y=True, alpha=0.3)
        
        self.hLineMeanY = pg.InfiniteLine(angle=0, movable=False, 
                                          pen=pg.mkPen('#51cf66', width=2, style=QtCore.Qt.PenStyle.DashLine))
        self.win4.addItem(self.hLineMeanY, ignoreBounds=True)
        
        yLayout.addWidget(self.win4, stretch=5)  # Graph prend 5 parts
        
        # Statistiques Y (cartes plus petites, verticales)
        yStatsLayout = QVBoxLayout()
        yStatsLayout.setSpacing(8)
        
        self.meanYCard = StatsCard('Mean', color='#51cf66')
        self.meanYCard.setMaximumWidth(100)
        self.stdYCard = StatsCard('Std', color='#51cf66')
        self.stdYCard.setMaximumWidth(100)
        self.pvYCard = StatsCard('P-V', color='#51cf66')
        self.pvYCard.setMaximumWidth(100)
        
        yStatsLayout.addWidget(self.meanYCard)
        yStatsLayout.addWidget(self.stdYCard)
        yStatsLayout.addWidget(self.pvYCard)
        yStatsLayout.addStretch()
        
        yLayout.addLayout(yStatsLayout, stretch=1)  # Stats prennent 1 part
        yGroup.setLayout(yLayout)
        mainLayout.addWidget(yGroup, stretch=1)
        
        # ===== SECTION INFO EN BAS =====
        infoLayout = QHBoxLayout()
        infoLayout.setSpacing(8)
        
        # Carte nombre de points (très petite)
        self.nbPointsCard = StatsCard('Buffer', color='#FFD700')
        self.nbPointsCard.setMaximumWidth(110)
        self.nbPointsCard.setMaximumHeight(70)
        
        # Carte taux de rafraîchissement (très petite)
        self.updateRateCard = StatsCard('Rate', color='#00CED1')
        self.updateRateCard.setValue(f'{1000/self.plot_update_interval:.0f}fps')
        self.updateRateCard.setMaximumWidth(90)
        self.updateRateCard.setMaximumHeight(70)
        
        infoLayout.addWidget(self.nbPointsCard)
        infoLayout.addWidget(self.updateRateCard)
        infoLayout.addStretch()
        
        mainLayout.addLayout(infoLayout)
        
        # Widget principal
        MainWidget = QWidget()
        MainWidget.setLayout(mainLayout)
        self.setCentralWidget(MainWidget)
        
        # Axes references
        self.axeY3 = self.win3.getAxis('left')
        self.axeY4 = self.win4.getAxis('left')
        
        if self.parent is not None:
            self.parent.signalPointing.connect(self.Display)
    
    def setMaxPointsDialog(self):
        """Dialogue pour définir le nombre maximum de points"""
        value, ok = QInputDialog.getInt(
            self, 
            'Set Maximum Points', 
            f'Enter maximum number of points to keep in memory:\n(Current: {self.max_points})',
            value=self.max_points,
            min=100,
            max=100000,
            step=100
        )
        
        if ok:
            self.max_points = value  # Utilise le setter qui recrée les deques
            # Sauvegarder dans la config
            self.conf.setValue(self.name+"/max_points", self.max_points)
            self.conf.sync()
            
            # Mettre à jour l'affichage
            self.updatePlots()
            
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Icon.Information)
            msg.setText(f"Maximum points set to {self.max_points}")
            msg.setInformativeText(f"Current number of points: {len(self.Xec)}")
            msg.setWindowTitle("Setting saved")
            msg.setWindowFlags(QtCore.Qt.WindowType.WindowStaysOnTopHint)
            msg.exec()
    
    def setUpdateRateDialog(self):
        """Dialogue pour définir la fréquence de mise à jour des graphiques"""
        current_fps = 1000 / self.plot_update_interval
        
        value, ok = QInputDialog.getInt(
            self, 
            'Set Plot Update Rate', 
            f'Enter plot update rate (fps):\n(Current: {current_fps:.0f} fps = {self.plot_update_interval} ms)',
            value=int(current_fps),
            min=1,
            max=60,
            step=1
        )
        
        if ok:
            self.plot_update_interval = int(1000 / value)
            self.plot_update_timer.stop()
            self.plot_update_timer.start(self.plot_update_interval)
            self.updateRateCard.setValue(f'{value}fps')
            
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Icon.Information)
            msg.setText(f"Plot update rate set to {value} fps ({self.plot_update_interval} ms)")
            msg.setWindowTitle("Setting saved")
            msg.setWindowFlags(QtCore.Qt.WindowType.WindowStaysOnTopHint)
            msg.exec()
    
    def togglePlots(self):
        """Activer/désactiver la mise à jour des graphiques"""
        if self.enablePlotsAct.isChecked():
            self.plot_update_timer.start(self.plot_update_interval)
            print('Plots update enabled')
        else:
            self.plot_update_timer.stop()
            print('Plots update disabled - data still recorded')
    
    def Display(self, obje):
        """Recevoir les données et les envoyer au worker"""
        # Mettre à jour le mode de calcul
        self.worker.use_center_of_mass = self.centerOfMass.isChecked()
        
        # Envoyer au worker (non-bloquant)
        self.worker.set_data(obje)
    
    def update_display(self, results):
        """Mettre à jour l'affichage avec les résultats calculés (dans le thread GUI)"""
        xec = results['xec']
        yec = results['yec']
        self.current_label = results['label']
        self.current_stepX = results['stepX']
        self.current_stepY = results['stepY']
        
        # Ajouter les nouvelles valeurs - la deque gère automatiquement la limite !
        self.Xec.append(xec)
        self.Yec.append(yec)
        
        # Mettre à jour le nombre de points affiché
        self.nbPointsCard.setValue(f"{len(self.Xec)}/{self.max_points}")
        
        # Calculs statistiques
        Xarray = np.array(self.Xec)
        Yarray = np.array(self.Yec)
        
        Xmean = np.mean(Xarray)
        Ymean = np.mean(Yarray)
        stdX = np.std(Xarray)
        stdY = np.std(Yarray)
        XPV = Xarray.max() - Xarray.min() if len(Xarray) > 0 else 0
        YPV = Yarray.max() - Yarray.min() if len(Yarray) > 0 else 0
        
        # Mise à jour des cartes statistiques
        self.meanXCard.setValue(f'{Xmean:.2f}')
        self.stdXCard.setValue(f'{stdX:.2f}')
        self.pvXCard.setValue(f'{XPV:.2f}')
        
        self.meanYCard.setValue(f'{Ymean:.2f}')
        self.stdYCard.setValue(f'{stdY:.2f}')
        self.pvYCard.setValue(f'{YPV:.2f}')
        
        # Mise à jour des lignes moyennes
        self.hLineMeanX.setPos(Xmean)
        self.hLineMeanY.setPos(Ymean)
        
        # Marquer qu'il y a de nouvelles données
        self.data_updated = True
        
        # Mise à jour des labels d'axes
        if self.current_stepX != 1:
            self.axeY3.setLabel('X(um) ' + self.current_label)
        else:
            self.axeY3.setLabel('X ' + self.current_label)
            
        if self.current_stepY != 1:
            self.axeY4.setLabel('Y(um) ' + self.current_label)
        else:
            self.axeY4.setLabel('Y ' + self.current_label)
    
    def updatePlotsFromTimer(self):
        """Mise à jour des plots appelée par le timer"""
        if self.data_updated and len(self.Xec) > 0:
            self.updatePlots()
            self.data_updated = False
    
    def updatePlots(self):
        """Mettre à jour tous les plots"""
        self.p3.setData(list(self.Xec))
        self.p4.setData(list(self.Yec))
    
    def OpenF(self, fileOpen=False):

        if fileOpen is False:
            chemin = self.conf.value(self.name+"/path")
            fname = QFileDialog.getOpenFileName(self, "Open File", chemin, " 1D data (*.txt )")
            fichier = fname[0]
        else:
            fichier = str(fileOpen)
            
        if not fichier:
            return
            
        ext = os.path.splitext(fichier)[1]
        
        if ext == '.txt':
            aa = np.loadtxt(fichier, delimiter=" ", comments='#')
            self.Xec = deque(aa[0], maxlen=self.max_points)
            self.Yec = deque(aa[1], maxlen=self.max_points)
            
            self.updatePlots()
            
            # Mettre à jour les statistiques
            Xarray = np.array(self.Xec)
            Yarray = np.array(self.Yec)
            
            Xmean = np.mean(Xarray)
            stdX = np.std(Xarray)
            self.hLineMeanX.setPos(Xmean)
            Ymean = np.mean(Yarray)
            stdY = np.std(Yarray)
            self.hLineMeanY.setPos(Ymean)
        
            XPV = Xarray.max() - Xarray.min()
            YPV = Yarray.max() - Yarray.min()
            
            self.meanXCard.setValue(f'{Xmean:.2f}')
            self.stdXCard.setValue(f'{stdX:.2f}')
            self.pvXCard.setValue(f'{XPV:.2f}')
            
            self.meanYCard.setValue(f'{Ymean:.2f}')
            self.stdYCard.setValue(f'{stdY:.2f}')
            self.pvYCard.setValue(f'{YPV:.2f}')
            
            self.nbPointsCard.setValue(f"{len(self.Xec)}/{self.max_points}")
        else:
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Icon.Critical)
            msg.setText("Wrong file format !")
            msg.setInformativeText("The format of the file must be : .txt ")
            msg.setWindowTitle("Warning ...")
            msg.setWindowFlags(QtCore.Qt.WindowType.WindowStaysOnTopHint)
            msg.exec()
    
    def SaveF(self):
        
        fname = QFileDialog.getSaveFileName(self, "Save data as txt", self.path)
        if not fname[0]:
            return
            
        self.path = os.path.dirname(str(fname[0]))
        fichier = fname[0]
        print(fichier, ' is saved')
        self.conf.setValue(self.name+"/path", self.path)
        self.conf.sync()
        time.sleep(0.1)
        
        # Convertir deque en array pour sauvegarder
        a = np.array(self.Xec).reshape(-1, 1)
        b = np.array(self.Yec).reshape(-1, 1)
        mat = np.concatenate((a, b), axis=1)
        
        # Ajouter un header avec les infos
        header = f"Max points: {self.max_points}\nNumber of points: {len(self.Xec)}"
        np.savetxt(str(fichier)+'.txt', mat.T, header=header)
        
    def Reset(self):
        print('reset')
        self.Xec.clear()
        self.Yec.clear()
        self.p3.clear()
        self.p4.clear()
        
        # Réinitialiser les cartes
        self.nbPointsCard.setValue(f"0/{self.max_points}")
        self.meanXCard.setValue('--')
        self.stdXCard.setValue('--')
        self.pvXCard.setValue('--')
        self.meanYCard.setValue('--')
        self.stdYCard.setValue('--')
        self.pvYCard.setValue('--')
        
        self.data_updated = False
        
    def closeEvent(self, event):
        """Arrêter le worker et le timer proprement"""
        self.plot_update_timer.stop()
        
        if self.worker.isRunning():
            self.worker.terminate()
            self.worker.wait()
        
        self.isWinOpen = False
        self.E = []
        self.Xec.clear()
        self.Yec.clear()
        time.sleep(0.1)
        event.accept()
     

if __name__ == "__main__":
    appli = QApplication(sys.argv)
    appli.setStyleSheet(qdarkstyle.load_stylesheet(qt_api='pyqt6'))
    e = WINPOINTING(name='VISU')
    e.show()
    appli.exec()