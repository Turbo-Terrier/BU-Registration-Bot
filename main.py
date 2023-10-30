# adapted from https://github.com/juliusfrost/BU-Registration-Bot/blob/master/reg.py
import logging
from getpass import getpass

import util
from configuration import Configurations
from registrar import Registrar, Status


def main() -> int:
    # init the logger
    util.init_logger()

    # load config
    logging.debug('Loading program config...')
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
        logging.debug('Successfully registered for all courses :)')
    return 0


if __name__ == "__main__":
    status = main()
    exit(status)
