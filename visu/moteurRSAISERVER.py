#! /home/upx/loaenv/bin/python3.12
# -*- coding: utf-8 -*-
"""
Created on 10octobre 2024
@author: Julien Gautier (LOA)
last modified 18 oct 2024

Dialog to RSAI motors rack via firebird database

"""

import time
from PyQt6 import QtCore
from PyQt6.QtWidgets import QMessageBox,QApplication
import  socket
from  PyQt6.QtCore import QUuid, QMutex
import sys, os 
import socket as _socket
import ast
import pathlib

p = pathlib.Path(__file__).parent
sepa = os.sep

fileconf = str(p) + sepa + "confServer.ini"
confServer = QtCore.QSettings(fileconf,QtCore.QSettings.Format.IniFormat)
server_host = str( confServer.value('MAIN'+'/server_host') )# 
serverPort =int(confServer.value('MAIN'+'/serverPort'))
clientSocket =_socket.socket(_socket.AF_INET,_socket.SOCK_STREAM)
#clientSocket.settimeout(5)

try :
    clientSocket.connect((server_host,serverPort))
    isconnected = True
    msg = 'clientid'
    clientSocket.sendall(msg.encode())
    id = clientSocket.recv(1024).decode()
    print('connected with id' ,id)
    

except :
    isconnected = False
    print('client not connected')

def listRack():
    cmdsend = " %s" %('listRack',)
    clientSocket.sendall((cmdsend).encode())
    listRack = clientSocket.recv(1024).decode()
    listRack = ast.literal_eval(listRack)
    return listRack

def nameEquipment(IP):
    cmd = 'nomRack'
    cmdsend = " %s, %s, %s " %(IP,1,cmd)
    clientSocket.sendall((cmdsend).encode())
    nameRack = clientSocket.recv(1024).decode().split()[0]
    return nameRack
    

mut = QMutex()

def closeConnection():
    # close connection
    clientSocket.close()

def listMotorName(IP):
    listMotor = []
    print(IP)
    for i in range(0,14):
            cmd = 'name'
            cmdsend = " %s, %s, %s " %(IP,i+1,cmd)
            clientSocket.sendall((cmdsend).encode())
            name = clientSocket.recv(1024).decode() #.split()[0]
            listMotor.append(name)
    return listMotor

class MOTORRSAI():
    """
    MOTORRSAI(IpAdrress,NoMotor) 
    class is defined by Ipadress of the rack and axis number 
    """

    def __init__(self, IpAdrress,NoMotor,parent=None):
        
        self.IpAdress = IpAdrress
        self.NoMotor = NoMotor
        self.isconnected = isconnected
        self.clientSocket = clientSocket
        #self.mut = mut
        self.update()

    def update(self):
        '''update from the data base')
        '''

        self.name = self.getName()
        self.step = self.getStepValue()
        self.butPlus = self.getButLogPlusValue()
        self.butMoins = self.getButLogMoinsValue()

        self.refName=[]
        for i in range (0,6):
            r = self.getRefName(i)
            self.refName.append(r)
            
        self.refValue=[]
        for i in range (0,6):
            if self.step == 0:
                self.step = 1
            rr = self.getRefValue(i)/self.step
            self.refValue.append(rr)
            # time.sleep(0.01)

    def sendMessage(self,message=''):
        # print('message',self.isconnected)
        retour = '1'
        if self.isconnected is True:
            mut.lock()
            try:
                #print('lock')
                a = self.clientSocket.sendall(message.encode())
                retour = self.clientSocket.recv(1024).decode()
                self.isconnected = True
                retour =  retour.split()[0]
                
            except:
                self.isconnected = False
                self.clientSocket.close()
                print('error connection')

                retour = '1'
        if self.isconnected is False :    
            try: 
                #print('try again')
                self.clientSocket = _socket.socket(_socket.AF_INET,_socket.SOCK_STREAM)
                self.clientSocket.settimeout(2)
                self.clientSocket.connect((server_host,serverPort))
                self.isconnected = True
                retour = 1 
                #print('try again succes')
            except:
                #print('try again error')
                retour = '1' # avoid divide by zero 
                self.isconnected = False
                self.clientSocket.close()
                #print('socket close)')
        mut.unlock() 
            
        return retour
    
    def position(self):
        '''
        return motor postion
        '''
        cmd ='position'
        cmdsend = " %s, %s, %s " %(self.IpAdress,self.NoMotor,cmd)
        
        
        self._position = self.sendMessage(cmdsend) 
        try :
            self._position = float(self._position) 
        except :
            self._position = 1 
        return self._position
        
    
    def getName(self):
        '''
        get motor name
        '''
        cmd ='name'
        cmdsend = " %s, %s, %s " %(self.IpAdress,self.NoMotor,cmd)
        
        
        self._name = self.sendMessage(cmdsend)
        return self._name
    
    def setName(self,nom):
        '''
        set motor name
        '''
        cmd = 'setName'
        cmdsend = " %s, %s, %s,%s " %(self.IpAdress,self.NoMotor,cmd,nom)
        time.sleep(0.05)
        

    def getRefName(self,nRef) :
        '''
        get ref n° name
        '''
        cmd = 'ref' +str(nRef)+'Name'
        cmdsend = " %s, %s, %s" %(self.IpAdress,self.NoMotor,cmd)
        
        dat = self.sendMessage(cmdsend)
        return dat
    
    def setRefName(self,nRef,name) :
        '''
        set ref n° name
        '''
        cmd ='setRefName'
        nRef = nRef+1
        nRef= str(nRef)
        name =str(name)
        cmdsend = " %s, %s, %s, %s, %s " %(self.IpAdress,self.NoMotor,cmd,name,nRef)
        dat = self.sendMessage(cmdsend)
        time.sleep(0.05)
        
    def getRefValue(self,nRef) :
        '''
        get value of the refereence position nRef
        '''
        nRef = nRef
        cmd = 'ref' +str(nRef)+'Pos'
        cmdsend = " %s, %s, %s" %(self.IpAdress,self.NoMotor,cmd)
        dat = float(self.sendMessage(cmdsend))
        return dat
    
    def setRefValue(self,nReff,value) :
        '''
        set value of the refereence position nRef
        '''
        cmd = 'setRefPos'
        nReff = str(nReff+1)
        value = str(value)
        cmdsend = " %s, %s, %s, %s, %s" %(self.IpAdress,self.NoMotor,cmd,value,nReff)
        dat = self.sendMessage(cmdsend)
        

    def getStepValue(self):
        '''Valeur de 1 pas dans l'unites
        '''
        cmd = 'step'
        cmdsend = "%s, %s, %s" %(self.IpAdress,self.NoMotor,cmd)
        
        
        dat = self.sendMessage(cmdsend)
        try :
            dat = float(dat)
        except :
            dat = 1 
        return dat

    def getButLogPlusValue(self):
        cmd = 'buteePos'
        cmdsend = "%s, %s, %s" %(self.IpAdress,self.NoMotor,cmd)
        
        dat = self.sendMessage(cmdsend)
        try :
            dat = float(dat)
        except :
            dat = 1
        return dat
    
    def setButLogPlusValue(self,butPlus):
        """"""
    
    def getButLogMoinsValue(self):
        cmd = 'buteeNeg'
        cmdsend = "%s, %s, %s" %(self.IpAdress,self.NoMotor,cmd)
        dat = self.sendMessage(cmdsend)
        try :
            dat = float(dat)
        except :
            dat = 1
        return dat
    
    def setButLogMoinsValue(self,butMoins):
        """"""

    def rmove(self,posrelatif,vitesse=1000):
        '''
        relative move of NoMotor of IpAdress
        posrelatif = position to move in step
        #to do faire self.curcwd
        '''
        cmd = 'rmove'
        pos = int(posrelatif)
        cmdsend = "%s, %s, %s,%s" %(self.IpAdress,self.NoMotor,cmd,pos)
        
        rec = self.sendMessage(cmdsend)
        if rec != 'ok':
            print('error cmd')
        

    def move(self,pos,vitesse=1000):
        '''absolue move of NoMotor  of IpAdress
        pos = position to move in step
        '''
        cmd = 'move'
        pos = int(pos)
        cmdsend =" %s, %s, %s,%s" %(self.IpAdress,self.NoMotor,cmd,pos)
        
        rec = self.sendMessage(cmdsend)
        if rec != 'ok':
            print('error cmd')

    def setzero(self):
        """
        setzero(self.moteurname):Set Zero
        """
        cmd = 'setzero'
    
        cmdsend = " %s, %s, %s" %(self.IpAdress,self.NoMotor,cmd)
        rec = self.sendMessage(cmdsend)
        if rec != 'ok':
            print('error cmd')

    def stopMotor(self): # stop le moteur motor
        """ 
        stopMotor(motor): stop le moteur motor
        """
        cmd = 'stop'
    
        cmdsend =" %s, %s, %s" %(self.IpAdress,self.NoMotor,cmd)
        
        rec = self.sendMessage(cmdsend)
        if rec != 'ok':
            print('error cmd')


    def etatMotor(self):
        '''
        read status of the motor
        '''
        cmd = 'etat'
        cmdsend = " %s, %s, %s" %(self.IpAdress,self.NoMotor,cmd)
        
        dat = self.sendMessage(cmdsend)
        
        if self.isconnected is False :
            print('server not connected')
            dat = 'notconnected'
        return dat
        

    def getEquipementName(self):
        '''
        return the name of the equipement of which the motor is connected

        '''
        cmd = 'nomRack'
        cmdsend = " %s, %s, %s" %(self.IpAdress,self.NoMotor,cmd)
        
        dat = self.sendMessage(cmdsend)
        return dat
 


if __name__ == '__main__':
    a = MOTORRSAI('10.0.6.30',1)
    print(listRack())
    #a.setRefName(0,'test')
    #closeConnection()

