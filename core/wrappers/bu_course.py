import time
from typing import Union

from core.wrappers.course_semester import CourseSemester


class BUCourse:
    semester: CourseSemester
    college: str
    dept: str
    course_code: str
    section: str
    added_timestamp: float
    registered_time: Union[None, time]

    def __init__(self, semester: CourseSemester, college: str, dept: str, course_code: str, section: str, added_timestamp: float, registered_timestamp: float = None):
        self.semester = semester
        self.college = college
        self.dept = dept
        self.course_code = course_code
        self.section = section
        self.added_timestamp = added_timestamp
        self.registered_timestamp = registered_timestamp

    def __str__(self):
        return '[' + str(self.semester) + '] ' + self.college.upper() + ' ' + self.dept.upper() + self.course_code + ' ' + self.section.upper()

    def __eq__(self, other):
        if not isinstance(other, BUCourse):
            return False
        return (self.college, self.dept, self.course_code, self.section) == (other.college, other.dept, other.course_code, other.section)

    def __hash__(self):
        return hash((self.college, self.dept, self.course_code, self.section))