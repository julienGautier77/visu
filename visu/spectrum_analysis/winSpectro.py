#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on 2025/12/23
@author: Aline Vernier
Spectrum deconvolution + make data available for diagServ
"""
from PyQt6.QtWidgets import QApplication
from PyQt6 import QtCore
import sys
import numpy as np
import qdarkstyle
import os
import pathlib

from visu.spectrum_analysis import Deconvolve_Spectrum as Deconvolve
from visu.spectrum_analysis import Spectrum_Features
from visu.spectrum_analysis import Build_Interface


sys.path.insert(1, '')
sepa = os.sep

class WINSPECTRO(Build_Interface.Spectrometer_Interface):
    signalSpectroDict = QtCore.pyqtSignal(object)

    def __init__(self, parent=None, file=None, conf=None, name='VISU', **kwds):
        '''
        class WINSPECTRO inherits interface from Build_Interface.Spectrometer_Interface
        :param parent:
        :param file:
        :param conf:
        :param name:
        :param kwds:
        '''
        
        super().__init__()
        self.name = name
        self.parent = parent
        p = pathlib.Path(__file__)
        self.icon = str(p.parent) + sepa + 'icons' + sepa
        self.data_dict = {}

        # (Main window setup from parent class)

        # Load calibration data
        self.load_calib()
        self.graph_setup()
        self.signal_setup()


    #####################################################################
    #                  Setup calibration for deconvolution
    #####################################################################

    def load_calib(self):
        # Load calibration for spectrum deconvolution
        p = pathlib.Path(__file__)
        self.deconv_calib = str(p.parent) + sepa
        self.calibration_data = Deconvolve.CalibrationData(cal_path=self.deconv_calib + 'dsdE_default.txt')
        self.calibration_data_json = None
        # Create initialization object for spectrum deconvolution
        initImage = Deconvolve.spectrum_image(im_path=self.deconv_calib +
                                                      'calib_image.TIFF',
                                              revert=True)
        self.deconvolved_spectrum = Deconvolve.DeconvolvedSpectrum(initImage, self.calibration_data,
                                                                   self.energy_resolution_ctl.value(),
                                                                   self.px_per_mm_ctl.value(),
                                                                   self.mrad_per_px_ctl.value(),
                                                                   self.reference_method.currentText(),
                                                                   (self.refpoint_x_or_energy.value(),
                                                                    self.refpoint_y_or_s.value()),
                                                                   self.pC_per_count_ctl.value()*1e-6,
                                                                   offset=self.lanex_offset_mm_ctl.value())
        self.image_dimensions = self.deconvolved_spectrum.image_dimensions

    def graph_setup(self):

        self.spectrum_2D_image.setLabel('bottom', 'Energy (MeV)')
        self.spectrum_2D_image.setLabel('left', 'mrad ')

        self.image_histogram.setImage(self.deconvolved_spectrum.image.T, autoLevels=True, autoDownsample=True)
        self.image_histogram.setRect(
            self.deconvolved_spectrum.energy[0],  # x origin
            self.deconvolved_spectrum.angle[0],  # y origin
            self.deconvolved_spectrum.energy[-1] - self.deconvolved_spectrum.energy[0],  # width
            self.deconvolved_spectrum.angle[-1] - self.deconvolved_spectrum.angle[0])    # height

        self.dnde_image.setLabel('bottom', 'Energy')
        self.dnde_image.setLabel('left', 'dN/dE (pC/MeV)')


    #####################################################################
    #                       Setup DiagServ signal
    #####################################################################

    def signal_setup(self):

        if self.parent is not None:
            # if signal emit in another thread (see visual)
            self.parent.signalSpectro.connect(self.Display)
            #self.parent.signalSpectroList.connect(self.spectro_dict)

    #####################################################################
    #       Display and generate data for DiagServ (dictionary)
    #####################################################################
    def Display(self, data):

        # Deconvolve and display 2D data
        if self.flip_image.isChecked():
            self.deconvolved_spectrum.deconvolve_data(np.flip(data.T, axis=1))
        else:
            self.deconvolved_spectrum.deconvolve_data(data.T)
        self.image_histogram.setImage(self.deconvolved_spectrum.image.T, autoLevels=True, autoDownsample=True)

        # Integrate over angle and show graph
        self.deconvolved_spectrum.integrate_spectrum(self.integration_bounds_dict()['signal'],
                                                     self.integration_bounds_dict()['bkg'])
        self.dnde_image.plot(self.deconvolved_spectrum.energy, self.deconvolved_spectrum.integrated_spectrum)

    def spectro_dict(self, temp_dataArray):
        # Creation of dictionary to pass to diagServ ; cut energy from interface to remove noise
        self.spectro_data_dict = Spectrum_Features.build_dict(self.deconvolved_spectrum.energy,
                                                              self.deconvolved_spectrum.integrated_spectrum,
                                                              temp_dataArray[1],
                                                              energy_bounds=[self.min_cutoff_energy_ctl.value(),
                                                                             self.max_cutoff_energy_ctl.value()])
        # Display values on interface
        self.mean_energy_ind.setValue(self.spectro_data_dict['Mean energy'])
        self.stdev_energy_ind.setValue(self.spectro_data_dict['Std energy'])
        self.charge_ind.setValue(self.spectro_data_dict['Charge'])
        self.signalSpectroDict.emit(self.spectro_data_dict)  # Signal for diagServ


if __name__ == "__main__":

    appli = QApplication(sys.argv)
    appli.setStyleSheet(qdarkstyle.load_stylesheet(qt_api='pyqt6'))
    file= str(pathlib.Path(__file__).parents[0])+'/tir_025.TIFF'
    e =WINSPECTRO(name='VISU', file=file)
    e.show()
    appli.exec_()
