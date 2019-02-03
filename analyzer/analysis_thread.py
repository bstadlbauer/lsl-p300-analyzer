'''
Created on May 1, 2017

@author: bstad
'''
import time
from threading import Thread

import numpy as np


class AnalysisThread(Thread):
    def __init__(self, data, connect_dict, message_q, plotting_queue, axis_queue):
        Thread.__init__(self)

        self.data = data
        self.connect_dict = connect_dict
        self.samplerate = connect_dict["samplerate"]
        self.message_q = message_q
        self.plotting_queue = plotting_queue
        self.axis_queue = axis_queue

        self.figure = None
        self.axes = None
        self.lines = []

    def create_mapped_markers(self, marker, marker_ts, eeg_ts):
        y_axis = range(len(eeg_ts))
        coeff = np.polyfit(eeg_ts, y_axis, 1)

        marker_ind = np.rint(np.polyval(coeff, marker_ts)).astype(int)

        # Hack to prevent last element from being rounded up and being out of bounds
        out_of_bounds = marker_ind - len(eeg_ts)
        out_of_bounds_ind = out_of_bounds >= 0

        if out_of_bounds.any():
            # TODO: Check if this is really an issue
            pass
            # print("marker problem")
        ##            print(marker_ind[out_of_bounds_ind])

        marker_ind[out_of_bounds_ind] = len(eeg_ts) - 1
        if marker_ind[-1] == len(eeg_ts):
            marker_ind[-1] -= 1

        mapped_markers = np.zeros([len(eeg_ts), 1])
        mapped_markers[marker_ind] = marker

        return mapped_markers.astype(int), marker_ind

    def split_up_trials(self, eeg, marker, marker_indices):
        trials_temp = []
        markers_temp = []

        for ind in marker_indices:
            trial = eeg[ind:ind + int(self.samplerate), :]

            # Check to get only complete 1 Second (samplerate samples)  trial
            if len(trial) == int(self.samplerate):
                trials_temp.append(eeg[ind:ind + int(self.samplerate), :])
                markers_temp.append(marker[ind])

        trials = np.array(trials_temp)
        markers_short = np.array(markers_temp)

        return trials, markers_short

    def avg_trials_by_marker(self, markers, trials):
        # print(len(markers))
        # print(len(trials))
        avg_trials = []
        markers = np.squeeze(markers)
        marker_set = list(set(list(markers)))
        marker_set.sort()
        for marker in marker_set:
            trial_ind_true = np.where(markers == marker)
            trial_ind = trial_ind_true[0][-30:]

            if self.connect_dict["squared"] == 1:
                avg_trials.append(np.mean(trials[trial_ind], 0) ** 2)
            else:
                avg_trials.append(np.mean(trials[trial_ind], 0))
        return np.array(avg_trials)

    def classify_trials(self, markers, trials):
        trials = np.swapaxes(trials, 0, 2)
        # print("trials", trials.shape)
        markers = np.squeeze(markers)
        marker_set = list(set(list(markers)))
        marker_set.sort()

        epochs_for_classification = 6

        # Make sure that a minimum amount of trials per class are available
        for marker in marker_set:
            if np.sum(markers == marker) < epochs_for_classification:
                return None

        channel_to_use = self.connect_dict["channel select"]

        start_feature_second = 0.2
        end_feature_second = 0.5
        start_feature = int(start_feature_second * self.samplerate)
        end_feature = int(end_feature_second * self.samplerate)

        fields = []
        for marker in marker_set:
            trials_one_marker = trials[:, :, markers == marker]
            fields.append(trials_one_marker[channel_to_use, start_feature:end_feature, -epochs_for_classification:])
        fields = np.array(fields)
        # print("fields", fields.shape)

        scores = []
        for field_nr, field in enumerate(fields):
            target_data = fields[field_nr, :, :]
            non_target_list = list(range(len(fields)))
            non_target_list.remove(field_nr)
            non_target_data = np.hstack(fields[non_target_list, :, :])
            scores.append(fisher_criterion(target_data, non_target_data))

        classification_result = classify(scores)
        # print("Result", classification_result, scores, "\n")
        return classification_result

    def print_to_console(self, message):
        self.message_q.put(message)

    def run(self):
        num_rows = self.connect_dict["num rows"]
        num_cols = self.connect_dict["num cols"]
        current_ylim = self.connect_dict["y lim"]

        min_diff_markers = num_rows * num_cols

        # Do not count last 20 markers because they might not be fully recorded
        while len(set(self.data.get_marker_numpy()[:-20, 0])) < min_diff_markers:
            self.print_to_console("Not all markers were sent yet, waiting two seconds and then retrying")
            time.sleep(2)

        while True:
            marker = self.data.get_marker_numpy()
            marker_ts = self.data.get_marker_ts_numpy()
            eeg = self.data.get_eeg_numpy()
            eeg_ts = self.data.get_eeg_ts_numpy()
            print('marker', marker.shape, 'eeg', eeg.shape)

            mapped_markers, marker_ind = self.create_mapped_markers(marker, marker_ts, eeg_ts)
            trials, marker_short = self.split_up_trials(eeg, mapped_markers, marker_ind)

            avg_trials = self.avg_trials_by_marker(marker_short, trials)

            classification = self.classify_trials(marker_short, trials)
            # classification = 0

            # if classification is not None:
            if type(classification) == int:
                classification = classification + 1
            print("\rCurrent classification: {}".format(classification))

            temp_ylim = self.connect_dict["y lim"]
            current_channel = self.connect_dict["channel select"]
            avg_trials = np.squeeze(avg_trials[:, :, current_channel])

            if current_ylim == temp_ylim:
                self.plotting_queue.put(avg_trials)
            else:
                print("axis changed")
                current_ylim = temp_ylim
                self.axis_queue.put(current_ylim)
                self.plotting_queue.put(avg_trials)

            time.sleep(self.connect_dict["update interval"])


def fisher_criterion(targets, non_targets):
    mean_target = np.sum(np.abs(np.mean(targets, axis=1)))
    mean_non_target = np.sum(np.abs(np.mean(non_targets, axis=1)))
    variance_target = np.sum(np.abs(np.var(targets, axis=1)))
    variance_non_target = np.sum(np.abs(np.var(non_targets, axis=1)))

    return (mean_target - mean_non_target) ** 2 / (variance_target + variance_non_target)


def classify(scores):
    scores = np.array(scores)
    results = []
    for score_nr, score in enumerate(scores):
        not_active = np.ones([len(scores)], dtype=bool)
        not_active[score_nr] = False
        if np.max(scores[not_active]) * 2 < score:
            results.append(score_nr)

    if len(results) == 1:
        return results[0]
    else:
        return None
