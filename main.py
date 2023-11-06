import logging
import traceback
from getpass import getpass

from core import util
from core.configuration import Configurations
from core.registrar import Registrar, Status
from core.util import LogColors


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

    logging.info(util.color_message("##############################################", LogColors.CYAN))
    logging.info(util.color_message("##", LogColors.CYAN) +
                 util.color_message("    Welcome to the BU Registration Bot    ", LogColors.YELLOW) +
                 util.color_message("##", LogColors.CYAN))
    logging.info(util.color_message("##", LogColors.CYAN) +
                 util.color_message("       Created By: contact@aseef.dev      ", LogColors.LIGHT_GRAY) +
                 util.color_message("##", LogColors.CYAN))
    logging.info(util.color_message("##                                          ##", LogColors.CYAN))
    logging.info(util.color_message("##", LogColors.CYAN) +
                 util.color_message("           Version  0.1.0-BETA            ", LogColors.GRAY) +
                 util.color_message("##", LogColors.CYAN))
    logging.info(util.color_message("##############################################", LogColors.CYAN))
    logging.info("")

    if False:  # TODO Finish Licensing
        logging.info(util.color_message("THANK YOU for purchasing the premium version of this product. Your license "
                                        "is now active!", LogColors.PURPLE))
    else:
        logging.info(util.color_message(" You are using a trial version of this product.", LogColors.LIGHT_RED))
        logging.info(util.color_message("  * Registration for only a single course allowed.", LogColors.BRIGHT_BLUE))
        logging.info(util.color_message("  * Checks less frequently for open classes (10 requests / min).",
                                        LogColors.BRIGHT_BLUE))
        logging.info(util.color_message("  * Only limited support offered for issues.",
                                        LogColors.BRIGHT_BLUE))
        logging.info(util.color_message("Upgrade to the full version of this product for:", LogColors.LIGHT_RED))
        logging.info(util.color_message("  * Unlimited registrations (up to 10 at a time)", LogColors.BRIGHT_BLUE))
        logging.info(
            util.color_message("  * x9 Faster checks for open class (90 requests / min)", LogColors.BRIGHT_BLUE))
        logging.info(util.color_message("  * Premium Support Offered", LogColors.BRIGHT_BLUE))
        logging.info("")

    input("Press enter to continue...")

    username = config.kerberos_username
    creds = (username, getpass(f'Password for {username} [won\'t be display on screen]: '))

    registrar = Registrar(creds, config)

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
        logging.warning('Script interrupted. Cleaning up and exiting...')
        traceback.print_exc()
    finally:
        registrar.graceful_exit()
        return 1


if __name__ == "__main__":
    status = main()
    exit(status)

# TODO: support for 'registering for ONE of these' **
# TODO: add support to automatically register as soon as registration starts **
# TODO: support for switching sections **
# TODO: smtp and/or phone message support
# TODO: finish licensing
# TODO: update checker

# TODO: Config option for browser to use + add more browser support?
