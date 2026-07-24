#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Dec 19 11:43:05 2018
@author: juliengautier

"""

from PyQt6.QtWidgets import QApplication, QVBoxLayout, QHBoxLayout, QWidget, QGridLayout
from PyQt6.QtWidgets import QCheckBox, QLabel, QSizePolicy, QSpinBox, QDoubleSpinBox
from PyQt6.QtWidgets import QGroupBox, QFormLayout, QFrame, QPushButton, QDialog
from PyQt6 import QtCore, QtGui
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QShortcut
from PyQt6.QtGui import QIcon
import sys
import time
import pyqtgraph as pg  # pyqtgraph biblio permettent l'affichage
import numpy as np
import qdarkstyle  # pip install qdakstyle https://github.com/ColinDuquesnoy/QDarkStyleSheet  sur conda
import pylab
import os
from scipy.ndimage.filters import gaussian_filter  # pour la reduction du bruit
from scipy.interpolate import splrep, sproot  # pour calcul fwhm et fit
from scipy.optimize import curve_fit  # pour le fit gaussien des coupes
import pathlib


class WINENCERCLED(QWidget):

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

        self.isWinOpen = False
        self.setWindowTitle('Encercled')
        self.setWindowIcon(QIcon(self.icon+'LOA.png'))
        self.setStyleSheet(qdarkstyle.load_stylesheet(qt_api='pyqt6'))
        self.left = 100
        self.top = 30
        self.width = 800
        self.height = 800
        self.setGeometry(self.left, self.top, self.width, self.height)
        self.dimx = 1200
        self.dimy = 900
        self.bloqq = 1
        self.xec = self._readConfInt(self.name+"/xec", 0)
        self.yec = self._readConfInt(self.name+"/yec", 0)
        self.r1x = self._readConfInt(self.name+"/r1x", 50)
        self.r1y = self._readConfInt(self.name+"/r1y", 50)
        self.r2 = self._readConfInt(self.name+"/r2x", 100)
        self.r2 = self._readConfInt(self.name+"/r2y", 100)
        
        # Paramètres pour le calcul du rayon d'Airy (tache de diffraction) :
        # r_Airy = 1.22 * lambda * focale / taille_faisceau
        self.airyFocale = self._readConfFloat(self.name+"/airyFocale", 1000)       # mm (défaut 1 m)
        self.airyBeamSize = self._readConfFloat(self.name+"/airyBeamSize", 85)      # mm (défaut 85 mm)
        self.airyWavelength = self._readConfFloat(self.name+"/airyWavelength", 800)  # nm (défaut 800 nm)
        self._airyAdded = False
        
        self.kE = 0  # variable pour la courbe E fct du nb shoot
        
        self.Xec = []
        self.Yec = []
        self.fwhmX = 100
        self.fwhmY = 100
        self.setWindowIcon(QIcon('./icons/LOA.png'))
        self.E = []
        
        # self.E=np.array([2,3,5])
        self.Xec = []
        self.Yec = []
        
        # Create x and y indices
        x = np.arange(0, self.dimx)
        y = np.arange(0, self.dimy)
        y, x = np.meshgrid(y, x)
    
        self.data = (40*np.random.rand(self.dimx, self.dimy)).round()
        
        self.setup()
        self.ActionButton()
        self.Display(self.data)

        # Ajuste la hauteur de la fenêtre à la hauteur réelle du panneau de
        # contrôle (vbox1) : sans ça, la fenêtre garde sa hauteur fixe
        # initiale (800 px) même après avoir déplacé les réglages Airy dans
        # une fenêtre séparée, ce qui rendait le graphique plus grand que
        # le panneau, désaligné par rapport au dernier widget ("E2 mean").
        sidebarHeight = self.vbox1.sizeHint().height() + 40  # marge pour les bords
        self.resize(self.width, max(sidebarHeight, 400))

    def _readConfFloat(self, key, default):
        """
        Lit une valeur flottante depuis la config, avec repli robuste sur
        `default` si la clé est absente, vide, ou invalide (ex : fichier
        confVisu.ini créé/partagé par un autre programme qui n'a jamais
        écrit cette clé -> QSettings peut renvoyer None ou une chaîne
        vide même en lui donnant une valeur par défaut). Dans ce cas, on
        réenregistre immédiatement le défaut dans le fichier pour que les
        prochaines lectures soient cohérentes.
        """
        raw = self.conf.value(key, default)
        try:
            if raw is None or raw == '':
                raise ValueError
            return float(raw)
        except (TypeError, ValueError):
            self.conf.setValue(key, default)
            return float(default)

    def _readConfInt(self, key, default):
        """Comme _readConfFloat, mais retourne un entier."""
        return int(self._readConfFloat(key, default))

    def setup(self):
        
        TogOff = self.icon+'Toggle_Off.png'
        TogOn = self.icon+'Toggle_On.png'       
        TogOff = pathlib.Path(TogOff)
        TogOff = pathlib.PurePosixPath(TogOff)
        TogOn = pathlib.Path(TogOn)
        TogOn = pathlib.PurePosixPath(TogOn)
        self.setStyleSheet(
            "QCheckBox::indicator{width: 26px;height: 26px;}"
            "QCheckBox::indicator:unchecked { image : url(%s);}"
            "QCheckBox::indicator:checked { image:  url(%s);}"
            "QCheckBox{font: 10pt;}"
            "QGroupBox{"
            "  font: bold 10pt;"
            "  border: 1px solid #3a3f4b;"
            "  border-radius: 6px;"
            "  margin-top: 10px;"
            "  padding-top: 10px;"
            "}"
            "QGroupBox::title{"
            "  subcontrol-origin: margin;"
            "  left: 10px;"
            "  padding: 0 4px;"
            "  color: #8ab4f8;"
            "}"
            % (TogOff, TogOn)
        )
        
        vbox1 = QVBoxLayout()
        self.vbox1 = vbox1  # gardé pour ajuster la hauteur de la fenêtre au contenu réel du panneau (voir __init__)
        vbox1.setSpacing(12)

        # --- Groupe : mode de détection ---
        modeGroup = QGroupBox("Détection")
        modeLayout = QHBoxLayout()
        self.checkBoxAuto = QCheckBox('Auto', self)
        self.checkBoxAuto.setChecked(True)
        self.bckButton = QCheckBox('Soustraire le fond', self)
        modeLayout.addWidget(self.checkBoxAuto)
        modeLayout.addWidget(self.bckButton)
        modeLayout.addStretch(1)
        modeGroup.setLayout(modeLayout)
        vbox1.addWidget(modeGroup)

        # --- Groupe : rapport d'énergie (résultat principal, mis en avant) ---
        ratioGroup = QGroupBox("Rapport d'énergie")
        ratioLayout = QHBoxLayout()
        self.lEnergie = QLabel('s(E1)/s(E2) :')
        self.lEnergie.setStyleSheet("color:#8ab4f8; font: 13pt;")
        self.energieRes = QLabel('?')
        self.energieRes.setStyleSheet("color:#8ab4f8; font: bold 20pt;")
        self.energieRes.setMaximumHeight(36)
        ratioLayout.addWidget(self.lEnergie)
        ratioLayout.addWidget(self.energieRes)
        ratioLayout.addStretch(1)
        ratioGroup.setLayout(ratioLayout)
        vbox1.addWidget(ratioGroup)

        # --- Groupe : rayons des cercles de mesure ---
        radiusGroup = QGroupBox("Rayons des cercles")
        radiusForm = QFormLayout()
        radiusForm.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        radiusForm.setVerticalSpacing(8)

        self.LabelR1x = QLabel("w = fwhm X × 0.85")
        self.LabelR1x.setStyleSheet("color:#ef5350; font: 11pt;")
        self.r1xBox = QDoubleSpinBox()
        self.r1xBox.setDecimals(2)
        self.r1xBox.setMaximum(20000)
        self.r1xBox.setSuffix(" px")

        self.LabelR1y = QLabel('w = fwhm Y × 0.85')
        self.LabelR1y.setStyleSheet("color:#66bb6a; font: 11pt;")
        self.r1yBox = QDoubleSpinBox()
        self.r1yBox.setDecimals(2)
        self.r1yBox.setMaximum(20000)
        self.r1yBox.setSuffix(" px")

        self.LabelR2 = QLabel('R2')
        self.LabelR2.setStyleSheet("color:#ffee58; font: 11pt;")
        self.r2Box = QDoubleSpinBox()
        self.r2Box.setDecimals(2)
        self.r2Box.setMaximum(20000)
        self.r2Box.setMaximumWidth(100)
        self.r2Box.setSuffix(" px")

        radiusForm.addRow(self.LabelR1x, self.r1xBox)
        radiusForm.addRow(self.LabelR1y, self.r1yBox)
        radiusForm.addRow(self.LabelR2, self.r2Box)
        radiusGroup.setLayout(radiusForm)
        vbox1.addWidget(radiusGroup)

        # --- Groupe : rayon d'Airy (tache de diffraction théorique) ---
        # Version compacte : seuls "Afficher" et le résultat sont dans le
        # panneau principal ; les 3 réglages (focale, taille faisceau,
        # longueur d'onde) sont dans une fenêtre séparée (voir
        # openAirySettings()), pour ne pas allonger inutilement le widget.
        airyGroup = QGroupBox("Rayon d'Airy (diffraction)")
        airyLayout = QHBoxLayout()

        self.checkBoxAiry = QCheckBox('Afficher', self)
        self.checkBoxAiry.setChecked(False)
        airyLayout.addWidget(self.checkBoxAiry)

        self.airySettingsBtn = QPushButton("⚙ Réglages...")
        self.airySettingsBtn.setMaximumWidth(110)
        airyLayout.addWidget(self.airySettingsBtn)

        self.labelAiryResult = QLabel("r = ? ")
        self.labelAiryResult.setStyleSheet("color:#4dd0e1; font: 11pt;")
        airyLayout.addWidget(self.labelAiryResult)
        airyLayout.addStretch(1)

        airyGroup.setLayout(airyLayout)
        vbox1.addWidget(airyGroup)

        # Les 3 spinbox existent toujours (utilisées par updateAiry()) mais
        # ne sont ajoutées qu'à la fenêtre de réglages séparée, pas ici
        self.airyFocaleBox = QDoubleSpinBox()
        self.airyFocaleBox.setDecimals(1)
        self.airyFocaleBox.setMaximum(1000000)
        self.airyFocaleBox.setSuffix(" mm")
        self.airyFocaleBox.setValue(self.airyFocale)

        self.airyBeamBox = QDoubleSpinBox()
        self.airyBeamBox.setDecimals(2)
        self.airyBeamBox.setMaximum(10000)
        self.airyBeamBox.setSuffix(" mm")
        self.airyBeamBox.setValue(self.airyBeamSize)

        self.airyWavelengthBox = QDoubleSpinBox()
        self.airyWavelengthBox.setDecimals(1)
        self.airyWavelengthBox.setMaximum(100000)
        self.airyWavelengthBox.setSuffix(" nm")
        self.airyWavelengthBox.setValue(self.airyWavelength)

        self._buildAirySettingsWindow()

        # --- Groupe : résultats E1 / E2 ---
        resultsGroup = QGroupBox("Résultats")
        resultsGrid = QGridLayout()
        resultsGrid.setHorizontalSpacing(16)
        resultsGrid.setVerticalSpacing(6)

        LabelE1 = QLabel("E1 Sum")
        LabelE1.setStyleSheet("color:#ef5350; font: 11pt;")
        self.LabelE1Sum = QLabel("?")
        self.LabelE1Sum.setStyleSheet("color:#ef5350; font: 11pt;")
        LabelE1M = QLabel("E1 mean")
        LabelE1M.setStyleSheet("color:#ef5350; font: 11pt;")
        self.LabelE1Mean = QLabel("?")
        self.LabelE1Mean.setStyleSheet("color:#ef5350; font: 11pt;")

        LabelE2 = QLabel("E2 Sum")
        LabelE2.setStyleSheet("color:#ffee58; font: 11pt;")
        self.LabelE2Sum = QLabel("?")
        self.LabelE2Sum.setStyleSheet("color:#ffee58; font: 11pt;")
        LabelE2M = QLabel("E2 mean")
        LabelE2M.setStyleSheet("color:#ffee58; font: 11pt;")
        self.LabelE2Mean = QLabel("?")
        self.LabelE2Mean.setStyleSheet("color:#ffee58; font: 11pt;")

        resultsGrid.addWidget(LabelE1, 0, 0)
        resultsGrid.addWidget(self.LabelE1Sum, 0, 1)
        resultsGrid.addWidget(LabelE1M, 1, 0)
        resultsGrid.addWidget(self.LabelE1Mean, 1, 1)

        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet("color:#3a3f4b;")
        resultsGrid.addWidget(sep, 2, 0, 1, 2)

        resultsGrid.addWidget(LabelE2, 3, 0)
        resultsGrid.addWidget(self.LabelE2Sum, 3, 1)
        resultsGrid.addWidget(LabelE2M, 4, 0)
        resultsGrid.addWidget(self.LabelE2Mean, 4, 1)

        resultsGroup.setLayout(resultsGrid)
        vbox1.addWidget(resultsGroup)

        vbox1.addStretch(1)
        
        self.winImage = pg.GraphicsLayoutWidget()
        self.winImage.setContentsMargins(0, 0, 0, 0)
        self.winImage.setAspectLocked(True)
        self.winImage.setSizePolicy(QSizePolicy.Policy.MinimumExpanding, QSizePolicy.Policy.MinimumExpanding)
        # self.winImage.ci.setContentsMargins(0,0,0,0)
        vbox2 = QVBoxLayout()
        hbox2 = QHBoxLayout()
        hbox2.addWidget(self.winImage)
        vbox2.addLayout(hbox2)
        vbox2.setContentsMargins(0, 0, 0, 0)
        
        self.p1 = self.winImage.addPlot(row=0, col=1)
        
        self.imh = pg.ImageItem()
        self.p1.addItem(self.imh)
        
        self.p1.setMouseEnabled(x=False, y=False)
        self.p1.setContentsMargins(0, 0, 0, 0)
        
        self.p1.setAspectLocked(True, ratio=1)
        self.p1.showAxis('right', show=False)
        self.p1.showAxis('top', show=False)
        self.p1.showAxis('left', show=True)
        self.p1.showAxis('bottom', show=True)

        # Coupe verticale (profil selon Y) : à gauche de l'image, axe Y lié
        # (zoom/pan synchronisés automatiquement). Axe des valeurs inversé
        # pour que 0 soit contre l'image et l'intensité grandisse en
        # s'éloignant vers la gauche.
        self.pProfileLeft = self.winImage.addPlot(row=0, col=0)
        self.pProfileLeft.setYLink(self.p1)
        self.pProfileLeft.setMouseEnabled(x=False, y=False)
        self.pProfileLeft.showAxis('bottom', show=False)
        self.pProfileLeft.showAxis('left', show=False)
        self.pProfileLeft.invertX(True)

        # Coupe horizontale (profil selon X) : en dessous de l'image, axe X
        # lié. Axe des valeurs inversé pour que 0 soit contre l'image et
        # l'intensité grandisse vers le bas.
        self.pProfileBottom = self.winImage.addPlot(row=1, col=1)
        self.pProfileBottom.setXLink(self.p1)
        self.pProfileBottom.setMouseEnabled(x=False, y=False)
        self.pProfileBottom.showAxis('bottom', show=False)
        self.pProfileBottom.showAxis('left', show=False)
        self.pProfileBottom.invertY(True)

        # L'image occupe la majorité de l'espace, les coupes restent fines
        self.winImage.ci.layout.setColumnStretchFactor(0, 1)
        self.winImage.ci.layout.setColumnStretchFactor(1, 4)
        self.winImage.ci.layout.setRowStretchFactor(0, 4)
        self.winImage.ci.layout.setRowStretchFactor(1, 1)

        self.vLine = pg.InfiniteLine(angle=90, movable=False, pen='w')
        self.hLine = pg.InfiniteLine(angle=0, movable=False, pen='w')
        self.p1.addItem(self.vLine)
        self.p1.addItem(self.hLine)
        
        self.vLine.setPos(self.xec)
        self.hLine.setPos(self.yec)
        
        self.roi1 = pg.CircleROI([self.xec, self.yec], [2*self.r1x, 2*self.r1y], pen='r', movable=False)
        self.roi1.setPos([self.xec-(self.r1x), self.yec-(self.r1y)])
        self.p1.addItem(self.roi1)
       
        self.roi2 = pg.CircleROI([self.xec, self.yec], [2*self.r2, 2*self.r2], pen='y', movable=False)
        self.roi2.setPos([self.xec-(self.r2), self.yec-(self.r2)])
        self.p1.addItem(self.roi2)

        # Cercle du rayon d'Airy (tache de diffraction théorique), pas
        # ajouté à l'image par défaut : seulement si "Afficher" est coché
        # (voir updateAiry())
        self.roiAiry = pg.CircleROI([self.xec, self.yec], [2, 2], pen='c', movable=False)
        
        # histogramme
        self.hist = pg.HistogramLUTItem() 
        self.hist.setImageItem(self.imh)
        self.hist.autoHistogramRange()
        self.hist.gradient.loadPreset('flame')
        
        # Courbes de coupe (données brutes, une par graphe dédié) + courbes
        # de fit gaussien superposées (en tirets cyan)
        self.curve2 = self.pProfileLeft.plot(pen='y')     # profil vertical brut
        self.curveFitLeft = self.pProfileLeft.plot(
            pen=pg.mkPen('c', width=2, style=QtCore.Qt.PenStyle.DashLine))
        self.curve3 = self.pProfileBottom.plot(pen='y')   # profil horizontal brut
        self.curveFitBottom = self.pProfileBottom.plot(
            pen=pg.mkPen('c', width=2, style=QtCore.Qt.PenStyle.DashLine))

        # texte FWHM (issu du fit gaussien), anchor centré (indépendant du
        # sens des axes inversés) ; textX pivoté car la colonne de gauche
        # est étroite
        self.textX = pg.TextItem(angle=-90, color='w', anchor=(0.5, 0.5))
        self.textY = pg.TextItem(angle=0, color='w', anchor=(0.5, 0.5))
        self.pProfileLeft.addItem(self.textX)
        self.pProfileBottom.addItem(self.textY)
        
        self.ROIRect = pg.RectROI([self.xec, self.yec], [4*self.r1x, 4*self.r1y], pen='m',)
        self.ROIRect.setPos([self.xec-(self.r1x), self.yec-(self.r1y)])
        hLayout1 = QHBoxLayout()
        hLayout1.addLayout(vbox2)
        hLayout1.addLayout(vbox1)
        hLayout1.setContentsMargins(1, 1, 1, 1)
        
        vMainLayout = QVBoxLayout()
        vMainLayout.addLayout(hLayout1)

        hMainLayout = QHBoxLayout()
        hMainLayout.addLayout(vMainLayout)
        self.setLayout(hMainLayout)
        self.setContentsMargins(1, 1, 1, 1)
        
    def ActionButton(self):
        # Blocage de la souris
        self.roi1.sigRegionChangeFinished.connect(self.energSouris)  # signal si changement à la souris de la taille des cercles
        self.roi2.sigRegionChangeFinished.connect(self.energSouris)
#
        self.r1xBox.editingFinished.connect(self.Rayon)  # w.r1Box.returnPressed.connect(Rayon)# rayon change a la main
        self.r1yBox.editingFinished.connect(self.Rayon)
        self.r2Box.editingFinished.connect(self.Rayon)
       
        self.shortcutb = QtGui.QShortcut(QtGui.QKeySequence("Ctrl+b"), self)
        self.shortcutb.activated.connect(self.bloquer)
        self.shortcutd = QtGui.QShortcut(QtGui.QKeySequence("Ctrl+d"), self)
        self.shortcutd.activated.connect(self.debloquer)
         
        self.shortcutPu = QShortcut(QtGui.QKeySequence("+"), self)
        self.shortcutPu.activated.connect(self.paletteup)
        self.shortcutPu.setContext(Qt.ShortcutContext(3))
        # 3: The shortcut is active when its parent widget, or any of its children has focus. default O The shortcut is active when its parent widget has focus.
        self.shortcutPd = QtGui.QShortcut(QtGui.QKeySequence("-"), self)
        self.shortcutPd.activated.connect(self.palettedown)
        self.shortcutPd.setContext(Qt.ShortcutContext(3))
        
        self.checkBoxAuto.stateChanged.connect(lambda: self.Display(self.data))
        # mvt de la souris
        self.proxy = pg.SignalProxy(self.p1.scene().sigMouseMoved, rateLimit=60, slot=self.mouseMoved)
        self.p1.scene().sigMouseClicked.connect(self.mouseClick)
        self.vb = self.p1.vb
        
        self.checkBoxAuto.stateChanged.connect(self.AutoE)
        self.bckButton.stateChanged.connect(self.Back)

        self.ROIRect.sigRegionChangeFinished.connect(self.roiBackChanged)

        self.checkBoxAiry.stateChanged.connect(self.updateAiry)
        self.airySettingsBtn.clicked.connect(self.openAirySettings)
        self.airyFocaleBox.valueChanged.connect(self.updateAiry)
        self.airyBeamBox.valueChanged.connect(self.updateAiry)
        self.airyWavelengthBox.valueChanged.connect(self.updateAiry)
        
        if self.parent is not None:
            self.parent.signalEng.connect(self.Display)
        
    def mouseClick(self):
        # bloque ou debloque la souris si click su le graph
        if self.bloqq == 1:
            self.debloquer()
        else:
            self.bloquer() 
            
    def bloquer(self):  # bloque la croix 
        self.bloqq = 1
        self.CalculE()
        
    def debloquer(self):  # deblaoque la croix : elle bouge avec la souris
        self.bloqq = 0
    
    # mvt de la souris
    
    def mouseMoved(self, evt):
        # pour que la cross suive le mvt de la souris
        if self.checkBoxAuto.isChecked() is False:

            if self.bloqq == 0:  # souris non bloquer
                pos = evt[0]  # using signal proxy turns original arguments into a tuple
                if self.p1.sceneBoundingRect().contains(pos):
                    mousePoint = self.vb.mapSceneToView(pos)
                    self.xec = int(mousePoint.x())
                    self.yec = int(mousePoint.y())
                    if ((self.xec > 0 and self.xec < self.data.shape[0]) and (self.yec > 0 and self.yec < self.data.shape[1])):
                        self.vLine.setPos(self.xec)
                        self.hLine.setPos(self.yec)  # la croix ne bouge que dans le graph
                        self.roi1.setPos([self.xec-(self.r1x), self.yec-(self.r1y)])
                        self.roi2.setPos([self.xec-(self.r2), self.yec-(self.r2)])
                        # Sans ces appels, les coupes (profils + fit gaussien),
                        # le rapport d'énergie et le cercle d'Airy restaient
                        # figés à leur dernière position calculée : ils ne
                        # suivaient pas la croix quand on la déplace à la
                        # souris (mode Auto décoché).
                        self.Coupe()
                        self.CalculE()
                        self.updateAiry()
                            
    def AutoE(self):
        if self.checkBoxAuto.isChecked() is False:
            self.energSouris()
            self.roi1.setSize([2*self.r1x, 2*self.r1y])
            self.roi2.setSize([2*self.r2, 2*self.r2])
            
    def energSouris(self):  # changement des rayons à la souris 
        if self.checkBoxAuto.isChecked() is False:
            s1 = self.roi1.size()
            s2 = self.roi2.size()
            self.r1xBox.setValue((int(s1[0]/2)))
            self.r1yBox.setValue((int(s1[1]/2)))
            self.r2Box.setValue((int(s2[0]/2)))
            self.r1x = int(s1[0]/2)
            self.r1y = int(s1[1]/2)
            self.r2 = int(s2[0]/2)
            if self.bloqq == 1:
                self.CalculE()
     
    def _scaleEnabled(self):
        """True si 'Scale Factor' est coché dans les Préférences (winPref)."""
        return (self.parent is not None
                and hasattr(self.parent, 'winPref')
                and self.parent.winPref.checkBoxAxeScale.isChecked())

    def _stepX(self):
        """Facteur pixel -> µm sur X (1.0 si l'échelle n'est pas active)."""
        if self._scaleEnabled():
            return self.parent.winPref.stepX or 1.0
        return 1.0

    def _stepY(self):
        """Facteur pixel -> µm sur Y (1.0 si l'échelle n'est pas active)."""
        if self._scaleEnabled():
            return self.parent.winPref.stepY or 1.0
        return 1.0

    def _realStepXY(self):
        """
        Calibration pixel <-> µm RÉELLE (self.parent.winPref.stepX/stepY),
        indépendamment de si la case "Scale Factor" est cochée ou non : le
        rayon d'Airy est une taille physique, il faut toujours la vraie
        calibration pour le convertir en pixels sur l'image, contrairement
        à _stepX()/_stepY() qui ne servent qu'à choisir l'UNITÉ D'AFFICHAGE
        des autres résultats (rayons, FWHM).
        Retourne (None, None) si aucune calibration n'est disponible.
        """
        if self.parent is not None and hasattr(self.parent, 'winPref'):
            stepX = self.parent.winPref.stepX
            stepY = self.parent.winPref.stepY
            if stepX and stepY:
                return stepX, stepY
        return None, None

    def computeAiryRadiusPx(self):
        """
        Calcule le rayon du disque d'Airy (1er anneau sombre de diffraction) :
            r_Airy = 1.22 * lambda * focale / taille_faisceau
        Retourne (rAiry_px, rAiry_um) ou (None, None) si la calibration
        pixel<->µm (winPref.stepX/stepY) n'est pas disponible.
        """
        stepX, stepY = self._realStepXY()
        if stepX is None:
            return None, None
        if self.airyBeamSize <= 0:
            return None, None
        focale_m = self.airyFocale / 1000.0        # mm -> m
        beamSize_m = self.airyBeamSize / 1000.0     # mm -> m
        wavelength_m = self.airyWavelength * 1e-9   # nm -> m
        rAiry_m = 1.22 * wavelength_m * focale_m / beamSize_m
        rAiry_um = rAiry_m * 1e6
        rAiry_px = rAiry_um / stepX
        return rAiry_px, rAiry_um

    def _buildAirySettingsWindow(self):
        """
        Construit la petite fenêtre séparée contenant les réglages du
        rayon d'Airy (focale, taille faisceau, longueur d'onde), pour ne
        pas allonger le panneau principal de winSuppE. Les spinbox sont
        les mêmes instances que celles créées dans setup() (utilisées par
        updateAiry()) — juste affichées ici plutôt que dans le panneau
        principal.
        """
        self.airySettingsWin = QDialog(self)
        self.airySettingsWin.setWindowTitle("Réglages rayon d'Airy")
        self.airySettingsWin.setStyleSheet(self.styleSheet())

        form = QFormLayout()
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        form.setVerticalSpacing(8)
        form.addRow(QLabel("Focale"), self.airyFocaleBox)
        form.addRow(QLabel("Taille faisceau"), self.airyBeamBox)
        form.addRow(QLabel("Longueur d'onde"), self.airyWavelengthBox)
        self.airySettingsWin.setLayout(form)

    def openAirySettings(self):
        """Affiche la fenêtre de réglages du rayon d'Airy (non modale)"""
        self.airySettingsWin.show()
        self.airySettingsWin.raise_()
        self.airySettingsWin.activateWindow()

    def updateAiry(self):
        """Met à jour le cercle d'Airy (affichage/position/taille) et le sauvegarde"""
        self.airyFocale = self.airyFocaleBox.value()
        self.airyBeamSize = self.airyBeamBox.value()
        self.airyWavelength = self.airyWavelengthBox.value()
        self.conf.setValue(self.name+"/airyFocale", self.airyFocale)
        self.conf.setValue(self.name+"/airyBeamSize", self.airyBeamSize)
        self.conf.setValue(self.name+"/airyWavelength", self.airyWavelength)

        if self.checkBoxAiry.isChecked():
            rAiry_px, rAiry_um = self.computeAiryRadiusPx()
            if rAiry_px is None:
                self.labelAiryResult.setText("Calibration manquante (Scale Factor / stepX,Y)")
                if self._airyAdded:
                    self.p1.removeItem(self.roiAiry)
                    self._airyAdded = False
                return
            self.roiAiry.setSize([2*rAiry_px, 2*rAiry_px])
            self.roiAiry.setPos([self.xec-rAiry_px, self.yec-rAiry_px])
            if not self._airyAdded:
                self.p1.addItem(self.roiAiry)
                self._airyAdded = True
            valPx = round(rAiry_px, 2)
            valUm = round(rAiry_um, 2)
            self.labelAiryResult.setText(f"r = {valUm} µm  ({valPx} px)")
        else:
            if self._airyAdded:
                self.p1.removeItem(self.roiAiry)
                self._airyAdded = False

    def Rayon(self): 
        """changement rayon dans les box
        """
        if self.checkBoxAuto.isChecked() is False:
            # Les box affichent en µm si l'échelle est active, en pixels
            # sinon : on reconvertit donc la valeur saisie vers des pixels
            # (self.r1x/r1y/r2 restent toujours en pixels en interne, car
            # les ROI pyqtgraph travaillent en coordonnées pixel de l'image)
            stepX = self._stepX()
            stepY = self._stepY()

            if self.r1xBox.hasFocus():
                self.r1x = self.r1xBox.value() / stepX
                self.roi1.setSize([2*self.r1x, 2*self.r1y])
            if self.r1yBox.hasFocus():
                self.r1y = self.r1yBox.value() / stepY
                self.roi1.setSize([2*self.r1x, 2*self.r1y])
            
            if self.r2Box.hasFocus():
                self.r2 = self.r2Box.value() / stepX
                self.roi2.setSize([2*self.r2, 2*self.r2])
            
            self.roi1.setPos([self.xec-(self.r1x), self.yec-(self.r1y)])
            self.roi2.setPos([self.xec-(self.r2), self.yec-(self.r2)])
            if self.bloqq == 1:
                self.CalculE()
    
    def CalculE(self):
        
        if self.fwhmX is None or self.fwhmY is None:
            self.fwhmX = 100
            self.fwhmY = 100

        # Unité d'affichage : µm si "Scale Factor" est coché dans les
        # Préférences (winPref), pixels sinon. Les valeurs internes
        # (self.r1x, self.r1y, self.r2) restent toujours en pixels, car les
        # ROI pyqtgraph opèrent en coordonnées pixel de l'image.
        scaleOn = self._scaleEnabled()
        stepX = self._stepX()
        stepY = self._stepY()
        unit = 'µm' if scaleOn else 'px'
        self.r1xBox.setSuffix(f' {unit}')
        self.r1yBox.setSuffix(f' {unit}')
        self.r2Box.setSuffix(f' {unit}')
        self.LabelR1x.setText(f"w = fwhm X × 0.85 ({unit})")
        self.LabelR1y.setText(f"w = fwhm Y × 0.85 ({unit})")
        self.LabelR2.setText(f"R2 ({unit})")
        
        if self.checkBoxAuto.isChecked() is True:
            # w (rayon 1/e², convention faisceau) = FWHM * 0.849, PAS FWHM/0.849.
            # FWHM = 2*sqrt(2*ln2)*sigma ≈ 2.3548*sigma, et w = 2*sigma pour
            # une gaussienne (convention exp(-x²/(2*sigma²))) : donc
            # w = FWHM/2.3548 * 2 = FWHM*0.8493. L'ancienne formule
            # (FWHM/0.849 ≈ 2.77*sigma au lieu de 2*sigma) donnait un rayon
            # ~39% trop grand, soit une aire ~2x trop grande, et donc une
            # énergie encerclée mesurée à ~97.9% au lieu des 86.5%
            # théoriques attendus pour une gaussienne parfaite.
            self.r1x = self.fwhmX * 0.849
            self.r1y = self.fwhmY * 0.849
            self.r1xBox.setValue(round(self.r1x * stepX, 2))
            self.r1yBox.setValue(round(self.r1y * stepY, 2))
            nbG = 2  # ré= 2 fois r1 pour le grand cercle
            self.roi2.setSize([2*nbG*self.r1x, 2*nbG*self.r1y])
            self.roi2.setPos([self.xec-nbG*self.r1x, self.yec-nbG*self.r1y])
            self.r2Box.setValue(round(2*nbG*self.r1x * stepX, 2))
            self.roi1.setSize([2*self.r1x, 2*self.r1y])
            self.roi1.setPos([self.xec-self.r1x, self.yec-self.r1y])
            
        else:
            self.r1x = self.r1x
            self.r1y = self.r1y
           
        E1 = self.roi1.getArrayRegion(self.data, self.imh).sum()
        E2 = self.roi2.getArrayRegion(self.data, self.imh).sum()
        self.rap = 100*E1/E2
        self.energieRes.setText('%.2f %%' % self.rap)
        # self.E=np.append(self.E,self.rap)
        # #self.E.append(self.rap)
        # Emean=np.mean(self.E)
        # self.meanAff.setText('%.2f' % Emean)
        # EPV=np.std(self.E)
        # self.PVAff.setText('%.2f' % EPV)
        # self.hLineMeanE.setPos(Emean)
        # (textX/textY sont déjà mis à jour par Coupe(), avec le FWHM issu
        # du fit gaussien — pas besoin de les réécrire ici)
        self.LabelE1Sum.setText('%.2f' % E1)
        self.LabelE1Mean.setText('%.2f' % (self.roi1.getArrayRegion(self.data, self.imh).mean()))
        self.LabelE2Sum.setText('%.2f' % E2)
        self.LabelE2Mean.setText('%.2f' % (self.roi2.getArrayRegion(self.data, self.imh).mean()))
        
    def _resizeWindowToMatchAspect(self, imgWidth, imgHeight):
        """
        Redimensionne la hauteur de la fenêtre pour que le panneau
        graphique (à largeur constante) ait un ratio proche de celui de
        l'image réelle de la caméra. Réduit au minimum la marge que
        setAspectLocked doit ajouter pour préserver des pixels carrés :
        sans ça, l'axe pouvait afficher une plage bien plus grande que la
        résolution réelle (ex : jusqu'à 2500 pour une caméra de 1500 px).
        """
        graphPxWidth = self.p1.vb.width()
        graphPxHeight = self.p1.vb.height()
        if graphPxWidth <= 0 or graphPxHeight <= 0:
            return
        targetGraphHeight = graphPxWidth * imgHeight / imgWidth
        delta = targetGraphHeight - graphPxHeight
        if abs(delta) > 20:  # évite les ajustements insignifiants/instables
            currentSize = self.size()
            newHeight = max(int(currentSize.height() + delta), 300)
            self.resize(currentSize.width(), newHeight)

    def _fitViewFullImage(self, imgWidth, imgHeight):
        """
        Ajuste la vue pour que l'image COMPLÈTE [0,imgWidth]x[0,imgHeight]
        reste toujours visible, sans jamais être recadrée.

        pyqtgraph, avec setAspectLocked + setRange/autoRange, choisit
        parfois de ROGNER un axe plutôt que d'agrandir l'autre pour
        respecter l'aspect ratio (comportement incohérent selon l'état
        interne) : une tache excentrée pouvait alors se retrouver hors du
        champ visible dans le widget principal, tout en restant correcte
        dans les mesures (coupe/FWHM), qui elles ne dépendent pas de la
        vue affichée. Ici, on calcule nous-mêmes la marge nécessaire sur
        l'axe le "moins large" (relativement au widget), en n'agrandissant
        jamais l'image, jamais en la rognant.
        """
        vb = self.p1.vb
        pxW = vb.width()
        pxH = vb.height()

        if pxW <= 0 or pxH <= 0:
            # Widget pas encore dimensionné (avant le premier affichage) :
            # repli simple, sera recalculé correctement dans showEvent()
            self.p1.setLimits(xMin=0, xMax=imgWidth, yMin=0, yMax=imgHeight)
            self.p1.setRange(xRange=(0, imgWidth), yRange=(0, imgHeight), padding=0)
            return

        dataAspect = imgWidth / imgHeight
        widgetAspect = pxW / pxH

        if widgetAspect > dataAspect:
            # Widget relativement plus large que l'image : on garde Y
            # exact et on élargit X — toute la marge est ajoutée du côté
            # positif (0 reste l'origine des deux axes, plus intuitif
            # qu'un axe qui démarre en négatif)
            newWidth = imgHeight * widgetAspect
            xRange = (0, max(newWidth, imgWidth))
            yRange = (0, imgHeight)
        else:
            # Widget relativement plus haut : on garde X exact et on
            # élargit Y, toujours à partir de 0
            newHeight = imgWidth / widgetAspect
            xRange = (0, imgWidth)
            yRange = (0, max(newHeight, imgHeight))

        self.p1.setLimits(xMin=xRange[0], xMax=xRange[1], yMin=yRange[0], yMax=yRange[1])
        self.p1.setRange(xRange=xRange, yRange=yRange, padding=0)

    def Display(self, data):
        self.dataOrg = data
        self.data = data
        
        self.dimx = self.data.shape[0]
        self.dimy = self.data.shape[1]
        self.p1.setAspectLocked(True, ratio=1)
        self.imh.setImage(data.astype(float), autoLevels=True, autoDownsample=True)

        # Ajuste la vue pour que l'image COMPLÈTE reste toujours visible
        # (jamais recadrée), quel que soit le ratio largeur/hauteur du
        # widget. Ne réinitialise la vue que la première fois ou si la
        # taille de l'image change, pour ne pas annuler un zoom manuel.
        imgWidth = self.imh.width()
        imgHeight = self.imh.height()
        if imgWidth and imgHeight and (imgWidth, imgHeight) != getattr(self, '_lastImgSize', None):
            # Redimensionne D'ABORD la fenêtre pour que le panneau
            # graphique ait un ratio proche de celui de l'image réelle de
            # la caméra : sans ça, l'axe pouvait s'étirer bien au-delà de
            # la résolution réelle (ex : jusqu'à 2500 pour une caméra de
            # 1500 px de haut) pour compenser un panneau mal proportionné.
            self._resizeWindowToMatchAspect(imgWidth, imgHeight)
            self._fitViewFullImage(imgWidth, imgHeight)
            self._lastImgSize = (imgWidth, imgHeight)

        self.CalculCentroid()
        self.Coupe()
        self.Back()
        self.updateAiry()
    
    def CalculCentroid(self):
        
        if self.checkBoxAuto.isChecked() is True:
            dataF = gaussian_filter(self.data, 5)
            (self.xec, self.yec) = pylab.unravel_index(dataF.argmax(), self.data.shape)  # prend le max 
            self.vLine.setPos(self.xec)
            self.hLine.setPos(self.yec)   
            self.roi1.setPos([self.xec-(self.r1x), self.yec-(self.r1y)])
            self.roi2.setPos([self.xec-(self.r2), self.yec-(self.r2)])
        
    def _gaussian1D(self, x, amplitude, x0, sigma, offset):
        return offset + amplitude * np.exp(-((x - x0) ** 2) / (2 * sigma ** 2))

    def fitGaussian(self, x, y):
        """
        Ajuste une gaussienne 1D sur (x, y) par moindres carrés.
        Retourne (yFit, fwhm, x0) ou (None, None, None) si l'ajustement
        échoue (peu de points, pas de pic net, non-convergence...).
        FWHM = 2*sqrt(2*ln2)*sigma, calculé directement depuis le sigma
        ajusté (plus précis que la méthode par recherche de racines de
        spline, notamment sur des données bruitées).
        """
        try:
            x = np.asarray(x, dtype=float)
            y = np.asarray(y, dtype=float)
            amplitude0 = np.max(y) - np.min(y)
            x0_0 = x[np.argmax(y)]
            sigma0 = max((x.max() - x.min()) / 10, 1e-3)
            offset0 = np.min(y)
            popt, _ = curve_fit(
                self._gaussian1D, x, y,
                p0=[amplitude0, x0_0, sigma0, offset0],
                maxfev=5000
            )
            amplitude, x0, sigma, offset = popt
            fwhm = 2 * np.sqrt(2 * np.log(2)) * abs(sigma)
            yFit = self._gaussian1D(x, *popt)
            return yFit, round(float(fwhm), 2), x0
        except Exception:
            return None, None, None

    def fwhm(self, x, y, order=3):
        
        """
            Determine full-with-half-maximum of a peaked set of points, x and y.
            Assumes that there is only one peak present in the datasset.  The function
            uses a spline interpolation of order k.
        """
        y = gaussian_filter(y, 5)  # filtre pour reduire le bruit
        half_max = np.amax(y)/2
        try:
            s = splrep(x, y - half_max, k=order)  # Find the B-spline representation of 1-D curve.
            roots = sproot(s)  # Given the knots (>=8) and coefficients of a cubic B-spline return the roots of the spline.
        except:
            roots = 0
           
        if len(roots) > 2:
            pass
            # print( "The dataset appears to have multiple peaks, and ","thus the FWHM can't be determined.")
        elif len(roots) < 2:
            pass
            #  print( "No proper peaks were found in the data set; likely ","the dataset is flat (e.g. all zeros).")
        else:
            return np.around(abs(roots[1] - roots[0]), decimals=2)
         
    def Coupe(self):
        
        xxx = np.arange(0, int(self.dimx), 1)
        yyy = np.arange(0, int(self.dimy), 1)
        coupeX = self.data[int(self.xec), :]  # profil vertical (selon Y)
        coupeY = self.data[:, int(self.yec)]  # profil horizontal (selon X)

        coupeXMax = np.max(coupeX)
        if coupeXMax == 0:  # evite la div par zero
            coupeXMax = 1
        coupeYMax = np.max(coupeY)
        if coupeYMax == 0:
            coupeYMax = 1

        # Données brutes, directement dans leur graphe dédié (plus besoin
        # de normaliser/décaler pour les faire tenir dans l'image : chaque
        # graphe a sa propre échelle auto-ajustée)
        self.curve2.setData(coupeX, yyy, clear=True)
        self.curve3.setData(xxx, coupeY, clear=True)

        # Marge garantie au-delà du pic (30%) pour que le texte FWHM soit
        # toujours visible, peu importe l'auto-range par défaut
        self.pProfileLeft.setXRange(0, coupeXMax * 1.3, padding=0)
        self.pProfileBottom.setYRange(0, coupeYMax * 1.3, padding=0)

        # Unité d'affichage pour le FWHM : µm si "Scale Factor" est coché
        # dans les Préférences, pixels sinon. self.fwhmX/self.fwhmY restent
        # toujours en pixels en interne (utilisés ensuite par CalculE()
        # pour positionner les ROI, qui travaillent en coordonnées pixel).
        scaleOn = self._scaleEnabled()
        stepX = self._stepX()
        stepY = self._stepY()
        unit = 'µm' if scaleOn else 'px'

        # Fit gaussien du profil vertical (coupeX en fonction de yyy) :
        # affiché seulement si le pic dépasse 20 coups (évite de fitter du
        # bruit pur)
        if coupeXMax > 20:
            yFitLeft, fwhmLeftVal, _ = self.fitGaussian(yyy, coupeX)
            if yFitLeft is not None:
                self.curveFitLeft.setData(yFitLeft, yyy)
                self.fwhmY = fwhmLeftVal  # toujours en pixels
                fwhmYDisplay = round(fwhmLeftVal * stepY, 2) if scaleOn else fwhmLeftVal
                self.textX.setText(f'FWHM fit = {fwhmYDisplay} {unit}')
                yPeak = yyy[np.argmax(coupeX)]
                self.textX.setPos(coupeXMax * 1.15, yPeak)
            else:
                self.curveFitLeft.setData([], [])
                self.textX.setText('')
        else:
            self.curveFitLeft.setData([], [])
            self.textX.setText('')

        # Fit gaussien du profil horizontal (coupeY en fonction de xxx)
        if coupeYMax > 20:
            yFitBottom, fwhmBottomVal, _ = self.fitGaussian(xxx, coupeY)
            if yFitBottom is not None:
                self.curveFitBottom.setData(xxx, yFitBottom)
                self.fwhmX = fwhmBottomVal  # toujours en pixels
                fwhmXDisplay = round(fwhmBottomVal * stepX, 2) if scaleOn else fwhmBottomVal
                self.textY.setText(f'FWHM fit = {fwhmXDisplay} {unit}')
                xPeak = xxx[np.argmax(coupeY)]
                self.textY.setPos(xPeak, coupeYMax * 1.15)
            else:
                self.curveFitBottom.setData([], [])
                self.textY.setText('')
        else:
            self.curveFitBottom.setData([], [])
            self.textY.setText('')

    def paletteup(self):
        levels = self.imh.getLevels()
        if levels[0] is None:
            xmax = self.data.max()
            xmin = self.data.min()
        else:
            xmax = levels[1]
            xmin = levels[0]
            
        self.imh.setLevels([xmin, xmax + (xmax - xmin) / 10])
        # hist.setImageItem(imh,clear=True)
        self.hist.setHistogramRange(xmin, xmax)

    def palettedown(self):
        levels = self.imh.getLevels()
        if levels[0] is None:
            xmax = self.data.max()
            xmin = self.data.min()
        else:
            xmax = levels[1]
            xmin = levels[0]
            
        self.imh.setLevels([xmin, xmax - (xmax - xmin) / 10])
        # hist.setImageItem(imh,clear=True)
        self.hist.setHistogramRange(xmin, xmax)

    def roiBackChanged(self):
        bg = self.ROIRect.getArrayRegion(self.dataOrg, self.imh).mean()
        # print(bg)
        self.data = self.dataOrg-bg
        self.CalculE()
    
    def Back(self):
        if self.bckButton.isChecked() is True:
            # Le ROI doit être ajouté à la scène AVANT setPos() : setPos()
            # déclenche sigRegionChangeFinished (-> roiBackChanged), qui a
            # besoin que le ROI et l'image soient déjà dans la même scène.
            self.p1.addItem(self.ROIRect)
            # Centre le carré au centre de l'image la première fois qu'il
            # est affiché (au lieu de rester bloqué à sa position initiale,
            # calculée avec xec/yec lus depuis la config — souvent (0,0) si
            # jamais sauvegardés, donc invisible dans le coin de l'image).
            # Les activations suivantes conservent la position choisie par
            # l'utilisateur si le carré a déjà été déplacé manuellement.
            if not getattr(self, '_roiRectCentered', False):
                w, h = self.ROIRect.size()
                centerX = self.dimx / 2 - w / 2
                centerY = self.dimy / 2 - h / 2
                self.ROIRect.setPos([centerX, centerY])
                self._roiRectCentered = True
            bg = self.ROIRect.getArrayRegion(self.dataOrg, self.imh).mean()
            self.data = self.dataOrg - bg
            self.CalculE()
        else:
            self.p1.removeItem(self.ROIRect)
            self.data = self.dataOrg
            self.CalculE()

    def showEvent(self, event):
        """
        Recalcule la vue une fois la fenêtre effectivement affichée à
        l'écran. Sans ça, le calibrage de la vue fait dans Display()
        (appelé dès __init__, avant que la fenêtre soit affichée) se base
        sur une taille de widget provisoire/incorrecte — d'où le besoin de
        cliquer manuellement sur le bouton "A" (auto-range) du graphique
        pour obtenir un cadrage correct.
        """
        super().showEvent(event)
        imgWidth = self.imh.width()
        imgHeight = self.imh.height()
        if imgWidth and imgHeight:
            self._fitViewFullImage(imgWidth, imgHeight)
            self._lastImgSize = (imgWidth, imgHeight)

    def resizeEvent(self, event):
        """
        Recalcule la vue si la fenêtre est redimensionnée : le ratio
        largeur/hauteur du widget change, donc la marge nécessaire pour
        garder l'image complète visible (sans la rogner) change aussi.
        """
        super().resizeEvent(event)
        imgWidth = self.imh.width()
        imgHeight = self.imh.height()
        if imgWidth and imgHeight:
            self._fitViewFullImage(imgWidth, imgHeight)

    def closeEvent(self, event):
        """ when closing the window
        """
        self.isWinOpen = False
        self.E = []
        self.Xec = []
        self.Yec = []
        time.sleep(0.1)
        event.accept()
     
        
if __name__ == "__main__":
    appli = QApplication(sys.argv) 
    appli.setStyleSheet(qdarkstyle.load_stylesheet(qt_api='pyqt6'))
    e = WINENCERCLED(name='VISU')
    e.show()
    appli.exec_()
