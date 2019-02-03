import matplotlib

from analyzer.testserver import BCNIDataServer

matplotlib.use('Qt4Agg')  # MUST BE CALLED BEFORE IMPORTING plt

test_server = BCNIDataServer("s1.mat")
test_server.daemon = True
test_server.start()

from analyzer.connect import ConnectorProc

main_process = ConnectorProc()
main_process.run()

# from analyzer.analizer_gui import MainWindow
# import multiprocessing as mp
#
# main_window = MainWindow(mp.Manager().dict(), mp.Queue(), mp.Event(), mp.Event(), mp.Event(), mp.Event())
# main_window.start()
#
# input('test')
