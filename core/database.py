import logging
import pickle
import sqlite3
import time
from sqlite3 import Connection
from typing import Union, List, Dict

from selenium.webdriver.chrome.webdriver import WebDriver

from core import util
from core.wrappers.bu_course import BUCourse
from core.wrappers.course_season import CourseSeason
from core.wrappers.course_semester import CourseSemester
from core.wrappers.profile_config import ProfileConfig


class BotDatabase:
    __connection: Connection = None

    @staticmethod
    def init(path: str) -> None:
        BotDatabase.__connection = sqlite3.connect(path)
        BotDatabase.__create_config_table()
        BotDatabase.__create_cookies_table()
        BotDatabase.__create_courses_table()
        BotDatabase.__create_encryption_keys_table()

    @staticmethod
    def get_course_list(profile_id: int) -> List[BUCourse]:
        assert BotDatabase.__connection is not None

        select_query = \
            """
                        SELECT semester_season, semester_year, college, department, 
                        course_id, course_section, added_timestamp, registered_timestamp
                        FROM target_courses
                        WHERE profile_id = ?
                        """

        result = BotDatabase.__connection.execute(select_query, (profile_id,)).fetchall()

        course_list = []
        for row in result:
            course = BUCourse(
                semester=CourseSemester(
                    season=CourseSeason.from_str(row[0]),
                    year=row[1]
                ),
                college=row[2],
                dept=row[3],
                course_code=row[4],
                section=row[5],
                added_timestamp=row[6],
                registered_timestamp=row[7]
            )
            course_list.append(course)

        return course_list

    @staticmethod
    def add_course(profile_id, course: BUCourse):
        assert BotDatabase.__connection is not None

        insert_query = \
            """
                    INSERT INTO target_courses (
                        profile_id, semester_season, semester_year, college, 
                        department, course_id, course_section, added_timestamp
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """

        BotDatabase.__connection.execute(insert_query, (
            profile_id, course.semester.season, course.semester.year, course.college, course.dept,
            course.course_code, course.section, int(course.added_timestamp * 1000)
        ))

        BotDatabase.__connection.commit()

    @staticmethod
    def update_course(profile_id, course: BUCourse, registered_timestamp: float):
        assert BotDatabase.__connection is not None

        update_query = """
            UPDATE target_courses
            SET registered_timestamp = ?
            WHERE profile_id = ? AND
                  semester_season = ? AND semester_year = ? AND
                  college = ? AND department = ? AND
                  course_id = ? AND course_section = ?
        """
        BotDatabase.__connection.execute(update_query, (
            int(registered_timestamp * 1000), profile_id,
            course.semester.season, course.semester.year, course.college, course.dept,
            course.course_code, course.section
        ))

        BotDatabase.__connection.commit()

    @staticmethod
    def create_profile(profile_config: ProfileConfig) -> ProfileConfig:
        assert BotDatabase.__connection is not None

        insert_query = """
                            INSERT INTO config (
                                license_key, kerberos_user, planner_mode,
                                driver_path, ignore_non_existent_courses, save_password, save_duo_session, debug
                            )
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """

        cursor = BotDatabase.__connection.cursor()

        BotDatabase.__connection.execute(insert_query, (
            profile_config.license_key,
            profile_config.kerberos_username,
            profile_config.is_planner,
            profile_config.driver_path,
            profile_config.should_ignore_non_existent_courses,
            profile_config.is_save_password,
            profile_config.is_save_duo_cookies,
            profile_config.is_debug_mode
        ))
        profile_id = cursor.lastrowid
        BotDatabase.__connection.commit()

        profile_config.profile_id = profile_id
        return profile_config

    @staticmethod
    def update_profile(profile_id: int, profile_config: ProfileConfig) -> ProfileConfig:
        assert BotDatabase.__connection is not None

        update_query = """
                        UPDATE config
                        SET
                            license_key = ?,
                            kerberos_user = ?,
                            planner_mode = ?,
                            driver_path = ?,
                            ignore_non_existent_courses = ?,
                            save_password = ?,
                            save_duo_session = ?,
                            debug = ?
                        WHERE profile_id = ?
                    """

        BotDatabase.__connection.execute(update_query, (
            profile_config.license_key,
            profile_config.kerberos_username,
            profile_config.is_planner,
            profile_config.driver_path,
            profile_config.should_ignore_non_existent_courses,
            profile_config.is_save_password,
            profile_config.is_save_duo_cookies,
            profile_config.is_debug_mode,
            profile_id
        ))

        BotDatabase.__connection.commit()
        profile_config.profile_id = profile_id

        return profile_config

    @staticmethod
    def load_all_profile() -> Dict[int, ProfileConfig]:
        assert BotDatabase.__connection is not None

        select_query = \
            """
                SELECT profile_id, license_key, kerberos_user, planner_mode, driver_path,
                ignore_non_existent_courses, save_password, save_duo_session, debug FROM config
            """

        results = BotDatabase.__connection.execute(select_query).fetchall()

        profile_dict: Dict[int, ProfileConfig] = {}
        for result in results:
            profile_config: ProfileConfig = ProfileConfig(
                result[0],
                result[1],
                result[2],
                result[3],
                result[4],
                result[5],
                result[6],
                result[7],
                result[8]
            )
            profile_dict[profile_config.profile_id] = profile_config

        return profile_dict

    @staticmethod
    def save_cookies(profile_id, driver: WebDriver):
        assert BotDatabase.__connection is not None

        cookies = driver.get_cookies()
        picked_cookies = util.dump_to_bytes(cookies)
        last_updated = int(time.time() * 1000)
        cursor = BotDatabase.__connection.cursor()
        cursor.execute("""
            INSERT INTO saved_cookies (profile_id, cookies, last_updated)
            VALUES (?, ?, ?)
        """, (profile_id, picked_cookies, last_updated))

    @staticmethod
    def load_cookies(profile_id, driver: WebDriver):
        assert BotDatabase.__connection is not None

        cursor = BotDatabase.__connection.cursor()
        cursor.execute("""
                    SELECT cookies
                    FROM saved_cookies
                    WHERE profile_id = ?
                """, (profile_id,))
        result = cursor.fetchone()

        if result:
            cookies = pickle.loads(result[0])
        else:
            logging.warning(f"No cookies found for profile_id={profile_id}")
            return

        # Enables network tracking, so we may use Network.setCookie method
        driver.execute_cdp_cmd('Network.enable', {})

        # Iterate through pickle dict and add all the cookies
        for cookie in cookies:
            # Fix issue Chrome exports 'expiry' key but expects 'expire' on import
            if 'expiry' in cookie:
                cookie['expires'] = cookie['expiry']
                del cookie['expiry']

            # Set the actual cookie
            driver.execute_cdp_cmd('Network.setCookie', cookie)

        # Disable network tracking
        driver.execute_cdp_cmd('Network.disable', {})

    @staticmethod
    def __create_config_table():
        assert BotDatabase.__connection is not None

        create = \
            """
            create table if not exists config
            (
                profile_id                  integer           not null
                    constraint config_pk
                        primary key autoincrement,
                license_key                 varchar,
                kerberos_user               integer           not null,
                planner_mode                tinyint default 1 not null,
                driver_path                 integer,
                ignore_non_existent_courses tinyint default 0 not null,
                save_password               tinyint default 0 not null,
                save_duo_session            tinyint default 0 not null,
                debug                       tinyint default 0 not null,
            );
            """
        BotDatabase.__connection.execute(create)

    @staticmethod
    def __create_courses_table():
        assert BotDatabase.__connection is not None

        create = \
            """
            create table if not exists target_courses
            (
                profile_id           int        not null,
                semester_season      varchar(8) not null,
                semester_year        tinyint    not null,
                college              varchar(5) not null,
                department           varchar(5) not null,
                course_id            tinyint    not null,
                course_section       varchar(4) not null,
                added_timestamp      bigint     not null,
                registered_timestamp bigint,
                constraint target_courses_pk
                    primary key (profile_id, semester_season, semester_year, college, department, course_id, course_section)
            );
            """
        BotDatabase.__connection.execute(create)

    @staticmethod
    def __create_cookies_table():
        assert BotDatabase.__connection is not None

        create = \
            """
            create table if not exists saved_cookies
            (
                profile_id   integer not null
                    constraint saved_cookies_config_profile_id_fk
                        references config,
                cookies      blob    not null,
                last_updated bigint  not null
            );
            """
        BotDatabase.__connection.execute(create)

    @staticmethod
    def __create_encryption_keys_table():
        assert BotDatabase.__connection is not None

        create = \
            """
            create table if not exists encryption_keys
            (
                name        varchar not null
                    constraint encryption_keys_pk
                        primary key,
                private_key blob,
                public_key  blob
            ); 
            """
        BotDatabase.__connection.execute(create)

    @staticmethod
    def get_connection() -> Connection:
        assert BotDatabase.__connection is not None

        return BotDatabase.__connection


BotDatabase.init("../bot_data.db")
test = {
    1: 221,
    3: "sup",
    4: 'xD'
}

print(test)
print()
data = util.dump_to_bytes(test)
print(data)

print(util.load_picked_obj(data))
