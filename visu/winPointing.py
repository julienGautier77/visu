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
    results_ready = pyqtSignal(dict)
    
    def __init__(self):
        super().__init__()
        self.data = None
        self.stepX = 1
        self.stepY = 1
        self.xini = 0
        self.yini = 0
        self.use_center_of_mass = False
        self.should_stop = False
        self._has_new_data = False
        self._lock = QtCore.QMutex()

    def set_data(self, obje):
        self._lock.lock()
        self.data = obje[0]
        self.stepX = obje[1]
        self.stepY = obje[2]
        self.xini = obje[3]
        self.yini = obje[4]
        self._has_new_data = True
        self._lock.unlock()
    
    def run(self):
        """Boucle permanente"""
        while not self.should_stop:
            if self._has_new_data:
                self._lock.lock()
                data = self.data.copy()
                stepX = self.stepX
                stepY = self.stepY
                xini = self.xini
                yini = self.yini
                self._has_new_data = False
                self._lock.unlock()
                
                try:
                    ds_threshold = 512
                    if data.shape[0] > ds_threshold or data.shape[1] > ds_threshold:
                        ds = 4
                        data_small = data[::ds, ::ds]
                        dataF = gaussian_filter(data_small, 2)
                    else:
                        ds = 1
                        dataF = gaussian_filter(data, 5)

                    if self.use_center_of_mass:
                        (xec, yec) = ndimage.center_of_mass(dataF)
                        label = 'center of mass'
                    else:
                        (xec, yec) = pylab.unravel_index(dataF.argmax(), data_small.shape if ds > 1 else data.shape)
                        label = 'max'
                    
                    # Raffinement
                    margin = ds * 2
                    xc = int(round(xec * ds))
                    yc = int(round(yec * ds))
                    x0 = max(0, xc - margin)
                    x1 = min(data.shape[0], xc + margin)
                    y0 = max(0, yc - margin)
                    y1 = min(data.shape[1], yc + margin)
                    
                    if x1 > x0 and y1 > y0:
                        patch = data[x0:x1, y0:y1]
                        if self.use_center_of_mass:
                            (dx, dy) = ndimage.center_of_mass(patch)
                        else:
                            (dx, dy) = pylab.unravel_index(patch.argmax(), patch.shape)
                        xec = (x0 + dx + xini) * stepX
                        yec = (y0 + dy + yini) * stepY
                    else:
                        xec = (xec * ds + xini) * stepX
                        yec = (yec * ds + yini) * stepY
                    
                    if not self.should_stop:
                        self.results_ready.emit({
                            'xec': xec, 'yec': yec, 'label': label,
                            'stepX': stepX, 'stepY': stepY
                        })
                except Exception as e:
                    print(f"Erreur PointingWorker: {e}")
            else:
                self.msleep(10)

    def stop(self):
        self.should_stop = True
        self.wait(500)


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
        layout.setSpacing(3)
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
        self.icon = str(p.parent) + sepa + 'icons' + sepa
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
        #  self.time_old = time.time()
        
        self._max_points = 1000  # Valeur par défaut
        
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
        self.worker.start() 
        # Timer pour la mise à jour des graphiques
        self.plot_update_timer = QTimer()
        self.plot_update_timer.timeout.connect(self.updatePlotsFromTimer)
        self.plot_update_interval = 200  # ms (5 fps par défaut)
        
        
        # Compteur pour ne mettre à jour QUE via le timer
        self.update_counter = 0
        self.update_every_n_points = 5  # Tous les 5 points
        
        # Flag pour indiquer si de nouvelles données sont arrivées
        self.new_data_available = False
        
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
        
        # Graphique X 
        self.win3 = pg.PlotWidget()
        #self.win3.setDownsampling(mode='auto')
        #self.win3.setClipToView(True)
        self.win3.setBackground('#1e1e1e')
        self.win3.setMinimumHeight(300)
        
        self.p3 = self.win3.plot(pen=pg.mkPen('#ff6b6b', width=2),
                                 name="x",
                                 antialias=False,
                                 )
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
        # self.win4.setDownsampling(mode='auto')
        #self.win4.setClipToView(True)
        self.win4.setBackground('#1e1e1e')
        self.win4.setMinimumHeight(300)
        
        self.p4 = self.win4.plot(pen=pg.mkPen('#51cf66', width=2),
                                 name="y",
                                 antialias=False,
                                 )
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
        # === MISE À JOUR DES LABELS D'AXES ===
        if self.current_stepX != 1:
            self.axeY3.setLabel('X(um) ' + self.current_label)
        else:
            self.axeY3.setLabel('X ' + self.current_label)
                
        if self.current_stepY != 1:
            self.axeY4.setLabel('Y(um) ' + self.current_label)
        else:
            self.axeY4.setLabel('Y ' + self.current_label)
        
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
            if len(self.Xec) > 0:
                self.updatePlots()  # ← Forcer la mise à jour
            
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Icon.Information)
            msg.setText(f"Maximum points set to {self.max_points}")
            msg.setInformativeText(f"Current number of points: {len(self.Xec)}")
            msg.setWindowTitle("Setting saved")
            msg.setWindowFlags(QtCore.Qt.WindowType.WindowStaysOnTopHint)
            msg.exec()
    
    def setUpdateRateDialog(self):
        """Dialogue pour définir la fréquence de mise à jour"""
        current_fps = 1000 / self.plot_update_interval
        
        value, ok = QInputDialog.getInt(
            self, 
            'Set Plot Update Rate', 
            f'Enter plot update rate (fps):\n(Current: {current_fps:.0f} fps = {self.plot_update_interval} ms)\n\nRecommendations:\n- 1-2 fps for high-speed acquisition (>100 Hz)\n- 5 fps for normal use\n- 10-20 fps for smooth display',
            value=int(current_fps),
            min=1,
            max=30,
            step=1
        )
        
        if ok:
            self.plot_update_interval = int(1000 / value)
            self.plot_update_timer.stop()
            self.plot_update_timer.start(self.plot_update_interval)
            self.updateRateCard.setValue(f'{value}fps')
            
            # Ajuster automatiquement update_every_n_points
            if value <= 2:
                self.update_every_n_points = 20  # Acquisition rapide
            elif value <= 5:
                self.update_every_n_points = 10
            else:
                self.update_every_n_points = 5
            
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Icon.Information)
            msg.setText(f"Plot update rate: {value} fps ({self.plot_update_interval} ms)")
            msg.setInformativeText(f"Updating every {self.update_every_n_points} points")
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
        # print(f"update_display n={len(self.Xec)} t={time.time():.3f}")
        """Recevoir les résultats du worker - SANS mise à jour des widgets"""
        xec = results['xec']
        yec = results['yec']
        self.current_label = results['label']
        self.current_stepX = results['stepX']
        self.current_stepY = results['stepY']
        
        # Juste ajouter les données - PAS de mise à jour graphique ici !
        self.Xec.append(xec)
        self.Yec.append(yec)
        # Démarrer le timer au premier point
        if not self.plot_update_timer.isActive():
            self.plot_update_timer.start(self.plot_update_interval)
        # Incrémenter le compteur
        self.update_counter += 1
        
        # Marquer qu'il y a de nouvelles données
        if self.update_counter >= self.update_every_n_points:
            self.new_data_available = True
            self.update_counter = 0
    
    def updatePlotsFromTimer(self):
        # self.time_old = time.time()
        """Mise à jour COMPLÈTE appelée par le timer uniquement"""
        # Ne rien faire s'il n'y a pas de nouvelles données
        if not self.new_data_available or len(self.Xec) == 0:
            return
        
        try:
            # Conversion UNE SEULE FOIS
            Xarray = np.array(self.Xec)
            Yarray = np.array(self.Yec)
            
            # === MISE À JOUR DES GRAPHIQUES ===
            
            n_points = len(Xarray)
            x_axis = np.arange(n_points)
            # Downsampling agressif si beaucoup de points
            
            self.p3.setData(x=x_axis, y=Xarray)
            self.p4.setData(x=x_axis, y=Yarray)
        
            # === CALCULS STATISTIQUES ===
            Xmean = Xarray.mean()
            Ymean = Yarray.mean()
            stdX = Xarray.std()
            stdY = Yarray.std()
            XPV = np.ptp(Xarray)
            YPV = np.ptp(Yarray)
            
            # === MISE À JOUR DES CARTES ===
            self.meanXCard.setValue(f'{Xmean:.2f}')
            self.stdXCard.setValue(f'{stdX:.2f}')
            self.pvXCard.setValue(f'{XPV:.2f}')
            
            self.meanYCard.setValue(f'{Ymean:.2f}')
            self.stdYCard.setValue(f'{stdY:.2f}')
            self.pvYCard.setValue(f'{YPV:.2f}')
            
            # === MISE À JOUR DES LIGNES MOYENNES ===
            self.hLineMeanX.setPos(Xmean)
            self.hLineMeanY.setPos(Ymean)
            
            # === MISE À JOUR DU BUFFER ===
            self.nbPointsCard.setValue(f"{n_points}/{self.max_points}")
            
        except Exception as e:
            print(f"Erreur dans updatePlotsFromTimer: {e}")
        finally:
            # Toujours réinitialiser le flag
            self.new_data_available = False
    
    def updatePlots(self):
        """Mettre à jour tous les plots - appelé manuellement (OpenF, Reset, etc.)"""
        if len(self.Xec) == 0:
            return
        
        # Forcer la mise à jour immédiate
        Xarray = np.array(self.Xec)
        Yarray = np.array(self.Yec)
        
        n_points = len(Xarray)
        x_axis = np.arange(n_points)
        self.p3.setData(x=x_axis, y=Xarray)
        self.p4.setData(x=x_axis, y=Yarray)
        
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
            
            # Forcer la mise à jour graphique
            self.updatePlots()  # ← Maintenant ça marche !
            
            # Mettre à jour les statistiques
            Xarray = np.array(self.Xec)
            Yarray = np.array(self.Yec)
            
            Xmean = Xarray.mean()
            Ymean = Yarray.mean()
            stdX = Xarray.std()
            stdY = Yarray.std()
            XPV = np.ptp(Xarray)
            YPV = np.ptp(Yarray)
            
            self.hLineMeanX.setPos(Xmean)
            self.hLineMeanY.setPos(Ymean)
            
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
        
        # ARRÊTER le worker AVANT de vider les données
        self.worker.should_stop = True
        if self.worker.isRunning():
            self.worker.wait(200)  # Attendre max 200ms
        
        # Relancer le worker
        self.worker.should_stop = False
        self.worker.start() 
        
        # Arrêter le timer pendant le reset
        self.plot_update_timer.stop()
        
        # Vider les données
        self.Xec.clear()
        self.Yec.clear()
        
        # Effacer les graphiques
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
        
        # Réinitialiser les lignes moyennes
        self.hLineMeanX.setPos(0)
        self.hLineMeanY.setPos(0)
        
        # Réinitialiser les flags
        self.new_data_available = False
        self.update_counter = 0
        
        # Redémarrer le timer
        self.plot_update_timer.stop()
        
        print('Reset complete')

    def closeEvent(self, event):
        """Arrêter le worker et le timer proprement"""
        print('Closing WINPOINTING...')
        
        # Arrêter le timer
        self.plot_update_timer.stop()
        
        # Arrêter le worker proprement
        self.worker.should_stop = True
        if self.worker.isRunning():
            print('Waiting for worker to finish...')
            self.worker.quit()
            self.worker.wait(500)  # Attendre max 500ms
            if self.worker.isRunning():
                print('Worker still running, terminating...')
                self.worker.terminate()
                self.worker.wait(200)
        
        self.isWinOpen = False
        self.E = []
        self.Xec.clear()
        self.Yec.clear()
        
        print('WINPOINTING closed')
        event.accept()
     

if __name__ == "__main__":
    appli = QApplication(sys.argv)
    appli.setStyleSheet(qdarkstyle.load_stylesheet(qt_api='pyqt6'))
    e = WINPOINTING(name='VISU')
    e.show()
    appli.exec()