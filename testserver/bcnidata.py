import os
import ssl
import urllib.request

import certifi
from scipy import io

from testserver.constants import BNCI_CACHE_DIR, BNCI_HORIZON_DATA_URL


class BCNIData(object):
    """Wrapper for a recordings from the BNCI Horizon Project

    Args:
        filename: Filename to load, e.g. 's1.mat'

    """

    def __init__(self, subject_number: int):
        self.subject_number = subject_number
        self.filename = os.path.join(BNCI_CACHE_DIR, f"s{subject_number}.mat")
        print(self.filename)
        self._download_data_if_not_present(subject_number)
        self.counter = 0

        self.timestamps = []
        self.eeg_data = []
        self.markers = []
        self.target = []
        self.length = None
        self.flash_mode = "Single Value"
        self.samplerate = 256  # Hz
        self.num_channels = None

        self.matrix = None

        self.load_file()

    def _download_data_if_not_present(self, subject_number: int):
        if not os.path.isfile(self.filename):
            os.makedirs(os.path.dirname(self.filename), exist_ok=True)
            url = BNCI_HORIZON_DATA_URL.format(subject_number=subject_number)
            print(
                f"No data for subject {subject_number} found. Downloading data from {url} to {self.filename}. "
                f"This data is open access. For more information visit: "
                f"http://bnci-horizon-2020.eu/database/data-sets (dataset 003-2015)"
            )
            with urllib.request.urlopen(url, context=ssl.create_default_context(cafile=certifi.where())) as response:
                subject_data = response.read()
            with open(self.filename, "wb") as out_file:
                out_file.write(subject_data)
            print("Done.")

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
        # axis: [filename][0][0][train/test]
        self.matrix = io.loadmat(self.filename)[f"s{self.subject_number}"][0][0][1]
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
