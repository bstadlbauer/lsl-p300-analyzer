if __name__ == '__main__':
    import platform
    import multiprocessing

    if platform.system() == "Darwin":
        multiprocessing.set_start_method('spawn')

from multiprocessing import freeze_support


import matplotlib

matplotlib.use('Qt5Agg')  # MUST BE CALLED BEFORE IMPORTING matplotlib.pyplot

from analyzer.connect import ConnectorProc


if __name__ == '__main__':
    freeze_support()
    main_process = ConnectorProc()
    main_process.run()
