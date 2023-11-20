from typing import Union

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey

loaded_key: Union[Ed25519PublicKey, None] = None


def get_public_key():
    global loaded_key
    if loaded_key is not None:
        return loaded_key
    with open('ed25519_public_key.pem', 'rb') as key_file:
        loaded_key = serialization.load_pem_public_key(key_file.read())
    return loaded_key


def get_base_url() -> str:
    return 'https://license.aseef.dev/bu-registration-bot'
