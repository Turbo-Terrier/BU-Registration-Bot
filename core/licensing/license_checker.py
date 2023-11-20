import logging

import requests

from core.licensing.cloud_actions import CloudAction
from core.licensing.license_util import get_public_key, get_base_url


class LicenseChecker:

    def __init__(self, kerberos_user, license_key):
        self.kerberos_user = kerberos_user
        self.license_key = license_key

    def is_licensed(self):
        resp = requests.get(get_base_url(), json=self.__get_body())
        json_resp = resp.json()
        license_resp = LicenseResponse(json_resp)
        if license_resp.verify_fingerprint():
            return license_resp.premium
        else:
            logging.error('Error! Invalid response signature received during license verification.')
            return False

    def __get_body(self):
        return {
            'action-id': CloudAction.LICENSE_CHECK.value,
            'kerberos-user': self.kerberos_user,
            'license-key': self.license_key
        }


class LicenseResponse:
    premium: bool
    kerberos_user: str
    timestamp: float
    signature: str

    def __init__(self, json):
        self.kerberos_user = json['kerberos-user']
        self.premium = json['premium']
        self.timestamp = json['timestamp']
        self.signature = json['signature']

    def verify_fingerprint(self):
        string_to_check = f"{self.kerberos_user}:{self.premium}:{self.timestamp}"
        print(string_to_check)
        try:
            get_public_key().verify(
                self.signature,
                string_to_check.encode('UTF-8')
            )
            return True
        except:
            return False