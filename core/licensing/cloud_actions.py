import base64
import json
import logging
from enum import Enum
from typing import List, Set, Union
from cryptography.exceptions import InvalidSignature

import requests
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey

from core.configuration import UserApplicationSettings

BASE_URL = "http://localhost:8080/api/app/v1"

loaded_key: Union[Ed25519PublicKey, None] = None


def get_public_key():
    global loaded_key
    if loaded_key is not None:
        return loaded_key
    with open('./core/licensing/ed25519_public_key.der', 'rb') as key_file:
        data = key_file.read()
        loaded_key = serialization.load_der_public_key(data)
    return loaded_key


class MembershipLevel(Enum):
    Full = 1,
    Demo = 2,
    Expired = 3,
    Error = 4


class ResponseStatus(Enum):
    Success = 1,
    Warning = 2,
    Error = 3


class SignableMessage:
    def get_verification_string(self) -> str:
        ...

    @staticmethod
    def from_json(json_obj):
        ...


class StatusResponse(SignableMessage):
    kerberos_username: str
    status: ResponseStatus
    reason: str
    response_timestamp: int

    def __init__(self, kerberos_username: str, status: ResponseStatus, reason: str, response_timestamp: int):
        self.kerberos_username = kerberos_username
        self.status = status
        self.reason = reason
        self.response_timestamp = response_timestamp

    def get_verification_string(self) -> str:
        return self.json_serialize()

    def __str__(self):
        return f"StatusResponse(kerberos_username={self.kerberos_username}, " \
               f"status={self.status}, reason={self.reason}, " \
               f"response_timestamp={self.response_timestamp})"

    @staticmethod
    def from_json(json_obj):
        return StatusResponse(
            json_obj['kerberos_username'],
            ResponseStatus[json_obj['status']],
            json_obj['reason'],
            json_obj['response_timestamp']
        )

    def __json__(self):
        return {
            "kerberos_username": self.kerberos_username,
            "status": self.status.name,
            "reason": self.reason,
            "response_timestamp": self.response_timestamp
        }

    def json_serialize(self):
        return json.dumps(self, default=lambda o: o.__json__(), separators=(',', ':'))


class ApplicationStartPermission(SignableMessage):
    kerberos_username: str
    membership_level: MembershipLevel
    app_settings: UserApplicationSettings
    session_id: int
    response_timestamp: int

    def __init__(self, kerberos_username: str, membership_level: MembershipLevel, app_settings: UserApplicationSettings,
                 session_id: int, response_timestamp: int):
        self.kerberos_username = kerberos_username
        self.membership_level = membership_level
        self.app_settings = app_settings
        self.session_id = session_id
        self.response_timestamp = response_timestamp

    def get_verification_string(self) -> str:
        return self.json_serialize()

    def __str__(self):
        return f"ApplicationStartPermission(kerberos_username={self.kerberos_username}, " \
               f"membership_level={self.membership_level}, " \
               f"app_settings={self.app_settings}, " \
               f"session_id={self.session_id}, " \
               f"response_timestamp={self.response_timestamp})"

    @staticmethod
    def from_json(json_obj):
        return ApplicationStartPermission(
            json_obj['kerberos_username'],
            MembershipLevel[json_obj['membership_level']],
            UserApplicationSettings.from_json(json_obj['user_app_settings']),
            json_obj['session_id'],
            json_obj['response_timestamp']
        )

    def __json__(self):
        return {
            "kerberos_username": self.kerberos_username,
            "membership_level": self.membership_level.name,
            "user_app_settings": self.app_settings.__json__(),
            "session_id": self.session_id,
            "response_timestamp": self.response_timestamp
        }

    def json_serialize(self):
        return json.dumps(self, default=lambda o: o.__json__(), separators=(',', ':'))


class SignedMessage:
    signature: str

    def __init__(self, base64_signature: str):
        self.signature = base64_signature

    def verify_signature_for(self, message: bytes):
        signature = base64.b64decode(self.signature)
        try:
            get_public_key().verify(signature, message)
            return True
        except InvalidSignature:
            return False


class SignedDataResponse(SignedMessage):
    data: SignableMessage

    def __init__(self, signature: str, data: SignableMessage):
        super().__init__(signature)
        self.data = data

    def verify_signature(self):
        return self.verify_signature_for(self.data.get_verification_string().encode())

    def __str__(self):
        return f"SignedApplicationStartPermission(data={self.data}, signature={self.signature})"


class SendableCloudMessage:
    path: str = None

    def __init__(self, path: str):
        self.path = path

    def get_url(self):
        return BASE_URL + self.path

    def json_serialize(self):
        return json.dumps(self, default=lambda o: o.__json__(), indent=4)

    def __json__(self):
        ...

    def send_and_get_response(self) -> Union[None, dict]:
        serialized_json_body = self.json_serialize()
        try:
            response = requests.post(self.get_url(), data=serialized_json_body, headers={
                "Content-Type": "application/json",
                "User-Agent": "Turbo-Terrier-Client"
            })
        except Exception as e:
            logging.critical("Unable to connect to the cloud server! Is your internet connection working? If this "
                             "issue persists, please contact the developer.")
            logging.debug(e)
            exit(1)

        if response.status_code == 200:
            return response.json()
        elif response.status_code == 401:
            return None
        else:
            raise ConnectionError(response.text)


class DeviceMeta:
    core_count: int
    cpu_speed: float
    name: str
    system_arch: str
    os: str

    def __init__(self, core_count: int, cpu_speed: float, name: str, system_arch: str, os: str):
        self.core_count = core_count
        self.name = name
        self.cpu_speed = cpu_speed
        self.system_arch = system_arch
        self.os = os


class ApplicationStart(SendableCloudMessage):
    license_key: str
    device_meta: DeviceMeta
    timestamp: int

    def __init__(self, license_key: str, device_meta: DeviceMeta,
                 timestamp: int):
        super().__init__("/app-started")
        self.license_key = license_key
        self.device_meta = device_meta
        self.timestamp = timestamp

    def __json__(self):
        return {
            "license_key": self.license_key,
            "device_meta": self.device_meta.__dict__,
            "timestamp": self.timestamp
        }


class ApplicationStop(SendableCloudMessage):
    license_key: str
    session_id: int
    did_finish: bool
    unknown_crash_occurred: bool
    reason: str
    avg_cycle_time: float
    std_cycle_time: float
    avg_sleep_time: float
    std_sleep_time: float
    timestamp: int

    def __init__(self, license_key: str, session_id: int, did_finish: bool, unknown_crash_occurred: bool,
                 reason: str, avg_cycle_time: float, std_cycle_time: float, avg_sleep_time: float,
                 std_sleep_time: float,
                 timestamp: int):
        super().__init__("/app-stopped")
        self.license_key = license_key
        self.session_id = session_id
        self.did_finish = did_finish
        self.unknown_crash_occurred = unknown_crash_occurred
        self.reason = reason
        self.avg_cycle_time = avg_cycle_time
        self.std_cycle_time = std_cycle_time
        self.avg_sleep_time = avg_sleep_time
        self.std_sleep_time = std_sleep_time
        self.timestamp = timestamp

    def __json__(self):
        return {
            "license_key": self.license_key,
            "session_id": self.session_id,
            "did_finish": self.did_finish,
            "unknown_crash_occurred": self.unknown_crash_occurred,
            "reason": self.reason,
            "avg_cycle_time": self.avg_cycle_time,
            "std_cycle_time": self.std_cycle_time,
            "avg_sleep_time": self.avg_sleep_time,
            "std_sleep_time": self.std_sleep_time,
            "timestamp": self.timestamp
        }


class SessionPing(SendableCloudMessage):
    license_key: str
    session_id: int
    timestamp: int

    def __init__(self, license_key: str, session_id: int, timestamp: int):
        super().__init__("/ping")
        self.license_key = license_key
        self.session_id = session_id
        self.timestamp = timestamp

    def __json__(self):
        return {
            "license_key": self.license_key,
            "session_id": self.session_id,
            "timestamp": self.timestamp
        }


class RegistrationNotification(SendableCloudMessage):
    license_key: str
    session_id: int
    planner: bool
    course_id: int
    course_section: str
    timestamp: int

    def __init__(self, license_key: str, session_id: int, planner: bool, course_id: int, course_section: str,
                 timestamp: int):
        super().__init__("/course-registered")
        self.license_key = license_key
        self.session_id = session_id
        self.planner = planner
        self.course_id = course_id
        self.course_section = course_section
        self.timestamp = timestamp

    def __json__(self):
        return {
            "license_key": self.license_key,
            "session_id": self.session_id,
            "planner": self.planner,
            "course_section": self.course_section,
            "course_id": self.course_id,
            "timestamp": self.timestamp
        }
