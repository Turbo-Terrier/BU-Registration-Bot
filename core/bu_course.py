from core.semester import Semester


class BUCourse:
    semester: Semester
    college: str
    department: str
    course_code: int
    section: str

    def __init__(self, semester: Semester, college: str, dept: str, course_code: int, section: str):
        self.semester = semester
        self.college = college
        self.department = dept
        self.course_code = course_code
        self.section = section

    def __json__(self):
        return {
            "semester": self.semester.__json__(),
            "college": self.college,
            "department": self.department,
            "course_code": self.course_code,
            "section": self.section
        }

    def __str__(self):
        return self.college.upper() + ' ' + self.department.upper() + str(self.course_code) + ' ' + self.section.upper() \
            + ' [' + str(self.semester) + ']'

    def __eq__(self, other):
        if not isinstance(other, BUCourse):
            return False
        return (self.semester, self.college, self.department, self.course_code, self.section) == (
            other.semester, other.college, other.department, other.course_code, other.section)

    def __hash__(self):
        return hash((self.semester, self.college, self.department, self.course_code, self.section))
