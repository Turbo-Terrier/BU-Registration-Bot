import logging
import time
import traceback
from getpass import getpass

from selenium import webdriver
from selenium.common import SessionNotCreatedException, NoSuchDriverException
from selenium.webdriver.chrome.service import Service

from core import util
from core.licensing import cloud_util
from core.licensing.cloud_actions import MembershipLevel
from core.registrar import Registrar, Status
from core.semester import Semester, SemesterSeason
from core.util import LogColors
from core.util import color_message


def main() -> int:
    # setup logger
    util.register_logger(False, False)

    license_key = "HNLwtHPCaIufrqAsqpwpOekZscxpgjHDJuKfBtcwdDhyvZEUupscirdggvOrCJgL"

    logging.info("Connecting to the cloud server...")
    # check license
    kerberos_username, config, membership, session_id = cloud_util.check_license_and_start_session(
        license_key
    )

    if config.debug_mode:
        util.register_logger(True, config.console_colors)
        logging.debug("Debug mode has been enabled.")
    else:
        util.register_logger(False, config.console_colors)

    # start the ping task
    # todo: since this is async, it still tries to ping after the app has initiated shutdown
    cloud_util.start_ping_task(license_key, session_id)

    logging.debug("Testing browser drivers by booting up a dummy browser...")
    service = Service(executable_path=config.custom_driver.driver_path) if config.custom_driver.enabled else Service()
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
        return 1
    except NoSuchDriverException:
        logging.critical("It seems you already have Google Chrome installed, however, we were unable to automatically "
                         "detect the path location for the browser drivers needed to launch this application. Try "
                         "manually downloading the chrome drivers from the web and specify the path to "
                         "your browser drivers using the 'driver-path' option in config.yaml. Make sure to download "
                         "the correct drivers for your hardware and operating system.")
        return 1
    except SessionNotCreatedException:
        logging.critical("Error! Browser test failed. You must have Google Chrome installed to use this application.")
        return 1

    logging.info("")
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

    if membership == MembershipLevel.Full:
        logging.info("")
        logging.info(color_message("THANK YOU for purchasing the premium version of this product. Your license "
                                   "is now active!", LogColors.PINK))
        logging.info("")
    elif membership == MembershipLevel.Demo:
        logging.info("")
        logging.info(color_message(" You are using a trial version of this product.", LogColors.LIGHT_RED))
        logging.info(color_message("  * Registration for only a single course allowed.", LogColors.BRIGHT_BLUE))
        logging.info(color_message("  * Checks less frequently for open classes.",
                                   LogColors.BRIGHT_BLUE))
        logging.info(color_message("  * Only limited support offered for issues.",
                                   LogColors.BRIGHT_BLUE))
        # TODO: do I want to restrict max registrations per semesters to 12?
        #  Maybe not and instead just use my statistics to make sure no one is abusing this tool
        logging.info(color_message("Upgrade to the full version of this product for:", LogColors.LIGHT_RED))
        logging.info(color_message("  * Unlimited registrations", LogColors.BRIGHT_BLUE))
        logging.info(color_message("  * Checks for open courses 6x more frequently reducing the chances of missed "
                                   "opportunities...!", LogColors.BRIGHT_BLUE))
        logging.info(color_message("  * Premium Support Offered.", LogColors.BRIGHT_BLUE))
        logging.info("")

        if len(config.target_courses) > 1:
            logging.error("Error! You are using the demo version of this product which only allows "
                          "registration for a single course. However, you have specified more than one course "
                          "to register for. Please either upgrade to the full version or remove all but one "
                          "course from your list of courses in config.yaml to continue.")
            return 1

    elif membership == MembershipLevel.Expired:
        logging.info("")
        logging.info(color_message("Whoops, it looks like you have used your one free "
                                   "course registration. This concludes the trial period"
                                   " of this application.", LogColors.LIGHT_RED))
        logging.info(color_message("In order to continue using this"
                                   " application, please purchase the full version.", LogColors.LIGHT_RED))
        logging.info("")
        logging.info(color_message("Upgrade to the full version of this product for:", LogColors.LIGHT_RED))
        logging.info(color_message("  * Unlimited registrations", LogColors.BRIGHT_BLUE))
        logging.info(color_message("  * Checks for open courses 6x more frequently than the demo version"
                                   " reducing the chances of missed opportunities...!", LogColors.BRIGHT_BLUE))
        logging.info(color_message("  * Premium Support Offered.", LogColors.BRIGHT_BLUE))
        logging.info("")
        return 1
    else:
        logging.info("")
        logging.error("Error! It looks like your license is invalid. Please re-check your license key and try again "
                      "or contact us at the above specified email address for support.")
        return 1

    assert session_id != -1  # should never trigger

    # confirmation
    logging.info(color_message("Based on configured options in", LogColors.BRIGHT_GREEN) +
                 color_message(" 'config.yml' ", LogColors.YELLOW) +
                 color_message("we now begin ", LogColors.BRIGHT_GREEN) +
                 (color_message("PLANNER", LogColors.BACKGROUND_GREEN) if not config.real_registrations
                  else color_message("REAL", LogColors.BACKGROUND_RED)) +
                 color_message(" registrations for...", LogColors.BRIGHT_GREEN))

    for course in config.target_courses:
        logging.info(color_message("  * ", LogColors.BRIGHT_GREEN) + color_message(f"{course}", LogColors.WHITE))

    time.sleep(1)
    input("Press enter to continue...")

    # start main program
    username = kerberos_username
    bu_creds = (username, getpass(f'Password for {username} [won\'t be display on screen]: '))

    registrar = Registrar(license_key, bu_creds, config, session_id, membership)

    try:
        logging.debug(f"Now attempting to login for user {username} with credentials {'*' * len(bu_creds[1])}...")
        if registrar.login() != Status.SUCCESS:
            logging.critical('Login failed! Invalid credentials?')
            registrar.graceful_exit()
            return 1
        time.sleep(3)
        registrar.navigate(semester=Semester(SemesterSeason.Spring, 2024))
        time.sleep(5)
        if registrar.find_courses() == Status.SUCCESS:
            logging.info('Successfully registered for all courses :)')

            registrar.graceful_exit()
            return 0
        else:
            logging.warning(f'Unable to register for {len(config.target_courses)} courses ;(')
            registrar.graceful_exit()
            return 1
    except KeyboardInterrupt as e:
        logging.warning('Program interrupted. Cleaning up and exiting...')
        registrar.graceful_exit()
        return 1
    except Exception:
        logging.error(traceback.format_exc())
        logging.error('Ran into an uncaught error while executing this program. See above stack for more info.')
        registrar.graceful_exit()
        return 1


if __name__ == "__main__":
    status = main()
    exit(status)

# TODO: more debug levels?

# TODO: take out already registered courses
# TODO: if internet goes out, can reconnect with out crashing
# TODO: too many unnecessary logs **
# TODO: support for 'registering for ONE of these' **
# TODO: add support to automatically register as soon as registration starts **
# TODO: support for switching sections **
# TODO: smtp and/or phone message support
# TODO: Setup auto building for multiple OS
# TODO: update checker

# TODO: Config option for browser to use + add more browser support?
