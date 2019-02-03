'''
Created on Apr 14, 2017

@author: bstad
'''
import multiprocessing as mp
import time

import matplotlib.pyplot as plt
import numpy as np
from pylsl import StreamInlet, resolve_stream

from analyzer.analizer_gui import MainWindow
from analyzer.analysis_thread import AnalysisThread
from analyzer.data import RecordedData
from analyzer.lsl_receiver_thread import LSLReceiverThread


class ConnectorProc(object):
    '''
    classdocs
    '''

    def __init__(self):
        '''
        Constructor
        '''
        self.eeg_inlet = None
        self.marker_inlet = None
        
        self.lsl_rec_threads = []
        self.analysis_thread = []
        
        self.recorded_data = None

        manager = mp.Manager()
        self.connector_dict = manager.dict()
        self.connector_dict["update interval"] = None
        self.connector_dict["channel select"] = None
        self.connector_dict["number of channels"] = None
        self.connector_dict["samplerate"] = None
        self.connector_dict["eeg stramname"] = None
        self.connector_dict["marker streamname"] = None
        self.connector_dict["sample count"] = 0
        self.connector_dict["num rows"] = 0
        self.connector_dict["num cols"] = 0
        self.connector_dict["flash mode"] = 0
        self.connector_dict["y lim"] = [0, 100]
        self.connector_dict["savefile"] = ["1"]
        self.connector_dict["filter"] = 0
        self.connector_dict["squared"] = 0
        self.start_recording_e = mp.Event()
        self.start_analysis_e = mp.Event()
        self.ready_for_connection_e = mp.Event()
        self.connected_e = mp.Event()
        self.save_e = mp.Event()

        self.message_q = mp.Queue()

        self.analyzer_gui = MainWindow(self.connector_dict, self.message_q, self.start_recording_e,
                                       self.start_analysis_e, self.connected_e, self.ready_for_connection_e,
                                       self.save_e)
        self.analyzer_gui.start()

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
        self.ready_for_connection_e.wait()
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

        data_to_plotter_queue = mp.Queue()
        axis_to_plotter_queue = mp.Queue()
        self.analysis_thread = AnalysisThread(self.recorded_data, self.connector_dict, self.message_q,
                                              data_to_plotter_queue, axis_to_plotter_queue)
        
        self.connected_e.set()
        
        self.start_recording_e.wait()

        for thread in self.lsl_rec_threads:
            thread.start()

        self.start_analysis_e.wait()
        samplerate = self.connector_dict["samplerate"]
        start_ylim = self.connector_dict["y lim"]
        num_rows = self.connector_dict["num rows"]
        num_cols = self.connector_dict["num cols"]
        plotter = Plotter(samplerate, start_ylim, num_rows, num_cols, data_to_plotter_queue, axis_to_plotter_queue)
        
        self.analysis_thread.start()

        while True:
            plotter.udpate_axis_if_possible()
            plotter.update_data_if_possible()

            if self.save_e.is_set():
                self.recorded_data.save(self.connector_dict["savefile"])
                self.save_e.clear()
            time.sleep(0.1)


class Plotter(object):
    def __init__(self, samplerate, start_ylim, num_rows, num_cols, data_queue, axis_queue):
        self.samplerate = samplerate
        self.num_rows = num_rows
        self.num_cols = num_cols

        self.data_queue = data_queue
        self.axis_queue = axis_queue

        self.create_figure(start_ylim)

    def update_plot(self, avg_trials):
        for i, line in enumerate(self.lines):
            line.set_ydata(avg_trials[i, :])

        self.figure.canvas.draw()
        self.figure.canvas.flush_events()

    def create_figure(self, ylim):
        # Turn on interactive plotting
        plt.ion()

        self.figure, self.axes = plt.subplots(self.num_rows, self.num_cols, sharex='col', sharey='row')

        x_axis = np.arange(int(self.samplerate)) / self.samplerate * 1000  # Show one second
        y = np.zeros(int(self.samplerate))

        self.lines = []
        for row in self.axes:
            for col in row:
                line, = col.plot(x_axis, y)
                self.lines.append(line)
                col.set_ylim(ylim)

        figManager = plt.get_current_fig_manager()
        figManager.window.showMaximized()
        self.figure.canvas.draw()
        self.figure.canvas.flush_events()
        # plt.show(block=False)

    def update_axes(self, ylim):
        for row in self.axes:
            for col in row:
                col.set_ylim(ylim)

    def update_data_if_possible(self):
        if not self.data_queue.empty():
            self.update_plot(self.data_queue.get())

    def udpate_axis_if_possible(self):
        if not self.axis_queue.empty():
            self.update_axes(self.axis_queue.get())
