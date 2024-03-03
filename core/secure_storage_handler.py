import base64
import json
import platform
import subprocess
from typing import Optional

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC


class SecurelyStorageData:
    license_key: str
    kerberos_password: Optional[str] = None
    duo_cookies: Optional[list[dict]] = None

    @staticmethod
    def from_dict(data: dict):
        securely_stored_data = SecurelyStorageData()
        securely_stored_data.__dict__.update(data)
        return securely_stored_data


loaded_storage: SecurelyStorageData | None = None


def load_encrypted_data() -> Optional[SecurelyStorageData]:
    global loaded_storage
    if loaded_storage is None:
        try:
            with open("secure_storage.tt", "r") as file:
                key = _get_encryption_key()
                raw_str = file.read()
                if len(raw_str) == 0:
                    return None
                json_str = _decrypt_message(key, raw_str)
                loaded_storage = SecurelyStorageData.from_dict(json.loads(json_str))
                return loaded_storage
        except FileNotFoundError:
            return None
    else:
        return loaded_storage


def save_encrypted_data(data: Optional[SecurelyStorageData]):
    global loaded_storage
    with open("secure_storage.tt", "w") as file:
        if data is None:
            _clear_encrypted_data()
            loaded_storage = None
            return
        key = _get_encryption_key()
        file.write(_encrypt_message(key, json.dumps(data.__dict__)))
        loaded_storage = data


def _clear_encrypted_data():
    try:
        with open("secure_storage.tt", "w") as file:
            file.write("")
    except FileNotFoundError:
        pass


def get_license_key() -> Optional[str]:
    return None if load_encrypted_data() is None else load_encrypted_data().license_key


def get_kerberos_password() -> Optional[str]:
    return None if load_encrypted_data() is None else load_encrypted_data().kerberos_password


def get_duo_cookies() -> Optional[list[dict]]:
    return None if load_encrypted_data() is None else load_encrypted_data().duo_cookies


def set_license_key(license_key: str):
    data = load_encrypted_data()
    if data is None:
        data = SecurelyStorageData()
    data.license_key = license_key
    save_encrypted_data(data)


def set_kerberos_password(kerberos_password: Optional[str]):
    data = load_encrypted_data()
    assert data is not None, "License key must be set before setting Kerberos password"
    data.kerberos_password = kerberos_password
    save_encrypted_data(data)


def set_duo_cookies(duo_cookies: Optional[list[dict]]):
    data = load_encrypted_data()
    assert data is not None, "License key must be set before setting Duo cookies"
    data.duo_cookies = duo_cookies
    save_encrypted_data(data)


def has_license_key() -> bool:
    return load_encrypted_data() is not None


def has_kerberos_password() -> bool:
    return load_encrypted_data().kerberos_password is not None


def has_duo_cookies() -> bool:
    return load_encrypted_data().duo_cookies is not None


def _encrypt_message(key: str, message: str) -> str:
    """Encrypts a message using a password-derived encryption key.

    :param key: The password used to derive the encryption key.
    :param message: The message to be encrypted.
    :return: The encrypted message as a string.
    """

    # Derive a secure key from the password using PBKDF2
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=b"I like salty food lol",
        iterations=390000,  # Adjust iterations based on security needs
    )
    key = base64.urlsafe_b64encode(kdf.derive(key.encode()))

    # Encrypt the message using Fernet
    fernet = Fernet(key)
    encrypted_message = fernet.encrypt(message.encode())
    return encrypted_message.decode()


def _decrypt_message(key: str, encrypted_message: str) -> str:
    """Decrypts an encrypted message using a password-derived encryption key.

    :param key: The password used to derive the encryption key.
    :param encrypted_message: The encrypted message to be decrypted.
    :return: The decrypted message as a string.
    """

    # Derive the same key from the password using PBKDF2
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=b"I like salty food lol",
        iterations=390000,
    )
    key = base64.urlsafe_b64encode(kdf.derive(key.encode()))

    # Decrypt the message using Fernet
    fernet = Fernet(key)
    decrypted_message = fernet.decrypt(encrypted_message.encode()).decode()
    return decrypted_message


def _get_encryption_key():
    return platform.system() + ":::" + _get_hardware_uuid()


def _get_hardware_uuid():
    system = platform.system()

    if system == "Linux":
        try:
            # Run the 'dmidecode' command to get the UUID on Linux
            result = subprocess.run(['dmidecode', '-s', 'system-uuid'], capture_output=True, text=True, check=True)
            return result.stdout.strip().upper()
        except subprocess.CalledProcessError as e:
            print(f"Error retrieving UUID on Linux: {e}")
            return None

    elif system == "Windows":
        try:
            # Run the 'wmic' command to get the UUID on Windows
            result = subprocess.run(['wmic', 'csproduct', 'get', 'UUID'], capture_output=True, text=True, check=True)
            return result.stdout.strip().split('\n')[-1].strip().upper()
        except subprocess.CalledProcessError as e:
            print(f"Error retrieving UUID on Windows: {e}")
            return None

    elif system == "Darwin":
        try:
            # Use the macOS 'system_profiler' command to get the UUID
            result = subprocess.run(['system_profiler', 'SPHardwareDataType'], capture_output=True, text=True,
                                    check=True)
            uuid_line = [line for line in result.stdout.split('\n') if 'UUID' in line][0]
            return uuid_line.split(':')[-1].strip().upper()
        except subprocess.CalledProcessError as e:
            print(f"Error retrieving UUID on macOS: {e}")
            return None

    else:
        print(f"Unsupported operating system: {system}")
        return None
