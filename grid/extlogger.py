import logging
import time
from os import makedirs
from os.path import dirname, join, basename


class LogCat:
    def __init__(self, file):
        self.file = file
        self.path = dirname(self.file)
        self.filename: str = str(basename(self.file)).split('.')[0]
        self.directory = self.filename + "Logs"
        self.today = time.strftime("%a %b %d %Y")
        self.fullpath = join(self.path, self.directory, self.today)
        makedirs(self.fullpath, exist_ok=True)
        self.formatter = logging.Formatter('|%(asctime)s.%(msecs)03d| (%(levelname)-8s)\
         [%(funcName)s] %(message)s', '%H:%M:%S')

    def get_logger(self, name, log_file: str, formatter=None, level=logging.DEBUG):
        formatter = self.formatter if not formatter else formatter
        log_file: str = log_file.replace(" ", "_")
        handler = logging.FileHandler(join(self.fullpath, log_file))
        handler.setFormatter(formatter)

        logger = logging.getLogger(name)
        logger.setLevel(level)
        logger.addHandler(handler)

        return logger
