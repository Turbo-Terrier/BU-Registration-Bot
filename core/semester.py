from enum import Enum


class SemesterSeason(Enum):
    # self note: these numbers are important and are the way
    # BU identifies each semester with
    Summer1 = 1,
    Summer2 = 2,
    Fall = 3
    Spring = 4,

    def is_summer(self):
        return self == SemesterSeason.Summer1 or self == SemesterSeason.Summer2


class Semester:
    semester_season: SemesterSeason
    semester_year: int

    def __init__(self, semester_season: SemesterSeason, semester_year: int):
        self.semester_season = semester_season
        self.semester_year = semester_year

    def to_semester_key(self):
        key_year = self.semester_year + 1 \
            if (self.semester_season != SemesterSeason.Spring) \
            else self.semester_year
        return str(key_year) + str(self.semester_season.value[0])

    def __json__(self):
        return {
            "semester_season": self.semester_season.name,
            "semester_year": self.semester_year
        }

    def __eq__(self, other):
        if not isinstance(other, Semester):
            return False
        return (self.semester_season, self.semester_year) == (other.semester_season, other.semester_year)

    def __str__(self):
        return F"{self.semester_season.name} {self.semester_year}"

    def __hash__(self):
        return hash((self.semester_season, self.semester_year))

    @staticmethod
    def from_json(json_obj):
        return Semester(semester_season_from_string(json_obj['semester_season']), json_obj['semester_year'])



def semester_season_from_string(season_str: str) -> SemesterSeason:
    for season in SemesterSeason:
        if season_str.lower() == season.name.lower():
            return season
    raise SyntaxError(F"Error! \'{season_str}\' is not a valid semester season!")
