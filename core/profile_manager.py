import logging
from typing import Dict

from core import util
from core.database import BotDatabase
from core.wrappers.profile_config import ProfileConfig
from core.wrappers.status import Status


class ProfileManager:
    __profiles: Dict[int, ProfileConfig] = None
    __current_profile: ProfileConfig = None

    @staticmethod
    def init():
        ProfileManager.__profiles = BotDatabase.load_all_profile()

    @staticmethod
    def get_available_profiles():
        assert ProfileManager.__profiles is not None, "Profile manager is not yet loaded"

        return ProfileManager.__profiles.keys()

    @staticmethod
    def get_profile(profile_id: int) -> ProfileConfig:
        assert ProfileManager.__profiles is not None, "Profile manager is not yet loaded"
        assert ProfileManager.__profiles.__contains__(profile_id), "That profile id does not exist."

        return ProfileManager.__profiles[profile_id]

    @staticmethod
    def get_current_profile():
        assert ProfileManager.__current_profile is not None, "Profile manager is not yet loaded"
        return ProfileManager.__current_profile

    @staticmethod
    def get_current_profile_id():
        assert ProfileManager.__current_profile is not None, "Profile manager is not yet loaded"
        return ProfileManager.__current_profile.profile_id

    @staticmethod
    def set_current_profile(profile_id: int):
        ProfileManager.__current_profile = ProfileManager.get_profile(profile_id)

    @staticmethod
    def add_profile(profile_config: ProfileConfig) -> ProfileConfig:
        assert profile_config.profile_id is None, "You can't add a profile that already has an associated ID."

        profile_config = BotDatabase.create_profile(profile_config)
        assert profile_config.profile_id is not None  # above method should've updated the profile id

        ProfileManager.__profiles[profile_config.profile_id] = profile_config
        return profile_config

    @staticmethod
    def update_profile(profile_config: ProfileConfig, profile_id: int = get_current_profile_id()) -> ProfileConfig:
        profile_config = BotDatabase.update_profile(profile_id, profile_config)
        ProfileManager.__profiles[profile_config.profile_id] = profile_config
        return profile_config

    @staticmethod
    def init_profile_creation_console() -> ProfileConfig:
        kerberos_username: str = input("Whats your kerberos username? Hint: It's probably the part of"
                                       " university email that comes BEFORE the @bu.edu.")

        license_key: str = input("Do you have a premium license key for this application?"
                                 " If not, press enter with out typing anything to continue"
                                 " with the trial version. Otherwise paste your full license key"
                                 " here.")

        is_planner: bool = not bool(input("Do you want to do real registrations, or planner registrations? Enter"
                                          "'True' for real registrations. Otherwise, enter 'False' and we will only"
                                          " register to the planner (useful for testing everything works)."))

        is_save_password: bool = bool(input("Should we save your kerberos password to this device so you don't need to"
                                            " re-enter it everytime? You can safely answer 'True' if this is your"
                                            " personal device. Otherwise answer 'False'."))

        is_save_duo_cookies: bool = is_save_password

        should_ignore_non_existent_courses: bool = bool(input("Would you like to be warned if you try to register for"
                                                              "a non-existent course? If yes, answer 'True', otherwise"
                                                              "answer 'False'. The only time you would answer 'False'"
                                                              "is when you want to register for a course that has not"
                                                              "yet been added but you know will be added later."))

        driver_test_status = util.test_drivers()
        if driver_test_status == Status.SUCCESS:
            driver_path: str = ""
        elif driver_test_status == Status.FAILURE:
            while True:
                driver_path = input("We were unable to automatically detect chrome drivers. Please specify the path to"
                                    " your chrome driver file. You can find more information on how to this at [TODO].")
                driver_test_status = util.test_drivers(driver_path)
                if driver_test_status == Status.SUCCESS:
                    break
        else:
            # I already check this at the start so in theory should never trigger
            exit(1)

        is_debug_mode: bool = bool(input("Just answer 'False' unless you know what you are doing."))

        return ProfileConfig(
            profile_id=None,
            license_key=license_key,
            kerberos_username=kerberos_username,
            is_planner=is_planner,
            driver_path=driver_path,
            is_save_password=is_save_password,
            is_save_duo_cookies=is_save_duo_cookies,
            should_ignore_non_existent_courses=should_ignore_non_existent_courses,
            is_debug_mode=is_debug_mode
        )
