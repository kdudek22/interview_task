import hashlib
import base64
import os


salt = os.environ.get("SALT")  # env variable
separator = "-"  # up to discussion, but still config related


def get_signature_from_headers(auth_header: str | None) -> str | None:
    if not auth_header:
        return None

    return get_tripcode(*get_basic_auth_credentials(auth_header))


def get_tripcode(username: str, secret: str) -> str:
    combined = username + secret + salt
    return f"{username}{separator}{hashlib.md5(combined.encode()).hexdigest()}"


def get_basic_auth_credentials(auth_header):
    # Strip "Basic " prefix and decode the base64 credentials
    encoded_credentials = auth_header.split(' ', 1)[1]

    decoded_bytes = base64.b64decode(encoded_credentials)
    decoded_credentials = decoded_bytes.decode('utf-8')

    return decoded_credentials.split(':', 1)
