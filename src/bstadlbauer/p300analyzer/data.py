import numpy as np

from bstadlbauer.p300analyzer.custom_filter import CustomBPFilter


class RecordedData(object):
    """Container that holds all data shared between threads and logic for processing samples.

    Args:
        filter_bool: Boolean that determines if data should be filtered or not

    """

    def __init__(self, filter_bool: bool):
        self.eeg_data = []
        self.eeg_ts = []
        self.marker_data = []
        self.marker_ts = []
        self.samplerate = None
        self.num_chan = None

        self.filter_bool = filter_bool

        self.target = []
        self.trials = None
        self.target_ind = None
        self.non_target_ind = None
        self.markers_short = []

        self.bandpass = None

    def set_samplerate(self, samplerate):
        self.samplerate = samplerate

    def set_num_channel(self, num_chan):
        self.num_chan = num_chan

    def append_eeg_sample(self, sample):
        if self.filter_bool == 1:
            if self.bandpass is None:
                self.bandpass = CustomBPFilter(self.samplerate, self.num_chan, 4, 1, 30)
            numpy_sample = np.array(sample)
            numpy_sample = numpy_sample[np.newaxis, :]
            filtered_sample = self.bandpass.filter(numpy_sample) * 1e6
            # filtered_sample = filtered_sample - filtered_sample[0, 31]  # Uncomment this to set reference channel
            self.eeg_data.append(filtered_sample)
        else:
            sample = np.array(sample) * 1e6
            # sample = sample - sample[31]  # Uncomment this to set reference channel
            self.eeg_data.append(sample)

    def append_eeg_ts(self, timestamp):
        self.eeg_ts.append(timestamp)

    def append_marker_sample(self, sample):
        self.marker_data.append(sample)

    def append_marker_ts(self, timestamp):
        self.marker_ts.append(timestamp)

    def get_eeg_list(self):
        return self.eeg_data

    def get_eeg_ts_list(self):
        return self.eeg_ts

    def get_marker_list(self):
        return self.marker_data

    def get_marker_ts_list(self):
        return self.marker_ts

    def get_eeg_numpy(self):
        return np.squeeze(np.array(self.eeg_data))

    def get_eeg_ts_numpy(self):
        return np.array(self.eeg_ts)

    def get_marker_numpy(self):
        if not self.marker_data:
            return np.zeros([1, 2])
        return np.array(self.marker_data)

    def get_marker_ts_numpy(self):
        return np.array(self.marker_ts)

    def split_into_trials(self):
        eeg_np = np.array(self.eeg_data)
        marker_indices = np.where(np.array(self.marker_data) != 0)[0]
        trials_temp = []
        markers_temp = []

        for ind in marker_indices:
            trials_temp.append(eeg_np[ind : ind + self.samplerate, :])
            markers_temp.append([self.marker_data[ind], self.target[ind]])

        self.trials = np.array(trials_temp)
        self.markers_short = np.array(markers_temp)

    def save(self, filename):
        print("save")
        prefix = "saved_data/"
        path_eeg = prefix + filename + "_eeg"
        path_eeg_ts = prefix + filename + "_eeg_ts"
        path_marker = prefix + filename + "_marker"
        path_marker_ts = prefix + filename + "marker_ts"

        np.save(path_eeg, self.get_eeg_numpy())
        np.save(path_eeg_ts, self.get_eeg_ts_numpy())
        np.save(path_marker, self.get_marker_numpy())
        np.save(path_marker_ts, self.get_marker_ts_numpy())
