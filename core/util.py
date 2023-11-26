import codecs
import logging
import os.path
import pickle
import platform
import traceback
from datetime import datetime
from logging.handlers import TimedRotatingFileHandler
from typing import Any

from selenium.common import NoSuchDriverException, SessionNotCreatedException
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.webdriver import WebDriver

from core.logging_formatter import LogColors, CustomFormatter
from selenium import webdriver

from core.wrappers.status import Status


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


def dump_to_bytes(obj: Any) -> bytes:
    return codecs.encode(pickle.dumps(obj), "base64")


def load_picked_obj(obj: bytes) -> Any:
    return pickle.loads(codecs.decode(obj, "base64"))

def test_drivers(driver_path='') -> Status:
    """
    :param driver_path: The chrome driver path

    :return: Returns Status.ERROR if chrome isn't installed. Returns
    Status.FAILURE if chrome is installed but we are unable to locate chrome drivers. And Returns Status.SUCCESS if
    everything is working fine.
    """
    logging.debug("Testing browser drivers by booting up a dummy browser...")
    service = Service() if driver_path == '' else Service(executable_path=driver_path)
    logging.debug(f"Initializing dummy browser service with service_url={service.service_url} path={service.path}...")
    try:
        dummy_driver = webdriver.Chrome(options=get_chrome_options(), service=service)
        logging.debug("Successfully loaded chrome drivers! Exiting dummy browser.")
        dummy_driver.close()
        dummy_driver.quit()
        return Status.SUCCESS
    except OSError:
        logging.critical(traceback.format_exc())
        logging.critical(f"Unable to launch chrome drivers due to an OS Error. Do you have the correct drivers? "
                         f"Read above stack dump for more info.")
        return Status.FAILURE
    except NoSuchDriverException:
        logging.critical("It seems you already have Google Chrome installed, however, we were unable to automatically "
                         "detect the path location for the browser drivers needed to launch this application. Try "
                         "manually downloading the chrome drivers from the web and specify the path to "
                         "your browser drivers using the 'driver-path' option in config.yaml. Make sure to download "
                         "the correct drivers for your hardware and operating system.")
        return Status.FAILURE
    except SessionNotCreatedException:
        logging.critical("Error! Browser test failed. You must have Google Chrome installed to use this application.")
        return Status.ERROR
