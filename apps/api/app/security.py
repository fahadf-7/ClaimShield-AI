import base64
import hashlib
import hmac
import json
import secrets
from datetime import timedelta

from app.common import utcnow
from app.config import settings


def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    digest = hashlib.scrypt(password.encode(), salt=salt, n=2**14, r=8, p=1, dklen=32)
    return f"scrypt${base64.urlsafe_b64encode(salt).decode()}${base64.urlsafe_b64encode(digest).decode()}"


def verify_password(password: str, stored: str) -> bool:
    try:
        algorithm, salt_value, digest_value = stored.split("$", 2)
        if algorithm != "scrypt":
            return False
        salt = base64.urlsafe_b64decode(salt_value)
        expected = base64.urlsafe_b64decode(digest_value)
        actual = hashlib.scrypt(password.encode(), salt=salt, n=2**14, r=8, p=1, dklen=32)
        return hmac.compare_digest(actual, expected)
    except (ValueError, TypeError):
        return False


def _encode_segment(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).decode().rstrip("=")


def _decode_segment(value: str) -> bytes:
    return base64.urlsafe_b64decode(value + "=" * (-len(value) % 4))


def create_access_token(user_id: str, organization_id: str, role: str) -> str:
    header = _encode_segment(json.dumps({"alg": "HS256", "typ": "JWT"}).encode())
    expires = utcnow() + timedelta(minutes=settings.access_token_minutes)
    payload = _encode_segment(
        json.dumps(
            {"sub": user_id, "org": organization_id, "role": role, "exp": int(expires.timestamp())}
        ).encode()
    )
    message = f"{header}.{payload}".encode()
    signature = _encode_segment(hmac.new(settings.secret_key.encode(), message, hashlib.sha256).digest())
    return f"{header}.{payload}.{signature}"


def decode_access_token(token: str) -> dict[str, object]:
    try:
        header, payload, signature = token.split(".")
        message = f"{header}.{payload}".encode()
        expected = hmac.new(settings.secret_key.encode(), message, hashlib.sha256).digest()
        if not hmac.compare_digest(expected, _decode_segment(signature)):
            raise ValueError("Invalid token signature")
        data = json.loads(_decode_segment(payload))
        if int(data["exp"]) < int(utcnow().timestamp()):
            raise ValueError("Token expired")
        return data
    except (ValueError, KeyError, json.JSONDecodeError) as exc:
        raise ValueError("Invalid or expired token") from exc

