import logging
import os.path
import platform
from datetime import datetime
from logging.handlers import TimedRotatingFileHandler
from typing import Tuple

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.remote.webdriver import BaseWebDriver
from selenium.webdriver.common.options import BaseOptions


# 1. Chrome
# 2. Safari
def get_best_browser() -> Tuple[BaseWebDriver.__class__, BaseOptions.__class__]:
    attempt_order = [
        (webdriver.ChromiumEdge, webdriver.ChromeOptions),
        (webdriver.Safari, webdriver.SafariOptions),
        (webdriver.Chrome, webdriver.ChromeOptions),
        (webdriver.Firefox, webdriver.FirefoxOptions),
        (webdriver.WPEWebKit, webdriver.WPEWebKitOptions),
        (webdriver.Ie, webdriver.IeOptions),
    ]
    if get_os() == 'Windows':
        return webdriver.Edge, webdriver.EdgeOptions
    elif get_os() == 'Darwin':
        return webdriver.Safari, webdriver.Safari
    else:
        try:
            service = Service(
                executable_path="/usr/lib/chromium-browser/chromedriver") if platform.system() == "Linux" else Service()
            webdriver.Chrome(service=service)
        except Exception:
            ...

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
    file_handler = TimedRotatingFileHandler(log_filename, when="midnight", interval=1, backupCount=7)
    file_handler.setLevel(logging.INFO)
    file_formatter = logging.Formatter(log_format)
    file_handler.setFormatter(file_formatter)

    # Add handlers to the logger
    logging.basicConfig(level=logging.DEBUG, handlers=[console_handler, file_handler])

