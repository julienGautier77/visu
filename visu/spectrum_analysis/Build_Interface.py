#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on 2025/12/16
@author: Aline Vernier
Build Spectrometer Interface - GUI only
"""
from PyQt6.QtWidgets import QApplication, QVBoxLayout, QWidget, QHBoxLayout, QGridLayout
from PyQt6.QtWidgets import (QLabel, QMainWindow, QStatusBar, QComboBox,
                             QCheckBox, QDoubleSpinBox,  QPushButton, QLineEdit)
from PyQt6.QtGui import QIcon, QFont
from PyQt6.QtCore import Qt
import sys
import pyqtgraph as pg
import qdarkstyle
import os
import pathlib

sepa = os.sep


class Spectrometer_Interface(QMainWindow):

    def __init__(self):
        super().__init__()
        p = pathlib.Path(__file__)
        self.icon = str(p.parent.parent) + sepa + 'icons' + sepa
        self.setup()
        self._cache_setup()
        self.action_button()

    def setup(self):
        #####################################################################
        #                   Window setup
        #####################################################################
        self.isWinOpen = False
        self.setWindowTitle('Electrons spectrometer')
        self.setWindowIcon(QIcon(self.icon + 'LOA.png'))
        self.setStyleSheet(qdarkstyle.load_stylesheet(qt_api='pyqt6'))
        self.setWindowIcon(QIcon('./icons/LOA.png'))
        self.setGeometry(100, 30, 1200, 750)

        self.toolBar = self.addToolBar('tools')
        self.toolBar.setMovable(False)
        self.statusBar = QStatusBar()
        self.setStatusBar(self.statusBar)

        self.fileMenu = self.menuBar().addMenu('&File')

        #####################################################################
        #                   Global layout and geometry
        #####################################################################

        # Toggle design
        TogOff = self.icon + 'Toggle_Off.png'
        TogOn = self.icon + 'Toggle_On.png'
        TogOff = pathlib.Path(TogOff)
        TogOff = pathlib.PurePosixPath(TogOff)
        TogOn = pathlib.Path(TogOn)
        TogOn = pathlib.PurePosixPath(TogOn)
        self.setStyleSheet("QCheckBox::indicator{width: 30px;height: 30px;}"
                           "QCheckBox::indicator:unchecked { image : url(%s);}"
                           "QCheckBox::indicator:checked { image:  url(%s);}"
                           "QCheckBox{font :10pt;}" % (TogOff, TogOn))

        # Horizontal box with LHS graphs, and RHS controls and indicators
        self.hbox = QHBoxLayout()
        MainWidget = QWidget()
        MainWidget.setLayout(self.hbox)
        b0 = QLabel('')
        b1 = QLabel('')
        self.setCentralWidget(MainWidget)

        # LHS vertical box with stacked graphs
        self.vbox1 = QVBoxLayout()
        self.hbox.addLayout(self.vbox1)

        # RHS vertical box with controls and indicators
        self.vbox2 = QVBoxLayout()
        self.vbox2widget = QWidget()
        self.vbox2widget.setLayout(self.vbox2)
        self.vbox2widget.setFixedWidth(350)
        self.hbox.addWidget(self.vbox2widget)

        # Title
        title_label = QLabel('Low energy spectrum')
        title_label.setFont(QFont('Arial', 14))
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.vbox2.addWidget(title_label)

        #####################################################################
        #       Fill layout with graphs, controls and indicators
        #####################################################################

        ######################
        #       Graphs
        ######################
        # 2D plot (image histogram) in LHS vbox
        self.winImage = pg.GraphicsLayoutWidget()
        self.vbox1.addWidget(self.winImage)

        # Add plot in column 0
        self.spectrum_2D_image = self.winImage.addPlot(row=0, col=0)
        self.image_histogram = pg.ImageItem()
        self.spectrum_2D_image.addItem(self.image_histogram)

        # Setup histogram LUT
        self.hist = pg.HistogramLUTItem()
        self.hist.setImageItem(self.image_histogram)
        self.hist.gradient.loadPreset('flame')

        # Hide the actual plot region
        self.hist.region.setVisible(False)  # Hides the draggable region
        self.hist.vb.setVisible(False)  # Hides the ViewBox containing histogram
        self.winImage.addItem(self.hist)

        # Setup 1D plot (dN/dE vs. E)
        self.graph_widget = pg.GraphicsLayoutWidget()
        self.vbox1.addWidget(self.graph_widget)

        self.dnde_image = self.graph_widget.addPlot()
        self.dnde_image.setContentsMargins(10, 10, 10, 10)

        ######################
        #    Lock Controls
        ######################
        # Controls and indicators, labels
        grid_layout_enable_controls = QGridLayout()
        lock_controls = QLabel('Lock controls')
        self.locked_unlocked = QLabel('Unlocked')
        self.enable_controls = QCheckBox()
        self.enable_controls.setChecked(True)
        grid_layout_enable_controls.addWidget(lock_controls, 0, 0)
        grid_layout_enable_controls.addWidget(self.enable_controls, 0, 1)
        grid_layout_enable_controls.addWidget(self.locked_unlocked, 0, 2)
        self.vbox2.addLayout(grid_layout_enable_controls)
        self.vbox2.addStretch(1)

        ######################
        # E, ds/dE, s config
        ######################

        calibration_label = QLabel('Calibration')
        calibration_label.setFont(QFont('Arial', 11))
        calibration_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.vbox2.addWidget(calibration_label)


        grid_layout_config = QGridLayout()
        self.config_path_button = QPushButton('Path : ')
        self.config_path_button.setFixedWidth(50)
        self.config_path_box = QLineEdit('spectrum analysis')
        self.config_path_box.setMaximumHeight(60)
        grid_layout_config.addWidget(self.config_path_button, 0, 0)
        grid_layout_config.addWidget(self.config_path_box, 0, 1)
        self.vbox2.addLayout(grid_layout_config)

        ######################
        # Calibration layout
        ######################

        grid_layout_calib = QGridLayout()
        flip_image_label = QLabel('s-axis R to L')

        self.flip_image = QCheckBox()
        self.flip_image.setChecked(True)

        lanex_offset_label = QLabel('Lanex Offset (+ to low E)')
        self.lanex_offset_mm_ctl = Numeric_IO(min=-100, max=100, incr=0.1, value=0, enabled=True)

        px_per_mm_label = QLabel('px/mm')
        self.px_per_mm_ctl = Numeric_IO(min=0.001, max=1000, incr=1, value=20.408, enabled=True)

        mrad_per_px_label = QLabel('mrad/px')
        self.mrad_per_px_ctl = Numeric_IO(min=1e-6, max=1, incr=0.1, value=0.1, enabled=True)

        pC_per_count_label = QLabel('pC/count ×10<sup>-6</sup>')
        self.pC_per_count_ctl = Numeric_IO(min=0.001, max=1000, incr=0.1, value=4.33, enabled=True)

        reference_label = QLabel('Ref. Method')
        self.reference_method = QComboBox()
        self.reference_method.addItem('Zero')
        self.reference_method.addItem('RefPoint')

        self.reference_pts_label = QLabel('(x, y): (px, px)')
        self.refpoint_x_or_energy = Numeric_IO(min=0, max=10000, incr=1, value=1953, enabled=True)
        self.refpoint_y_or_s = Numeric_IO(min=0, max=10000, incr=1, value=650, enabled=True)


        grid_layout_calib.addWidget(flip_image_label, 0, 0)
        grid_layout_calib.addWidget(self.flip_image, 0, 2)
        grid_layout_calib.addWidget(lanex_offset_label, 1, 0)
        grid_layout_calib.addWidget(self.lanex_offset_mm_ctl, 1, 2)
        grid_layout_calib.addWidget(px_per_mm_label, 2, 0)
        grid_layout_calib.addWidget(self.px_per_mm_ctl, 2, 2)
        grid_layout_calib.addWidget(mrad_per_px_label, 3, 0)
        grid_layout_calib.addWidget(self.mrad_per_px_ctl, 3, 2)
        grid_layout_calib.addWidget(reference_label, 4, 0)
        grid_layout_calib.addWidget(self.reference_method, 4, 2)
        grid_layout_calib.addWidget(self.reference_pts_label, 5, 0)
        grid_layout_calib.addWidget(self.refpoint_x_or_energy, 5, 1)
        grid_layout_calib.addWidget(self.refpoint_y_or_s, 5, 2)
        grid_layout_calib.addWidget(pC_per_count_label, 6, 0)
        grid_layout_calib.addWidget(self.pC_per_count_ctl, 6, 2)
        self.vbox2.addLayout(grid_layout_calib)

        self.vbox2.addStretch(1)

        ######################
        #   Post-processing
        ######################

        postproc_label = QLabel('Post-Processing')
        postproc_label.setFont(QFont('Arial', 11))
        postproc_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.vbox2.addWidget(postproc_label)

        cutoff_energies_label = QLabel('Cutoff energies (MeV)')
        self.min_cutoff_energy_ctl = Numeric_IO(min=0, max=10000, incr=1, value=10, enabled=True)
        self.max_cutoff_energy_ctl = Numeric_IO(min=0, max=10000, incr=1, value=150, enabled=True)

        integration_label = QLabel('Integrated rows (mrad)')
        self.min_int_mrad_ctl = Numeric_IO(min=-5000, max=5000, incr=1, value=0)
        self.max_int_mrad_ctl = Numeric_IO(min=-5000, max=5000, incr=1, value=15)

        background_label = QLabel('Background rows (mrad)')
        self.min_bkg_mrad_ctl = Numeric_IO(min=-5000, max=10000, incr=1, value=-40)
        self.max_bkg_mrad_ctl = Numeric_IO(min=-5000, max=10000, incr=1, value=-35)

        energy_resolution_label = QLabel('Energy resolution (MeV)')
        self.energy_resolution_ctl = Numeric_IO(min=0.1, max=10, incr=0.5, value=0.5, enabled=True)

        mean_energy_label = QLabel('Mean energy (MeV)')
        self.mean_energy_ind = Numeric_IO(enabled=False)

        stdev_energy_label = QLabel('Energy Std Dev (MeV)')
        self.stdev_energy_ind = Numeric_IO(enabled=False)

        charge_label = QLabel('Estimated charge (pC)')
        self.charge_ind = Numeric_IO(enabled=False)

        post_proc_layout = QGridLayout()
        post_proc_layout.addWidget(QLabel(), 1, 2)
        post_proc_layout.addWidget(cutoff_energies_label, 3, 0)
        post_proc_layout.addWidget(self.min_cutoff_energy_ctl, 3, 2)
        post_proc_layout.addWidget(self.max_cutoff_energy_ctl, 3, 3)

        post_proc_layout.addWidget(integration_label, 4, 0)
        post_proc_layout.addWidget(self.min_int_mrad_ctl, 4, 2)
        post_proc_layout.addWidget(self.max_int_mrad_ctl, 4, 3)

        post_proc_layout.addWidget(background_label, 5, 0)
        post_proc_layout.addWidget(self.min_bkg_mrad_ctl, 5, 2)
        post_proc_layout.addWidget(self.max_bkg_mrad_ctl, 5, 3)

        post_proc_layout.addWidget(energy_resolution_label, 6, 0)
        post_proc_layout.addWidget(self.energy_resolution_ctl, 6, 3)
        post_proc_layout.addWidget(mean_energy_label, 7, 0)
        post_proc_layout.addWidget(self.mean_energy_ind, 7, 3)
        post_proc_layout.addWidget(stdev_energy_label, 8, 0)
        post_proc_layout.addWidget(self.stdev_energy_ind, 8, 3)
        post_proc_layout.addWidget(charge_label, 9, 0)
        post_proc_layout.addWidget(self.charge_ind, 9, 3)
        self.vbox2.addLayout(post_proc_layout)

        self.vbox2.addStretch(1)

        ######################
        #  Interface comfort
        ######################
        self.clear_graph_ctl = QPushButton(text="Clear Graph")
        interface_comfort_layout = QGridLayout()
        interface_comfort_layout.addWidget(self.clear_graph_ctl, 0, 1)
        self.vbox2.addLayout(interface_comfort_layout)

        #####################################################################
        #                       Interface actions
        #####################################################################
    def _cache_setup(self):
        self._bounds_cache = None
    def action_button(self) -> None:
        self.min_cutoff_energy_ctl.valueChanged.connect(self.change_energy_bounds)
        self.max_cutoff_energy_ctl.valueChanged.connect(self.change_energy_bounds)
        self.lanex_offset_mm_ctl.valueChanged.connect(self.change_lanex_offset_mm)
        self.enable_controls.stateChanged.connect(self.enable_disable_controls)
        self.flip_image.stateChanged.connect(self.clear_graph)
        self.reference_method.currentTextChanged.connect(self.update_refpoint)
        self.min_int_mrad_ctl.valueChanged.connect(self.clear_bounds_cache)
        self.max_int_mrad_ctl.valueChanged.connect(self.clear_bounds_cache)
        self.min_bkg_mrad_ctl.valueChanged.connect(self.clear_bounds_cache)
        self.max_bkg_mrad_ctl.valueChanged.connect(self.clear_bounds_cache)
        self.clear_graph_ctl.clicked.connect(self.clear_graph)

    def clear_bounds_cache(self):
        self._bounds_cache = None
    def integration_bounds_dict(self) -> dict:
        if self._bounds_cache is None:
            px_bound = lambda value: round(value/self.mrad_per_px_ctl.value()+self.image_dimensions[0]/2)
            min_int_px = px_bound(self.min_int_mrad_ctl.value())
            max_int_px = px_bound(self.max_int_mrad_ctl.value())
            min_bkg_px = px_bound(self.min_bkg_mrad_ctl.value())
            max_bkg_px = px_bound(self.max_bkg_mrad_ctl.value())
            self._bounds_cache = dict({('bkg', (min_bkg_px, max_bkg_px)), ('signal', (min_int_px, max_int_px))})
        return self._bounds_cache



    def update_refpoint(self) -> None:
        if self.reference_method.currentText() == "Zero":
            self.reference_pts_label.setText('(x, y): (px, px)')
        else:
            self.reference_pts_label.setText('(E, s): (MeV, mm)')
        self.clear_graph()
        self.load_calib()
        self.graph_setup()

    def clear_graph(self) -> None:
        self.dnde_image.clear()


    def enable_disable_controls(self):
        '''
        Enable or disable elements on interface
        :return:
        '''
        if self.enable_controls.isChecked():
            self.locked_unlocked.setText('Unlocked')
        else:
            self.locked_unlocked.setText('Locked')

        self.min_cutoff_energy_ctl.setEnabled(self.enable_controls.isChecked())
        self.max_cutoff_energy_ctl.setEnabled(self.enable_controls.isChecked())
        self.flip_image.setEnabled(self.enable_controls.isChecked())
        self.lanex_offset_mm_ctl.setEnabled(self.enable_controls.isChecked())
        self.config_path_button.setEnabled(self.enable_controls.isChecked())
        self.config_path_box.setEnabled(self.enable_controls.isChecked())
        self.px_per_mm_ctl.setEnabled(self.enable_controls.isChecked())
        self.mrad_per_px_ctl.setEnabled(self.enable_controls.isChecked())
        self.pC_per_count_ctl.setEnabled(self.enable_controls.isChecked())
        self.reference_method.setEnabled(self.enable_controls.isChecked())
        self.energy_resolution_ctl.setEnabled(self.enable_controls.isChecked())
        self.refpoint_x_or_energy.setEnabled(self.enable_controls.isChecked())
        self.refpoint_y_or_s.setEnabled(self.enable_controls.isChecked())
        self.min_int_mrad_ctl.setEnabled((self.enable_controls.isChecked()))
        self.max_int_mrad_ctl.setEnabled((self.enable_controls.isChecked()))
        self.min_bkg_mrad_ctl.setEnabled((self.enable_controls.isChecked()))
        self.max_bkg_mrad_ctl.setEnabled((self.enable_controls.isChecked()))

    def change_energy_bounds(self) -> None:
        '''
        Change energy bouds for spectrum statistics and integration
        :return: None
        '''
        self.min_cutoff_energy = self.min_cutoff_energy_ctl.value()
        self.max_cutoff_energy = self.max_cutoff_energy_ctl.value()


    def change_lanex_offset_mm(self) -> None:
        '''
        Change offset with respect to zero or reference point (manual offset or motorized)
        :return: None
        '''
        self.lanex_offset_mm = self.lanex_offset_mm_ctl.value()
        self.clear_graph()
        self.load_calib()
        self.graph_setup()

class Numeric_IO(QDoubleSpinBox):
    def __init__(self, min:float=0, max: float=100, incr: float=1,
                 value: float=1, enabled: bool=True):
        super().__init__()
        self.setMinimum(min)
        self.setMaximum(max)
        self.setSingleStep(incr)
        self.setEnabled(enabled)
        self.setFixedWidth(80)
        self.setValue(value)


if __name__ == "__main__":

    appli = QApplication(sys.argv)
    appli.setStyleSheet(qdarkstyle.load_stylesheet(qt_api='pyqt6'))
    e=Spectrometer_Interface()
    e.show()
    appli.exec_()
