import numpy as np
from PIL import Image
import time as t
import pyqtgraph as pg
from pyqtgraph import ColorBarItem
from scipy.interpolate import interp1d
from os import sep

VIRIDIS = pg.colormap.get('viridis')


def spectrum_image(im_path: str, revert: bool):
    """Opens image from file, returns 2D numpy array"""
    if revert:
        return np.flip(np.array(Image.open(im_path)), axis=1)
    else:
        return np.array(Image.open(im_path))


class CalibrationData:
    """
    :param cal_path: path to calibration file (absolute)
    Calibration Data takes a calibration file formatted as:
        1st column: energy in MeV
        2nd column: ds/dE in mm/MeV
        3rd column: s in mm (longitudinal coordinate along the lanex
                    with respect to beam position without magnet)
    Attributes:
        energy: array with equal spacing in energy
        dsde: ds/dE interpolated for each energy value
        s: s interpolated for each energy value
    """
    def __init__(self, cal_path: str):
        cal = np.loadtxt(cal_path).T
        self.energy = cal[0]
        self.dsde = cal[1]
        self.s = cal[2]


class DeconvolvedSpectrum:
    """
    :param image: image is a 2D numpy array, not an image :)
    :param pixel_per_mm: calibration in pixel per mm
    :param mrad_per_pix: calibration mrad per pixel
    :param ref_mode: string, should be "zero" or "refpoint"
    :param ref_point: tuple, either (x, y) coordinates of zero in pixels if chosen method is "zero"
                             or (x, E) x-coordinate (mm) of a given energy (MeV) is chosen method is "refpoint"
    :param pC_per_Count: pC pre count on camera, from calibration
    :param offset: offset of lanex. Positive = to low energy (larger s), negatives to high energy (lower s)

    Public attributes:

    """
    def __init__(self, image: np.ndarray, calibration: CalibrationData, spacing: float, pixel_per_mm: float,
                 mrad_per_pix: float, ref_mode: str, ref_point: tuple, pC_per_count: float, offset: float=0):

        self.pixel_per_mm = pixel_per_mm
        self.mrad_per_pix = mrad_per_pix
        self.ref_mode = ref_mode
        self.ref_point = ref_point
        self.calibration = calibration
        self.spacing = spacing
        self.pC_per_count = pC_per_count
        self.image_dimensions = image.shape
        self.offset_px = offset*pixel_per_mm

        self.set_axes()
        self.set_dsde()

        self.deconvolve_data(image)

    def set_axes(self):
        # x-axis: energy
        if self.ref_mode == "Zero":
            x_min = self.ref_point[0] + self.offset_px - self.image_dimensions[1]
            x_max = self.ref_point[0] + self.offset_px

        elif self.ref_mode == "RefPoint":
            s_ref = np.interp(self.ref_point[1], self.calibration.energy, self.calibration.s, 
                                        right=np.nan, left=np.nan)
            x_min = int((s_ref - self.ref_point[0])*self.pixel_per_mm) + self.offset_px
            x_max = x_min + self.image_dimensions[1]

        else:
            raise ValueError("referencing mode should be either 'zero' or 'refpoint'")

        x_lanex = np.linspace(x_min, x_max, self.image_dimensions[1]) / self.pixel_per_mm
        # Filter axis with Yamask (Filter-out undefined s-values)
        x_lanex[x_lanex < min(self.calibration.s)] = np.nan
        x_lanex[x_lanex > max(self.calibration.s)] = np.nan
        self._energy_uneven = np.interp(x_lanex, np.flip(self.calibration.s), np.flip(self.calibration.energy),
                                        right=np.nan, left=np.nan)

        self._valid_yamask = ~np.isnan(x_lanex)  # take only not NaN elements
        self._energy_uneven = self._energy_uneven[self._valid_yamask]

        emin = min(self._energy_uneven) # Min measurable energy on lanex
        emax = max(self._energy_uneven) # Max measurable energy on lanex
        # Evenly spaced energy axis
        self.energy = np.linspace(emin, emax, int((emax - emin) / self.spacing))

        # y-axis: angle
        self.angle = np.linspace(-self.image_dimensions[0] / 2,
                                 self.image_dimensions[0] / 2, self.image_dimensions[0]) * self.mrad_per_pix

    def set_dsde(self):
        self.dsdE = np.interp(self.energy, self.calibration.energy, self.calibration.dsde,
                              right=np.nan, left=np.nan)

    def deconvolve_data(self, image):
        # keep all rows, filter-out meaningless data from columns
        try:
            self._filtered_image = image[:, self._valid_yamask]
        except IndexError as e:
            print(f'{e}:\n Does your calibration image (calib_image.tiff) '
                  f'have the same dimensions as your camera output?')
        # Interpolation function: takes data array and creates an interpolation function that can then be called
        # with any input energy array
        interp_func = interp1d(self._energy_uneven, self._filtered_image, axis=1, kind='linear')
        self.image = interp_func(self.energy)

    def integrate_spectrum(self, data_cursors: tuple, background_cursors: tuple):
        data = self.image[data_cursors[0]:data_cursors[1], :]
        background = np.average(self.image[background_cursors[0]:background_cursors[1], :])
        data = data - background
        data[data < 0] = 0
        self.integrated_spectrum = (self.pC_per_count*self.pixel_per_mm*
                                    np.multiply(np.sum(data, axis=0), abs(self.dsdE)))

class SpectrumGraph:
    def __init__(self, _spectrum_image: DeconvolvedSpectrum):
        self.app = pg.mkQApp()
        self.win = pg.GraphicsLayoutWidget()
        self.win.show()

        self.plot = self.win.addPlot()
        self.set_labels()
        self.set_image(_spectrum_image)
        self.set_colorbar(_spectrum_image)

    def set_labels(self):
        self.plot.setLabel('bottom', 'Energy', units='MeV')  # adjust units
        self.plot.setLabel('left', 'Angle', units='mrad')

    def set_image(self, _spectrum_image):
        self.img = pg.ImageItem(_spectrum_image.image.T)  # transpose so axes align correctly
        self.plot.addItem(self.img)

        self.img.setRect(
            _spectrum_image.energy[0],  # x origin
            _spectrum_image.angle[0],  # y origin
            _spectrum_image.energy[-1] - _spectrum_image.energy[0],  # width
            _spectrum_image.angle[-1] - _spectrum_image.angle[0]  # height
        )

    def set_colorbar(self, _spectrum_image):
        self.bar = ColorBarItem(values=(_spectrum_image.image.min(), _spectrum_image.image.max()))
        self.img.setColorMap(VIRIDIS)
        self.bar.setImageItem(self.img)
        self.win.addItem(self.bar)


if __name__ == "__main__":
    """
    Experimental data: 
        spatial calibration 49µm/px, 
        zero position {x=1953px, y=635px}, 
        signal calibration 4.33e-6pC/count
    For testing purposes, usage with refpoint (x, 10 MeV) as reference:
        x-coor = s(10MeV)+(imsize-1953)/mm_per_px = 47.86mm 
    """
    show = True
    # Load image and calibration
    spImage = spectrum_image(im_path=f'magnet0.4T_Soectrum_isat4.9cm_26bar_gdd25850_HeAr_0002.TIFF',
                             revert=True)
    calibration_data = CalibrationData(cal_path=f'dsdE_Small_LHC.txt')

    # Deconvolve data
    # "refpoint" method
    #deconvolved_spectrum = DeconvolvedSpectrum(spImage, calibration_data,0.5,
    #                                           20.408, 0.1,
    #                                           "refPoint", (47.855, 10))
    # "zero" method
    deconvolved_spectrum = DeconvolvedSpectrum(spImage, calibration_data, 0.5, 20.408, 0.1, "Zero", (1953, 635),
                                               4.33e-6, 0)
    t0 = t.time()
    deconvolved_spectrum.deconvolve_data(spImage)
    print(f'Deconvolution time: {t.time()-t0} s')

    t0 = t.time()
    deconvolved_spectrum.integrate_spectrum((600, 670), (750, 850))
    print(f'Integration time: {t.time() - t0} s')
    if show:
        # Show 2D plot
        graph = SpectrumGraph(deconvolved_spectrum)
        pg.exec()
