import hashlib
import base64


salt = "test123"  # env variable
separator = "-"  # up to discussion, but still config related


def get_tripcode(username: str, secret: str) -> str:
    raw = username + secret + salt
    return f"{username}{separator}{hashlib.md5(raw.encode()).hexdigest()}"


def get_basic_auth_credentials(auth_header):
    # Strip "Basic " prefix and decode the base64 credentials
    encoded_credentials = auth_header.split(' ', 1)[1]

    decoded_bytes = base64.b64decode(encoded_credentials)
    decoded_credentials = decoded_bytes.decode('utf-8')  # why only utf8?

    return decoded_credentials.split(':', 1)
