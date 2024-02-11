import json
import os.path
import re
from typing import Tuple, List, Set, Optional

import yaml

from core.bu_course import BUCourseSection


class PushNotification:
    enabled: bool
    email_alerts: bool
    text_alerts: bool
    call_alerts: bool

    def __init__(self, enabled: bool, email_alerts: bool, text_alerts: bool, call_alerts: bool):
        self.enabled = enabled
        self.email_alerts = email_alerts
        self.text_alerts = text_alerts
        self.call_alerts = call_alerts

    @staticmethod
    def from_json(json_obj):
        return PushNotification(json_obj['enabled'], json_obj['email_alerts'], json_obj['text_alerts'],
                                json_obj['call_alerts'])

    def __json__(self):
        return {
            "enabled": self.enabled,
            "email_alerts": self.email_alerts,
            "text_alerts": self.text_alerts,
            "call_alerts": self.call_alerts
        }


class CustomerDriver:
    enabled: bool
    driver_path: Optional[str]

    def __init__(self, enabled: bool, driver_path: Optional[str]):
        self.enabled = enabled
        self.driver_path = driver_path

    def json_serialize(self):
        return json.dumps(self, default=lambda o: o.__json__(), indent=4)

    @staticmethod
    def from_json(json_obj):
        return CustomerDriver(json_obj['enabled'], json_obj['driver_path'])

    def __json__(self):
        return {
            "enabled": self.enabled,
            "driver_path": self.driver_path
        }


class UserApplicationSettings:
    real_registrations: bool
    keep_trying: bool
    save_password: bool
    save_duo_cookies: bool
    registration_notifications: PushNotification
    watchdog_notifications: PushNotification
    console_colors: bool
    custom_driver: CustomerDriver
    debug_mode: bool
    target_courses: List[BUCourseSection]
    allow_update_emails: bool
    allow_marketing_emails: bool
    email: Optional[str]
    phone: Optional[str]

    def __init__(self, real_registrations: bool, keep_trying: bool, save_password: bool, save_duo_cookies: bool,
                 registration_notifications: PushNotification, watchdog_notifications: PushNotification,
                 console_colors: bool,
                 custom_driver: CustomerDriver, debug_mode: bool, target_courses: List[BUCourseSection],
                 allow_update_emails: bool, allow_marketing_emails: bool, email: Optional[str], phone: Optional[str]):
        self.real_registrations = real_registrations
        self.keep_trying = keep_trying
        self.save_password = save_password
        self.save_duo_cookies = save_duo_cookies
        self.registration_notifications = registration_notifications
        self.watchdog_notifications = watchdog_notifications
        self.console_colors = console_colors
        self.custom_driver = custom_driver
        self.debug_mode = debug_mode
        self.target_courses = target_courses
        self.allow_update_emails = allow_update_emails
        self.allow_marketing_emails = allow_marketing_emails
        self.email = email
        self.phone = phone

    @staticmethod
    def from_json(json_obj):
        return UserApplicationSettings(
            json_obj['real_registrations'],
            json_obj['keep_trying'],
            json_obj['save_password'],
            json_obj['save_duo_cookies'],
            PushNotification.from_json(json_obj['registration_notifications']),
            PushNotification.from_json(json_obj['watchdog_notifications']),
            json_obj['console_colors'],
            CustomerDriver.from_json(json_obj['custom_driver']),
            json_obj['debug_mode'],
            [BUCourseSection.from_json(x) for x in json_obj['target_courses']],
            json_obj['allow_update_emails'],
            json_obj['allow_marketing_emails'],
            json_obj['email'],
            json_obj['phone']
        )

    def json_serialize(self):
        return json.dumps(self, default=lambda o: o.__json__(), separators=(',', ':'))

    def __json__(self):
        return {
            "real_registrations": self.real_registrations,
            "keep_trying": self.keep_trying,
            "save_password": self.save_password,
            "save_duo_cookies": self.save_duo_cookies,
            "registration_notifications": self.registration_notifications.__json__(),
            "watchdog_notifications": self.watchdog_notifications.__json__(),
            "console_colors": self.console_colors,
            "custom_driver": self.custom_driver.__json__(),
            "debug_mode": self.debug_mode,
            "target_courses": [x.__json__() for x in self.target_courses],
            "allow_update_emails": self.allow_update_emails,
            "allow_marketing_emails": self.allow_marketing_emails,
            "email": self.email,
            "phone": self.phone
        }

    def __str__(self):
        return self.json_serialize()
