# -*- coding: UTF-8
"""
Pilotage des controleurs RSAI via les ddl PilmotTango.dll et openMD.dll
python 3.X pyQT5
system 32 bit (at least python MSC v.1900 32 bit (Intel)) 
@author: Gautier julien loa
Created on Tue Jan 4 10:42:10 2018
modified on Tue Feb 27 15:49:32 2018
"""

#%% Imports
import ctypes
import time
import pathlib

try:
    from PyQt5.QtCore import QSettings
except:
    from PyQt4.QtCore import QSettings


#%% DLL

#conf = QSettings(QSettings.IniFormat, QSettings.UserScope, "configMoteur", "configMoteurRSAI")

p = pathlib.Path(__file__)
l = p.parent / 'DLL' /'PilMotTango.dll'
#sepa=os.sep
#pathDLL=str(p.parent) + sepa+'DLL' +sepa
dll_file =str(l)
print(dll_file)# './DLL/PilMotTango.dll'
#modbus_file='DLL/OpenModbus.dll'

    #PilMot=ctypes.windll.PilMotTango # Chargement de la dll PilMotTango et OpenMD .dll
PilMot = ctypes.windll.LoadLibrary(dll_file)

IP    = b"10.0.2.30\0      10.0.2.31\0      10.0.4.30\0      " 
IPs_C = ctypes.create_string_buffer(IP, 48) # permet d avoir la liste comme demander dans la dll
    


#%% Functions connections RSAI
def startConnexion():
    """ Ouverture d'une connexion avec les racks RSAI """
    print("RSAI initialisation ...")
    
        #modbus=ctypes.windll.LoadLibrary(modbus_file)

    
    #%% ENTREE
    # liste adresse IP des modules
   
    
    
    argout = 0
    argoutetat = PilMot.rEtatConnexion( ctypes.c_int16(0) ) # numero equipement
    if argoutetat != 3:
        argout = PilMot.Start(ctypes.c_int(3), IPs_C) # nb equipement , liste IP
        if argout == 1 :
            print('RSAI connection : OK RSAI connected @\n', IP)
        else:
            print('RSAI connexion failed')
    return argout

def stopConnexion():
    """ arret des connexions """
    print('RSAI  connexion stopped ')
    PilMot.Stop() # arret de toute les connexion


def testConnection():
    argout = PilMot.rEtatConnexion(ctypes.c_int16(0)) # numero equipement
    if argout == 3:
            print('Test connection OK')
    elif argout == 1:
            print('Already connected at \n', IP)
    else :
        print('Test connexion failed')
    return argout



#%% class MOTORSAI
    
class MOTORRSAI():
    def __init__(self, mot1='',parent=None):
        #super(MOTORNEWPORT, self).__init__()
        self.moteurname=mot1
        p = pathlib.Path(__file__)
        l = p.parent / 'fichiersConfig'/'configMoteurRSAI.ini'
        confRSAI = QSettings(str(l), QSettings.IniFormat)
        self.numEsim=ctypes.c_int16(int(confRSAI.value(self.moteurname+'/numESim')))
        self.numMoteur=ctypes.c_int16(int(confRSAI.value(self.moteurname+'/numMoteur')) )
        
        
    def stopMotor(self): # stop le moteur motor
        """ stopMotor(motor): stop le moteur motor """
        regCde = ctypes.c_uint(8) # 8 commande pour arreter le moteur
        PilMot.wCdeMot( self.numEsim , self.numMoteur, regCde, 0, 0)
        print("Stop")


    def move(self, pos, vitesse=10000):
        """
        move(self.moteurname,pos,vitesse): mouvement absolu du moteur (motor) a la position pos avec la vitesse vitesse
        """
        regCde = ctypes.c_uint(2) # commande mvt absolue
        posi   = ctypes.c_int(int(pos))
        vit    = ctypes.c_int( int(vitesse) )
        print(time.strftime("%A %d %B %Y %H:%M:%S"))
        print(self.moteurname, "position before ", self.position(), "(step)")
        PilMot.wCdeMot(self.numEsim , self.numMoteur, regCde, posi, vit)
        print(self.moteurname, "move to", pos, "(step)")

    def rmove(self, posrelatif, vitesse=1000):
        """
        rmove(motor,posrelatif,vitesse): : mouvement absolu du moteur (motor) a la position posrelatif avec la vitesse vitesse
        """
        regCde    = ctypes.c_uint(2) # commande mvt absolue
        posActuel = self.position()
        print(time.strftime("%A %d %B %Y %H:%M:%S"))
        print(self.moteurname,"position before ",posActuel,"(step)")
        pos  = int(posActuel+posrelatif)
        posi = ctypes.c_int(pos)
        vit  = ctypes.c_int(int(vitesse))
        PilMot.wCdeMot(self.numEsim , self.numMoteur, regCde, posi, vit)
        print(self.moteurname, "relative move of", posrelatif, "(step)")

    def setzero(self):
        """
        ## setzero(self.moteurname):Set Zero
        """
        regCde=ctypes.c_int(1024) #  commande pour zero le moteur (2^10)

        a=PilMot.wCdeMot(self.numEsim , self.numMoteur,regCde,ctypes.c_int(0),ctypes.c_int(0))
       
        print (self.moteurname,"zero set",a)


#%% Functions ETAT Moteur

    def etatMotor(self):
        """ Etat du moteur (alimentation on/off)
        a verifier
        """
        a=PilMot.rEtatMoteur(self.numEsim , self.numMoteur)
        if a==8320 or a==41088  or a==128 or a==41104 or a==32869:
            etat=1
        else :
            etat=0
        return etat
        print(self.moteurname,a,etat)

    def position(self):
        """ position (self.moteurname) : donne la postion de motor """
        pos=PilMot.rPositionMot(self.numEsim , self.numMoteur) # lecture position theorique en nb pas
        return pos
 
    
#%% Demarage connexion
        
startConnexion()   

 
#%%
if __name__ == "__main__":
    print("test")
    #startConnexion()


