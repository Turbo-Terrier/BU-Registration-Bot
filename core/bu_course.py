from typing import Optional

from core.semester import Semester


class BUCourse:
    course_id: int
    semester: Semester
    college: str
    department: str
    course_code: str
    title: Optional[str]
    credits: Optional[int]

    def __init__(self, course_id, semester, college, department, course_code,
                 title=None, credits=None):
        self.course_id = course_id
        self.semester = semester
        self.college = college
        self.department = department
        self.course_code = course_code
        self.title = title
        self.credits = credits

    def __json__(self):
        return {
            "course_id": self.course_id,
            "semester": self.semester.__json__(),
            "college": self.college,
            "department": self.department,
            "course_code": self.course_code,
            "title": self.title,
            "credits": self.credits
        }

    def __str__(self):
        return '[' + str(self.semester) + '] ' + \
            self.college.upper() + ' ' + self.department.upper() + self.course_code

    def __eq__(self, other):
        if not isinstance(other, BUCourse):
            return False
        return self.course_id == other.course_id

    def __hash__(self):
        return hash(self.course_id)

    @staticmethod
    def from_json(json_obj):
        return BUCourse(
            json_obj['course_id'],
            Semester.from_json(json_obj['semester']),
            json_obj['college'],
            json_obj['department'],
            json_obj['course_code'],
            json_obj['title'],
            json_obj['credits']
        )


class CourseSection:
    section: str
    open_seats: Optional[int]
    instructor: Optional[str]
    section_type: Optional[str]
    location: Optional[str]
    schedule: Optional[str]
    dates: Optional[str]
    notes: Optional[str]

    def __init__(self, section, open_seats=None, instructor=None, section_type=None,
                 location=None, schedule=None, dates=None, notes=None):
        self.section = section
        self.open_seats = open_seats
        self.instructor = instructor
        self.section_type = section_type
        self.location = location
        self.schedule = schedule
        self.dates = dates
        self.notes = notes

    def __hash__(self):
        return hash(self.section)

    def __eq__(self, other):
        if not isinstance(other, CourseSection):
            return False
        return self.section == other.section

    def __str__(self):
        return self.section

    def __json__(self):
        return {
            "section": self.section,
            "open_seats": self.open_seats,
            "instructor": self.instructor,
            "section_type": self.section_type,
            "location": self.location,
            "schedule": self.schedule,
            "dates": self.dates,
            "notes": self.notes
        }

    @staticmethod
    def from_json(json_obj):
        return CourseSection(
            json_obj['section'],
            json_obj['open_seats'],
            json_obj['instructor'],
            json_obj['section_type'],
            json_obj['location'],
            json_obj['schedule'],
            json_obj['dates'],
            json_obj['notes']
        )


class BUCourseSection:
    course: BUCourse
    section: CourseSection
    existence_confirmed: bool

    def __init__(self, course, section, existence_confirmed):
        self.course = course
        self.section = section
        self.existence_confirmed = existence_confirmed

    def __json__(self):
        return {
            "course": self.course.__json__(),
            "section": self.section.__json__(),
            "existence_confirmed": self.existence_confirmed
        }

    def __str__(self):
        return str(self.course) + ' ' + str(self.section)

    def __eq__(self, other):
        if not isinstance(other, BUCourseSection):
            return False
        return (self.course, self.section) == (other.course, other.section)

    def __hash__(self):
        return hash((self.course, self.section))

    @staticmethod
    def from_json(json_obj):
        return BUCourseSection(
            BUCourse.from_json(json_obj['course']),
            CourseSection.from_json(json_obj['section']),
            json_obj['existence_confirmed']
        )

    def get_registration_string(self):
        bu_course = self.course
        bu_course_section = self.section
        return bu_course.college + ' ' + \
            bu_course.department + str(bu_course.course_code) + \
            ('S' if bu_course.semester.semester_season.is_summer() else ' ') + \
            bu_course_section.section
