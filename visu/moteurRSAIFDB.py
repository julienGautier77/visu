# -*- coding: utf-8 -*-
"""
Created on 01 December 2023
@author: Julien Gautier (LOA)
last modified 22 decembre 2023

Dialog to RSAI motors rack via firebird database

"""

from firebird.driver import connect    ### pip install  firebird-driver
import time
from PyQt6 import QtCore
from PyQt6.QtWidgets import QMessageBox,QApplication
import  socket
from  PyQt6.QtCore import QUuid, QMutex
import sys

IPSoft = socket.gethostbyname(socket.gethostname()) # get the ip adress of the computer

UUIDSoftware = QUuid.createUuid() # create unique Id for software
UUIDSoftware = str(UUIDSoftware.toString()).replace("{","")
UUIDSoftware = UUIDSoftware.replace("}","")

mut=QMutex()
# if not local  dsn=10.0.5.X/ ??

## connection to data base 
con = connect('10.0.48.1/3050:C:/PilMotDB/PILMOTCONFIG.FDB', user='sysdba', password='masterkey')
# con = connect('C:\PilMotDB\PILMOTCONFIG.FDB', user='sysdba', password='masterkey')
cur = con.cursor()
curCWD=con.cursor()

def closeConnection():
    # close connection
    con.close()

# " dict for table values"
listParaStr ={'nomAxe' : 2 ,'nomEquip':10, 'nomRef1': 1201 , 'nomRef2':1202 , 'nomRef3':1203 , 'nomRef4':1204 , 'nomRef5':1205 , 'nomRef6':1206 , 'nomRef7':1207 , 'nomRef8':1208 , 'nomRef9':1209 , 'nomRef10':1210}
listParaReal = {'Step':1106 , 'Ref1Val': 1211 , 'Ref2Val':1212 , 'Ref3Val':1213 , 'Ref4Val':1214 , 'Ref5Val':1215 , 'Ref6Val':1216 , 'Ref7Val':1217 , 'Ref8Val':1218 , 'Ref9Val':1219 , 'Ref10Val':1220}
listParaInt = {'ButLogPlus': 1009 , 'ButLogNeg':1010 }

def addSoftToConnectedList():
    # add adress ip of the soft in the data base 
    # not working yet  to do ... 
    # need to create new Pikd for the table ...  
    insert = ( "INSERT INTO TbConnectedList(d_ParaDbUUID, d_ParaDbConnectName,d_ParaDbAlias) values(%s,%s,%s)" % (str(UUIDSoftware),str(IPSoft),"" ))
    cur.execute(insert)
    con.commit()
    
def listProgConnected():
    # Read the list of programs connected to database
    # nbProgConnected :  number of programs connected into database
    # p_ListPrg (returned): Described list of programs into database
    #  (Format of the field of the list for one program: PkId, UUID, SoftName, Alias, Hostname, IpAddress, TimeConnection, HeartCnt)
    SoftName = []
    HostName = []
    IpProgram = []
    cur.execute("SELECT * FROM " + "TBCONNECTEDLIST" + " ORDER BY PkId;" )

    for row in cur:
        SoftName.append(row[2])
        HostName.append(row[4])
        IpProgram.append(row[5])
    nbProgConnected = len(SoftName)
    return nbProgConnected, SoftName, HostName, IpProgram

if  'PilMotServer' in listProgConnected()[1]:
    print('server RSAI connected')
else :
    print('Server RSAI not launched')
    appli = QApplication(sys.argv)
    msg = QMessageBox()
    msg.setIcon(QMessageBox.Icon.Critical)
    msg.setText("Server RSAI not launched")
    msg.setInformativeText("Server RSAI not launched : start server ")
    msg.setWindowTitle("Warning ...")
    msg.setWindowFlags(QtCore.Qt.WindowType.WindowStaysOnTopHint)
    msg.exec()

def rEquipmentList():
    '''
    Read the list of Equipment connected to database equipement =Rack =IPadress 
    Described list of equipment into database
    Format of the field of the list for one equipment: PkId, Address, Category, Status)
    '''
    addressEquipement=[]
    cur.execute("SELECT * FROM " + "TBEQUIPMENT")
    for row in cur:
        addressEquipement.append (row[1])
    return addressEquipement

def getValueWhere1ConditionAND(cursor,TableName, ValToRead, ConditionColName,ConditionValue):
    ''' 
    Read the field value in a table where the 'column' equals 'value' corresponding Query = SELECT 'ValToRead'  FROM TableName WHERE ConditionColName = ConditionValue
    TableName : Table in which execute query
    ValToRead : Field Value to read
    ConditionColName : Column name for the condition of the query search
    ConditionValue : Value name for the condition of the query search
    return param p_DataRead : values read
    '''
   
    Prepare1Cond= "SELECT " + ValToRead  + " FROM " + TableName + " WHERE " + ConditionColName + " = '" + ConditionValue + "' ;"
    cursor.execute(Prepare1Cond )
    p_DataRead = cursor.fetchone()[0]
    
    return p_DataRead

def rEquipmentIdNbr(IpAddress):
    ''' Get Identification number of one PilMot equipement from its IP Address
    IpAddress: IP Address
    p_IdEquipment: Identification number of the equipement
    '''
    p_IdEquipment = getValueWhere1ConditionAND(cur,"TbEquipment", "PkId", "Address", IpAddress)
    
    return p_IdEquipment

def getSlotNumber(NoMotor):
    ''' 
    Get the slot number of ESBIM corresponding to the motor number
    return Slot number (value from 1 to 7)
    '''
    SlotNbr = 0
    SlotNbr = (NoMotor + 1 ) / 2
    return SlotNbr

def getAxisNumber(NoMotor):
    '''
    Get the axis number of module corresponding to the motor number
    return Slot number (value 1 or 2)
    '''
    AxisNbr = 1
    if(NoMotor % 2) == 0:
        AxisNbr = 2
    return AxisNbr

def readPkModBim2BOC(cursor,PkEsbim, NumSlotMod, NumAxis, FlgReadWrite=1):
    '''
    Read Primary key identifier of an axis module Bim2BOC :  p_PkModBim
    PkEsbim : numero Equipment on which the module is plugged
    NumSlotMod : Number of the slot of the module to get PK
    NumAxis : Axis number of the module
    param FlgReadWrite : Indicate if the function accesses to Read or Write table (value : 1=ReadTb, 0=WriteTb)
    '''
    TbToRead = "TbBim2Boc_1Axis_W"
    cursor.execute( "SELECT m.PkId FROM TbModule m INNER JOIN TbEquipment e ON m.idEquipment = e.PKID WHERE (e.PkId = " + str(int(PkEsbim)) + " and m.NumSlot = " + str(int(NumSlotMod)) + ");" )
    # for row in cur :
    #     TmpPkModBim=row[0] # cle dans TbModule correspondant cle Esbim dans TbEquipement et numero du slot  
    TmpPkModBim = cursor.fetchone()[0]
    cursor.execute( "SELECT b.PkId FROM " + TbToRead + " b WHERE IdModule = " + str(TmpPkModBim) + " AND NumAxis = " + str(int(NumAxis)) + ";" );
    # for row in cur :
    #     p_PKModBim =row[0]
    p_PKModBim = cursor.fetchone()[0]
    return p_PKModBim # cle dans TbBim2Boc_1Axis_W correpondant idmodule et au numero d axe

def nameMoteur(IpAdress,NoMotor):
    '''
    Get motor name from Ipadress et axe number
    '''
    IdEquipt = rEquipmentIdNbr(IpAdress)
    NoMod  = getSlotNumber(NoMotor)
    NoAxis = getAxisNumber(NoMotor)
    PkIdTbBoc = readPkModBim2BOC(cur,IdEquipt, NoMod, NoAxis, FlgReadWrite=1) # Read Primary key identifier of an axis module Bim2BOC :  p_PkModBim
    name = rStepperParameter(cur,PkIdTbBoc,NoMotor,listParaStr['nomAxe'])
    return name

def listMotorName(IpAdress):
    '''List des moteurs sur l'equipement IpAdress
    '''
    IdEquipt = rEquipmentIdNbr(IpAdress)
    
    listSlot=[]
    SELECT = 'select NumSlot from %s  where  IdEquipment= %s and NumSlot>=0'% ('TbModule',str(IdEquipt))   # list SLot
    cur.execute(SELECT)
    for row in cur :
       listSlot.append(row[0])
    
    listNameMotor=[]
    for noMot in range (1,2*len(listSlot)+1): # dans notre cas 1...14
        listNameMotor.append(nameMoteur(IpAdress,noMot))
    return listNameMotor
 
def nameEquipment(IpAdress):
    '''
    return the equipment name defined by IpAdress
    '''
    IdEquipt = rEquipmentIdNbr(IpAdress)
    SELECT = 'select PkId from %s  where  IdEquipment = %s and NumSlot = -1'% ('TbModule',str(IdEquipt))   # list Pkid module
    cur.execute(SELECT)
    PkIdMod = cur.fetchone()[0]

    SELECT = 'select ValParam from %s where IDMODULE = %s and IDNAME = 10 '% ('TbParameterSTR',str(PkIdMod))
    cur.execute(SELECT)
    nameEquip=cur.fetchone()[0]
    return nameEquip

    
def getValueWhere2ConditionAND(cursor,TableName, ValToRead, ConditionColName1, ConditionValue1, ConditionColName2, ConditionValue2):
    '''
    Read the field value in a table where the 'column' equals 'value' corresponding Query = SELECT 'ValToRead' FROM TableName WHERE 'ConditionColName1' = 'ConditionValue1' AND 'ConditionColName2' = 'ConditionValue2' "
    TableName : Table in which execute query
    ValToRead : Field Value to read
    ConditionColName1 : First column name for the condition of the query search
    ConditionValue1 : First value name for the condition of the query search
    ConditionColName2 : Second column name for the condition of the query search
    ConditionValue2 : Second value name for the condition of the query search
    return p_DataRead : values read
    '''
    cursor.execute("SELECT " + ValToRead  + " FROM " + TableName + " WHERE " + ConditionColName1 + " = '" + ConditionValue1 + "' AND " + ConditionColName2 + " = '" + ConditionValue2 + "' ;" )
    p_DataRead = cursor.fetchone()[0]
    # for row in cursor:
    #     p_DataRead=row[0]
    #con.commit()
    return p_DataRead

def getValueWhere3ConditionAND(cursor,TableName, ValToRead,  ConditionColName1, ConditionValue1, ConditionColName2, ConditionValue2, ConditionColName3,  ConditionValue3):
    '''
    Read the field value in a table where the 'column' equals 'value' corresponding Query = SELECT 'ValToRead' FROM TableName WHERE 'ConditionColName1' = 'ConditionValue1' AND 'ConditionColName2' = 'ConditionValue2' " ...
    param TableName : Table in which execute query
    ValToRead : Field Value to read
    ConditionColName1 : First column name for the condition of the query search
    ConditionValue1 : First value name for the condition of the query search
    ConditionColName2 : Second column name for the condition of the query search
    ConditionValue2 : Second value name for the condition of the query search
    ConditionColName3 : Third column name for the condition of the query search
    ConditionValue3 : Third value name for the condition of the query search
    '''
    cursor.execute( "SELECT " + ValToRead  + " FROM " + TableName + " WHERE " + ConditionColName1 + " = '" + ConditionValue1 + "' AND " + ConditionColName2 + " = '" + ConditionValue2 + "' AND " + ConditionColName3 + " = '" + ConditionValue3 + "' ;" )
    # for row in cur:
    #     p_DataRead=row[0]
    p_DataRead = cursor.fetchone()[0]
    #con.commit()
    return p_DataRead 

def rEquipmentStatus(IpAddress): 
    '''
    Read the status of an equipment from its IP Address
    '''
    status =getValueWhere1ConditionAND(cur,"TbEquipment", "status", "Address", IpAddress)
    return status

def rStepperParameter(cursor,PkIdTbBoc,NoMotor, NoParam):
    '''
    Read one stepper parameter
    PkIdTbBoc: Primary key identifier of an axis module Bim2BOC
    NoMotor: number of the motor on the equipment
    NoParam: number(Id) of the parameter to read
    '''
    NoMod  = getSlotNumber(NoMotor)
    NoAxis = getAxisNumber(NoMotor)
    #PkIdTbBoc = readPkModBim2BOC(IdEquipt, NoMod, NoAxis, FlgReadWrite=1) # Read Primary key identifier of an axis module Bim2BOC :  p_PkModBim
    PkIdModuleBIM = getValueWhere2ConditionAND(cursor, "TbBim2BOC_1Axis_R", "IdModule", "PkId", str(PkIdTbBoc), "NumAxis", str(NoAxis))
        
    if NoParam  in listParaStr.values()  : #  str 
        tbToread = "TbParameterSTR"
        p_ReadValue = getValueWhere3ConditionAND(cursor,tbToread, "ValParam", "IdName", str(NoParam), "IdModule", str(PkIdModuleBIM), "NumAxis", str(NoAxis))
        return p_ReadValue    
    elif NoParam in listParaReal.values(): # Real
        tbToread="TbParameterREAL"
        p_ReadValue = getValueWhere3ConditionAND(cursor,tbToread, "ValParam", "IdName", str(NoParam), "IdModule", str(PkIdModuleBIM), "NumAxis", str(NoAxis))
        return p_ReadValue 
    elif  NoParam in listParaInt.values(): # Int 
        tbToread="TbParameterINT"
        p_ReadValue = getValueWhere3ConditionAND(cursor,tbToread, "ValParam", "IdName", str(NoParam), "IdModule", str(PkIdModuleBIM), "NumAxis", str(NoAxis))
        return p_ReadValue 
    else :
        print( 'parameter value not valid')
        return 0

def wStepperParameter(cursor,IdEquipt,NoMotor, NoParam,valParam):
    '''
    write one stepper parameter
    param IdEquipt: Ident of equipment to read
    NoMotor: number of the motor on the equipment
    NoParam: number(Id) of the parameter to read
    '''
    NoMod  = getSlotNumber(NoMotor)
    NoAxis = getAxisNumber(NoMotor)
    PkIdTbBoc = readPkModBim2BOC(cursor,IdEquipt, NoMod, NoAxis, FlgReadWrite=1) # Read Primary key identifier of an axis module Bim2BOC :  p_PkModBim
    PkIdModuleBIM = getValueWhere2ConditionAND( cursor,"TbBim2BOC_1Axis_R", "IdModule", "PkId", str(PkIdTbBoc), "NumAxis", str(NoAxis))
    
    if NoParam  in listParaStr.values()  : #  str 
        tbToread = "TbParameterSTR"
        UPDATE = "UPDATE %s set ValParam ='%s' WHERE IdName= %s and IdModule =%s and NumAxis =%s ;" % (tbToread,valParam,str(NoParam),str(PkIdModuleBIM),str(NoAxis))
        a=cursor.execute(UPDATE)
        con.commit()

    elif NoParam in listParaReal.values():
        tbToread="TbParameterREAL"
        UPDATE = "UPDATE %s set ValParam =%s WHERE IdName= %s and IdModule =%s and NumAxis =%s ; " % (tbToread,valParam,str(NoParam),str(PkIdModuleBIM),str(NoAxis))
        a=cursor.execute(UPDATE)
        con.commit() 
    elif  NoParam in listParaInt.values():
        tbToread="TbParameterINT"
        UPDATE= "UPDATE %s set ValParam =%s WHERE IdName= %s and IdModule =%s and NumAxis =%s ; " % (tbToread,valParam,str(NoParam),str(PkIdModuleBIM),str(NoAxis))
        a=cursor.execute(UPDATE)
        con.commit() 
    else :
        print( 'parameter value is not valid')
        a = 0
        
    return a
def wStepperCmd(cursor,PkIdTbBoc, RegOrder, RegPosition, RegVelocity=1000):
    '''
    Write a command to a stepper axis (BOCM) with a cursor
    cursor  firbird cursor 
    PkIdTbBoc = readPkModBim2BOC(IdEquipt, NoMod, NoAxis, FlgReadWrite=1) 
    CmdRegister: command register to write
    SetpointPosition: Position setpoint
    SetpointVelocity: Velocity setpoint
    IdEquipt = rEquipmentIdNbr(IpAdress)
    NoMod  = getSlotNumber(NoMotor)
    NoAxis = getAxisNumber(NoMotor) 
    '''
    # test si pas de commande en cours 
    if getValueWhere1ConditionAND(cursor,'TBBIM2BOC_1AXIS_W','Cmd','PkId',str(PkIdTbBoc)) == 0  or getValueWhere1ConditionAND(cursor,'TBBIM2BOC_1AXIS_R','StateCmd','PkId',str(PkIdTbBoc)) == (0 or 3 or 4):
        # write parameter cmd
        UPDATE = 'UPDATE %s set RegOrder = %s, RegPosition = %s, RegVelocity = %s WHERE PkId =%s ;' % ('TBBIM2BOC_1AXIS_W',str(RegOrder),str(RegPosition),str(RegVelocity),str(PkIdTbBoc))
        cursor.execute(UPDATE)
        # take write right
        UPDATE = 'UPDATE  %s set cmd=1 WHERE PkId =%s ;' % ('TBBIM2BOC_1AXIS_W',str(PkIdTbBoc)) 
        
        cursor.execute(UPDATE)
        con.commit()
        time.sleep(0.15) # ?? sinon ca marche pas ...
    #  test si commande est terminé cmd=3 ou 4 (erreur ?)
        select = "SELECT " + "StateCmd"  + " FROM " + "TbBim2BOC_1Axis_R" + " WHERE " + "PkId" + " = " + str(PkIdTbBoc) + ";"
        cursor.execute(select )
        cmd = cursor.fetchone()
        
    # liberer le champ cmd =0  
        UPDATE = 'UPDATE  %s set  Cmd = 0 WHERE PkId =%s ;' % ('TBBIM2BOC_1AXIS_W',str(PkIdTbBoc)) # clear commande right
        cursor.execute(UPDATE)
        con.commit()
        time.sleep(0.15)
        
        if cmd == 4:
            return'cmd error'
        else:
            return 'cmd ok'

class MOTORRSAI():
    """
    MOTORRSAI(IpAdrress,NoMotor) 
    class is defined by Ipadress of the rack and axis number 
    """

    def __init__(self, IpAdrress,NoMotor,parent=None):
        self.IpAdress = IpAdrress
        self.NoMotor = NoMotor
        self.IdEquipt = rEquipmentIdNbr(self.IpAdress)
        self.NoMod  = getSlotNumber(self.NoMotor)
        self.NoAxis = getAxisNumber(self.NoMotor)
        
        # each action to database have different cursor 
        self.cur = con.cursor() # def cursor to read postion
        self.curcwd = con.cursor() # def cursor to write cmd
        self.curEtat = con.cursor() # def cursor to read state
        self.cursorRead =con.cursor() # def cursor to read parameter value
        self.cursorWrite=con.cursor() # def cursor to write parameter value

        self.PkIdTbBoc = readPkModBim2BOC(self.cursorRead,self.IdEquipt, self.NoMod, self.NoAxis, FlgReadWrite=1) # Read Primary key identifier of an axis module Bim2BOC :  p_PkModBim
        self._name = rStepperParameter(self.cursorRead,self.PkIdTbBoc,NoMotor,listParaStr['nomAxe'])
        self.update()

    def update(self):
        '''update from the data base')
        '''
        self.name = self.getName()
        self.step = self.getStepValue()
        self.butPlus = self.getButLogPlusValue()
        self.butMoins = self.getButLogMoinsValue()
        self.refName=[]
        for i in range (1,7):
            r = self.getRefName(i)
            self.refName.append(r)
            # time.sleep(0.01)
        self.refValue=[]
        for i in range (1,7):
            rr = self.getRefValue(i)/self.step
            self.refValue.append(rr)
            # time.sleep(0.01)

    def position(self):
        '''
        return motor postion
        '''
        mut.lock()
        con.commit()
        TableName = "TbBim2BOC_1Axis_R"
        ValToRead = "PosAxis"
        ConditionColName = "PkId"
        ConditionValue = str(self.PkIdTbBoc)
        Prepare1Cond= "SELECT " + ValToRead  + " FROM " + TableName + " WHERE " + ConditionColName + " = '" + ConditionValue + "' ;"
        self.cur.execute(Prepare1Cond )      
        posi = self.cur.fetchone()[0]
        mut.unlock()
        return  posi
    
    def getName(self):
        '''
        get motor name
        '''
        mut.lock()
        self._name = rStepperParameter(self.cursorRead,self.PkIdTbBoc,self.NoMotor,listParaStr['nomAxe'])
        mut.unlock()
        return self._name
    
    def setName(self,nom):
        '''
        set motor name
        '''
        valParam = nom
        mut.lock()
        a = wStepperParameter(self.cursorWrite,self.IdEquipt,self.NoMotor, listParaStr['nomAxe'],valParam)
        time.sleep(0.05)
        mut.unlock()

    def getRefName(self,nRef) :
        '''
        set ref n° name
        '''
        mut.lock()
        key = listParaStr['nomRef'+str(nRef)]
        mut.unlock()
        return rStepperParameter(self.cursorRead,self.PkIdTbBoc, self.NoMotor, key)
    
    def setRefName(self,nRef,name) :
        '''
        set ref n° name
        '''
        mut.lock()
        key = listParaStr['nomRef'+str(nRef)]
        a = wStepperParameter(self.cursorWrite,self.IdEquipt, self.NoMotor, key, name)   # to do change to self.PkIdTbBoc?
        mut.unlock()
    
    def getRefValue(self,nRef) :
        '''
        get value of the refereence position nRef
        '''
        mut.lock()
        key = listParaReal['Ref'+str(nRef)+'Val']
        ref = rStepperParameter(self.cursorRead,self.PkIdTbBoc, self.NoMotor, key)
        mut.unlock()
        return ref
    
    def setRefValue(self,nReff,value) :
        '''
        set value of the refereence position nRef
        '''
        key = listParaReal['Ref'+str(nReff)+'Val']
        wStepperParameter(self.cursorWrite,self.IdEquipt, self.NoMotor, key, value) # to do change to self.PkIdTbBoc? change for self.cur? 

    def getStepValue(self):
        '''Valeur de 1 pas dans l'unites
        '''
        mut.lock()
        key = listParaReal['Step'] #1106
        step = rStepperParameter(self.cursorRead,self.PkIdTbBoc, self.NoMotor, key)
        mut.unlock()
        return step 

    def getButLogPlusValue(self):
        key = listParaInt['ButLogPlus'] 
        mut.lock()
        but = rStepperParameter(self.cursorRead,self.PkIdTbBoc, self.NoMotor, key)
        mut.unlock()
        return but 
    
    def setButLogPlusValue(self,butPlus):
        key = listParaInt['ButLogPlus'] 
        wStepperParameter(self.cursorWrite,self.IdEquipt, self.NoMotor, key, butPlus) # to do change to self.PkIdTbBoc?
    
    def getButLogMoinsValue(self):
        key = listParaInt['ButLogNeg'] 
        mut.lock()
        b = rStepperParameter(self.cursorRead,self.PkIdTbBoc, self.NoMotor, key)
        mut.unlock()
        return b
    
    def setButLogMoinsValue(self,butMoins):
        key = listParaInt['ButLogNeg'] 
        wStepperParameter(self.cursorWrite,self.IdEquipt, self.NoMotor, key, butMoins) # to do change to self.PkIdTbBoc?

    def rmove(self,posrelatif,vitesse=1000):
        '''
        relative move of NoMotor of IpAdress
        posrelatif = position to move in step
        #to do faire self.curcwd
        '''
        RegOrder = 3
        posrelatif = int(posrelatif)
        print(self._name,'relative move of ',posrelatif,' step')
        mut.lock()
        a = wStepperCmd(cursor=self.curcwd, PkIdTbBoc=self.PkIdTbBoc, RegOrder=RegOrder, RegPosition=posrelatif,RegVelocity=vitesse)  
        mut.unlock()

    def move(self,pos,vitesse=1000):
        '''absolue move of NoMotor  of IpAdress
        pos = position to move in step
        '''
        mut.lock()
        RegOrder = 2
        a = wStepperCmd(cursor =self.curcwd, PkIdTbBoc=self.PkIdTbBoc,RegOrder=RegOrder, RegPosition=pos,RegVelocity=vitesse)  
        print(self._name, 'absolue move of ',pos,' step')
        mut.unlock()

    def setzero(self):
        """
        setzero(self.moteurname):Set Zero
        """
        mut.lock()
        RegOrder=10  #  commande pour zero le moteur 
        a=wStepperCmd(cursor =self.curcwd,PkIdTbBoc=self.PkIdTbBoc, RegOrder=RegOrder, RegPosition=0,RegVelocity=0) 
        mut.unlock()

    def stopMotor(self): # stop le moteur motor
        """ 
        stopMotor(motor): stop le moteur motor
        """
        mut.lock()
        RegOrder = 4
        a = wStepperCmd(cursor =self.curcwd,PkIdTbBoc=self.PkIdTbBoc, RegOrder=RegOrder, RegPosition=0,RegVelocity=0)  
        mut.unlock()

    def etatMotor(self):
        '''
        read status of the motor
        '''
        mut.lock()
        TbToRead = "TbBim2Boc_1Axis_R"
        # PkIdTbBoc = readPkModBim2BOC(self.IdEquipt, self.NoMod, self.NoAxis, FlgReadWrite=1) # Read Primary key identifier of an axis module Bim2BOC :  p_PkModBim 
        #a =str( hex(getValueWhere1ConditionAND(TbToRead , "StatusAxis", "PkId", str(self.PkIdTbBoc))))
        # ecire direct la fonction 
        Prepare1Cond = "SELECT " + "StatusAxis"  + " FROM " + TbToRead + " WHERE " + "PkId" + " = " + str(self.PkIdTbBoc) + ";"
        self.curEtat.execute(Prepare1Cond )
        a=self.curEtat.fetchone()[0]
        a=str(hex(a))
        con.commit()
        time.sleep(0.1)
        mut.unlock()
        if a == '0x2030' or a == '0x30' or a == '0x20': 
            etat='mvt'
        elif a=='0x2012' or a=='0x12' or a=='0x92' or a=='0x2082' or a== '0x2002' or a== '0x2': 
            etat='FDC-'
        elif a=='0x2011' or a=='0x11' or a=='0x91' or a=='0x2081' or a== '0x2001' or a =='0x1': 
            etat='FDC+'
        elif a=='0x2010' or a=='0x10' : 
            etat='ok'
        elif a=='0x2090' or a=='0x90' or a=='0x4000': 
            etat='ok'    
        elif a=='0x2090' or a=='0x80'or a=='0x0': 
            etat='ok'
        elif a=='0x890' or a == '0x2890' or a == '0x880' or a=='0x8c0': 
            etat='Power off'
        else:
            etat=str(a)
        
        return etat

    def getEquipementName(self):
        '''
        return the name of the equipement of which the motor is connected
        '''
        return nameEquipment(self.IpAdress)    


if __name__ == '__main__':
    
    closeConnection()

