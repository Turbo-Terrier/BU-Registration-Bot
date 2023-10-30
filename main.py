# adapted from https://github.com/juliusfrost/BU-Registration-Bot/blob/master/reg.py
from getpass import getpass

from configuration import Configurations
from registrar import Registrar, Status

if __name__ == "__main__":

    config = Configurations('./config.yaml')

    season, year = config.get_target_semester()
    username = config.get_kerberos_username()
    is_planner = config.is_planner_mode()
    course_list = config.get_course_list()
    creds = (username, getpass(f'Password for {username} [secure input]: '))

    registrar = Registrar(creds, is_planner, season, year, course_list)
    while registrar.login() != Status.SUCCESS:
        print('Login failed! Invalid credentials?')
        exit(1)
    registrar.navigate()
    if registrar.find_courses() == Status.SUCCESS:
        print('Successfully registered for all courses :)')
    exit(0)
