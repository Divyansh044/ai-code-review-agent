import hashlib
import hmac

from app.webhooks.security import verify_signature

SECRET = "test-secret"


def sign(body: bytes, secret: str = SECRET) -> str:
    return "sha256=" + hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()


def test_valid_signature_is_accepted() -> None:
    body = b'{"hello": "world"}'
    assert verify_signature(body, sign(body), SECRET) is True


def test_tampered_body_is_rejected() -> None:
    body = b'{"hello": "world"}'
    signature = sign(body)
    assert verify_signature(b'{"hello": "mallory"}', signature, SECRET) is False


def test_wrong_secret_is_rejected() -> None:
    body = b'{"hello": "world"}'
    assert verify_signature(body, sign(body, secret="wrong-secret"), SECRET) is False


def test_missing_signature_is_rejected() -> None:
    assert verify_signature(b"{}", None, SECRET) is False


def test_malformed_signature_is_rejected() -> None:
    assert verify_signature(b"{}", "not-a-valid-signature", SECRET) is False
