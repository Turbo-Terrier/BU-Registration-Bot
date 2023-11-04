class BUCourse:
    college: str
    dept: str
    course_code: str
    section: str

    def __init__(self, college: str, dept: str, course_code: str, section: str):
        self.college = college
        self.dept = dept
        self.course_code = course_code
        self.section = section

    def __str__(self):
        return self.college.upper() + ' ' + self.dept.upper() + self.course_code + ' ' + self.section.upper()

    def __eq__(self, other):
        if not isinstance(other, BUCourse):
            return False
        return (self.college, self.dept, self.course_code, self.section) == (other.college, other.dept, other.course_code, other.section)

    def __hash__(self):
        return hash((self.college, self.dept, self.course_code, self.section))