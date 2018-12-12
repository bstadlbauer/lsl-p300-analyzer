'''
Created on Apr 12, 2017

@author: bstad
'''
from threading import Thread
import numpy as np

class LSLReceiverThread(Thread):
    '''
    classdocs
    '''
    
    def __init__(self, lsl_inlet, sample_func, sample_ts_func, connect_dict = None):
        ''' 
        Constructor
        '''
        Thread.__init__(self);
        self.lsl_stream_inlet = lsl_inlet
        self.sample_func = sample_func
        self.sample_ts_func = sample_ts_func
        
        self.connect_dict = connect_dict
              
    def run(self):
        self.receive_data()

    def receive_data(self):
        """Receives the data from the stream and puts it into the queue"""
        # First call of inlet correction is slower. Called once before "real"
        # use
       
        self.lsl_stream_inlet.time_correction() 
        
        num_samples = 0
        while True:
#             tuple_sample_timestamp = self.lsl_stream_inlet.pull_sample()
#             sample_timestamp = np.array(tuple_sample_timestamp)
#             # Time correction 
#             sample_timestamp[1] -= self.lsl_stream_inlet.time_correction()
            (sample, timestamp) = self.lsl_stream_inlet.pull_sample()
            timestamp -= self.lsl_stream_inlet.time_correction()

##            print(sample)
            self.sample_func(sample)
            self.sample_ts_func(timestamp)
            num_samples += 1
            
            if self.connect_dict is not None: 
                self.connect_dict["sample count"] = num_samples
