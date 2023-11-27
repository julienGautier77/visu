from PyQt6 import QtWidgets, QtCore
import sys
from PyQt6.QtWidgets import QApplication
import pathlib
from PyQt6.QtGui import QIcon
import qdarkstyle
import os
import pyqtgraph as pg
import numpy as np

class InputE(QtWidgets.QWidget):
    closeEventVar = QtCore.pyqtSignal(bool)

    def __init__(self,parent=None):

        super().__init__()

        p = pathlib.Path(__file__)
        sepa = os.sep
        self.icon = str(p.parent) + sepa+'icons' + sepa
        self.isWinOpen = False
        self.setStyleSheet(qdarkstyle.load_stylesheet(qt_api='pyqt6'))
        self.defvalfile = QtCore.QSettings(str(pathlib.Path(__file__).parent / 'default_values.ini'), QtCore.QSettings.Format.IniFormat)
        self.buttonSelected = False
        self.buttonSelectedBack = False
        self.hminBg = 0
        self.hmaxBg = 1
        self.setup()
        self.actionButton()
        self.setWindowTitle('Spectro input')
        self.setWindowIcon(QIcon(self.icon+'LOA.png'))
        self.parent=parent

    def setup(self):
        # definition of all button   
        
        layout = QtWidgets.QVBoxLayout(self)
        
        # Create layout for dimension with four input entries
        dimension_layout = QtWidgets.QHBoxLayout()

        dimension_layout.addWidget(QtWidgets.QLabel('Dimensions :'))
        
        self.wmin = QtWidgets.QSpinBox()
        #self.wmin.setPlaceholderText('Left limit')
        self.wmin.setMaximum(10000)
        
        self.wmin.setValue(int(self.defvalfile.value("/"+"/wmin")))
        dimension_layout.addWidget(self.wmin)

        self.wmax = QtWidgets.QSpinBox()
        #self.wmax.setPlaceholderText('Right limit')
        self.wmax.setMaximum(10000)
        self.wmax.setValue(int(self.defvalfile.value("/"+"/wmax")))
        dimension_layout.addWidget(self.wmax)

        self.hmin = QtWidgets.QSpinBox()
        self.hmin.setMaximum(10000)
        self.hmin.setValue(int(self.defvalfile.value("/"+"/hmin")))
        dimension_layout.addWidget(self.hmin)

        self.hmax = QtWidgets.QSpinBox()
        self.hmax.setMaximum(10000)
        self.hmax.setValue(int(self.defvalfile.value("/"+"/hmax")))
        dimension_layout.addWidget(self.hmax)
        
        self.selectButton=QtWidgets.QToolButton()
        self.selectButton.setText('Select')
        dimension_layout.addWidget(self.selectButton)

        layout.addLayout(dimension_layout)
        ppmm_layout = QtWidgets.QHBoxLayout()
        ppmm_layout.addWidget(QtWidgets.QLabel('Pixel per millimeter :'))
        self.ppmm = QtWidgets.QDoubleSpinBox()
        self.ppmm.setMaximum(10000)
        ppmm_layout.addWidget(self.ppmm)
        self.ppmm.setValue(float(self.defvalfile.value("/"+"/ppmm")))
        layout.addLayout(ppmm_layout)

        # Create layout for pixel position of high energy edge s0
        pps0_layout = QtWidgets.QHBoxLayout()
        pps0_layout.addWidget(QtWidgets.QLabel('Pixel position of zero Lanex :'))
        self.pps0 = QtWidgets.QDoubleSpinBox()
        pps0_layout.addWidget(self.pps0)
        self.pps0.setMaximum(10000)
        self.pps0.setValue(float(self.defvalfile.value("/"+"/pps0")))
        layout.addLayout(pps0_layout)

        # Create layout for source screen distance
        ssd_layout = QtWidgets.QHBoxLayout()
        ssd_layout.addWidget(QtWidgets.QLabel('Source screen distance :'))
        self.ssd = QtWidgets.QDoubleSpinBox()
        self.ssd.setMaximum(10000)
        ssd_layout.addWidget(self.ssd)
        self.ssd.setValue(float(self.defvalfile.value("/"+"/ssd")))
        layout.addLayout(ssd_layout)
        
        # Create layout for median filter strength with increase button
        medfilt_layout = QtWidgets.QHBoxLayout()
        medfilt_layout.addWidget(QtWidgets.QLabel('Median Filter Strength :'))
        self.medfilt = QtWidgets.QSpinBox()
        self.medfilt.setMaximum(100)
        medfilt_layout.addWidget(self.medfilt)
        self.medfilt.setValue((int(self.defvalfile.value("/"+"/medfilt"))))
        layout.addLayout(medfilt_layout)

        # Create layout for number of energy points
        npoints_layout = QtWidgets.QHBoxLayout()
        npoints_layout.addWidget(QtWidgets.QLabel('Number of energy points :'))
        self.npoints = QtWidgets.QDoubleSpinBox()
        self.npoints.setMaximum(10000)
        npoints_layout.addWidget(self.npoints)
        self.npoints.setValue((int(self.defvalfile.value("/"+"/npoints"))))
        layout.addLayout(npoints_layout)
        count_layout = QtWidgets.QHBoxLayout()
        count_layout.addWidget(QtWidgets.QLabel('Charge/pixel :'))
        self.count = QtWidgets.QDoubleSpinBox()
        self.count.setMaximum(10000)
        count_layout.addWidget(self.count)
        self.count.setValue((int(self.defvalfile.value("/"+"/count"))))
        layout.addLayout(count_layout)

        # Create Select dsdE file button
        self.select_dsde_button = QtWidgets.QPushButton('Select dsdE file', self)
        layout.addWidget(self.select_dsde_button)

        # Create a label to display the selected dsdE file name
        self.selected_dsde_label = QtWidgets.QLineEdit(self)
        layout.addWidget(self.selected_dsde_label)
        self.dsde_name = (str(self.defvalfile.value("/"+"/dsde_name")))
        self.selected_dsde_label.setText(self.dsde_name)
        # Read ds_dE data from file
        try:
         self.slist, self.elist, self.dsdelist,self.thetalist,self.dlist = self.readfile(self.dsde_name)
        except:
            self.slist, self.elist, self.dsdelist,self.thetalist,self.dlist=0,0,0,0,0
            print('error file calibration' )

        # Create label to display the warning message if no file has been selected
        self.warning_label = QtWidgets.QLabel('', self)
        self.warning_label.setStyleSheet('color: red')
        layout.addWidget(self.warning_label)
        
        self.backgroudButton = QtWidgets.QPushButton('Select ROI background', self)
        layout.addWidget(self.backgroudButton)

        self.setLayout(layout)
        # rect for Background
        self.rectSelectBack = pg.RectROI([100, 10], [4*100, 15],
                                            pen='r')

    def actionButton(self):
        self.wmin.editingFinished.connect(self.set_default)
        self.wmax.editingFinished.connect(self.set_default)
        self.hmin.editingFinished.connect(self.set_default)
        self.hmax.editingFinished.connect(self.set_default)
        self.medfilt.editingFinished.connect(self.set_default)
        self.npoints.editingFinished.connect(self.set_default)
        self.ppmm.editingFinished.connect(self.set_default)
        self.pps0.editingFinished.connect(self.set_default)
        self.ssd.editingFinished.connect(self.set_default)
        self.count.editingFinished.connect(self.set_default)
        self.selected_dsde_label.textChanged.connect(self.dsdseChange)
        self.select_dsde_button.clicked.connect(self.select_dsde)
        self.backgroudButton.clicked.connect(self.selectBackground)
        self.rectSelectBack.sigRegionChangeFinished.connect(self.changeDimbg)

    def select_dsde(self):
        # Pick dsdE file 
        dsde_dialog = QtWidgets.QFileDialog()
        self.dsde_name, _ = dsde_dialog.getOpenFileName()
        
        # Update the label text to display the selected file name
        if self.dsde_name:
            self.selected_dsde_label.setText(str(self.dsde_name))
    
    def set_default(self):
        # save values in the default ini file
        self.defvalfile.setValue("/"+"/wmin",self.wmin.value())
        self.defvalfile.setValue("/"+"/wmax",self.wmax.value())
        self.defvalfile.setValue("/"+"/hmin",self.hmin.value())
        self.defvalfile.setValue("/"+"/hmax",self.hmax.value())
        self.defvalfile.setValue("/"+"/medfilt",self.medfilt.value())
        self.defvalfile.setValue("/"+"/npoints",self.npoints.value())
        self.defvalfile.setValue("/"+"/ppmm",self.ppmm.value())
        self.defvalfile.setValue("/"+"/pps0",self.pps0.value())
        self.defvalfile.setValue("/"+"/ssd",self.ssd.value())
        self.defvalfile.setValue("/"+"/count",self.count.value())

    def dsdseChange(self):
        self.defvalfile.setValue("/"+"/dsde_name",self.dsde_name)
        # Read ds_dE data from file
        self.slist, self.elist, self.dsdelist,self.thetalist,self.dlist = self.readfile(self.dsde_name)
        
    def selectBackground(self):
        if self.parent is not None:
            if self.buttonSelectedBack is False: 
                self.rectSelectBack.setPos([self.parent.energy_min,0])
                self.rectSelectBack.setSize([self.parent.energy_max-self.parent.energy_min,3])
                self.parent.p1.addItem(self.rectSelectBack)
                self.buttonSelectedBack = True
                self.parent.checkBoxBg.setChecked(True)
            else:
                self.buttonSelectedBack = False
                self.parent.p1.removeItem(self.rectSelectBack)
            
    def changeDimbg(self):
        self.wminBg = 0 #  (int(self.rectSelectSpectro.pos()[0]))
        self.wmaxBg = self.parent.dimx #  (int(self.rectSelectSpectro.pos()[0] + self.rectSelectSpectro.size()[0] ))
        self.hminBg = int((self.rectSelectBack.pos()[1]-self.parent.transY*self.parent.scaleY)/self.parent.scaleY)
        self.hmaxBg = int((self.rectSelectBack.size()[1]+self.rectSelectBack.pos()[1] -  self.parent.transY*self.parent.scaleY)/self.parent.scaleY)

        if self.parent is not None:
            self.parent.SpectroChanged()

    def readfile(self,filename):
        elist,dsdelist,slist,thetalist,dlist=np.loadtxt(str(filename),unpack=True)
        # elist list de energie
        # slist list des postion sur le lanex
        # dsdelist derive position/energie
        # thetalist liste angle sur lannex
        # dlist distance parcourue par les electrons
        
        if elist[1] < elist[0]:
            slist = slist[::-1] # reversed slist
            elist = elist[::-1] # reversed elist
            dsdelist = dsdelist[::-1] # reversed elist 
            thetalist = thetalist[::-1]
            dlist =dlist[::-1]
        
        return slist, elist,dsdelist,thetalist,dlist

    def closeEvent(self, event):
        """ when closing the window
        """
        self.isWinOpen = False
        self.set_default()
        if self.parent is not None :
            if self.parent.parent is not None:
            # closing rectangular selection of size on visu 
                if self.buttonSelected is True: 
                    self.parent.parent.p1.removeItem(self.parent.rectSelectSpectro)
        if self.parent is not None: # supress back roi on spectrowindow
            if self.buttonSelectedBack is True:
                self.parent.p1.removeItem(self.rectSelectBack)

        self.closeEventVar.emit(True)
        
if __name__ == "__main__":
    appli = QApplication(sys.argv)
    appli.setStyleSheet(qdarkstyle.load_stylesheet(qt_api='pyqt6'))
    e = InputE()
    e.show()
    appli.exec_()