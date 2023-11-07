import logging
import os.path
import platform
from datetime import datetime
from logging.handlers import TimedRotatingFileHandler

from core.logging_formatter import LogColors, CustomFormatter
from selenium import webdriver

def get_logs_dir() -> str:
    return './logs'


def get_os():
    return platform.system()


def get_arch():
    return platform.architecture()[0]


def get_machine():
    return platform.machine()


def get_chrome_options():
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-gpu')
    options.add_argument('enable-automation')
    options.add_argument('--blink-settings=imagesEnabled=false')  # disable image loading to speed stuff up a bit
    return options

def register_logger(debug: bool, colors: bool):
    os.makedirs(get_logs_dir(), exist_ok=True)

    log_format = '[%(asctime)s] [%(levelname)s] %(message)s'
    logging_level = logging.INFO if not debug else logging.DEBUG

    # Create a console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging_level)
    if colors:
        console_handler.setFormatter(CustomFormatter())
    else:
        console_formatter = logging.Formatter(log_format)
        console_handler.setFormatter(console_formatter)

    # Create a file handler that rotates daily
    log_filename = f'./logs/log-{datetime.now().strftime("%Y-%m-%d")}.log'
    file_handler = TimedRotatingFileHandler(log_filename, when="midnight", interval=1, backupCount=0)
    file_handler.setLevel(logging_level)
    file_formatter = logging.Formatter(log_format)
    file_handler.setFormatter(file_formatter)

    # Add handlers to the logger
    logging.basicConfig(level=logging_level, handlers=[console_handler, file_handler])


def color_message(message, color):
    return f'{LogColors.RESET.value}{color.value}{message}{LogColors.RESET.value}'