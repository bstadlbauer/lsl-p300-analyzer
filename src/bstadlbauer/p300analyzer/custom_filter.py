import numpy as np
from scipy import signal


class CustomBPFilter(object):
    """Wrapper for a scipy.signal.lfilter using cofficients from scipy.signal.butter

    Args:
        samplerate: Samplerate of the data
        num_chan: Number of channels
        order: Filter order
        cutoff_low: Low cutoff frequency in Hz
        cutoff_high: High cutoff frequency in Hz

    """

    def __init__(self, samplerate: int, num_chan: int, order: int, cutoff_low: int, cutoff_high: int):
        self.samplerate = samplerate
        self.num_chan = num_chan

        self.b = None
        self.a = None
        self.update_filter_coefficients(order, cutoff_low, cutoff_high)

        self.filter_delay = None
        self.init_filter_delay()

    def update_filter_coefficients(self, order, cutoff_low, cutoff_high):
        cutoff_freq_norm = np.array([cutoff_low, cutoff_high]) / (self.samplerate / 2.0)
        [self.b, self.a] = signal.butter(order, cutoff_freq_norm, "bandpass")

    def init_filter_delay(self):
        length = max(len(self.a), len(self.b)) - 1
        self.filter_delay = np.zeros([length, self.num_chan])

    def filter(self, x):
        y, self.filter_delay = signal.lfilter(self.b, self.a, x, 0, self.filter_delay)
        return y
