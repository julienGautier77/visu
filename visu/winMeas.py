#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Window for Measurement
Réécriture avec connexion ZMQ directe au serveur RSAI
Sans utiliser le client MOTORRSAI complet

@author: juliengautier
@modified: 2025 - Connexion ZMQ directe
"""

import qdarkstyle
from PyQt6 import QtCore, QtGui
from PyQt6.QtWidgets import (QApplication, QVBoxLayout, QHBoxLayout, QMainWindow, 
                              QHeaderView, QWidget, QTableWidget, QTableWidgetItem, 
                              QAbstractItemView, QComboBox, QInputDialog, QLabel,
                              QDialog, QLineEdit, QDialogButtonBox, QFormLayout,
                              QMessageBox, QGroupBox)
from PyQt6.QtGui import QAction, QIcon
from PyQt6.QtCore import Qt, QMutex,QTimer
from visu.WinCut import GRAPHCUT
from visu.winZoom import ZOOM
import pathlib
import numpy as np
import sys
import time
import os
import zmq
import ast
from scipy import ndimage


class ServerConfigDialog(QDialog):
    """
    Dialogue pour configurer l'adresse IP et le port du serveur ZMQ
    """
    
    def __init__(self, current_host='localhost', current_port='5555', parent=None):
        super().__init__(parent)
        self.setWindowTitle("Configuration Serveur ZMQ")
        self.setModal(True)
        self.setMinimumWidth(350)
        
        # Appliquer le style sombre
        self.setStyleSheet(qdarkstyle.load_stylesheet(qt_api='pyqt6'))
        
        layout = QVBoxLayout()
        
        # Groupe de configuration
        groupBox = QGroupBox("Paramètres du serveur RSAI")
        formLayout = QFormLayout()
        
        # Champ IP/Host
        self.hostEdit = QLineEdit(current_host)
        self.hostEdit.setPlaceholderText("Ex: 192.168.1.100 ou localhost")
        formLayout.addRow("Adresse IP / Host:", self.hostEdit)
        
        # Champ Port
        self.portEdit = QLineEdit(current_port)
        self.portEdit.setPlaceholderText("Ex: 5555")
        formLayout.addRow("Port:", self.portEdit)
        
        groupBox.setLayout(formLayout)
        layout.addWidget(groupBox)
        
        # Info
        infoLabel = QLabel("⚠️ Les modifications seront appliquées au prochain démarrage.")
        infoLabel.setStyleSheet("color: orange; font-style: italic;")
        layout.addWidget(infoLabel)
        
        # Boutons
        buttonBox = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | 
            QDialogButtonBox.StandardButton.Cancel
        )
        buttonBox.accepted.connect(self.accept)
        buttonBox.rejected.connect(self.reject)
        layout.addWidget(buttonBox)
        
        self.setLayout(layout)
    
    def getValues(self):
        """Retourne les valeurs saisies"""
        return self.hostEdit.text().strip(), self.portEdit.text().strip()


class ZMQMotorClient:
    """
    Client ZMQ léger pour communiquer avec le serveur RSAI
    Basé sur le code fonctionnel de mainMotor.py
    """
    
    def __init__(self, server_host='localhost', server_port='5555'):
        self.server_address = f"tcp://{server_host}:{server_port}"
        self.context = zmq.Context()
        self.socket = None
        self.isconnected = False
        self.server_available = False
        self.mut = QMutex()
        self._connect()
    
    def _connect(self):
        """Établit la connexion ZMQ DEALER"""
        try:
            if self.socket:
                self.socket.close()
            
            self.socket = self.context.socket(zmq.DEALER)
            self.socket.setsockopt(zmq.RCVTIMEO, 5000)  # 5s timeout
            self.socket.setsockopt(zmq.SNDTIMEO, 5000)
            self.socket.setsockopt(zmq.LINGER, 1000)
            self.socket.setsockopt(zmq.SNDHWM, 100)
            self.socket.setsockopt(zmq.RCVHWM, 100)
            
            # Identité unique
            import uuid
            identity = f"MEAS_{uuid.uuid4()}".encode('utf-8')
            self.socket.setsockopt(zmq.IDENTITY, identity)
            
            self.socket.connect(self.server_address)
            
            # Vider le buffer au démarrage (comme dans mainMotor.py)
            self.socket.setsockopt(zmq.LINGER, 0)
            self.socket.setsockopt(zmq.RCVTIMEO, 1000)  # Timeout 1 seconde
            
            # Vider les messages résiduels éventuels
            try:
                while True:
                    self.socket.recv(zmq.NOBLOCK)
                    print("🧹 Message résiduel vidé")
            except zmq.Again:
                print("✅ Buffer vidé, socket prêt")
            
            # Remettre le timeout normal
            self.socket.setsockopt(zmq.RCVTIMEO, 5000)
            
            self.isconnected = True
            self.server_available = True
            print(f"✅ ZMQMotorClient connecté à {self.server_address}")
            time.sleep(0.5)  # Attendre un peu comme dans mainMotor.py
            
        except Exception as e:
            self.isconnected = False
            self.server_available = False
            print(f"❌ Erreur connexion ZMQ: {e}")
    
    def sendMessage(self, message):
        """Envoie un message et retourne la réponse"""
        if not self.server_available:
            print("⚠️ Serveur non disponible")
            return "error: server not available"
        
        self.mut.lock()
        try:
            # DEALER envoie: [frame vide, message]
            self.socket.send(b'', zmq.SNDMORE)
            self.socket.send_string(message)
            
            # Recevoir: frame vide + réponse
            empty = self.socket.recv()
            retour_brut = self.socket.recv_string()
            
            # Nettoyer la réponse
            response = retour_brut.strip()
            
            self.isconnected = True
            self.server_available = True
            return response
            
        except zmq.Again:
            print(f"⏱️ Timeout ZMQ pour: {message}")
            self.isconnected = False
            self.server_available = False
            return "error: timeout"
        except Exception as e:
            print(f"❌ Erreur ZMQ: {e}")
            self.isconnected = False
            self.server_available = False
            return f"error: {e}"
        finally:
            self.mut.unlock()
    
    def getListRack(self):
        """Récupère la liste des IPs des racks"""
        response = self.sendMessage("listRack")
        print(f"📋 getListRack response: '{response}'")
        try:
            result = ast.literal_eval(response)
            print(f"📋 Liste des racks: {result}")
            return result
        except Exception as e:
            print(f"❌ Erreur parsing listRack: {e}")
            return []
    
    def getDict(self):
        """Récupère le dictionnaire des moteurs"""
        response = self.sendMessage("dict")
        print(f"📋 getDict response length: {len(response)}")
        try:
            result = ast.literal_eval(response)
            return result
        except Exception as e:
            print(f"❌ Erreur parsing dict: {e}")
            return {}
    
    def getNbMotorRack(self):
        """Récupère le nombre de moteurs par rack"""
        response = self.sendMessage("nbMotRack")
        print(f"📋 getNbMotorRack response: '{response}'")
        try:
            return ast.literal_eval(response)
        except:
            return []
    
    def getRackName(self, ip):
        """Récupère le nom du rack"""
        response = self.sendMessage(f"{ip}, 1, nomRack")
        return response if response else ip
    
    def getMotorList(self, ip, dict_moteurs):
        """Récupère la liste des noms de moteurs pour un rack"""
        dict_name = f"self.dictMotor_{ip}"
        print(f"🔍 Recherche moteurs pour: {dict_name}")
        print(f"🔍 Clés disponibles: {list(dict_moteurs.keys())}")
        
        if dict_name in dict_moteurs:
            motor_dict = dict_moteurs[dict_name]
            motor_names = []
            # Trier les clés numériques
            numeric_keys = sorted([k for k in motor_dict.keys() if isinstance(k, int)])
            for key in numeric_keys:
                # Récupérer le nom du moteur
                name = self.sendMessage(f"{ip}, {key}, name")
                motor_names.append(name if name else f"Motor_{key}")
            print(f"📋 Moteurs trouvés: {motor_names}")
            return motor_names
        return []
    
    def getMotorListFromCount(self, ip, count):
        """Récupère la liste des noms de moteurs en utilisant le nombre de moteurs"""
        motor_names = []
        for i in range(1, count + 1):
            name = self.sendMessage(f"{ip}, {i}, name")
            motor_names.append(name if name else f"Motor_{i}")
        return motor_names
    
    def getPosition(self, ip, numMotor):
        """Récupère la position du moteur"""
        response = self.sendMessage(f"{ip}, {numMotor}, position")
        try:
            return float(response)
        except:
            return 0.0
    
    def getStep(self, ip, numMotor):
        """Récupère la valeur du pas"""
        response = self.sendMessage(f"{ip}, {numMotor}, step")
        try:
            return float(response)
        except:
            return 1.0
    
    def getMotorName(self, ip, numMotor):
        """Récupère le nom du moteur"""
        return self.sendMessage(f"{ip}, {numMotor}, name")
    
    def close(self):
        """Ferme la connexion"""
        try:
            if self.socket:
                self.socket.close()
            self.context.term()
        except:
            pass
        self.isconnected = False


class MEAS(QMainWindow):
    
    signalPlot = QtCore.pyqtSignal(object)
    
    def __init__(self, parent=None, conf=None, name='VISU', confMot=None, **kwds):
        
        super().__init__()

        self.parent = parent
        self.setStyleSheet(qdarkstyle.load_stylesheet(qt_api='pyqt6'))
        p = pathlib.Path(__file__)
        sepa = os.sep
        
        if conf is None:
            self.conf = QtCore.QSettings(str(p.parent / 'confVisu.ini'), QtCore.QSettings.Format.IniFormat)
        else:
            self.conf = conf
        self.confMot = confMot
        self.name = name
        self.ThresholdState = False
        self.symbol = False
        
        # Configuration serveur ZMQ
        self.serverHost = 'localhost'
        self.serverPort = '5555'
        
        # Lecture config serveur si disponible
        fileconf = str(p.parent) + sepa + "confServer.ini"
        if os.path.exists(fileconf):
            confServer = QtCore.QSettings(fileconf, QtCore.QSettings.Format.IniFormat)
            self.serverHost = str(confServer.value('MAIN/server_host', 'localhost'))
            self.serverPort = str(confServer.value('MAIN/serverPort', '5555'))
        
        # Gestion moteurs RSAI via ZMQ
        self.motRSAI = kwds.get('motRSAI', False)
        self.zmqClient = None
        self.listRack = []
        self.listRackNames = []
        self.listMotorName = []
        self.dict_moteurs = {}
        self.currentIP = None
        self.currentMotorNum = 0
        self.stepmotor = 1
        
        if self.motRSAI:
            self._initZMQConnection()
        
        # Gestion moteurs A2V (inchangé)
        self.motA2V = kwds.get('motA2V', False)
        if self.motA2V:
            sys.path.append('C:/Users/UPX/Desktop/python/camera')
            import moteurA2V as A2V
            self.A2V = A2V
            self.listMotorName = self.A2V.listMotorName
            self.listMotor = self.A2V.listMotor
            print('TMCL motor connected to database')

        self.indexUnit = 1  # micron
        self.icon = str(p.parent) + sepa + 'icons' + sepa
        self.isWinOpen = False
        self.setup()
        
        self.setWindowTitle('MEASUREMENTS')
        self.shoot = 0
        self.nomFichier = ' '
        self.TableSauv = ['file,Max,Min,x Max,y max,Sum,Mean,Size,x c.mass,y c.mass,user1']
        
        self.path = self.conf.value(self.name + "/path")
        
        # Création des fenêtres de graphiques
        self.winCoupeMax = GRAPHCUT(parent=self, conf=self.conf, name=self.name, symbol='t', pen=None, lastColored=True)
        self.winCoupeMin = GRAPHCUT(parent=self, conf=self.conf, name=self.name, symbol='t', pen=None, lastColored=True)
        self.winCoupeXmax = GRAPHCUT(parent=self, conf=self.conf, name=self.name, symbol='t', pen=None, lastColored=True)
        self.winCoupeYmax = GRAPHCUT(parent=self, conf=self.conf, name=self.name, symbol='t', pen=None, lastColored=True)
        self.winCoupeSum = GRAPHCUT(parent=self, conf=self.conf, name=self.name, symbol='t', pen=None, lastColored=True)
        self.winCoupeMean = GRAPHCUT(parent=self, conf=self.conf, name=self.name, symbol='t', pen=None, lastColored=True)
        self.winCoupeXcmass = GRAPHCUT(parent=self, conf=self.conf, name=self.name, symbol='t', pen=None, lastColored=True)
        self.winCoupeYcmass = GRAPHCUT(parent=self, conf=self.conf, name=self.name, symbol='t', pen=None, lastColored=True)
        self.winCoupeSumThreshold = GRAPHCUT(parent=self, conf=self.conf, name=self.name, symbol='t', pen=None, lastColored=True)
        self.winCoupeUser1 = GRAPHCUT(parent=self, conf=self.conf, name=self.name, symbol='t', pen=None, lastColored=True)
        self.signalTrans = dict()
        
        # Listes de données
        self.Maxx = []
        self.Minn = []
        self.Summ = []
        self.Mean = []
        self.Xmax = []
        self.Ymax = []
        self.Xcmass = []
        self.Ycmass = []
        self.labelsVert = []
        self.posMotor = []
        self.SummThre = []
        self.USER1 = []
        
        # Fenêtres zoom
        self.winZoomMax = ZOOM()
        self.winZoomSum = ZOOM()
        self.winZoomMean = ZOOM()
        self.winZoomXmax = ZOOM()
        self.winZoomYmax = ZOOM()
        self.winZoomCxmax = ZOOM()
        self.winZoomCymax = ZOOM()
        self.winZoomSumThreshold = ZOOM()
        self.winZoomUser1 = ZOOM()
        
        self.maxx = 0
        self.summ = 0
        self.moy = 0
        self.user1 = 0
        self.label = 'Shoot'
        self.setWindowIcon(QIcon(self.icon + 'LOA.png'))
        self.setGeometry(100, 300, 1000, 300)
        
        if self.motRSAI or self.motA2V:
            self.unit()
            
            # Timer pour mise à jour de la position moteur (200ms)
            self.positionTimer = QTimer()
            self.positionTimer.timeout.connect(self._updatePositionLabel)
            self.positionTimer.start(200)

    def _initZMQConnection(self):
        """Initialise la connexion ZMQ et récupère les infos des racks/moteurs"""
        try:
            self.zmqClient = ZMQMotorClient(self.serverHost, self.serverPort)
            
            if self.zmqClient.isconnected:
                # Récupérer la liste des racks
                self.listRack = self.zmqClient.getListRack()
                print(f"🔧 Racks trouvés: {self.listRack}")
                
                if not self.listRack:
                    print("⚠️ Aucun rack trouvé, vérifiez le serveur")
                    return
                
                # Récupérer le nombre de moteurs par rack
                self.nbMotorRack = self.zmqClient.getNbMotorRack()
                print(f"🔧 Nombre de moteurs par rack: {self.nbMotorRack}")
                
                # Récupérer les noms des racks
                self.listRackNames = []
                for ip in self.listRack:
                    name = self.zmqClient.getRackName(ip)
                    self.listRackNames.append(name)
                print(f"🔧 Noms des racks: {self.listRackNames}")
                
                # Récupérer le dictionnaire des moteurs
                self.dict_moteurs = self.zmqClient.getDict()
                print(f"🔧 Dict moteurs récupéré: {len(self.dict_moteurs)} entrées")
                
                # Initialiser avec le premier rack
                if self.listRack:
                    self.currentIP = self.listRack[0]
                    self._updateMotorList()
                
                print('✅ RSAI motors connected via ZMQ server')
            else:
                print('⚠️ Impossible de se connecter au serveur ZMQ')
                self.motRSAI = False
                
        except Exception as e:
            print(f'❌ Erreur initialisation ZMQ: {e}')
            import traceback
            traceback.print_exc()
            self.motRSAI = False

    def _updateMotorList(self):
        """Met à jour la liste des moteurs pour le rack actuel"""
        if self.currentIP and self.zmqClient:
            # Essayer d'abord avec le dictionnaire
            self.listMotorName = self.zmqClient.getMotorList(self.currentIP, self.dict_moteurs)
            
            # Si pas de résultat, utiliser le nombre de moteurs
            if not self.listMotorName and hasattr(self, 'nbMotorRack') and self.nbMotorRack:
                try:
                    idx = self.listRack.index(self.currentIP)
                    count = self.nbMotorRack[idx]
                    print(f"🔧 Utilisation du nombre de moteurs: {count}")
                    self.listMotorName = self.zmqClient.getMotorListFromCount(self.currentIP, count)
                except Exception as e:
                    print(f"❌ Erreur récupération moteurs: {e}")
            
            print(f"🔧 Liste moteurs pour {self.currentIP}: {self.listMotorName}")

    def setFile(self, file):
        self.nomFichier = file
        
    def setup(self):
        vLayout = QVBoxLayout()
        hLayout1 = QHBoxLayout()
        
        menubar = self.menuBar()
        menubar.setNativeMenuBar(False)
        self.fileMenu = menubar.addMenu('&File')
        self.PlotMenu = menubar.addMenu('&Plot')
        self.ZoomMenu = menubar.addMenu('&Zoom')
        self.settingsMenu = menubar.addMenu('&Settings')
        
        self.ThresholdAct = QAction('Threshold', self)
        self.ThresholdMenu = menubar.addAction(self.ThresholdAct)
        self.ThresholdAct.triggered.connect(self.Threshold)
        
        self.setContentsMargins(0, 0, 0, 0)
       
        self.openAct = QAction(QtGui.QIcon(self.icon + "Open.png"), 'Open File', self)
        self.openAct.setShortcut('Ctrl+o')
        self.openAct.triggered.connect(self.openF)
        self.fileMenu.addAction(self.openAct)
        
        self.saveAct = QAction(QtGui.QIcon(self.icon + "disketteSave.png"), 'Save file', self)
        self.saveAct.setShortcut('Ctrl+s')
        self.saveAct.triggered.connect(self.saveF)
        self.fileMenu.addAction(self.saveAct)
        
        # Menu Settings
        self.serverConfigAct = QAction('🔧 Configure Serveur Motors ZMQ...', self)
        self.serverConfigAct.triggered.connect(self.openServerConfig)
        self.settingsMenu.addAction(self.serverConfigAct)
        
        self.reconnectAct = QAction('🔄 Reconnect', self)
        self.reconnectAct.triggered.connect(self.reconnectServer)
        self.settingsMenu.addAction(self.reconnectAct)
        
        self.settingsMenu.addSeparator()
        
        self.showConnectionInfoAct = QAction('ℹ️ Info Connexion', self)
        self.showConnectionInfoAct.triggered.connect(self.showConnectionInfo)
        self.settingsMenu.addAction(self.showConnectionInfoAct)
        
        # Menus Plot
        self.PlotMenu.addAction('max', self.PlotMAX)
        self.PlotMenu.addAction('min', self.PlotMIN)
        self.PlotMenu.addAction('x max', self.PlotXMAX)
        self.PlotMenu.addAction('y max', self.PlotYMAX)
        self.PlotMenu.addAction('Sum', self.PlotSUM)
        self.PlotMenu.addAction('Mean', self.PlotMEAN)
        self.PlotMenu.addAction('x center mass', self.PlotXCMASS)
        self.PlotMenu.addAction('y center mass', self.PlotYCMASS)
        self.PlotMenu.addAction('User 1', self.PlotUSER1)

        # Menus Zoom
        self.ZoomMenu.addAction('max', self.ZoomMAX)
        self.ZoomMenu.addAction('Sum', self.ZoomSUM)
        self.ZoomMenu.addAction('Mean', self.ZoomMEAN)
        self.ZoomMenu.addAction('X max', self.ZoomXmax) 
        self.ZoomMenu.addAction('Y max', self.ZoomYmax)
        self.ZoomMenu.addAction(' X c.of.m', self.ZoomCxmax)
        self.ZoomMenu.addAction(' Y c.of.m', self.ZoomCymax)
        self.ZoomMenu.addAction(' User1', self.ZoomUser1)
        
        self.But_reset = QAction('Reset', self)
        menubar.addAction(self.But_reset)
        
        hLayout2 = QHBoxLayout()
        self.table = QTableWidget()
        hLayout2.addWidget(self.table)
        
        self.table.setColumnCount(12)
        self.table.setHorizontalHeaderLabels(('File', 'Max', 'Min', 'x max', 'y max', 'Sum', 'Mean', 'Size', 'x c.mass', 'y c.mass', 'user1', 'date'))
        header = self.table.horizontalHeader()
        header.setDefaultAlignment(Qt.AlignmentFlag.AlignHCenter)
        header.setDefaultAlignment(Qt.AlignmentFlag.AlignVCenter)
        header.setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)

        # Configuration pour moteurs RSAI ou A2V
        if self.motRSAI or self.motA2V:
            # Indicateur de connexion
            self.connectionLabel = QLabel()
            self._updateConnectionStatus()
            hLayout1.addWidget(self.connectionLabel)
            
            # Sélecteur d'unité
            self.unitBouton = QComboBox()
            self.unitBouton.addItems(['Step', 'µm', 'mm', 'ps', '°'])
            self.unitBouton.setMaximumWidth(100)
            self.unitBouton.setMinimumWidth(80)
            self.unitBouton.setCurrentIndex(self.indexUnit)
            self.unitBouton.currentIndexChanged.connect(self.unit)
            hLayout1.addWidget(self.unitBouton)
            
            # Sélecteur de rack (IP)
            self.rackChoise = QComboBox()
            self.rackChoise.setMinimumWidth(200)
            if self.motRSAI:
                for i, ip in enumerate(self.listRack):
                    name = self.listRackNames[i] if i < len(self.listRackNames) else ip
                    self.rackChoise.addItem(f"{name}  ({ip})")
            self.rackChoise.currentIndexChanged.connect(self.ChangeIPRack)
            hLayout1.addWidget(self.rackChoise)
            
            # Sélecteur de moteur
            self.motorNameBox = QComboBox()
            self.motorNameBox.setMinimumWidth(200)
            self.motorNameBox.addItem('Choose a Motor')
            if self.motRSAI:
                self.motorNameBox.addItems(self.listMotorName)
            elif self.motA2V:
                self.motorNameBox.addItems(self.listMotorName)
            self.motorNameBox.currentIndexChanged.connect(self.motorChange)
            hLayout1.addWidget(self.motorNameBox)
            
            # Label position moteur
            self.positionLabel = QLabel("Pos: ---")
            self.positionLabel.setStyleSheet("font-weight: bold; color: #00ff00;")
            self.positionLabel.setMinimumWidth(150)
            hLayout1.addWidget(self.positionLabel)
            
            # Configuration table avec colonne Motor
            self.table.setColumnCount(13)
            self.table.setHorizontalHeaderLabels(('File', 'Max', 'Min', 'x max', 'y max', 'Sum', 'Mean', 'Size', 'x c.mass', 'y c.mass', 'user1', 'Motor', 'date'))
             
        self.table.horizontalHeader().setVisible(True)
        self.table.setAlternatingRowColors(True)
        self.table.resizeColumnsToContents()
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        
        vLayout.addLayout(hLayout1)
        vLayout.addLayout(hLayout2)
        
        MainWidget = QWidget()
        MainWidget.setLayout(vLayout)
        self.setCentralWidget(MainWidget)
        self.setContentsMargins(1, 1, 1, 1)
        
        if self.parent is not None:
            self.parent.signalMeas.connect(self.Display)
            
        self.But_reset.triggered.connect(self.Reset)

    def _updateConnectionStatus(self):
        """Met à jour l'indicateur de connexion"""
        if hasattr(self, 'connectionLabel'):
            if self.zmqClient and self.zmqClient.isconnected:
                self.connectionLabel.setText("🟢 Motors Connected")
                self.connectionLabel.setStyleSheet("color: #00ff00; font-weight: bold;")
            else:
                self.connectionLabel.setText("🔴 Motors not Connected")
                self.connectionLabel.setStyleSheet("color: #ff0000; font-weight: bold;")

    def _updatePositionLabel(self):
        """Met à jour l'affichage de la position du moteur"""
        if hasattr(self, 'positionLabel') and self.motRSAI:
            if self.motorNameBox.currentIndex() > 0 and self.zmqClient:
                pos = self.zmqClient.getPosition(self.currentIP, self.currentMotorNum)
                pos_converted = pos / self.unitChange if self.unitChange != 0 else pos
                self.positionLabel.setText(f"Pos: {pos_converted:.2f} {self.unitName}")
            else:
                self.positionLabel.setText("Pos: ---")

    def openServerConfig(self):
        """Ouvre le dialogue de configuration du serveur"""
        dialog = ServerConfigDialog(
            current_host=self.serverHost,
            current_port=self.serverPort,
            parent=self
        )
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
            new_host, new_port = dialog.getValues()
            
            # Validation basique
            if not new_host:
                QMessageBox.warning(self, "Erreur", "L'adresse IP ne peut pas être vide.")
                return
            
            if not new_port.isdigit() or not (1 <= int(new_port) <= 65535):
                QMessageBox.warning(self, "Erreur", "Le port doit être un nombre entre 1 et 65535.")
                return
            
            # Sauvegarder dans le fichier ini
            self._saveServerConfig(new_host, new_port)
            
            # Demander si on veut reconnecter maintenant
            reply = QMessageBox.question(
                self, 
                "Reconnecter ?",
                f"Configuration sauvegardée:\n\nHost: {new_host}\nPort: {new_port}\n\nVoulez-vous reconnecter maintenant ?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.Yes
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                self.serverHost = new_host
                self.serverPort = new_port
                self.reconnectServer()
    
    def _saveServerConfig(self, host, port):
        """Sauvegarde la configuration du serveur dans confServer.ini"""
        p = pathlib.Path(__file__)
        sepa = os.sep
        fileconf = str(p.parent) + sepa + "confServer.ini"
        
        confServer = QtCore.QSettings(fileconf, QtCore.QSettings.Format.IniFormat)
        confServer.setValue('MAIN/server_host', host)
        confServer.setValue('MAIN/serverPort', port)
        confServer.sync()
        
        print(f"✅ Configuration sauvegardée: {host}:{port}")
    
    def reconnectServer(self):
        """Reconnecte au serveur ZMQ"""
        print(f"🔄 Reconnexion au serveur {self.serverHost}:{self.serverPort}...")
        
        # Fermer l'ancienne connexion
        if self.zmqClient:
            self.zmqClient.close()
            time.sleep(0.3)
        
        # Réinitialiser les données
        self.listRack = []
        self.listRackNames = []
        self.listMotorName = []
        self.dict_moteurs = {}
        self.currentIP = None
        
        # Reconnecter
        self._initZMQConnection()
        
        # Mettre à jour l'interface
        self._updateConnectionStatus()
        
        if self.motRSAI and hasattr(self, 'rackChoise'):
            # Mettre à jour le combo des racks
            self.rackChoise.clear()
            for i, ip in enumerate(self.listRack):
                name = self.listRackNames[i] if i < len(self.listRackNames) else ip
                self.rackChoise.addItem(f"{name}  ({ip})")
            
            # Mettre à jour le combo des moteurs
            self.motorNameBox.clear()
            self.motorNameBox.addItem('Choose a motor')
            if self.listMotorName:
                self.motorNameBox.addItems(self.listMotorName)
        
        if self.zmqClient and self.zmqClient.isconnected:
            QMessageBox.information(self, "Connexion", "✅ Connexion réussie !")
        else:
            QMessageBox.warning(self, "Connexion", "❌ Échec de la connexion au serveur.")
    
    def showConnectionInfo(self):
        """Affiche les informations de connexion"""
        if self.zmqClient:
            status = "✅ Connecté" if self.zmqClient.isconnected else "❌ Déconnecté"
            server_status = "✅ Disponible" if self.zmqClient.server_available else "❌ Non disponible"
        else:
            status = "❌ Non initialisé"
            server_status = "❌ Non disponible"
        
        info = f"""
<b>Configuration Serveur ZMQ</b><br><br>
<b>Adresse:</b> {self.serverHost}<br>
<b>Port:</b> {self.serverPort}<br>
<b>URL complète:</b> tcp://{self.serverHost}:{self.serverPort}<br><br>
<b>État connexion:</b> {status}<br>
<b>État serveur:</b> {server_status}<br><br>
<b>Racks détectés:</b> {len(self.listRack)}<br>
<b>Moteurs disponibles:</b> {len(self.listMotorName)}
        """
        
        msgBox = QMessageBox(self)
        msgBox.setWindowTitle("Info Connexion")
        msgBox.setTextFormat(Qt.TextFormat.RichText)
        msgBox.setText(info)
        msgBox.setIcon(QMessageBox.Icon.Information)
        msgBox.exec()

    def ChangeIPRack(self):
        """Changement de rack sélectionné"""
        if not self.motRSAI or not self.listRack:
            return
            
        index = self.rackChoise.currentIndex()
        if 0 <= index < len(self.listRack):
            self.currentIP = self.listRack[index]
            print(f"🔧 Rack sélectionné: {self.currentIP}")
            
            # Mettre à jour la liste des moteurs
            self.motorNameBox.clear()
            self.motorNameBox.addItem('Choose a motor')
            
            self._updateMotorList()
            
            if self.listMotorName:
                self.motorNameBox.addItems(self.listMotorName)
                print(f"🔧 {len(self.listMotorName)} moteurs ajoutés au menu")

    def motorChange(self):
        """Changement de moteur sélectionné"""
        if self.motorNameBox.currentIndex() > 0:
            self.currentMotorNum = self.motorNameBox.currentIndex()
            
            if self.motA2V:
                self.currentMotorNum -= 1
                self.MOT = self.A2V.MOTORA2V(self.listMotor[self.currentMotorNum])
                self.stepmotor = self.MOT.step
                
            elif self.motRSAI and self.zmqClient:
                # Récupérer le step du moteur via ZMQ
                self.stepmotor = self.zmqClient.getStep(self.currentIP, self.currentMotorNum)
                if self.stepmotor == 0:
                    self.stepmotor = 1
                    
            self.unit()
            self._updatePositionLabel()
            
            print(f"Moteur sélectionné: {self.currentMotorNum}, step: {self.stepmotor}")

    def unit(self):
        """Changement d'unité"""
        self.indexUnit = self.unitBouton.currentIndex()
        
        if self.indexUnit == 0:  # step
            self.unitChange = 1
            self.unitName = 'step'
        elif self.indexUnit == 1:  # micron
            self.unitChange = float(1 * self.stepmotor)
            self.unitName = 'µm'
        elif self.indexUnit == 2:  # mm
            self.unitChange = float(1000 * self.stepmotor)
            self.unitName = 'mm'
        elif self.indexUnit == 3:  # ps (double passage: 1 micron = 6fs)
            self.unitChange = float(1 * self.stepmotor / 0.0066666666)
            self.unitName = 'ps'
        elif self.indexUnit == 4:  # degrés
            self.unitChange = 1 * self.stepmotor
            self.unitName = '°'
        
        if self.unitChange == 0:
            self.unitChange = 1
            
        self._updatePositionLabel()

    def Reset(self):
        self.shoot = 0
        self.table.setRowCount(0)
        self.Maxx = []
        self.Minn = []
        self.Summ = []
        self.Mean = []
        self.Xmax = []
        self.Ymax = []
        self.Xcmass = []
        self.Ycmass = []
        self.labelsVert = []
        self.posMotor = []
        self.SummThre = []
        self.USER1 = []

    def saveF(self):
        fname = QtGui.QFileDialog.getSaveFileName(self, "Save Measurements as txt file", self.path)
        self.path = os.path.dirname(str(fname[0]))
        f = open(str(fname[0]) + '.txt', 'w')
        f.write("\n".join(self.TableSauv))
        f.close()
        
    def openF(self):
        print('open not done yet')
    
    # Méthodes Zoom
    def ZoomMAX(self):
        self.open_widget(self.winZoomMax)
        self.winZoomMax.SetTITLE('MAX')
        self.winZoomMax.setZoom(self.maxx)
        
    def ZoomSUM(self):
        self.open_widget(self.winZoomSum)
        self.winZoomSum.SetTITLE('Sum')
        self.winZoomSum.setZoom(self.summ)
        
    def ZoomMEAN(self):
        self.open_widget(self.winZoomMean)
        self.winZoomMean.SetTITLE('Mean')
        self.winZoomMean.setZoom(self.moy)    
   
    def ZoomXmax(self):
        self.open_widget(self.winZoomXmax)
        self.winZoomXmax.SetTITLE('x max')
        self.winZoomXmax.setZoom(self.xmax)
        
    def ZoomYmax(self):
        self.open_widget(self.winZoomYmax)
        self.winZoomYmax.SetTITLE('y max')
        self.winZoomYmax.setZoom(self.ymax) 
    
    def ZoomCxmax(self):
        self.open_widget(self.winZoomCxmax)
        self.winZoomCxmax.SetTITLE('x center of mass')
        self.winZoomCxmax.setZoom(self.xcmass)   
    
    def ZoomCymax(self):
        self.open_widget(self.winZoomCymax)
        self.winZoomCymax.SetTITLE('y center of mass')
        self.winZoomCymax.setZoom(self.ycmass)
        
    def ZoomSUMThreshold(self):
        self.open_widget(self.winZoomSumThreshold)
        self.winZoomSumThreshold.SetTITLE('Sum threshold')
        self.winZoomSumThreshold.setZoom(self.summThre) 
    
    def ZoomUser1(self):
        self.open_widget(self.winZoomUser1)
        self.winZoomUser1.SetTITLE('User 1')
        self.winZoomUser1.setZoom(self.user1)

    # Méthodes Plot
    def PlotMAX(self):
        self.open_widget(self.winCoupeMax)
        self.winCoupeMax.SetTITLE('Plot Max')
        self.signalTrans['data'] = self.Maxx
        self.signalTrans['axis'] = self.posMotor
        self.signalTrans['label'] = self.label
        self.signalPlot.emit(self.signalTrans)
    
    def PlotMIN(self):
        self.open_widget(self.winCoupeMin)
        self.winCoupeMin.SetTITLE('Plot Min')
        self.signalTrans['data'] = self.Minn
        self.signalTrans['axis'] = self.posMotor
        self.signalTrans['label'] = self.label
        self.signalPlot.emit(self.signalTrans)
        
    def PlotXMAX(self):
        self.open_widget(self.winCoupeXmax)
        self.winCoupeXmax.SetTITLE('Plot X MAX')
        self.signalTrans['data'] = self.Xmax
        self.signalTrans['axis'] = self.posMotor
        self.signalTrans['label'] = self.label
        self.signalPlot.emit(self.signalTrans)
    
    def PlotYMAX(self):
        self.open_widget(self.winCoupeYmax)
        self.winCoupeYmax.SetTITLE('Plot Y MAX')
        self.signalTrans['data'] = self.Ymax
        self.signalTrans['axis'] = self.posMotor
        self.signalTrans['label'] = self.label
        self.signalPlot.emit(self.signalTrans)
     
    def PlotSUM(self):
        self.open_widget(self.winCoupeSum)
        self.winCoupeSum.SetTITLE('Plot Sum')
        self.signalTrans['data'] = self.Summ
        self.signalTrans['axis'] = self.posMotor
        self.signalTrans['label'] = self.label
        self.signalPlot.emit(self.signalTrans)
    
    def PlotMEAN(self):
        self.open_widget(self.winCoupeMean)
        self.winCoupeMean.SetTITLE('Plot Mean')
        self.signalTrans['data'] = self.Mean
        self.signalTrans['axis'] = self.posMotor
        self.signalTrans['label'] = self.label
        self.signalPlot.emit(self.signalTrans)
        
    def PlotXCMASS(self):
        self.open_widget(self.winCoupeXcmass)
        self.winCoupeXcmass.SetTITLE('Plot x center of mass')
        self.signalTrans['data'] = self.Xcmass
        self.signalTrans['axis'] = self.posMotor
        self.signalTrans['label'] = self.label
        self.signalPlot.emit(self.signalTrans)
    
    def PlotYCMASS(self):
        self.open_widget(self.winCoupeYcmass)
        self.winCoupeYcmass.SetTITLE('Plot Y center of mass')
        self.signalTrans['data'] = self.Ycmass
        self.signalTrans['axis'] = self.posMotor
        self.signalTrans['label'] = self.label
        self.signalPlot.emit(self.signalTrans)
    
    def PlotSUMTHRESHOLD(self):
        self.open_widget(self.winCoupeSumThreshold)
        self.winCoupeSumThreshold.SetTITLE('Plot Sum with Threshold')
        self.signalTrans['data'] = self.SummThre
        self.signalTrans['axis'] = self.posMotor
        self.signalTrans['label'] = self.label
        self.signalPlot.emit(self.signalTrans)
    
    def Threshold(self):
        threshold, ok = QInputDialog.getInt(self, 'Threshold Filter', 'Enter threshold value')
        if ok:
            self.ThresholdState = True
            self.threshold = threshold
            self.Reset()
            self.PlotMenu.addAction('Sum Threshold', self.PlotSUMTHRESHOLD)
            self.ZoomMenu.addAction('Sum with Threshold', self.ZoomSUMThreshold)
            self.Display(self.data)
        else:
            self.ThresholdState = False

    def PlotUSER1(self):
        self.open_widget(self.winCoupeUser1)
        self.winCoupeUser1.SetTITLE('User1')
        self.signalTrans['data'] = self.USER1
        self.signalTrans['axis'] = self.posMotor
        self.signalTrans['label'] = self.label
        self.signalPlot.emit(self.signalTrans)

    def Display(self, data):
        self.data = data[0]
        self.transx = data[1]
        self.transy = data[2]
        self.scalex = data[3]
        self.scaley = data[4]
        
        self.maxx = round(self.data.max(), 3)
        self.minn = round(self.data.min(), 3)
        self.summ = round(self.data.sum(), 3)
        self.moy = round(self.data.mean(), 3)
        self.user1 = round(self.FctUser1(), 3)
        self.date = time.strftime("%Y_%m_%d_%H_%M_%S")
        
        (self.xmax, self.ymax) = np.unravel_index(self.data.argmax(), self.data.shape)
        self.xmax = (self.xmax + self.transx) * self.scalex 
        self.ymax = (self.ymax + self.transy) * self.scaley 
        
        (self.xcmass, self.ycmass) = ndimage.center_of_mass(self.data)
        self.xcmass = (round(self.xcmass, 3) + self.transx) * self.scalex
        self.ycmass = (round(self.ycmass, 3) + self.transy) * self.scaley
        
        self.xs = self.data.shape[0]
        self.ys = self.data.shape[1]
        
        # Remplissage du tableau
        self.table.setRowCount(self.shoot + 1)
        self.table.setItem(self.shoot, 0, QTableWidgetItem(str(self.nomFichier)))
        self.table.setItem(self.shoot, 1, QTableWidgetItem(str(self.maxx)))
        self.table.setItem(self.shoot, 2, QTableWidgetItem(str(self.minn)))
        self.table.setItem(self.shoot, 3, QTableWidgetItem(str(self.xmax)))
        self.table.setItem(self.shoot, 4, QTableWidgetItem(str(self.ymax)))
        self.table.setItem(self.shoot, 5, QTableWidgetItem("{:.3e}".format(self.summ)))
        self.table.setItem(self.shoot, 6, QTableWidgetItem(str(self.moy)))
        self.table.setItem(self.shoot, 7, QTableWidgetItem((str(self.xs) + '*' + str(self.ys))))
        self.table.setItem(self.shoot, 8, QTableWidgetItem(str(self.xcmass)))
        self.table.setItem(self.shoot, 9, QTableWidgetItem(str(self.ycmass)))
        self.table.setItem(self.shoot, 10, QTableWidgetItem(str(self.user1)))

        # Gestion de la position moteur
        if self.motRSAI or self.motA2V:
            if self.motorNameBox.currentIndex() == 0:
                Posi = self.shoot
                self.label = 'Shoot'
            else:
                if self.motRSAI and self.zmqClient:
                    pos = self.zmqClient.getPosition(self.currentIP, self.currentMotorNum)
                    Posi = round(pos / self.unitChange, 2)
                    motorName = self.zmqClient.getMotorName(self.currentIP, self.currentMotorNum)
                    self.label = f"{motorName} ({self.unitName})"
                elif self.motA2V:
                    Posi = round(self.MOT.position() / self.unitChange, 2)
                    self.label = f"{self.MOT.name} ({self.unitName})"
                else:
                    Posi = self.shoot
                    self.label = 'Shoot'
        else:
            Posi = self.shoot
            self.label = 'Shoot'
            
        self.posMotor.append(Posi)    
        self.table.resizeColumnsToContents()
        self.labelsVert.append('%s' % self.shoot)
        
        # Gestion du threshold
        if self.ThresholdState:
            dataCor = np.where(self.data < self.threshold, 0, self.data)
            self.summThre = round(dataCor.sum(), 3)
            self.SummThre.append(self.summThre)
            
            if self.motRSAI or self.motA2V:
                self.table.setColumnCount(14)
                self.table.setHorizontalHeaderLabels(('File', 'Max', 'Min', 'x max', 'y max', 'Sum', 'Mean', 'Size', 'x c.mass', 'y c.mass', 'Sum Thr', 'user1', 'Motor', 'date'))
                self.table.setItem(self.shoot, 12, QTableWidgetItem(str(Posi)))
                self.table.setItem(self.shoot, 13, QTableWidgetItem(str(self.date)))
            else:
                self.table.setColumnCount(13)
                self.table.setHorizontalHeaderLabels(('File', 'Max', 'Min', 'x max', 'y max', 'Sum', 'Mean', 'Size', 'x c.mass', 'y c.mass', 'Sum Thr', 'user1', 'date'))
                self.table.setItem(self.shoot, 12, QTableWidgetItem(str(self.date)))
            self.table.setItem(self.shoot, 10, QTableWidgetItem("{:.3e}".format(self.summThre)))
            
        else:
            if self.motRSAI or self.motA2V:
                self.table.setHorizontalHeaderLabels(('File', 'Max', 'Min', 'x max', 'y max', 'Sum', 'Mean', 'Size', 'x c.mass', 'y c.mass', 'user1', 'Motor', 'date'))
                self.table.setColumnCount(13)
                self.table.setItem(self.shoot, 11, QTableWidgetItem(str(Posi)))
                self.table.setItem(self.shoot, 12, QTableWidgetItem(str(self.date)))
            else:
                self.table.setHorizontalHeaderLabels(('File', 'Max', 'Min', 'x max', 'y max', 'Sum', 'Mean', 'Size', 'x c.mass', 'y c.mass', 'user1', 'date'))
                self.table.setColumnCount(12)
                self.table.setItem(self.shoot, 11, QTableWidgetItem(str(self.date)))
        
        self.table.selectRow(self.shoot)
        
        # Mise à jour des listes
        self.Maxx.append(self.maxx)
        self.Minn.append(self.minn)
        self.Summ.append(self.summ)
        self.Mean.append(self.moy)
        self.Xmax.append(self.xmax)
        self.Ymax.append(self.ymax)
        self.Xcmass.append(self.xcmass)
        self.Ycmass.append(self.ycmass)
        self.USER1.append(self.user1)

        self.table.setVerticalHeaderLabels(self.labelsVert)

        # Mise à jour des fenêtres de plot ouvertes
        if self.winCoupeMax.isWinOpen:
            self.PlotMAX()
        if self.winCoupeMin.isWinOpen:
            self.PlotMIN()
        if self.winCoupeXmax.isWinOpen:
            self.PlotXMAX()
        if self.winCoupeYmax.isWinOpen:
            self.PlotYMAX()
        if self.winCoupeSum.isWinOpen:
            self.PlotSUM()
        if self.winCoupeMean.isWinOpen:
            self.PlotMEAN()
        if self.winCoupeXcmass.isWinOpen:
            self.PlotXCMASS()
        if self.winCoupeYcmass.isWinOpen:
            self.PlotYCMASS()
        if self.winCoupeSumThreshold.isWinOpen:
            self.PlotSUMTHRESHOLD()
        if self.winCoupeUser1.isWinOpen:
            self.PlotUSER1()

        # Mise à jour des fenêtres zoom ouvertes
        if self.winZoomMax.isWinOpen:
            self.ZoomMAX()
        if self.winZoomSum.isWinOpen:
            self.ZoomSUM()
        if self.winZoomMean.isWinOpen:
            self.ZoomMEAN() 
        if self.winZoomXmax.isWinOpen:
            self.ZoomXmax()
        if self.winZoomYmax.isWinOpen:
            self.ZoomYmax()
        if self.winZoomCxmax.isWinOpen:
            self.ZoomCxmax()
        if self.winZoomCymax.isWinOpen:
            self.ZoomCymax()   
        if self.winZoomSumThreshold.isWinOpen:
            self.ZoomSUMThreshold()
        if self.winZoomUser1.isWinOpen:
            self.ZoomUser1()
            
        # Mise à jour position
        self._updatePositionLabel()
        
        self.shoot += 1
      
    def closeEvent(self, event):
        """Fermeture de la fenêtre"""
        self.isWinOpen = False
        self.shoot = 0
        self.TableSauv = ['file,Max,Min,x Max,y max,Sum,Mean,Size,x c.mass,y c.mass']
        
        # Arrêter le timer de position
        if hasattr(self, 'positionTimer'):
            self.positionTimer.stop()
        
        # Fermeture des fenêtres de graphiques
        for win in [self.winCoupeMax, self.winCoupeMin, self.winCoupeXmax, 
                    self.winCoupeYmax, self.winCoupeSum, self.winCoupeMean,
                    self.winCoupeXcmass, self.winCoupeYcmass, self.winCoupeSumThreshold]:
            if win.isWinOpen:
                win.close()
        
        # Fermeture de la connexion ZMQ
        if self.zmqClient:
            self.zmqClient.close()
            
        time.sleep(0.1)
        event.accept()

    def open_widget(self, fene):
        """Ouverture widget supplémentaire"""
        if fene.isWinOpen is False:
            fene.setup
            fene.isWinOpen = True
            fene.show()
        else:
            fene.showNormal()

    def FctUser1(self):
        """Fonction utilisateur personnalisable"""
        a = 0
        return a


if __name__ == "__main__":
    appli = QApplication(sys.argv)
    appli.setStyleSheet(qdarkstyle.load_stylesheet(qt_api='pyqt6'))
    e = MEAS(motRSAI=True)
    e.show()
    appli.exec()