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

"""
Get the logger for this bot
"""
def get_logger():
    return logger


def __create_logger():
    os.makedirs(get_logs_dir(), exist_ok=True)
    # first we init our logging system
    # Create a logger

    logger = logging.getLogger("registration-bot")
    logger.setLevel(logging.DEBUG)

    log_format = '[%(asctime)s] [%(levelname)s]  %(message)s'

    # Create a console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)  # Adjust the log level as needed
    console_formatter = logging.Formatter(log_format)
    console_handler.setFormatter(console_formatter)

    # Create a file handler that rotates daily
    log_filename = f'./logs/log-{datetime.now().strftime("%Y-%m-%d")}.log'
    file_handler = TimedRotatingFileHandler(log_filename, when="midnight", interval=1, backupCount=7)
    file_handler.setLevel(logging.DEBUG)
    file_formatter = logging.Formatter(log_format)
    file_handler.setFormatter(file_formatter)

    # Add handlers to the logger
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)

    return logger


logger = __create_logger()
