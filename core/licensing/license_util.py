from typing import Union

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey

loaded_key: Union[Ed25519PublicKey, None] = None


def get_public_key():
    global loaded_key
    if loaded_key is not None:
        return loaded_key
    with open('ed25519_public_key.der', 'rb') as key_file:
        data = key_file.read()
        loaded_key = serialization.load_der_public_key(data)
    return loaded_key


def get_base_url() -> str:
    return 'https://license.aseef.dev/bu-registration-bot'


