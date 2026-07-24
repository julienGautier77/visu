#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
widgetZMQPlot.py

Widget de traçage en temps réel des données publiées par un ou
PLUSIEURS serveurs ZMQ Publisher de winMeas.py, typiquement chacun
tournant sur un PC caméra différent (menu Settings > "Activer serveur
ZMQ Publisher" de winMeas.py).

Cas d'usage : N caméras sur N PC différents, chacune publiant sur son
propre "tcp://IP_caméra:port". Ce widget se connecte à toutes ces
adresses avec un seul socket ZMQ SUB (ZMQ permet de connecter un même
SUB à plusieurs PUB), et trace une courbe par caméra (identifiée par
le champ 'name', c.-à-d. le self.name de la fenêtre MEAS émettrice)
pour le champ sélectionné (Max, Sum, Mean, ...).

Fonctionnement :
- Un ZMQSubscriberWorker tourne dans un QThread dédié, avec un socket
  SUB unique connecté à toutes les adresses ajoutées. Il reste en
  attente événementielle des messages (recv bloquant avec timeout
  court, ce qui permet aussi de traiter les commandes d'ajout/retrait
  d'endpoints déposées par le thread GUI dans une queue.Queue
  thread-safe, sans dépendre de la boucle d'événements Qt du thread).
- Chaque message reçu (topic + JSON) est retransmis à l'interface
  graphique via le signal Qt newData, qui alimente l'historique de la
  caméra correspondante (par son 'name') et met à jour sa courbe.

@author: juliengautier
"""

import sys
import os
import csv
import time
import json
import queue

import zmq
import qdarkstyle
import pyqtgraph as pg
from PyQt6 import QtCore
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                              QHBoxLayout, QComboBox, QLabel, QPushButton,
                              QLineEdit, QListWidget, QGroupBox, QFormLayout,
                              QMessageBox, QCheckBox, QSpinBox, QFileDialog)


# Champs numériques publiés par winMeas.py que l'on peut tracer
FIELDS = ['Max', 'Min', 'x max', 'y max', 'Sum', 'Mean',
          'x c.mass', 'y c.mass', 'user1', 'Motor']

# Colonnes écrites dans le fichier CSV de sauvegarde automatique
SAVE_COLUMNS = ['timestamp_local', 'name', 'File', 'Max', 'Min', 'x max', 'y max',
                'Sum', 'Mean', 'Size', 'x c.mass', 'y c.mass', 'user1',
                'Motor', 'MotorName', 'MotorUnit', 'AutoSave', 'TirNumber', 'date']


class ZMQSubscriberWorker(QtCore.QObject):
    """
    Tourne dans un QThread séparé. Un seul socket ZMQ SUB, connecté à
    plusieurs endpoints ("host:port") ajoutés/retirés dynamiquement.
    Émet un signal Qt à chaque nouveau message reçu, quelle que soit
    la caméra émettrice.
    """

    newData = QtCore.pyqtSignal(dict)
    connectionChanged = QtCore.pyqtSignal(bool)
    endpointStatusChanged = QtCore.pyqtSignal(str, bool)  # adresse, connecté

    def __init__(self):
        super().__init__()
        self.context = None
        self.socket = None
        self._running = False
        self._connectedEndpoints = set()
        # Queue thread-safe : le thread GUI y dépose des commandes
        # ('connect'/'disconnect', adresse), le thread worker les
        # traite entre deux réceptions (pas besoin de la boucle
        # d'événements Qt, qui ne tourne pas ici puisqu'on utilise une
        # boucle recv() bloquante avec timeout).
        self._commandQueue = queue.Queue()

    # --- Appelés depuis le thread GUI (thread-safe) ---
    def addEndpoint(self, address):
        """address: 'host:port'"""
        self._commandQueue.put(('connect', address))

    def removeEndpoint(self, address):
        self._commandQueue.put(('disconnect', address))

    def requestStop(self):
        self._running = False

    # --- Tourne dans le thread du worker ---
    @QtCore.pyqtSlot()
    def start(self):
        try:
            self.context = zmq.Context()
            self.socket = self.context.socket(zmq.SUB)
            self.socket.setsockopt_string(zmq.SUBSCRIBE, '')  # tous les topics/caméras
            self.socket.setsockopt(zmq.RCVTIMEO, 200)
            self._running = True
            self.connectionChanged.emit(True)
            print("📡 Abonné ZMQ prêt (en attente d'ajout de caméras)")
        except Exception as e:
            print(f"❌ Erreur initialisation ZMQ SUB: {e}")
            self.connectionChanged.emit(False)
            return

        self._receiveLoop()

    def _processCommands(self):
        while True:
            try:
                cmd, address = self._commandQueue.get_nowait()
            except queue.Empty:
                break
            url = f"tcp://{address}"
            try:
                if cmd == 'connect' and address not in self._connectedEndpoints:
                    self.socket.connect(url)
                    self._connectedEndpoints.add(address)
                    self.endpointStatusChanged.emit(address, True)
                    print(f"📡 Connecté à la caméra {url}")
                elif cmd == 'disconnect' and address in self._connectedEndpoints:
                    self.socket.disconnect(url)
                    self._connectedEndpoints.discard(address)
                    self.endpointStatusChanged.emit(address, False)
                    print(f"📡 Déconnecté de {url}")
            except Exception as e:
                print(f"❌ Erreur endpoint {url}: {e}")

    def _receiveLoop(self):
        """Boucle d'attente événementielle des messages PUB (recv bloquant avec timeout)."""
        while self._running:
            self._processCommands()
            try:
                topic_bytes, payload_bytes = self.socket.recv_multipart()
                data = json.loads(payload_bytes.decode('utf-8'))
                self.newData.emit(data)
            except zmq.Again:
                # Rien reçu pendant le timeout : on reboucle pour
                # vérifier _running et traiter d'éventuelles commandes
                continue
            except Exception as e:
                print(f"❌ Erreur réception ZMQ: {e}")
                continue
        self._cleanup()

    def _cleanup(self):
        try:
            if self.socket:
                self.socket.close()
            if self.context:
                self.context.term()
        except Exception:
            pass
        finally:
            self.socket = None
            self.context = None
            self._connectedEndpoints.clear()
            self.connectionChanged.emit(False)
            print("📡 Abonné ZMQ arrêté")


class ZMQPlotWidget(QMainWindow):
    """
    Fenêtre affichant, pour plusieurs caméras/PC émetteurs simultanément,
    l'évolution d'un champ (Max, Min, Sum, Mean, ...) reçu en direct via
    ZMQ SUB. Une courbe par caméra (identifiée par son 'name'), avec légende.
    """

    def __init__(self, endpoints=None, parent=None):
        super().__init__(parent)
        self.setStyleSheet(qdarkstyle.load_stylesheet(qt_api='pyqt6'))
        self.setWindowTitle('Traçage ZMQ multi-caméras - MEAS')
        self.resize(1000, 900)

        self.zmqThread = None
        self.zmqWorker = None
        self.listening = False

        self.historyByName = {}   # name (self.name de MEAS) -> liste de dicts reçus
        self.endpoints = []       # liste des "host:port" ajoutés
        self.lastMotorInfo = (None, None)  # (nom, unité) du dernier moteur actif reçu
        
        # Deux graphes indépendants, chacun avec son propre champ sélectionné
        # et ses propres courbes par caméra : {1: {...}, 2: {...}}
        self.curvesByName = {1: {}, 2: {}}
        self.fieldBox = {}
        self.plotWidget = {}
        self.legend = {}
        
        # Sauvegarde automatique périodique (CSV, un nouveau fichier par jour)
        self.pendingSaveRows = []  # lignes accumulées depuis la dernière sauvegarde
        self.autoSaveTimer = QtCore.QTimer(self)
        self.autoSaveTimer.timeout.connect(self.performAutoSave)

        self._setupUI()

        for ep in (endpoints or []):
            self._addEndpointToList(ep)

    # ------------------------------------------------------------------
    def _setupUI(self):
        central = QWidget()
        vLayout = QVBoxLayout()

        # --- Ligne 1 : gestion des caméras (endpoints) ---
        camGroup = QGroupBox("Caméras (PC émetteurs)")
        camLayout = QHBoxLayout()

        formAdd = QFormLayout()
        self.hostEdit = QLineEdit("localhost")
        self.hostEdit.setMaximumWidth(140)
        formAdd.addRow("IP / Host:", self.hostEdit)

        self.portEdit = QLineEdit("5556")
        self.portEdit.setMaximumWidth(80)
        formAdd.addRow("Port:", self.portEdit)
        camLayout.addLayout(formAdd)

        btnLayout = QVBoxLayout()
        self.addEndpointBtn = QPushButton("➕ Ajouter caméra")
        self.addEndpointBtn.clicked.connect(self.onAddEndpoint)
        btnLayout.addWidget(self.addEndpointBtn)

        self.removeEndpointBtn = QPushButton("➖ Retirer sélection")
        self.removeEndpointBtn.clicked.connect(self.onRemoveEndpoint)
        btnLayout.addWidget(self.removeEndpointBtn)
        camLayout.addLayout(btnLayout)

        self.endpointList = QListWidget()
        self.endpointList.setMaximumHeight(90)
        self.endpointList.setMinimumWidth(220)
        camLayout.addWidget(self.endpointList)

        listenLayout = QVBoxLayout()
        self.listenBtn = QPushButton("▶ Démarrer l'écoute")
        self.listenBtn.clicked.connect(self.toggleListening)
        listenLayout.addWidget(self.listenBtn)

        self.statusLabel = QLabel("🔴 Non connecté")
        listenLayout.addWidget(self.statusLabel)
        camLayout.addLayout(listenLayout)

        camGroup.setLayout(camLayout)
        vLayout.addWidget(camGroup)

        # --- Groupe : sauvegarde automatique (CSV, nouveau fichier chaque jour) ---
        saveGroup = QGroupBox("Sauvegarde automatique")
        saveLayout = QHBoxLayout()

        self.autoSaveCheckBox = QCheckBox("Activer")
        self.autoSaveCheckBox.stateChanged.connect(self.toggleAutoSave)
        saveLayout.addWidget(self.autoSaveCheckBox)

        saveLayout.addWidget(QLabel("Intervalle (min):"))
        self.autoSaveIntervalSpin = QSpinBox()
        self.autoSaveIntervalSpin.setMinimum(1)
        self.autoSaveIntervalSpin.setMaximum(120)
        self.autoSaveIntervalSpin.setValue(5)
        self.autoSaveIntervalSpin.valueChanged.connect(self.onAutoSaveIntervalChanged)
        saveLayout.addWidget(self.autoSaveIntervalSpin)

        saveLayout.addWidget(QLabel("Dossier:"))
        self.saveFolderEdit = QLineEdit()
        self.saveFolderEdit.setMinimumWidth(200)
        self.saveFolderEdit.setPlaceholderText("Choisir un dossier de sauvegarde...")
        saveLayout.addWidget(self.saveFolderEdit)

        self.browseSaveFolderBtn = QPushButton("📁 Parcourir...")
        self.browseSaveFolderBtn.clicked.connect(self.onBrowseSaveFolder)
        saveLayout.addWidget(self.browseSaveFolderBtn)

        self.saveNowBtn = QPushButton("💾 Sauvegarder maintenant")
        self.saveNowBtn.clicked.connect(self.performAutoSave)
        saveLayout.addWidget(self.saveNowBtn)

        self.loadFileBtn = QPushButton("📂 Ouvrir données enregistrées")
        self.loadFileBtn.clicked.connect(self.onLoadSavedFile)
        saveLayout.addWidget(self.loadFileBtn)

        self.autoSaveStatusLabel = QLabel("Sauvegarde auto désactivée")
        self.autoSaveStatusLabel.setStyleSheet("color: #aaaaaa;")
        saveLayout.addWidget(self.autoSaveStatusLabel)
        saveLayout.addStretch()

        saveGroup.setLayout(saveLayout)
        vLayout.addWidget(saveGroup)

        # --- Ligne 2 : nombre de caméras actives + effacement (commun aux 2 graphes) ---
        hLayout2 = QHBoxLayout()
        self.camerasLabel = QLabel("Caméras actives : 0")
        self.camerasLabel.setStyleSheet("font-weight: bold; color: #00bfff;")
        hLayout2.addWidget(self.camerasLabel)

        self.clearBtn = QPushButton("Effacer historique")
        self.clearBtn.clicked.connect(self.clearHistory)
        hLayout2.addWidget(self.clearBtn)
        hLayout2.addStretch()
        vLayout.addLayout(hLayout2)

        # --- Graphe 1 et Graphe 2 : chacun avec son sélecteur de champ ---
        self._setupOnePlot(vLayout, plotIdx=1, defaultFieldIndex=0)
        self._setupOnePlot(vLayout, plotIdx=2, defaultFieldIndex=4)  # 'Sum' par défaut

        central.setLayout(vLayout)
        self.setCentralWidget(central)

    def _setupOnePlot(self, parentLayout, plotIdx, defaultFieldIndex=0):
        """Crée un bloc [sélecteur de champ + graphique] pour le graphe plotIdx (1 ou 2)."""
        hLayout = QHBoxLayout()
        hLayout.addWidget(QLabel(f"Champ à tracer (graphe {plotIdx}):"))
        fieldBox = QComboBox()
        fieldBox.addItems(FIELDS)
        fieldBox.setCurrentIndex(defaultFieldIndex)
        fieldBox.currentIndexChanged.connect(lambda _=None, idx=plotIdx: self.redrawAll(idx))
        hLayout.addWidget(fieldBox)
        hLayout.addStretch()
        parentLayout.addLayout(hLayout)

        plotWidget = pg.PlotWidget()
        plotWidget.showGrid(x=True, y=True, alpha=0.3)
        plotWidget.setLabel('bottom', 'N° de tir (autosave) / Shoot')
        legend = plotWidget.addLegend()
        parentLayout.addWidget(plotWidget)

        self.fieldBox[plotIdx] = fieldBox
        self.plotWidget[plotIdx] = plotWidget
        self.legend[plotIdx] = legend

    # ------------------------------------------------------------------
    # Gestion des endpoints (caméras)
    # ------------------------------------------------------------------
    def onAddEndpoint(self):
        host = self.hostEdit.text().strip() or 'localhost'
        port = self.portEdit.text().strip() or '5556'
        if not port.isdigit():
            QMessageBox.warning(self, "Erreur", "Le port doit être un nombre.")
            return
        self._addEndpointToList(f"{host}:{port}")

    def _addEndpointToList(self, address):
        if address in self.endpoints:
            return
        self.endpoints.append(address)
        self.endpointList.addItem(address)
        if self.listening and self.zmqWorker:
            self.zmqWorker.addEndpoint(address)

    def onRemoveEndpoint(self):
        item = self.endpointList.currentItem()
        if item is None:
            return
        address = item.text().split()[0]  # enlève le pictogramme 🟢 éventuel
        if address in self.endpoints:
            self.endpoints.remove(address)
        self.endpointList.takeItem(self.endpointList.row(item))
        if self.listening and self.zmqWorker:
            self.zmqWorker.removeEndpoint(address)

    # ------------------------------------------------------------------
    # Démarrage / arrêt de l'écoute ZMQ
    # ------------------------------------------------------------------
    def toggleListening(self):
        if not self.listening:
            self.startListening()
        else:
            self.stopListening()

    def startListening(self):
        if not self.endpoints:
            QMessageBox.information(
                self, "Aucune caméra",
                "Ajoutez au moins une caméra (IP/Host + port) avant de démarrer l'écoute."
            )
            return

        self.zmqThread = QtCore.QThread()
        self.zmqWorker = ZMQSubscriberWorker()
        self.zmqWorker.moveToThread(self.zmqThread)

        self.zmqThread.started.connect(self.zmqWorker.start)
        self.zmqWorker.newData.connect(self.onNewData)
        self.zmqWorker.connectionChanged.connect(self.onConnectionChanged)
        self.zmqWorker.endpointStatusChanged.connect(self.onEndpointStatusChanged)

        self.zmqThread.start()

        # On dépose les commandes de connexion : elles seront traitées
        # dès que le worker aura terminé son start() (queue thread-safe).
        for address in self.endpoints:
            self.zmqWorker.addEndpoint(address)

        self.listening = True
        self.listenBtn.setText("⏹ Arrêter l'écoute")

    def stopListening(self):
        if self.zmqWorker:
            self.zmqWorker.requestStop()
        if self.zmqThread:
            self.zmqThread.quit()
            self.zmqThread.wait(1500)

        self.listening = False
        self.listenBtn.setText("▶ Démarrer l'écoute")
        self.statusLabel.setText("🔴 Non connecté")

    def onConnectionChanged(self, ok):
        self.statusLabel.setText("🟢 En écoute" if ok else "🔴 Non connecté")

    def onEndpointStatusChanged(self, address, connected):
        # Repère visuellement dans la liste les caméras effectivement connectées
        for i in range(self.endpointList.count()):
            item = self.endpointList.item(i)
            if item.text().split()[0] == address:
                item.setText(f"{address}  {'🟢' if connected else ''}")

    # ------------------------------------------------------------------
    # Réception des données / traçage multi-courbes
    # ------------------------------------------------------------------
    def onNewData(self, data):
        self._ingestDataPoint(data, recordForSave=True)

    def _ingestDataPoint(self, data, recordForSave=True):
        """
        Ajoute un point de donnée à l'historique et met à jour les courbes.
        Utilisée à la fois pour les données reçues en direct (ZMQ) et pour
        les données rechargées depuis un fichier CSV enregistré
        (recordForSave=False dans ce dernier cas, pour ne pas ré-écrire
        dans le fichier de sauvegarde des données qui en proviennent déjà).
        """
        name = str(data.get('name', 'inconnu'))
        self.historyByName.setdefault(name, []).append(data)
        
        # Mémorise le dernier moteur actif connu (nom + unité), pour
        # affiner le label de l'axe quand le champ 'Motor' est tracé
        motorName = data.get('MotorName')
        motorUnit = data.get('MotorUnit')
        if motorName is not None:
            self.lastMotorInfo = (motorName, motorUnit)

        if recordForSave:
            # Accumule la ligne pour la prochaine sauvegarde automatique (même
            # si la sauvegarde auto n'est pas activée : coût négligeable, et
            # permet de ne rien perdre si on l'active plus tard)
            row = dict(data)
            row['name'] = name
            row['timestamp_local'] = time.strftime("%Y-%m-%d %H:%M:%S")
            self.pendingSaveRows.append(row)

        isNewCamera = name not in self.curvesByName[1]
        for plotIdx in (1, 2):
            if name not in self.curvesByName[plotIdx]:
                self._createCurve(name, plotIdx)
            self._updateCurve(name, plotIdx)

        if isNewCamera:
            self.camerasLabel.setText(f"Caméras actives : {len(self.curvesByName[1])}")

    def _createCurve(self, name, plotIdx):
        idx = len(self.curvesByName[plotIdx])
        color = pg.intColor(idx, hues=max(idx + 1, 6))
        curve = self.plotWidget[plotIdx].plot(
            pen=pg.mkPen(color=color, width=2),
            symbol='o', symbolSize=5, symbolBrush=color,
            name=name,
        )
        self.curvesByName[plotIdx][name] = curve

    def _updateCurve(self, name, plotIdx):
        field = self.fieldBox[plotIdx].currentText()
        x = []
        y = []
        seq = 0  # compteur incrémental utilisé quand l'autosave n'est pas actif
        for d in self.historyByName.get(name, []):
            v = d.get(field)
            try:
                v = float(v)
            except (TypeError, ValueError):
                # ex: 'Size' est une chaîne "x*y", non numérique -> ignoré
                continue
            
            tirNumber = d.get('TirNumber')
            if d.get('AutoSave') and tirNumber is not None:
                # Mode autosave actif : on utilise le numéro de tir réel,
                # cohérent avec la numérotation des fichiers sauvegardés
                xVal = tirNumber
            else:
                # Pas d'autosave (ou pas de numéro dispo) : comportement
                # inchangé, simple compteur incrémental
                xVal = seq
            
            x.append(xVal)
            y.append(v)
            seq += 1
        
        self.curvesByName[plotIdx][name].setData(x, y)
        
        if field == 'Motor' and self.lastMotorInfo[0] is not None:
            motorName, motorUnit = self.lastMotorInfo
            label = f"{motorName} ({motorUnit})" if motorUnit else motorName
        else:
            label = field
        self.plotWidget[plotIdx].setLabel('left', label)

    def redrawAll(self, plotIdx=None):
        """Retrace les courbes (ex: après changement de champ sélectionné).
        Si plotIdx est None, retrace les deux graphes."""
        indices = (plotIdx,) if plotIdx is not None else (1, 2)
        for idx in indices:
            for name in self.curvesByName[idx]:
                self._updateCurve(name, idx)

    def clearHistory(self):
        self.historyByName = {}
        self.lastMotorInfo = (None, None)
        for plotIdx in (1, 2):
            for curve in self.curvesByName[plotIdx].values():
                self.plotWidget[plotIdx].removeItem(curve)
            self.curvesByName[plotIdx] = {}
        self.camerasLabel.setText("Caméras actives : 0")

    # ------------------------------------------------------------------
    # Sauvegarde automatique (CSV, un nouveau fichier par jour)
    # ------------------------------------------------------------------
    def onBrowseSaveFolder(self):
        folder = QFileDialog.getExistingDirectory(
            self, "Choisir le dossier de sauvegarde",
            self.saveFolderEdit.text().strip() or os.path.expanduser("~")
        )
        if folder:
            self.saveFolderEdit.setText(folder)

    def toggleAutoSave(self, state):
        if state:
            if not self.saveFolderEdit.text().strip():
                QMessageBox.warning(
                    self, "Dossier manquant",
                    "Choisissez d'abord un dossier de sauvegarde."
                )
                self.autoSaveCheckBox.setChecked(False)
                return
            intervalMs = self.autoSaveIntervalSpin.value() * 60 * 1000
            self.autoSaveTimer.start(intervalMs)
            self.autoSaveStatusLabel.setText(
                f"Sauvegarde auto active (toutes les {self.autoSaveIntervalSpin.value()} min)"
            )
        else:
            self.autoSaveTimer.stop()
            self.autoSaveStatusLabel.setText("Sauvegarde auto désactivée")

    def onAutoSaveIntervalChanged(self, value):
        if self.autoSaveTimer.isActive():
            self.autoSaveTimer.start(value * 60 * 1000)  # redémarre avec le nouvel intervalle

    def performAutoSave(self):
        """
        Écrit (en ajout) toutes les lignes reçues depuis la dernière
        sauvegarde dans un fichier CSV nommé avec la date du jour. Un
        nouveau fichier est donc automatiquement créé chaque jour, sans
        logique supplémentaire : le nom de fichier change avec la date.
        """
        if not self.pendingSaveRows:
            self.autoSaveStatusLabel.setText(
                f"Rien à sauvegarder ({time.strftime('%H:%M:%S')})"
            )
            return

        folder = self.saveFolderEdit.text().strip()
        if not folder or not os.path.isdir(folder):
            self.autoSaveStatusLabel.setText("⚠️ Dossier de sauvegarde invalide")
            return

        today = time.strftime("%Y_%m_%d")
        filepath = os.path.join(folder, f"widgetZMQPlot_{today}.csv")
        fileExists = os.path.isfile(filepath)

        try:
            with open(filepath, 'a', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=SAVE_COLUMNS, extrasaction='ignore')
                if not fileExists:
                    writer.writeheader()
                for row in self.pendingSaveRows:
                    writer.writerow(row)

            savedCount = len(self.pendingSaveRows)
            self.pendingSaveRows = []
            self.autoSaveStatusLabel.setText(
                f"✅ Dernière sauvegarde {time.strftime('%H:%M:%S')} "
                f"({savedCount} lignes) → {os.path.basename(filepath)}"
            )
        except Exception as e:
            print(f"❌ Erreur sauvegarde auto: {e}")
            self.autoSaveStatusLabel.setText(f"⚠️ Erreur sauvegarde: {e}")

    def onLoadSavedFile(self):
        """Ouvre un fichier CSV précédemment enregistré et retrace les courbes."""
        startDir = self.saveFolderEdit.text().strip() or os.path.expanduser("~")
        filepath, _ = QFileDialog.getOpenFileName(
            self, "Ouvrir un fichier de données enregistrées", startDir,
            "Fichiers CSV (*.csv);;Tous les fichiers (*)"
        )
        if not filepath:
            return

        reply = QMessageBox.question(
            self, "Charger les données",
            "Charger ce fichier va remplacer les courbes actuellement affichées.\n"
            "Continuer ?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.Yes
        )
        if reply != QMessageBox.StandardButton.Yes:
            return

        self.clearHistory()

        count = 0
        try:
            with open(filepath, newline='', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    data = self._parseSavedRow(row)
                    self._ingestDataPoint(data, recordForSave=False)
                    count += 1
        except Exception as e:
            QMessageBox.warning(self, "Erreur", f"Impossible de charger le fichier :\n{e}")
            return

        self.setWindowTitle(f"Traçage ZMQ multi-caméras - MEAS  [{os.path.basename(filepath)}]")
        self.autoSaveStatusLabel.setText(f"📂 {count} points chargés depuis {os.path.basename(filepath)}")

    def _parseSavedRow(self, row):
        """Reconvertit une ligne CSV (tout en texte) vers les types d'origine."""
        numericFields = ('Max', 'Min', 'x max', 'y max', 'Sum', 'Mean',
                         'x c.mass', 'y c.mass', 'user1', 'Motor', 'TirNumber')
        data = {}
        for key in SAVE_COLUMNS:
            v = row.get(key)
            if v is None or v == '':
                data[key] = None
            elif key in numericFields:
                try:
                    data[key] = float(v)
                except ValueError:
                    data[key] = None
            elif key == 'AutoSave':
                data[key] = str(v).strip().lower() in ('true', '1', 'yes')
            else:
                data[key] = v
        return data

    def closeEvent(self, event):
        if self.autoSaveTimer.isActive():
            self.autoSaveTimer.stop()
            if self.pendingSaveRows:
                self.performAutoSave()  # sauvegarde ce qui reste en attente
        if self.listening:
            self.stopListening()
        event.accept()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyleSheet(qdarkstyle.load_stylesheet(qt_api='pyqt6'))
    # Exemple : pré-remplir avec les caméras connues
    w = ZMQPlotWidget(endpoints=['localhost:5556'])
    w.show()
    sys.exit(app.exec())
