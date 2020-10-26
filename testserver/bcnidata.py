import os

from scipy import io


class BCNIData(object):
    """Wrapper for a recordings from the BNCI Horizon Project

    Args:
        filename: Filename to load, e.g. 's1.mat'

    """

    def __init__(self, filename):
        self.filename = filename
        self.counter = 0

        self.timestamps = []
        self.eeg_data = []
        self.markers = []
        self.target = []
        self.length = None
        self.flash_mode = "Single Value"
        self.samplerate = 256  # Hz
        self.num_channels = None

        self.file_location = None
        self.prefix = None
        self.path = None
        self.matrix = None

        self.load_file()

    def get_timestamp(self):
        return self.timestamps[self.counter % self.length]

    def get_eeg_data(self):
        return self.eeg_data[:, self.counter % self.length]

    def get_marker(self):
        return [int(self.markers[self.counter % self.length])]

    def set_counter(self, value):
        self.counter = value

    def increase_counter(self):
        self.counter += 1

    def load_file(self):
        self.file_location = os.path.dirname(__file__)
        self.prefix = "/BNCI Horizon - Guger 2009/Data/"

        self.path = self.file_location + self.prefix + self.filename

        self.matrix = io.loadmat(self.path)["s1"][0][0][1]  # axis: [filename][0][0][train/test]
        self.timestamps = self.matrix[0]
        self.eeg_data = self.matrix[1:9]

        self.markers = normalize_markers(self.matrix[9].astype(int))

        self.target = normalize_markers(self.matrix[10].astype(int))

        self.length = len(self.timestamps)
        self.num_channels = len(self.eeg_data)


def normalize_markers(markers):
    """Removes additional markers if there is more than one"""
    init = 2
    new_flash_ids = markers[0:init].tolist()
    number_of_ids = len(markers)

    for i in range(init, number_of_ids):
        if markers[i] != 0 and markers[i - 1] == 0:
            new_flash_ids.append(markers[i])
        else:
            new_flash_ids.append(0)

    return new_flash_ids
