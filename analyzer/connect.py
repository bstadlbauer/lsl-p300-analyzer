'''
Created on Apr 14, 2017

@author: bstad
'''
import multiprocessing as mp

from pylsl import StreamInlet, resolve_stream

from analyzer.analysis_thread import AnalysisThread
from analyzer.data import RecordedData
from analyzer.lsl_receiver_thread import LSLReceiverThread


class ConnectorProc(mp.Process):
    '''
    classdocs
    '''


    def __init__(self, connect_dict, message_q, start_recording_e, 
                 start_analysis_e, connected_e, save_e):
        '''
        Constructor
        '''
        mp.Process.__init__(self)
        self.connector_dict = connect_dict
        self.message_q = message_q
        
        self.start_recording_e = start_recording_e
        self.start_analysis_e = start_analysis_e
        self.connected_e = connected_e
        self.save_e = save_e
        
        self.eeg_inlet = None
        self.marker_inlet = None
        
        self.lsl_rec_threads = []
        self.analysis_thread = []
        
        self.recorded_data = None
        
    def create_inlets(self):
        self.eeg_inlet = self.create_inlet(self.connector_dict["eeg streamname"])
        self.marker_inlet = self.create_inlet(self.connector_dict["marker streamname"])
           
    def create_inlet(self, name):
        streams = resolve_stream("name", str(name))
        inlet = StreamInlet(streams[0])

        if len(streams) != 1:
            self.print_to_console("ATTENTION: More streams with name: \"" +
                  name + "\" found, using the first one")
              
        return inlet
    
    def update_lsl_metadata(self):
        info_eeg = self.eeg_inlet.info()
        self.connector_dict["number of channels"] = info_eeg.channel_count()
        self.connector_dict["samplerate"] = info_eeg.nominal_srate()
        
        info_marker = self.marker_inlet.info()
        self.connector_dict["num rows"] = int(info_marker.desc().child_value("num_rows"))
        self.connector_dict["num cols"] = int(info_marker.desc().child_value("num_cols"))
        self.connector_dict["flash mode"] = info_marker.desc().child_value("flash_mode")
        
    def print_to_console(self, message):
        self.message_q.put(message)
        
    def run(self):
        self.create_inlets()
        self.update_lsl_metadata()
        
        samplerate = self.connector_dict["samplerate"]
        number_of_channels = self.connector_dict["number of channels"]
        self.print_to_console("Connected! There are {} channels with a samplerate of {}Hz".format(number_of_channels, samplerate))
        
        self.recorded_data = RecordedData(self.connector_dict["filter"])
        self.recorded_data.set_samplerate(samplerate)
        self.recorded_data.set_num_channel(number_of_channels)
        
        eeg_thread = LSLReceiverThread(self.eeg_inlet, self.recorded_data.append_eeg_sample, 
                                       self.recorded_data.append_eeg_ts, self.connector_dict)
        marker_thread = LSLReceiverThread(self.marker_inlet, self.recorded_data.append_marker_sample, 
                                          self.recorded_data.append_marker_ts)
        
        self.lsl_rec_threads.append(eeg_thread)
        self.lsl_rec_threads.append(marker_thread)
        
        self.analysis_thread = AnalysisThread(self.recorded_data, self.connector_dict, self.message_q)
        
        self.connected_e.set()
        
        self.start_recording_e.wait()

        for thread in self.lsl_rec_threads:
            thread.start()
            
        self.start_analysis_e.wait()
        
        self.analysis_thread.start()
        
        while True: 
            
            self.save_e.wait()
            self.recorded_data.save(self.connector_dict["savefile"])
            self.save_e.clear()
        
            
#         while True: 
#             print(len(self.recorded_data.eeg_data), len(self.recorded_data.marker_data))
#             time.sleep(1)
            
        
        
        
        
