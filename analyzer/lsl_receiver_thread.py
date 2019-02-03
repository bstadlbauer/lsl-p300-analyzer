from threading import Thread
from typing import Callable, Optional, Dict

from pylsl import pylsl


class LSLReceiverThread(Thread):
    """Worker that reveives samples from an LSL stream

    Args:
        lsl_inlet: LSL stream inlet
        sample_func: Function that will be called every time a new sample arrives. Should take one argument which is
            the sample
        sample_ts_func: Function that will be called every time a new sample arrives. Should take one argument which
            is the current timestamp of a sample.
        connect_dict: Connection dict created with multiprocessing.Manager().dict() that holds information shared
            between all processes and threads. Optional, defaults to None.

    """

    def __init__(self,
                 lsl_inlet: pylsl.StreamInlet,
                 sample_func: Callable,
                 sample_ts_func: Callable,
                 connect_dict: Optional[Dict] = None):
        Thread.__init__(self)
        self.lsl_stream_inlet = lsl_inlet
        self.sample_func = sample_func
        self.sample_ts_func = sample_ts_func

        self.connect_dict = connect_dict

    def run(self):
        self.receive_data()

    def receive_data(self):
        # First call of inlet correction is slower. Called once before "real"
        # use
        self.lsl_stream_inlet.time_correction()

        num_samples = 0
        while True:
            (sample, timestamp) = self.lsl_stream_inlet.pull_sample()
            timestamp -= self.lsl_stream_inlet.time_correction()
            self.sample_func(sample)
            self.sample_ts_func(timestamp)
            num_samples += 1

            if self.connect_dict is not None:
                self.connect_dict['sample count'] = num_samples
