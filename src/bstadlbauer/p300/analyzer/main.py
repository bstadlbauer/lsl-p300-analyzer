from bstadlbauer.p300.analyzer.connect import ConnectorProc


def main():
    import platform
    import multiprocessing

    if platform.system() == "Darwin":
        multiprocessing.set_start_method('spawn')

    main_process = ConnectorProc()
    main_process.run()
