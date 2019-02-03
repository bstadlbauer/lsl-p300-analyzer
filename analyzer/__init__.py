"""Uses EEG and marker data streamed via LSL to show averaging process of P300

To start the analyzer on creates an instance of analyzer.connect.ConnectorProc and calls its run() function.
This will spawn a new process of analyzer.analizer_gui.MainWindow which contains the the control elements.
After one has selected LSL streams for EEG and makers respectively and pressed 'Connect' this spawns two threads,
one receiving samples, the other markers. This data is stored in a shard instance of analyzer.data.RecordedData.
After pressing 'Start Recording' and 'Start Analysis' an instance of analyzer.analysis_thread.AnalysisThread will
be started, which does all the heavy lifting in averaging and classifying the EEG samples.

The current setup is tested with an eego sports by ANT neuro, which has an internal reference subtraction. If this
is not given, one can subtract a channel changing analyzer.data.RecordedData.append_eeg_sample. Examples lines of how
to do this are in there but commented.

"""
