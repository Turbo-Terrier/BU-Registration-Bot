import re
from typing import Tuple, List

import yaml


class Configurations:
    def __init__(self, config_path):
        with open(config_path, 'r') as config:
            self.config = yaml.safe_load(config)

    def is_planner_mode(self) -> bool:
        planner_mode: bool = self.config['planner-mode']
        return planner_mode

    def get_kerberos_username(self) -> str:
        username: str = self.config['kerberos-user']
        alphanumerical = re.compile('[a-zA-Z0-9_]+')
        if alphanumerical.match(username) is None:
            raise SyntaxError(F'Error! The Kerberos username should be an alphanumeral but is instead {username}!')
        else:
            return username

    def get_target_semester(self) -> Tuple[str, int]:
        target_semester: str = self.config['target-semester']
        semester_pattern = re.compile('(Fall|Summer1|Summer2|Spring) [0-9]{4}', re.RegexFlag.IGNORECASE)
        if semester_pattern.match(target_semester) is None:
            raise SyntaxError(F"Error! \'{target_semester}\' is not a valid semester!")
        splits = target_semester.split(' ')
        return splits[0].lower(), int(splits[1])

    def get_course_list(self) -> List[Tuple[str, str, str, str]]:
        courses: List[str] = self.config['course-list']
        # [School] [Department] [Course Number] [Section]
        course_pattern = re.compile('[a-zA-Z]{3} [a-zA-Z]{2,4} [0-9]{3} [A-Z][0-9]')

        failures: List[str] = []
        course_tuples: List[Tuple[str, str, str, str]] = []
        for course in courses:
            if course_pattern.match(course) is None:
                failures += [F"'{course}' is not in the correct format. Example entry: CAS CS 111 A1"]
            else:
                split = course.split(' ')
                course_tuples += [split[0], split[1], split[2], split[3]]
        if len(failures) > 0:
            raise SyntaxError('Error(s): ' + ', '.join(failures))

        return course_tuples
