import threading
import time
from typing import Tuple
import logging

from core.configuration import UserApplicationSettings
from core.licensing.cloud_actions import MembershipLevel, ApplicationStart, SignedDataResponse, \
    ApplicationStartPermission, RegistrationNotification, StatusResponse, ResponseStatus, SessionPing, ApplicationStop
from core.registrar import RegistrationResult
from core import util
from core.status import Status


def get_base_url() -> str:
    return 'https://license.aseef.dev/bu-registration-bot'


def check_license_and_start_session(license_key: str) -> Tuple[str, UserApplicationSettings, MembershipLevel, int]:
    send_timestamp = util.get_new_york_timestamp()
    app_start = ApplicationStart(
        license_key, util.get_device_meta(), send_timestamp
    ).send_and_get_response()

    if app_start is not None:
        start_permission = SignedDataResponse(
            app_start['signature'], ApplicationStartPermission.from_json(app_start['data'])
        )

        data: ApplicationStartPermission = start_permission.data

        if not start_permission.verify_signature():
            logging.critical("Invalid signature for start permission detected. This application may have been "
                             "tampered with. Please contact us for help.")
            return exit(1)

        if not data.response_timestamp >= send_timestamp:
            logging.critical("Invalid timestamp detected for start permission. Is your system time correct?"
                             "If this issue persists, please contact us for help.")
            return exit(1)

        logging.debug("Signature verified successfully.")

        membership = data.membership_level
        session_id = data.session_id
        kerberos_username = data.kerberos_username
        config = data.app_settings
    else:
        membership = MembershipLevel.Error
        session_id = -1
        kerberos_username = None
        config = None

    return kerberos_username, config, membership, session_id


def send_course_register_update(license_key: str, session_id: int, course_id: int, course_section: str) -> ResponseStatus:
    send_timestamp = util.get_new_york_timestamp()
    resp = RegistrationNotification(license_key, session_id, course_id, course_section, send_timestamp).send_and_get_response()
    if resp is None:
        # probably will never actually happen
        logging.error("Error. Your license key no longer exists (for some reason)? Please contact the developer.")
        exit(1)
    else:
        status_resp = SignedDataResponse(resp['signature'], StatusResponse.from_json(resp['data']))

        if not status_resp.verify_signature():
            logging.critical("Error! Invalid signature detected for course registration notification. This "
                             "application may have been tampered with. Please contact us for help.")
            exit(1)

        logging.debug("Signature verified successfully.")

        data: StatusResponse = status_resp.data
        if not data.response_timestamp >= send_timestamp:
            logging.critical("Error! Invalid timestamp detected for course registration notification. Is your system "
                             "time correct? If this issue persists, please contact us for help.")
            return exit(1)

        return data.status


# todo add error handling
def send_ping(license_key: str, session_id: int):
    send_timestamp = util.get_new_york_timestamp()
    resp = SessionPing(license_key, session_id, send_timestamp).send_and_get_response()
    if resp is None:
        # probably will never actually happen
        logging.error("Error. Your license key no longer exists (for some reason)? Please contact the developer.")
        exit(1)
    else:
        status_resp = SignedDataResponse(resp['signature'], StatusResponse.from_json(resp['data']))

        if not status_resp.verify_signature():
            logging.critical("Error! Invalid signature detected for session ping. This application may have been "
                             "tampered with. Please contact us for help.")
            exit(1)

        logging.debug("Signature verified successfully.")

        data: StatusResponse = status_resp.data
        if not data.response_timestamp >= send_timestamp:
            logging.critical("Error! Invalid timestamp detected for session ping. Is your system time correct?"
                             "If this issue persists, please contact us for help.")
            return exit(1)

        return data.status


def start_ping_task(license_key: str, session_id: int) -> threading.Thread:
    def ping_task():
        while True:
            send_ping(license_key, session_id)
            time.sleep(20)

    # Create a thread object
    ping_thread = threading.Thread(target=ping_task)

    # Start the thread
    ping_thread.start()

    return ping_thread

def send_app_terminated(license_key: str, session_id: int, registration_result: RegistrationResult):
    send_timestamp = util.get_new_york_timestamp()
    resp = ApplicationStop(license_key,
                           session_id,
                           registration_result.status == Status.SUCCESS,
                           registration_result.unknown_crash_occurred,
                           registration_result.reason,
                           registration_result.avg_cycle_time,
                           registration_result.std_cycle_time,
                           registration_result.avg_sleep_time,
                           registration_result.std_sleep_time,
                           send_timestamp)\
        .send_and_get_response()
    if resp is None:
        # probably will never actually happen
        logging.error("Error. Your license key no longer exists (for some reason)? Please contact the developer.")
        exit(1)
    else:
        status_resp = SignedDataResponse(resp['signature'], StatusResponse.from_json(resp['data']))

        if not status_resp.verify_signature():
            logging.critical("Error! Invalid signature detected for session ping. This application may have been "
                             "tampered with. Please contact us for help.")
            exit(1)

        logging.debug("Signature verified successfully.")

        data: StatusResponse = status_resp.data
        if not data.response_timestamp >= send_timestamp:
            logging.critical("Error! Invalid timestamp detected for session ping. Is your system time correct?"
                             "If this issue persists, please contact us for help.")
            return exit(1)

        return data.status