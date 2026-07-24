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
import json
from collections import deque
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


class ZMQPublisherWorker(QtCore.QObject):
    """
    Serveur ZMQ PUB tournant dans un thread dédié, en mode événementiel :
    aucune boucle ni polling actif, l'envoi des données se déclenche
    uniquement via le signal 'signalPublish' de la fenêtre MEAS (connecté
    à publishData en Qt.QueuedConnection car l'objet vit dans un autre thread).

    Publie un message ZMQ multipart : [topic (nom du widget), JSON du dictionnaire]
    contenant les clés : 'File', 'Max', 'Min', 'x max', 'y max', 'Sum', 'Mean',
    'Size', 'x c.mass', 'y c.mass', 'user1', 'Motor', 'date', 'name'.
    """

    started = QtCore.pyqtSignal(bool)

    def __init__(self, port='5556'):
        super().__init__()
        self.port = port
        self.context = None
        self.socket = None

    @QtCore.pyqtSlot()
    def start(self):
        """Ouvre le socket PUB. Appelé automatiquement au démarrage du QThread."""
        try:
            self.context = zmq.Context()
            self.socket = self.context.socket(zmq.PUB)
            self.socket.setsockopt(zmq.LINGER, 0)
            self.socket.bind(f"tcp://*:{self.port}")
            print(f"📡 Serveur ZMQ Publisher (widget data) démarré sur le port {self.port}")
            self.started.emit(True)
        except Exception as e:
            print(f"❌ Erreur démarrage serveur ZMQ Publisher: {e}")
            self.started.emit(False)

    @QtCore.pyqtSlot(dict)
    def publishData(self, data):
        """
        Slot appelé de façon événementielle à chaque nouvelle mesure
        (connecté au signal signalPublish émis par MEAS.Display()).
        """
        if not self.socket:
            return
        try:
            topic = str(data.get('name', 'MEAS'))
            payload = json.dumps(data, default=self._jsonDefault)
            self.socket.send_multipart([topic.encode('utf-8'), payload.encode('utf-8')])
        except Exception as e:
            print(f"❌ Erreur publication ZMQ: {e}")

    @staticmethod
    def _jsonDefault(obj):
        """
        Filet de sécurité pour json.dumps : convertit les types numpy
        (int64, float64, ndarray, ...) qui ne sont pas nativement
        sérialisables en JSON, vers des types Python standards.
        """
        if isinstance(obj, np.integer):
            return int(obj)
        if isinstance(obj, np.floating):
            return float(obj)
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        return str(obj)

    @QtCore.pyqtSlot()
    def stop(self):
        """Ferme proprement le socket. Exécuté dans le thread du worker."""
        try:
            if self.socket:
                self.socket.close()
            if self.context:
                self.context.term()
        except Exception as e:
            print(f"❌ Erreur fermeture serveur ZMQ Publisher: {e}")
        finally:
            self.socket = None
            self.context = None
            print("📡 Serveur ZMQ Publisher arrêté")


class MEAS(QMainWindow):
    
    signalPlot = QtCore.pyqtSignal(object)
    signalPublish = QtCore.pyqtSignal(dict)
    
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
        # Option (activée par défaut) : utiliser un filtre médian+gaussien
        # (avec sous-échantillonnage sur les grandes images) pour trouver
        # la position du Max, plus robuste au bruit/pixels chauds et plus
        # rapide qu'un filtre gaussien plein résolution sur une grande image
        self.useFilteredMaxPosition = True
        
        # Nombre maximum de points conservés dans les listes utilisées pour
        # les graphes (Max, Sum, ...) : au-delà, les points les plus anciens
        # sont automatiquement supprimés. Évite que le traçage devienne
        # coûteux/instable sur de très longues acquisitions. Modifiable via
        # le menu Settings > "Limiter l'historique des graphes...".
        self.maxPlotHistory = int(self.conf.value(self.name + "/maxPlotHistory", 500))
        
        # Configuration serveur ZMQ
        self.serverHost = 'localhost'
        self.serverPort = '5555'
        
        # Configuration serveur ZMQ Publisher (envoi des données du widget MEAS)
        self.pubPort = '5556'
        self.pubServerActive = False
        self.pubThread = None
        self.pubWorker = None
        
        # Lecture config serveur si disponible
        fileconf = str(p.parent) + sepa + "confServer.ini"
        if os.path.exists(fileconf):
            confServer = QtCore.QSettings(fileconf, QtCore.QSettings.Format.IniFormat)
            self.serverHost = str(confServer.value('MAIN/server_host', 'localhost'))
            self.serverPort = str(confServer.value('MAIN/serverPort', '5555'))
            self.pubPort = str(confServer.value('MAIN/pubPort', '5556'))
        
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
        self._resetPlotHistory()
        
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

    def _getFileInfoFromOptions(self):
        """
        Récupère le nom de fichier et le numéro de tir directement depuis
        la fenêtre WinOption (self.parent.winOpt), plutôt que depuis
        self.nomFichier/self.shoot qui ne reflètent pas toujours l'état
        réel de la sauvegarde (autosave notamment).
        Retourne (fileNameOpt, tirNumberOpt), chacun pouvant être None
        si l'info n'est pas disponible (pas de parent, pas de winOpt...).
        """
        if self.parent is None or not hasattr(self.parent, 'winOpt'):
            return None, None
        try:
            fileNameOpt = self.parent.winOpt.nameBox.text()
            tirNumberOpt = int(self.parent.winOpt.tirNumberBox.value())
            return fileNameOpt, tirNumberOpt
        except Exception as e:
            print(f"⚠️ Impossible de récupérer le nom/tir depuis WinOption: {e}")
            return None, None

    def _isAutoSaveActive(self):
        """
        Indique si le mode autosave est actif côté fenêtre parente (visual.py),
        pour permettre au widget de traçage ZMQ de choisir entre le numéro
        de tir réel (autosave) ou un simple compteur incrémental (sinon).
        """
        if self.parent is not None and hasattr(self.parent, 'checkBoxAutoSave'):
            try:
                return bool(self.parent.checkBoxAutoSave.isChecked())
            except Exception:
                return False
        return False

    def _resetPlotHistory(self):
        """
        (Ré)initialise les listes de données utilisées pour les graphes
        (Max, Min, Sum, Mean, ...), plafonnées à self.maxPlotHistory points
        via des deque(maxlen=...) : au-delà de cette limite, les points les
        plus anciens sont automatiquement supprimés à chaque ajout (coût
        constant, O(1) par tir), au lieu de laisser ces listes grandir sans
        limite pendant une longue acquisition.
        """
        self.Maxx = deque(maxlen=self.maxPlotHistory)
        self.Minn = deque(maxlen=self.maxPlotHistory)
        self.Summ = deque(maxlen=self.maxPlotHistory)
        self.Mean = deque(maxlen=self.maxPlotHistory)
        self.Xmax = deque(maxlen=self.maxPlotHistory)
        self.Ymax = deque(maxlen=self.maxPlotHistory)
        self.Xcmass = deque(maxlen=self.maxPlotHistory)
        self.Ycmass = deque(maxlen=self.maxPlotHistory)
        self.posMotor = deque(maxlen=self.maxPlotHistory)
        self.SummThre = deque(maxlen=self.maxPlotHistory)
        self.USER1 = deque(maxlen=self.maxPlotHistory)

    def setMaxPlotHistory(self):
        """Dialogue pour configurer le nombre maximum de points gardés pour les graphes"""
        value, ok = QInputDialog.getInt(
            self, "Limiter l'historique des graphes",
            "Nombre maximum de points conservés pour les graphes\n"
            "(Max, Sum, Mean, ...) :",
            self.maxPlotHistory, 10, 1000000
        )
        if ok:
            self.maxPlotHistory = value
            self.conf.setValue(self.name + "/maxPlotHistory", self.maxPlotHistory)
            self.conf.sync()
            # Recrée les deques avec la nouvelle limite, en conservant les
            # données déjà présentes (tronquées si besoin)
            for attrName in ('Maxx', 'Minn', 'Summ', 'Mean', 'Xmax', 'Ymax',
                              'Xcmass', 'Ycmass', 'posMotor', 'SummThre', 'USER1'):
                oldValues = list(getattr(self, attrName))
                setattr(self, attrName, deque(oldValues, maxlen=self.maxPlotHistory))

    def _shootOrTirPosi(self):
        """
        Retourne (Posi, label) pour l'axe des tracés/tableau, en mode
        'pas de moteur sélectionné' :
        - si l'autosave est actif, utilise le numéro de tir récupéré
          depuis WinOption (cohérent avec le nom du fichier réellement
          sauvegardé) ;
        - sinon (pas d'autosave), utilise le compteur interne self.shoot,
          qui s'incrémente à chaque acquisition et repart à 0 au Reset.
          Sans cette vérification, le numéro de tir de WinOption restait
          bloqué à la même valeur (il ne s'incrémente que lors d'une
          sauvegarde autosave réelle), ce qui faisait que l'axe des tracés
          affichait toujours la même valeur en dehors du mode autosave.
        """
        if self._isAutoSaveActive() and self.tirNumberOpt is not None:
            return self.tirNumberOpt, 'Tir'
        return self.shoot, 'Shoot'

    def toggleFilterMaxPosition(self, checked):
        """Active/désactive le filtre médian+gaussien pour la position du Max."""
        self.useFilteredMaxPosition = checked

    def _findMaxPosition(self, data):
        """
        Détermine la position (indices pixel) du maximum de l'image.

        - Si self.useFilteredMaxPosition est False : comportement d'origine,
          argmax brut sur l'image complète (rapide mais sensible au bruit
          et aux pixels chauds).
        - Si True (par défaut) : applique un filtre médian (retire les
          pixels chauds isolés) puis un filtre gaussien (lisse le bruit)
          avant de chercher le maximum. Sur les grandes images, un
          sous-échantillonnage est appliqué avant le filtrage gaussien
          (qui est coûteux en pleine résolution), puis la position trouvée
          est affinée par un argmax local en pleine résolution sur un petit
          patch autour de cette position approximative.
        """
        if not self.useFilteredMaxPosition:
            return np.unravel_index(data.argmax(), data.shape)

        try:
            ds_threshold = 512
            if data.shape[0] > ds_threshold or data.shape[1] > ds_threshold:
                ds = 4
                data_small = data[::ds, ::ds]  # sous-échantillonnage pour accélérer le gaussien
                dataF = ndimage.median_filter(data_small, size=3)
                dataF = ndimage.gaussian_filter(dataF, 2)
                shapeUsed = data_small.shape
            else:
                ds = 1
                dataF = ndimage.median_filter(data, size=3)
                dataF = ndimage.gaussian_filter(dataF, 5)
                shapeUsed = data.shape

            (xec, yec) = np.unravel_index(dataF.argmax(), shapeUsed)

            # Raffinement : argmax local en pleine résolution autour de la
            # position approximative trouvée sur l'image (sous-)filtrée
            margin = ds * 2
            xc = int(round(xec * ds))
            yc = int(round(yec * ds))
            x0 = max(0, xc - margin)
            x1 = min(data.shape[0], xc + margin)
            y0 = max(0, yc - margin)
            y1 = min(data.shape[1], yc + margin)

            if x1 > x0 and y1 > y0:
                patch = data[x0:x1, y0:y1]
                (dx, dy) = np.unravel_index(patch.argmax(), patch.shape)
                return x0 + dx, y0 + dy
            else:
                return xc, yc

        except Exception as e:
            print(f"⚠️ Erreur filtre position Max, retour au calcul brut: {e}")
            return np.unravel_index(data.argmax(), data.shape)

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
        
        self.settingsMenu.addSeparator()
        
        # Filtre médian+gaussien (accéléré) pour trouver la position du Max
        self.filterMaxPositionAct = QAction('🎯 Filtre Médian+Gaussien pour position du Max (rapide)', self)
        self.filterMaxPositionAct.setCheckable(True)
        self.filterMaxPositionAct.setChecked(self.useFilteredMaxPosition)
        self.filterMaxPositionAct.triggered.connect(self.toggleFilterMaxPosition)
        self.settingsMenu.addAction(self.filterMaxPositionAct)
        
        self.settingsMenu.addSeparator()
        
        # Serveur ZMQ Publisher : publie les données du widget (Max, Min, Sum, ...)
        # dans un thread séparé, en mode événementiel (PUB/SUB, pas de polling)
        self.pubServerAct = QAction('📡 Activer serveur ZMQ Publisher (données widget)', self)
        self.pubServerAct.setCheckable(True)
        self.pubServerAct.setChecked(False)
        self.pubServerAct.triggered.connect(self.togglePubServer)
        self.settingsMenu.addAction(self.pubServerAct)
        
        self.pubConfigAct = QAction('🔧 Configurer port Publisher...', self)
        self.pubConfigAct.triggered.connect(self.openPubConfig)
        self.settingsMenu.addAction(self.pubConfigAct)
        
        self.openPlotWidgetAct = QAction('📈 Ouvrir widget de traçage ZMQ', self)
        self.openPlotWidgetAct.triggered.connect(self.openZMQPlotWidget)
        self.settingsMenu.addAction(self.openPlotWidgetAct)
        
        self.settingsMenu.addSeparator()
        
        # Ajustement manuel des colonnes : n'est plus fait automatiquement
        # à chaque tir (coût qui grandit avec le nombre de lignes et
        # bloquait l'interface après quelques centaines de tirs) ; à faire
        # à la demande, par exemple une fois l'acquisition terminée.
        self.resizeColumnsAct = QAction('↔️ Ajuster la largeur des colonnes', self)
        self.resizeColumnsAct.triggered.connect(lambda: self.table.resizeColumnsToContents())
        self.settingsMenu.addAction(self.resizeColumnsAct)
        
        self.maxPlotHistoryAct = QAction('📉 Limiter l\'historique des graphes...', self)
        self.maxPlotHistoryAct.triggered.connect(self.setMaxPlotHistory)
        self.settingsMenu.addAction(self.maxPlotHistoryAct)
        
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
        
        self.table.setColumnCount(13)
        self.table.setHorizontalHeaderLabels(('File', 'Tir', 'Max', 'Min', 'x max', 'y max', 'Sum', 'Mean', 'Size', 'x c.mass', 'y c.mass', 'user1', 'date'))
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
            self.table.setColumnCount(14)
            self.table.setHorizontalHeaderLabels(('File', 'Tir', 'Max', 'Min', 'x max', 'y max', 'Sum', 'Mean', 'Size', 'x c.mass', 'y c.mass', 'user1', 'Motor', 'date'))
             
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
    
    def togglePubServer(self, checked):
        """Active/désactive le serveur ZMQ Publisher (coché depuis le menu Settings)"""
        if checked:
            self.startPubServer()
        else:
            self.stopPubServer()

    def startPubServer(self):
        """
        Démarre, dans un QThread dédié, un serveur ZMQ PUB en mode événementiel :
        le thread ne fait qu'attendre les signaux Qt (signalPublish), il n'y a
        aucune boucle de polling. Chaque appel à Display() déclenche l'envoi.
        """
        if self.pubServerActive:
            return
        
        self.pubThread = QtCore.QThread()
        self.pubWorker = ZMQPublisherWorker(port=self.pubPort)
        self.pubWorker.moveToThread(self.pubThread)
        
        # Démarrage du socket PUB dès que le thread (et sa boucle d'événements) tourne
        self.pubThread.started.connect(self.pubWorker.start)
        # Connexion événementielle : chaque emit() de signalPublish déclenche
        # publishData() DANS le thread du worker (QueuedConnection implicite
        # car l'émetteur et le récepteur sont dans des threads différents)
        self.signalPublish.connect(self.pubWorker.publishData)
        
        self.pubThread.start()
        self.pubServerActive = True
        if hasattr(self, 'pubServerAct'):
            self.pubServerAct.setChecked(True)

    def stopPubServer(self):
        """Arrête proprement le thread et le socket ZMQ Publisher"""
        if not self.pubServerActive or self.pubThread is None:
            return
        
        try:
            self.signalPublish.disconnect(self.pubWorker.publishData)
        except (TypeError, RuntimeError):
            pass
        
        # 'stop' est exécuté dans le thread du worker (QueuedConnection)
        QtCore.QMetaObject.invokeMethod(
            self.pubWorker, 'stop', QtCore.Qt.ConnectionType.QueuedConnection
        )
        self.pubThread.quit()
        self.pubThread.wait(1500)
        
        self.pubServerActive = False
        if hasattr(self, 'pubServerAct'):
            self.pubServerAct.setChecked(False)

    def openPubConfig(self):
        """Dialogue simple pour configurer le port du serveur Publisher"""
        port, ok = QInputDialog.getText(
            self, "Port du serveur Publisher ZMQ", "Port:",
            QLineEdit.EchoMode.Normal, self.pubPort
        )
        if ok and port.strip():
            port = port.strip()
            if not port.isdigit() or not (1 <= int(port) <= 65535):
                QMessageBox.warning(self, "Erreur", "Le port doit être un nombre entre 1 et 65535.")
                return
            
            restart = self.pubServerActive
            if restart:
                self.stopPubServer()
            
            self.pubPort = port
            self._savePubConfig(self.pubPort)
            
            if restart:
                self.startPubServer()
            
            QMessageBox.information(self, "Info", f"Port Publisher configuré : {self.pubPort}")

    def _savePubConfig(self, port):
        """Sauvegarde le port du serveur Publisher dans confServer.ini"""
        p = pathlib.Path(__file__)
        sepa = os.sep
        fileconf = str(p.parent) + sepa + "confServer.ini"
        
        confServer = QtCore.QSettings(fileconf, QtCore.QSettings.Format.IniFormat)
        confServer.setValue('MAIN/pubPort', port)
        confServer.sync()
        
        print(f"✅ Configuration Publisher sauvegardée: port {port}")

    def openZMQPlotWidget(self):
        """Ouvre le widget de traçage qui s'abonne (SUB) au serveur Publisher"""
        # On force le dossier de winMeas.py dans sys.path : si winMeas.py est
        # importé comme module depuis un autre répertoire de travail (et non
        # lancé directement), son propre dossier n'est pas toujours présent
        # dans sys.path, et l'import de widgetZMQPlot.py échoue même s'il est
        # bien à côté de winMeas.py.
        moduleDir = str(pathlib.Path(__file__).resolve().parent)
        if moduleDir not in sys.path:
            sys.path.insert(0, moduleDir)
        
        try:
            from widgetZMQPlot import ZMQPlotWidget
        except Exception as e:
            # On n'attrape plus seulement ImportError : une dépendance
            # manquante (pyqtgraph, qdarkstyle, zmq...) lève aussi une
            # ImportError/ModuleNotFoundError qui serait sinon confondue
            # avec un fichier introuvable.
            import traceback
            traceback.print_exc()
            QMessageBox.warning(
                self, "Erreur d'import widgetZMQPlot",
                f"Impossible de charger widgetZMQPlot.py :\n\n{type(e).__name__}: {e}\n\n"
                f"Dossier recherché :\n{moduleDir}\n\n"
                "Vérifiez que le fichier s'y trouve et que ses dépendances "
                "(pyqtgraph, qdarkstyle, pyzmq) sont installées."
            )
            return
        
        self.zmqPlotWidget = ZMQPlotWidget(endpoints=[f"localhost:{self.pubPort}"])
        self.zmqPlotWidget.show()

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
        self._resetPlotHistory()

        # Rafraîchit les fenêtres de tracé déjà ouvertes pour qu'elles
        # s'effacent aussi (sinon elles continuaient d'afficher l'ancienne
        # courbe alors que le tableau, lui, était bien vidé).
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
        
        # Récupération du nom de fichier et du numéro de tir depuis WinOption
        # (utilisés pour la colonne 'File' du tableau et comme axe des tracés)
        self.fileNameOpt, self.tirNumberOpt = self._getFileInfoFromOptions()
        if self.fileNameOpt is not None:
            if self.tirNumberOpt is not None:
                self.nomFichier = f"{self.fileNameOpt}_{self.tirNumberOpt:04d}"
            else:
                self.nomFichier = self.fileNameOpt
        
        # Position du Max (brute ou filtrée selon self.useFilteredMaxPosition) :
        # calculée AVANT self.maxx pour que la valeur affichée dans la colonne
        # 'Max' corresponde bien au pixel situé à (x max, y max), même quand
        # le filtre médian+gaussien déplace légèrement la position détectée.
        (xIdx, yIdx) = self._findMaxPosition(self.data)
        self.maxx = round(float(self.data[xIdx, yIdx]), 3)
        self.minn = round(self.data.min(), 3)
        self.summ = round(self.data.sum(), 3)
        self.moy = round(self.data.mean(), 3)
        self.user1 = round(self.FctUser1(), 3)
        self.date = time.strftime("%Y_%m_%d_%H_%M_%S")
        
        self.xmax = (xIdx + self.transx) * self.scalex 
        self.ymax = (yIdx + self.transy) * self.scaley 
        
        (self.xcmass, self.ycmass) = ndimage.center_of_mass(self.data)
        self.xcmass = (round(self.xcmass, 3) + self.transx) * self.scalex
        self.ycmass = (round(self.ycmass, 3) + self.transy) * self.scaley
        
        self.xs = self.data.shape[0]
        self.ys = self.data.shape[1]
        
        # Remplissage du tableau
        self.table.setRowCount(self.shoot + 1)
        self.table.setItem(self.shoot, 0, QTableWidgetItem(str(self.nomFichier)))
        # Numéro de tir affiché dans le tableau : le vrai numéro de tir
        # (WinOption) si l'autosave est actif, sinon un simple compteur
        # incrémental (self.shoot) puisque le numéro de WinOption ne bouge
        # pas tant qu'aucune sauvegarde réelle n'a lieu.
        if self._isAutoSaveActive() and self.tirNumberOpt is not None:
            tirDisplay = self.tirNumberOpt
        else:
            tirDisplay = self.shoot
        self.table.setItem(self.shoot, 1, QTableWidgetItem(str(tirDisplay)))
        self.table.setItem(self.shoot, 2, QTableWidgetItem(str(self.maxx)))
        self.table.setItem(self.shoot, 3, QTableWidgetItem(str(self.minn)))
        self.table.setItem(self.shoot, 4, QTableWidgetItem(str(self.xmax)))
        self.table.setItem(self.shoot, 5, QTableWidgetItem(str(self.ymax)))
        self.table.setItem(self.shoot, 6, QTableWidgetItem("{:.3e}".format(self.summ)))
        self.table.setItem(self.shoot, 7, QTableWidgetItem(str(self.moy)))
        self.table.setItem(self.shoot, 8, QTableWidgetItem((str(self.xs) + '*' + str(self.ys))))
        self.table.setItem(self.shoot, 9, QTableWidgetItem(str(self.xcmass)))
        self.table.setItem(self.shoot, 10, QTableWidgetItem(str(self.ycmass)))
        self.table.setItem(self.shoot, 11, QTableWidgetItem(str(self.user1)))

        # Gestion de la position moteur
        self.motorNameOpt = None   # nom du moteur actif (None si mode Shoot/Tir)
        self.motorUnitOpt = None   # unité du moteur actif (None si mode Shoot/Tir)
        
        if self.motRSAI or self.motA2V:
            if self.motorNameBox.currentIndex() == 0:
                Posi, self.label = self._shootOrTirPosi()
            else:
                if self.motRSAI and self.zmqClient:
                    pos = self.zmqClient.getPosition(self.currentIP, self.currentMotorNum)
                    Posi = round(pos / self.unitChange, 2)
                    motorName = self.zmqClient.getMotorName(self.currentIP, self.currentMotorNum)
                    self.label = f"{motorName} ({self.unitName})"
                    self.motorNameOpt = motorName
                    self.motorUnitOpt = self.unitName
                elif self.motA2V:
                    Posi = round(self.MOT.position() / self.unitChange, 2)
                    self.label = f"{self.MOT.name} ({self.unitName})"
                    self.motorNameOpt = self.MOT.name
                    self.motorUnitOpt = self.unitName
                else:
                    Posi, self.label = self._shootOrTirPosi()
        else:
            Posi, self.label = self._shootOrTirPosi()
            
        self.posMotor.append(Posi)    

        # Publication événementielle vers le serveur ZMQ Publisher (si activé)
        if self.pubServerActive:
            self.signalPublish.emit({
                'name': self.name,
                'File': str(self.nomFichier),
                'Max': float(self.maxx),
                'Min': float(self.minn),
                'x max': float(self.xmax),
                'y max': float(self.ymax),
                'Sum': float(self.summ),
                'Mean': float(self.moy),
                'Size': f"{self.xs}*{self.ys}",
                'x c.mass': float(self.xcmass),
                'y c.mass': float(self.ycmass),
                'user1': float(self.user1),
                'Motor': float(Posi) if isinstance(Posi, (int, float, np.integer, np.floating)) else str(Posi),
                'MotorName': self.motorNameOpt,   # nom du moteur actif (None si mode Shoot/Tir)
                'MotorUnit': self.motorUnitOpt,    # unité du moteur actif (None si mode Shoot/Tir)
                'date': self.date,
                # Utilisés par le widget de traçage ZMQ pour choisir l'axe X :
                # numéro de tir réel si autosave actif, sinon simple compteur
                'AutoSave': self._isAutoSaveActive(),
                'TirNumber': self.tirNumberOpt,
            })

        # Mise à jour incrémentale de l'en-tête vertical (numéro de ligne),
        # au lieu de reconstruire toute la liste des labels à chaque tir
        # (coût O(n) par appel -> O(n²) au total, cause principale du
        # ralentissement/blocage observé après quelques centaines de tirs).
        self.table.setVerticalHeaderItem(self.shoot, QTableWidgetItem('%s' % self.shoot))
        
        # Gestion du threshold
        if self.ThresholdState:
            dataCor = np.where(self.data < self.threshold, 0, self.data)
            self.summThre = round(dataCor.sum(), 3)
            self.SummThre.append(self.summThre)
            
            if self.motRSAI or self.motA2V:
                self.table.setColumnCount(15)
                self.table.setHorizontalHeaderLabels(('File', 'Tir', 'Max', 'Min', 'x max', 'y max', 'Sum', 'Mean', 'Size', 'x c.mass', 'y c.mass', 'Sum Thr', 'user1', 'Motor', 'date'))
                self.table.setItem(self.shoot, 13, QTableWidgetItem(str(Posi)))
                self.table.setItem(self.shoot, 14, QTableWidgetItem(str(self.date)))
            else:
                self.table.setColumnCount(14)
                self.table.setHorizontalHeaderLabels(('File', 'Tir', 'Max', 'Min', 'x max', 'y max', 'Sum', 'Mean', 'Size', 'x c.mass', 'y c.mass', 'Sum Thr', 'user1', 'date'))
                self.table.setItem(self.shoot, 13, QTableWidgetItem(str(self.date)))
            self.table.setItem(self.shoot, 11, QTableWidgetItem("{:.3e}".format(self.summThre)))
            
        else:
            if self.motRSAI or self.motA2V:
                self.table.setHorizontalHeaderLabels(('File', 'Tir', 'Max', 'Min', 'x max', 'y max', 'Sum', 'Mean', 'Size', 'x c.mass', 'y c.mass', 'user1', 'Motor', 'date'))
                self.table.setColumnCount(14)
                self.table.setItem(self.shoot, 12, QTableWidgetItem(str(Posi)))
                self.table.setItem(self.shoot, 13, QTableWidgetItem(str(self.date)))
            else:
                self.table.setHorizontalHeaderLabels(('File', 'Tir', 'Max', 'Min', 'x max', 'y max', 'Sum', 'Mean', 'Size', 'x c.mass', 'y c.mass', 'user1', 'date'))
                self.table.setColumnCount(13)
                self.table.setItem(self.shoot, 12, QTableWidgetItem(str(self.date)))
        
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
        
        # Arrêt du serveur ZMQ Publisher s'il tourne
        if self.pubServerActive:
            self.stopPubServer()
            
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