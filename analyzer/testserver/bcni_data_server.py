'''
Created on Mar 26, 2017

@author: bstad
'''
import multiprocessing as mp
import time

from pylsl import StreamInfo, StreamOutlet, IRREGULAR_RATE
from pylsl import resolve_stream, StreamInlet

from analyzer.testserver.bcnidata import BCNIData


class BCNIDataServer(mp.Process):
    
    def __init__(self, filename):
        mp.Process.__init__(self)
        self.data = BCNIData(filename)
        
    def second_init(self):
        '''Used because otherwise multiprocessing cannot pickle object
        '''
        #self.data.load_file()
        
        # LSL Settings
        self.eeg_streamname = "testeeg_stream"
        self.marker_streamname = "marker_stream"
        self.period_time = 1.0 / self.data.samplerate # seconds
        
        
        # EEG stream
        self.eeg_info = StreamInfo(name = self.eeg_streamname, nominal_srate = self.data.samplerate, 
                                   type='EEG', channel_count=self.data.num_channels, channel_format="float32", 
                                   source_id='eeg_stream_test', handle=None)
        self.lsl_eeg = StreamOutlet(self.eeg_info)
        
        # Marker Stream
        self.marker_info = StreamInfo(name = self.marker_streamname, type='P300_Marker', 
                                      nominal_srate=IRREGULAR_RATE,
                                      channel_count=1, channel_format="int8", 
                                      source_id='marker_stream', handle=None)
        self.marker_info.desc().append_child_value("flash_mode", self.data.flash_mode)
        self.marker_info.desc().append_child_value("num_rows", "6")
        self.marker_info.desc().append_child_value("num_cols", "6")
        self.lsl_marker = StreamOutlet(self.marker_info)

    def run(self):
        self.second_init()
        
        # Stream data
        print("Server started...")
        print("EEG samples stream: \"" + self.eeg_streamname + "\"")
        print("P300 Markers stream: \"" + self.marker_streamname + "\"")
        
        # Hack to start earlier 
        self.data.set_counter(3000)
        
        while True: 
            timestamp = self.data.get_timestamp()
            eeg_data = self.data.get_eeg_data()
            marker = self.data.get_marker()
            self.data.increase_counter()
            
            self.lsl_eeg.push_sample(eeg_data, timestamp)
            
            # Push only non zero markers
            if marker[0] != 0:
                self.lsl_marker.push_sample(marker, timestamp)
            
            time.sleep(self.period_time)


if __name__ == "__main__":
    server = BCNIDataServer("s1.mat")
    server.start()
    
    streams = resolve_stream("name", "testeeg_stream")
    inlet = StreamInlet(streams[0])
#     while True:
#         print(inlet.pull_sample())
