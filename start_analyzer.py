import matplotlib

matplotlib.use('Qt5Agg')  # MUST BE CALLED BEFORE IMPORTING matplotlib.pyplot

from analyzer.connect import ConnectorProc

main_process = ConnectorProc()
main_process.run()
