from typing import List, Tuple, Union

from core.wrappers.bu_course import BUCourse
from core.wrappers.course_semester import CourseSemester


class ProfileConfig:
    profile_id: int
    license_key: str
    kerberos_username: str
    is_planner: bool
    driver_path: str
    should_ignore_non_existent_courses: bool
    is_save_password: bool
    is_save_duo_cookies: bool
    is_debug_mode: bool

    def __init__(
            self,
            profile_id: Union[int, None],
            license_key: str,
            kerberos_username: str,
            is_planner: bool,
            driver_path: str,
            should_ignore_non_existent_courses: bool,
            is_save_password: bool,
            is_save_duo_cookies: bool,
            is_debug_mode: bool,
    ):
        self.profile_id = profile_id
        self.license_key = license_key
        self.kerberos_username = kerberos_username
        self.is_planner = is_planner
        self.driver_path = driver_path
        self.should_ignore_non_existent_courses = should_ignore_non_existent_courses
        self.is_save_password = is_save_password
        self.is_save_duo_cookies = is_save_duo_cookies
        self.is_debug_mode = is_debug_mode
