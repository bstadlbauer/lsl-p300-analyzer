from bstadlbauer.p300analyzer.connect import ConnectorProc


def main():
    import multiprocessing
    import platform

    if platform.system() == "Darwin":
        multiprocessing.set_start_method("spawn")

    main_process = ConnectorProc()
    main_process.run()
