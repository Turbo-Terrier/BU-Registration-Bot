import logging
import os.path
import platform
import zipfile
from io import BytesIO
from logging.handlers import TimedRotatingFileHandler
from typing import Union

import requests


# TODO:
def create_logger():
    os.makedirs(get_logs_dir(), exist_ok=True)
    # first we init our logging system
    # Create a logger

    logger = logging.getLogger("registration-bot")
    logger.setLevel(logging.DEBUG)

    # Create a TimedRotatingFileHandler to rotate logs daily
    log_file_handler = TimedRotatingFileHandler(F"{get_logs_dir()}/log", when="midnight", interval=1, backupCount=7)
    log_file_handler.suffix = "-%Y-%m-%d.long"
    log_file_handler.extMatch = r"^\d{4}-\d{2}-\d{2}$"

    # Create a formatter
    formatter = logging.Formatter('[%(asctime)s] [%(name)s] [%(levelname)s]  %(message)s')
    log_file_handler.setFormatter(formatter)

    return logger


def get_logs_dir() -> str:
    return './logs'


def get_driver_path() -> str:
    return F"{get_driver_dir()}/{get_drive_file_name()}"


def get_drive_file_name() -> str:
    return F"chromedriver{'.exe' if get_os().lower() == 'windows' else ''}"


def get_driver_dir() -> str:
    return './chromedriver'


def get_chrome_driver() -> bool:
    os.makedirs(get_driver_dir(), exist_ok=True)
    if os.path.exists(get_driver_path()):
        return True

    target_platform = __get_driver_platform()
    # if we failed to get the target platform
    if target_platform is None:
        return False

    download_url = F"https://github.com/electron/electron/releases/download/v26.4.2/chromedriver-v26.4.2-{target_platform}.zip"
    print(f'Downloading Chrome drivers for platform {target_platform} from {download_url}... This may take a second.')

    driver_download = requests.get(download_url)
    zip_data = BytesIO(driver_download.content)
    with zipfile.ZipFile(zip_data, 'r') as zip_ref:
        for file in zip_ref.filelist:
            if not file.filename.endswith(get_drive_file_name()):
                continue
            file_to_extract = file.filename
            with zip_ref.open(file_to_extract) as file:
                file_data = file.read()
                # Save the specific file to the save directory
                with open(get_driver_path(), 'wb') as output_file:
                    output_file.write(file_data)
    os.chmod(get_driver_path(), 0o755)
    print(f'Chrome Driver successfully saved in {get_driver_path()}!')

    return True


def __get_driver_platform() -> Union[None, str]:
    chrome_driver_platform = None
    system = get_os()
    machine = get_machine()

    if system == "Darwin" and machine == "arm64":
        chrome_driver_platform = "darwin-arm64"
    elif system == "Darwin" and machine == "x86_64":
        chrome_driver_platform = "darwin-x64"
    elif system == "Linux" and machine == "aarch64":
        chrome_driver_platform = "linux-arm64"
    elif system == "Linux" and machine == "armv7l":
        chrome_driver_platform = "linux-armv7l"
    elif system == "Linux" and "64" in machine:
        chrome_driver_platform = "linux-x64"
    elif system == "Darwin" and machine == "arm64":
        chrome_driver_platform = "mas-arm64"
    elif system == "Darwin" and machine == "x86_64":
        chrome_driver_platform = "mas-x64"
    elif system == "Windows" and machine == "AMD64":
        chrome_driver_platform = "win32-x64"
    elif system == "Windows" and "32" in machine:
        chrome_driver_platform = "win32-ia32"
    elif system == "Windows" and "64" in machine:
        chrome_driver_platform = "win32-x64"

    return chrome_driver_platform


def get_os():
    return platform.system()


def get_arch():
    return platform.architecture()[0]


def get_machine():
    return platform.machine()
