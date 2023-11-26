from enum import Enum


class CourseSeason(Enum):
    SPRING = 4,
    SUMMER_1 = 1,
    SUMMER_2 = 2,
    FALL = 3

    @classmethod
    def from_id(cls, season_id):
        for season in cls:
            if season.value == season_id:
                return season
        raise ValueError(f"No matching enum found for id {season_id}")

    @classmethod
    def from_str(cls, season_str: str):
        for season in cls:
            normalized_str = season_str.replace("_", "").replace(" ", "").lower()
            normalized_enum = season.name.replace("_", "").replace(" ", "").lower()
            if normalized_enum == normalized_str:
                return season
        raise ValueError(f"No matching enum found for {season_str}")