from multiprocessing import freeze_support

from testserver.bcni_data_server import BCNIDataServer

if __name__ == "__main__":
    freeze_support()
    server = BCNIDataServer(1)
    server.start()
