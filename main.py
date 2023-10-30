# adapted from https://github.com/juliusfrost/BU-Registration-Bot/blob/master/reg.py
from getpass import getpass

import util
from configuration import Configurations
from registrar import Registrar, Status


def main() -> int:
    # get logger
    logger = util.get_logger()

    # load config
    try:
        config = Configurations('./config.yaml')
    except SyntaxError as e:
        logger.critical(e)
        return 1

    season, year = config.target_semester
    username = config.kerberos_username
    is_planner = config.is_planner
    course_list = config.course_list
    creds = (username, getpass(f'Password for {username} [secure input]: '))

    registrar = Registrar(creds, is_planner, season, year, course_list)
    while registrar.login() != Status.SUCCESS:
        logger.critical('Login failed! Invalid credentials?')
        return 1
    registrar.navigate()
    if registrar.find_courses() == Status.SUCCESS:
        logger.debug('Successfully registered for all courses :)')
    return 0


if __name__ == "__main__":
    status = main()
    exit(status)
