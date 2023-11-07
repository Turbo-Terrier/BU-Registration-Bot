import logging
import traceback
from getpass import getpass
from selenium import webdriver
from selenium.common import SessionNotCreatedException, NoSuchDriverException
from selenium.webdriver.chrome.service import Service

from core import util
from core.configuration import Configurations
from core.registrar import Registrar, Status
from core.util import LogColors
from core.util import color_message


def main() -> int:
    # setup logger
    util.register_logger(False, False)

    # load config
    try:
        config = Configurations('./config.yaml')
    except SyntaxError as e:
        logging.critical(e)
        return 1

    if config.is_debug_mode:
        util.register_logger(True, config.is_console_colored)
        logging.debug("Debug mode has been enabled.")
    else:
        util.register_logger(False, config.is_console_colored)

    logging.debug("Testing browser drivers by booting up a dummy browser...")
    service = Service() if config.driver_path == '' else Service(executable_path=config.driver_path)
    logging.debug(f"Initializing dummy browser service with service_url={service.service_url} path={service.path}...")
    try:
        dummy_driver = webdriver.Chrome(options=util.get_chrome_options(), service=service)
        logging.debug("Successfully loaded chrome drivers! Exiting dummy browser.")
        dummy_driver.close()
        dummy_driver.quit()
    except OSError:
        logging.critical(traceback.format_exc())
        logging.critical(f"Unable to launch chrome drivers due to an OS Error. Do you have the correct drivers? "
                         f"Read above stack dump for more info.")
        exit(1)
    except NoSuchDriverException:
        logging.critical("It seems you already have Google Chrome installed, however, we were unable to automatically "
                         "detect the path location for the browser drivers needed to launch this application. Try "
                         "manually downloading the chrome drivers from the web and specify the path to "
                         "your browser drivers using the 'driver-path' option in config.yaml. Make sure to download "
                         "the correct drivers for your hardware and operating system.")
        exit(1)
    except SessionNotCreatedException:
        logging.critical("Error! Browser test failed. You must have Google Chrome installed to use this application.")
        exit(1)

    logging.debug("Initializing the actual application...")

    logging.info(color_message("##############################################", LogColors.CYAN))
    logging.info(color_message("##", LogColors.CYAN) +
                 color_message("    Welcome to the BU Registration Bot    ", LogColors.YELLOW) +
                 color_message("##", LogColors.CYAN))
    logging.info(color_message("##", LogColors.CYAN) +
                 color_message("       Created By: contact@aseef.dev      ", LogColors.LIGHT_GRAY) +
                 color_message("##", LogColors.CYAN))
    logging.info(color_message("##                                          ##", LogColors.CYAN))
    logging.info(color_message("##", LogColors.CYAN) +
                 color_message("           Version  0.1.0-BETA            ", LogColors.GRAY) +
                 color_message("##", LogColors.CYAN))
    logging.info(color_message("##############################################", LogColors.CYAN))
    logging.info("")

    premium = True  # TODO Finish Licensing System
    if premium:
        logging.info(color_message("THANK YOU for purchasing the premium version of this product. Your license "
                                   "is now active!", LogColors.PINK))
        logging.info()
    else:
        logging.info(color_message(" You are using a trial version of this product.", LogColors.LIGHT_RED))
        logging.info(color_message("  * Registration for only a single course allowed.", LogColors.BRIGHT_BLUE))
        logging.info(color_message("  * Checks less frequently for open classes.",
                                   LogColors.BRIGHT_BLUE))
        logging.info(color_message("  * Only limited support offered for issues.",
                                   LogColors.BRIGHT_BLUE))
        logging.info(color_message("Upgrade to the full version of this product for:", LogColors.LIGHT_RED))
        # TODO: do I want to restrict max registrations per semesters to 12?
        #  Maybe not and instead just use my statistics to make sure no one is abusing this tool
        logging.info(color_message("  * Unlimited registrations (up to 12 per semester)", LogColors.BRIGHT_BLUE))
        logging.info(color_message("  * Checks for open courses 6x more frequently reducing the chances of missed "
                                   "opportunities...!", LogColors.BRIGHT_BLUE))
        logging.info(color_message("  * Premium Support Offered.", LogColors.BRIGHT_BLUE))
        logging.info(color_message("If you have already purchased a license, make sure to put the license key into ",
                                   LogColors.LIGHT_RED) +
                     color_message("'config.yml'", LogColors.YELLOW) + color_message("!", LogColors.LIGHT_RED))
        logging.info("")

    logging.info(color_message("Based on configured options in", LogColors.BRIGHT_GREEN) +
                 color_message(" 'config.yml' ", LogColors.YELLOW) +
                 color_message("we now begin", LogColors.BRIGHT_GREEN) +
                 color_message(" PLANNER " if config.is_planner else " REAL ", LogColors.CYAN) +
                 color_message("registrations for...", LogColors.BRIGHT_GREEN))
    for course in config.course_list:
        logging.info(color_message("  * ", LogColors.BRIGHT_GREEN) + color_message(f"{course}", LogColors.WHITE))

    input("Press enter to continue...")

    username = config.kerberos_username
    creds = (username, getpass(f'Password for {username} [won\'t be display on screen]: '))

    registrar = Registrar(creds, config, premium)

    try:
        logging.debug(f"Now attempting to login for user {username} with credentials {'*' * len(creds[1])}...")
        if registrar.login() != Status.SUCCESS:
            logging.critical('Login failed! Invalid credentials?')
            return 1
        registrar.navigate()
        if registrar.find_courses() == Status.SUCCESS:
            logging.info('Successfully registered for all courses :)')
            return 0
        else:
            logging.warning(f'Unable to register for {len(config.course_list)} courses ;(')
            return 1
    except KeyboardInterrupt as e:
        logging.warning('Program interrupted. Cleaning up and exiting...')
    except Exception:
        logging.error(traceback.format_exc())
        logging.error('Ran into an uncaught error while executing this program. See above stack for more info.')
    finally:
        registrar.graceful_exit()
        return 1


if __name__ == "__main__":
    status = main()
    exit(status)

# TODO: too many unnecessary logs
# TODO: support for 'registering for ONE of these' **
# TODO: add support to automatically register as soon as registration starts **
# TODO: support for switching sections **
# TODO: smtp and/or phone message support
# TODO: finish licensing
# TODO: update checker

# TODO: Config option for browser to use + add more browser support?
