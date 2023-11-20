from cryptography.hazmat.primitives.asymmetric import ed25519
from cryptography.hazmat.primitives import serialization

# Generate a new Ed25519 key pair
private_key = ed25519.Ed25519PrivateKey.generate()

# Serialize the private key to a PEM format
private_pem = private_key.private_bytes(
    encoding=serialization.Encoding.PEM,
    format=serialization.PrivateFormat.PKCS8,
    encryption_algorithm=serialization.NoEncryption()
)

# Get the public key from the private key
public_key = private_key.public_key()

# Serialize the public key to a PEM format
public_pem = public_key.public_bytes(
    encoding=serialization.Encoding.PEM,
    format=serialization.PublicFormat.SubjectPublicKeyInfo
)

# Save the private and public keys to files
with open("ed25519_private_key.pem", "wb") as private_key_file:
    private_key_file.write(private_pem)

with open("ed25519_public_key.pem", "wb") as public_key_file:
    public_key_file.write(public_pem)
