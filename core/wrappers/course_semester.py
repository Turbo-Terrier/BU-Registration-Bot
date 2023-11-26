from datetime import datetime

import pytz

from core.wrappers.course_season import CourseSeason


class CourseSemester:
    season: CourseSeason
    year: int

    def __init__(self, season: CourseSeason, year: int):
        self.season = season
        self.__assert_year(year)
        self.year = year

    @staticmethod
    def __assert_year(year_to_test):
        ny_timezone = pytz.timezone('America/New_York')
        current_time_ny = datetime.now(ny_timezone)
        current_year_ny = current_time_ny.year
        assert year_to_test >= current_year_ny, f"Provided year ({year_to_test}) should be greater than or equal to " \
                                                f"the current year ({current_year_ny}) in 'America/New_York'!"

    def __eq__(self, other):
        if not isinstance(other, CourseSemester):
            return False
        return self.season == other.season and self.year == other.year

    def __hash__(self):
        return hash((self.season, self.year))

    def __str__(self):
        return f"{self.season.name} {self.year}"
