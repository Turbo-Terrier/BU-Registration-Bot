import logging
import os.path
import platform
from datetime import datetime
from logging.handlers import TimedRotatingFileHandler

def get_logs_dir() -> str:
    return './logs'


def get_os():
    return platform.system()


def get_arch():
    return platform.architecture()[0]


def get_machine():
    return platform.machine()


def create_logger():
    os.makedirs(get_logs_dir(), exist_ok=True)

    log_format = '[%(asctime)s] [%(levelname)s] %(message)s'

    # Create a console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_formatter = logging.Formatter(log_format)
    console_handler.setFormatter(console_formatter)

    # Create a file handler that rotates daily
    log_filename = f'./logs/log-{datetime.now().strftime("%Y-%m-%d")}.log'
    file_handler = TimedRotatingFileHandler(log_filename, when="midnight", interval=1, backupCount=0)
    file_handler.setLevel(logging.INFO)
    file_formatter = logging.Formatter(log_format)
    file_handler.setFormatter(file_formatter)

    # Add handlers to the logger
    logging.basicConfig(level=logging.INFO, handlers=[console_handler, file_handler])

