import base64
import json
from enum import Enum
from typing import List, Set
from cryptography.exceptions import InvalidSignature

import requests

from core.bu_course import BUCourse
from core.licensing import license_util

BASE_URL = "http://localhost:8080/api/v1"


class MembershipLevel(Enum):
    Full = 1,
    Demo = 2,
    Expired = 3,
    Error = 4


class ApplicationStartPermission:
    kerberos_username: str
    membership_level: MembershipLevel
    session_id: int
    response_timestamp: int

    def __init__(self, kerberos_username: str, membership_level: MembershipLevel, session_id: int, response_timestamp: int):
        self.kerberos_username = kerberos_username
        self.membership_level = membership_level
        self.session_id = session_id
        self.response_timestamp = response_timestamp

    def get_verification_string(self):
        return self.kerberos_username + "," + \
            str(self.membership_level.name) + \
            "," + str(self.session_id) + "," + \
            str(self.response_timestamp)

    def __str__(self):
        return f"ApplicationStartPermission(kerberos_username={self.kerberos_username}, " \
               f"membership_level={self.membership_level}, session_id={self.session_id}, " \
               f"response_timestamp={self.response_timestamp})"

    @staticmethod
    def from_json(json_obj):
        return ApplicationStartPermission(
            json_obj['kerberos_username'],
            MembershipLevel[json_obj['membership_level']],
            json_obj['session_id'],
            json_obj['response_timestamp']
        )



class SignedMessage:
    signature: str

    def __init__(self, base64_signature: str):
        self.signature = base64_signature

    def verify_signature_for(self, message: bytes):
        signature = base64.b64decode(self.signature)
        try:
            license_util.get_public_key().verify(signature, message)
            return True
        except InvalidSignature:
            return False


class SignedApplicationStartPermission(SignedMessage):
    data: ApplicationStartPermission

    def __init__(self, signature: str, data: ApplicationStartPermission):
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

    def send_and_get_response(self):
        serialized_json_body = self.json_serialize()
        response = requests.post(self.get_url(), data=serialized_json_body, headers={
            "Content-Type": "application/json"
        })
        if response.status_code == 200:
            return response.json()
        else:
            raise ConnectionError("Unable to connect to the licensing server.")


class AppCredentials:
    kerberos_username: str
    authentication_key: str

    def __init__(self, kerberos_username: str, authentication_key: str):
        self.kerberos_username = kerberos_username
        self.authentication_key = authentication_key


class DeviceMeta:
    core_count: int
    cpu_speed: float
    system_arch: str
    os: str

    def __init__(self, core_count: int, cpu_speed: float, system_arch: str, os: str):
        self.core_count = core_count
        self.cpu_speed = cpu_speed
        self.system_arch = system_arch
        self.os = os


class ApplicationStart(SendableCloudMessage):
    credentials: AppCredentials
    target_courses: Set[BUCourse]
    device_meta: DeviceMeta
    timestamp: int

    def __init__(self, credentials: AppCredentials, target_courses: Set[BUCourse], device_meta: DeviceMeta,
                 timestamp: int):
        super().__init__("/app-started")
        self.credentials = credentials
        self.target_courses = target_courses
        self.device_meta = device_meta
        self.timestamp = timestamp

    def __json__(self):
        return {
            "credentials": self.credentials.__dict__,
            "target_courses": list(map(lambda course: course.__json__(), self.target_courses)),
            "device_meta": self.device_meta.__dict__,
            "timestamp": self.timestamp
        }


class ApplicationStop(SendableCloudMessage):
    credentials: AppCredentials
    session_id: int
    did_finish: bool
    unknown_crash_occurred: bool
    reason: str
    avg_cycle_time: float
    std_cycle_time: float
    avg_sleep_time: float
    std_sleep_time: float
    timestamp: int

    def __init__(self, credentials: AppCredentials, session_id: int, did_finish: bool, unknown_crash_occurred: bool,
                 reason: str, avg_cycle_time: float, std_cycle_time: float, avg_sleep_time: float,
                 std_sleep_time: float,
                 timestamp: int):
        super().__init__("/app-stopped")
        self.credentials = credentials
        self.session_id = session_id
        self.did_finish = did_finish
        self.unknown_crash_occurred = unknown_crash_occurred
        self.reason = reason
        self.avg_cycle_time = avg_cycle_time
        self.std_cycle_time = std_cycle_time
        self.avg_sleep_time = avg_sleep_time
        self.std_sleep_time = std_sleep_time
        self.timestamp = timestamp


class SessionPing(SendableCloudMessage):
    credentials: AppCredentials
    session_id: int

    def __init__(self, credentials: AppCredentials, session_id: int):
        super().__init__("/ping")
        self.credentials = credentials
        self.session_id = session_id


class RegistrationNotification(SendableCloudMessage):
    credentials: AppCredentials
    session_id: int
    course: BUCourse
    timestamp: int

    def __init__(self, credentials: AppCredentials, session_id: int, course: BUCourse, timestamp: int):
        super().__init__("/course-registered")
        self.credentials = credentials
        self.session_id = session_id
        self.course = course
        self.timestamp = timestamp
