#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Feb 13 16:02:40 2019

@author: juliengautier
"""

import qdarkstyle
from PyQt6.QtCore import pyqtSignal as Signal
from PyQt6 import QtCore, QtGui
from PyQt6.QtWidgets import QApplication, QCheckBox, QVBoxLayout, QHBoxLayout, QPushButton
from PyQt6.QtWidgets import QWidget, QLabel, QSpinBox, QLineEdit, QMessageBox, QFileDialog
from PyQt6.QtGui import QIcon
import sys
import os
import numpy as np
import socket as _socket
import pathlib
import time
import zmq
import uuid

class OPTION(QWidget):
    
    closeEventVar = QtCore.pyqtSignal(bool)
    emitChangeScale = QtCore.pyqtSignal(bool)
    emitChangeRot = QtCore.pyqtSignal(bool)

    def __init__(self, conf=None, name='VISU',parent=None):
        
        super().__init__()
        
        p = pathlib.Path(__file__)

        self.parent = parent
        self.setStyleSheet(qdarkstyle.load_stylesheet(qt_api='pyqt6'))
        if conf is None:
            self.conf = QtCore.QSettings(str(p.parent / 'confVisu.ini'), QtCore.QSettings.Format.IniFormat)
        else:
            self.conf = conf

        self.name = name
        sepa = os.sep
        self.icon = str(p.parent) + sepa+'icons' + sepa
        self.isWinOpen = False
        self.auto = False
        self.setWindowTitle('Options Auto Save & visualisation')
        self.setWindowIcon(QIcon(self.icon+'LOA.png'))
        
        # self.stepX=float(self.conf.value(self.name+"/stepX"))
        # self.stepY=float(self.conf.value(self.name+"/stepY"))

        self.shoot = int(self.conf.value(self.name+"/tirNumber"))
        self.setup()
        self.pathAutoSave = self.conf.value(self.name+"/path")
        self.pathBg = self.conf.value(self.name+"/pathBg")
        self.actionButton()
        self.dataBgExist = False
        self.rotateValue = 0
        self.modeTrig = False

    def setFile(self, file):
        self.nomFichier = file

    def setup(self):
        
        
        TogOff = self.icon+'Toggle_Off.png'
        TogOn = self.icon+'Toggle_On.png'
        TogOff = pathlib.Path(TogOff)
        TogOff = pathlib.PurePosixPath(TogOff)
        TogOn = pathlib.Path(TogOn)
        TogOn = pathlib.PurePosixPath(TogOn)
        self.setStyleSheet("QCheckBox::indicator{width: 30px;height: 30px;}""QCheckBox::indicator:unchecked { image : url(%s);}""QCheckBox::indicator:checked { image:  url(%s);}""QCheckBox{font :10pt;}" % (TogOff, TogOn))
        
        vbox1 = QVBoxLayout()
        self.buttonPath = QPushButton('Path : ')
        self.pathBox = QLineEdit(str(self.conf.value(self.name+"/pathAutoSave")))
        self.pathBox.setMaximumHeight(60)
        hbox1 = QHBoxLayout()
        hbox1.addWidget(self.buttonPath)
        hbox1.addWidget(self.pathBox)
        vbox1.addLayout(hbox1)
        
        hbox2 = QHBoxLayout()
        labelName = QLabel('Name : ')
        self.nameBox = QLineEdit(str(self.conf.value(self.name+"/nameFile")))
        self.nameBox.setMaximumHeight(30)
        hbox2.addWidget(labelName)
        hbox2.addWidget(self.nameBox)
        vbox1.addLayout(hbox2)
        
        hbox3 = QHBoxLayout()
        self.checkBoxTiff = QCheckBox('Save as TIFF', self)
        self.checkBoxTiff.setChecked(True)
        hbox2.addWidget(self.checkBoxTiff)
        
        self.checkBoxDate = QCheckBox('add date', self)
        self.checkBoxDate.setChecked(False)
        hbox2.addWidget(self.checkBoxDate)
        vbox1.addLayout(hbox3)
        
        hbox4 = QHBoxLayout()
        labelTirNumber = QLabel('Next number : ')
        self.checkBoxServer = QCheckBox('Auto', self)
        self.checkBoxServer.setChecked(False)
        hbox4.addWidget(self.checkBoxServer)
        
        self.tirNumberBox = QSpinBox()
        self.tirNumberBox.setMaximum(100000)
        self.tirNumberBox.setValue(self.shoot)
        hbox4.addWidget(labelTirNumber)
        hbox4.addWidget(self.tirNumberBox)
        vbox1.addLayout(hbox4)
        
        hbox5 = QHBoxLayout()
        self.buttonFileBg = QPushButton('Select Background File : ')
        self.fileBgBox = QLineEdit('bgfile not selected')
        self.fileBgBox.setMaximumHeight(60)
        hbox5 = QHBoxLayout()
        hbox5.addWidget(self.buttonFileBg)
        hbox5.addWidget(self.fileBgBox)
        vbox1.addLayout(hbox5)
        
        hMainLayout = QHBoxLayout()
        hMainLayout.addLayout(vbox1)
        self.setLayout(hMainLayout)
        self.setStyleSheet(qdarkstyle.load_stylesheet(qt_api='pyqt6'))
        
    def actionButton(self):
        self.buttonPath.clicked.connect(self.PathChanged)
        self.pathBox.textChanged.connect(self.pathTextChanged)
        self.nameBox.textChanged.connect(self.nameFileChanged)
        self.tirNumberBox.valueChanged.connect(self.TirNumberChange)
        self.buttonFileBg.clicked.connect(self.selectBg)
        # self.fileBgBox.textChanged.connect(self.bgTextChanged)
        self.checkBoxServer.stateChanged.connect(self.checkBoxServerChange)

    def pathTextChanged(self):
        self.pathAutoSave = self.pathBox.text()
        self.conf.setValue(self.name+"/pathAutoSave", str(self.pathAutoSave))
        
    def PathChanged(self):
       
        self.pathAutoSave = str(QFileDialog.getExistingDirectory(self, "Select Directory", self.pathAutoSave))
        self.pathBox.setText(self.pathAutoSave)
        self.conf.setValue(self.name+"/pathAutoSave", str(self.pathAutoSave))
        
    def nameFileChanged(self):
        self.fileName = self.nameBox.text()
        self.conf.setValue(self.name+"/nameFile", str(self.fileName))
            
    def TirNumberChange(self):
        self.tirNumber = self.tirNumberBox.value()
        self.conf.setValue(self.name+"/tirNumber", self.tirNumber)
        self.conf.sync()
        
    def setTirNumber(self, tirNumber):
        self.tirNumber = tirNumber
        self.tirNumberBox.setValue(self.tirNumber)
 
    def selectBg(self):
        
        fname = QFileDialog.getOpenFileName(self, "Select a background file", self.pathBg, "Images (*.txt *.spe *.TIFF *.sif);;Text File(*.txt);;Ropper File (*.SPE);;Andor File(*.sif);; TIFF file(*.TIFF)")
        fichier = fname[0]
        ext = os.path.splitext(fichier)[1]
        self.fileBgBox.setText(fichier)
        
        self.conf.setValue(self.name+"/pathBg", os.path.dirname(fichier))
        
        self.dataBgExist = True
        self.parent.checkBoxBg.setChecked(True)
        self.parent.BackgroundF()

        if ext == '.txt':  # text file
            self.dataBg = np.loadtxt(str(fichier))
            self.dataBg = np.rot90(self.dataBg, 3)
        elif ext == '.spe' or ext == '.SPE':  # SPE file
            from winspec import SpeFile
            dataSPE = SpeFile(fichier)
            data1 = dataSPE.data[0]  # .transpose() # first frame
            self.dataBg = data1  # np.flipud(data1)
        elif ext == '.TIFF':  # tiff File
            from PIL import Image
            dat = Image.open(fichier)
            dat = np.rot90(dat, 3)
            self.dataBg = np.array(dat)
        elif ext == '.sif':
            from andor import SifFile
            sifop = SifFile()
            im = sifop.openA(fichier)
            self.dataBg = np.rot90(im, 3)
            
        else:
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Icon.Critical)
            msg.setText("Wrong file format !")
            msg.setInformativeText("The format of the file must be : .SPE  .TIFF .sif or .txt ")
            msg.setWindowTitle("Warning ...")
            msg.setWindowFlags(QtCore.Qt.WindowType.WindowStaysOnTopHint)
            msg.exec_()
            self.dataBgExist = False
    
    def checkBoxServerChange(self):
        
        if self. checkBoxServer.isChecked():
            # print('start number of shot Client')
            self.threadClient = THREADCLIENT(self)
            self.threadClient.start()
            self.threadClient.newShotnumber.connect(self.receiveNewNumber)
            self.threadClient.pathSignal.connect(self.receiveNewPath)
            self.threadClient.autoSignal.connect(self.receiveAuto)
        else:
            # print('close client')
            self.threadClient.stopClientThread()
    
    def receiveNewNumber(self, nbShot):
        self.tirNumberBox.setValue(nbShot)
        
    def receiveNewPath(self,path):
        self.pathBox.setText(path)

    def receiveAuto(self,auto):
        self.auto = auto
        if auto == 'True':
            auto = True
        else : 
            auto = False 
        
        self.parent.checkBoxAutoSave.setChecked(auto)  # on passe en auto save sur visu 
        self.parent.autoSaveColor()
        if self.parent.parent is not None:
            # quand on passe en mode auto save la camera si elle existe passe aussi en mode trig et en play
            try: 
                if auto == True:
                    self.parent.parent.trigg.setCurrentIndex(1)
                    # time.sleep(0.1)
                    self.parent.parent.runButton.click()
                    self.modeTrig = True
                else:
                    if self.modeTrig == True: # quand on decoche le mode autosave camera en mode free run 
                        #  on stop 1 fois mais apress on peut faire play sur la camera 
                        self.parent.parent.stopButton.click()
                        self.modeTrig = False
                    # self.parent.parent.trigg.setCurrentIndex(0)
            except Exception as e:
                print('error auto play or stop', e)

    def closeEvent(self, event):
        """ when closing the window
        """
        self.isWinOpen = False
        self.closeEventVar.emit(True)


class THREADCLIENT(QtCore.QThread):
    '''
    Thread client ZMQ 
    Tous les événements (SHOOT, CONFIG) sont reçus via PUB/SUB
    '''
    newShotnumber = Signal(int)   # Signal pour le numéro de tir
    pathSignal = Signal(str)      # Signal pour le path
    autoSignal = Signal(str)      # Signal pour autosave
    
    def __init__(self, parent):
        super(THREADCLIENT, self).__init__(parent)
        self.parent = parent
        self.conf = self.parent.conf
        self.name = self.parent.name
        
        # Lire la configuration
        self.serverHost = str(self.conf.value(self.name + "/server"))
        self.serverPort = int(self.conf.value(self.name + "/serverPort"))#, "5009")) # ? ??
        
        self.ClientIsConnected = False
        self.client_id = str(uuid.uuid4())
        
        # envoyer heartbeat au serveur 
        self.last_heartbeat = time.time()
        self.heartbeat_interval = 10 # interval de temps pour envoyer les heartbeat au serveur 
        
        # ZMQ context et sockets
        self.context = None
        self.sub_socket = None
        self.pub_socket = None
        
    def run(self):

        print(f"Connecting to ZMQ server: {self.serverHost}:{self.serverPort}")
        
        try:
            # Créer le contexte ZMQ
            self.context = zmq.Context()
            
            # Socket SUB pour recevoir les événements du serveur
            self.sub_socket = self.context.socket(zmq.SUB)
            self.sub_socket.connect(f"tcp://{self.serverHost}:{self.serverPort}")
            
            # S'abonner à tous les types d'événements
            self.sub_socket.setsockopt_string(zmq.SUBSCRIBE, "SHOOT")      # Événements de tir
            self.sub_socket.setsockopt_string(zmq.SUBSCRIBE, "CONFIG")     # Mises à jour path/autosave
            self.sub_socket.setsockopt_string(zmq.SUBSCRIBE, "REGISTERED") # Confirmation d'enregistrement client
            self.sub_socket.setsockopt_string(zmq.SUBSCRIBE, "HEARTBEAT")  # Heartbeat serveur pour gerer si deconnection

            # Socket PUB pour envoyer notre enregistrement
            self.pub_socket = self.context.socket(zmq.PUB)
            self.pub_socket.connect(f"tcp://{self.serverHost}:{self.serverPort + 1}")
            
            # Petite pause pour que la connexion s'établisse
            time.sleep(0.1)
            
            # S'enregistrer auprès du serveur
            self._send_register()
            
            self.ClientIsConnected = True
            #print(f'Client connected to server {self.serverHost}')
            
            # Mettre à jour l'interface
            self.parent.nameBox.setText(self.parent.name)
            
        except Exception as e:
            print(f'Connection error: {e}')
            print('Do you start the server?')
            self.ClientIsConnected = False
            self.parent.checkBoxServer.setChecked(False)
            return
        
        # Poller pour gérer les timeouts
        poller = zmq.Poller()
        poller.register(self.sub_socket, zmq.POLLIN)
        
        # Variables pour détecter la déconnexion
        last_heartbeat = time.time()
        self.heartbeat_timeout = 15.0  # 10 secondes sans heartbeat = serveur déconnecté

        # Boucle principale - Écouter les événements
        while self.ClientIsConnected:
            try:
                # Attendre un événement avec timeout de 100ms
                socks = dict(poller.poll(100))
                
                if self.sub_socket in socks and socks[self.sub_socket] == zmq.POLLIN:
                    # Recevoir l'événement
                    topic = self.sub_socket.recv_string()
                    event = self.sub_socket.recv_json()
                    
                    # Dispatcher selon le type d'événement
                    if topic == "SHOOT":
                        #print('client : shoot nb received')
                        self._handle_shoot_event(event)
                        last_heartbeat = time.time()  # Reset heartbeat
                    elif topic == "CONFIG":
                        self._handle_config_event(event)
                        last_heartbeat = time.time()  # Reset heartbeat
                    elif topic == "REGISTERED":
                        self._handle_registered_event(event)
                        last_heartbeat = time.time()  # Reset heartbeat
                    elif topic == "HEARTBEAT":
                        last_heartbeat = time.time()
                        # print("💓 Heartbeat received")
                else:
                    # vérifier si serveur toujours vivant
                    time_since_heartbeat = time.time() - last_heartbeat
                    
                    if time_since_heartbeat > self.heartbeat_timeout:
                        print(f"❌ Server timeout ({time_since_heartbeat:.1f}s without response)")
                        self.ClientIsConnected = False
                        # Fermer les sockets
                        if self.sub_socket:
                            self.sub_socket.close()
                        if self.pub_socket:
                            self.pub_socket.close()
                        if self.context:
                            self.context.term()
                        self.parent.checkBoxServer.setChecked(False)
                        time.sleep(1)
                        break

                # Petite pause pour ne pas surcharger le CPU
                time.sleep(0.01)
                if time.time() - self.last_heartbeat > self.heartbeat_interval :
                    self.send_hearbeat()

            except zmq.ZMQError as e:
                if e.errno == zmq.ETERM:
                    break  # Context terminé
                #print(f'ZMQ Error: {e}')
                self.ClientIsConnected = False
                self.parent.checkBoxServer.setChecked(False)
                break
            except Exception as e:
                #print(f'Error in client loop: {e}')
                import traceback
                traceback.print_exc()
                self.ClientIsConnected = False
                self.parent.checkBoxServer.setChecked(False)
                break
        
        # Nettoyage
        self._cleanup()
    
    def _send_register(self):
        """Envoyer notre enregistrement au serveur"""
        register_event = {
            'client_id': self.client_id,
            'name': self.name,
            'timestamp': time.time()
        }
        
        # Publier sur le topic REGISTER
        self.pub_socket.send_string("REGISTER", zmq.SNDMORE)
        self.pub_socket.send_json(register_event)
        
       # print(f"Sent registration for {self.name}")
    
    def _handle_registered_event(self, event):
        """Gérer la confirmation d'enregistrement"""
        client_id = event.get('client_id')
        if client_id == self.client_id:
            # print(f"Registration confirmed by server")
            # Optionnel: traiter la config initiale si le serveur l'envoie
            if 'path' in event:
                path = event['path']
                if sys.platform == 'linux':
                    lpath = "/mnt/SJ_NAS/"
                    path = path.replace("X:/", lpath)
                self.pathSignal.emit(path)
            
            if 'autosave' in event:
                self.autoSignal.emit(str(event['autosave']))
    
    def _handle_shoot_event(self, event):
        """
        Gérer un événement de tir reçu
    
        """
        nbshot = event.get('number')
        timestamp = event.get('timestamp') # pour aline si besoin
         # print('clien shoot receveid,nbshot', nbshot)
        # Émettre le signal si le numéro a changé
        if int(self.parent.tirNumberBox.value()) != nbshot:
            self.newShotnumber.emit(nbshot)
        
    
    def _handle_config_event(self, event):
        """
        Gérer un événement de mise à jour de configuration
        Permet au serveur de pousser des changements de config en temps réel
        """
        # Vérifier si c'est pour nous
        client_id = event.get('client_id')
        if client_id and client_id != self.client_id:
            return  # Pas pour nous
        
        # Mise à jour du path
        if 'path' in event:
            path = event['path']
            
            # Adaptation Linux
            if sys.platform == 'linux':
                lpath = "/mnt/SJ_NAS/"      # pas tres propre mais bon ...
                path = path.replace("X:/", lpath)
            
            if str(self.parent.pathBox.text()) != path:
                self.pathSignal.emit(path)
                # print(f"Path updated to: {path}")
        
        # Mise à jour de l'autosave
        if 'autosave' in event:
            autosave = str(event['autosave'])
            # print('autosave received', autosave)
            if autosave != self.parent.auto:
                self.autoSignal.emit(autosave)
                # print(f"Autosave updated to: {autosave}")
    
    def _cleanup(self):
        """Nettoyer les ressources"""
        try:
            # Envoyer un événement de déconnexion
            unregister_event = {
                'client_id': self.client_id,
                'name': self.name
            }
            self.pub_socket.send_string("UNREGISTER", zmq.SNDMORE)
            self.pub_socket.send_json(unregister_event)
            self.parent.checkBoxServer.setChecked(False)
        except:
            pass
        
        # Fermer les sockets
        if self.sub_socket:
            self.sub_socket.close()
        if self.pub_socket:
            self.pub_socket.close()
        if self.context:
            self.context.term()
    
    def send_hearbeat(self):
        """fct pouur envoyer heartbeat au serveur """

        self.pub_socket.send_string("CLIENT_HEARTBEAT",zmq.SNDMORE)
        self.pub_socket.send_json({
            'client_id':self.client_id,
            'timestamp':time.time()
        })
        self.last_heartbeat = time.time()

    def stopClientThread(self):
        """Arrêter le thread client"""
        self.ClientIsConnected = False
        time.sleep(0.1)
        self.quit()
        self.wait()



if __name__ == "__main__":
    appli = QApplication(sys.argv)
    appli.setStyleSheet(qdarkstyle.load_stylesheet(qt_api='pyqt6'))
    e = OPTION()
    e.show()
    appli.exec_() 