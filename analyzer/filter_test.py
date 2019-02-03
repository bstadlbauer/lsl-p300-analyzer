'''
Created on May 11, 2017

@author: bstad
'''

import matplotlib.pyplot as plt
import numpy as np
from numpy import matlib

from analyzer.data import RecordedData

if __name__ == '__main__':
    samplerate = 1000  # Hz
    length = 5  # s
    num_chan = 8

    t = np.linspace(0, length, samplerate * length)

    sin1 = np.sin(2 * np.pi * t * 5)
    sin2 = np.sin(2 * np.pi * t * 200)

    one_y = (sin1 + sin2).T
    y = matlib.repmat(one_y, num_chan, 1).T

    plt.plot(t, y[:, 1])
    plt.show()

    data = RecordedData()
    data.set_samplerate(samplerate)
    data.set_num_channel(num_chan)

    for row in y:
        data.append_eeg_sample(row)

    filtered_data = data.get_eeg_numpy()

    plt.plot(filtered_data[:, 5])
    plt.show()
