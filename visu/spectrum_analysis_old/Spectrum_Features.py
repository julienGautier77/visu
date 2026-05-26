import numpy as np
import math as m


def find_nearest(data, value) -> float:
    return (np.abs(data - value)).argmin()


def find_indices(energy: np.ndarray, energy_bounds: list = None) -> tuple:
    '''
    Extracts subdata from energy and data array, given energy bounds specified in interface
    :param energy:
    :return:
    '''
    if energy_bounds is None:
        return 0, -1
    else:
        low_index = find_nearest(energy, energy_bounds[0])
        high_index = find_nearest(energy, energy_bounds[1])
        return low_index, high_index


def weighted_avg_and_std(energy: np.ndarray, data_counts: np.ndarray) -> tuple:
    average = np.average(energy, weights=data_counts)
    variance = np.average((energy - average) ** 2, weights=data_counts)
    return average, m.sqrt(variance)


def electron_charge(energy: np.ndarray, data_counts: np.ndarray):
    return np.sum(np.diff(energy) * data_counts[1:])


def build_dict(energy: np.ndarray, data: np.ndarray, shotNum: int, energy_bounds):
    low, high = find_indices(energy, energy_bounds)
    energy = energy[low:high]
    data = data[low:high]
    mean_energy, std_energy = weighted_avg_and_std(energy, data)
    charge = electron_charge(energy, data)

    data_dict = dict((('Std energy', std_energy),
                      ('Mean energy', mean_energy),
                      ('Charge', charge),
                      ('Shot number', shotNum)))
    return data_dict
