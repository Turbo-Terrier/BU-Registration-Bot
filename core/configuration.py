import os.path
import re
from typing import Tuple, List, Set

import yaml

from core.bu_course import BUCourse


class Configurations:
    is_planner: bool
    kerberos_username: str
    target_semester: Tuple[str, int]
    course_list = List[BUCourse]
    driver_path: str
    should_ignore_non_existent_courses: bool
    license_key: str
    is_debug_mode: bool
    is_console_colored: bool
    is_never_give_up: bool

    def __init__(self, config_path):
        with open(config_path, 'r') as config:
            self.config = yaml.safe_load(config)
        self.is_planner = self.__load_planner()
        self.kerberos_username = self.__load_kerberos_username()
        self.target_semester = self.__load_target_semester()
        self.course_list = self.__load_course_list()
        self.driver_path = self.__load_driver_path()
        self.should_ignore_non_existent_courses = self.__load_should_ignore_non_existent_courses()
        self.license_key = self.__load_license_key()
        self.is_debug_mode = self.__load_is_debug_mode()
        self.is_console_colored = self.__load_is_console_colored()
        self.is_never_give_up = self.__load_is_never_give_up()

    def __load_planner(self) -> bool:
        planner_mode: bool = self.config['planner-mode']
        if not isinstance(planner_mode, bool):
            raise SyntaxError(F"Error! The \"planner-mode\" option must be a boolean (a True or False value with no "
                              F"quotes). However, got, \"{planner_mode}\", which cannot be resolved to a boolean.")
        return planner_mode

    def __load_kerberos_username(self) -> str:
        username: str = self.config['kerberos-user']
        alphanumerical = re.compile('[a-zA-Z0-9_]+')
        if alphanumerical.match(username) is None:
            raise SyntaxError(F'Error! The Kerberos username should be an alphanumeral but is instead {username}!')
        else:
            return username

    def __load_target_semester(self) -> Tuple[str, int]:
        target_semester: str = self.config['target-semester']
        semester_pattern = re.compile('(Fall|Summer1|Summer2|Spring) [0-9]{4}', re.RegexFlag.IGNORECASE)
        if semester_pattern.match(target_semester) is None:
            raise SyntaxError(F"Error! \'{target_semester}\' is not a valid semester!")
        splits = target_semester.split(' ')
        return splits[0].lower(), int(splits[1])

    def __load_course_list(self) -> Set[BUCourse]:
        courses: List[str] = self.config['course-list']
        # [School] [Department] [Course Number] [Section]
        course_pattern = re.compile('[a-zA-Z]{3} [a-zA-Z]{2,4} [0-9]{3} [A-Z][0-9]')

        failures: List[str] = []
        bu_courses: List[BUCourse] = []
        for course in courses:
            if course_pattern.match(course) is None:
                failures += [F"'{course}' is not in the correct format. Example entry: CAS CS 111 A1"]
            else:
                split = course.split(' ')
                bu_courses += [BUCourse(split[0], split[1], split[2], split[3])]
        if len(failures) > 0:
            raise SyntaxError('Error(s): ' + ', '.join(failures))

        if len(bu_courses) == 0:
            raise SyntaxError('Error! No courses were specified. I don\'t know what to register for!')

        if len(bu_courses) > 10:
            raise SyntaxError('Error! To prevent abuse, are not allowed to use this bot to attempt to register '
                              'for more than 10 courses at once.')

        return set(bu_courses)

    def __load_driver_path(self) -> str:
        driver_path: str = self.config['driver-path']
        if driver_path == '':
            return driver_path

        if not os.path.exists(driver_path):
            raise SyntaxError(f'Error! No file exists at your specified driver path ({driver_path}).')

        return driver_path

    def __load_should_ignore_non_existent_courses(self) -> bool:
        ignore_non_existent_courses: bool = self.config['ignore-non-existent-courses']
        if not isinstance(ignore_non_existent_courses, bool):
            raise SyntaxError(F"Error! The \"ignore-non-existent-courses\" option must be a boolean (a True or False "
                              F"value with no quotes). However, got, \"{ignore_non_existent_courses}\", which cannot "
                              F"be resolved to a boolean.")
        return ignore_non_existent_courses

    def __load_license_key(self) -> str:
        license_key: str = self.config['license-key']
        return license_key

    def __load_is_debug_mode(self) -> bool:
        is_debug_mode: bool = self.config['debug']
        if not isinstance(is_debug_mode, bool):
            raise SyntaxError(F"Error! The \"debug\" option must be a boolean (a True or False value with no quotes). "
                              F"However, got, \"{is_debug_mode}\", which cannot be resolved to a boolean.")
        return is_debug_mode

    def __load_is_console_colored(self) -> bool:
        is_console_colored: bool = self.config['console-colors']
        if not isinstance(is_console_colored, bool):
            raise SyntaxError(F"Error! The \"console-color\" option must be a boolean (a True or False value with no "
                              F"quotes). However, got, \"{is_console_colored}\", which cannot be resolved to a boolean.")
        return is_console_colored

    def __load_is_never_give_up(self) -> bool:
        never_give_up: bool = self.config['never-give-up']
        if not isinstance(never_give_up, bool):
            raise SyntaxError(F"Error! The \"never-give-up\" option must be a boolean (a True or False value with no "
                              F"quotes). However, got, \"{never_give_up}\", which cannot be resolved to a boolean.")
        return never_give_up