import multiprocessing as mp
from typing import Dict

from pylsl import resolve_byprop


class MainWindow(mp.Process):
    """Defines the main control window and all its control logic.

    As Tkinter only allows to create root windwo (Tk()) in the main process, this is implemented as its own
    subprocess that will open the window with a call to self.run()

    Args:
        connector_dict: Dictionary create by calling multiprocessing.Manger().dict()
        message_q: Queue that will be polled every few seconds. Elements in queue will be plotted to the internal
            text field.
        start_analysis_e: Event signaling if analysis can be started
        connected_e: Event signaling that LSL streams are connected
        ready_for_connection_e: Event signaling that LSL streams have been selected in GUI
        save_e: Event signaling that data should be saved.

    """

    def __init__(self, connector_dict: Dict,
                 message_q: mp.Queue,
                 start_recording_e: mp.Event,
                 start_analysis_e: mp.Event,
                 connected_e: mp.Event,
                 ready_for_connection_e: mp.Event,
                 save_e: mp.Event):
        super().__init__()
        self.connector_dict = connector_dict
        self.message_q = message_q
        self.start_recording_e = start_recording_e
        self.start_analysis_e = start_analysis_e
        self.ready_for_connection_e = ready_for_connection_e
        self.connected_e = connected_e
        self.save_e = save_e

        self.master = None

        # Parameters
        self.eeg_stream = None
        self.eeg_streams_dict = None
        self.marker_stream = None
        self.marker_streams_dict = None
        self.channel_select = None
        self.update_interval = None
        self.record_time = None
        self.y_min = None
        self.y_max = None
        self.save_filename = None
        self.filter_check = None
        self.squared_check = None
        self.connected = None

        # Widgets
        self.eeg_stream_label = None
        self.eeg_stream_combobox = None
        self.eeg_stream_button = None
        self.marker_stream_label = None
        self.marker_stream_combobox = None
        self.marker_stream_button = None
        self.filter_checkbutton_label = None
        self.filter_checkbutton = None
        self.connect_button = None
        self.seperator = None
        self.start_recording_btn = None
        self.record_time_label = None
        self.Separator_2 = None
        self.update_interval_label = None
        self.update_interval_combobox = None
        self.start_analysis_btn = None
        self.channel_select_label = None
        self.channel_select_combobox = None
        self.squared_label = None
        self.squared_checkbtn = None
        self.update_ylim_btn = None
        self.y_min_label = None
        self.y_min_entry = None
        self.y_max_label = None
        self.y_max_entry = None
        self.seperator = None
        self.save_label = None
        self.save_entry = None
        self.save_btn = None
        self.text_console = None

    def build_main_window(self):
        # Hack to make tkinter work in other process than main
        from tkinter import Tk, StringVar, Text, HORIZONTAL, EW, IntVar
        from tkinter.ttk import Separator, Combobox, Button, Label, Entry, Checkbutton

        self.master = Tk()

        # Parameters
        self.eeg_stream = StringVar()
        self.eeg_streams_dict = {}
        self.marker_stream = StringVar()
        self.marker_streams_dict = {}
        self.channel_select = IntVar()
        self.channel_select.set(0)
        self.update_interval = IntVar()
        self.update_interval.set(3)
        self.record_time = StringVar()
        self.record_time.set("00:00 minutes recorded")
        self.y_min = IntVar()
        self.y_min.set(0)
        self.y_max = IntVar()
        self.y_max.set(100)
        self.save_filename = StringVar()
        self.save_filename.set("1")
        self.filter_check = IntVar()
        self.filter_check.set(0)
        self.squared_check = IntVar()
        self.squared_check.set(0)

        self.connected = False

        self.print_from_queue()

        # Widgets
        self.eeg_stream_label = Label(self.master, text='EEG LSL-stream:')
        self.eeg_stream_label.grid(row=0, column=0)

        self.eeg_stream_combobox = Combobox(self.master, textvariable=self.eeg_stream)
        self.eeg_stream_combobox.configure(state='disabled')
        self.eeg_stream_combobox.grid(row=0, column=1)

        self.eeg_stream_button = Button(self.master, text='Refresh',
                                        command=lambda: self.find_streams('EEG',
                                                                          self.eeg_stream_combobox,
                                                                          self.eeg_streams_dict,
                                                                          self.eeg_stream))
        self.eeg_stream_button.grid(row=0, column=2)

        self.marker_stream_label = Label(self.master, text='Marker LSL-stream:')
        self.marker_stream_label.grid(row=1, column=0)

        self.marker_stream_combobox = Combobox(self.master, textvariable=self.marker_stream)
        self.marker_stream_combobox.configure(state='disabled')
        self.marker_stream_combobox.grid(row=1, column=1)

        self.marker_stream_button = Button(self.master, text='Refresh',
                                           command=lambda: self.find_streams('P300_Marker',
                                                                             self.marker_stream_combobox,
                                                                             self.marker_streams_dict,
                                                                             self.marker_stream))
        self.marker_stream_button.grid(row=1, column=2)

        self.filter_checkbutton_label = Label(self.master, text='Filter (Butter, Order 4, Cutoff: 1, 30):')
        self.filter_checkbutton_label.grid(row=2, column=0)

        self.filter_checkbutton = Checkbutton(self.master, variable=self.filter_check, text='')
        self.filter_checkbutton.grid(row=2, column=1)

        self.connect_button = Button(self.master, text='Connect', command=self.connect_streams)
        self.connect_button.grid(row=2, column=2)
        self.connect_button.configure(state='disabled')

        self.seperator = Separator(self.master, orient=HORIZONTAL)
        self.seperator.grid(row=3, column=0, columnspan=3, sticky=EW)

        self.start_recording_btn = Button(self.master, text='Start recoding',
                                          command=self.start_recording)
        self.start_recording_btn.grid(row=4, column=2)
        self.start_recording_btn.configure(state='disabled')

        self.record_time_label = Label(self.master, textvariable=self.record_time)
        self.record_time_label.grid(row=4, column=1)

        self.Separator_2 = Separator(self.master)
        self.Separator_2.grid(row=5, column=0, columnspan=3, sticky=EW)

        self.update_interval_label = Label(self.master, text='Update interval (seconds):')
        self.update_interval_label.grid(row=6, column=0)

        self.update_interval_combobox = Combobox(self.master, textvariable=self.update_interval)
        self.update_interval_combobox.bind('<<ComboboxSelected>>', self.update_connector_dict)
        self.update_interval_combobox.grid(row=6, column=1)
        self.update_interval_combobox['values'] = list(range(10))
        self.update_interval_combobox.configure(state='disabled')

        self.start_analysis_btn = Button(self.master, text='Start analysis', command=self.start_analysis)
        self.start_analysis_btn.grid(row=6, column=2)
        self.start_analysis_btn.configure(state='disabled')

        self.channel_select_label = Label(self.master, text='Channel to display:')
        self.channel_select_label.grid(row=7, column=0)

        self.channel_select_combobox = Combobox(self.master, textvariable=self.channel_select)
        self.channel_select_combobox.bind('<<ComboboxSelected>>', self.update_connector_dict)
        self.channel_select_combobox.grid(row=7, column=1)
        self.channel_select_combobox.configure(state='disabled')

        self.squared_label = Label(self.master, text='squared')
        self.squared_label.grid(row=8, column=0)

        self.squared_checkbtn = Checkbutton(self.master, variable=self.squared_check)
        self.squared_checkbtn.grid(row=8, column=1)
        self.squared_checkbtn.configure(state='disabled')

        self.update_ylim_btn = Button(self.master, text='Update', command=self.update_connector_dict)
        self.update_ylim_btn.grid(row=8, column=2)
        self.update_ylim_btn.configure(state='disabled')

        self.y_min_label = Label(self.master, text='Y min:')
        self.y_min_label.grid(row=9, column=0)

        self.y_min_entry = Entry(self.master, textvariable=self.y_min)
        self.y_min_entry.grid(row=9, column=1)
        self.y_min_entry.configure(state='disabled')

        self.y_max_label = Label(self.master, text='Y max:')
        self.y_max_label.grid(row=10, column=0)

        self.y_max_entry = Entry(self.master, textvariable=self.y_max)
        self.y_max_entry.grid(row=10, column=1)
        self.y_max_entry.configure(state='disabled')

        self.seperator = Separator(self.master, orient=HORIZONTAL)
        self.seperator.grid(row=11, column=0, columnspan=3, sticky=EW)

        self.save_label = Label(self.master, text='Filename:')
        self.save_label.grid(row=12, column=0)

        self.save_entry = Entry(self.master, textvariable=self.save_filename)
        self.save_entry.grid(row=12, column=1)
        self.save_entry.configure(state='disabled')

        self.save_btn = Button(self.master, text='Save', command=self.save)
        self.save_btn.grid(row=12, column=2)
        self.save_btn.configure(state='disabled')

        self.text_console = Text(self.master)
        self.text_console.grid(row=15, column=0, rowspan=3, columnspan=3)
        self.text_console.configure(state='disabled')

    def save(self):
        self.update_connector_dict()
        self.save_e.set()

    def update_channel_select(self):
        num_channels = self.connector_dict['number of channels']
        self.channel_select_combobox['values'] = list(range(num_channels))

    def start_recording(self):
        self.connect_button.configure(state='disabled')
        self.start_recording_btn.configure(state='disabled')
        self.channel_select_combobox.configure(state='normal')
        self.update_interval_combobox.configure(state='normal')
        self.y_min_entry.configure(state='normal')
        self.y_max_entry.configure(state='normal')
        self.update_ylim_btn.configure(state='normal')
        self.squared_checkbtn.configure(state='normal')

        self.update_channel_select()
        self.update_recording_time()

        self.start_recording_e.set()

        self.start_analysis_btn.configure(state='normal')

    def update_recording_time(self):
        num_samples = self.connector_dict['sample count']
        samplerate = self.connector_dict['samplerate']
        number_of_seconds = int(num_samples / samplerate)

        minutes = number_of_seconds // 60
        remaining_seconds = number_of_seconds % 60

        result_string = '{:02}:{:02} minutes recorded'.format(minutes, remaining_seconds)

        self.record_time.set(result_string)
        self.master.after(1000, self.update_recording_time)

    def start_analysis(self):
        self.start_analysis_btn.configure(state='disabled')
        self.save_btn.configure(state='normal')
        self.save_entry.configure(state='normal')

        self.update_connector_dict()
        self.start_analysis_e.set()

    def find_streams(self, stream_type, widget, stream_dict, var):
        stream_dict.clear()
        timeout = 3
        self.print_to_console('Searching for ' + stream_type +
                              ' streams... (timeout = ' + str(timeout) + ' seconds)')

        streams = resolve_byprop('type', stream_type, timeout=timeout)
        if not streams:
            self.print_to_console('No stream found.')
            return

        widget.configure(state='normal')

        stream_list = []
        for stream in streams:
            stream_dict[stream.name()] = stream
            stream_list.append(stream.name())

        widget['values'] = stream_list

        if len(streams) >= 1:
            var.set(streams[0].name())

        self.print_to_console(str(len(streams)) + ' Stream(s) found!')
        self.test_if_two_streams()

    def test_if_two_streams(self):
        if self.eeg_stream.get() is not '' and self.marker_stream.get() is not '':
            self.connect_button.configure(state='normal')
        else:
            self.connect_button.configure(state='disabled')

    def print_to_console(self, text_to_print):
        text_to_print = str(text_to_print)

        self.text_console.configure(state='normal')
        self.text_console.insert('end', text_to_print + '\n')
        self.text_console.configure(state='disabled')

    def print_from_queue(self):
        if not self.message_q.empty():
            self.print_to_console(self.message_q.get())
        self.master.after(500, self.print_from_queue)

    # noinspection PyUnusedLocal
    def update_connector_dict(self, event=None):
        self.connector_dict['update interval'] = self.update_interval.get()
        self.connector_dict['channel select'] = self.channel_select.get()
        self.connector_dict['eeg streamname'] = self.eeg_stream.get()
        self.connector_dict['marker streamname'] = self.marker_stream.get()
        self.connector_dict['y lim'] = [self.y_min.get(), self.y_max.get()]
        self.connector_dict['savefile'] = self.save_filename.get()
        self.connector_dict['filter'] = self.filter_check.get()
        self.connector_dict['squared'] = self.squared_check.get()

    def connect_streams(self):
        self.eeg_stream_combobox.configure(state='disabled')
        self.eeg_stream_button.configure(state='disabled')
        self.marker_stream_combobox.configure(state='disabled')
        self.marker_stream_button.configure(state='disabled')
        self.filter_checkbutton.configure(state='disabled')
        self.connect_button.configure(state='disabled')

        self.update_connector_dict()
        self.ready_for_connection_e.set()

        self.connected_e.wait()

        self.start_recording_btn.configure(state='normal')

    def run(self):
        self.build_main_window()
        self.master.mainloop()
