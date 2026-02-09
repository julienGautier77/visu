#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Feb  8 14:46:20 2019
Windows for plot
@author: juliengautier
"""

import pyqtgraph as pg
import qdarkstyle

from PyQt6 import QtCore, QtGui
from PyQt6.QtWidgets import QApplication, QHBoxLayout, QWidget, QStatusBar
from PyQt6.QtWidgets import QVBoxLayout, QLabel, QPushButton, QMessageBox
from PyQt6.QtWidgets import QColorDialog, QInputDialog, QGridLayout
from PyQt6.QtWidgets import QDoubleSpinBox, QMainWindow
from PyQt6.QtWidgets import QTableWidget, QTableWidgetItem, QFileDialog
from PyQt6.QtWidgets import QListWidget, QListWidgetItem
from PyQt6.QtGui import QAction
from PyQt6.QtGui import QIcon
from PyQt6.QtCore import Qt
import numpy as np
import pathlib
from scipy.optimize import curve_fit
from scipy.ndimage import gaussian_filter
from scipy.interpolate import splrep, sproot
import sys
import time
import os


class WINDOWRANGE(QWidget):
    """Small widget to set axis range"""
    def __init__(self):
        super().__init__()
        self.isWinOpen = False
        self.setup()
        
    def setup(self):
        hRangeGrid = QGridLayout()
        
        self.labelXmin = QLabel('Xmin:')
        self.xMinBox = QDoubleSpinBox(self)
        self.xMinBox.setMinimum(-100000)
        self.xMinBox.setMaximum(100000)
        hRangeGrid.addWidget(self.labelXmin, 0, 0)
        hRangeGrid.addWidget(self.xMinBox, 0, 1)
        self.labelXmax = QLabel('Xmax:')
        self.xMaxBox = QDoubleSpinBox(self)
        self.xMaxBox.setMaximum(100000)
        self.xMaxBox.setMinimum(-100000)
        hRangeGrid.addWidget(self.labelXmax, 1, 0)
        hRangeGrid.addWidget(self.xMaxBox, 1, 1)
        
        self.labelYmin = QLabel('Ymin:')
        self.yMinBox = QDoubleSpinBox(self)
        self.yMinBox.setMinimum(-100000)
        self.yMinBox.setMaximum(100000)
        hRangeGrid.addWidget(self.labelYmin, 2, 0)
        hRangeGrid.addWidget(self.yMinBox, 2, 1)
        self.labelYmax = QLabel('Ymax:')
        self.yMaxBox = QDoubleSpinBox(self)
        self.yMaxBox.setMaximum(100000)
        self.yMaxBox.setMinimum(-100000)
        hRangeGrid.addWidget(self.labelYmax, 3, 0)
        hRangeGrid.addWidget(self.yMaxBox, 3, 1)
        self.applyButton = QPushButton('Apply')
        self.ResetButton = QPushButton('Reset')
        hRangeGrid.addWidget(self.applyButton, 4, 0)
        hRangeGrid.addWidget(self.ResetButton, 4, 1)
        self.setLayout(hRangeGrid)

    def closeEvent(self, event):
        self.isWinOpen = False
        time.sleep(0.1)
        event.accept()


class PlotHistoryWidget(QWidget):
    """Widget pour gérer l'historique des plots"""
    def __init__(self, parent=None, max_plots=20):
        super().__init__()
        self.parent = parent
        self.isWinOpen = False
        self.max_plots = max_plots
        p = pathlib.Path(__file__)
        sepa = os.sep
        self.icon = str(p.parent) + sepa + 'icons' + sepa
        self.setWindowTitle('Plot History Manager')
        self.setWindowIcon(QIcon(self.icon+'LOA.png'))
        self.setStyleSheet(qdarkstyle.load_stylesheet(qt_api='pyqt6'))
        self.setGeometry(100, 100, 350, 500)
        self.setup()
        
    def setup(self):
        mainLayout = QVBoxLayout()
        mainLayout.setSpacing(15)
        mainLayout.setContentsMargins(15, 15, 15, 15)
        
        # ===== HEADER =====
        titleLabel = QLabel('📊 Plot History')
        titleLabel.setStyleSheet("""
            font: bold 16pt;
            color: #4dabf7;
            padding: 10px;
        """)
        titleLabel.setAlignment(Qt.AlignmentFlag.AlignCenter)
        mainLayout.addWidget(titleLabel)
        
        # ===== PLOT LIST =====
        listLabel = QLabel('Select plots to display:')
        listLabel.setStyleSheet("font: bold 11pt; color: #adb5bd;")
        mainLayout.addWidget(listLabel)
        
        self.plotList = QListWidget()
        self.plotList.setSelectionMode(QListWidget.SelectionMode.MultiSelection)
        # Changer le signal - utiliser itemClicked au lieu de itemChanged
        self.plotList.itemChanged.connect(self.onItemChanged)
        self.plotList.setStyleSheet("""
            QListWidget {
                background-color: #1e1e1e;
                border: 2px solid #495057;
                border-radius: 8px;
                padding: 5px;
                font: 10pt;
            }
            QListWidget::item {
                padding: 10px;
                margin: 3px;
                border-radius: 5px;
            }
            QListWidget::item:hover {
                background-color: #343a40;
            }
            QListWidget::item:selected {
                background-color: #495057;
            }
        """)
        mainLayout.addWidget(self.plotList)
        
        # ===== ACTION BUTTONS =====
        buttonLayout = QHBoxLayout()
        buttonLayout.setSpacing(10)
        
        self.selectAllBtn = QPushButton('✓ Select All')
        self.selectAllBtn.setStyleSheet("""
            QPushButton {
                background-color: #4dabf7;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 12px 20px;
                font: bold 10pt;
            }
            QPushButton:hover {
                background-color: #339af0;
            }
            QPushButton:pressed {
                background-color: #1c7ed6;
            }
        """)
        self.selectAllBtn.clicked.connect(self.selectAll)
        buttonLayout.addWidget(self.selectAllBtn)
        
        self.deselectAllBtn = QPushButton('✗ Deselect All')
        self.deselectAllBtn.setStyleSheet("""
            QPushButton {
                background-color: #495057;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 12px 20px;
                font: bold 10pt;
            }
            QPushButton:hover {
                background-color: #343a40;
            }
            QPushButton:pressed {
                background-color: #212529;
            }
        """)
        self.deselectAllBtn.clicked.connect(self.deselectAll)
        buttonLayout.addWidget(self.deselectAllBtn)
        
        mainLayout.addLayout(buttonLayout)
        
        # ===== CLEAR BUTTON =====
        self.clearBtn = QPushButton('🗑️ Clear History')
        self.clearBtn.setStyleSheet("""
            QPushButton {
                background-color: #ff6b6b;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 12px;
                font: bold 11pt;
            }
            QPushButton:hover {
                background-color: #fa5252;
            }
            QPushButton:pressed {
                background-color: #e03131;
            }
        """)
        self.clearBtn.clicked.connect(self.clearHistory)
        mainLayout.addWidget(self.clearBtn)
        
        # ===== INFO LABEL =====
        self.infoLabel = QLabel('')
        self.infoLabel.setStyleSheet("""
            color: #adb5bd;
            font: 10pt;
            padding: 8px;
            background-color: #2b2b2b;
            border-radius: 5px;
        """)
        self.infoLabel.setAlignment(Qt.AlignmentFlag.AlignCenter)
        mainLayout.addWidget(self.infoLabel)
        
        # ===== WARNING LABEL =====
        self.warningLabel = QLabel('')
        self.warningLabel.setStyleSheet("""
            color: #ffd43b;
            font: bold 9pt;
            padding: 5px;
        """)
        self.warningLabel.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.warningLabel.setVisible(False)
        mainLayout.addWidget(self.warningLabel)
        
        mainLayout.addStretch()
        
        self.setLayout(mainLayout)
        self.updateInfo()
    
    def addPlot(self, plot_id, label):
        """Ajouter un plot à la liste"""
        # Vérifier si la limite est atteinte
        if self.plotList.count() >= self.max_plots:
            # Supprimer le plus ancien (premier de la liste)
            self.removeOldestPlot()
            self.showWarning(f'⚠️ Maximum {self.max_plots} plots - oldest removed')
        
        # Créer l'item avec icône colorée
        item = QListWidgetItem()
        
        # Extraire la couleur du plot_id depuis le parent
        color = '#ffffff'
        if self.parent is not None:
            for plot_data in self.parent.plot_history:
                if plot_data['id'] == plot_id:
                    color = plot_data['color']
                    break
        
        # Formater le label avec une puce colorée
        formatted_label = f"●  {label}"
        item.setText(formatted_label)
        item.setForeground(QtGui.QColor(color))
        
        item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
        item.setCheckState(Qt.CheckState.Checked)
        item.setData(Qt.ItemDataRole.UserRole, plot_id)
        
        self.plotList.addItem(item)
        self.updateInfo()
    
    def removeOldestPlot(self):
        """Supprimer le plot le plus ancien"""
        if self.plotList.count() > 0:
            first_item = self.plotList.item(0)
            plot_id = first_item.data(Qt.ItemDataRole.UserRole)
            
            # Informer le parent de supprimer ce plot
            if self.parent is not None:
                self.parent.removePlotFromHistory(plot_id)
            
            self.plotList.takeItem(0)
    
    def onItemChanged(self, item):
        """Quand l'état de la checkbox change"""
        # Pas besoin de toggle - Qt gère ça automatiquement
        if self.parent is not None:
            plot_id = item.data(Qt.ItemDataRole.UserRole)
            is_visible = item.checkState() == Qt.CheckState.Checked
            self.parent.setPlotVisibility(plot_id, is_visible)
        
        self.updateInfo()
    
    def selectAll(self):
        """Sélectionner tous les plots"""
        for i in range(self.plotList.count()):
            item = self.plotList.item(i)
            if item.checkState() != Qt.CheckState.Checked:
                item.setCheckState(Qt.CheckState.Checked)
                # Mettre à jour la visibilité
                if self.parent is not None:
                    plot_id = item.data(Qt.ItemDataRole.UserRole)
                    self.parent.setPlotVisibility(plot_id, True)
        self.updateInfo()
    
    def deselectAll(self):
        """Désélectionner tous les plots"""
        for i in range(self.plotList.count()):
            item = self.plotList.item(i)
            if item.checkState() != Qt.CheckState.Unchecked:
                item.setCheckState(Qt.CheckState.Unchecked)
                # Mettre à jour la visibilité
                if self.parent is not None:
                    plot_id = item.data(Qt.ItemDataRole.UserRole)
                    self.parent.setPlotVisibility(plot_id, False)
        self.updateInfo()
    
    def clearHistory(self):
        """Effacer l'historique"""
        if self.plotList.count() == 0:
            return
        
        reply = QMessageBox.question(
            self, 
            'Clear History', 
            f'Are you sure you want to clear all {self.plotList.count()} plots from history?',
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.plotList.clear()
            if self.parent is not None:
                self.parent.clearPlotHistory()
            self.updateInfo()
            self.hideWarning()
    
    def updateInfo(self):
        """Mettre à jour les informations"""
        count = self.plotList.count()
        visible_count = sum(1 for i in range(count) if self.plotList.item(i).checkState() == Qt.CheckState.Checked)
        
        self.infoLabel.setText(f"Plots: {count}/{self.max_plots}  |  Visible: {visible_count}/{count}")  # max_plots au lieu de max_points
    
    def showWarning(self, message):
        """Afficher un message d'avertissement"""
        self.warningLabel.setText(message)
        self.warningLabel.setVisible(True)
        
        # Auto-hide après 3 secondes
        from PyQt6.QtCore import QTimer
        QTimer.singleShot(3000, self.hideWarning)
    
    def hideWarning(self):
        """Cacher le message d'avertissement"""
        self.warningLabel.setVisible(False)
    
    def closeEvent(self, event):
        self.isWinOpen = False
        event.accept()


class WINDOWMEAS(QWidget):
    def __init__(self, title='Plot Measurement'):
        
        super().__init__()
        self.isWinOpen = False
        p = pathlib.Path(__file__)
        sepa = os.sep
        self.title = title
        self.icon = str(p.parent) + sepa + 'icons' + sepa
        self.setWindowTitle(self.title)
        self.setWindowIcon(QIcon(self.icon + 'LOA.png'))
        self.setStyleSheet(qdarkstyle.load_stylesheet(qt_api='pyqt6'))
        self.setup()
        self.setGeometry(50, 100, 200, 350)
    
    def setup(self):
        hLayout1 = QHBoxLayout()
        self.table = QTableWidget()
        hLayout1.addWidget(self.table)
        
        self.table.setColumnCount(1)
        self.table.setRowCount(7)
        self.table.setVerticalHeaderLabels(('Max', 'Min', 'x max', 'x min', 'Mean', 'PV', 'Std'))
        self.setLayout(hLayout1)
    
    def Display(self, cutData, axis=None, fwhm=False, axisOn=False, fit=False, **kwds):
       
        cutData = np.array(cutData)
        Max = round(max(cutData), 3)
        Min = round(min(cutData), 3)
        Mean = round(np.mean(cutData), 3)
        PV = Max - Min
        Std = round(np.std(cutData), 3)
        
        if axisOn is False:
            xmax = np.argmax(cutData)
            xmin = np.argmin(cutData)
        else:
            xmax = np.argmax(cutData)
            xmax = axis[xmax]
            xmin = np.argmin(cutData)
            xmin = axis[xmin]
        
        fit = fit
        self.table.setItem(0, 0, QTableWidgetItem(str(Max)))
        self.table.setItem(1, 0, QTableWidgetItem(str(Min)))
        self.table.setItem(2, 0, QTableWidgetItem(str(xmax)))
        self.table.setItem(3, 0, QTableWidgetItem(str(xmin)))
        self.table.setItem(4, 0, QTableWidgetItem(str(Mean)))
        self.table.setItem(5, 0, QTableWidgetItem(str(PV)))
        self.table.setItem(6, 0, QTableWidgetItem(str(Std)))
        
        if fit is True:
            fitA = kwds["fitA"]
            fitMu = kwds["fitMu"]
            fitSigma = kwds["fitSigma"]
            if fwhm is True:
                self.table.setRowCount(11)
                self.table.setVerticalHeaderLabels(('Max', 'Min', 'x max', 'x min', 'Mean', 'PV', 'Std', 'FWHM', 'Fit A', 'Fit Mu', 'Fit Sigma'))
                self.table.setItem(8, 0, QTableWidgetItem(str(fitA)))
                self.table.setItem(9, 0, QTableWidgetItem(str(fitMu)))
                self.table.setItem(10, 0, QTableWidgetItem(str(fitSigma)))
                
                if axisOn is False:
                    xxx = np.arange(0, np.shape(cutData)[0])
                else:
                    xxx = axis
                
                try:
                    fwhmValue = self.fwhm(xxx, cutData)[0]
                except Exception as e:
                    fwhmValue = ''
                self.table.setItem(7, 0, QTableWidgetItem(str(fwhmValue)))
                
            else:
                self.table.setRowCount(10)
                self.table.setVerticalHeaderLabels(('Max', 'Min', 'x max', 'x min', 'Mean', 'PV', 'Std', 'Fit A', 'Fit Mu', 'Fit Sigma'))
                self.table.setItem(7, 0, QTableWidgetItem(str(round(fitA, 3))))
                self.table.setItem(8, 0, QTableWidgetItem(str(round(fitMu, 3))))
                self.table.setItem(9, 0, QTableWidgetItem(str(round(fitSigma, 3))))
        else:
            if fwhm is True:
                self.table.setRowCount(8)
                self.table.setVerticalHeaderLabels(('Max', 'Min', 'x max', 'x min', 'Mean', 'PV', 'Std', 'FWHM'))
                if axisOn is False:
                    xxx = np.arange(0, np.shape(cutData)[0])
                else:
                    xxx = axis
                
                try:
                    fwhmValue = self.fwhm(xxx, cutData)[0]
                except:
                    fwhmValue = ''
                self.table.setItem(7, 0, QTableWidgetItem(str(round(fwhmValue, 3))))
            else:
                self.table.setVerticalHeaderLabels(('Max', 'Min', 'x max', 'x min', 'Mean', 'PV', 'Std'))
                self.table.setRowCount(7)
                  
    def fwhm(self, x, y, order=3):
        y = gaussian_filter(y, 5)
        half_max = np.amax(y)/2
        
        try:
            s = splrep(x, y - half_max, k=order)
            roots = sproot(s)
        except:
            roots = 0
        
        if len(roots) > 2:
            pass
        elif len(roots) < 2:
            pass
        else:
            return np.around(abs(roots[1] - roots[0]), decimals=2), half_max
    
    def closeEvent(self, event):
        self.isWinOpen = False
        time.sleep(0.1)
        event.accept()


class GRAPHCUT(QMainWindow):
    
    def __init__(self, parent=None, symbol=None, title='Plot', conf=None, name='VISU', meas=False, pen='w', symbolPen='w', label=None, labelY=None, clearPlot=True, lastColored=False):
        
        super().__init__()
        p = pathlib.Path(__file__)
        sepa = os.sep
        self.parent = parent
        self.title = title
        self.icon = str(p.parent) + sepa + 'icons' + sepa
        self.isWinOpen = False
        self.dimx = 10
        self.bloqq = 0
        self.xc = 0
        self.measWidget = WINDOWMEAS()
        self.meas = meas
        self.cutData = np.zeros(self.dimx)
        self.path = None
        self.axisOn = False
        self.lastColored = lastColored
        
        # Historique des plots
        self.plot_history = []  # Liste de dictionnaires contenant les données et paramètres
        self.plot_items = []  # Liste des objets PlotDataItem affichés
        self.plot_counter = 0  # Compteur pour générer des IDs uniques
        self.historyWidget = PlotHistoryWidget(parent=self)
        
        # Palette de couleurs pour les différents plots
        self.color_palette = [
            '#ff6b6b',  # Rouge
            '#51cf66',  # Vert
            '#4dabf7',  # Bleu
            '#ffd43b',  # Jaune
            '#a78bfa',  # Violet
            '#ff9f43',  # Orange
            '#5f3dc4',  # Violet foncé
            '#20c997',  # Turquoise
        ]
        
        if conf is None:
            self.conf = QtCore.QSettings(str(p.parent / 'confVisu.ini'), QtCore.QSettings.Format.IniFormat)
        else:
            self.conf = conf

        self.name = name
        
        self.setWindowTitle(self.title)
        self.setWindowIcon(QIcon(self.icon + 'LOA.png'))
        self.scatter = False
        self.symbol = symbol
        self.axis = None
        self.label = label
        self.labelY = labelY
        self.symbolPen = symbolPen
        self.symbolBrush = 'w'
        self.ligneWidth = 1
        self.color = 'w'
        self.plotRectZoomEtat = "Zoom"
        self.pen = pen
        self.clearPlot = clearPlot
        self.xLog = False
        self.yLog = False
        self.fitA = ""
        self.fitMu = ""
        self.fitSigma = ""
        self.widgetRange = WINDOWRANGE()
        self.setup()
        self.actionButton()
        
    def setup(self):
        
        self.toolBar = self.addToolBar('tools')
        menubar = self.menuBar()
        menubar.setNativeMenuBar(False)
        self.fileMenu = menubar.addMenu('&File')
        self.ImageMenu = menubar.addMenu('&Plot option')
        self.axisMenu = menubar.addMenu('&Axis option')
        self.AnalyseMenu = menubar.addMenu('&Analyse')
        self.historyMenu = menubar.addMenu('&History')  # Nouveau menu History
        
        self.Aboutenu = menubar.addMenu('&About')
        self.statusBar = QStatusBar()
        self.setContentsMargins(5, 5, 5, 5)
        
        self.setStatusBar(self.statusBar)
        
        self.openAct = QAction(QtGui.QIcon(self.icon+"Open.png"), 'Open File', self)
        self.openAct.setShortcut('Ctrl+o')
        self.openAct.triggered.connect(self.OpenF)
        self.toolBar.addAction(self.openAct)
        self.fileMenu.addAction(self.openAct)
        
        self.saveAct = QAction(QtGui.QIcon(self.icon+"disketteSave.png"), 'Save file', self)
        self.saveAct.setShortcut('Ctrl+s')
        self.saveAct.triggered.connect(self.SaveF)
        self.toolBar.addAction(self.saveAct)
        self.fileMenu.addAction(self.saveAct)
        
        # Menu History
        self.showHistoryAct = QAction('Show History', self)
        self.showHistoryAct.setShortcut('Ctrl+h')
        self.showHistoryAct.triggered.connect(lambda: self.open_widget(self.historyWidget))
        self.historyMenu.addAction(self.showHistoryAct)
        
        self.clearHistoryAct = QAction('Clear All Plots', self)
        self.clearHistoryAct.triggered.connect(self.clearPlotHistory)
        self.historyMenu.addAction(self.clearHistoryAct)
        
        self.keepPlotsAct = QAction('Keep Plots in History', self)
        self.keepPlotsAct.setCheckable(True)
        self.keepPlotsAct.setChecked(False)
        self.historyMenu.addAction(self.keepPlotsAct)
        
        vLayout = QVBoxLayout()
        hLayout1 = QHBoxLayout()
        self.checkBoxPlot = QAction(QtGui.QIcon(self.icon+"target.png"), 'Cross On (ctrl+b to block ctrl+d to deblock)', self)
        self.checkBoxPlot.setCheckable(True)
        self.checkBoxPlot.setChecked(False)
        self.checkBoxPlot.triggered.connect(self.PlotXY)
        self.toolBar.addAction(self.checkBoxPlot)
        self.AnalyseMenu.addAction(self.checkBoxPlot)
        
        self.measAction = QAction('Measure')
        self.AnalyseMenu.addAction(self.measAction)
        self.measAction.triggered.connect(lambda: self.open_widget(self.measWidget))
        self.measAction.triggered.connect(lambda: self.measWidget.Display(cutData=self.cutData, axis=self.axis, axisOn=self.axisOn))
        
        self.fwhmAction = QAction('fwhm')
        self.fwhmAction.setCheckable(True)
        self.fwhmAction.setChecked(False)
        self.fwhmAction.triggered.connect(lambda: self.open_widget(self.measWidget))
        self.fwhmAction.triggered.connect(lambda: self.measWidget.Display(cutData=self.cutData, axis=self.axis, axisOn=self.axisOn, fwhm=self.fwhmAction.isChecked(), fit=self.fit, fitA=self.fitA, fitMu=self.fitMu, fitSigma=self.fitSigma))
       
        self.AnalyseMenu.addAction(self.fwhmAction)
        
        self.actionLigne = QAction('Set line', self)
        self.actionLigne.triggered.connect(self.setLine)
        self.actionLigne.setCheckable(True)
        if self.pen is not None:
            self.actionLigne.setChecked(True)
            
        self.ImageMenu.addAction(self.actionLigne)
        
        self.actionColor = QAction('Set line color', self)
        self.actionColor.triggered.connect(self.setColorLine)
        self.ImageMenu.addAction(self.actionColor)
        
        self.actionLigneWidth = QAction('Set line width', self)
        self.actionLigneWidth.triggered.connect(self.setWidthLine)
        self.ImageMenu.addAction(self.actionLigneWidth)
        
        self.label_CrossValue = QLabel()
        self.label_CrossValue.setStyleSheet("font:13pt")
        
        self.label_Cross = QLabel()
        self.label_Cross.setMaximumWidth(170)
        self.label_Cross.setStyleSheet("font:12pt")
        self.statusBar.addPermanentWidget(self.label_Cross)
        self.statusBar.addPermanentWidget(self.label_CrossValue)
        
        if self.meas is True:
            self.label_Mean = QLabel('Mean :')
            hLayout1.addWidget(self.label_Mean)
            self.label_MeanValue = QLabel('...')
            hLayout1.addWidget(self.label_MeanValue)
            self.label_PV = QLabel('PV :')
            hLayout1.addWidget(self.label_PV)
            self.label_PVValue = QLabel('...')
            hLayout1.addWidget(self.label_PVValue)
            self.label_Variance = QLabel('variance :')
            hLayout1.addWidget(self.label_Variance)
            self.label_VarianceValue = QLabel('...')
            hLayout1.addWidget(self.label_VarianceValue)
        
        self.checkBoxSymbol = QAction('Set Symbol on', self)
        self.checkBoxSymbol.setCheckable(True)
        
        if self.symbol is not None:
            self.checkBoxSymbol.setChecked(True)
        self.ImageMenu.addAction(self.checkBoxSymbol)
        self.checkBoxSymbol.triggered.connect(self.setSymbol)
        
        self.checkBoxSymbolColor = QAction('Set Symbol color', self)
        self.ImageMenu.addAction(self.checkBoxSymbolColor)
        self.checkBoxSymbolColor.triggered.connect(self.setColorSymbol)
        
        self.showGridX = QAction('Show X grid', self)
        self.showGridX.setCheckable(True)
        self.ImageMenu.addAction(self.showGridX)
        self.showGridX.triggered.connect(self.showGrid)
        
        self.showGridY = QAction('Show Y grid', self)
        self.showGridY.setCheckable(True)
        self.ImageMenu.addAction(self.showGridY)
        self.showGridY.triggered.connect(self.showGrid)
        
        self.lockGraphAction = QAction('Lock Graph', self)
        self.lockGraphAction.setCheckable(True)
        self.ImageMenu.addAction(self.lockGraphAction)
        self.lockGraphAction.triggered.connect(self.lockGraph)
        
        self.axisRange = QAction('Set Axis Range', self)
        self.axisMenu.addAction(self.axisRange)
        self.axisRange.triggered.connect(self.showRange)
        
        self.logActionX = QAction('Log X', self)
        self.axisMenu.addAction(self.logActionX)
        self.logActionX.setCheckable(True)
        self.logActionX.triggered.connect(self.logMode)
        
        self.logActionY = QAction('Log Y', self)
        self.axisMenu.addAction(self.logActionY)
        self.logActionY.setCheckable(True)
        self.logActionY.triggered.connect(self.logMode)
        
        self.ZoomRectButton = QAction(QtGui.QIcon(self.icon+"loupe.png"), 'Zoom', self)
        self.ZoomRectButton.triggered.connect(self.zoomRectAct)
        self.toolBar.addAction(self.ZoomRectButton)
        
        self.plotRectZoom = pg.RectROI([0, 0], [100, 100], pen='b')
            
        self.fitAction = QAction('Gaussian Fit', self)
        self.AnalyseMenu.addAction(self.fitAction)
        self.fitAction.setCheckable(True)
        
        self.fitAction.triggered.connect(self.setFit)
        self.fitAction.triggered.connect(lambda: self.open_widget(self.measWidget))
        self.fitAction.triggered.connect(lambda: self.measWidget.Display(cutData=self.cutData, axis=self.axis, axisOn=self.axisOn, fwhm=self.fwhmAction.isChecked(), fit=self.fit, fitA=self.fitA, fitMu=self.fitMu, fitSigma=self.fitSigma))
        
        self.vLine = pg.InfiniteLine(angle=90, movable=False, pen='y')
        self.hLine = pg.InfiniteLine(angle=0, movable=False, pen='y')
    
        self.vLine.setPos(0)
        self.hLine.setPos(0)
        
        vLayout.addLayout(hLayout1)
        hLayout2 = QHBoxLayout()
        
        self.winImage = pg.GraphicsLayoutWidget()
        self.winPLOT = self.winImage.addPlot()
        
        if self.label is not None:
            self.winPLOT.setLabel('bottom', self.label)
        if self.labelY is not None:
            self.winPLOT.setLabel('left', self.labelY)
        hLayout2.addWidget(self.winImage)
        vLayout.addLayout(hLayout2)
     
        MainWidget = QWidget()
        
        MainWidget.setLayout(vLayout)
        
        self.setCentralWidget(MainWidget)
        
        self.pCut = self.winPLOT.plot(symbol=self.symbol, symbolPen=self.symbolPen, symbolBrush=self.symbolBrush, pen=self.pen, clear=self.clearPlot)
        self.pCut2 = self.winPLOT.plot(symbol='o', symbolPen='g')
        
        pen = pg.mkPen(color='r', width=3)
        self.pFit = self.winPLOT.plot(pen=pen)

    def addLegend(self):
        self.winPLOT.addLegend(offset=(300, 100))

    def actionButton(self):
        self.proxy = pg.SignalProxy(self.winPLOT.scene().sigMouseMoved, rateLimit=60, slot=self.mouseMoved)
        self.vb = self.winPLOT.vb
        self.winPLOT.scene().sigMouseClicked.connect(self.mouseClick)
        self.widgetRange.applyButton.clicked.connect(self.setRangeOn)
        self.widgetRange.ResetButton.clicked.connect(self.setRangeReset)
        if self.parent is not None:
            self.parent.signalPlot.connect(self.PLOTSIG)
    
    def addToHistory(self, cutData, axis=None, label=None):
        """Ajouter un plot à l'historique"""
        if not self.keepPlotsAct.isChecked():
            return
        
        self.plot_counter += 1
        plot_id = self.plot_counter
        
        # Choisir une couleur dans la palette
        color_index = (self.plot_counter - 1) % len(self.color_palette)
        color = self.color_palette[color_index]
        
        # Créer un label pour l'historique
        if label is None:
            timestamp = time.strftime("%H:%M:%S")
            hist_label = f"Plot #{plot_id} - {timestamp}"
        else:
            hist_label = f"{label} (#{plot_id})"
        
        # Stocker les données
        plot_data = {
            'id': plot_id,
            'data': np.array(cutData),
            'axis': np.array(axis) if axis is not None else None,
            'label': hist_label,
            'color': color,
            'visible': True,
            'plot_item': None
        }
        
        self.plot_history.append(plot_data)
        
        # Créer le plot item
        pen = pg.mkPen(color=color, width=1.5)
        if axis is not None:
            plot_item = self.winPLOT.plot(y=cutData, x=axis, pen=pen, name=hist_label)
        else:
            plot_item = self.winPLOT.plot(cutData, pen=pen, name=hist_label)
        
        plot_data['plot_item'] = plot_item
        
        # Ajouter à la liste du widget historique
        self.historyWidget.addPlot(plot_id, hist_label)
        
        #  print(f"Added to history: {hist_label}")

    def removePlotFromHistory(self, plot_id):

        """Supprimer un plot spécifique de l'historique"""
        for i, plot_data in enumerate(self.plot_history):
            if plot_data['id'] == plot_id:
                # Supprimer du graphique
                if plot_data['plot_item'] is not None:
                    self.winPLOT.removeItem(plot_data['plot_item'])
                # Supprimer de la liste
                self.plot_history.pop(i)
                #  print(f"Removed plot #{plot_id} from history")
                break

    def setPlotVisibility(self, plot_id, visible):
        """Afficher/masquer un plot de l'historique"""
        for plot_data in self.plot_history:
            if plot_data['id'] == plot_id:
                plot_data['visible'] = visible
                if plot_data['plot_item'] is not None:
                    if visible:
                        plot_data['plot_item'].show()
                    else:
                        plot_data['plot_item'].hide()
                break
    
    def clearPlotHistory(self):
        """Effacer tout l'historique des plots"""
        # Supprimer tous les plot items du graphique
        for plot_data in self.plot_history:
            if plot_data['plot_item'] is not None:
                self.winPLOT.removeItem(plot_data['plot_item'])
        
        # Vider la liste
        self.plot_history.clear()
        self.plot_counter = 0
        
        # Réafficher le plot actuel
        self.CHANGEPLOT(self.cutData)
        
    def OpenF(self, fileOpen=False):

        if fileOpen is False:
            chemin = self.conf.value(self.name+"/path")
            fname = QFileDialog.getOpenFileName(self, "Open File", chemin, " 1D data (*.txt )")
            fichier = fname[0]
        else:
            fichier = str(fileOpen)
    
        ext = os.path.splitext(fichier)[1]
        
        if ext == '.txt':
            self.cutData = np.genfromtxt(fichier, delimiter=" ")
            self.PLOT(self.cutData)
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
        self.path = os.path.dirname(str(fname[0]))
        fichier = fname[0]
        
        print(fichier, ' is saved')
        self.conf.setValue(self.name+"/path", self.path)
        time.sleep(0.1)
        if self.axis is None:
            np.savetxt(str(fichier)+'.txt', self.cutData)
        else:
            saveData = np.array([self.axis, self.cutData])
            saveData = saveData.T
            np.savetxt(str(fichier)+'.txt', saveData)
        
    def mouseMoved(self, evt):
        
        if self.checkBoxPlot.isChecked() is False:
            
            if self.bloqq == 0:
                pos = evt[0]
                if self.winPLOT.sceneBoundingRect().contains(pos):
                
                    mousePoint = self.vb.mapSceneToView(pos)
                    
                    self.xMouse = (mousePoint.x())
                    self.yMouse = (mousePoint.y())
                    if self.axisOn is True:
                        
                        if (self.xMouse > self.axis.min()-10 and self.xMouse < self.axis.max() + 10):
                            self.xMc = self.xMouse
                            self.yMc = self.yMouse
                            self.label_Cross.setText('x=' + str(round((self.xMc), 2)) + ' y=' + str(round(self.yMc, 2)))
                    else:
                        if (self.xMouse > -1 and self.xMouse < self.dimx - 1):
                            self.xMc = int(self.xMouse)
                            self.yMc = self.cutData[self.xMc]
                            self.label_Cross.setText('x=' + str(round((self.xMc), 2)) + ' y=' + str(round(self.cutData[self.xMc], 2)))
                            
        if self.checkBoxPlot.isChecked() and self.bloqq == 0:
            pos = evt[0]
            if self.winPLOT.sceneBoundingRect().contains(pos):
                mousePoint = self.vb.mapSceneToView(pos)
                self.xMouse = (mousePoint.x())
                self.yMouse = (mousePoint.y())
                if self.axisOn is True:
                
                    if (self.xMouse > self.axis.min()-10 and self.xMouse < self.axis.max() + 10):
                        self.xc = int(self.xMouse)
                        self.yc = self.yMouse
                        self.vLine.setPos(self.xc)
                        self.hLine.setPos(self.yc)
                        self.affiCross()
                else: 
                    if (self.xMouse > -1 and self.xMouse < self.dimx - 1):
                        self.xc = int(self.xMouse)
                        self.yc = self.cutData[self.xc]
                        self.vLine.setPos(self.xc)
                        self.hLine.setPos(self.yc)     
                        self.affiCross()
    
    def affiCross(self):
        if self.checkBoxPlot.isChecked():
            if self.axisOn is True:
                self.label_Cross.setText('x=' + str(round((self.xc), 2)) + ' y=' + str(round(self.yc, 2)))
            else:
                self.label_Cross.setText('x=' + str(round((self.xc), 2)) + ' y=' + str(round(self.cutData[self.xc], 2)))
            
    def mouseClick(self):
        if self.bloqq == 1:
            self.bloqq = 0
        else:
            self.bloqq = 1
            
    def PlotXY(self):
        if self.checkBoxPlot.isChecked():
            self.winPLOT.addItem(self.vLine, ignoreBounds=False)
            self.winPLOT.addItem(self.hLine, ignoreBounds=False)
            self.vLine.setPos(self.xc)
            self.hLine.setPos(self.cutData[self.xc])
        else:
            self.winPLOT.removeItem(self.vLine)
            self.winPLOT.removeItem(self.hLine)
    
    def PLOTSIG(self, P):
        
        cutData = P['data']
        try:
            axis = P['axis']
        except:
            axis = None
        try:
            label = P['label']
        except:
            label = None
        try:
            labelY = P['labelY']
        except:
            labelY = None
                
        self.PLOT(cutData, axis=axis, label=label, labelY=labelY)
    
    def PLOT(self, cutData, axis=None, label=None, labelY=None):
        self.label = label
        self.labelY = labelY
        self.cutData = cutData
        self.axis = axis
        
        # Ajouter à l'historique si activé
        if self.keepPlotsAct.isChecked():
            self.addToHistory(cutData, axis=axis, label=label)
        
        self.dimy = max(cutData)
        self.minY = min(cutData)
        if self.axis is None:
            self.dimx = np.shape(self.cutData)[0]
            self.minX = 0
            self.data = self.cutData
            
            if self.clearPlot is False:
                self.pCut = self.winPLOT.plot(self.cutData, clear=self.clearPlot, symbol=self.symbol, symbolPen=self.symbolPen, symbolBrush=self.symbolBrush, pen=self.pen)          
            else:
                self.pCut.setData(self.data)
            self.axisOn = False
        else:
            self.axis = np.array(axis)
            self.dimx = max(self.axis)
            self.minX = min(self.axis)
            if self.clearPlot is False:
                self.pCut = self.winPLOT.plot(y=self.cutData, x=self.axis, clear=self.clearPlot, symbol=self.symbol, symbolPen=self.symbolPen, symbolBrush=self.symbolBrush, pen=self.pen)
            else:
                if self.lastColored is True:
                    
                    if self.scatter is True: 
                        self.winPLOT.removeItem(self.scatter_point)
                        
                    self.scatter_point = pg.ScatterPlotItem(
                        x=self.axis[-1].flatten(), 
                        y=self.cutData[-1].flatten(), 
                        pen=None,
                        symbol='d',
                        brush=pg.mkBrush(255, 0, 0),
                        size=15,
                        symbolBrush='r',
                        name='Last Shoot')
                    self.winPLOT.addItem(self.scatter_point)
                    self.scatter = True
                    self.uniqueAxis = np.unique(self.axis)
                    self.cutData = np.array(self.cutData)
                    self.axis = np.array(self.axis)
                    self.moy = np.array([np.mean(self.cutData[self.axis == val]) for val in self.uniqueAxis])
                    
                    self.pCut2.setData(y=self.moy, x=self.uniqueAxis, clear=False, symbol='o', symbolPen=self.symbolPen, symbolBrush='g', pen=self.pen, name='Mean')
                self.pCut.setData(y=self.cutData[:-1], x=self.axis[:-1], clear=self.clearPlot, symbol=self.symbol, symbolPen=self.symbolPen, symbolBrush=self.symbolBrush, pen=self.pen)
    
            self.axisOn = True
            
        self.zoomRectupdate()
        self.setFit()
        if self.label is not None:
            self.winPLOT.setLabel('bottom', self.label)
        if self.labelY is not None:
            self.winPLOT.setLabel('left', self.labelY)
        self.fit = self.fitAction.isChecked()
        
        self.measWidget.Display(cutData=self.cutData, axis=self.axis, axisOn=self.axisOn, fwhm=self.fwhmAction.isChecked(), fit=self.fit, fitA=self.fitA, fitMu=self.fitMu, fitSigma=self.fitSigma)
       
    def CHANGEPLOT(self, cutData):
        if self.axis is None:
            self.pCut = self.winPLOT.plot(self.cutData, clear=self.clearPlot, symbol=self.symbol, symbolPen=self.symbolPen, symbolBrush=self.symbolBrush, pen=self.pen)
        else:
            self.axisOn = True
            self.pCut = self.winPLOT.plot(y=self.cutData, x=self.axis, clear=self.clearPlot, symbol=self.symbol, symbolPen=self.symbolPen, symbolBrush=self.symbolBrush, pen=self.pen)
            
        if self.label is not None:
            self.winPLOT.setLabel('bottom', self.label)
        if self.labelY is not None:
            self.winPLOT.setLabel('left', self.labelY)
            
        self.affiCross()
        self.fit = self.fitAction.isChecked()

        if self.fitAction.isChecked():
            self.pFit = self.winPLOT.plot(pen='r')
            self.setFit()
            
        if self.meas is True:
            self.label_MeanValue.setText(str(round(np.mean(self.cutData), 3)))
            self.label_PVValue.setText(str(round(np.ptp(self.cutData), 3)))
            self.label_VarianceValue.setText(str(round(np.var(self.cutData), 3)))
       
    def SetTITLE(self, title):
        self.setWindowTitle(title)
    
    def dragEnterEvent(self, e):
        e.accept()

    def dropEvent(self, e):
        listFile = []
        for url in e.mimeData().urls():
            listFile.append(str(url.toLocalFile()))
        e.accept()
        self.OpenF(fileOpen=listFile[0])
    
    def setLine(self):
        if self.actionLigne.isChecked():
            self.pen = None
        else:
            self.pen = pg.mkPen(color=self.color, width=self.ligneWidth)
            
        self.CHANGEPLOT(self.cutData)
    
    def setColorLine(self):
        color = QColorDialog.getColor()
        self.color = str(color.name())
        self.pen = pg.mkPen(color=self.color, width=self.ligneWidth)
        self.CHANGEPLOT(self.cutData)
    
    def setWidthLine(self):
        num, ok = QInputDialog.getInt(self, "Line width", "enter a width ")
        if ok:
            self.ligneWidth = float(num)
            self.pen = pg.mkPen(color=self.color, width=self.ligneWidth)
            self.CHANGEPLOT(self.cutData)
            
    def setColorSymbol(self):
        color = QColorDialog.getColor()
        self.colorSymbol = str(color.name())
        self.symbolPen = pg.mkPen({'color': self.colorSymbol})
        self.symbolBrush = pg.mkBrush(self.colorSymbol)
        self.CHANGEPLOT(self.cutData)
    
    def showGrid(self):
        self.winPLOT.showGrid(x=self.showGridX.isChecked(), y=self.showGridY.isChecked())
        
    def setSymbol(self):
        if self.checkBoxSymbol.isChecked():
            self.symbol = 't'
        else:
            self.symbol = None
        
        self.CHANGEPLOT(self.cutData)
       
    def zoomRectAct(self):
        
        if self.plotRectZoomEtat == "Zoom":
            [[xmin, xmax], [ymin, ymax]] = self.winPLOT.viewRange()
            self.winPLOT.addItem(self.plotRectZoom)
            
            self.plotRectZoom.setPos([xmin+(xmax-xmin)/2, ymin+(ymax-ymin)/2])
            self.ZoomRectButton.setIcon(QtGui.QIcon(self.icon+"zoom-in.png"))
            self.plotRectZoomEtat = "ZoomIn"
            
        elif self.plotRectZoomEtat == "ZoomIn":
            self.ZoomRectButton.setIcon(QtGui.QIcon(self.icon+"zoom-out.png"))
            self.xZoomMin = (self.plotRectZoom.pos()[0])
            self.yZoomMin = (self.plotRectZoom.pos()[1])
            self.xZoomMax = (self.plotRectZoom.pos()[0])+self.plotRectZoom.size()[0]
            self.yZoomMax = (self.plotRectZoom.pos()[1])+self.plotRectZoom.size()[1]
            self.winPLOT.setXRange(self.xZoomMin, self.xZoomMax)
            self.winPLOT.setYRange(self.yZoomMin, self.yZoomMax)
            self.winPLOT.removeItem(self.plotRectZoom)
            
            self.plotRectZoomEtat = "ZoomOut"
        
        elif self.plotRectZoomEtat == "ZoomOut":
            self.winPLOT.setYRange(self.minY, self.dimy)
            self.winPLOT.setXRange(self.minX, self.dimx)
            self.ZoomRectButton.setIcon(QtGui.QIcon(self.icon+"loupe.png"))
            self.plotRectZoomEtat = "Zoom"
            
    def zoomRectupdate(self):
        if self.plotRectZoomEtat == "ZoomOut":
            self.winPLOT.setXRange(self.xZoomMin, self.xZoomMax)
            self.winPLOT.setYRange(self.yZoomMin, self.yZoomMax)
    
    def showRange(self):
        self.open_widget(self.widgetRange)
        
    def setRangeOn(self):
        self.xZoomMin = (self.widgetRange.xMinBox.value())
        self.yZoomMin = (self.widgetRange.yMinBox.value())
        self.xZoomMax = (self.widgetRange.xMaxBox.value())
        self.yZoomMax = (self.widgetRange.yMaxBox.value())
        self.winPLOT.setXRange(self.xZoomMin, self.xZoomMax)
        self.winPLOT.setYRange(self.yZoomMin, self.yZoomMax)
        self.plotRectZoomEtat = "ZoomIn"
        
    def setRangeReset(self):
        self.winPLOT.setYRange(self.minY, self.dimy)
        self.winPLOT.setXRange(self.minX, self.dimx)
        self.plotRectZoomEtat = "Zoom"
     
    def lockGraph(self):
        if self.lockGraphAction.isChecked():
            self.clearPlot = False
        else:
            self.clearPlot = True
        self.CHANGEPLOT(self.cutData)
    
    def logMode(self):
        if self.logActionY.isChecked():
            self.yLog = True
        else:
            self.yLog = False
        if self.logActionX.isChecked():
            self.xLog = True
        else:
            self.xLog = False
        self.winPLOT.setLogMode(x=self.xLog, y=self.yLog)
        self.CHANGEPLOT(self.cutData)
        
    def setXlog(self):
        self.logActionX.setChecked(True)
        self.xLog = True
        self.winPLOT.setLogMode(x=self.xLog, y=self.yLog)

    def setYlog(self):
        self.logActionY.setChecked(True)
        self.yLog = True
        self.winPLOT.setLogMode(x=self.xLog, y=self.yLog)

    def setFit(self):
        self.fit = self.fitAction.isChecked()
        if self.fitAction.isChecked():
            try:
                if self.axis is None:
                    xxx = np.arange(0, int(self.dimx), 1)
                else:
                    xxx = self.axis
            except:
                if self.axis.any is None:
                    xxx = np.arange(0, int(self.dimx), 1)
                else:
                    xxx = self.axis
            try:
                Datafwhm, xDataMax = self.fwhm(xxx, self.cutData)
                xmaxx = self.cutData.max()
                ymaxx = self.cutData[int(xmaxx)]
            except:
                xmaxx, ymaxx, Datafwhm = 0, 0, 0
              
            init_vals = [ymaxx, xmaxx, Datafwhm, 0]
            try:
                best_vals, covar = curve_fit(self.gauss, xxx, gaussian_filter(self.cutData, 5), p0=init_vals)
                y_fit = self.gauss(xxx, best_vals[0], best_vals[1], best_vals[2], best_vals[3])
                self.pFit.setData(x=xxx, y=y_fit)
            except:
                y_fit = [0]
                self.pFit.setData(x=[], y=[], clear=True)
            
            self.fitA = best_vals[0]
            self.fitMu = best_vals[1]
            self.fitSigma = best_vals[2]
            
        else:
            self.pFit.setData(x=[], y=[], clear=True)
            
    def open_widget(self, fene):
        if fene.isWinOpen is False:
            fene.setup
            fene.isWinOpen = True
            fene.show()
        else:
            fene.raise_()
            fene.showNormal()
    
    def fwhm(self, x, y, order=3):
        y = gaussian_filter(y, 5)
        half_max = np.amax(y)/2
        
        try:
            s = splrep(x, y - half_max, k=order)
            roots = sproot(s)
        except:
            roots = 0
        
        if len(roots) > 2:
            pass
        elif len(roots) < 2:
            pass
        else:
            return np.around(abs(roots[1] - roots[0]), decimals=2), half_max
    
    def gauss(self, x, A, mu, sigma, B):
        if sigma == 0:
            return 0
        else:
            return A*np.exp(-(x-mu)**2/(2.*sigma**2))+B
    
    def plot2D(self, cutData, axis=None, symbol=None, pen='r', symbolPen='w', clearPlot=False, legend=''):
        self.symbol = symbol
        self.symbolPen = symbolPen
        self.pen = pen
        self.cutData = cutData
        self.axis = axis
        self.dimy = max(cutData)
        self.minY = min(cutData)
        if self.axis is None:
            self.dimx = np.shape(self.cutData)[0]
            self.minX = 0
            self.data = self.cutData
            self.pCut = self.winPLOT.plot(y=cutData, clear=clearPlot, symbol=symbol, symbolPen=symbolPen, pen=pen, name=legend)
            self.axisOn = False
        else:
            self.axis = np.array(axis)
            self.dimx = max(self.axis)
            self.minX = min(self.axis)
            self.pCut = self.winPLOT.plot(y=cutData, x=axis, clear=clearPlot, symbol=symbol, symbolPen=symbolPen, pen=pen, name=legend)
            self.axisOn = True

    def closeEvent(self, event):
        self.isWinOpen = False
        time.sleep(0.1)
        event.accept()
        if self.measWidget.isWinOpen is True:
            self.measWidget.close()
        if self.widgetRange.isWinOpen is True:
            self.widgetRange.close()
        if self.historyWidget.isWinOpen is True:
            self.historyWidget.close()


if __name__ == "__main__":

    appli = QApplication(sys.argv)
    e = GRAPHCUT()
    a = [2, 3, 7, 100, 1000]
    b = [2, 4, 5, 100, 2000]
    e.PLOT(a, b)
    e.show()
    appli.exec()