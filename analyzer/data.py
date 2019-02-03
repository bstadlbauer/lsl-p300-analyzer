'''
Created on Apr 12, 2017

@author: bstad
'''
import numpy as np

from analyzer.custom_filter import CustomBPFilter
from analyzer.testserver import BCNIData


class RecordedData(object):
    '''
    classdocs
    '''


    def __init__(self, filter_bool):
        '''
        Constructor
        '''
        self.eeg_data = []
        self.eeg_ts = []
        self.marker_data = []
        self.marker_ts = []
        self.samplerate = None
        self.num_chan = None
        
        self.filter_bool = filter_bool
#         self.channel_to_show = 8
        
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
                self.bandpass = CustomBPFilter(self.samplerate, 
                                               self.num_chan, 4, 1, 30)       
            numpy_sample = np.array(sample)
            numpy_sample = numpy_sample[np.newaxis, :]
            filtered_sample = self.bandpass.filter(numpy_sample) * 1e6
            # filtered_sample = filtered_sample - filtered_sample[0, 31]
            self.eeg_data.append(filtered_sample)
        else:
            sample = np.array(sample) * 1e6
            # sample = sample - sample[31]
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
        if self.marker_data == []:
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
            trials_temp.append(eeg_np[ind:ind + self.samplerate, :])
            markers_temp.append([self.marker_data[ind], self.target[ind]])
#             trial.append(self.marker_data[ind])
#             trial.append(self.target[ind])
            
        self.trials = np.array(trials_temp)   
        self.markers_short = np.array(markers_temp) 
#         marker_for_one_target = self.markers_short[:, 0] == 1 
#         for marker in self.markers_short[marker_for_one_target]:
#             print(marker)

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
        
        
#     def plot_avg(self):
#         non_target_ind = self.markers_short[:, 1] == 0
#         target_ind = self.markers_short[:, 1] == 1
#         select_element_non_target = self.markers_short[non_target_ind, 0] == 1
#         select_element_target = self.markers_short[target_ind, 0] == 21
#         
# #         print(len(selected_element))
# #         print(np.count_nonzero(selected_element))
#         
#         data_non_target = self.trials[non_target_ind, :, self.channel_to_show]
#         data_target = self.trials[target_ind, :, self.channel_to_show]
#         avg_non_target = np.mean(data_non_target[select_element_non_target, :], 0)**2
#         avg_target = np.mean(data_target[select_element_target, :], 0)**2
#         
#         f, (ax1, ax2) = plt.subplots(1, 2, sharey=True)
#         ax1.plot(avg_non_target)
#         ax1.set_title('Sharing Y axis')
#         ax2.plot(avg_target)
#         
#         plt.show()

    
if __name__ == "__main__":
    testdata = BCNIData("s1.mat")
    timestamps = testdata.timestamps
    eeg_data = testdata.eeg_data
    markers = testdata.markers
    
#     print(np.shape(timestamps))
#     print(np.shape(eeg_data))
#     print(np.shape(markers))
    print(np.array(markers))
    
    rec_data = RecordedData()
    rec_data.samplerate = testdata.samplerate
    rec_data.target = testdata.target
    
    for row in eeg_data.T:
        rec_data.eeg_data.append(row)
        
    for row in markers: 
        rec_data.marker_data.append(row)
    
#     target = np.array(testdata.target)
#     print(set(target))
#     print(target)
#     print(np.where(target == 1))
#     target_ind = target != 0
#     
#      
#     target_markers = np.array(rec_data.marker_data)[target_ind]
#     print(target_markers)
#     print(set(target_markers))

    rec_data.split_into_trials()
    rec_data.plot_avg()
   
    
    
