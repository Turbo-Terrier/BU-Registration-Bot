import logging
import traceback
from getpass import getpass

from core import util
from core.configuration import Configurations
from core.registrar import Registrar, Status


def main() -> int:
    # setup logger
    util.create_logger()

    # load config
    logging.info('Loading program config...')
    try:
        config = Configurations('./config.yaml')
    except SyntaxError as e:
        logging.critical(e)
        return 1

    username = config.kerberos_username
    creds = (username, getpass(f'Password for {username} [secure input]: '))

    registrar = Registrar(creds, config)

    try:
        while registrar.login() != Status.SUCCESS:
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

# TODO: get a list of registered courses and remove them from the list of courses
# TODO: support for switching sections
# TODO: support for 'registering for ONE of these'
# TODO: support to query currently registered courses
# TODO: smtp and/or phone message support
# TODO: Config option for wait duration
# TODO: Config option for browser to use + add more browser support
# TODO: switch to helium for speed?
# TODO: add support to automatically register as soon as registration starts