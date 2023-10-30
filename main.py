# adapted from https://github.com/juliusfrost/BU-Registration-Bot/blob/master/reg.py
from getpass import getpass

import util
from configuration import Configurations
from registrar import Registrar, Status


def main() -> int:

    # create our logger
    #TODO

    # first we download chrome drivers
    if not util.get_chrome_driver():
        print('Error! Unable to find a valid chrome driver for your system.')
        return 1

    config = Configurations('./config.yaml')

    season, year = config.get_target_semester()
    username = config.get_kerberos_username()
    is_planner = config.is_planner_mode()
    course_list = config.get_course_list()
    creds = (username, getpass(f'Password for {username} [secure input]: '))

    registrar = Registrar(creds, is_planner, season, year, course_list)
    while registrar.login() != Status.SUCCESS:
        print('Login failed! Invalid credentials?')
        return 1
    registrar.navigate()
    if registrar.find_courses() == Status.SUCCESS:
        print('Successfully registered for all courses :)')
    return 0


if __name__ == "__main__":
    status = main()
    exit(status)
