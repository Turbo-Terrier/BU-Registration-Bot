import logging
import sys
import traceback
from getpass import getpass

from core import util
from core.database import BotDatabase
from core.profile_manager import ProfileManager
from core.registrar import Registrar, Status
from core.util import LogColors
from core.util import color_message


def main() -> int:
    # setup logger
    util.register_logger(False, sys.stdout.isatty())

    # make sure chrome is installed before doing anything else
    if util.test_drivers() == Status.ERROR:
        return 1

    # load DB
    logging.info("Loading database...")
    BotDatabase.init('./bot_data.db')

    # load profile
    ProfileManager.init()
    if len(ProfileManager.get_available_profiles()) == 0:
        logging.info("First startup detected. Initializing program settings.")
        # create new profile
        profile_config = ProfileManager.init_profile_creation_console()
        profile_config = ProfileManager.add_profile(profile_config)
        # TODO: add something to edit the profile
    else:
        profile_config = ProfileManager.get_profile(0)
        ProfileManager.set_current_profile(0)

    # load course list
    # TODO

    if profile_config.is_debug_mode:
        logging.debug("Debug mode has been enabled.")

    logging.info(color_message("##############################################", LogColors.CYAN))
    logging.info(color_message("##", LogColors.CYAN) +
                 color_message("    Welcome to the BU Registration Bot    ", LogColors.YELLOW) +
                 color_message("##", LogColors.CYAN))
    logging.info(color_message("##", LogColors.CYAN) +
                 color_message("       Created By: contact@aseef.dev      ", LogColors.LIGHT_GRAY) +
                 color_message("##", LogColors.CYAN))
    logging.info(color_message("##                                          ##", LogColors.CYAN))
    logging.info(color_message("##", LogColors.CYAN) +
                 color_message("           Version  0.2.0-BETA            ", LogColors.GRAY) +
                 color_message("##", LogColors.CYAN))
    logging.info(color_message("##############################################", LogColors.CYAN))
    logging.info("")

    premium = True  # TODO Finish Licensing System
    if premium:
        logging.info(color_message("THANK YOU for purchasing the premium version of this product. Your license "
                                   "is now active!", LogColors.PINK))
        logging.info("")
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
                 color_message("we now begin ", LogColors.BRIGHT_GREEN) +
                 (color_message("PLANNER", LogColors.BACKGROUND_GREEN) if profile_config.is_planner else color_message("REAL", LogColors.BACKGROUND_RED)) +
                 color_message(" registrations for...", LogColors.BRIGHT_GREEN))

    for course in config.course_list:
        logging.info(color_message("  * ", LogColors.BRIGHT_GREEN) + color_message(f"{course}", LogColors.WHITE))

    input("Press enter to continue...")

    username = profile_config.kerberos_username
    creds = (username, getpass(f'Password for {username} [won\'t be display on screen]: '))

    registrar = Registrar(creds, profile_config, premium)

    try:
        logging.debug(f"Now attempting to login for user {username} with credentials {'*' * len(creds[1])}...")
        if registrar.login() != Status.SUCCESS:
            logging.critical('Login failed! Invalid credentials?')
            registrar.graceful_exit()
            return 1
        registrar.navigate()
        if registrar.find_courses() == Status.SUCCESS:
            logging.info('Successfully registered for all courses :)')
            registrar.graceful_exit()
            return 0
        else:
            logging.warning(f'Unable to register for {len(config.course_list)} courses ;(')
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
        # TODO: smtp email here to inform about the crash
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
# TODO: if no config exists, pull it from "the source of truth" on aseef.dev
# TODO: finish licensing
# TODO: update checker

# TODO: Config option for browser to use + add more browser support?
