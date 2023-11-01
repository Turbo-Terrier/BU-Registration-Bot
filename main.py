# adapted from https://github.com/juliusfrost/BU-Registration-Bot/blob/master/reg.py
import logging
from getpass import getpass

import util
from configuration import Configurations
from registrar import Registrar, Status


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

    season, year = config.target_semester
    username = config.kerberos_username
    is_planner = config.is_planner
    course_list = config.course_list
    creds = (username, getpass(f'Password for {username} [secure input]: '))

    registrar = Registrar(creds, is_planner, season, year, course_list)
    while registrar.login() != Status.SUCCESS:
        logging.critical('Login failed! Invalid credentials?')
        return 1
    registrar.navigate()
    if registrar.find_courses() == Status.SUCCESS:
        logging.info('Successfully registered for all courses :)')
    return 0


if __name__ == "__main__":
    status = main()
    exit(status)

# TODO: support for switching sections
# TODO: support for 'registering for ONE of these' --- NAH
# TODO: support to query currently registered courses
# TODO: smtp and/or phone message support
# TODO: Dynamic wait interval based on CPU speed
# TODO: Config option for wait duration
# TODO: Config option for browser to use
# TODO: parallelize with max threads option as config, default -1 means auto select
# TODO: switch to helium for speed?
# TODO: only say registered when registration is successful
# TODO: get a list of registered courses and remove them from the list of courses